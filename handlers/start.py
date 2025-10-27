from aiogram import Router, types
from keyboards.superadmin_kb import superadmin_menu
from keyboards.admin_kb import admin_menu
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID

router = Router()

@router.message(commands=["start"])
async def start_command(message: types.Message):
    if message.from_user.id == SUPERADMIN_ID:
        await message.answer("👑 SuperAdmin menyusi:", reply_markup=superadmin_menu())
    elif message.from_user.username and message.from_user.username.startswith("admin"):
        await message.answer("🧭 Admin menyusi:", reply_markup=admin_menu())
    else:
        await message.answer(
            f"👋 Salom, {message.from_user.full_name}!\nIshchi menyusi orqali harakat qiling 👇",
            reply_markup=worker_menu()
        )
