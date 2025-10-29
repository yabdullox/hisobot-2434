# from aiogram import Router, F, types
# from aiogram.filters import Command
# from keyboards.superadmin_kb import get_superadmin_kb
# from keyboards.admin_kb import get_admin_kb
# from keyboards.worker_kb import get_worker_kb
# from database import fetchone, execute
# from config import SUPERADMIN_ID

# router = Router()


# @router.message()
# async def ignore_unmatched_messages(message: types.Message):
#     """Hech bir handler mos kelmasa, jim turadi"""
#     return  # hech qanday javob yubormaydi
# # ===================== /start komandasi =====================
# @router.message(Command("start"))
# async def cmd_start(message: types.Message):
#     tg_id = message.from_user.id
#     full_name = message.from_user.full_name

#     # 🔹 SuperAdmin uchun
#     if int(tg_id) == int(SUPERADMIN_ID):
#         user = fetchone("SELECT * FROM users WHERE telegram_id = :tid", {"tid": tg_id})
#         if not user:
#             execute("""
#                 INSERT INTO users (telegram_id, full_name, role)
#                 VALUES (:tid, :name, 'superadmin')
#             """, {"tid": tg_id, "name": full_name})

#         await message.answer(
#             "👑 <b>Salom, SuperAdmin!</b>\nHISOBOT24 boshqaruv paneliga xush kelibsiz!",
#             reply_markup=get_superadmin_kb(),
#             parse_mode="HTML"
#         )
#         return

#     # 🔹 Oddiy foydalanuvchi uchun
#     user = fetchone("SELECT role FROM users WHERE telegram_id=:tid", {"tid": tg_id})

#     if not user:
#         await message.answer("👋 Salom! Siz hali tizimda ro‘yxatdan o‘tmagansiz.")
#         return

#     role = user["role"]

#     if role == "superadmin":
#         await message.answer(
#             "👑 <b>Salom, SuperAdmin!</b>\nPanelga xush kelibsiz!",
#             reply_markup=get_superadmin_kb(),
#             parse_mode="HTML"
#         )
#     elif role == "admin":
#         await message.answer(
#             "👨‍💼 <b>Salom, Filial Admin!</b>\nSiz filial boshqaruv panelidasiz.",
#             reply_markup=get_admin_kb(),
#             parse_mode="HTML"
#         )
#     elif role == "worker":
#         await message.answer(
#             "👷‍♂️ <b>Salom, Ishchi!</b>\nHisobot tizimi ishga tayyor.",
#             reply_markup=get_worker_kb(),
#             parse_mode="HTML"
#         )
#     else:
#         await message.answer("⚠️ Sizning ro‘lingiz aniqlanmadi.")


# # ===================== MENYUGA QAYTISH =====================
# @router.message(F.text == "⬅️ Menyuga qaytish")
# async def back_to_main_menu(message: types.Message):
#     tg_id = message.from_user.id
#     user = fetchone("SELECT role FROM users WHERE telegram_id=:tid", {"tid": tg_id})

#     if not user:
#         await message.answer("⚠️ Tizimda foydalanuvchi topilmadi.")
#         return

#     role = user["role"]

#     if role == "superadmin":
#         await message.answer("📋 SuperAdmin menyusiga qaytdingiz.", reply_markup=get_superadmin_kb())
#     elif role == "admin":
#         await message.answer("📋 Filial admin menyusiga qaytdingiz.", reply_markup=get_admin_kb())
#     elif role == "worker":
#         await message.answer("📋 Ishchi menyusiga qaytdingiz.", reply_markup=get_worker_kb())
#     else:
#         await message.answer("⚠️ Tizimda ro‘lingiz aniqlanmadi.")
# src/handlers/start.py
from aiogram import Router, F, types
from aiogram.filters import Command
from keyboards.superadmin_kb import get_superadmin_kb
from keyboards.admin_kb import get_admin_kb
from keyboards.worker_kb import get_worker_kb
from database import fetchone, execute
from config import SUPERADMIN_ID

router = Router()



# ===================== /start komandasi =====================
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    tg_id = message.from_user.id
    full_name = message.from_user.full_name

    # 🔹 SuperAdmin
    allowed = [s.strip() for s in str(SUPERADMIN_ID).split(",") if s.strip()]
    if str(tg_id) in allowed:
        user = fetchone("SELECT * FROM users WHERE telegram_id = :tid", {"tid": tg_id})
        if not user:
            execute("""
                INSERT INTO users (telegram_id, full_name, role)
                VALUES (:tid, :name, 'superadmin')
            """, {"tid": tg_id, "name": full_name})

        await message.answer(
            "👑 <b>Salom, SuperAdmin!</b>\nHISOBOT24 boshqaruv paneliga xush kelibsiz!",
            reply_markup=get_superadmin_kb(),
            parse_mode="HTML"
        )
        return

    # 🔹 Oddiy foydalanuvchi
    user = fetchone("SELECT role FROM users WHERE telegram_id=:tid", {"tid": tg_id})
    if not user:
        await message.answer("👋 Salom! Siz hali tizimda ro‘yxatdan o‘tmagansiz.")
        return

    role = user["role"]
    if role == "admin":
        await message.answer(
            "👨‍💼 <b>Salom, Filial Admin!</b>\nSiz filial boshqaruv panelidasiz.",
            reply_markup=get_admin_kb(),
            parse_mode="HTML"
        )
    elif role == "worker":
        await message.answer(
            "👷‍♂️ <b>Salom, Ishchi!</b>\nHisobot tizimi ishga tayyor.",
            reply_markup=get_worker_kb(),
            parse_mode="HTML"
        )
    else:
        await message.answer("⚠️ Sizning ro‘lingiz aniqlanmadi.")
