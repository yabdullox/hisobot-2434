from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, date, time
from config import SUPERADMINS, ADMINS
import database
from keyboards.worker_kb import worker_menu, bonus_menu

router = Router()


# ===============================
# 👷 /start - ishchi menyusi
# ===============================
@router.message(Command("start"))
async def start_worker(message: types.Message):
    user = database.fetchone(
        "SELECT * FROM users WHERE telegram_id=:tid",
        {"tid": message.from_user.id}
    )
    if not user:
        return await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")
    await message.answer(
        f"👋 Salom, {user['full_name']}!\nHisobot tizimi ishga tayyor.",
        reply_markup=worker_menu
    )


# ===============================
# 🕘 Ishni boshladim
# ===============================
@router.message(F.text == "🕘 Ishni boshladim")
async def start_work(message: types.Message):
    user_id = message.from_user.id
    now = datetime.now()
    today = now.date()
    start_time = now.strftime("%H:%M:%S")

    # Tekshir: bugun boshlaganmi
    existing = database.fetchone(
        "SELECT id FROM reports WHERE user_id=:u AND date=:d",
        {"u": user_id, "d": today}
    )
    if existing:
        await message.answer("⚠️ Siz bugun ishni allaqachon boshlagansiz.")
        return

    # Hisobot qo‘shish
    database.execute("""
        INSERT INTO reports (user_id, date, start_time)
        VALUES (:u, :d, :t)
    """, {"u": user_id, "d": today, "t": start_time})

    # Ishchi ma’lumoti
    worker = database.fetchone(
        "SELECT id, full_name, branch_id FROM users WHERE telegram_id=:t",
        {"t": user_id}
    )
    if not worker:
        await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")
        return

    # Kech / erta logika
    ish_boshlash_vaqti = time(9, 0)
    farq_daqiqa = (datetime.combine(today, now.time()) -
                   datetime.combine(today, ish_boshlash_vaqti)).total_seconds() / 60

    text = ""
    if farq_daqiqa > 10:
        penalty = round((farq_daqiqa / 60) * 10000)
        database.execute("""
            INSERT INTO fines (user_id, branch_id, amount, reason, created_by, auto)
            VALUES (:u, :b, :a, :r, :c, TRUE)
        """, {
            "u": worker["id"],
            "b": worker["branch_id"],
            "a": penalty,
            "r": f"{farq_daqiqa:.0f} daqiqa kech kelgan",
            "c": user_id
        })
        text = f"⚠️ {farq_daqiqa:.0f} daqiqa kech kelgan. Jarima: -{penalty:,} so‘m"
    elif farq_daqiqa < 0:
        bonus = round((abs(farq_daqiqa) / 60) * 10000)
        database.execute("""
            INSERT INTO bonuses (user_id, branch_id, amount, reason, created_by, auto)
            VALUES (:u, :b, :a, :r, :c, TRUE)
        """, {
            "u": worker["id"],
            "b": worker["branch_id"],
            "a": bonus,
            "r": f"{abs(farq_daqiqa):.0f} daqiqa erta kelgan",
            "c": user_id
        })
        text = f"🌅 {abs(farq_daqiqa):.0f} daqiqa erta kelgan. Bonus: +{bonus:,} so‘m"
    else:
        text = "🕓 Ishni o‘z vaqtida boshladi."

    await message.answer(f"{text}\n🕘 Ish boshlanish vaqti: {start_time}")

    # Adminlarga xabar
    info = (
        f"🧍‍♂️ Ishchi ishni boshladi\n"
        f"👤 {worker['full_name']}\n"
        f"🏢 Filial ID: {worker['branch_id']}\n"
        f"📅 Sana: {today}\n"
        f"⏰ {start_time}\n\n{text}"
    )
    for admin in SUPERADMINS + ADMINS:
        try:
            await message.bot.send_message(admin, info)
        except:
            pass


# ===============================
# 🏁 Ishni tugatdim
# ===============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: types.Message):
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

    # Adminlarga xabar
    worker = database.fetchone(
        "SELECT full_name, branch_id FROM users WHERE telegram_id=:t",
        {"t": user_id}
    )
    info = (
        f"🏁 Ishchi ishni tugatdi\n"
        f"👤 {worker['full_name']}\n"
        f"🏢 Filial ID: {worker['branch_id']}\n"
        f"📅 Sana: {today}\n"
        f"⏰ Tugash: {end_time}"
    )
    for admin in SUPERADMINS + ADMINS:
        try:
            await message.bot.send_message(admin, info)
        except:
            pass


# ===============================
# 🧾 Hisobot yuborish
# ===============================
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report(message: types.Message, state: FSMContext):
    await message.answer("✍️ Hisobot matnini yuboring:")
    await state.set_state("waiting_report")


