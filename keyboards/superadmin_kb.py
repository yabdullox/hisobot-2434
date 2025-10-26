from telegram import ReplyKeyboardMarkup, KeyboardButton

def superadmin_menu():
    kb = [
        [KeyboardButton("🏢 Filiallar ro‘yxati"), KeyboardButton("➕ Filial qo‘shish")],
        [KeyboardButton("❌ Filialni o‘chirish"), KeyboardButton("👥 Adminlar ro‘yxati")],
        [KeyboardButton("➕ Admin qo‘shish")],  # ✅ yangi tugma qo‘shildi
        [KeyboardButton("📅 Bugungi hisobotlar"), KeyboardButton("📊 Umumiy hisobotlar")],
        [KeyboardButton("📦 Export (Excel)"), KeyboardButton("⚠️ Muammolar ro‘yxati")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)
