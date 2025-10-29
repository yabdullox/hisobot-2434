from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# 🧭 ADMIN PANEL — ODDIY TUGMALAR
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

        # 🏢 FILIALLAR BO‘LIMI
        [
            KeyboardButton(text="🏢 Filiallar ro‘yxati"),
            KeyboardButton(text="➕ Filial qo‘shish")
        ],
        [
            KeyboardButton(text="❌ Filialni o‘chirish")
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

        # ⚙️ TIZIM / ORQAGA
        [
            KeyboardButton(text="⬅️ Menyuga qaytish")
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Tanlang 👇",
        one_time_keyboard=False
    )


# 🧩 INLINE TUGMALAR (Ishchi uchun harakatlar)
def get_admin_inline_actions(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_worker:{user_id}"),
            InlineKeyboardButton(text="🗑️ O‘chirish", callback_data=f"delete_worker:{user_id}")
        ],
        [
            InlineKeyboardButton(text="💰 Bonus yozish", callback_data=f"bonus:{user_id}"),
            InlineKeyboardButton(text="⚠️ Jarima yozish", callback_data=f"fine:{user_id}")
        ]
    ])
