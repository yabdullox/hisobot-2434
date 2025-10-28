from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.admin_kb import get_admin_kb
from aiogram.types import Message
import database

router = Router()

# ================== FSM HOLATLARI ==================
class AddWorker(StatesGroup):
    name = State()
    telegram_id = State()


# ================== START ==================
@router.message(Command("start"))
async def admin_start(message: types.Message):
    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})

    # Agar admin DBda yo'q bo‘lsa, ro‘yxatdan o‘tkazamiz
    if not admin:
        database.execute("""
            INSERT INTO users (telegram_id, full_name, role, branch_id)
            VALUES (:tid, :name, 'admin', 1)
        """, {"tid": message.from_user.id, "name": message.from_user.full_name})
        admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})

    # Agar adminning filial ID yo‘q bo‘lsa, avtomatik 1 ga tayinlaymiz
    if not admin["branch_id"]:
        database.execute("UPDATE users SET branch_id=1 WHERE telegram_id=:tid", {"tid": message.from_user.id})

    await message.answer(f"👋 Salom, {admin['full_name']}!\nSiz Filial Admin panelidasiz.",
                         reply_markup=get_admin_kb())


# ================== ISHCHILAR RO‘YXATI ==================
@router.message(F.text == "👥 Ishchilar ro‘yxati")
async def show_workers(message: types.Message):
    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})

    if not admin or not admin["branch_id"]:
        await message.answer("⚠️ Siz filialga biriktirilmagansiz.")
        return

    workers = database.fetchall(
        "SELECT * FROM users WHERE role='worker' AND branch_id=:b",
        {"b": admin["branch_id"]}
    )

    if not workers:
        await message.answer("📭 Filialda ishchilar yo‘q.")
        return

    text = "👥 <b>Ishchilar ro‘yxati</b>\n\n"
    for w in workers:
        text += f"🆔 <code>{w['telegram_id']}</code> — {w['full_name']}\n"

    await message.answer(text, parse_mode="HTML")


# ================== ISHCHI QO‘SHISH ==================
@router.message(F.text == "➕ Ishchi qo‘shish")
async def add_worker_start(message: types.Message, state: FSMContext):
    await message.answer("✏️ Ishchining to‘liq ismini kiriting:")
    await state.set_state(AddWorker.name)

@router.message(AddWorker.name)
async def add_worker_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📱 Endi ishchining Telegram ID raqamini kiriting:")
    await state.set_state(AddWorker.telegram_id)

@router.message(AddWorker.telegram_id)
async def add_worker_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    tid = message.text.strip()

    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})
    if not admin or not admin["branch_id"]:
        await message.answer("⚠️ Siz filialga ulanmagansiz.")
        await state.clear()
        return

    # 🔍 Ishchi mavjudligini tekshiramiz
    existing = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": tid})

    if existing:
        # Agar mavjud ishchi filialsiz bo‘lsa, unga filialni belgilaymiz
        if not existing["branch_id"]:
            database.execute("UPDATE users SET branch_id=:b WHERE telegram_id=:tid", {"b": admin["branch_id"], "tid": tid})
            await message.answer(f"✅ Avvaldan mavjud ishchi <b>{existing['full_name']}</b> filialga biriktirildi!\n🏢 Filial ID: {admin['branch_id']}", parse_mode="HTML")
        else:
            await message.answer("⚠️ Bu Telegram ID bilan ishchi allaqachon tizimda mavjud!")
        await state.clear()
        return

    # ✅ Yangi ishchini shu filialga biriktirib qo‘shamiz
    database.execute("""
        INSERT INTO users (telegram_id, full_name, role, branch_id)
        VALUES (:tid, :name, 'worker', :b)
    """, {"tid": tid, "name": name, "b": admin["branch_id"]})

    await message.answer(
        f"✅ Ishchi <b>{name}</b> muvaffaqiyatli qo‘shildi!\n"
        f"🏢 Filial ID: <code>{admin['branch_id']}</code>",
        parse_mode="HTML",
        reply_markup=get_admin_kb()
    )

    await state.clear()
# =================== ISHCHINI O‘CHIRISH ===================
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from keyboards.admin_kb import get_admin_kb

@router.message(F.text == "🗑️ Ishchini o‘chirish")
async def delete_worker_start(message: types.Message, state: FSMContext):
    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})
    if not admin or not admin["branch_id"]:
        await message.answer("⚠️ Siz filialga ulanmagansiz.")
        return

    workers = database.fetchall(
        "SELECT * FROM users WHERE role='worker' AND branch_id=:b",
        {"b": admin["branch_id"]}
    )

    if not workers:
        await message.answer("📭 Filialda ishchilar yo‘q.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{w['full_name']} ({w['telegram_id']})", callback_data=f"delw_{w['telegram_id']}")]
        for w in workers
    ])
    # 🔘 Bekor qilish tugmasi
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delete")])

    await message.answer("🗑️ O‘chirish uchun ishchini tanlang:", reply_markup=kb)


@router.callback_query(F.data.startswith("delw_"))
async def delete_worker_confirm(callback: types.CallbackQuery):
    tid = callback.data.split("_")[1]
    worker = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": tid})

    if not worker:
        await callback.message.edit_text("⚠️ Ishchi topilmadi.")
        return

    database.execute("DELETE FROM users WHERE telegram_id=:tid", {"tid": tid})
    await callback.message.edit_text(
        f"✅ Ishchi <b>{worker['full_name']}</b> tizimdan o‘chirildi.",
        parse_mode="HTML",
        reply_markup=None
    )


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ O‘chirish bekor qilindi.", reply_markup=None)
    await callback.message.answer("Asosiy menyu:", reply_markup=get_admin_kb())

# =================== JARIMA / BONUS YOZISH ===================
from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State

class FineBonus(StatesGroup):
    type = State()
    worker_id = State()
    reason = State()
    amount = State()

@router.message(F.text == "💰 Jarima/Bonus yozish")
async def fine_bonus_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Bonus qo‘shish", callback_data="bonus_add")],
        [InlineKeyboardButton(text="➖ Jarima yozish", callback_data="fine_add")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_fb")]
    ])
    await message.answer("💰 Jarima yoki Bonus turini tanlang:", reply_markup=kb)


@router.callback_query(F.data.in_(["bonus_add", "fine_add"]))
async def select_worker_for_fb(callback: types.CallbackQuery, state: FSMContext):
    fb_type = "bonus" if callback.data == "bonus_add" else "fine"
    await state.update_data(type=fb_type)

    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": callback.from_user.id})
    workers = database.fetchall(
        "SELECT * FROM users WHERE role='worker' AND branch_id=:b",
        {"b": admin["branch_id"]}
    )

    if not workers:
        await callback.message.edit_text("📭 Filialda ishchilar yo‘q.")
        await state.clear()
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{w['full_name']} ({w['telegram_id']})", callback_data=f"fbw_{w['telegram_id']}")]
        for w in workers
    ])
    kb.inline_keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_fb")])

    await callback.message.edit_text(
        "👤 Qaysi ishchiga yozmoqchisiz:",
        reply_markup=kb
    )


@router.callback_query(F.data.startswith("fbw_"))
async def fb_worker_selected(callback: types.CallbackQuery, state: FSMContext):
    tid = callback.data.split("_")[1]
    await state.update_data(worker_id=tid)
    await callback.message.edit_text("✏️ Sababni kiriting:")
    await state.set_state(FineBonus.reason)


@router.message(FineBonus.reason)
async def fb_get_reason(message: types.Message, state: FSMContext):
    await state.update_data(reason=message.text)
    await message.answer("💵 Summani kiriting (so‘mda):")
    await state.set_state(FineBonus.amount)


@router.message(FineBonus.amount)
async def fb_get_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = float(message.text)
    worker_id = data["worker_id"]
    fb_type = data["type"]
    reason = data["reason"]

    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})
    branch_id = admin["branch_id"]

    table = "bonuses" if fb_type == "bonus" else "fines"
    database.execute(f"""
        INSERT INTO {table} (user_id, branch_id, amount, reason, created_by)
        VALUES (:uid, :b, :a, :r, :by)
    """, {"uid": worker_id, "b": branch_id, "a": amount, "r": reason, "by": message.from_user.id})

    text = (
        f"✅ {'Bonus qo‘shildi' if fb_type == 'bonus' else 'Jarima yozildi'}!\n\n"
        f"👤 Ishchi ID: {worker_id}\n"
        f"💬 Sabab: {reason}\n"
        f"💵 Miqdor: {amount:.0f} so‘m"
    )
    await message.answer(text, reply_markup=get_admin_kb())
    await state.clear()


