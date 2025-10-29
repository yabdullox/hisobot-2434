from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# 👷 Ishchi menyusi uchun keyboard
def get_worker_kb():
    kb = [
        [KeyboardButton(text="🕘 Ishni boshladim"), KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="🧹 Tozalash rasmi yuborish"), KeyboardButton(text="💬 Muammo yuborish")],
        [KeyboardButton(text="📤 Bugungi hisobotni yuborish")],  # ✅ yangi tugma
        [KeyboardButton(text="💰 Bonus / Jarimalarim"), KeyboardButton(text="📓 Eslatmalarim")],
        [KeyboardButton(text="⬅️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# 💰 Bonus / Jarima bo‘limi uchun keyboard
def get_bonus_kb():
    kb = [
        [KeyboardButton(text="📅 Bugungi"), KeyboardButton(text="📋 Umumiy")],
        [KeyboardButton(text="⬅️ Orqaga")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# 🏠 Asosiy menyu
def get_main_kb():
    kb = [
        [KeyboardButton(text="👷 Ishchi menyusi")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
