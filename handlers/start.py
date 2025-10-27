from aiogram import Router, types, F
from aiogram.filters import CommandStart
from keyboards.superadmin_kb import superadmin_menu
from keyboards.admin_kb import admin_menu
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID

router = Router()

# /start buyrug'i uchun to‘g‘ri 3.x format
@router.message(CommandStart())
async def start_command(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name

    if user_id == SUPERADMIN_ID:
        await message.answer(
            f"👑 Salom, SuperAdmin {full_name}!\nQuyidagi menyu orqali ishlang:",
            reply_markup=superadmin_menu()
        )
    elif message.from_user.username and message.from_user.username.startswith("admin"):
        await message.answer(
            f"🧭 Salom, Admin {full_name}!\nMenyudan tanlang:",
            reply_markup=admin_menu()
        )
    else:
        await message.answer(
            f"👋 Salom, {full_name}!\nIshchi menyusi orqali harakat qiling 👇",
            reply_markup=worker_menu()
        )
