# from aiogram import Router, types, F
# from database import db
# from keyboards.superadmin_kb import superadmin_menu
# from keyboards.admin_kb import admin_menu
# from keyboards.worker_kb import worker_menu
# from aiogram import Router, types
# from aiogram.filters import CommandStart
# from keyboards.worker_kb import worker_menu

# import os


# router = Router()


# router = Router()
# SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID") or 0)

# @router.message(F.text == "/start")
# # @router.message(commands=["start"])
# async def start_command(msg: types.Message):
#     user_id = msg.from_user.id
#     if user_id == SUPERADMIN_ID:
#         await msg.answer("👑 SuperAdmin paneliga xush kelibsiz.", reply_markup=superadmin_menu())
#         return

#     admin = db.get_conn().execute("SELECT * FROM admins WHERE tg_id=?", (user_id,)).fetchone()
#     if admin:
#         await msg.answer("🧑‍💼 Filial admin paneliga xush kelibsiz.", reply_markup=admin_menu())
#         return

#     worker = db.get_conn().execute("SELECT * FROM workers WHERE tg_id=?", (user_id,)).fetchone()
#     if worker:
#         await msg.answer("👷 Ishchi menyusiga xush kelibsiz.", reply_markup=worker_menu)
#         return

#     await msg.answer("Siz tizimda yo‘qsiz. SuperAdmin bilan bog‘laning.")
# from aiogram import Router, types
# from keyboards.worker_kb import worker_menu

# router = Router()

import os
import asyncio
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from database import db
from keyboards.superadmin_kb import superadmin_menu
from keyboards.admin_kb import admin_menu
from keyboards.worker_kb import worker_menu

router = Router()

# 🔹 .env dan SUPERADMIN_ID ni olish
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

    # 👑 Superadminni tekshirish
    if user_id == SUPERADMIN_ID:
        await message.answer("👑 SuperAdmin paneliga xush kelibsiz.", reply_markup=superadmin_menu)
        return

    # 🧑‍💼 Filial adminni tekshirish
    admin = await asyncio.to_thread(
        lambda: db.get_conn().execute("SELECT * FROM admins WHERE tg_id=?", (user_id,)).fetchone()
    )
    if admin:
        await message.answer("🧑‍💼 Filial admin paneliga xush kelibsiz.", reply_markup=admin_menu)
        return

    # 👷 Worker ni tekshirish
    worker = await asyncio.to_thread(
        lambda: db.get_conn().execute("SELECT * FROM workers WHERE tg_id=?", (user_id,)).fetchone()
    )
    if worker:
        await message.answer("👷 Ishchi menyusiga xush kelibsiz.", reply_markup=worker_menu)
        return

    # Agar foydalanuvchi tizimda topilmasa
    await message.answer("⛔ Siz tizimda ro‘yxatdan o‘tmagansiz. SuperAdmin bilan bog‘laning.")
