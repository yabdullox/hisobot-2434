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
        "📤 Iltimos, hisobot matnini yuboring.\nMasalan: <b>'Bugun 5 ta mijoz, 3 ta tozalash.'</b>",
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
    """Hisobot matnini qabul qilib, superadminga yuborish"""
    report_text = message.text.strip()

    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            (
                f"📩 <b>Yangi hisobot</b>\n"
                f"👷 {message.from_user.full_name}\n"
                f"🆔 <code>{message.from_user.id}</code>\n\n"
                f"🧾 {report_text}"
            ),
            parse_mode="HTML"
        )
        await message.answer("✅ Hisobot yuborildi! Rahmat.", reply_markup=worker_menu())
    except Exception as e:
        print(f"⚠️ Xato: {e}")
        await message.answer("⚠️ Hisobot yuborishda xato yuz berdi.", reply_markup=worker_menu())

# ==============================
# ⏰ ISHNI BOSHLADIM
# ==============================
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(message: types.Message):
    await message.answer("✅ Ishni boshladingiz. Omad!", reply_markup=worker_menu())
    await message.bot.send_message(
        SUPERADMIN_ID,
        f"🕒 <b>Ishchi ishni boshladi:</b>\n👷 {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )

# ==============================
# 🏁 ISHNI TUGATDIM
# ==============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(message: types.Message):
    await message.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())

# ==============================
# 📷 TOZALASH RASMI
# ==============================
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def clean_photo_instruction(message: types.Message):
    await message.answer("📸 Tozalash joyining rasmini yuboring.", reply_markup=ReplyKeyboardRemove())

@router.message(F.photo)
async def receive_photo(message: types.Message):
    file_id = message.photo[-1].file_id
    caption = message.caption or "Tozalash rasmi"
    await message.bot.send_photo(
        SUPERADMIN_ID,
        photo=file_id,
        caption=f"🧹 <b>{caption}</b>\n👷 {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )
    await message.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())

# ==============================
# 📸 MUAMMO YUBORISH
# ==============================
@router.message(F.text == "📸 Muammo yuborish")
async def problem_instruction(message: types.Message):
    await message.answer("⚠️ Muammo haqida rasm yoki izoh yuboring:", reply_markup=ReplyKeyboardRemove())

# ==============================
# 💰 BONUS / JARIMALAR
# ==============================
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def bonus_info(message: types.Message):
    await message.answer("💸 Hozircha bonus yoki jarimalar yo‘q.", reply_markup=worker_menu())

# ==============================
# ↩️ MENYUGA QAYTISH
# ==============================
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(message: types.Message):
    await message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
