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
from aiogram import Router, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, date
import database
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl import Workbook
from keyboards.superadmin_kb import get_superadmin_kb
from config import SUPERADMIN_ID
from utils.excel_export import export_reports_to_excel
from datetime import datetime, date
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
# 📊 HISOBOTLAR BO‘LIMI
# ===============================
@router.message(F.text.in_(["📊 Bugungi hisobotlar", "📈 Umumiy hisobotlar"]))
async def choose_report_type(message: types.Message):
    """Hisobot turi tanlangandan keyin filiallar chiqadi."""
    action = "today" if message.text == "📊 Bugungi hisobotlar" else "all"

    branches = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not branches:
        await message.answer("⚠️ Hozircha filiallar mavjud emas.")
        return

    # Inline tugmalar yaratamiz
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=b["name"], callback_data=f"{action}_branch:{b['id']}")]
            for b in branches
        ] + [
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )

    await message.answer(
        f"📅 Qaysi filialning {'bugungi' if action == 'today' else 'umumiy'} hisobotlarini ko‘rmoqchisiz?",
        reply_markup=kb
    )


# ===============================
# ❌ BEKOR QILISH
# ===============================
@router.callback_query(F.data == "cancel")
async def cancel_action(callback: types.CallbackQuery):
    await callback.message.answer("❌ Bekor qilindi.", reply_markup=get_superadmin_kb())
    await callback.answer()




