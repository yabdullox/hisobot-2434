from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_worker_kb():
    keyboard = [
        [KeyboardButton(text="🧾 Hisobot yuborish")],
        [KeyboardButton(text="🕘 Ishni boshladim"), KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="🧹 Tozalash rasmi yuborish"), KeyboardButton(text="📷 Muammo yuborish")],
        [KeyboardButton(text="💰 Bonus/Jarimalarim")],
        [KeyboardButton(text="⬅️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
