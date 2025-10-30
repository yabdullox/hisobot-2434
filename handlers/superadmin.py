    # src/handlers/superadmin.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from keyboards.superadmin_kb import get_superadmin_kb
from config import SUPERADMIN_ID
from utils.excel_export import export_reports_to_excel

import database
import os
import datetime

router = Router()


# ===============================
# FSM holatlari (agar kerak bo'lsa keyin kengaytirish mumkin)
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
# Start (SuperAdmin tekshiruvi)
# ===============================
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    # SUPERADMIN_ID — string yoki vergul bilan bo'lingan IDlar bo'lishi mumkin
    allowed = [s.strip() for s in str(SUPERADMIN_ID).split(",") if s.strip()]
    if str(message.from_user.id) not in allowed:
        await message.answer("❌ Siz SuperAdmin emassiz.")
        return

    await message.answer(
        "👋 Salom, SuperAdmin!\nHISOBOT24 boshqaruv paneli ishga tayyor.",
        reply_markup=get_superadmin_kb()
    )


# ➕ Adminni filialga biriktirish - bosilganda adminlar ro'yxati chiqadi
@router.message(F.text == "➕ Adminni filialga biriktirish")
async def start_admin_branch_link(message: types.Message):
    # Adminlar ro'yxatini oling (role='admin')
    admins = database.fetchall("SELECT id, full_name, telegram_id FROM users WHERE role='admin' ORDER BY id")
    if not admins:
        await message.answer("👥 Hozircha adminlar mavjud emas.")
        return

    kb = InlineKeyboardMarkup()
    for a in admins:
        # callback format: link_admin:{admin_id}
        kb.add(InlineKeyboardButton(text=f"{a['full_name']} ({a['telegram_id']})", callback_data=f"link_admin:{a['id']}"))

    kb.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="link_admin:cancel"))
    await message.answer("👥 Adminni tanlang — keyin filialni tanlaysiz:", reply_markup=kb)


# Callback: admin tanlandi -> filiallar ro'yxatini ko'rsat
@router.callback_query(F.data.startswith("link_admin:"))
async def handle_admin_selected(callback: types.CallbackQuery):
    data = callback.data.split(":")[1]
    if data == "cancel":
        await callback.message.answer("❌ Bekor qilindi.")
        await callback.answer()
        return

    admin_id = int(data)
    # filiallar
    branches = database.fetchall("SELECT id, name FROM branches ORDER BY id")
    if not branches:
        await callback.message.answer("🏢 Hozircha filiallar mavjud emas.")
        await callback.answer()
        return

    kb = InlineKeyboardMarkup()
    for b in branches:
        # callback format: link_admin_confirm:{admin_id}:{branch_id}
        kb.add(InlineKeyboardButton(text=f"{b['name']} (ID:{b['id']})", callback_data=f"link_admin_confirm:{admin_id}:{b['id']}"))

    kb.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="link_admin:cancel"))
    await callback.message.answer("🏢 Qaysi filialga biriktirmoqchisiz? (bitta yoki bir nechta tanlang — ketma-ket bosing)", reply_markup=kb)
    await callback.answer()


