# src/handlers/worker.py

from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu, product_menu
from database import db
from config import SUPERADMIN_ID
import datetime
import aiosqlite

router = Router()

# oddiy in-memory holat
worker_state = {}
worker_data = {}

# ==========================
# 🧾 HISOBOT YUBORISH (3 bosqich)
# ==========================
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(msg: types.Message):
    worker_state[msg.from_user.id] = "report_step_text"
    worker_data[msg.from_user.id] = {}
    await msg.answer("✏️ Hisobot matnini yuboring (masalan: 5 ta mijoz, 3 ta tozalash):", reply_markup=ReplyKeyboardRemove())


@router.message(F.text)
async def handle_report_steps(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if not state or not state.startswith("report_step"):
        return

    # 1️⃣ Matn
    if state == "report_step_text":
        worker_data[uid]["text"] = msg.text.strip()
        worker_state[uid] = "report_step_sum"
        await msg.answer("💵 Bugungi umumiy savdo summasini kiriting (so‘mda):")
        return

    # 2️⃣ Summani kiritish
    if state == "report_step_sum":
        try:
            worker_data[uid]["sum"] = int(msg.text.replace(" ", ""))
        except:
            return await msg.answer("❌ Faqat raqam kiriting (masalan: 1200000).")
        worker_state[uid] = "report_step_confirm"
        await msg.answer(
            f"✅ Hisobot tayyor:\n\n🧾 {worker_data[uid]['text']}\n💵 {worker_data[uid]['sum']:,} so‘m\n\n"
            "Tasdiqlash uchun <b>tasdiqlash</b> deb yozing yoki <b>bekor</b> deb yozing.",
            parse_mode="HTML"
        )
        return

    # 3️⃣ Tasdiqlash
    if state == "report_step_confirm":
        if msg.text.lower() in ["tasdiqlash", "ok", "ha"]:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
                    worker = await cur.fetchone()
                if not worker:
                    worker_state[uid] = None
                    return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

                wid, fid, wname = worker
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                await conn.execute("""
                    INSERT INTO reports (worker_id, filial_id, text, created_at)
                    VALUES (?, ?, ?, ?)
                """, (wid, fid,
                      f"{worker_data[uid]['text']}\n💵 Savdo: {worker_data[uid]['sum']:,} so‘m", now))
                await conn.commit()

            try:
                await msg.bot.send_message(
                    SUPERADMIN_ID,
                    f"📩 <b>Yangi hisobot</b>\n👷 {wname}\n🕒 {now}\n"
                    f"{worker_data[uid]['text']}\n💵 {worker_data[uid]['sum']:,} so‘m",
                    parse_mode="HTML"
                )
            except:
                pass

            worker_state[uid] = None
            await msg.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())
        elif msg.text.lower() in ["bekor", "cancel"]:
            worker_state[uid] = None
            await msg.answer("❌ Hisobot bekor qilindi.", reply_markup=worker_menu())


