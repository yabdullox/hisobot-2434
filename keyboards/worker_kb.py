from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# 👷‍♂️ Ishchi menyusi
def get_worker_kb():
    kb = [
        # 🔹 Ish jarayoni
        [
            KeyboardButton(text="🕘 Ishni boshladim"),
            KeyboardButton(text="🏁 Ishni tugatdim")
        ],

        # 🔹 Tozalash va muammo
        [
            KeyboardButton(text="🧹 Tozalash rasmi yuborish"),
            KeyboardButton(text="💬 Muammo yuborish")
        ],

        # 🔹 Qo‘shimcha ma’lumotlar
        [
            KeyboardButton(text="💰 Bonus / Jarimalarim"),
            KeyboardButton(text="📓 Eslatmalarim")
        ],

        # 🔹 Orqaga chiqish
        [
            KeyboardButton(text="⬅️ Menyuga qaytish")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# 💰 Bonus / Jarima menyusi
def get_bonus_kb():
    kb = [
        [
            KeyboardButton(text="📅 Bugungi holat"),
            KeyboardButton(text="📋 Umumiy ro‘yxat")
        ],
        [
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# 📓 Eslatma bo‘limi menyusi
def get_notes_kb():
    kb = [
        [
            KeyboardButton(text="📝 Eslatma yozish"),
            KeyboardButton(text="📖 Eslatmalarimni ko‘rish")
        ],
        [
            KeyboardButton(text="⬅️ Orqaga")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# 🏠 Asosiy menyuga qaytish
def get_main_kb():
    kb = [
        [
            KeyboardButton(text="👷 Ishchi menyusiga qaytish")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