@router.callback_query(F.data == "cancel_fb")
async def cancel_fine_bonus(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Amaliyot bekor qilindi.", reply_markup=None)
    await callback.message.answer("Asosiy menyu:", reply_markup=get_admin_kb())

# =================== MUAMMOLAR ===================
@router.message(F.text == "💬 Muammolar")
async def problems_menu(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Bugungi muammolar", callback_data="today_problems")],
        [InlineKeyboardButton(text="📊 Umumiy muammolar", callback_data="all_problems")],
        [InlineKeyboardButton(text="⬅️ Menyuga qaytish", callback_data="cancel_problems")]
    ])
    await message.answer("💬 Qaysi muammolarni ko‘rmoqchisiz?", reply_markup=kb)


@router.callback_query(F.data.in_(["today_problems", "all_problems"]))
async def show_problems(callback: types.CallbackQuery):
    admin = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": callback.from_user.id})
    branch_id = admin["branch_id"]

    if callback.data == "today_problems":
        problems = database.fetchall("""
            SELECT p.description, p.photo_file_id, p.created_at, u.full_name
            FROM problems p
            JOIN users u ON u.telegram_id = p.user_id
            WHERE p.branch_id=:b AND DATE(p.created_at)=DATE('now')
            ORDER BY p.created_at DESC
        """, {"b": branch_id})
        title = "📅 Bugungi muammolar"
    else:
        problems = database.fetchall("""
            SELECT p.description, p.photo_file_id, p.created_at, u.full_name
            FROM problems p
            JOIN users u ON u.telegram_id = p.user_id
            WHERE p.branch_id=:b
            ORDER BY p.created_at DESC
        """, {"b": branch_id})
        title = "📊 Umumiy muammolar"

    if not problems:
        await callback.message.edit_text(f"{title} mavjud emas.")
        return

    text = f"{title}:\n\n"
    for p in problems:
        text += (
            f"👤 {p['full_name']}\n"
            f"🕒 {p['created_at']}\n"
            f"💬 {p['description']}\n\n"
        )
    await callback.message.edit_text(text)


@router.callback_query(F.data == "cancel_problems")
async def cancel_problems(callback: types.CallbackQuery):
    await callback.message.edit_text("Asosiy menyu:", reply_markup=get_admin_kb())

# ===============================
# 💰 Bonus/Jarimalar ro‘yxati
# ===============================
@router.message(F.text == "💰 Bonus/Jarimalar ro‘yxati")
async def show_branch_fines_and_bonuses(message: Message):
    admin = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:t", {"t": message.from_user.id})
    if not admin or not admin["branch_id"]:
        await message.answer("⚠️ Sizning filial ID topilmadi.")
        return

    branch_id = admin["branch_id"]

    fines = database.fetchall("""
        SELECT u.full_name, f.amount, f.reason, f.created_at
        FROM fines f
        LEFT JOIN users u ON f.user_id = u.id
        WHERE f.branch_id=:b
        ORDER BY f.created_at DESC
        LIMIT 20
    """, {"b": branch_id})

    bonuses = database.fetchall("""
        SELECT u.full_name, b.amount, b.reason, b.created_at
        FROM bonuses b
        LEFT JOIN users u ON b.user_id = u.id
        WHERE b.branch_id=:b
        ORDER BY b.created_at DESC
        LIMIT 20
    """, {"b": branch_id})

    text = f"💰 <b>Filial {branch_id} — Bonus/Jarimalar ro‘yxati</b>\n\n"
    if not fines and not bonuses:
        await message.answer("📂 Bu filialda hozircha bonus yoki jarimalar mavjud emas.")
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
# =================== MENYUGA QAYTISH ===================
from aiogram import F
from keyboards.admin_kb import get_admin_kb
from keyboards.superadmin_kb import get_superadmin_kb

@router.message(F.text == "⬅️ Menyuga qaytish")
async def back_to_main_menu(message: types.Message):
    user = database.fetchone("SELECT * FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})

    # Agar foydalanuvchi SuperAdmin bo‘lsa
    if user and user["role"] == "superadmin":
        await message.answer("📋 SuperAdmin menyusiga qaytdingiz.", reply_markup=get_superadmin_kb())

    # Agar foydalanuvchi filial admini bo‘lsa
    elif user and user["role"] == "admin":
        await message.answer("📋 Filial admin menyusiga qaytdingiz.", reply_markup=get_admin_kb())

    # Agar foydalanuvchi ishchi bo‘lsa
    elif user and user["role"] == "worker":
        from keyboards.worker_kb import get_worker_kb
        await message.answer("📋 Ishchi menyusiga qaytdingiz.", reply_markup=get_worker_kb())

    # Agar hech qaysi rol topilmasa
    else:
        await message.answer("⚠️ Tizimda ro‘lingiz aniqlanmadi.")
