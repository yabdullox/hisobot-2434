from aiogram import Router, F, types
from keyboards.worker_kb import worker_menu
import datetime, aiosqlite
from database import db
from config import SUPERADMIN_ID

router = Router()
worker_state = {}

# 1️⃣ Ishni boshladim
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    await msg.answer("✅ Ishni boshladingiz. Omad!", reply_markup=worker_menu())

# 2️⃣ Ishni tugatdim
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=worker_menu())

# 3️⃣ Tozalash rasmi
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def send_clean_photo(msg: types.Message):
    await msg.answer("📸 Tozalash rasmini yuboring:", reply_markup=worker_menu())

# 4️⃣ Muammo yuborish
@router.message(F.text == "📸 Muammo yuborish")
async def send_problem_photo(msg: types.Message):
    await msg.answer("⚠️ Muammo haqida rasm/izoh yuboring:", reply_markup=worker_menu())

# 5️⃣ Bugungi hisobotlarim
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def today_reports(msg: types.Message):
    await msg.answer("📅 Bugungi hisobotlaringiz yo‘q yoki tayyor emas.", reply_markup=worker_menu())

# 6️⃣ Bonus/Jarimalarim
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def finance_info(msg: types.Message):
    await msg.answer("💰 Bonus va jarimalaringiz hozircha mavjud emas.", reply_markup=worker_menu())

# 7️⃣ Hisobot yuborish
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report(msg: types.Message):
    await msg.answer("✏️ Hisobot matnini yuboring:", reply_markup=worker_menu())

# 8️⃣ Menyuga qaytish
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
