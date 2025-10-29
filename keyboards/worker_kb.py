from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# 🔹 Ishchi menyusi (asosiy)
worker_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="🕓 Ishni boshladim")],
        [KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="🧹 Tozalash rasmi yuborish"), KeyboardButton(text="📷 Muammo yuborish")],
        [KeyboardButton(text="💰 Bonus/Jarimalarim")],
    ],
    resize_keyboard=True
)

# 🔹 Bonus/Jarimalar menyusi
bonus_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📅 Bugungi", callback_data="bonus_today")],
        [InlineKeyboardButton(text="📊 Umumiy", callback_data="bonus_all")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_worker")]
    ]
)
