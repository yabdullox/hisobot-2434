from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID

router = Router()

# ==============================
# 🧾 HISOBOT YUBORISH
# ==============================
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report_prompt(message: types.Message):
    await message.answer(
        "📤 Iltimos, hisobot matnini yuboring.\n"
        "Masalan: <b>'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(
    F.text
    & ~F.text.in_([
        "🧾 Hisobot yuborish",
        "⏰ Ishni boshladim",
        "🏁 Ishni tugatdim",
        "📷 Tozalash rasmi yuborish",
        "📸 Muammo yuborish",
        "💰 Bonus/Jarimalarim",
        "↩️ Menyuga qaytish"
    ])
)
async def receive_report(message: types.Message):
    """Ishchi hisobot yuborganda superadminga jo‘natish"""
    report_text = message.text.strip()

    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            (
                f"📩 <b>Yangi hisobot</b>\n"
                f"👷 Ishchi: <b>{message.from_user.full_name}</b>\n"
                f"🆔 <code>{message.from_user.id}</code>\n\n"
                f"🧾 {report_text}"
            ),
            parse_mode="HTML"
        )
        await message.answer("✅ Hisobot yuborildi! Rahmat 👌", reply_markup=worker_menu())
    except Exception as e:
        print(f"⚠️ Superadminga hisobot yuborishda xato: {e}")
        await message.answer("⚠️ Xatolik yuz berdi, keyinroq urinib ko‘ring.", reply_markup=worker_menu())


# ==============================
# ⏰ ISHNI BOSHLADIM
# ==============================
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(message: types.Message):
    await message.answer("✅ Ishni boshladingiz! Omad tilaymiz 💪", reply_markup=worker_menu())

    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            (
                f"🕒 <b>Ishni boshlash</b>\n"
                f"👷 {message.from_user.full_name}\n"
                f"🆔 <code>{message.from_user.id}</code>"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Ish boshlash haqida yuborishda xato: {e}")


# ==============================
# 🏁 ISHNI TUGATDIM
# ==============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(message: types.Message):
    await message.answer("✏️ Yakuniy hisobotni yuboring:", reply_markup=ReplyKeyboardRemove())


# ==============================
# 📷 TOZALASH RASMI YUBORISH
# ==============================
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def clean_photo_instruction(message: types.Message):
    await message.answer("📸 Iltimos, tozalash joyining rasmini yuboring.", reply_markup=ReplyKeyboardRemove())


# ==============================
# 📸 MUAMMO YUBORISH
# ==============================
@router.message(F.text == "📸 Muammo yuborish")
async def problem_instruction(message: types.Message):
    await message.answer("⚠️ Muammo haqida rasm yoki izoh yuboring.", reply_markup=ReplyKeyboardRemove())


# ==============================
# 📷 / 📸 RASM QABUL QILISH
# ==============================
@router.message(F.photo)
async def receive_photo(message: types.Message):
    try:
        file_id = message.photo[-1].file_id
        caption = message.caption or ""

        # Caption mavjud bo‘lsa, muammo deb hisoblaymiz
        if caption:
            msg_type = "⚠️ Muammo rasmi"
        else:
            msg_type = "🧹 Tozalash rasmi"

        await message.bot.send_photo(
            SUPERADMIN_ID,
            photo=file_id,
            caption=(
                f"{msg_type}\n\n"
                f"👷 Ishchi: {message.from_user.full_name}\n"
                f"🆔 <code>{message.from_user.id}</code>\n"
                f"📝 {caption}"
            ),
            parse_mode="HTML"
        )

        await message.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())

    except Exception as e:
        print(f"⚠️ Rasm yuborishda xato: {e}")
        await message.answer("⚠️ Rasmni yuborishda xato yuz berdi.", reply_markup=worker_menu())


# ==============================
# 💰 BONUS / JARIMALAR
# ==============================
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def bonus_info(message: types.Message):
    await message.answer("💸 Hozircha bonus yoki jarimalar mavjud emas.", reply_markup=worker_menu())


# ==============================
# ↩️ MENYUGA QAYTISH
# ==============================
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(message: types.Message):
    await message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
