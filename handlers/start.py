import os
import asyncio
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from database import db

# Klaviatura fayllarni import qilamiz (funksiya shaklida bo‘lishi kerak)
from keyboards.superadmin_kb import superadmin_menu
from keyboards.admin_kb import admin_menu
from keyboards.worker_kb import worker_menu

router = Router()

# .env dan SUPERADMIN_ID ni olish
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID") or 0)


@router.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    """
    /start buyrug‘i - foydalanuvchini roli bo‘yicha menyuga yo‘naltiradi:
    👑 SuperAdmin → superadmin_menu
    🧑‍💼 Filial admin → admin_menu
    👷 Worker → worker_menu
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    print(f"🔹 Foydalanuvchi start bosdi: {user_name} ({user_id})")

    # 👑 SUPERADMIN ni tekshirish
    if user_id == SUPERADMIN_ID:
        await message.answer(
            "👑 SuperAdmin paneliga xush kelibsiz.",
            reply_markup=superadmin_menu()
        )
        return

    # 🧑‍💼 ADMIN ni tekshirish
    admin = await asyncio.to_thread(
        lambda: db.get_conn().execute("SELECT * FROM admins WHERE tg_id=?", (user_id,)).fetchone()
    )

    if admin:
        await message.answer(
            "🧑‍💼 Admin paneliga xush kelibsiz.",
            reply_markup=admin_menu()
        )
        return

    # 👷 WORKER ni tekshirish
    worker = await asyncio.to_thread(
        lambda: db.get_conn().execute("SELECT * FROM workers WHERE tg_id=?", (user_id,)).fetchone()
    )

    
        def worker_menu(
       
            "👷 Ishchi menyusiga xush kelibsiz.",
           reply_markup = worker_menu
       )
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    # Agar foydalanuvchi topilmasa
    await message.answer(
        "⛔ Siz tizimda ro‘yxatdan o‘tmagansiz.\n"
        "Iltimos, SuperAdmin bilan bog‘laning."
    )


