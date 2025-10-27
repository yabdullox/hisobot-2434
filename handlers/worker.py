from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID
from database import db
import datetime
import aiosqlite

router = Router()
worker_state = {}

# 🧩 Yordamchi: filial adminlarini topish
async def get_filial_admins(fid: int):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT tg_id FROM admins WHERE filial_id=?", (fid,)) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows] if rows else []


# ========== 🧾 HISOBOT MENYUSI ==========
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(msg: types.Message):
    await msg.answer("✏️ Hisobot matnini kiriting:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_report"


@router.message(F.text)
async def handle_report(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_report":
        return

    text = msg.text
    now = datetime.datetime.now()

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (wid, fid, text, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())

    # Superadmin va filial adminlarga yuborish
    admins = await get_filial_admins(fid)
    notify = f"🧾 <b>Yangi hisobot:</b>\n👷 {wname}\n🕒 {now.strftime('%H:%M')}\n📄 {text}"
    for admin in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_message(admin, notify, parse_mode="HTML")
        except:
            pass


# ========== ⏰ ISHNI BOSHLADIM ==========
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    uid = msg.from_user.id
    now = datetime.datetime.now()

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        start_minutes = 9 * 60  # 9:00
        grace = 10
        current = now.hour * 60 + now.minute

        bonus, fine = 0, 0

        # Erta kelish → bonus
        if current < start_minutes:
            diff = start_minutes - current
            bonus = int((diff / 60) * 10000)
            await conn.execute("""
                INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, f"Erta kelish ({diff} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))

        # Kechikish → jarima
        elif current > start_minutes + grace:
            diff = current - (start_minutes + grace)
            fine = int((diff / 60) * 10000)
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, f"Kechikish ({diff} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))

        await conn.execute("""
            INSERT INTO work_start_log (worker_id, filial_id, start_time)
            VALUES (?, ?, ?)
        """, (wid, fid, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    text = f"✅ Ishni boshladingiz ({now.strftime('%H:%M')})"
    if bonus:
        text += f"\n🎉 Bonus: +{bonus:,} so‘m"
    if fine:
        text += f"\n⚠️ Jarima: -{fine:,} so‘m"

    await msg.answer(text, reply_markup=worker_menu())

    admins = await get_filial_admins(fid)
    notify = f"👷 <b>{wname}</b> ishni boshladi.\n{text}"
    for admin in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_message(admin, notify, parse_mode="HTML")
        except:
            pass


# ========== 🏁 ISHNI TUGATDIM ==========
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_final_report"
    await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())


@router.message(F.text)
async def final_report(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_final_report":
        return

    now = datetime.datetime.now()
    text = msg.text

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker

        # Bugungi bonus va jarimalar
        async with conn.execute("""
            SELECT IFNULL(SUM(amount), 0) FROM bonuses WHERE worker_id=? AND DATE(created_at)=DATE(?)
        """, (wid, now.strftime("%Y-%m-%d"))) as cur:
            bonus = (await cur.fetchone())[0]
        async with conn.execute("""
            SELECT IFNULL(SUM(amount), 0) FROM fines WHERE worker_id=? AND DATE(created_at)=DATE(?)
        """, (wid, now.strftime("%Y-%m-%d"))) as cur:
            fine = (await cur.fetchone())[0]

        full_text = (
            f"🏁 <b>Yakuniy hisobot</b>\n👷 {wname}\n🕒 {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"📄 {text}\n\n🎉 Bonus: +{bonus:,} so‘m\n⚠️ Jarima: -{fine:,} so‘m"
        )

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (wid, fid, full_text, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi.", reply_markup=worker_menu())

    admins = await get_filial_admins(fid)
    for admin in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_message(admin, full_text, parse_mode="HTML")
        except:
            pass


# ========== 📷 TOZALASH RASMI ==========
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def clean_photo_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_clean_photo"
    await msg.answer("📸 Tozalash rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


# ========== 📸 MUAMMO YUBORISH ==========
@router.message(F.text == "📸 Muammo yuborish")
async def problem_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_problem_photo"
    await msg.answer("⚠️ Muammo rasm yoki izoh bilan yuboring:", reply_markup=ReplyKeyboardRemove())


# ========== 📸 RASM QABUL QILISH ==========
@router.message(F.photo)
async def receive_photo(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if state not in ["waiting_clean_photo", "waiting_problem_photo"]:
        return

    caption = msg.caption or ""
    file_id = msg.photo[-1].file_id
    now = datetime.datetime.now()

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        kind = "🧹 Tozalash rasmi" if state == "waiting_clean_photo" else "⚠️ Muammo"

        if state == "waiting_clean_photo":
            await conn.execute("""
                INSERT INTO photos (worker_id, filial_id, file_id, note, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, file_id, caption, now.strftime("%Y-%m-%d %H:%M")))
        else:
            await conn.execute("""
                INSERT INTO problems (worker_id, filial_id, note, file_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (wid, fid, caption, file_id, "new", now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yuborildi.", reply_markup=worker_menu())

    admins = await get_filial_admins(fid)
    for admin in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_photo(admin, file_id, caption=f"{kind}\n👷 {wname}\n📝 {caption}")
        except:
            pass


# ========== ↩️ MENYUGA QAYTISH ==========
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
