from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

worker_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="🕘 Ishni boshladim")],
        [KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="📸 Tozalash rasmi yuborish"), KeyboardButton(text="💬 Muammo yuborish")],
        [KeyboardButton(text="💰 Bonus/Jarimalarim")]
    ],
    resize_keyboard=True
)

bonus_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📅 Bugungi", callback_data="bonus_today")],
        [InlineKeyboardButton(text="📊 Umumiy", callback_data="bonus_all")]
    ]
)

# ✅ eski kodni buzmaslik uchun
def get_worker_kb():
    return worker_menu
