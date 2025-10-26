from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# === 🏠 ASOSIY ISHCHI MENYU ===
def worker_menu():
    """
    👷 Ishchilar uchun asosiy menyu (ishchi paneli)
    """
    kb = [
        [
            KeyboardButton(text="🧾 Hisobot yuborish"),
            KeyboardButton(text="⏰ Ishni boshladim")
        ],
        [
            KeyboardButton(text="🏁 Ishni tugatdim")
        ],
        [
            KeyboardButton(text="📷 Tozalash rasmi yuborish"),
            KeyboardButton(text="📸 Muammo yuborish")
        ],
        [
            KeyboardButton(text="📦 Mahsulotlarim"),  # 🆕 YANGI TUGMA
            KeyboardButton(text="📅 Bugungi hisobotlarim")
        ],
        [
            KeyboardButton(text="💰 Bonus/Jarimalarim"),
            KeyboardButton(text="↩️ Menyuga qaytish")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Kerakli bo‘limni tanlang 👇"
    )


# === 📤 HISOBOT YUBORISH MENYUSI ===
def report_menu():
    """
    📤 Hisobot yuborish jarayonida chiqadigan menyu
    """
    kb = [
        [KeyboardButton(text="✅ Hisobotni yuborish"), KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Hisobotingizni yozing ✏️"
    )


# === 🕒 ISHNI BOSHLASH MENYUSI ===
def start_work_menu():
    """
    ⏰ Ishni boshlashdan keyin paydo bo‘ladigan menyu
    """
    kb = [
        [KeyboardButton(text="📷 Tozalash rasmi yuborish")],
        [KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Ish faoliyatingizni davom eting 👇"
    )


# === 🏁 ISHNI TUGATISH (YAKUNIY HISOBOT) MENYUSI ===
def confirm_end_work_menu():
    """
    🏁 Ishni tugatgandan keyin chiqadigan yakuniy menyu
    """
    kb = [
        [KeyboardButton(text="📤 Yakuniy hisobotni yuborish")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Ish yakunini tasdiqlang 👇"
    )


# === 📸 MUAMMO YUBORISH MENYUSI ===
def problem_menu():
    """
    ⚠️ Muammo yuborish jarayonida chiqadigan menyu
    """
    kb = [
        [KeyboardButton(text="📸 Rasm yuborish"), KeyboardButton(text="📝 Izoh yozish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Muammoni tavsiflab yuboring..."
    )


# === 💰 BONUS/JARIMALAR MENYUSI ===
def finance_menu():
    """
    💰 Bonus va jarimalarni ko‘rish uchun menyu
    """
    kb = [
        [KeyboardButton(text="🎉 Bonuslarim"), KeyboardButton(text="⚠️ Jarimalarim")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Moliyaviy ma’lumotlar 👇"
    )


# === 🗓 HISOBOTLAR KO‘RISH MENYUSI ===
def reports_menu():
    """
    📅 Hisobotlarni ko‘rish uchun menyu
    """
    kb = [
        [KeyboardButton(text="📅 Bugungi hisobotlarim"), KeyboardButton(text="🗓 Umumiy hisobotlarim")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Hisobotni tanlang 👇"
    )


# === 🔙 MINIMAL ORQAGA QAYTISH MENYUSI ===
def minimal_back_menu():
    """
    🔙 Minimal orqaga qaytish klaviaturasi
    """
    kb = [
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )


# === 📷 RASM YUBORISH (TOZALASH) MENYUSI ===
def photo_send_menu():
    """
    📸 Rasm yuborish uchun soddalashtirilgan menyu
    """
    kb = [
        [KeyboardButton(text="📷 Tozalash rasmi yuborish")],
        [KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False
    )
