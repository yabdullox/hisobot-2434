from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from config import SUPERADMIN_ID
from keyboards.superadmin_kb import get_superadmin_kb
from aiogram import Router, F, types
from aiogram.types import FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from database import fetchall
from utils.excel_export import export_reports_to_excel
import os
import datetime
import database
import pandas as pd
import datetime
import os

router = Router()

# ===============================
# FSM holatlari
# ===============================
class AddBranchFSM(StatesGroup):
    name = State()
    branch_id = State()

class DelBranchFSM(StatesGroup):
    branch_id = State()

class AddAdminFSM(StatesGroup):
    name = State()
    phone = State()
    tg_id = State()
    branch_id = State()

class DelAdminFSM(StatesGroup):
    admin_id = State()

# ===============================
# Start
# ===============================
@router.message(Command("start"))
async def cmd_start(message: Message):
    if str(message.from_user.id) != str(SUPERADMIN_ID):
        await message.answer("❌ Siz SuperAdmin emassiz.")
        return
    await message.answer("👋 Salom, SuperAdmin!\nHISOBOT24 boshqaruv paneli ishga tayyor.", 
                         reply_markup=get_superadmin_kb())

# ===============================
# 📊 Bugungi hisobotlar
# ===============================
@router.message(F.text == "📊 Bugungi hisobotlar")
async def today_reports(message: Message):
    today = datetime.date.today()
    reports = database.fetchall("""
        SELECT r.id, u.full_name, r.branch_id, r.date, r.start_time, r.end_time, r.text
        FROM reports r
        LEFT JOIN users u ON r.user_id = u.telegram_id
        WHERE r.date = :today
        ORDER BY r.start_time ASC
    """, {"today": today})
    
    if not reports:
        await message.answer("📅 Buguncha hisobotlar mavjud emas.")
        return

    text = "📊 Bugungi hisobotlar:\n\n"
    for r in reports:
        text += (f"👤 {r['full_name'] or 'Nomaʼlum'}\n"
                 f"🏢 Filial ID: {r['branch_id']}\n"
                 f"🕘 {r['start_time'] or '-'} - {r['end_time'] or '-'}\n"
                 f"🧾 Hisobot: {r['text'] or '—'}\n\n")
    await message.answer(text)

# ===============================
# 📈 Umumiy hisobotlar
# ===============================
@router.message(F.text == "📈 Umumiy hisobotlar")
async def all_reports(message: Message):
    reports = database.fetchall("""
        SELECT r.id, u.full_name, r.branch_id, r.date, r.text
        FROM reports r
        LEFT JOIN users u ON r.user_id = u.telegram_id
        ORDER BY r.date DESC LIMIT 20
    """)
    if not reports:
        await message.answer("📊 Hali umumiy hisobotlar mavjud emas.")
        return
    text = "📈 So‘nggi 20 ta hisobot:\n\n"
    for r in reports:
        text += f"📅 {r['date']} — 👤 {r['full_name'] or 'Nomaʼlum'} — 🏢 {r['branch_id']}\n🧾 {r['text'] or '—'}\n\n"
    await message.answer(text)

# ===============================
# 🏢 Filiallar ro‘yxati
# ===============================
@router.message(F.text == "🏢 Filiallar ro‘yxati")
async def branch_list(message: Message):
    rows = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not rows:
        await message.answer("🏢 Hozircha filiallar mavjud emas.")
        return
    text = "🏢 Filiallar ro‘yxati:\n\n"
    for r in rows:
        text += f"🆔 {r['id']} — {r['name']}\n"
    await message.answer(text)

# ===============================
# ➕ Filial qo‘shish
# ===============================
@router.message(F.text == "➕ Filial qo‘shish")
async def add_branch_start(message: Message, state: FSMContext):
    await state.set_state(AddBranchFSM.name)
    await message.answer("🏢 Filial nomini kiriting:")

@router.message(AddBranchFSM.name)
async def add_branch_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddBranchFSM.branch_id)
    await message.answer("🆔 Filial ID raqamini kiriting (faqat raqam):")

@router.message(AddBranchFSM.branch_id)
async def add_branch_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Faqat raqam kiriting.")
        return
    data = await state.get_data()
    database.execute("INSERT INTO branches (id, name) VALUES (:id, :name)", 
                     {"id": int(message.text), "name": data["name"]})
    await state.clear()
    await message.answer(f"✅ Filial qo‘shildi: {data['name']} (ID: {message.text})")

# ===============================
# ❌ Filialni o‘chirish
# ===============================
@router.message(F.text == "❌ Filialni o‘chirish")
async def del_branch_start(message: Message, state: FSMContext):
    rows = database.fetchall("SELECT id, name FROM branches")
    if not rows:
        await message.answer("❌ Filiallar mavjud emas.")
        return
    text = "🗑️ Qaysi filialni o‘chirmoqchisiz?\n\n"
    for r in rows:
        text += f"{r['id']}. {r['name']}\n"
    await message.answer(text)
    await state.set_state(DelBranchFSM.branch_id)

@router.message(DelBranchFSM.branch_id)
async def del_branch_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Filial ID raqamini kiriting.")
        return
    database.execute("DELETE FROM branches WHERE id=:id", {"id": int(message.text)})
    await state.clear()
    await message.answer("✅ Filial muvaffaqiyatli o‘chirildi.")

# ===============================
# 👥 Adminlar ro‘yxati
# ===============================
@router.message(F.text == "👥 Adminlar ro‘yxati")
async def admin_list(message: Message):
    admins = database.fetchall("SELECT id, full_name, telegram_id, branch_id FROM users WHERE role='admin'")
    if not admins:
        await message.answer("👥 Adminlar hozircha mavjud emas.")
        return
    text = "👥 Adminlar:\n\n"
    for a in admins:
        text += f"{a['id']}. {a['full_name']} — 🆔 {a['telegram_id']} — Filial: {a['branch_id']}\n"
    await message.answer(text)

# ===============================
# ➕ Admin qo‘shish
# ===============================
@router.message(F.text == "➕ Admin qo‘shish")
async def add_admin_start(message: Message, state: FSMContext):
    await state.set_state(AddAdminFSM.name)
    await message.answer("👤 Admin ismini kiriting:")

@router.message(AddAdminFSM.name)
async def add_admin_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddAdminFSM.phone)
    await message.answer("📞 Admin telefon raqamini kiriting:")

@router.message(AddAdminFSM.phone)
async def add_admin_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(AddAdminFSM.tg_id)
    await message.answer("🆔 Admin Telegram ID kiriting:")