# ===============================
# 📅 BUGUNGI HISOBOTLAR
# ===============================
@router.callback_query(F.data.startswith("today_branch:"))
async def show_today_reports(callback: types.CallbackQuery):
    """Bugungi filial hisobotlarini ko‘rsatadi."""
    branch_id = int(callback.data.split(":")[1])
    today = date.today()

    reports = database.fetchall("""
        SELECT 
            r.user_id,
            u.full_name,
            u.branch_id,
            r.date,
            r.start_time,
            r.end_time,
            r.text,
            b.name AS branch_name
        FROM reports r
        LEFT JOIN users u ON u.telegram_id = r.user_id
        LEFT JOIN branches b ON b.id = r.branch_id
        WHERE DATE(r.date) = :today AND r.branch_id = :bid AND r.text IS NOT NULL
        ORDER BY r.date DESC, r.start_time
    """, {"today": today, "bid": branch_id})

    if not reports:
        await callback.message.answer("📭 Bu filialda bugun hisobot yo‘q.")
        await callback.answer()
        return

    branch_name = reports[0]["branch_name"] or f"ID: {branch_id}"
    result = f"📅 <b>{branch_name}</b> — bugungi hisobotlar:\n\n"

    for r in reports:
        result += (
            f"👷‍♂️ <b>Ishchi:</b> {r['full_name'] or 'Noma’lum'}\n"
            f"🏢 <b>Filial:</b> {r['branch_name']} (ID: {r['branch_id']})\n"
            f"🆔 <b>Telegram ID:</b> <code>{r['user_id']}</code>\n\n"
            f"📅 <b>Sana:</b> {r['date']}\n"
            f"🕒 <b>Vaqt:</b> {r['start_time'] or '-'} — {r['end_time'] or '-'}\n\n"
            f"🧾 <b>Hisobot:</b>\n{r['text']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    await callback.message.answer(result, parse_mode="HTML")
    await callback.answer()


# ===============================
# 📈 UMUMIY HISOBOTLAR
# ===============================
@router.callback_query(F.data.startswith("all_branch:"))
async def show_all_reports(callback: types.CallbackQuery):
    """Tanlangan filial uchun umumiy hisobotlar."""
    branch_id = int(callback.data.split(":")[1])

    reports = database.fetchall("""
        SELECT 
            r.user_id,
            u.full_name,
            u.branch_id,
            r.date,
            r.start_time,
            r.end_time,
            r.text,
            b.name AS branch_name
        FROM reports r
        LEFT JOIN users u ON u.telegram_id = r.user_id
        LEFT JOIN branches b ON b.id = r.branch_id
        WHERE r.branch_id = :bid AND r.text IS NOT NULL
        ORDER BY r.date DESC, r.start_time
    """, {"bid": branch_id})

    if not reports:
        await callback.message.answer("📭 Bu filialda hali hisobotlar yo‘q.")
        await callback.answer()
        return

    branch_name = reports[0]["branch_name"] or f"ID: {branch_id}"
    result = f"📈 <b>{branch_name}</b> — umumiy hisobotlar:\n\n"

    for r in reports:
        result += (
            f"👷‍♂️ <b>Ishchi:</b> {r['full_name'] or 'Noma’lum'}\n"
            f"🏢 <b>Filial:</b> {r['branch_name']} (ID: {r['branch_id']})\n"
            f"🆔 <b>Telegram ID:</b> <code>{r['user_id']}</code>\n\n"
            f"📅 <b>Sana:</b> {r['date']}\n"
            f"🕒 <b>Vaqt:</b> {r['start_time'] or '-'} — {r['end_time'] or '-'}\n\n"
            f"🧾 <b>Hisobot:</b>\n{r['text']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

    await callback.message.answer(result, parse_mode="HTML")
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
        SELECT 
            u.id,
            u.full_name,
            u.telegram_id,
            u.branch_id,
            u.role,
            u.created_at,
            b.name AS branch_name
        FROM users u
        LEFT JOIN branches b ON b.id = u.branch_id
        WHERE u.role IN ('admin', 'superadmin', 'worker')
        ORDER BY u.id ASC
    """)

    if not admins:
        await message.answer("👥 Hozircha foydalanuvchilar mavjud emas.")
        return

    text = "👥 <b>Foydalanuvchilar ro‘yxati:</b>\n\n"
    for idx, a in enumerate(admins, start=1):
        name = a['full_name'] or "—"
        tg_id = a['telegram_id'] or "—"
        branch = a['branch_name'] or f"ID: {a['branch_id'] or '—'}"
        role = a['role'] or "—"
        created = a['created_at'].strftime('%Y-%m-%d %H:%M') if a.get('created_at') else "—"

        text += (
            f"<b>{idx}.</b> 👤 <b>{name}</b>\n"
            f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
            f"🏢 <b>Filial:</b> {branch}\n"
            f"⚙️ <b>Roli:</b> {role}\n"
            f"🕒 <b>Qo‘shilgan:</b> {created}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # Har 40 tadan keyin alohida xabar yuboriladi (limitdan chiqmaslik uchun)
        if idx % 40 == 0:
            await message.answer(text, parse_mode="HTML")
            text = ""

    # Qolganlari
    if text:
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
    admins = database.fetchall("""
        SELECT 
            u.id,
            u.full_name,
            u.telegram_id,
            u.branch_id,
            b.name AS branch_name
        FROM users u
        LEFT JOIN branches b ON b.id = u.branch_id
        WHERE u.role = 'admin'
        ORDER BY u.id ASC
    """)

    if not admins:
        await message.answer("👥 Adminlar hozircha mavjud emas.")
        return

    # Matnni to‘plab ketamiz
    text = "🗑️ <b>O‘chirish uchun admin ID kiriting:</b>\n\n"
    messages = []  # keyinchalik bo‘lib yuboramiz
    for a in admins:
        name = a["full_name"] or "—"
        tg_id = a["telegram_id"] or "—"
        branch = a["branch_name"] or f"Filial ID: {a['branch_id'] or '—'}"

        block = (
            f"<b>{a['id']}.</b> 👤 {name}\n"
            f"🆔 <code>{tg_id}</code>\n"
            f"🏢 {branch}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # Xabar uzunligini nazorat qilamiz (Telegram limiti ~4096 belgi)
        if len(text) + len(block) > 3500:
            messages.append(text)
            text = ""

        text += block

    if text:
        messages.append(text)

    # Hammasini yuboramiz
    for msg_text in messages:
        await message.answer(msg_text, parse_mode="HTML")

    await state.set_state(DelAdminFSM.admin_id)


# ===============================
# Export menyulari (Excel/CSV)
# ===============================
# =====================================
# 📤 Export menyusi
# =====================================
@router.message(F.text == "📤 Export (Excel / CSV)")
async def export_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Bugungi hisobotni eksport qilish", callback_data="export:today"),
        ],
        [
            InlineKeyboardButton(text="📆 Umumiy barcha hisobotlar (Excel)", callback_data="export:all")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="export:cancel")
        ]
    ])
    await message.answer("📊 Qaysi turdagi hisobotni eksport qilmoqchisiz?", reply_markup=kb)


# =====================================
# 📆 Umumiy barcha hisobotlarni Excel’ga eksport qilish
# =====================================
@router.callback_query(F.data == "export:all")
async def export_all_reports(callback: types.CallbackQuery):
    try:
        reports = database.fetchall("""
            SELECT 
                u.full_name AS worker_name,
                u.branch_id,
                b.name AS branch_name,
                r.date,
                r.start_time,
                r.end_time,
                r.text AS report_text
            FROM reports r
            JOIN users u ON r.user_id = u.telegram_id
            JOIN branches b ON u.branch_id = b.id
            ORDER BY b.id, r.date DESC
        """)

        if not reports:
            await callback.message.answer("📭 Umumiy hisobotlar mavjud emas.")
            return

        wb = Workbook()
        sheet_map = {}

        # Excel dizayn
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        border = Border(left=Side(style="thin"), right=Side(style="thin"),
                        top=Side(style="thin"), bottom=Side(style="thin"))

        for r in reports:
            branch_name = r["branch_name"] or f"Filial_{r['branch_id']}"
            sheet_name = branch_name[:31]
            if sheet_name not in sheet_map:
                ws = wb.create_sheet(title=sheet_name)
                sheet_map[sheet_name] = ws
                headers = ["👷 Ishchi", "📅 Sana", "🕘 Boshlanish", "🏁 Tugash", "🧾 Hisobot matni"]
                ws.append(headers)
                for c in range(1, len(headers) + 1):
                    cell = ws.cell(row=1, column=c)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = align_center
                    cell.border = border

            ws = sheet_map[sheet_name]
            ws.append([
                r["worker_name"],
                r["date"].strftime("%Y-%m-%d") if r["date"] else "-",
                r["start_time"] or "-",
                r["end_time"] or "-",
                r["report_text"] or "",
            ])

        # Sheet kengligi
        for ws in wb.worksheets:
            for col in ws.columns:
                max_len = 0
                col_letter = col[0].column_letter
                for cell in col:
                    if cell.value:
                        max_len = max(max_len, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max_len + 4

        # Default bo'sh "Sheet"ni o'chiramiz
        if "Sheet" in wb.sheetnames:
            wb.remove(wb["Sheet"])

        # ⚙️ Fayl nomini yaratamiz (datetime moduli bilan to‘g‘ri ishlaydi)
        from datetime import datetime
        filename = f"Umumiy_Hisobot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        path = os.path.join("/tmp", filename)
        wb.save(path)

        await callback.message.answer_document(
            FSInputFile(path),
            caption="📊 <b>Barcha filiallar bo‘yicha umumiy Excel fayl tayyor!</b>",
            parse_mode="HTML"
        )
        os.remove(path)

    except Exception as e:
        await callback.message.answer(f"⚠️ Xatolik: {e}")


# =====================================
# 📅 Bugungi hisobotlar uchun filial tanlash
# =====================================
@router.callback_query(F.data == "export:today")
async def choose_branch_today(callback: types.CallbackQuery):
    branches = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not branches:
        await callback.message.answer("🏢 Hech qanday filial topilmadi.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=b["name"], callback_data=f"export_branch:{b['id']}")] for b in branches
    ])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="export:cancel")])

    await callback.message.answer("📍 Qaysi filialning bugungi hisobotini eksport qilmoqchisiz?", reply_markup=kb)


# =====================================
# 📍 Tanlangan filial uchun bugungi hisobotni Excel’ga eksport qilish
# =====================================
@router.callback_query(F.data.startswith("export_branch:"))
async def export_today_branch(callback: types.CallbackQuery):
    branch_id = int(callback.data.split(":")[1])
    from datetime import date
    today = date.today()

    reports = database.fetchall("""
        SELECT 
            u.full_name AS worker_name,
            r.date,
            r.start_time,
            r.end_time,
            r.text AS report_text,
            b.name AS branch_name
        FROM reports r
        JOIN users u ON r.user_id = u.telegram_id
        JOIN branches b ON u.branch_id = b.id
        WHERE r.date = :today AND u.branch_id = :bid
        ORDER BY r.start_time ASC
    """, {"today": today, "bid": branch_id})

    if not reports:
        await callback.message.answer("📭 Bugun bu filialda hisobot yo‘q.")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = reports[0]["branch_name"]

    headers = ["👷 Ishchi", "📅 Sana", "🕘 Boshlanish", "🏁 Tugash", "🧾 Hisobot matni"]
    ws.append(headers)

    # Dizayn
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(left=Side(style="thin"), right=Side(style="thin"),
                    top=Side(style="thin"), bottom=Side(style="thin"))

    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border

    for r in reports:
        ws.append([
            r["worker_name"],
            r["date"].strftime("%Y-%m-%d"),
            r["start_time"] or "-",
            r["end_time"] or "-",
            r["report_text"] or "",
        ])

    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_len + 4

    from datetime import datetime
    filename = f"{reports[0]['branch_name']}_Bugungi_{datetime.now().strftime('%Y%m%d')}.xlsx"
    path = os.path.join("/tmp", filename)
    wb.save(path)

    await callback.message.answer_document(
        FSInputFile(path),
        caption=f"📅 <b>{reports[0]['branch_name']}</b> filialining bugungi hisobotlari tayyor ✅",
        parse_mode="HTML"
    )
    os.remove(path)
# =====================================
# 📈 Umumiy barcha hisobotlar — bitta filial uchun
# =====================================
@router.callback_query(F.data == "export:all")
async def choose_branch_all(callback: types.CallbackQuery):
    """Filial tanlash — umumiy hisobot uchun."""
    branches = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not branches:
        await callback.message.answer("🏢 Hech qanday filial topilmadi.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=b["name"], callback_data=f"export_all_branch:{b['id']}")] for b in branches
    ])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="export:cancel")])

    await callback.message.answer("📊 Qaysi filialning <b>umumiy hisobotini</b> eksport qilmoqchisiz?", 
                                  reply_markup=kb, parse_mode="HTML")


# =====================================
# 📆 Umumiy barcha hisobotlar — filial tanlash (xuddi bugungidek)
# =====================================
@router.callback_query(F.data == "export:all")
async def choose_branch_all(callback: types.CallbackQuery):
    """Umumiy hisobotlar uchun filial tanlash."""
    branches = database.fetchall("SELECT id, name FROM branches ORDER BY id ASC")
    if not branches:
        await callback.message.answer("🏢 Hech qanday filial topilmadi.")
        return

    # Inline tugmalar (bir xil dizayn)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=b["name"], callback_data=f"export_all_branch:{b['id']}")] for b in branches
    ])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="export:cancel")])

    await callback.message.answer(
        "📊 Qaysi filialning <b>umumiy hisobotini</b> eksport qilmoqchisiz?",
        reply_markup=kb,
        parse_mode="HTML"
    )


# =====================================
# 📈 Tanlangan filial uchun umumiy hisobotni Excel’ga eksport qilish
# =====================================
@router.callback_query(F.data.startswith("export_all_branch:"))
async def export_all_branch_reports(callback: types.CallbackQuery):
    """Tanlangan filialning barcha hisobotlarini Excel'ga chiqaradi."""
    branch_id = int(callback.data.split(":")[1])

    reports = database.fetchall("""
        SELECT 
            u.full_name AS worker_name,
            r.date,
            r.start_time,
            r.end_time,
            r.text AS report_text,
            b.name AS branch_name
        FROM reports r
        JOIN users u ON r.user_id = u.telegram_id
        JOIN branches b ON u.branch_id = b.id
        WHERE u.branch_id = :bid AND r.text IS NOT NULL
        ORDER BY r.date DESC, r.start_time
    """, {"bid": branch_id})

    if not reports:
        await callback.message.answer("📭 Bu filialda hali umumiy hisobotlar yo‘q.")
        return

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from datetime import datetime
    import os
    from aiogram.types import FSInputFile

    wb = Workbook()
    ws = wb.active
    ws.title = reports[0]["branch_name"]

    # Headerlar
    headers = ["👷 Ishchi", "📅 Sana", "🕘 Boshlanish", "🏁 Tugash", "🧾 Hisobot matni"]
    ws.append(headers)

    # Header dizayni
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(left=Side(style="thin"), right=Side(style="thin"),
                    top=Side(style="thin"), bottom=Side(style="thin"))

    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = border

    # Ma'lumotlarni qo‘shish
    for r in reports:
        ws.append([
            r["worker_name"],
            r["date"].strftime("%Y-%m-%d"),
            r["start_time"] or "-",
            r["end_time"] or "-",
            r["report_text"] or "",
        ])

    # Ustun kengligi avtomatik
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_len + 4

    filename = f"{reports[0]['branch_name']}_Umumiy_{datetime.now().strftime('%Y%m%d')}.xlsx"
    path = os.path.join("/tmp", filename)
    wb.save(path)

    await callback.message.answer_document(
        FSInputFile(path),
        caption=f"📈 <b>{reports[0]['branch_name']}</b> filialining umumiy hisobotlari tayyor ✅",
        parse_mode="HTML"
    )
    os.remove(path)

# =====================================
# ❌ Bekor qilish
# =====================================
@router.callback_query(F.data == "export:cancel")
async def cancel_export(callback: types.CallbackQuery):
    await callback.message.answer("❌ Bekor qilindi.")
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
