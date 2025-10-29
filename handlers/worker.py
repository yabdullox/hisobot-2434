from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from datetime import datetime, date, time
from config import SUPERADMIN_ID, ADMIN_ID
import os
import database

router = Router()

# ===============================
# 👷 Ishchini /start komandasi
# ===============================
@router.message(F.text == "/start")
async def start_worker(message: Message):
    await message.answer(
        "👷 Salom, ishchi!\n"
        "Hisobot tizimiga xush kelibsiz.\n"
        "Quyidagi menyudan tanlang 👇",
        reply_markup=None
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

    # Superadmin va adminlarga xabar yuborish (agar kerak bo‘lsa)
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

    await message.answer(f"🏁 Ish tugash vaqti saqlandi: {end_time}")

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


# ===============================
# 📸 Tozalash rasmi yuborish
# ===============================
@router.message(F.photo)
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


# ===============================
# ⬅️ Menyuga qaytish
# ===============================
@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_menu(message: Message):
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=None)
