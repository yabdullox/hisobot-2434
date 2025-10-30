from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date, time
from config import SUPERADMIN_ID, ADMIN_ID
import database
import os

from keyboards.worker_kb import get_worker_kb, get_bonus_kb

router = Router()

# === FSM holatlar ===
class ReportState(StatesGroup):
    waiting_for_report = State()

class ProblemFSM(StatesGroup):
    waiting_description = State()
    waiting_photo = State()


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

    # ✅ branch_id ni user jadvalidan olish
    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})
    branch_id = user["branch_id"] if user else None

    # ✅ branch_id bilan birga saqlash
    database.execute("""
        INSERT INTO reports (user_id, branch_id, date, start_time)
        VALUES (:u, :b, :d, :t)
    """, {"u": user_id, "b": branch_id, "d": today, "t": start_time})

    # Bonus / jarima
    ish_boshlash_vaqti = time(9, 0)
    farq_daqiqa = (datetime.combine(today, now.time()) - datetime.combine(today, ish_boshlash_vaqti)).total_seconds() / 60

    if farq_daqiqa > 10:
        penalty = round((farq_daqiqa / 60) * 10000)
        database.execute("""
            INSERT INTO fines (user_id, amount, reason, created_by, auto)
            VALUES (:u, :a, :r, :c, TRUE)
        """, {"u": user_id, "a": penalty, "r": "Kech qolganligi uchun avtomatik jarima", "c": user_id})
        await message.answer(f"⚠️ Siz {farq_daqiqa:.0f} daqiqa kech keldingiz.\n❌ Jarima: {penalty:,} so‘m.")
    elif farq_daqiqa < 0:
        bonus = round((abs(farq_daqiqa) / 60) * 10000)
        database.execute("""
            INSERT INTO bonuses (user_id, amount, reason, created_by, auto)
            VALUES (:u, :a, :r, :c, TRUE)
        """, {"u": user_id, "a": bonus, "r": "Erta kelganligi uchun avtomatik bonus", "c": user_id})
        await message.answer(f"🌅 Siz {abs(farq_daqiqa):.0f} daqiqa erta keldingiz.\n✅ Bonus: {bonus:,} so‘m.")

    await message.answer(f"🕘 Ish boshlanish vaqti saqlandi: {start_time}")

    # Superadminlarga xabar
    admins = [int(x.strip()) for x in os.getenv("SUPERADMIN_ID", str(SUPERADMIN_ID)).split(",")]
    for admin_id in admins:
        try:
            await message.bot.send_message(admin_id, f"👷 {message.from_user.full_name} ({user_id}) ishni boshladi ({start_time})")
        except:
            pass


# ===============================
# 🏁 Ishni tugatdim
# ===============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: Message):
    user_id = message.from_user.id
    now = datetime.now()
    time_str = now.strftime("%H:%M:%S")

    database.execute(
        "UPDATE reports SET end_time=:t WHERE user_id=:u AND date=:d",
        {"t": time_str, "u": user_id, "d": date.today()}
    )

    await message.answer(
        f"🏁 Ish tugash vaqti saqlandi: <b>{time_str}</b>\n\n"
        "Endi 🧾 <b>Bugungi hisobotni yuboring</b> tugmasini bosing.",
        parse_mode="HTML"
    )


# ===============================
# 🧾 Bugungi hisobot
# ===============================
@router.message(F.text == "🧾 Bugungi hisobotni yuborish")
async def ask_report_text(message: Message, state: FSMContext):
    await message.answer("✍️ Hisobotingizni matn shaklida yuboring:")
    await state.set_state(ReportState.waiting_for_report)


