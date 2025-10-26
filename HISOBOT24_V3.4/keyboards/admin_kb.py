from aiogram import types

def admin_menu():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="👷 Ishchilar ro‘yxati"), types.KeyboardButton(text="➕ Ishchi qo‘shish")],
            [types.KeyboardButton(text="🗑 Ishchini o‘chirish"), types.KeyboardButton(text="💸 Jarima/Bonus yozish")],
        ],
        resize_keyboard=True
    )

# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# def admin_menu():
#     kb = [
#         [KeyboardButton(text="👷 Ishchi qo‘shish"), KeyboardButton(text="❌ Ishchini o‘chirish")],
#         [KeyboardButton(text="👥 Ishchilar ro‘yxati")],
#         [KeyboardButton(text="💸 Jarima/Bonus yozish")],
#         [KeyboardButton(text="↩️ Ortga")]
#     ]
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
