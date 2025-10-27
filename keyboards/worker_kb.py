from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# 👷‍♂️ Worker menyusi
worker_menu = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [
            KeyboardButton(text="🧾 Hisobot yuborish"),
            KeyboardButton(text="⏰ Ishni boshladim")
        ],
        [
            KeyboardButton(text="🐝 Bonus/Jarimalarim")
        ],
        [
            KeyboardButton(text="📷 Tozalash rasmi yuborish")
            
        ],
        [
            KeyboardButton(text="🔙 Menyuga qaytish")
        ]
    ]
)