@router.message(StateFilter(ReportState.waiting_for_report))
async def receive_report(message: Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text
    now = datetime.now()

    user = database.fetchone("SELECT full_name, branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})
    if not user:
        await message.answer("⚠️ Siz ro‘yxatdan o‘tmagansiz.")
        return

    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # ✅ hisobotni saqlab qo'yamiz (filial bilan)
    database.execute("""
        UPDATE reports 
        SET text=:t 
        WHERE user_id=:u AND date=:d
    """, {"t": text, "u": user_id, "d": date_str})

    report_message = (
        f"🧾 <b>Yangi ishchi hisobot!</b>\n\n"
        f"👷 Ishchi: <b>{user['full_name']}</b>\n"
        f"🏢 Filial ID: <b>{user['branch_id']}</b>\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        f"📅 Sana: <b>{date_str}</b>\n"
        f"🕘 Vaqt: <b>{time_str}</b>\n\n"
        f"🧾 Hisobot matni:\n{text}"
    )

    admins = [int(x.strip()) for x in os.getenv("SUPERADMIN_ID", str(SUPERADMIN_ID)).split(",")]
    for admin_id in admins:
        try:
            await message.bot.send_message(admin_id, report_message, parse_mode="HTML")
        except Exception as e:
            print(f"⚠️ Hisobot yuborishda xato: {e}")

    await message.answer("✅ Hisobotingiz yuborildi, rahmat!", parse_mode="HTML")
    await state.clear()


# ===============================
# ⬅️ Orqaga
# ===============================
@router.message(F.text == "⬅️ Orqaga")
async def back_to_main_worker_menu(message: types.Message):
    await message.answer("🏠 Asosiy ishchi menyuga qaytdingiz:", reply_markup=get_worker_kb())



# =====================================
# 💰 BONUS / JARIMALAR BO‘LIMI
# =====================================
@router.message(F.text == "💰 Bonus / Jarimalarim")
async def open_bonus_menu(message: types.Message):
    """Ishchi bonus/jarimalar menyusini ochish."""
    await message.answer(
        "💰 Bonus yoki jarimalar bo‘limini tanlang:",
        reply_markup=get_bonus_kb()
    )


# =====================================
# 📅 BUGUNGI BONUS/JARIMALAR
# =====================================
@router.message(F.text == "📅 Bugungi")
async def show_today_bonus(message: types.Message):
    """Bugungi bonus va jarimalarni ko‘rsatish."""
    uz_tz = pytz.timezone("Asia/Tashkent")
    today = datetime.now(uz_tz).date()
    user_id = message.from_user.id

    bonuses = database.fetchall("""
        SELECT amount, reason, created_at
        FROM bonuses
        WHERE user_id = :uid AND DATE(created_at) = :today
        ORDER BY created_at DESC
    """, {"uid": user_id, "today": today})

    fines = database.fetchall("""
        SELECT amount, reason, created_at
        FROM fines
        WHERE user_id = :uid AND DATE(created_at) = :today
        ORDER BY created_at DESC
    """, {"uid": user_id, "today": today})

    text = f"📅 <b>Bugungi ({today}) bonus va jarimalar:</b>\n\n"

    if not bonuses and not fines:
        text += "📭 Bugun sizda bonus yoki jarima yozuvlari yo‘q."
    else:
        if bonuses:
            text += "✅ <b>Bonuslar:</b>\n"
            for b in bonuses:
                text += f"➕ {b['amount']:,} so‘m — {b['reason']} ({b['created_at']})\n"
            text += "\n"
        if fines:
            text += "❌ <b>Jarimalar:</b>\n"
            for f in fines:
                text += f"➖ {f['amount']:,} so‘m — {f['reason']} ({f['created_at']})\n"

    await message.answer(text, parse_mode="HTML")


# =====================================
# 📋 UMUMIY BONUS/JARIMALAR
# =====================================
@router.message(F.text == "📋 Umumiy")
async def show_all_bonus(message: types.Message):
    """Umumiy bonus va jarimalarni ko‘rsatish."""
    user_id = message.from_user.id

    bonuses = database.fetchall("""
        SELECT amount, reason, created_at
        FROM bonuses
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT 30
    """, {"uid": user_id})

    fines = database.fetchall("""
        SELECT amount, reason, created_at
        FROM fines
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT 30
    """, {"uid": user_id})

    text = "📋 <b>Umumiy bonus va jarimalar (so‘nggi 30 ta yozuv):</b>\n\n"

    if not bonuses and not fines:
        text += "📭 Hozircha bonus yoki jarimalar mavjud emas."
    else:
        if bonuses:
            text += "✅ <b>Bonuslar:</b>\n"
            for b in bonuses:
                text += f"➕ {b['amount']:,} so‘m — {b['reason']} ({b['created_at']})\n"
            text += "\n"
        if fines:
            text += "❌ <b>Jarimalar:</b>\n"
            for f in fines:
                text += f"➖ {f['amount']:,} so‘m — {f['reason']} ({f['created_at']})\n"

    await message.answer(text, parse_mode="HTML")


# =====================================
# ⬅️ ORQAGA — ASOSIY ISHCHI MENYUGA QAYTISH
# =====================================
@router.message(F.text == "⬅️ Orqaga")
async def back_to_worker_menu(message: types.Message):
    """Asosiy ishchi menyusiga qaytish."""
    await message.answer(
        "🏠 Asosiy menyuga qaytdingiz.",
        reply_markup=get_worker_kb()
    )

# ===============================
# 📓 Eslatma (faqat worker uchun)
# ===============================
@router.message(F.text.regexp(r".+") & ~F.text.in_([
    "🕘 Ishni boshladim", "🏁 Ishni tugatdim",
    "🧹 Tozalash rasmi yuborish", "💬 Muammo yuborish",
    "🧾 Bugungi hisobotni yuborish", "💰 Bonus / Jarimalarim",
    "📓 Eslatmalarim", "⬅️ Menyuga qaytish",
    "📅 Bugungi", "📋 Umumiy", "⬅️ Orqaga"
]))
async def save_note(message: types.Message):
    """Eslatma funksiyasi endi faqat WORKER foydalanuvchilar uchun ishlaydi."""
    user = database.fetchone("SELECT role FROM users WHERE telegram_id = :tid", {"tid": message.from_user.id})
    if not user or user.get("role") != "worker":
        return

    text = message.text.strip()
    if not text:
        await message.answer("⚠️ Eslatma bo‘sh bo‘lishi mumkin emas.")
        return

    database.execute("INSERT INTO notes (telegram_id, text) VALUES (:u, :t)",
                     {"u": message.from_user.id, "t": text})
    await message.answer("📝 Eslatma saqlandi (faqat sizga ko‘rinadi).")
