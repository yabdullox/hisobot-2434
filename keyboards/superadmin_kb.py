from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_superadmin_kb():
    keyboard = [
        # 📊 HISOBOTLAR BO‘LIMI
        [
            KeyboardButton(text="📊 Bugungi hisobotlar"),
            KeyboardButton(text="📈 Umumiy hisobotlar")
        ],

        # 🏢 FILIALLAR BO‘LIMI
        [
            KeyboardButton(text="🏢 Filiallar ro‘yxati"),
            KeyboardButton(text="➕ Filial qo‘shish"),
        ],
        [
            KeyboardButton(text="❌ Filialni o‘chirish")
        ],

        # 👥 ADMINLAR BO‘LIMI
        [
            KeyboardButton(text="👥 Adminlar ro‘yxati"),
            KeyboardButton(text="➕ Admin qo‘shish")
            [KeyboardButton(text="➕ Adminni filialga biriktirish")],
        ],
        [
            KeyboardButton(text="🗑️ Adminni o‘chirish")
        ],

        # 💰 MOLIYAVIY BO‘LIM
        [
            KeyboardButton(text="💰 Bonus/Jarimalar ro‘yxati"),
            KeyboardButton(text="📤 Export (Excel/CSV)")
        ],

        # ⚙️ TIZIM VA ORQAGA
        [
            KeyboardButton(text="⚙️ Sozlamalar"),
            KeyboardButton(text="🧾 Loglar / Jurnallar")
        ],
        [
            KeyboardButton(text="⬅️ Menyuga qaytish")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )
