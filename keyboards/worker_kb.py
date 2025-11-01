from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 👷 ISHCHI — ASOSIY MENYU
def get_worker_kb():
    kb = [
        [  # Ish vaqtlarini belgilash
            KeyboardButton(text="🕘 Ishni boshladim"),
            KeyboardButton(text="🏁 Ishni tugatdim"),
        ],
        [  # Hisobot va Ombor
            KeyboardButton(text="🧾 Bugungi hisobotni yuborish"),
            KeyboardButton(text="📋 Ombor holati"),
        ],
        [  # Bonus/Jarima bo‘limi
            KeyboardButton(text="💰 Bonus / Jarimalarim"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Tanlang 👇",
    )


# 💰 BONUS / JARIMA BO‘LIMI
def get_bonus_kb():
    kb = [
        [
            KeyboardButton(text="📅 Bugungi"),
            KeyboardButton(text="📋 Umumiy"),   # 🔁 handlerga mos: show_all_bonus()
        ],
        [
            KeyboardButton(text="⬅️ Orqaga"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Bonus / Jarima bo‘limini tanlang 👇",
    )
