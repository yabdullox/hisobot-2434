from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from datetime import datetime, date, time
from aiogram import Router, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime, date, time
from config import SUPERADMIN_ID, ADMIN_ID
import database

import database
import os

router = Router()


class ProblemFSM(StatesGroup):
    waiting_description = State()
    waiting_photo = State()

# ===============================
# /start
# ===============================
@router.message(F.text == "/start")
async def start_worker(message: types.Message):
    await message.answer(
        "👷 Salom, Ishchi!\nHisobot tizimi ishga tayyor.\nQuyidagi menyudan tanlang 👇",
        reply_markup=get_worker_kb()
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

    # Bonus / jarima logikasi
    ish_boshlash_vaqti = time(9, 0)
    farq_daqiqa = (datetime.combine(today, now.time()) - datetime.combine(today, ish_boshlash_vaqti)).total_seconds() / 60

    if farq_daqiqa > 10:
        penalty = round((farq_daqiqa / 60) * 10000)
        database.execute("""
            INSERT INTO fines (user_id, amount, reason, created_by, auto)
            VALUES (:u, :a, :r, :c, TRUE)
        """, {
            "u": user_id,
            "a": penalty,
            "r": "Kech qolganligi uchun avtomatik jarima",
            "c": user_id
        })
        await message.answer(f"⚠️ Siz {farq_daqiqa:.0f} daqiqa kech keldingiz.\n❌ Jarima: {penalty:,} so‘m.")
    elif farq_daqiqa < 0:
        bonus = round((abs(farq_daqiqa) / 60) * 10000)
        database.execute("""
            INSERT INTO bonuses (user_id, amount, reason, created_by, auto)
            VALUES (:u, :a, :r, :c, TRUE)
        """, {
            "u": user_id,
            "a": bonus,
            "r": "Erta kelganligi uchun avtomatik bonus",
            "c": user_id
        })
        await message.answer(f"🌅 Siz {abs(farq_daqiqa):.0f} daqiqa erta keldingiz.\n✅ Bonus: {bonus:,} so‘m.")

    await message.answer(f"🕘 Ish boshlanish vaqti saqlandi: {start_time}")

    # Superadmin/Adminlarga xabar
    try:
        await message.bot.send_message(SUPERADMIN_ID, f"👷 Ishchi {message.from_user.full_name} ({user_id}) ishni boshladi ({start_time})")
        if ADMIN_ID:
            await message.bot.send_message(ADMIN_ID, f"👷 Ishchi {message.from_user.full_name} ({user_id}) ishni boshladi ({start_time})")
    except Exception:
        pass


# ===============================
# 🏁 Ishni tugatdim
# ===============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: types.Message):
    user_id = message.from_user.id
    user = database.fetchone("SELECT * FROM users WHERE telegram_id = %s", (user_id,))

    if not user:
        await message.answer("⚠️ Siz ro‘yxatdan o‘tmagansiz.")
        return

    # Sana va vaqt
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Tugash vaqtini bazaga saqlaymiz
    database.query("UPDATE users SET end_time=%s WHERE telegram_id=%s", (time_str, user_id))

    await message.answer(f"🏁 Ish tugash vaqti saqlandi: <b>{time_str}</b>\n\n"
                         "Endi 🧾 <b>Bugungi hisobotni yuboring</b> tugmasini bosing.",
                         parse_mode="HTML")


# Bugungi hisobotni yuborish
@router.message(F.text == "🧾 Bugungi hisobotni yuborish")
async def send_daily_report(message: types.Message):
    user_id = message.from_user.id
    user = database.fetchone("SELECT * FROM users WHERE telegram_id = %s", (user_id,))

    if not user:
        await message.answer("⚠️ Siz ro‘yxatdan o‘tmagansiz.")
        return

    await message.answer("🧾 Hisobotingizni yuboring (matn shaklida):")
    await message.bot.send_message(user_id, "✍️ Hisobot matnini kiriting:")
    await message.bot.set_state(user_id, "waiting_for_report")


# Foydalanuvchi hisobot matnini yuborganda
@router.message(state="waiting_for_report")
async def receive_report(message: types.Message, state):
    report_text = message.text
    user_id = message.from_user.id
    user = database.fetchone("SELECT * FROM users WHERE telegram_id = %s", (user_id,))

    if not user:
        await message.answer("⚠️ Siz ro‘yxatdan o‘tmagansiz.")
        return

    full_name = user["fullname"]
    branch = user["branch"]
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Hisobotni Superadmin (yoki Admin)ga yuboramiz
    report_message = (
        f"🧾 <b>Yangi ishchi hisobot!</b>\n\n"
        f"👷 Ishchi: <b>{full_name}</b>\n"
        f"🏢 Filial: <b>{branch}</b>\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
        f"🕒 Sana: <b>{date_str}</b>\n"
        f"🕘 Hisobot yuborilgan vaqt: <b>{time_str}</b>\n\n"
        f"🧹 Hisobot matni:\n{report_text}"
    )

    await message.bot.send_message(SUPERADMIN_ID, report_message, parse_mode="HTML")
    await message.answer("✅ Hisobotingiz yuborildi, rahmat!", parse_mode="HTML")
    await state.clear()
# ===============================
# 💬 Muammo yuborish
# ===============================
@router.message(F.text == "💬 Muammo yuborish")
async def send_problem(message: Message, state: FSMContext):
    await state.set_state(ProblemFSM.waiting_description)
    await message.answer(
        "� Muammoni batafsil yozib yuboring. Agar kerak bo'lsa, keyin surat ham yuborishingiz mumkin."
    )


@router.message(ProblemFSM.waiting_description, F.text)
async def handle_problem_text(message: Message, state: FSMContext):
    description = message.text.strip()
    if not description:
        await message.answer("❗️ Muammo matni bo'sh. Iltimos, yana kiriting.")
        return

    user_id = message.from_user.id
    worker = database.fetchone("SELECT id, branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})
    if not worker:
        await state.clear()
        await message.answer("❌ Siz tizimda ro'yxatdan o'tmagansiz.")
        return

    report = database.fetchone(
        "SELECT id FROM reports WHERE user_id=:uid AND date=:d",
        {"uid": user_id, "d": date.today()},
    )

    problem_id = database.execute_returning(
        """
        INSERT INTO problems (user_id, branch_id, report_id, description)
        VALUES (:u, :b, :r, :descr)
        RETURNING id
        """,
        {
            "u": user_id,
            "b": worker["branch_id"],
            "r": report["id"] if report else None,
            "descr": description,
        },
    )

    if problem_id is None:
        last_row = database.fetchone(
            "SELECT id FROM problems WHERE user_id=:u ORDER BY id DESC LIMIT 1",
            {"u": user_id},
        )
        problem_id = last_row["id"] if last_row else None

    await state.update_data(problem_id=problem_id)
    await state.set_state(ProblemFSM.waiting_photo)
    await message.answer(
        "✅ Muammo matni saqlandi. Agar surat yubormoqchi bo'lsangiz, hozir jo'nating."
        " Surat kerak bo'lmasa, '✅ Tayyor' deb yozing."
    )


@router.message(ProblemFSM.waiting_photo, F.photo)
async def handle_problem_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    problem_id = data.get("problem_id")
    if not problem_id:
        await message.answer("⚠️ Avval muammo matnini yuboring.")
        return

    photo_id = message.photo[-1].file_id
    database.execute(
        "UPDATE problems SET photo_file_id=:photo WHERE id=:pid",
        {"photo": photo_id, "pid": problem_id},
    )

    await state.clear()
    await message.answer("📸 Muammo surati qabul qilindi. Rahmat!")


@router.message(ProblemFSM.waiting_photo, F.text)
async def finalize_problem(message: Message, state: FSMContext):
    text_content = message.text.strip()
    data = await state.get_data()
    problem_id = data.get("problem_id")

    if not problem_id:
        await state.clear()
        await message.answer("⚠️ Muammo holati topilmadi. Iltimos, qayta urinib ko'ring.")
        return

    if text_content.lower() in {"✅ tayyor", "tayyor", "done", "ok"}:
        await state.clear()
        await message.answer("✅ Muammo qabul qilindi. Rahmat!")
        return

    database.execute(
        """
        UPDATE problems
        SET description = COALESCE(description, '') || '\n' || :extra
        WHERE id = :pid
        """,
        {"extra": text_content, "pid": problem_id},
    )

    await message.answer(
        "📝 Qo'shimcha ma'lumot saqlandi. Surat yubormoqchi bo'lsangiz, davom eting yoki '✅ Tayyor' deb yozing."
    )

    # ✅ Hisobotni bazaga saqlash (agar add_report funksiyasi bo'lsa)
    try:
        add_report(telegram_id, now, "Bugungi hisobot yuborildi.")
    except Exception as e:
        print(f"Hisobot saqlashda xatolik: {e}")

    # ✅ Superadmin yoki filial adminiga xabar yuborish
    text = (
        f"📬 <b>Yangi hisobot</b>\n"
        f"👤 Ishchi: {message.from_user.full_name}\n"
        f"🆔 ID: <code>{telegram_id}</code>\n"
        f"📅 Sana: {now}"
    )

    # Agar SUPPERADMIN_ID ro‘yxat ko‘rinishida bo‘lsa
    from config import SUPERADMIN_ID
    admins = [int(x.strip()) for x in SUPERADMIN_ID.split(",")]
    for admin in admins:
        try:
            await message.bot.send_message(admin, text, parse_mode="HTML")
        except:
            pass

    # ✅ Ishchiga tasdiq
    await message.answer(
        "✅ Hisobotingiz yuborildi!\nRahmat, bugungi ish natijalari tizimda saqlandi.",
        reply_markup=get_worker_kb()
    )

# ===============================
# 📸 Tozalash rasmi yuborish
# ===============================
@router.message(F.text == "🧹 Tozalash rasmi yuborish")
async def ask_photo(message: types.Message):
    await message.answer("📷 Iltimos, tozalangan joyning rasmini yuboring.")


@router.message(F.photo)
async def save_cleaning_photo(message: Message, state: FSMContext):
    if await state.get_state() == ProblemFSM.waiting_photo.state:
        # Bu handlerga tushmasligi kerak, biroq xavfsizlik uchun tekshiruv
        return

    user_id = message.from_user.id
    today = date.today()
    photo_id = message.photo[-1].file_id

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

    await message.answer("✅ Tozalash rasmi saqlandi! Rahmat.")

    # Superadmin va adminlarga yuboriladi
    try:
        await message.bot.send_photo(SUPERADMIN_ID, photo_id, caption=f"🧹 Ishchi {message.from_user.full_name} tozalash rasmini yubordi.")
        if ADMIN_ID:
            await message.bot.send_photo(ADMIN_ID, photo_id, caption=f"🧹 Ishchi {message.from_user.full_name} tozalash rasmini yubordi.")
    except Exception:
        pass


# ===============================
# 💬 Muammo yuborish
# ===============================
@router.message(F.text == "💬 Muammo yuborish")
async def send_problem(message: types.Message):
    await message.answer("✏️ Muammo tafsilotlarini yozing. Agar kerak bo‘lsa, rasm ham yuborishingiz mumkin.")


@router.message(F.text.regexp(r".+") & ~F.text.in_(["🕘 Ishni boshladim", "🏁 Ishni tugatdim", "🧹 Tozalash rasmi yuborish", "💰 Bonus/Jarimalarim", "📓 Eslatmalarim"]))
async def handle_problem_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    database.execute("""
        INSERT INTO problems (user_id, text, created_at)
        VALUES (:u, :t, CURRENT_TIMESTAMP)
    """, {"u": user_id, "t": text})

    await message.answer("📩 Muammo matni saqlandi va yuborildi.")

    try:
        await message.bot.send_message(SUPERADMIN_ID, f"⚠️ Ishchidan muammo xabari:\n\n{text}")
        if ADMIN_ID:
            await message.bot.send_message(ADMIN_ID, f"⚠️ Ishchidan muammo xabari:\n\n{text}")
    except Exception:
        pass


# ===============================
# 💰 Bonus / Jarimalar
# ===============================
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_bonus_menu(message: types.Message):
    await message.answer("💰 Bonus yoki jarimalar hisobotini tanlang:", reply_markup=get_bonus_kb())


@router.message(F.text == "📅 Bugungi")
async def show_today_bonus_fines(message: types.Message):
    user_id = message.from_user.id
    today = date.today()

    bonuses = database.fetchall("SELECT * FROM bonuses WHERE user_id=:u AND DATE(created_at)=:d", {"u": user_id, "d": today})
    fines = database.fetchall("SELECT * FROM fines WHERE user_id=:u AND DATE(created_at)=:d", {"u": user_id, "d": today})

    text = "💰 <b>Bugungi Bonus va Jarimalar:</b>\n\n"
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
    user_id = message.from_user.id
    bonuses = database.fetchall("SELECT * FROM bonuses WHERE user_id=:u", {"u": user_id})
    fines = database.fetchall("SELECT * FROM fines WHERE user_id=:u", {"u": user_id})

    text = "💰 <b>So‘nggi 20 ta Bonus va Jarimalar:</b>\n\n"
    for b in bonuses[-10:]:
        text += f"✅ +{b['amount']:,} so‘m | {b['reason']}\n"
    for f in fines[-10:]:
        text += f"❌ -{f['amount']:,} so‘m | {f['reason']}\n"

    await message.answer(text or "📭 Ma’lumot yo‘q.", parse_mode="HTML")


# ===============================
# 📓 Eslatmalar
# ===============================
@router.message(F.text == "📓 Eslatmalarim")
async def show_notes(message: types.Message):
    user_id = message.from_user.id
    notes = database.fetchall("SELECT * FROM notes WHERE telegram_id=:u", {"u": user_id})

    if not notes:
        await message.answer("📓 Sizda hali eslatmalar yo‘q.\n✏️ Eslatma yozish uchun xabar yuboring.")
    else:
        text = "📒 <b>Sizning eslatmalaringiz:</b>\n\n"
        for n in notes[-10:]:
            text += f"🕒 {n['created_at']}\n📝 {n['text']}\n\n"
        await message.answer(text, parse_mode="HTML")


@router.message(F.text.regexp(r".+") & ~F.text.in_(["🕘 Ishni boshladim", "🏁 Ishni tugatdim", "🧹 Tozalash rasmi yuborish", "💰 Bonus/Jarimalarim", "⬅️ Menyuga qaytish"]))
async def save_note(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    database.execute("""
        INSERT INTO notes (telegram_id, text)
        VALUES (:u, :t)
    """, {"u": user_id, "t": text})

    await message.answer("📝 Eslatma saqlandi (faqat sizda ko‘rinadi).")


# ===============================
# ⬅️ Menyuga qaytish
# ===============================
@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=None)
