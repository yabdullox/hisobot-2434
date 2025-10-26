from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu, confirm_end_work_menu
from database import db
from config import SUPERADMIN_ID
import datetime

router = Router()

# Har bir ishchi uchun holatni saqlaymiz (hisobot yuborayaptimi, rasm yuborayaptimi va hok.)
worker_state = {}


# === 🧾 HISOBOT YUBORISH ===
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report_prompt(message: types.Message):
    await message.answer(
        "📤 Iltimos, hisobot matnini yuboring.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
        reply_markup=ReplyKeyboardRemove()
    )
    worker_state[message.from_user.id] = "waiting_for_report"


@router.message(F.text & ~F.text.in_(["⏰ Ishni boshladim", "🏁 Ishni tugatdim", "📷 Tozalash rasmi yuborish",
                                      "📸 Muammo yuborish", "💰 Bonus/Jarimalarim", "↩️ Menyuga qaytish"]))
async def receive_report(message: types.Message):
    if worker_state.get(message.from_user.id) != "waiting_for_report":
        return

    conn = db.get_conn()
    cur = conn.cursor()
    worker = cur.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (message.from_user.id,)).fetchone()

    if not worker:
        return await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

    # Hisobotni bazaga yozamiz
    cur.execute("""
        INSERT INTO reports (worker_id, filial_id, text, created_at)
        VALUES (?, ?, ?, ?)
    """, (worker[0], worker[1], message.text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

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
    conn = db.get_conn()
    cur = conn.cursor()

    worker = cur.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not worker:
        return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

    now = datetime.datetime.now()
    hour, minute = now.hour, now.minute
    start_hour = 9
    grace_minutes = 10
    total_minutes = hour * 60 + minute
    start_minutes = start_hour * 60
    late_minutes = total_minutes - (start_minutes + grace_minutes)

    filial_id, worker_id, name = worker[1], worker[0], worker[2]

    # Kechikish — jarima
    if late_minutes > 0:
        fine = int((late_minutes / 60) * 10000)
        cur.execute("""
            INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (worker_id, filial_id, f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        await msg.answer(f"⚠️ Siz kech keldingiz ({late_minutes} daqiqa).\nJarima: {fine:,} so‘m.", reply_markup=worker_menu())

    # Erta kelgan — bonus
    elif total_minutes < start_minutes:
        early_minutes = start_minutes - total_minutes
        bonus = int((early_minutes / 60) * 10000)
        cur.execute("""
            INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (worker_id, filial_id, f"Erta kelgan ({early_minutes} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        await msg.answer(f"🎉 Siz ertaroq keldingiz! Bonus: +{bonus:,} so‘m.", reply_markup=worker_menu())

    else:
        await msg.answer("✅ Siz ishni o‘z vaqtida boshladingiz!", reply_markup=worker_menu())

    # Ish boshlanishini loglash
    cur.execute("""
        CREATE TABLE IF NOT EXISTS work_start_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            start_time TEXT
        )
    """)
    cur.execute(
        "INSERT INTO work_start_log (worker_id, filial_id, start_time) VALUES (?, ?, ?)",
        (worker_id, filial_id, now.strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()

    # Superadminga xabar
    try:
        await msg.bot.send_message(
            SUPERADMIN_ID,
            f"🕒 Ishchi <b>{name}</b> ishni boshladi.\n📍 Filial ID: {filial_id}\n🕓 Vaqt: {now.strftime('%H:%M')}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Superadminga ish boshlash haqida yuborishda xato: {e}")


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer(
        "✅ Ishni tugatganingiz qayd etildi.\n📩 Iltimos, yakuniy hisobot yuboring:",
        reply_markup=confirm_end_work_menu()
    )
    worker_state[msg.from_user.id] = "waiting_for_end_report"


# === 📤 YAKUNIY HISOBOT YUBORISH ===
@router.message(F.text)
async def send_end_report(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_end_report":
        return

    conn = db.get_conn()
    cur = conn.cursor()
    worker = cur.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()

    if not worker:
        return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

    cur.execute("""
        INSERT INTO reports (worker_id, filial_id, text, created_at)
        VALUES (?, ?, ?, ?)
    """, (worker[0], worker[1], f"Yakuniy hisobot: {msg.text}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()

    try:
        await msg.bot.send_message(
            SUPERADMIN_ID,
            f"🏁 <b>{worker[2]}</b> ishni tugatdi.\n🧾 Hisobot: {msg.text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Superadminga yakuniy hisobot yuborishda xato: {e}")

    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi.", reply_markup=worker_menu())


# === 📷 TOZALASH RASMI ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    await msg.answer("📸 Iltimos, tozalash jarayoni rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_clean_photo"


@router.message(F.photo)
async def receive_clean_photo(msg: types.Message):
    state = worker_state.get(msg.from_user.id)
    if state not in ["waiting_for_clean_photo", "waiting_for_problem_photo"]:
        return

    file_id = msg.photo[-1].file_id
    conn = db.get_conn()
    cur = conn.cursor()
    worker = cur.execute("SELECT name FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()

    caption = "🧹 Tozalash rasmi" if state == "waiting_for_clean_photo" else "🚨 Muammo rasmi"
    try:
        await msg.bot.send_photo(
            SUPERADMIN_ID,
            photo=file_id,
            caption=f"{caption}\n👷 {worker[0]}\n🆔 {msg.from_user.id}"
        )
    except Exception as e:
        print(f"⚠️ Rasm yuborishda xato: {e}")

    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# === 📸 MUAMMO YUBORISH ===
@router.message(F.text == "📸 Muammo yuborish")
async def ask_problem_photo(msg: types.Message):
    await msg.answer("📸 Muammo rasmini yuboring (izohni captionga yozing):", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_problem_photo"


# === 💰 BONUS/JARIMALAR ===
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finance(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    worker = cur.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not worker:
        return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

    worker_id = worker[0]
    bonuses = cur.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=?", (worker_id,)).fetchall()
    fines = cur.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=?", (worker_id,)).fetchall()

    text = f"💰 <b>{worker[1]} uchun ma'lumotlar:</b>\n\n"
    if bonuses:
        text += "🎉 <b>Bonuslar:</b>\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]} ({b[2]})" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ <b>Jarimalar:</b>\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]} ({f[2]})" for f in fines])

    if not bonuses and not fines:
        text += "📭 Sizda hozircha bonus yoki jarima yo‘q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())
