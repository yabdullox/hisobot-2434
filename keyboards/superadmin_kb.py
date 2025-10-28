from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_superadmin_kb():
    keyboard = [
        [KeyboardButton(text="📊 Bugungi hisobotlar"), KeyboardButton(text="📈 Umumiy hisobotlar")],
        [KeyboardButton(text="🏢 Filiallar ro‘yxati"), KeyboardButton(text="➕ Filial qo‘shish")],
        [KeyboardButton(text="❌ Filialni o‘chirish")],
        [KeyboardButton(text="👥 Adminlar ro‘yxati"), KeyboardButton(text="➕ Admin qo‘shish")],
        [KeyboardButton(text="🗑️ Adminni o‘chirish")],
        [KeyboardButton(text="💰 Bonus/Jarimalar ro‘yxati")],   # ✅ yangi tugma
        [KeyboardButton(text="📤 Export (Excel/CSV)")],
        [KeyboardButton(text="⬅️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