# ==========================
# ⏰ ISHNI BOSHLADIM
# ==========================
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    uid = msg.from_user.id
    now = datetime.datetime.now()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        start_minutes = 9 * 60
        grace_minutes = 10
        current_minutes = now.hour * 60 + now.minute
        now_str = now.strftime("%Y-%m-%d %H:%M")

        if current_minutes < start_minutes:
            early = start_minutes - current_minutes
            bonus = int((early / 60) * 10000)
            if bonus > 0:
                await conn.execute("""
                    INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (wid, fid, f"Erta kelish ({early} daqiqa)", bonus, now_str))
                await conn.commit()
                await msg.answer(f"🎉 Erta keldingiz: Bonus +{bonus:,} so‘m")
        elif current_minutes > start_minutes + grace_minutes:
            late = current_minutes - (start_minutes + grace_minutes)
            fine = int((late / 60) * 10000)
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, f"Kechikish ({late} daqiqa)", fine, now_str))
            await conn.commit()
            await msg.answer(f"⚠️ Kech keldingiz: Jarima -{fine:,} so‘m")
        else:
            await msg.answer("✅ Siz o‘z vaqtida keldingiz!")

        await conn.execute("INSERT INTO work_start_log (worker_id, filial_id, start_time) VALUES (?, ?, ?)",
                           (wid, fid, now_str))
        await conn.commit()

    await msg.answer("📋 Asosiy menyu:", reply_markup=worker_menu())


# ==========================
# 🏁 ISHNI TUGATDIM
# ==========================
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_final"
    await msg.answer("✏️ Yakuniy hisobotni kiriting:", reply_markup=ReplyKeyboardRemove())


@router.message(F.text)
async def save_final_report(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_final":
        return
    text = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                           (wid, fid, f"Yakuniy hisobot: {text}", now))
        await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi!", reply_markup=worker_menu())


# ==========================
# 📷 TOZALASH RASMI / 📸 MUAMMO YUBORISH
# ==========================
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_clean_photo"
    await msg.answer("📸 Tozalash rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "📸 Muammo yuborish")
async def ask_problem_photo(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_problem_photo"
    await msg.answer("📸 Muammo rasmini yoki izohni yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(F.photo)
async def handle_photos(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if state not in ["waiting_clean_photo", "waiting_problem_photo"]:
        return

    file_id = msg.photo[-1].file_id
    caption = msg.caption or ""
    kind = "tozalash" if state == "waiting_clean_photo" else "muammo"

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
        wid, fid, wname = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        if kind == "tozalash":
            await conn.execute("INSERT INTO photos (worker_id, filial_id, file_id, note, created_at) VALUES (?, ?, ?, ?, ?)",
                               (wid, fid, file_id, caption, now))
        else:
            await conn.execute("INSERT INTO problems (worker_id, filial_id, note, file_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                               (wid, fid, caption, file_id, 'yangi', now))
        await conn.commit()

    await msg.bot.send_photo(SUPERADMIN_ID, photo=file_id,
                             caption=f"📸 {kind.title()} rasmi\n👷 {wname}\n🕒 {now}\n📝 {caption}")
    worker_state[uid] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# ==========================
# 📦 MAHSULOTLAR
# ==========================
@router.message(F.text == "📦 Mahsulotlarim")
async def show_products(msg: types.Message):
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM products WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)", (uid,)) as cur:
            rows = await cur.fetchall()
    if not rows:
        text = "📦 Sizda hozircha mahsulot yo‘q."
    else:
        text = "📦 Sizning mahsulotlaringiz:\n" + "\n".join([f"• {r[0]}" for r in rows])
    await msg.answer(text, reply_markup=product_menu())


# ➕ / ❌ / 📋 ishlovchilar
@router.message(F.text == "➕ Mahsulot qo‘shish")
async def add_product(msg: types.Message):
    worker_state[msg.from_user.id] = "adding_product"
    await msg.answer("🆕 Mahsulot nomini yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "❌ Mahsulotni o‘chirish")
async def del_product_start(msg: types.Message):
    worker_state[msg.from_user.id] = "deleting_product"
    await msg.answer("🗑 O‘chirmoqchi bo‘lgan mahsulot nomini yuboring:", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "📋 Mavjud mahsulotlar")
async def list_products(msg: types.Message):
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM products WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)", (uid,)) as cur:
            rows = await cur.fetchall()
    if not rows:
        return await msg.answer("📭 Sizda mahsulot yo‘q.", reply_markup=worker_menu())
    text = "📋 Mahsulotlar:\n" + "\n".join([f"• {r[0]}" for r in rows])
    await msg.answer(text, reply_markup=worker_menu())


@router.message(F.text)
async def product_add_del(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if state not in ["adding_product", "deleting_product"]:
        return

    name = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
        wid, fid = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        if state == "adding_product":
            await conn.execute("INSERT INTO products (worker_id, filial_id, name, created_at) VALUES (?, ?, ?, ?)",
                               (wid, fid, name, now))
            await conn.commit()
            worker_state[uid] = None
            return await msg.answer(f"✅ Mahsulot '{name}' qo‘shildi!", reply_markup=worker_menu())

        elif state == "deleting_product":
            await conn.execute("DELETE FROM products WHERE worker_id=? AND name=?", (wid, name))
            await conn.commit()
            worker_state[uid] = None
            return await msg.answer(f"🗑 '{name}' o‘chirildi.", reply_markup=worker_menu())


# ==========================
# 📅 BUGUNGI HISOBOTLARIM
# ==========================
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
        return await msg.answer("📭 Bugun hali hech qanday hisobot yubormagansiz.", reply_markup=worker_menu())

    text = "📅 <b>Bugungi hisobotlaringiz:</b>\n\n"
    for r in rows:
        text += f"🆔 <b>ID:</b> {r[0]}\n🕒 {r[2]}\n📋 {r[1]}\n\n"
    text += "✏️ Tahrirlash uchun: <code>tahrirlash ID</code> deb yozing."
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


@router.message(F.text.startswith("tahrirlash "))
async def edit_report_start(msg: types.Message):
    parts = msg.text.split()
    if len(parts) < 2:
        return await msg.answer("❗ Format: tahrirlash <ID>")
    try:
        rid = int(parts[1])
    except:
        return await msg.answer("❌ ID raqam bo‘lishi kerak.")
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM reports WHERE id=? AND worker_id=(SELECT id FROM workers WHERE tg_id=?)",
                                (rid, uid)) as cur:
            found = await cur.fetchone()
    if not found:
        return await msg.answer("❌ Bunday hisobot sizga tegishli emas.")
    worker_state[uid] = f"edit_report_{rid}"
    await msg.answer(f"✏️ Yangi matnni kiriting (ID {rid}):", reply_markup=ReplyKeyboardRemove())


@router.message(F.text)
async def edit_report_apply(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if not state or not state.startswith("edit_report_"):
        return
    rid = int(state.split("_")[-1])
    new_text = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("UPDATE reports SET text=? WHERE id=? AND worker_id=(SELECT id FROM workers WHERE tg_id=?)",
                           (new_text, rid, uid))
        await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Hisobot yangilandi.", reply_markup=worker_menu())


# ==========================
# 💰 BONUS/JARIMALAR
# ==========================
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finance(msg: types.Message):
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())
        wid = worker[0]
        async with conn.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=? ORDER BY id DESC LIMIT 10", (wid,)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=? ORDER BY id DESC LIMIT 10", (wid,)) as cur:
            fines = await cur.fetchall()
    text = f"💰 {worker[1]} uchun:\n\n"
    if bonuses:
        text += "🎉 Bonuslar:\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]} ({b[2]})" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ Jarimalar:\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]} ({f[2]})" for f in fines])
    if not bonuses and not fines:
        text += "📭 Hozircha ma’lumot yo‘q."
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# ==========================
# ↩️ ORQAGA QAYTISH
# ==========================
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
