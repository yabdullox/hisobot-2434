from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date, time
from config import SUPERADMIN_ID, ADMIN_ID
import database
import os

router = Router()

# Vaqtinchalik holatlar uchun xotira (eslatmalar, muammolar va h.k.)
WORKER_STATE = {}

# ===============================
# 👷 /start komandasi
# ===============================
@router.message(F.text == "/start")
async def start_worker(message: Message):
    await message.answer(
        "👷 Salom, ishchi!\n"
        "Hisobot tizimiga xush kelibsiz.\n"
        "Quyidagi menyudan tanlang 👇",
        reply_markup=get_worker_kb()
    )


# ===============================
# 🕘 Ishni boshladim
# ===============================
@router.message(F.text == "🕘 Ishni boshladim")
async def start_work(message: Message):
    user_id = message.from_user.id
    now = datetime.now()
    today = now.date()
    start_time = now.strftime("%H:%M:%S")

    existing = database.fetchone(
        "SELECT id FROM reports WHERE user_id=:u AND date=:d",
        {"u": user_id, "d": today}
    )
    if existing:
        await message.answer("⚠️ Siz bugun ishni allaqachon boshlagansiz.")
        return

    database.execute("""
        INSERT INTO reports (user_id, date, start_time)
        VALUES (:u, :d, :t)
    """, {"u": user_id, "d": today, "t": start_time})

    # Avtomatik bonus/jarima logikasi
    ish_boshlash_vaqti = time(9, 0)
    farq_daqiqa = (datetime.combine(today, now.time()) -
                   datetime.combine(today, ish_boshlash_vaqti)).total_seconds() / 60

    worker = database.fetchone(
        "SELECT id, branch_id FROM users WHERE telegram_id=:t",
        {"t": user_id}
    )
    if not worker:
        await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")
        return

    if farq_daqiqa > 10:
        penalty = round((farq_daqiqa / 60) * 10000)
        database.execute("""
            INSERT INTO fines (user_id, branch_id, amount, reason, created_by, auto)
            VALUES (:u, :b, :a, :r, :c, TRUE)
        """, {
            "u": worker["id"],
            "b": worker["branch_id"],
            "a": penalty,
            "r": "Kech qolganligi uchun avtomatik jarima",
            "c": user_id
        })
        await message.answer(f"⚠️ Siz {farq_daqiqa:.0f} daqiqa kech keldingiz.\n❌ Jarima: {penalty:,} so‘m.")
    elif farq_daqiqa < 0:
        bonus = round((abs(farq_daqiqa) / 60) * 10000)
        database.execute("""
            INSERT INTO bonuses (user_id, branch_id, amount, reason, created_by, auto)
            VALUES (:u, :b, :a, :r, :c, TRUE)
        """, {
            "u": worker["id"],
            "b": worker["branch_id"],
            "a": bonus,
            "r": "Erta kelganligi uchun avtomatik bonus",
            "c": user_id
        })
        await message.answer(f"🌅 Siz {abs(farq_daqiqa):.0f} daqiqa erta keldingiz.\n✅ Bonus: {bonus:,} so‘m.")

    await message.answer(f"🕘 Ish boshlanish vaqti saqlandi: {start_time}")

    # Superadmin va adminlarga xabar yuborish
    try:
        await message.bot.send_message(SUPERADMIN_ID, f"👷 Ishchi {user_id} ishni boshladi ({start_time})")
        if ADMIN_ID:
            await message.bot.send_message(ADMIN_ID, f"👷 Ishchi {user_id} ishni boshladi ({start_time})")
    except Exception:
        pass


# ===============================
# 🏁 Ishni tugatdim
# ===============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: Message):
    user_id = message.from_user.id
    now = datetime.now()
    today = now.date()
    end_time = now.strftime("%H:%M:%S")

    report = database.fetchone(
        "SELECT id FROM reports WHERE user_id=:u AND date=:d",
        {"u": user_id, "d": today}
    )
    if not report:
        await message.answer("⚠️ Siz bugun ishni boshlamagansiz.")
        return

    database.execute("""
        UPDATE reports SET end_time=:t WHERE id=:id
    """, {"t": end_time, "id": report["id"]})

    await message.answer(
        f"🏁 Ish tugash vaqti saqlandi: {end_time}\n\n"
        "Endi '📤 Bugungi hisobotni yuboring' tugmasini bosing."
    )

    # Superadmin va adminlarga avtomatik xabar
    try:
        await message.bot.send_message(SUPERADMIN_ID, f"🏁 Ishchi {user_id} ishni tugatdi ({end_time})")
        if ADMIN_ID:
            await message.bot.send_message(ADMIN_ID, f"🏁 Ishchi {user_id} ishni tugatdi ({end_time})")
    except Exception:
        pass


# ===============================
# 💬 Muammo yuborish
# ===============================
@router.message(F.text == "💬 Muammo yuborish")
async def send_problem(message: Message):
    await message.answer("📷 Muammoning suratini yuboring yoki yozma tarzda kiriting.")
    WORKER_STATE[message.from_user.id] = {"awaiting_issue": True}


