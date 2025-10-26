from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# === ASOSIY ISHCHI MENYU ===
def worker_menu():
    """
    👷 Ishchilar uchun asosiy menyu
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
            KeyboardButton(text="📅 Bugungi hisobotlarim"),
            KeyboardButton(text="💰 Bonus/Jarimalarim")
        ],
        [
            KeyboardButton(text="↩️ Menyuga qaytish")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Kerakli bo‘limni tanlang 👇"
    )


# === HISOBOT YUBORISH BOSHLANG'ICH MENYU ===
def report_menu():
    """
    📤 Hisobot yuborish boshlanganida chiqadigan klaviatura
    """
    kb = [
        [KeyboardButton(text="✅ Yuborish"), KeyboardButton(text="🔙 Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Hisobotingizni yozing ✏️"
    )


# === ISHNI BOSHLAGANDAN KEYINGI MENYU ===
def start_work_menu():
    """
    ⏰ Ishni boshlashdan keyingi variantlar
    """
    kb = [
        [KeyboardButton(text="📷 Tozalash rasmi yuborish"), KeyboardButton(text="📸 Muammo yuborish")],
        [KeyboardButton(text="🏁 Ishni tugatdim")],
        [KeyboardButton(text="🔙 Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Ish jarayonidagi variantlardan birini tanlang 👇"
    )


# === ISHNI TUGATISH (YAKUNIY) MENYU ===
def confirm_end_work_menu():
    """
    🏁 Ishni tugatgandan keyin — yakuniy hisobot so‘rashi uchun
    """
    kb = [
        [KeyboardButton(text="📤 Yakuniy hisobotni yuborish")],
        [KeyboardButton(text="🔙 Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Ish yakunini tasdiqlang 👇"
    )


# === MUAMMO YUBORISH (RASMLI) MENYU ===
def problem_menu():
    """
    ⚠️ Muammo yuborish paytida chiqadigan menyu
    """
    kb = [
        [KeyboardButton(text="📸 Rasm yuborish"), KeyboardButton(text="📝 Izoh yozish")],
        [KeyboardButton(text="🔙 Bekor qilish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Muammoni yozing yoki rasm yuboring..."
    )


# === BONUS/JARIMALAR KO‘RISH MENYUSI ===
def finance_menu():
    """
    💰 Bonus va jarimalar sahifasi
    """
    kb = [
        [KeyboardButton(text="📊 Bonuslarim"), KeyboardButton(text="⚠️ Jarimalarim")],
        [KeyboardButton(text="🔙 Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True
    )


# === HISOBOT KO‘RISH MENYUSI ===
def reports_menu():
    """
    📅 Bugungi yoki umumiy hisobotlarni ko‘rish uchun
    """
    kb = [
        [KeyboardButton(text="📅 Bugungi hisobotlarim"), KeyboardButton(text="🗓 Umumiy hisobotlarim")],
        [KeyboardButton(text="🔙 Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        one_time_keyboard=True
    )


# === MINIMAL ORQAGA QAYTISH MENYUSI ===
def minimal_back_menu():
    """
    🔙 Minimal orqaga qaytish klaviaturasi
    """
    kb = [
        [KeyboardButton(text="🔙 Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )
