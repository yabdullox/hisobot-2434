# src/handlers/worker.py
from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import (worker_menu, product_menu, start_work_menu,
                                confirm_end_work_menu)
from database import db
from config import SUPERADMIN_ID
import datetime
import aiosqlite

router = Router()

# oddiy in-memory state (kichik loyiha uchun yetarli)
worker_state = {}
worker_data = {}

# --- yordamchi funksiyalar ---
async def ensure_tables():
    """Agar db jadvali bo'lmasa — yaratiladi. (Qayta chaqirish xavfsiz)"""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                tg_id TEXT UNIQUE,
                filial_id INTEGER
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                text TEXT,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                reason TEXT,
                amount INTEGER,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                reason TEXT,
                amount INTEGER,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                note TEXT,
                file_id TEXT,
                status TEXT,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                file_id TEXT,
                note TEXT,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                name TEXT,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS product_sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                worker_id INTEGER,
                quantity TEXT,
                created_at TEXT
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS work_start_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                start_time TEXT
            )
        """)
        await conn.commit()

# chaqirish (router yuklanganda bir marta chaqirish foydali)
@router.startup()
async def on_startup_worker():
    await ensure_tables()

# ----------------------------
# 🧾 HISOBOT YUBORISH (3 bosqich)
# ----------------------------
@router.message(F.text == "🧾 Hisobot yuborish")
async def cmd_report_start(msg: types.Message):
    worker_state[msg.from_user.id] = "report_step_text"
    worker_data[msg.from_user.id] = {}
    await msg.answer("✏️ Hisobot matnini yuboring (masalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo'):", reply_markup=ReplyKeyboardRemove())

@router.message(F.text)
async def report_steps_router(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)

    # agar boshqa holatlarda bo'lsa, bu handlerga tushmasin
    if state is None or not state.startswith("report_step"):
        return

    # 1) matn
    if state == "report_step_text":
        worker_data[uid]["text"] = msg.text.strip()
        worker_state[uid] = "report_step_sum"
        await msg.answer("💵 Bugungi umumiy savdo summasi (so‘mda)ni raqam bilan kiriting:")
        return

    # 2) summa
    if state == "report_step_sum":
        try:
            amount = int(msg.text.replace(" ", ""))
        except Exception:
            return await msg.answer("❌ Iltimos, faqat raqam kiriting (masalan: 1200000).")
        worker_data[uid]["sum"] = amount
        worker_state[uid] = "report_step_products"
        await msg.answer("🧺 Agar mahsulotlar sotgan bo‘lsangiz, ularni vergul bilan yozing (masalan: Johori, Kiyim) yoki 'yoq' deb yozing:")
        return

    # 3) mahsulotlar ro'yxati yoki 'yoq'
    if state == "report_step_products":
        text = msg.text.strip()
        if text.lower() in ["yoq", "yo'q", "yo‘q", "yoʼq", "none", ""]:
            worker_data[uid]["products"] = []
            worker_state[uid] = "report_step_confirm"
            await msg.answer("✅ Hisobot tayyor. Tasdiqlash uchun 'tasdiqlash' deb yozing yoki 'bekor' deb yozing.")
            return

        products = [p.strip() for p in text.split(",") if p.strip()]
        worker_data[uid]["products"] = products
        # so'ng har bir mahsulot uchun miqdor so'raymiz
        worker_data[uid]["quantities"] = {}
        worker_state[uid] = f"report_qty_0"
        await msg.answer(f"📦 '{products[0]}' dan qancha sotdingiz? (masalan: '18kg' yoki '5 dona')")
        return

    # 4) ketma-ket mahsulot miqdorini qabul qilish
    if state.startswith("report_qty_"):
        idx = int(state.split("_")[-1])
        products = worker_data[uid]["products"]
        if idx < len(products):
            worker_data[uid]["quantities"][products[idx]] = msg.text.strip()
            idx += 1
            if idx < len(products):
                worker_state[uid] = f"report_qty_{idx}"
                await msg.answer(f"📦 '{products[idx]}' dan qancha sotdingiz?")
                return
            else:
                worker_state[uid] = "report_step_confirm"
                await msg.answer("✅ Hisobot tayyor. Tasdiqlash uchun 'tasdiqlash' deb yozing yoki 'bekor' deb yozing.")
                return

    # 5) tasdiqlash
    if state == "report_step_confirm":
        if msg.text.lower() in ["tasdiqlash", "ok", "ha"]:
            # saqlash va yuborish
            async with aiosqlite.connect(db.DB_PATH) as conn:
                async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
                    worker = await cur.fetchone()
                if not worker:
                    worker_state[uid] = None
                    return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

                wid, fid, wname = worker
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                # tuzilgan matn
                body = f"{worker_data[uid]['text']}\n💵 Savdo: {worker_data[uid]['sum']:,} so‘m\n"
                if worker_data[uid].get("products"):
                    body += "🧺 Sotilgan mahsulotlar:\n"
                    for p, q in worker_data[uid].get("quantities", {}).items():
                        body += f" • {p}: {q}\n"

                await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                                   (wid, fid, body, now))
                await conn.commit()

            # superadminga yuborish
            try:
                await msg.bot.send_message(SUPERADMIN_ID, f"📩 <b>Yangi hisobot</b>\n👷 {wname}\n🕒 {now}\n{body}", parse_mode="HTML")
            except Exception as e:
                print("Superadminga yuborishda xato:", e)

            worker_state[uid] = None
            worker_data[uid] = {}
            await msg.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())
            return
        elif msg.text.lower() in ["bekor", "cancel"]:
            worker_state[uid] = None
            worker_data[uid] = {}
            return await msg.answer("❌ Hisobot bekor qilindi.", reply_markup=worker_menu())
        else:
            return await msg.answer("❗ Tasdiqlash uchun 'tasdiqlash' yoki bekor qilish uchun 'bekor' deb yozing.")

# ----------------------------
# ⏰ ISHNI BOSHLADIM -> bonus / jarima avtomatik
# ----------------------------
@router.message(F.text == "⏰ Ishni boshladim")
async def cmd_start_work(msg: types.Message):
    uid = msg.from_user.id
    now = datetime.datetime.now()

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        wid, fid, wname = worker

        # start time 9:00; grace 10 daqiqa
        start_minutes = 9 * 60
        grace_minutes = 10
        current_minutes = now.hour * 60 + now.minute

        # Agar ertaroq (current < start_minutes) -> bonus hisoblash
        if current_minutes < start_minutes:
            early_minutes = start_minutes - current_minutes
            # miltatsiya: har 60 min uchun 10000 so'm
            bonus = int((early_minutes / 60) * 10000)
            if bonus > 0:
                await conn.execute("INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                                   (wid, fid, f"Erta kelish ({early_minutes} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
                await conn.commit()
                await msg.answer(f"🎉 Erta keldingiz: {early_minutes} daqiqa. Bonus +{bonus:,} so‘m", reply_markup=worker_menu())
        else:
            # agar kechikish grace dan oshsa
            late = current_minutes - (start_minutes + grace_minutes)
            if late > 0:
                fine = int((late / 60) * 10000)
                await conn.execute("INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                                   (wid, fid, f"Kechikish ({late} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
                await conn.commit()
                await msg.answer(f"⚠️ Kech keldingiz: {late} daqiqa. Jarima: {fine:,} so‘m", reply_markup=worker_menu())
            else:
                await msg.answer("✅ Ishni o‘z vaqtida boshladingiz.", reply_markup=worker_menu())

        # logga saqlash
        await conn.execute("INSERT INTO work_start_log (worker_id, filial_id, start_time) VALUES (?, ?, ?)",
                           (wid, fid, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

        # superadminga xabar
        try:
            await msg.bot.send_message(SUPERADMIN_ID, f"🕒 {wname} ishni boshladi: {now.strftime('%Y-%m-%d %H:%M')}")
        except Exception:
            pass

# ----------------------------
# 🏁 ISHNI TUGATDIM -> yakuniy hisobot
# ----------------------------
@router.message(F.text == "🏁 Ishni tugatdim")
async def cmd_end_work(msg: types.Message):
    uid = msg.from_user.id
    worker_state[uid] = "waiting_final_report"
    await msg.answer("✏️ Iltimos, yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(F.text)
async def final_report_receiver(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_final_report":
        return
    text = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                           (wid, fid, f"Yakuniy: {text}", now))
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi!", reply_markup=worker_menu())

    try:
        await msg.bot.send_message(SUPERADMIN_ID, f"🏁 <b>{wname}</b> yakuniy hisobotini yubordi.\n\n{str(text)}", parse_mode="HTML")
    except Exception:
        pass

# ----------------------------
# 📷 Tozalash rasmi / 📸 Muammo yuborish
# ----------------------------
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_clean_photo"
    await msg.answer("📸 Tozalash rasmini yuboring (agar izoh bo'lsa captionda yozing):", reply_markup=ReplyKeyboardRemove())

@router.message(F.text == "📸 Muammo yuborish")
async def ask_problem_photo(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_problem_photo"
    await msg.answer("📸 Muammo rasm yoki izoh bilan yuboring (captionda izoh):", reply_markup=ReplyKeyboardRemove())

@router.message(F.photo)
async def receive_photo(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if state not in ["waiting_clean_photo", "waiting_problem_photo"]:
        return

    file_id = msg.photo[-1].file_id
    caption = msg.caption or ""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        # saqlash photos jadvaliga
        await conn.execute("INSERT INTO photos (worker_id, filial_id, file_id, note, created_at) VALUES (?, ?, ?, ?, ?)",
                           (wid, fid, file_id, caption, now))
        await conn.commit()

    # superadminga yuborish — tozalash yoki muammo ekanini aytib yuboramiz
    kind = "Tozalash rasmi" if state == "waiting_clean_photo" else "Muammo rasmi"
    try:
        await msg.bot.send_photo(SUPERADMIN_ID, photo=file_id, caption=f"📸 {kind}\n👷 {wname}\n🆔 {uid}\n📝 {caption}")
    except Exception:
        pass

    worker_state[uid] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())

# ----------------------------
# 📦 MAHSULOTLARIM: ko'rish / qo'shish / o'chirish
# ----------------------------
@router.message(F.text == "📦 Mahsulotlarim")
async def products_menu(msg: types.Message):
    await msg.answer("📦 Mahsulotlar bo‘limi:", reply_markup=product_menu())

@router.message(F.text == "➕ Mahsulot qo‘shish")
async def product_add_start(msg: types.Message):
    worker_state[msg.from_user.id] = "product_add_name"
    await msg.answer("➕ Mahsulot nomini yuboring (masalan: Johori):", reply_markup=ReplyKeyboardRemove())

@router.message(F.text)
async def product_router(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)

    # qo'shish - nom
    if state == "product_add_name":
        name = msg.text.strip()
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (uid,)) as cur:
                worker = await cur.fetchone()
            if not worker:
                worker_state[uid] = None
                return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
            wid, fid = worker
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            await conn.execute("INSERT INTO products (worker_id, filial_id, name, created_at) VALUES (?, ?, ?, ?)",
                               (wid, fid, name, now))
            await conn.commit()
        worker_state[uid] = None
        await msg.answer(f"✅ '{name}' mahsuloti qo‘shildi.", reply_markup=worker_menu())
        return

    # o'chirish
    if msg.text == "❌ Mahsulotni o‘chirish":
        worker_state[uid] = "product_del_name"
        await msg.answer("❌ O‘chirmoqchi bo‘lgan mahsulot nomini yuboring:", reply_markup=ReplyKeyboardRemove())
        return

    if state == "product_del_name":
        name = msg.text.strip()
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("DELETE FROM products WHERE name=? AND worker_id=(SELECT id FROM workers WHERE tg_id=?)", (name, uid))
            await conn.commit()
        worker_state[uid] = None
        await msg.answer(f"✅ '{name}' mahsuloti o‘chirildi (agar mavjud bo‘lgan bo‘lsa).", reply_markup=worker_menu())
        return

    # Mavjud mahsulotlarni ko'rish
    if msg.text == "📋 Mavjud mahsulotlar":
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT name FROM products WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)", (uid,)) as cur:
                rows = await cur.fetchall()
        if not rows:
            return await msg.answer("📦 Sizda mavjud mahsulotlar yo‘q.", reply_markup=worker_menu())
        text = "📦 Sizda mavjud mahsulotlar:\n" + "\n".join([f"• {r[0]}" for r in rows])
        return await msg.answer(text, reply_markup=worker_menu())

# ----------------------------
# 📅 Bugungi hisobotlarim + tahrirlash
# ----------------------------
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def show_today_reports(msg: types.Message):
    uid = msg.from_user.id
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT id, text, created_at FROM reports
            WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)
            AND DATE(created_at)=DATE(?)
            ORDER BY id DESC
        """, (uid, today)) as cur:
            rows = await cur.fetchall()
    if not rows:
        return await msg.answer("📭 Bugun hech qanday hisobot kelmagan.", reply_markup=worker_menu())

    # ro'yxat bilan chiqaramiz (id ko'rsatib)
    out = "📅 Bugungi hisobotlaringiz:\n\n"
    for r in rows:
        out += f"ID:{r[0]} — {r[2]}\n{r[1]}\n\n"
    out += "📝 Agar tahrirlash kerak bo'lsa, 'tahrirlash <ID>' deb yozing."
    await msg.answer(out, reply_markup=worker_menu())

