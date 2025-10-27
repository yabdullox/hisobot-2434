from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_menu():
    kb = [
        [KeyboardButton(text="👷 Ishchilar ro‘yxati"), KeyboardButton(text="➕ Ishchi qo‘shish")],
        [KeyboardButton(text="🗑 Ishchini o‘chirish"), KeyboardButton(text="💸 Jarima/Bonus yozish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
