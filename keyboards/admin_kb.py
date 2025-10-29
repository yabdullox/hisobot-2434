from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_admin_kb():
    keyboard = [
        # 👥 ISHCHILAR BO‘LIMI
        [
            KeyboardButton(text="👥 Ishchilar ro‘yxati"),
            KeyboardButton(text="➕ Ishchi qo‘shish")
        ],
        [
            KeyboardButton(text="🗑️ Ishchini o‘chirish")
        ],

        # 💰 MOLIYAVIY BO‘LIM
        [
            KeyboardButton(text="💰 Jarima/Bonus yozish"),
            KeyboardButton(text="💰 Bonus/Jarimalar ro‘yxati")
        ],

        # 💬 MUAMMOLAR BO‘LIMI
        [
            KeyboardButton(text="💬 Muammolar")
        ],

        # ⚙️ TIZIM/ORQAGA
        [
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="⬅️ Menyuga qaytish")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
