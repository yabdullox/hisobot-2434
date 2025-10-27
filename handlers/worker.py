from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID
import datetime

router = Router()

# 🧾 Hisobot yuborish
@router.message(F.text == "🧾 Hisobot yuborish")
async def ask_report(message: types.Message):
    await message.answer("📋 Hisobot matnini yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message(F.text & ~F.text.in_([
    "⏰ Ishni boshladim", "🏁 Ishni tugatdim",
    "📷 Tozalash rasmi yuborish", "📸 Muammo yuborish",
    "🐝 Bonus/Jarimalarim", "🔙 Menyuga qaytish"
]))
async def receive_report(message: types.Message):
    text = message.text.strip()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    await message.bot.send_message(
        SUPERADMIN_ID,
        f"📩 <b>Yangi hisobot</b>\n👷 {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>\n🕒 {now}\n\n{text}",
        parse_mode="HTML"
    )

    await message.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())

# ⏰ Ishni boshladim
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(message: types.Message):
    await message.answer("✅ Ishni boshladingiz. Omad!", reply_markup=worker_menu())
    await message.bot.send_message(
        SUPERADMIN_ID,
        f"🕒 {message.from_user.full_name} ishni boshladi.\n🆔 {message.from_user.id}"
    )

# 🏁 Ishni tugatdim
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(message: types.Message):
    await message.answer("✏️ Yakuniy hisobotni yuboring:", reply_markup=ReplyKeyboardRemove())

# 📷 Tozalash rasmi yuborish
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def clean_photo(message: types.Message):
    await message.answer("📸 Tozalash joyining rasmini yuboring:", reply_markup=ReplyKeyboardRemove())

# 📸 Muammo yuborish
@router.message(F.text == "📸 Muammo yuborish")
async def problem_photo(message: types.Message):
    await message.answer("⚠️ Muammo haqida rasm/izoh yuboring:", reply_markup=ReplyKeyboardRemove())

# 🖼 Rasm yuborish (ikkalasi uchun ham ishlaydi)
@router.message(F.photo)
async def photo_handler(message: types.Message):
    file_id = message.photo[-1].file_id
    caption = message.caption or "Rasm yuborildi"
    await message.bot.send_photo(
        SUPERADMIN_ID,
        file_id,
        caption=f"📷 {caption}\n👷 {message.from_user.full_name}\n🆔 {message.from_user.id}"
    )
    await message.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())

# 🐝 Bonus/Jarimalarim
@router.message(F.text == "🐝 Bonus/Jarimalarim")
async def bonus_info(message: types.Message):
    await message.answer("💰 Sizda hozircha bonus yoki jarimalar yo‘q.", reply_markup=worker_menu())

# 🔙 Menyuga qaytish
@router.message(F.text == "🔙 Menyuga qaytish")
async def back_to_menu(message: types.Message):
    await message.answer("🔄 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
