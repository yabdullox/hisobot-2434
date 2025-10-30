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


# # ===============================
# # /start
# # ===============================
# @router.message(F.text == "/start")
# async def start_worker(message: Message):
#     await message.answer(
#         "👷 <b>Salom, ishchi!</b>\nHisobot tizimiga xush kelibsiz.\nQuyidagi menyudan tanlang 👇",
#         parse_mode="HTML",
#         reply_markup=get_worker_kb()
#     )


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

# ===============================
# 💰 Bonus / Jarimalarim
# ===============================
@router.message(F.text == "💰 Bonus / Jarimalarim")
async def show_bonus_menu(message: types.Message):
    """Foydalanuvchiga bonus/jarima tanlash menyusini chiqaradi."""
    from keyboards.worker_kb import get_bonus_kb
    await message.answer(
        "💰 Bonus yoki Jarimalar bo‘limini tanlang:",
        reply_markup=get_bonus_kb()
    )


@router.message(F.text == "📅 Bugungi")
async def show_today_bonus_fines(message: types.Message):
    """Foydalanuvchining bugungi bonus va jarimalarini ko‘rsatadi."""
    user_id = message.from_user.id
    today = date.today()

    bonuses = database.fetchall(
        "SELECT amount, reason FROM bonuses WHERE user_id=:u AND DATE(created_at)=:d",
        {"u": user_id, "d": today}
    )
    fines = database.fetchall(
        "SELECT amount, reason FROM fines WHERE user_id=:u AND DATE(created_at)=:d",
        {"u": user_id, "d": today}
    )

    text = "💰 <b>Bugungi Bonus / Jarimalaringiz:</b>\n\n"
    if bonuses:
        for b in bonuses:
            text += f"✅ +{b['amount']:,} so‘m — {b['reason']}\n"
    if fines:
        for f in fines:
            text += f"❌ -{f['amount']:,} so‘m — {f['reason']}\n"
    if not bonuses and not fines:
        text += "📭 Bugun bonus yoki jarima yo‘q."

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📋 Umumiy")
async def show_all_bonus_fines(message: types.Message):
    """Foydalanuvchining umumiy bonus/jarima tarixini chiqaradi."""
    user_id = message.from_user.id
    bonuses = database.fetchall(
        "SELECT amount, reason, created_at FROM bonuses WHERE user_id=:u ORDER BY created_at DESC LIMIT 10",
        {"u": user_id}
    )
    fines = database.fetchall(
        "SELECT amount, reason, created_at FROM fines WHERE user_id=:u ORDER BY created_at DESC LIMIT 10",
        {"u": user_id}
    )

    text = "📊 <b>So‘nggi 10 ta Bonus / Jarimalar:</b>\n\n"
    if bonuses:
        for b in bonuses:
            text += f"✅ {b['created_at'].strftime('%Y-%m-%d')} — +{b['amount']:,} so‘m ({b['reason']})\n"
    if fines:
        for f in fines:
            text += f"❌ {f['created_at'].strftime('%Y-%m-%d')} — -{f['amount']:,} so‘m ({f['reason']})\n"

    if not bonuses and not fines:
        text += "📭 Ma’lumotlar topilmadi."

    await message.answer(text, parse_mode="HTML")
    
@router.message(F.text == "⬅️ Orqaga")
async def back_to_main_worker_menu(message: types.Message):
    from keyboards.worker_kb import get_worker_kb  # to'g'ri import
    await message.answer(
        "🏠 Asosiy ishchi menyuga qaytdingiz:",
        reply_markup=get_worker_kb()
    )


# ===============================
# 📓 Eslatmalarim
# ===============================
@router.message(F.text == "📓 Eslatmalarim")
async def show_notes(message: types.Message):
    """Foydalanuvchining oxirgi 10 ta eslatmasini ko‘rsatadi."""
    user_id = message.from_user.id
    notes = database.fetchall(
        "SELECT text, created_at FROM notes WHERE telegram_id=:u ORDER BY created_at DESC LIMIT 10",
        {"u": user_id}
    )

    if not notes:
        await message.answer("📓 Sizda hali eslatmalar yo‘q.\n✏️ Yangi eslatma yozish uchun xabar yuboring.")
    else:
        text = "📒 <b>Sizning eslatmalaringiz:</b>\n\n"
        for n in notes:
            t = n['created_at'].strftime('%Y-%m-%d %H:%M')
            text += f"🕒 {t}\n📝 {n['text']}\n\n"
        await message.answer(text, parse_mode="HTML")

@router.message(F.text.regexp(r".+") & ~F.text.in_([
    "🕘 Ishni boshladim", "🏁 Ishni tugatdim",
    "🧹 Tozalash rasmi yuborish", "💬 Muammo yuborish",
    "🧾 Bugungi hisobotni yuborish", "💰 Bonus / Jarimalarim",
    "📓 Eslatmalarim", "⬅️ Menyuga qaytish",
    "📅 Bugungi", "📋 Umumiy", "⬅️ Orqaga"
]))
async def save_note(message: types.Message):
    """
    Eslatma funksiyasi endi faqat WORKER foydalanuvchilar uchun ishlaydi.
    Superadmin va Adminlar uchun bu handler hech narsa qilmaydi.
    """
    # 🔹 Foydalanuvchining roli kimligini tekshiramiz
    user = database.fetchone(
        "SELECT role FROM users WHERE telegram_id = :tid",
        {"tid": message.from_user.id}
    )

    # 🔹 Agar worker bo‘lmasa — chiqamiz, hech narsa qilmaymiz
    if not user or user.get("role") != "worker":
        return

    # 🔹 Faqat worker uchun ishlaydi:
    user_id = message.from_user.id
    text = message.text.strip()

    if not text:
        await message.answer("⚠️ Eslatma bo‘sh bo‘lishi mumkin emas.")
        return

    database.execute(
        "INSERT INTO notes (telegram_id, text) VALUES (:u, :t)",
        {"u": user_id, "t": text}
    )

    await message.answer("📝 Eslatma saqlandi (faqat sizga ko‘rinadi).")
