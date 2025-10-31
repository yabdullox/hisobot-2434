from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 👷 ISHCHI ASOSIY MENYUSI
def get_worker_kb():
    kb = [
        [
            KeyboardButton(text="🕘 Ishni boshladim"),
            KeyboardButton(text="🏁 Ishni tugatdim")
        ],
        [
            KeyboardButton(text="🧹 Tozalash rasmi yuborish"),
            KeyboardButton(text="💬 Muammo yuborish")
        ],
        [
            KeyboardButton(text="📋 Ombor holati"),
            KeyboardButton(text="🧾 Bugungi hisobotni yuborish")
        ],
        [
            KeyboardButton(text="💰 Bonus / Jarimalarim"),
            KeyboardButton(text="📓 Eslatmalarim")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Tanlang 👇"
    )


# 💰 BONUS / JARIMA BO‘LIMI — 🔹 SHU YO‘Q BO‘LGANI SABABLI XATO BO‘LGAN
def get_bonus_kb():
    kb = [
        [
            KeyboardButton(text="📅 Bugungi"),
            KeyboardButton(text="📊 Umumiy")
        ],
        [
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Bonus / Jarima bo‘limini tanlang 👇"
    )