@router.message(F.text, F.state == "waiting_report")
async def receive_report(message: types.Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id
    today = date.today()

    worker = database.fetchone(
        "SELECT id, full_name, branch_id FROM users WHERE telegram_id=:t",
        {"t": user_id}
    )

    database.execute("""
        UPDATE reports SET text=:t WHERE user_id=:u AND date=:d
    """, {"t": text, "u": user_id, "d": today})

    await message.answer("✅ Hisobot saqlandi.", reply_markup=worker_menu)
    await state.clear()

    info = (
        f"🧾 Yangi hisobot\n"
        f"👤 {worker['full_name']}\n"
        f"🏢 Filial ID: {worker['branch_id']}\n"
        f"📅 Sana: {today}\n"
        f"🕓 Vaqt: {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"✍️ Hisobot:\n{text}"
    )
    for admin in SUPERADMINS + ADMINS:
        try:
            await message.bot.send_message(admin, info)
        except:
            pass


# ===============================
# 📸 Tozalash rasmi yuborish
# ===============================
@router.message(F.text == "📸 Tozalash rasmi yuborish")
async def cleaning_photo_request(message: types.Message, state: FSMContext):
    await message.answer("📷 Tozalash rasmini yuboring:")
    await state.set_state("waiting_clean_photo")


@router.message(F.photo, F.state == "waiting_clean_photo")
async def cleaning_photo_receive(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    today = date.today()

    report = database.fetchone(
        "SELECT id FROM reports WHERE user_id=:u AND date=:d",
        {"u": user_id, "d": today}
    )
    if not report:
        await message.answer("⚠️ Avval ishni boshlang.")
        return

    database.execute("""
        INSERT INTO cleaning_photos (user_id, report_id, file_id)
        VALUES (:u, :r, :f)
    """, {"u": user_id, "r": report["id"], "f": photo_id})

    await message.answer("✅ Tozalash rasmi saqlandi.", reply_markup=worker_menu)
    await state.clear()

    for admin in SUPERADMINS + ADMINS:
        try:
            await message.bot.send_photo(admin, photo=photo_id, caption=f"🧹 Tozalash rasmi\n👤 Ishchi ID: {user_id}")
        except:
            pass


# ===============================
# 💬 Muammo yuborish
# ===============================
@router.message(F.text == "💬 Muammo yuborish")
async def problem_request(message: types.Message, state: FSMContext):
    await message.answer("📷 Muammo rasmini yuboring yoki izoh yozing:")
    await state.set_state("waiting_problem")


@router.message(F.photo, F.state == "waiting_problem")
async def problem_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id

    for admin in SUPERADMINS + ADMINS:
        try:
            await message.bot.send_photo(admin, photo=photo_id, caption=f"⚠️ Muammo xabari\n👤 Ishchi ID: {user_id}")
        except:
            pass

    await message.answer("⚠️ Muammo yuborildi.", reply_markup=worker_menu)
    await state.clear()


# ===============================
# 💰 Bonus/Jarimalarim
# ===============================
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def bonus_menu_open(message: types.Message):
    await message.answer("Tanlang:", reply_markup=bonus_menu)


@router.callback_query(F.data == "bonus_today")
async def bonus_today(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    today = date.today()

    bonuses = database.fetchall("SELECT amount FROM bonuses WHERE user_id=:u AND DATE(created_at)=:d", {"u": user_id, "d": today})
    fines = database.fetchall("SELECT amount FROM fines WHERE user_id=:u AND DATE(created_at)=:d", {"u": user_id, "d": today})

    total_bonus = sum(b['amount'] for b in bonuses) if bonuses else 0
    total_fine = sum(f['amount'] for f in fines) if fines else 0

    await callback.message.edit_text(
        f"📅 Bugungi natijalar:\n\n💰 Bonuslar: {total_bonus:,} so‘m\n💸 Jarimalar: {total_fine:,} so‘m",
        reply_markup=bonus_menu
    )


@router.callback_query(F.data == "bonus_all")
async def bonus_all(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    bonuses = database.fetchall("SELECT amount FROM bonuses WHERE user_id=:u", {"u": user_id})
    fines = database.fetchall("SELECT amount FROM fines WHERE user_id=:u", {"u": user_id})

    total_bonus = sum(b['amount'] for b in bonuses) if bonuses else 0
    total_fine = sum(f['amount'] for f in fines) if fines else 0

    await callback.message.edit_text(
        f"📊 Umumiy natijalar:\n\n💰 Bonuslar: {total_bonus:,} so‘m\n💸 Jarimalar: {total_fine:,} so‘m",
        reply_markup=bonus_menu
    )