# Callback: tasdiqlash -> jadvalga yozamiz (bitta tugma bosilganda qo'shiladi)
@router.callback_query(F.data.startswith("link_admin_confirm:"))
async def handle_admin_branch_confirm(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    admin_id = int(parts[1])
    branch_id = int(parts[2])

    # Chek — admin_branches jadvali borligini ta'minlash (agar kerak bo'lsa)
    database.execute("""
        CREATE TABLE IF NOT EXISTS admin_branches (
            id SERIAL PRIMARY KEY,
            admin_id BIGINT NOT NULL,
            branch_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tekshir: bunday bog'lanish mavjudmi?
    exists = database.fetchone(
        "SELECT id FROM admin_branches WHERE admin_id=:a AND branch_id=:b",
        {"a": admin_id, "b": branch_id}
    )
    if exists:
        await callback.answer("⚠️ Bu admin allaqachon ushbu filialga biriktirilgan.", show_alert=True)
        return

    # Chek: admin 5 tadan ortiq filialga biriktirilmasin
    count = database.fetchone(
        "SELECT COUNT(*) AS cnt FROM admin_branches WHERE admin_id=:a",
        {"a": admin_id}
    )
    if count and int(count.get("cnt", 0)) >= 5:
        await callback.answer("❌ Bu admin allaqachon 5 ta filialga biriktirilgan.", show_alert=True)
        return

    # Qo'shish
    database.execute(
        "INSERT INTO admin_branches (admin_id, branch_id) VALUES (:a, :b)",
        {"a": admin_id, "b": branch_id}
    )

    await callback.answer("✅ Admin muvaffaqiyatli biriktirildi.", show_alert=True)
    await callback.message.answer(f"✅ Admin ID {admin_id} ✅ Filial ID {branch_id} ga biriktirildi.")

# ===============================
# 📊 HISOBOT MENYUSI
# ===============================
@router.message(F.text.in_(["📊 Bugungi hisobotlar", "📈 Umumiy hisobotlar"]))
async def show_report_type_menu(message: types.Message):
    """Hisobot turi tanlash menyusi."""
    action = "today" if message.text == "📊 Bugungi hisobotlar" else "all"

    branches = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not branches:
        await message.answer("⚠️ Hozircha filiallar mavjud emas.")
        return

    buttons = [
        [types.KeyboardButton(text=b["name"])] for b in branches
    ]
    buttons.append([types.KeyboardButton(text="❌ Bekor qilish")])

    await message.answer(
        "📅 Qaysi filialning hisobotlarini ko‘rmoqchisiz?",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True,
            input_field_placeholder="Filialni tanlang 👇"
        )
    )

    # Holatni vaqtincha saqlab qo‘yamiz
    message.bot['report_mode'] = action


# ===============================
# ❌ BEKOR QILISH
# ===============================
@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: types.Message):
    """Bekor qilish tugmasi bosilganda menyuga qaytadi."""
    await message.answer("❌ Bekor qilindi.", reply_markup=get_superadmin_kb())


# ===============================
# 🗓️ HISOBOTLARNI KO‘RISH
# ===============================
@router.message()
async def show_reports_for_branch(message: types.Message):
    """Tanlangan filial uchun bugungi yoki umumiy hisobotlarni ko‘rsatadi."""
    branch_name = message.text.strip()

    # Faqat filial nomi bilan ishlaymiz
    branch = database.fetchone("SELECT id FROM branches WHERE name=:n", {"n": branch_name})
    if not branch:
        return  # boshqa tugmalar uchun jim turadi

    branch_id = branch["id"]
    mode = message.bot.get('report_mode', 'today')
    today = date.today()

    if mode == "today":
        query = """
            SELECT 
                r.user_id,
                u.full_name,
                r.date,
                r.start_time,
                r.end_time,
                r.text
            FROM reports r
            LEFT JOIN users u ON u.telegram_id = r.user_id
            WHERE DATE(r.date) = :today
              AND r.branch_id = :bid
              AND r.text IS NOT NULL
            ORDER BY r.date DESC, r.start_time
        """
        params = {"today": today, "bid": branch_id}
        title = f"📅 {branch_name} — Bugungi hisobotlar"
    else:
        query = """
            SELECT 
                r.user_id,
                u.full_name,
                r.date,
                r.start_time,
                r.end_time,
                r.text
            FROM reports r
            LEFT JOIN users u ON u.telegram_id = r.user_id
            WHERE r.branch_id = :bid
              AND r.text IS NOT NULL
            ORDER BY r.date DESC, r.start_time
        """
        params = {"bid": branch_id}
        title = f"📈 {branch_name} — Umumiy hisobotlar"

    reports = database.fetchall(query, params)

    if not reports:
        await message.answer("📭 Bu filialda hisobot topilmadi.")
        return

    # 📋 Chiroyli formatda chiqaramiz
    result_text = f"{title}\n\n"
    for r in reports:
        result_text += (
            f"👷 <b>{r['full_name'] or 'Noma’lum'}</b>\n"
            f"📅 {r['date']}\n"
            f"🕘 {r['start_time'] or '-'} — {r['end_time'] or '-'}\n"
            f"🧾 {r['text']}\n\n"
        )

    # Juda uzun bo‘lsa, bo‘lib yuboramiz
    if len(result_text) > 4000:
        parts = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
        for part in parts:
            await message.answer(part, parse_mode="HTML")
    else:
        await message.answer(result_text, parse_mode="HTML")

    # 🔙 Hisobotdan keyin menyuga qaytish
    await message.answer("⬅️ Asosiy menyu", reply_markup=get_superadmin_kb())








# ================== Umumiy filial hisobotlari (oxirgi 20)
@router.callback_query(F.data.startswith("all_branch:"))
async def show_all_reports(callback: types.CallbackQuery):
    branch_id = int(callback.data.split(":")[1])

    reports = database.fetchall(
        """
        SELECT r.*, u.full_name, u.telegram_id, b.name AS branch_name
        FROM reports r
        LEFT JOIN users u ON r.user_id = u.telegram_id
        LEFT JOIN branches b ON r.branch_id = b.id
        WHERE r.branch_id = :bid
        ORDER BY r.date DESC
        LIMIT 20
        """,
        {"bid": branch_id}
    )

    if not reports:
        await callback.message.answer("📭 Bu filialda hali hisobotlar yo‘q.")
        await callback.answer()
        return

    for r in reports:
        full_name = r.get("full_name", "—")
        branch = r.get("branch_name", "—")
        user_id = r.get("telegram_id", "—")
        date_str = str(r.get("date") or "—")
        time_str = str(r.get("end_time") or r.get("start_time") or "—")
        report_text = r.get("text") or "—"

        text = (
            f"🧾 <b>Yangi ishchi hisobot!</b>\n\n"
            f"👷 Ishchi: <b>{full_name}</b>\n"
            f"🏢 Filial ID: <b>{branch_id}</b> ({branch})\n"
            f"🆔 Telegram ID: <code>{user_id}</code>\n\n"
            f"📅 Sana: {date_str}\n"
            f"🕘 Vaqt: {time_str}\n\n"
            f"🧹 Hisobot matni:\n<code>{report_text}</code>"
        )

        await callback.message.answer(text, parse_mode="HTML")

    await callback.answer()



# ===============================
# Filiallar ro'yxati, qo'shish, o'chirish
# ===============================
@router.message(F.text == "🏢 Filiallar ro‘yxati")
async def branch_list(message: types.Message):
    rows = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not rows:
        await message.answer("🏢 Hozircha filiallar mavjud emas.")
        return
    text = "🏢 Filiallar ro‘yxati:\n\n"
    for r in rows:
        text += f"🆔 {r['id']} — {r['name']}\n"
    await message.answer(text)


@router.message(F.text == "➕ Filial qo‘shish")
async def add_branch_start(message: types.Message, state: FSMContext):
    await state.set_state(AddBranchFSM.name)
    await message.answer("🏢 Filial nomini kiriting:")


@router.message(AddBranchFSM.name)
async def add_branch_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddBranchFSM.branch_id)
    await message.answer("🆔 Filial ID raqamini kiriting (faqat raqam):")


@router.message(AddBranchFSM.branch_id)
async def add_branch_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Faqat raqam kiriting.")
        return
    data = await state.get_data()
    database.execute("INSERT INTO branches (id, name) VALUES (:id, :name)", {"id": int(message.text), "name": data["name"]})
    await state.clear()
    await message.answer(f"✅ Filial qo‘shildi: {data['name']} (ID: {message.text})")


@router.message(F.text == "❌ Filialni o‘chirish")
async def del_branch_start(message: types.Message, state: FSMContext):
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
async def del_branch_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Filial ID raqamini kiriting.")
        return
    database.execute("DELETE FROM branches WHERE id=:id", {"id": int(message.text)})
    await state.clear()
    await message.answer("✅ Filial muvaffaqiyatli o‘chirildi.")


# ===============================
# Adminlar ro'yxati va qo'shish/o'chirish
# ===============================
# @router.message(F.text == "👥 Adminlar ro‘yxati")
# async def admin_list(message: types.Message):
#     admins = database.fetchall("SELECT id, full_name, telegram_id, branch_id FROM users WHERE role='admin'")
#     if not admins:
#         await message.answer("👥 Adminlar hozircha mavjud emas.")
#         return
#     text = "👥 Adminlar:\n\n"
#     for a in admins:
#         text += f"{a['id']}. {a['full_name']} — 🆔 {a['telegram_id']} — Filial: {a.get('branch_id','—')}\n"
#     await message.answer(text)
@router.message(F.text == "👥 Adminlar ro‘yxati")
async def admin_list(message: types.Message):
    admins = database.fetchall("""
        SELECT id, full_name, telegram_id, branch_id
        FROM users
        WHERE role='admin'
        ORDER BY id
    """)

    if not admins:
        await message.answer("👥 Hozircha adminlar mavjud emas.")
        return

    text = "👥 <b>Adminlar ro‘yxati:</b>\n\n"
    for idx, a in enumerate(admins, start=1):
        name = a['full_name'] or "—"
        tg_id = a['telegram_id'] or "—"
        branch = a.get('branch_id', '—')

        text += (
            f"<b>{idx}.</b> 👤 <b>{name}</b>\n"
            f"🆔 <code>{tg_id}</code>\n"
            f"🏢 Filial ID: <b>{branch}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
        )

    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "➕ Admin qo‘shish")
async def add_admin_start(message: types.Message, state: FSMContext):
    await state.set_state(AddAdminFSM.name)
    await message.answer("👤 Admin ismini kiriting:")


@router.message(AddAdminFSM.name)
async def add_admin_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddAdminFSM.phone)
    await message.answer("📞 Admin telefon raqamini kiriting:")


@router.message(AddAdminFSM.phone)
async def add_admin_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(AddAdminFSM.tg_id)
    await message.answer("🆔 Admin Telegram ID kiriting:")


@router.message(AddAdminFSM.tg_id)
async def add_admin_tg(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Raqam kiriting.")
        return
    await state.update_data(tg_id=int(message.text))
    await state.set_state(AddAdminFSM.branch_id)
    await message.answer("🏢 Qaysi filialga biriktiriladi? Filial ID kiriting:")


@router.message(AddAdminFSM.branch_id)
async def add_admin_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Raqam kiriting.")
        return
    data = await state.get_data()
    database.execute(
        """
        INSERT INTO users (telegram_id, full_name, role, branch_id)
        VALUES (:tg, :fn, 'admin', :br)
        """,
        {"tg": data["tg_id"], "fn": f"{data['name']} ({data['phone']})", "br": int(message.text)}
    )
    await state.clear()
    await message.answer("✅ Admin qo‘shildi.")


@router.message(F.text == "🗑️ Adminni o‘chirish")
async def del_admin_start(message: types.Message, state: FSMContext):
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
async def del_admin_finish(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❗️Admin ID kiriting.")
        return
    database.execute("DELETE FROM users WHERE id=:id AND role='admin'", {"id": int(message.text)})
    await state.clear()
    await message.answer("✅ Admin o‘chirildi.")


# ===============================
# Export menyulari (Excel/CSV)
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


@router.message(F.text == "📅 Bugungi hisobotni eksport qilish")
async def export_today_reports(message: types.Message):
    today = datetime.date.today()
    reports = database.fetchall(
        """
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
        """,
        {"today": today}
    )

    if not reports:
        await message.answer("📅 Bugungi hisobotlar mavjud emas.")
        return

    file_path = export_reports_to_excel(reports, branch_name=f"Bugungi_{today}", report_type="Bugungi Hisobot")
    await message.answer_document(FSInputFile(file_path), caption=f"📅 Bugungi hisobotlar ({today}) — Excel fayl")
    try:
        os.remove(file_path)
    except Exception:
        pass


@router.message(F.text == "📊 Umumiy hisobotni eksport qilish")
async def export_all_reports(message: types.Message):
    reports = database.fetchall(
        """
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
        """
    )

    if not reports:
        await message.answer("📊 Umumiy hisobotlar topilmadi.")
        return

    file_path = export_reports_to_excel(reports, branch_name="Barcha_Filiallar", report_type="Umumiy Hisobot")
    await message.answer_document(FSInputFile(file_path), caption="📊 Umumiy hisobotlar (Excel)")
    try:
        os.remove(file_path)
    except Exception:
        pass


# ===============================
# Bonus/Jarimalar ro'yxati
# ===============================
@router.message(F.text == "💰 Bonus/Jarimalar ro‘yxati")
async def show_all_fines_and_bonuses(message: types.Message):
    fines = database.fetchall(
        """
        SELECT u.full_name, f.amount, f.reason, f.created_at
        FROM fines f
        LEFT JOIN users u ON f.user_id = u.telegram_id
        ORDER BY f.created_at DESC
        LIMIT 20
        """
    )
    bonuses = database.fetchall(
        """
        SELECT u.full_name, b.amount, b.reason, b.created_at
        FROM bonuses b
        LEFT JOIN users u ON b.user_id = u.telegram_id
        ORDER BY b.created_at DESC
        LIMIT 20
        """
    )

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


# ===============================
# Menyuga qaytish
# ===============================
@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_menu(message: types.Message):
    allowed = [s.strip() for s in str(SUPERADMIN_ID).split(",") if s.strip()]
    if str(message.from_user.id) not in allowed:
        await message.answer("❌ Siz SuperAdmin emassiz.")
        return
    await message.answer("🏠 Asosiy menyuga qaytdingiz.", reply_markup=get_superadmin_kb())
