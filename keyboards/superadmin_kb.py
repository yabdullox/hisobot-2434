from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def superadmin_menu():
    kb = [
        [KeyboardButton(text="🏢 Filiallar ro‘yxati"), KeyboardButton(text="➕ Filial qo‘shish")],
        [KeyboardButton(text="❌ Filialni o‘chirish"), KeyboardButton(text="👥 Adminlar ro‘yxati")],
        [KeyboardButton(text="➕ Admin qo‘shish"), KeyboardButton(text="🗑 Adminni o‘chirish")],
        [KeyboardButton(text="📅 Bugungi hisobotlar"), KeyboardButton(text="📊 Umumiy hisobotlar")],
        [KeyboardButton(text="📦 Export (Excel)"), KeyboardButton(text="⚠️ Muammolar ro‘yxati")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
