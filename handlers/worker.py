from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from datetime import datetime, date, time
import database

router = Router()


class ProblemFSM(StatesGroup):
    waiting_description = State()
    waiting_photo = State()

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

    # Bonus / jarima logikasi
    ish_boshlash_vaqti = time(9, 0)  # 9:00 da boshlanadi
    farq_daqiqa = (datetime.combine(today, now.time()) -
                   datetime.combine(today, ish_boshlash_vaqti)).total_seconds() / 60

    worker = database.fetchone(
        "SELECT id, branch_id FROM users WHERE telegram_id=:t",
        {"t": user_id}
    )
    if not worker:
        await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")
        return

    # Kech qolgan bo‘lsa
    if farq_daqiqa > 10:
        soat_kech = farq_daqiqa / 60
        penalty = round(soat_kech * 10000)
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
        await message.answer(
            f"⚠️ Siz {farq_daqiqa:.0f} daqiqa kech keldingiz.\n❌ Jarima: {penalty:,} so‘m."
        )

    # Erta kelgan bo‘lsa
    elif farq_daqiqa < 0:
        soat_erta = abs(farq_daqiqa) / 60
        bonus = round(soat_erta * 10000)
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
        await message.answer(
            f"🌅 Siz {abs(farq_daqiqa):.0f} daqiqa erta keldingiz.\n✅ Bonus: {bonus:,} so‘m."
        )

    await message.answer(f"🕘 Ish boshlanish vaqti saqlandi: {start_time}")


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


# ===============================
# 📸 Tozalash rasmi yuborish
# ===============================
@router.message(F.photo)
async def save_cleaning_photo(message: Message, state: FSMContext):
    if await state.get_state() == ProblemFSM.waiting_photo.state:
        # Bu handlerga tushmasligi kerak, biroq xavfsizlik uchun tekshiruv
        return

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
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=None)
