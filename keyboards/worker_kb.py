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
            KeyboardButton(text="🧾 Mahsulotlar"),
            KeyboardButton(text="🛒 Sotilgan mahsulotlar")
        ],
        [
            KeyboardButton(text="📋 Barcha mahsulotlar")
        ],
        [
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
        input_field_placeholder="Tanlang 👇",
        one_time_keyboard=False
    )


# 🧾 MAHSULOTLAR BO‘LIMI
def get_mahsulot_kb():
    kb = [
        [
            KeyboardButton(text="➕ Mahsulot qo‘shish"),
            KeyboardButton(text="➖ Mahsulot o‘chirish")
        ],
        [
            KeyboardButton(text="📦 Qolgan mahsulotlar"),
            KeyboardButton(text="🛒 Sotilgan mahsulotlar")
        ],
        [
            KeyboardButton(text="📋 Barcha mahsulotlar")
        ],
        [
            KeyboardButton(text="⬅️ Menyuga qaytish")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Mahsulotlar bo‘limidan tanlang 👇",
        one_time_keyboard=False
    )


# 💰 BONUS / JARIMA BO‘LIMI
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
        input_field_placeholder="Bonus / Jarima hisobotini tanlang 👇",
        one_time_keyboard=False
    )


# 🏠 ASOSIY MENYU (Super oddiy)
def get_main_kb():
    kb = [
        [KeyboardButton(text="👷 Ishchi menyusi")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Asosiy menyudan tanlang 👇",
        one_time_keyboard=False
    )
