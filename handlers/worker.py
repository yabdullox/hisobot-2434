from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from database import db
from config import SUPERADMIN_ID
import datetime
import aiosqlite

router = Router()
worker_state = {}
worker_data = {}

# === 🧩 Yordamchi funksiya: filial adminlarini topish ===
async def get_filial_admins(fid: int):
    """Filial adminlarini qaytaradi"""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT tg_id FROM admins WHERE filial_id=?", (fid,)) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows] if rows else []


# === ⏰ ISHNI BOSHLADIM ===
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
        start_minutes = 9 * 60  # 9:00
        grace_minutes = 10
        total_minutes = now.hour * 60 + now.minute

        bonus, fine = 0, 0
        reason = ""

        # Erta kelgan — bonus
        if total_minutes < start_minutes:
            diff = start_minutes - total_minutes
            bonus = int((diff / 60) * 10000)
            reason = f"Erta kelish ({diff} daqiqa)"
            await conn.execute("""
                INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, reason, bonus, now.strftime("%Y-%m-%d %H:%M")))

        # Kechikkan — jarima
        elif total_minutes > start_minutes + grace_minutes:
            diff = total_minutes - (start_minutes + grace_minutes)
            fine = int((diff / 60) * 10000)
            reason = f"Kechikish ({diff} daqiqa)"
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, reason, fine, now.strftime("%Y-%m-%d %H:%M")))

        # Ish boshlash logi
        await conn.execute("""
            INSERT INTO work_start_log (worker_id, filial_id, start_time)
            VALUES (?, ?, ?)
        """, (wid, fid, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    # Xabar tayyorlash
    text = f"✅ Ishni boshladingiz: {now.strftime('%H:%M')}"
    if bonus:
        text += f"\n🎉 Bonus: +{bonus:,} so‘m"
    if fine:
        text += f"\n⚠️ Jarima: -{fine:,} so‘m"

    await msg.answer(text, reply_markup=worker_menu())

    # Superadmin va filial adminlarga yuborish
    admins = await get_filial_admins(fid)
    notify_text = f"👷 <b>{wname}</b> ishni boshladi.\n{text}"
    for admin_id in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_message(admin_id, notify_text, parse_mode="HTML")
        except:
            pass


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_final_report"
    await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())


@router.message(F.text)
async def handle_final_report(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_final_report":
        return

    text = msg.text
    now = datetime.datetime.now()

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            worker_state[uid] = None
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        wid, fid, wname = worker

        # Bugungi bonus va jarimalarni topamiz
        async with conn.execute("""
            SELECT IFNULL(SUM(amount), 0) FROM bonuses WHERE worker_id=? AND DATE(created_at)=DATE(?)
        """, (wid, now.strftime("%Y-%m-%d"))) as cur:
            today_bonus = (await cur.fetchone())[0]
        async with conn.execute("""
            SELECT IFNULL(SUM(amount), 0) FROM fines WHERE worker_id=? AND DATE(created_at)=DATE(?)
        """, (wid, now.strftime("%Y-%m-%d"))) as cur:
            today_fine = (await cur.fetchone())[0]

        total_text = (
            f"📝 <b>Yakuniy hisobot</b>\n"
            f"👷 {wname}\n"
            f"🕒 {now.strftime('%Y-%m-%d %H:%M')}\n"
            f"📄 {text}\n\n"
            f"🎉 Bonus: +{today_bonus:,} so‘m\n"
            f"⚠️ Jarima: -{today_fine:,} so‘m"
        )

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (wid, fid, total_text, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi.", reply_markup=worker_menu())

    # Superadmin va filial adminlarga yuborish
    admins = await get_filial_admins(fid)
    for admin_id in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_message(admin_id, total_text, parse_mode="HTML")
        except:
            pass


# === 📷 TOZALASH RASMI ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def clean_photo_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_clean_photo"
    await msg.answer("📸 Tozalash rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


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

        if state == "waiting_clean_photo":
            await conn.execute("""
                INSERT INTO photos (worker_id, filial_id, file_id, note, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (wid, fid, file_id, caption, now.strftime("%Y-%m-%d %H:%M")))
            kind = "🧹 Tozalash rasmi"
        else:
            await conn.execute("""
                INSERT INTO problems (worker_id, filial_id, note, file_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (wid, fid, caption, file_id, "new", now.strftime("%Y-%m-%d %H:%M")))
            kind = "⚠️ Muammo xabari"

        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Rasm yuborildi.", reply_markup=worker_menu())

    # Superadmin va filial adminlarga yuborish
    admins = await get_filial_admins(fid)
    for admin_id in [SUPERADMIN_ID, *admins]:
        try:
            await msg.bot.send_photo(admin_id, file_id, caption=f"{kind}\n👷 {wname}\n📝 {caption}")
        except:
            pass


# === 📸 MUAMMO YUBORISH ===
@router.message(F.text == "📸 Muammo yuborish")
async def problem_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_problem_photo"
    await msg.answer("⚠️ Muammo rasm yoki izoh bilan yuboring:", reply_markup=ReplyKeyboardRemove())


# === ↩️ MENYUGA QAYTISH ===
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
