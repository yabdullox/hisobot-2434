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
async def send_report_prompt(message: types.Message):
    await message.answer(
        "📤 Iltimos, bugungi ish hisobotini yuboring.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
        reply_markup=ReplyKeyboardRemove()
    )
    worker_state[message.from_user.id] = "waiting_for_report"


@router.message(F.text & ~F.text.in_(["⏰ Ishni boshladim", "🏁 Ishni tugatdim", "📷 Tozalash rasmi yuborish",
                                      "📸 Muammo yuborish", "💰 Bonus/Jarimalarim", "📅 Bugungi hisobotlarim",
                                      "↩️ Menyuga qaytish"]))
async def receive_report(message: types.Message):
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

    # Superadminga yuboramiz
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
        hour, minute = now.hour, now.minute
        start_hour = 9
        grace_minutes = 10
        total_minutes = hour * 60 + minute
        start_minutes = start_hour * 60
        late_minutes = total_minutes - (start_minutes + grace_minutes)

        worker_id, filial_id, name = worker

        # Kechikkan bo‘lsa — jarima
        if late_minutes > 0:
            fine = int((late_minutes / 60) * 10000)
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker_id, filial_id, f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
            await msg.answer(f"⚠️ Siz kech keldingiz ({late_minutes} daqiqa). Jarima: {fine:,} so‘m.")

        # Erta kelgan bo‘lsa — bonus
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


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✅ Ishni tugatganingiz qayd etildi.\n📩 Endi yakuniy hisobotni yuboring:",
                     reply_markup=confirm_end_work_menu())
    worker_state[msg.from_user.id] = "waiting_for_final_button"


# === 📤 YAKUNIY HISOBOT ===
@router.message(F.text == "📤 Yakuniy hisobotni yuborish")
async def ask_final_report_text(msg: types.Message):
    await msg.answer("✏️ Iltimos, bugungi yakuniy hisobotni yozing.",
                     reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_final_report_text"


@router.message(F.text)
async def receive_final_report_text(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_final_report_text":
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
    state = worker_state.get(msg.from_user.id)
    if state not in ["waiting_for_clean_photo", "waiting_for_problem_photo"]:
        return

    file_id = msg.photo[-1].file_id
    caption = "🧹 Tozalash rasmi" if state == "waiting_for_clean_photo" else "🚨 Muammo rasmi"
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

    await msg.bot.send_photo(SUPERADMIN_ID, photo=file_id,
                             caption=f"{caption}\n👷 {worker[0]}\n🆔 {msg.from_user.id}")

    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# === 📸 MUAMMO YUBORISH ===
@router.message(F.text == "📸 Muammo yuborish")
async def ask_problem_photo(msg: types.Message):
    await msg.answer("📸 Muammo rasmini yuboring (captionda izoh yozing):",
                     reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_problem_photo"


# === 💰 BONUS/JARIMALARIM ===
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finance(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        async with conn.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=?", (worker[0],)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=?", (worker[0],)) as cur:
            fines = await cur.fetchall()

    text = f"💰 <b>{worker[1]} uchun bonus va jarimalar:</b>\n\n"
    if bonuses:
        text += "🎉 <b>Bonuslar:</b>\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]} ({b[2]})" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ <b>Jarimalar:</b>\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]} ({f[2]})" for f in fines])
    if not bonuses and not fines:
        text += "📭 Sizda hozircha bonus yoki jarima yo‘q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


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
