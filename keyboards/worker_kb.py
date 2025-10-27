from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def worker_menu():
    kb = [
        [KeyboardButton("🧾 Hisobot yuborish"), KeyboardButton("⏰ Ishni boshladim")],
        [KeyboardButton("🏁 Ishni tugatdim")],
        [KeyboardButton("📷 Tozalash rasmi yuborish"), KeyboardButton("📸 Muammo yuborish")],
        [KeyboardButton("💰 Bonus/Jarimalarim"), KeyboardButton("↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
