# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# # 👷‍♂️ Worker menyusi
# worker_menu = ReplyKeyboardMarkup(
#     resize_keyboard=True,
#     keyboard=[
#         [
#             KeyboardButton(text="🧾 Hisobot yuborish"),
#             KeyboardButton(text="⏰ Ishni boshladim")
#         ],
#         [
#             KeyboardButton(text="🐝 Bonus/Jarimalarim")
#         ],
#         [
#             KeyboardButton(text="📷 Tozalash rasmi yuborish")
            
#         ],
#         [
#             KeyboardButton(text="🔙 Menyuga qaytish")
#         ]
#     ]
# )

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def worker_menu():
    kb = [
        [KeyboardButton(text="🧾 Hisobot yuborish"), KeyboardButton(text="📅 Bugungi hisobot")],
        [KeyboardButton(text="💸 Bonus/Jarimalar"), KeyboardButton(text="⚙️ Sozlamalar")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
