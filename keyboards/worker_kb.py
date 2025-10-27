# src/keyboards/worker_kb.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def worker_menu():
    kb = [
        [KeyboardButton("🧾 Hisobot yuborish"), KeyboardButton("⏰ Ishni boshladim")],
        [KeyboardButton("🏁 Ishni tugatdim")],
        [KeyboardButton("📷 Tozalash rasmi yuborish"), KeyboardButton("📸 Muammo yuborish")],
        [KeyboardButton("📦 Mahsulotlarim"), KeyboardButton("📅 Bugungi hisobotlarim")],
        [KeyboardButton("💰 Bonus/Jarimalarim"), KeyboardButton("↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def product_menu():
    kb = [
        [KeyboardButton("➕ Mahsulot qo‘shish"), KeyboardButton("❌ Mahsulotni o‘chirish")],
        [KeyboardButton("📋 Mavjud mahsulotlar"), KeyboardButton("↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def start_work_menu():
    kb = [
        [KeyboardButton("📷 Tozalash rasmi yuborish")],
        [KeyboardButton("↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def confirm_end_work_menu():
    kb = [
        [KeyboardButton("📤 Yakuniy hisobotni yuborish")],
        [KeyboardButton("↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# Inline helper for editing/list actions (if kerak)
def make_edit_inline(report_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_report:{report_id}"))
    return kb