@router.message(F.text.startswith("tahrirlash "))
async def edit_report_start(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("❗ To'g'ri format: tahrirlash <ID>")
    try:
        rid = int(parts[1])
    except Exception:
        return await msg.answer("❗ ID raqam bo'lishi kerak.")
    uid = msg.from_user.id
    # tekshir: bu id ushbu ishchiga tegishli ekanini tekshiramiz
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM reports WHERE id=? AND worker_id=(SELECT id FROM workers WHERE tg_id=?)", (rid, uid)) as cur:
            found = await cur.fetchone()
    if not found:
        return await msg.answer("❌ Bunday hisobot topilmadi.")
    worker_state[uid] = f"edit_report_{rid}"
    await msg.answer(f"✏️ Endi yangi matnni yuboring (ID: {rid}):", reply_markup=ReplyKeyboardRemove())

@router.message(F.text)
async def edit_report_apply(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if not state or not state.startswith("edit_report_"):
        return
    rid = int(state.split("_")[-1])
    new_text = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("UPDATE reports SET text=? WHERE id=? AND worker_id=(SELECT id FROM workers WHERE tg_id=?)", (new_text, rid, uid))
        await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Hisobot tahrirlandi va yangilandi.", reply_markup=worker_menu())

# ----------------------------
# 💰 Bonus / Jarimalar
# ----------------------------
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finances(msg: types.Message):
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())
        wid = worker[0]
        async with conn.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=? ORDER BY id DESC LIMIT 20", (wid,)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=? ORDER BY id DESC LIMIT 20", (wid,)) as cur:
            fines = await cur.fetchall()

    text = f"💰 {worker[1]} uchun: \n\n"
    if bonuses:
        text += "🎉 Bonuslar:\n" + "\n".join([f"{b[2]} — +{b[1]} so‘m — {b[0]}" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ Jarimalar:\n" + "\n".join([f"{f[2]} — -{f[1]} so‘m — {f[0]}" for f in fines]) + "\n\n"
    if not bonuses and not fines:
        text += "📭 Hozircha ma'lumot yo'q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())

# ↩️ menyuga qaytish (har joyda ishlaydi)
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
