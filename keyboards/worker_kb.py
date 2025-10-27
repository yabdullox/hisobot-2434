# # src/keyboards/worker_kb.py

# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# def worker_menu():
#     kb = [
#         [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="⏰ Ishni boshladim")],
#         [KeyboardButton(text="🏁 Ishni tugatdim")],
#         [KeyboardButton(text="📷 Tozalash rasmi yuborish"), KeyboardButton(text="📸 Muammo yuborish")],
#         [KeyboardButton(text="📦 Mahsulotlarim"), KeyboardButton(text="📅 Bugungi hisobotlarim")],
#         [KeyboardButton(text="💰 Bonus/Jarimalarim"), KeyboardButton(text="↩️ Menyuga qaytish")]
#     ]
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# def product_menu():
#     kb = [
#         [KeyboardButton(text="➕ Mahsulot qo‘shish"), KeyboardButton(text="❌ Mahsulotni o‘chirish")],
#         [KeyboardButton(text="📋 Mavjud mahsulotlar"), KeyboardButton(text="↩️ Menyuga qaytish")]
#     ]
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# def start_work_menu():
#     kb = [
#         [KeyboardButton(text="📷 Tozalash rasmi yuborish")],
#         [KeyboardButton(text="↩️ Menyuga qaytish")]
#     ]
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# def confirm_end_work_menu():
#     kb = [
#         [KeyboardButton(text="📤 Yakuniy hisobotni yuborish")],
#         [KeyboardButton(text="↩️ Menyuga qaytish")]
#     ]
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# def make_edit_inline(report_id: int):
#     kb = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"edit_report:{report_id}")]
#     ])
#     return kb

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# === 🏠 Asosiy ishchi menyusi ===
def worker_menu():
    kb = [
        [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="⏰ Ishni boshladim")],
        [KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="📷 Tozalash rasmi yuborish"), KeyboardButton(text="📸 Muammo yuborish")],
        [KeyboardButton(text="📦 Mahsulotlarim"), KeyboardButton(text="📅 Bugungi hisobotlarim")],
        [KeyboardButton(text="💰 Bonus/Jarimalarim"), KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Kerakli bo‘limni tanlang 👇"
    )


# === 📦 Mahsulotlar menyusi ===
def product_menu():
    kb = [
        [KeyboardButton(text="➕ Mahsulot qo‘shish"), KeyboardButton(text="❌ Mahsulotni o‘chirish")],
        [KeyboardButton(text="📋 Mavjud mahsulotlar"), KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Mahsulotlar bo‘limi 👇"
    )


# === 🏁 Ishni tugatish menyusi ===
def confirm_end_work_menu():
    kb = [
        [KeyboardButton(text="📤 Yakuniy hisobotni yuborish")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )


# === 📷 Rasm yuborish menyusi ===
def photo_menu():
    kb = [
        [KeyboardButton(text="📷 Tozalash rasmi yuborish")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
