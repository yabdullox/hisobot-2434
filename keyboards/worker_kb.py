from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 👷 ISHCHI ASOSIY MENYUSI (keraksiz tugmalar olib tashlangan)
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
        input_field_placeholder="Tanlang 👇",
        one_time_keyboard=False
    )
