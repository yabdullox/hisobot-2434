# import os
# import asyncio
# from aiogram import Router, types
# from aiogram.filters import CommandStart
# from aiogram.fsm.context import FSMContext
# from database import db

# # Klaviatura fayllarni import qilamiz (funksiya shaklida bo‘lishi kerak)
# from keyboards.superadmin_kb import superadmin_menu
# from keyboards.admin_kb import admin_menu
# from keyboards.worker_kb import worker_menu

# router = Router()

# # .env dan SUPERADMIN_ID ni olish
# SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID") or 0)


# @router.message(CommandStart())
# async def start_command(message: types.Message, state: FSMContext):
#     """
#     /start buyrug‘i - foydalanuvchini roli bo‘yicha menyuga yo‘naltiradi:
#     👑 SuperAdmin → superadmin_menu
#     🧑‍💼 Filial admin → admin_menu
#     👷 Worker → worker_menu
#     """
#     user_id = message.from_user.id
#     user_name = message.from_user.full_name

#     print(f"🔹 Foydalanuvchi start bosdi: {user_name} ({user_id})")

#     # 👑 SUPERADMIN ni tekshirish
#     if user_id == SUPERADMIN_ID:
#         await message.answer(
#             "👑 SuperAdmin paneliga xush kelibsiz.",
#             reply_markup=superadmin_menu()
#         )
#         return

#     # 🧑‍💼 ADMIN ni tekshirish
#     admin = await asyncio.to_thread(
#         lambda: db.get_conn().execute("SELECT * FROM admins WHERE tg_id=?", (user_id,)).fetchone()
#     )

#     if admin:
#         await message.answer(
#             "🧑‍💼 Admin paneliga xush kelibsiz.",
#             reply_markup=admin_menu()
#         )
#         return

#     # 👷 WORKER ni tekshirish
#     worker = await asyncio.to_thread(
#         lambda: db.get_conn().execute("SELECT * FROM workers WHERE tg_id=?", (user_id,)).fetchone()
#     )

    
#         def worker_menu(
       
#             "👷 Ishchi menyusiga xush kelibsiz.",
#            reply_markup = worker_menu
#        )
#     return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
#     # Agar foydalanuvchi topilmasa
#     await message.answer(
#         "⛔ Siz tizimda ro‘yxatdan o‘tmagansiz.\n"
#         "Iltimos, SuperAdmin bilan bog‘laning."
#     )


from aiogram import Router, F, types
from config import SUPERADMIN_ID
from keyboards.superadmin_kb import superadmin_menu
from keyboards.worker_kb import worker_menu
from keyboards.admin_kb import admin_menu   # agar admin menyusi bo‘lsa
from database import db

router = Router()


# 🔹 /start komandasi
@router.message(F.text == "/start")
async def start_command(msg: types.Message):
    user_id = msg.from_user.id
    full_name = msg.from_user.full_name

    # --- 1️⃣ SuperAdmin ---
    if user_id == SUPERADMIN_ID:
        await msg.answer(
            f"👋 Salom, <b>SuperAdmin</b> {full_name}!\nQuyidagi menyudan birini tanlang:",
            parse_mode="HTML",
            reply_markup=superadmin_menu()
        )
        return

    # --- 2️⃣ Admin ---
    conn = db.get_conn()
    cur = conn.cursor()
    admin = cur.execute("SELECT id FROM admins WHERE tg_id=?", (user_id,)).fetchone()
    if admin:
        await msg.answer(
            f"👋 Salom, <b>Admin</b> {full_name}!\nFilialingizdagi hisobotlarni kuzatishingiz mumkin.",
            parse_mode="HTML",
            reply_markup=admin_menu()
        )
        conn.close()
        return

    # --- 3️⃣ Worker (ishchi) ---
    worker = cur.execute("SELECT id FROM workers WHERE tg_id=?", (user_id,)).fetchone()
    conn.close()

    if worker:
        await msg.answer(
            f"👋 Salom, <b>{full_name}</b>!\nIshchi menyusi orqali harakat qiling:",
            parse_mode="HTML",
            reply_markup=worker_menu()
        )
    else:
        await msg.answer(
            "⛔ Siz tizimda ro‘yxatdan o‘tmagansiz.\nIltimos, SuperAdmin bilan bog‘laning."
        )


# 🔹 /help komandasi
@router.message(F.text == "/help")
async def help_command(msg: types.Message):
    text = (
        "ℹ️ <b>Botdan foydalanish bo‘yicha yordam:</b>\n\n"
        "🧾 <b>Hisobot yuborish</b> — kunlik ish natijangizni yuboring.\n"
        "📷 <b>Tozalash rasmi yuborish</b> — joyda olingan rasmlarni yuboring.\n"
        "⏰ <b>Ishni boshladim</b> — ishga kirishgan vaqtni belgilang.\n"
        "💸 <b>Bonus/Jarimalarim</b> — moliyaviy holatni ko‘rish.\n"
        "📅 <b>Bugungi hisobotlar</b> — SuperAdmin uchun bugungi natijalar.\n"
        "📊 <b>Umumiy hisobotlar</b> — barcha hisobotlarni ko‘rish.\n"
        "⚙️ <b>Filiallar, adminlar va ishchilarni boshqarish</b> — faqat SuperAdmin uchun."
    )
    await msg.answer(text, parse_mode="HTML")

