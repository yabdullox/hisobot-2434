from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def worker_menu():
    kb = [
        [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="⏰ Ishni boshladim")],
        [KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="📷 Tozalash rasmi yuborish"), KeyboardButton(text="📷 Muammo yuborish")],
        [KeyboardButton(text="💸 Bonus/Jarimalarim")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# def worker_menu():
#     kb = [
#         [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="📅 Bugungi hisobot")],
#         [KeyboardButton(text="💸 Bonus/Jarimalar"), KeyboardButton(text="⚙️ Sozlamalar")]
#     ]
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)



