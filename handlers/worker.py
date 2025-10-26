from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu, confirm_end_work_menu
from database import db
from config import SUPERADMIN_ID
import datetime
import aiosqlite

router = Router()
worker_state = {}


# === 🧾 HISOBOT YUBORISH ===
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(message: types.Message):
    await message.answer(
        "📤 Iltimos, bugungi ish hisobotini yozing.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
        reply_markup=ReplyKeyboardRemove()
    )
    worker_state[message.from_user.id] = "waiting_for_report"


@router.message(F.text)
async def save_report(message: types.Message):
    if worker_state.get(message.from_user.id) != "waiting_for_report":
        return

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (message.from_user.id,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            return await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (worker[0], worker[1], message.text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            f"📩 <b>Yangi hisobot</b>\n👷 Ishchi: {worker[2]}\n🆔 {message.from_user.id}\n📍 Filial ID: {worker[1]}\n\n🧾 {message.text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Superadminga hisobot yuborishda xato: {e}")

    worker_state[message.from_user.id] = None
    await message.answer("✅ Hisobot yuborildi! Rahmat 👌", reply_markup=worker_menu())


# === ⏰ ISHNI BOSHLADIM ===
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        now = datetime.datetime.now()
        start_hour = 9
        grace_minutes = 10
        total_minutes = now.hour * 60 + now.minute
        start_minutes = start_hour * 60
        late_minutes = total_minutes - (start_minutes + grace_minutes)

        worker_id, filial_id, name = worker

        if late_minutes > 0:
            fine = int((late_minutes / 60) * 10000)
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker_id, filial_id, f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
            await msg.answer(f"⚠️ Siz kech keldingiz ({late_minutes} daqiqa). Jarima: {fine:,} so‘m.")
        elif total_minutes < start_minutes:
            early_minutes = start_minutes - total_minutes
            bonus = int((early_minutes / 60) * 10000)
            await conn.execute("""
                INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker_id, filial_id, f"Erta kelgan ({early_minutes} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
            await msg.answer(f"🎉 Siz ertaroq keldingiz! Bonus: +{bonus:,} so‘m.")
        else:
            await msg.answer("✅ Siz ishni o‘z vaqtida boshladingiz!")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS work_start_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                start_time TEXT
            )
        """)
        await conn.execute("""
            INSERT INTO work_start_log (worker_id, filial_id, start_time)
            VALUES (?, ?, ?)
        """, (worker_id, filial_id, now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    try:
        await msg.bot.send_message(
            SUPERADMIN_ID,
            f"🕒 <b>{name}</b> ishni boshladi.\n🕓 {now.strftime('%H:%M')} | 📍 Filial ID: {filial_id}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Superadminga yuborishda xato: {e}")

    await msg.answer("↩️ Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✅ Ishni tugatganingiz qayd etildi.\n📩 Endi yakuniy hisobotni yozing:",
                     reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_final_report"


@router.message(F.text)
async def receive_final_report(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_final_report":
        return

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (worker[0], worker[1], f"Yakuniy hisobot: {msg.text}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    try:
        await msg.bot.send_message(
            SUPERADMIN_ID,
            f"🏁 <b>{worker[2]}</b> ishni tugatdi.\n🧾 Yakuniy hisobot:\n{msg.text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Superadminga yakuniy hisobot yuborishda xato: {e}")

    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi! Rahmat 👏", reply_markup=worker_menu())


# === 📷 TOZALASH RASMI ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    await msg.answer("📸 Tozalash jarayoni rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_clean_photo"


@router.message(F.photo)
async def receive_photo(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_clean_photo":
        return

    file_id = msg.photo[-1].file_id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=f"🧹 Tozalash rasmi\n👷 {worker[0]}\n🆔 {msg.from_user.id}")
    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# === 📅 BUGUNGI HISOBOTLARIM ===
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def show_today_reports(msg: types.Message):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT text, created_at FROM reports
            WHERE worker_id = (SELECT id FROM workers WHERE tg_id = ?)
            AND DATE(created_at) = DATE(?)
            ORDER BY id DESC
        """, (msg.from_user.id, today)) as cur:
            reports = await cur.fetchall()

    if not reports:
        return await msg.answer("📭 Bugun hech qanday hisobot kelmagan.", reply_markup=worker_menu())

    text = "🗓 <b>Bugungi hisobotlaringiz:</b>\n\n" + "\n".join(
        [f"🕒 {r[1]} — {r[0]}" for r in reports])
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())