@router.message(F.photo)
async def receive_problem_photo(message: Message):
    state = WORKER_STATE.get(message.from_user.id)
    if state and state.get("awaiting_issue"):
        photo_id = message.photo[-1].file_id
        await message.bot.send_photo(SUPERADMIN_ID, photo_id, caption=f"⚠️ Muammo rasmi: {message.from_user.full_name}")
        if ADMIN_ID:
            await message.bot.send_photo(ADMIN_ID, photo_id, caption=f"⚠️ Muammo rasmi: {message.from_user.full_name}")
        await message.answer("✅ Muammo rasmi yuborildi.")
        WORKER_STATE[message.from_user.id] = {}


@router.message()
async def receive_problem_text(message: Message):
    state = WORKER_STATE.get(message.from_user.id)
    if state and state.get("awaiting_issue"):
        text = message.text
        caption = f"⚠️ Muammo:\n👷 {message.from_user.full_name}\n📝 {text}"
        await message.bot.send_message(SUPERADMIN_ID, caption)
        if ADMIN_ID:
            await message.bot.send_message(ADMIN_ID, caption)
        await message.answer("✅ Muammo yuborildi.")
        WORKER_STATE[message.from_user.id] = {}


# ===============================
# 🧹 Tozalash rasmi yuborish
# ===============================
@router.message(F.text == "🧹 Tozalash rasmi yuborish")
async def cleaning_request(message: Message):
    await message.answer("📸 Iltimos, tozalangan joyning rasmini yuboring.")


@router.message(F.photo & ~F.text)
async def save_cleaning_photo(message: Message):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    today = date.today()

    report = database.fetchone(
        "SELECT id FROM reports WHERE user_id=:u AND date=:d",
        {"u": user_id, "d": today}
    )
    if not report:
        await message.answer("⚠️ Avval '🕘 Ishni boshladim' tugmasini bosing.")
        return

    database.execute("""
        INSERT INTO cleaning_photos (user_id, report_id, file_id)
        VALUES (:u, :r, :f)
    """, {"u": user_id, "r": report["id"], "f": photo_id})

    await message.answer("✅ Tozalash rasmi saqlandi!")
    try:
        await message.bot.send_photo(SUPERADMIN_ID, photo_id, caption=f"🧹 Tozalash rasmi - {message.from_user.full_name}")
        if ADMIN_ID:
            await message.bot.send_photo(ADMIN_ID, photo_id, caption=f"🧹 Tozalash rasmi - {message.from_user.full_name}")
    except Exception:
        pass


# ===============================
# 📓 Eslatmalar (Notes)
# ===============================
@router.message(F.text == "📓 Eslatmalarim")
async def notes_menu(message: Message):
    tg_id = message.from_user.id
    notes = database.fetchall(
        "SELECT text, created_at FROM notes WHERE telegram_id=:tid ORDER BY id DESC LIMIT 10",
        {"tid": tg_id}
    )

    if not notes:
        await message.answer(
            "📓 Sizda hali eslatma yo‘q.\n\n📝 Yangi eslatma yozing:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🆕 Yangi eslatma yozish")],
                    [KeyboardButton(text="⬅️ Menyuga qaytish")]
                ],
                resize_keyboard=True
            )
        )
        return

    text = "📓 <b>Sizning so‘nggi 10 ta eslatmangiz:</b>\n\n"
    for note in notes:
        t = note["created_at"].split(" ")[0]
        text += f"🗓️ {t}\n📝 {note['text']}\n\n"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🆕 Yangi eslatma yozish")],
                [KeyboardButton(text="⬅️ Menyuga qaytish")]
            ],
            resize_keyboard=True
        )
    )


@router.message(F.text == "🆕 Yangi eslatma yozish")
async def add_note_prompt(message: Message):
    await message.answer("📝 Iltimos, eslatmani yozing:")
    WORKER_STATE[message.from_user.id] = {"awaiting_note": True}


@router.message()
async def save_note_if_needed(message: Message):
    tg_id = message.from_user.id
    state = WORKER_STATE.get(tg_id, {})

    if state.get("awaiting_note"):
        text = message.text.strip()
        if len(text) < 2:
            await message.answer("⚠️ Eslatma juda qisqa, qayta yozing.")
            return

        database.execute(
            "INSERT INTO notes (telegram_id, text) VALUES (:tid, :text)",
            {"tid": tg_id, "text": text}
        )
        await message.answer("✅ Eslatma saqlandi!", reply_markup=get_worker_kb())
        WORKER_STATE[tg_id] = {}


# ===============================
# ⬅️ Menyuga qaytish
# ===============================
@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_menu(message: Message):
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_worker_kb())


# ===============================
# Klaviatura
# ===============================
def get_worker_kb():
    kb = [
        [KeyboardButton(text="🕘 Ishni boshladim"), KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="🧹 Tozalash rasmi yuborish"), KeyboardButton(text="💬 Muammo yuborish")],
        [KeyboardButton(text="💰 Bonus/Jarimalarim"), KeyboardButton(text="📓 Eslatmalarim")],
        [KeyboardButton(text="⬅️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )
