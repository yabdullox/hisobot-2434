from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_kb():
    keyboard = [
        [KeyboardButton(text="👥 Ishchilar ro‘yxati"), KeyboardButton(text="➕ Ishchi qo‘shish")],
        [KeyboardButton(text="🗑️ Ishchini o‘chirish"), KeyboardButton(text="💰 Jarima/Bonus yozish")],
        [KeyboardButton(text="💬 Muammolar"), KeyboardButton(text="💰 Bonus/Jarimalar ro‘yxati")],  # ✅ yangi tugma
        [KeyboardButton(text="⬅️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
