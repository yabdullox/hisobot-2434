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

        # 📦 OMBOR VA HISOBOTLAR (YANGI QO‘SHILDI)
        [
            KeyboardButton(text="📦 Ombor boshqaruvi"),
            KeyboardButton(text="🧾 Bugungi hisobotlar")
        ],
        [
            KeyboardButton(text="📊 Hisobotlar tarixi")
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
def get_admin_branch_kb(admin_id: int):
    """Admin biriktirilgan filiallar ro‘yxatini chiqaradi."""
    branches = database.get_admin_branches(admin_id)
    buttons = []

    if branches:
        for b in branches:
            buttons.append([InlineKeyboardButton(text=b["name"], callback_data=f"warehouse_branch:{b['id']}")])

    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_warehouse")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_warehouse_menu_kb(branch_id: int):
    """Tanlangan filial uchun ombor menyusi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Mahsulot qo‘shish", callback_data=f"add_product:{branch_id}")],
        [InlineKeyboardButton(text="➖ Mahsulot o‘chirish", callback_data=f"remove_product:{branch_id}")],
        [InlineKeyboardButton(text="👁 Barcha mahsulotlarni ko‘rish", callback_data=f"view_products:{branch_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_branches")]
    ])
