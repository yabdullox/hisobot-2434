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
# /start
# ===============================
@router.message(F.text == "/start")
async def start_worker(message: Message):
    await message.answer(
        "👷 <b>Salom, ishchi!</b>\nHisobot tizimiga xush kelibsiz.\nQuyidagi menyudan tanlang 👇",
        parse_mode="HTML",
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

    report_message = (
        f"🧾 <b>Yangi ishchi hisobot!</b>\n\n"
        f"👷 Ishchi: <b>{user['full_name']}</b>\n"
        f"🏢 Filial ID: <b>{user['branch_id']}</b>\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        f"📅 Sana: <b>{date_str}</b>\n"
        f"🕘 Vaqt: <b>{time_str}</b>\n\n"
        f"🧹 Hisobot matni:\n{text}"
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
# 💬 Muammo yuborish
# ===============================
@router.message(F.text == "💬 Muammo yuborish")
async def start_problem(message: Message, state: FSMContext):
    await message.answer("✏️ Muammo tafsilotlarini yozing:")
    await state.set_state(ProblemFSM.waiting_description)


@router.message(StateFilter(ProblemFSM.waiting_description))
async def receive_problem_text(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("📸 Agar surat yubormoqchi bo‘lsangiz, hozir yuboring.\nAgar kerak bo‘lmasa — ✅ <b>Tayyor</b> deb yozing.", parse_mode="HTML")
    await state.set_state(ProblemFSM.waiting_photo)


@router.message(StateFilter(ProblemFSM.waiting_photo), F.photo)
async def receive_problem_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    desc = data.get("description")
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    now = datetime.now()

    user = database.fetchone("SELECT full_name, branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})
    if not user:
        await message.answer("⚠️ Siz ro‘yxatdan o‘tmagansiz.")
        return

    msg = (
        f"⚠️ <b>Yangi muammo xabari!</b>\n\n"
        f"👷 Ishchi: <b>{user['full_name']}</b>\n"
        f"🏢 Filial ID: <b>{user['branch_id']}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📅 Sana: <b>{now.strftime('%Y-%m-%d')}</b>\n🕒 Vaqt: <b>{now.strftime('%H:%M:%S')}</b>\n\n"
        f"💬 Tavsif:\n{desc}"
    )

    for admin_id in [int(x.strip()) for x in os.getenv("SUPERADMIN_ID", str(SUPERADMIN_ID)).split(",")]:
        try:
            await message.bot.send_photo(admin_id, photo_id, caption=msg, parse_mode="HTML")
        except:
            pass

    await message.answer("✅ Muammo tafsilotlari va surat yuborildi. Rahmat!", parse_mode="HTML")
    await state.clear()


@router.message(StateFilter(ProblemFSM.waiting_photo), F.text)
async def finish_problem(message: Message, state: FSMContext):
    text = message.text.lower()
    if text in ["✅ tayyor", "tayyor", "done", "ok"]:
        data = await state.get_data()
        desc = data.get("description")
        user_id = message.from_user.id
        now = datetime.now()
        user = database.fetchone("SELECT full_name, branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})

        msg = (
            f"⚠️ <b>Yangi muammo xabari!</b>\n\n"
            f"👷 Ishchi: <b>{user['full_name']}</b>\n"
            f"🏢 Filial ID: <b>{user['branch_id']}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📅 Sana: <b>{now.strftime('%Y-%m-%d')}</b>\n🕒 Vaqt: <b>{now.strftime('%H:%M:%S')}</b>\n\n"
            f"💬 Tavsif:\n{desc}"
        )

        for admin_id in [int(x.strip()) for x in os.getenv("SUPERADMIN_ID", str(SUPERADMIN_ID)).split(",")]:
            try:
                await message.bot.send_message(admin_id, msg, parse_mode="HTML")
            except:
                pass

        await message.answer("✅ Muammo yuborildi, rahmat!", parse_mode="HTML")
        await state.clear()
    else:
        await message.answer("⚠️ Iltimos, '✅ Tayyor' deb yozing yoki surat yuboring.")


# ===============================
# ⬅️ Menyuga qaytish
# ===============================
@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_worker_kb())
