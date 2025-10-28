import database
from aiogram import Router, F
from aiogram.types import Message, PhotoSize
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from datetime import datetime, time
from keyboards.worker_kb import get_worker_kb
from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime, timedelta, time
import pytz
import database
from aiogram import Router, F
from aiogram.types import Message
from datetime import datetime, date, time, timedelta
import database
router = Router()

router = Router()


# ===============================
# FSM holatlari
# ===============================
class ReportFSM(StatesGroup):
    text = State()

class CleaningFSM(StatesGroup):
    photo = State()

class ProblemFSM(StatesGroup):
    text = State()
    photo = State()


# ===============================
# START komandasi
# ===============================
@router.message(Command("start"))
async def start_worker(message: Message):
    await message.answer("👋 Ishchi panelga xush kelibsiz!", reply_markup=get_worker_kb())


# ===============================
# 🕘 Ishni boshladim
# ===============================

#
# 🕘 ISHNI BOSHLADIM
@router.message(F.text == "🕘 Ishni boshladim")
async def start_work(message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    # 00:00–05:00 oralig‘idagi vaqtni kechagi kun deb hisoblash
    if now.time() < time(5, 0):
        today = (now - timedelta(days=1)).date()
    else:
        today = now.date()

    start_time = now.strftime("%H:%M:%S")

    # Bugun uchun hisobot allaqachon bor-yo‘qligini tekshirish
    existing = database.fetchone("""
        SELECT id, start_time FROM reports
        WHERE user_id=:u AND date=:d
    """, {"u": user_id, "d": today})

    # Faqat haqiqatan yozilgan ish uchun ogohlantirish
    if existing and existing["start_time"]:
        await message.answer("⚠️ Siz bugun ishni allaqachon boshlagansiz.")
        return

    # Yangi hisobot qo‘shish
    if not existing:
        database.execute("""
            INSERT INTO reports (user_id, date, start_time)
            VALUES (:u, :d, :t)
        """, {"u": user_id, "d": today, "t": start_time})
    else:
        database.execute("""
            UPDATE reports SET start_time=:t WHERE id=:i
        """, {"t": start_time, "i": existing["id"]})

    # Foydalanuvchini bazadan olish
    worker = database.fetchone("""
        SELECT id, branch_id FROM users WHERE telegram_id=:t
    """, {"t": user_id})

    if not worker:
        await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")
        return

    # Ish boshlanishi 9:00 deb belgilaymiz
    ish_vaqti = time(9, 0)
    diff_minutes = (datetime.combine(today, now.time()) - datetime.combine(today, ish_vaqti)).total_seconds() / 60

    # BONUS yoki JARIMA hisoblash
    if diff_minutes > 10:
        penalty = round(diff_minutes / 60 * 10000)
        database.execute("""
            INSERT INTO fines (user_id, branch_id, amount, reason, created_by, auto)
            VALUES (:u, :b, :a, :r, :c, 1)
        """, {
            "u": worker["id"],
            "b": worker["branch_id"],
            "a": penalty,
            "r": "Kech kelganligi uchun avtomatik jarima",
            "c": user_id
        })
        await message.answer(f"⚠️ Siz {diff_minutes:.0f} daqiqa kech keldingiz.\n❌ Jarima: {penalty:,} so‘m.")
    elif diff_minutes < -5:
        bonus = round(abs(diff_minutes) / 60 * 10000)
        database.execute("""
            INSERT INTO bonuses (user_id, branch_id, amount, reason, created_by, auto)
            VALUES (:u, :b, :a, :r, :c, 1)
        """, {
            "u": worker["id"],
            "b": worker["branch_id"],
            "a": bonus,
            "r": "Erta kelganligi uchun avtomatik bonus",
            "c": user_id
        })
        await message.answer(f"🌅 Siz {abs(diff_minutes):.0f} daqiqa erta keldingiz.\n✅ Bonus: {bonus:,} so‘m.")

    await message.answer(f"🕘 Ish boshlanish vaqti saqlandi: {start_time}")
# ===============================
# 🏁 Ishni tugatdim
# ===============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: Message):
    user_id = message.from_user.id
    now = datetime.now()
    today = now.date()
    end_time = now.time().strftime("%H:%M:%S")

    report = database.fetchone("SELECT id FROM reports WHERE user_id=:u AND date=:d", {"u": user_id, "d": today})
    if not report:
        await message.answer("⚠️ Siz hali ishni boshlamagan ekansiz.")
        return

    database.execute("UPDATE reports SET end_time=:t WHERE user_id=:u AND date=:d", {"t": end_time, "u": user_id, "d": today})
    await message.answer(f"🏁 Ish tugash vaqti saqlandi: {end_time}")


# ===============================
# 🧾 Hisobot yuborish
# ===============================
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(message: Message, state: FSMContext):
    await state.set_state(ReportFSM.text)
    await message.answer("🧾 Iltimos, bugungi hisobotni yozib yuboring:")

@router.message(ReportFSM.text)
async def finish_report(message: Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id
    today = datetime.now().date()

    database.execute("""
        INSERT INTO reports (user_id, date, text)
        VALUES (:u, :d, :t)
        ON CONFLICT(user_id, date) DO UPDATE SET text=:t
    """, {"u": user_id, "d": today, "t": text})

    await message.answer("✅ Hisobot yuborildi.", reply_markup=get_worker_kb())
    await state.clear()


# ===============================
# 🧹 Tozalash rasmi yuborish
# ===============================
@router.message(F.text == "🧹 Tozalash rasmi yuborish")
async def ask_cleaning_photo(message: Message, state: FSMContext):
    await state.set_state(CleaningFSM.photo)
    await message.answer("📸 Tozalashdan keyingi rasmni yuboring:")

@router.message(CleaningFSM.photo, F.photo)
async def receive_cleaning_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    today = datetime.now().date()

    database.execute("""
        UPDATE reports SET cleaning_photo_id=:p WHERE user_id=:u AND date=:d
    """, {"p": photo_id, "u": user_id, "d": today})

    await message.answer("✅ Tozalash rasmi qabul qilindi.", reply_markup=get_worker_kb())
    await state.clear()


# ===============================
# 📷 Muammo yuborish
# ===============================
@router.message(F.text == "📷 Muammo yuborish")
async def start_problem(message: Message, state: FSMContext):
    await state.set_state(ProblemFSM.text)
    await message.answer("🧾 Muammo tafsilotini yozing:")

@router.message(ProblemFSM.text)
async def ask_problem_photo(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await state.set_state(ProblemFSM.photo)
    await message.answer("📸 Endi muammo rasmini yuboring:")

@router.message(ProblemFSM.photo, F.photo)
async def finish_problem(message: Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id
    worker = database.fetchone("SELECT id, branch_id FROM users WHERE telegram_id=:t", {"t": user_id})
    if not worker:
        await message.answer("❌ Siz tizimda topilmadingiz.")
        await state.clear()
        return

    database.execute("""
        INSERT INTO problems (user_id, branch_id, description, photo_file_id)
        VALUES (:u, :b, :d, :p)
    """, {"u": worker["id"], "b": worker["branch_id"], "d": data["text"], "p": photo_id})

    await message.answer("✅ Muammo qabul qilindi. Rahmat!", reply_markup=get_worker_kb())
    await state.clear()


# ===============================
# 💰 Bonus/Jarimalarim
# ===============================
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def my_fines_bonuses(message: Message):
    user_id = message.from_user.id
    today = datetime.now().date()

    bonuses = database.fetchall("SELECT amount, reason FROM bonuses WHERE created_at >= :d AND user_id IN (SELECT id FROM users WHERE telegram_id=:t)", {"d": today, "t": user_id})
    fines = database.fetchall("SELECT amount, reason FROM fines WHERE created_at >= :d AND user_id IN (SELECT id FROM users WHERE telegram_id=:t)", {"d": today, "t": user_id})

    text = "<b>💰 Bugungi bonus va jarimalaringiz:</b>\n\n"
    if bonuses:
        text += "✅ <b>Bonuslar:</b>\n"
        for b in bonuses:
            text += f"+{int(b['amount'])} so‘m — {b['reason']}\n"
    else:
        text += "✅ Bonuslar: yo‘q\n"

    if fines:
        text += "\n❌ <b>Jarimalar:</b>\n"
        for f in fines:
            text += f"-{int(f['amount'])} so‘m — {f['reason']}\n"
    else:
        text += "\n❌ Jarimalar: yo‘q\n"

    await message.answer(text, reply_markup=get_worker_kb())


# ===============================
# 🔙 Menyuga qaytish
# ===============================
@router.message(F.text == "🔙 Menyuga qaytish")
async def back_to_menu(message: Message):
    await message.answer("🏠 Asosiy menyu", reply_markup=get_worker_kb())