@router.message(AddAdminFSM.tg_id)
async def add_admin_tg(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Raqam kiriting.")
        return
    await state.update_data(tg_id=int(message.text))
    await state.set_state(AddAdminFSM.branch_id)
    await message.answer("🏢 Qaysi filialga biriktiriladi? Filial ID kiriting:")

@router.message(AddAdminFSM.branch_id)
async def add_admin_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Raqam kiriting.")
        return
    data = await state.get_data()
    database.execute("""
        INSERT INTO users (telegram_id, full_name, role, branch_id)
        VALUES (:tg, :fn, 'admin', :br)
    """, {"tg": data["tg_id"], "fn": f"{data['name']} ({data['phone']})", "br": int(message.text)})
    await state.clear()
    await message.answer("✅ Admin qo‘shildi.")

# ===============================
# 🗑️ Adminni o‘chirish
# ===============================
@router.message(F.text == "🗑️ Adminni o‘chirish")
async def del_admin_start(message: Message, state: FSMContext):
    admins = database.fetchall("SELECT id, full_name FROM users WHERE role='admin'")
    if not admins:
        await message.answer("👥 Adminlar yo‘q.")
        return
    text = "🗑️ O‘chirish uchun admin ID kiriting:\n\n"
    for a in admins:
        text += f"{a['id']}. {a['full_name']}\n"
    await message.answer(text)
    await state.set_state(DelAdminFSM.admin_id)

@router.message(DelAdminFSM.admin_id)
async def del_admin_finish(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Admin ID kiriting.")
        return
    database.execute("DELETE FROM users WHERE id=:id AND role='admin'", {"id": int(message.text)})
    await state.clear()
    await message.answer("✅ Admin o‘chirildi.")

# ===============================
# 📤 EXPORT MENU — 2 variantli menyu
# ===============================
@router.message(F.text == "📤 Export (Excel/CSV)")
async def export_menu(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugungi hisobotni eksport qilish")],
            [KeyboardButton(text="📊 Umumiy hisobotni eksport qilish")],
            [KeyboardButton(text="⬅️ Menyuga qaytish")]
        ],
        resize_keyboard=True
    )
    await message.answer("📤 Qaysi hisobotni eksport qilamiz?", reply_markup=kb)


# ===============================
# 📅 BUGUNGI HISOBOTNI EXPORT QILISH
# ===============================
@router.message(F.text == "📅 Bugungi hisobotni eksport qilish")
async def export_today_reports(message: types.Message):
    today = datetime.date.today()
    reports = fetchall("""
        SELECT 
            u.full_name AS Ishchi,
            b.name AS Filial,
            r.date AS Sana,
            r.start_time AS "Boshlanish vaqti",
            r.end_time AS "Tugash vaqti",
            r.text AS "Hisobot matni"
        FROM reports r
        LEFT JOIN users u ON u.telegram_id = r.user_id
        LEFT JOIN branches b ON b.id = r.branch_id
        WHERE r.date = :today
        ORDER BY r.start_time ASC
    """, {"today": today})

    if not reports:
        await message.answer("📅 Bugungi hisobotlar mavjud emas.")
        return

    # ✅ To‘g‘ri nom bilan eksport
    file_path = export_reports_to_excel(
        reports,
        branch_name=f"Bugungi_{today}",
        report_type="Bugungi Hisobot"
    )
    await message.answer_document(
        FSInputFile(file_path),
        caption=f"📅 Bugungi hisobotlar ({today}) — Excel fayl"
    )
    os.remove(file_path)


# ===============================
# 📊 UMUMIY HISOBOTNI EXPORT QILISH
# ===============================
@router.message(F.text == "📊 Umumiy hisobotni eksport qilish")
async def export_all_reports(message: types.Message):
    reports = fetchall("""
        SELECT 
            u.full_name AS Ishchi,
            b.name AS Filial,
            r.date AS Sana,
            r.start_time AS "Boshlanish vaqti",
            r.end_time AS "Tugash vaqti",
            r.text AS "Hisobot matni"
        FROM reports r
        LEFT JOIN users u ON u.telegram_id = r.user_id
        LEFT JOIN branches b ON b.id = r.branch_id
        ORDER BY r.date DESC
    """)

    if not reports:
        await message.answer("📊 Umumiy hisobotlar topilmadi.")
        return

    # ✅ Umumiy hisobot uchun alohida nom
    file_path = export_reports_to_excel(
        reports,
        branch_name="Barcha_Filiallar",
        report_type="Umumiy Hisobot"
    )
    await message.answer_document(
        FSInputFile(file_path),
        caption="📊 Umumiy hisobotlar (Excel)"
    )
    os.remove(file_path)

@router.message(Command("start"))
async def cmd_start(message: Message):
    if str(message.from_user.id) != str(SUPERADMIN_ID):
        await message.answer("❌ Siz SuperAdmin emassiz.")
        return
    await message.answer(
        "👋 Salom, SuperAdmin!\nHISOBOT24 boshqaruv paneli ishga tayyor.",
        reply_markup=get_superadmin_kb()
    )

# ===============================
# 💰 Bonus/Jarimalar ro‘yxati
# =============================== 
@router.message(F.text == "💰 Bonus/Jarimalar ro‘yxati")
async def show_all_fines_and_bonuses(message: Message):
    fines = database.fetchall("""
        SELECT u.full_name, f.amount, f.reason, f.created_at
        FROM fines f
        LEFT JOIN users u ON f.user_id = u.id
        ORDER BY f.created_at DESC
        LIMIT 20
    """)
    bonuses = database.fetchall("""
        SELECT u.full_name, b.amount, b.reason, b.created_at
        FROM bonuses b
        LEFT JOIN users u ON b.user_id = u.id
        ORDER BY b.created_at DESC
        LIMIT 20
    """)

    text = "💰 <b>So‘nggi 20 ta Bonus va Jarimalar</b>\n\n"
    if not fines and not bonuses:
        await message.answer("📂 Bonus yoki jarima yozuvlari topilmadi.")
        return

    if bonuses:
        text += "✅ <b>Bonuslar:</b>\n"
        for b in bonuses:
            text += f"👤 {b['full_name']} | +{b['amount']:,} so‘m\n📅 {b['created_at']}\n📝 {b['reason']}\n\n"
    if fines:
        text += "❌ <b>Jarimalar:</b>\n"
        for f in fines:
            text += f"👤 {f['full_name']} | -{f['amount']:,} so‘m\n📅 {f['created_at']}\n📝 {f['reason']}\n\n"

    await message.answer(text, parse_mode="HTML")
# =============================
# ⬅️ Menyuga qaytish
# =============================
@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_menu(message: Message):
    if str(message.from_user.id) != str(SUPERADMIN_ID):
        await message.answer("❌ Siz SuperAdmin emassiz.")
        return
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_superadmin_kb())