from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from keyboards.admin_kb import admin_menu
from keyboards.worker_kb import worker_menu
from database import db
import datetime

router = Router()

# --- FSM holatlari ---
from aiogram.fsm.state import StatesGroup, State


class AddWorker(StatesGroup):
    waiting_for_name = State()
    waiting_for_tg_id = State()


class DeleteWorker(StatesGroup):
    waiting_for_id = State()


class FineBonusState(StatesGroup):
    waiting_for_worker_id = State()
    choosing_type = State()
    waiting_for_reason = State()
    waiting_for_amount = State()


# --- Admin menyusi ---
@router.message(Command("admin"))
async def admin_panel(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    admin = cur.execute("SELECT * FROM admins WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not admin:
        return await msg.answer("❌ Siz admin sifatida ro‘yxatdan o‘tmagansiz.")
    await msg.answer("🧑‍💼 Filial admin menyusi:", reply_markup=admin_menu())


# --- 👷 Ishchilar ro‘yxati ---
@router.message(F.text == "👷 Ishchilar ro‘yxati")
async def show_workers(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    admin = cur.execute("SELECT filial_id FROM admins WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not admin:
        return await msg.answer("❌ Siz admin emassiz.")
    workers = cur.execute("SELECT id, name, tg_id FROM workers WHERE filial_id=?", (admin[0],)).fetchall()
    if not workers:
        return await msg.answer("📭 Sizning filialda ishchilar yo‘q.")
    text = "👷 <b>Ishchilar ro‘yxati:</b>\n\n"
    for w in workers:
        text += f"ID: <code>{w[0]}</code> | {w[1]} — {w[2]}\n"
    await msg.answer(text, parse_mode="HTML")


# --- ➕ Ishchi qo‘shish ---
@router.message(F.text == "➕ Ishchi qo‘shish")
async def add_worker_start(msg: types.Message, state: FSMContext):
    await msg.answer("👷 Ishchi ismini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddWorker.waiting_for_name)


@router.message(AddWorker.waiting_for_name)
async def add_worker_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("🔢 Ishchining Telegram ID raqamini kiriting (faqat raqam):")
    await state.set_state(AddWorker.waiting_for_tg_id)


@router.message(AddWorker.waiting_for_tg_id)
async def add_worker_finish(msg: types.Message, state: FSMContext):
    tg_id = msg.text.strip()
    if not tg_id.isdigit():
        return await msg.answer("⚠️ Faqat raqam kiriting (Telegram ID raqami).")

    data = await state.get_data()
    name = data["name"]

    conn = db.get_conn()
    cur = conn.cursor()
    admin = cur.execute("SELECT filial_id FROM admins WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not admin:
        return await msg.answer("❌ Siz admin emassiz.")
    filial_id = admin[0]

    cur.execute(
        "INSERT INTO workers (name, tg_id, filial_id) VALUES (?, ?, ?)",
        (name, tg_id, filial_id)
    )
    conn.commit()
    await msg.answer(f"✅ Ishchi qo‘shildi:\n👷 {name}\n🆔 ID: {tg_id}", reply_markup=admin_menu())
    await state.clear()


# --- 🗑 Ishchini o‘chirish ---
@router.message(F.text == "🗑 Ishchini o‘chirish")
async def delete_worker_start(msg: types.Message, state: FSMContext):
    await msg.answer("🆔 O‘chirmoqchi bo‘lgan ishchi ID raqamini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(DeleteWorker.waiting_for_id)


@router.message(DeleteWorker.waiting_for_id)
async def delete_worker_finish(msg: types.Message, state: FSMContext):
    worker_id = msg.text.strip()
    if not worker_id.isdigit():
        return await msg.answer("⚠️ Faqat raqam kiriting.")

    conn = db.get_conn()
    cur = conn.cursor()
    check = cur.execute("SELECT id FROM workers WHERE id=?", (worker_id,)).fetchone()
    if not check:
        return await msg.answer("❌ Bunday ishchi topilmadi.")
    cur.execute("DELETE FROM workers WHERE id=?", (worker_id,))
    conn.commit()
    await msg.answer("✅ Ishchi o‘chirildi.", reply_markup=admin_menu())
    await state.clear()


# --- 💸 Jarima yoki Bonus yozish ---
@router.message(F.text == "💸 Jarima/Bonus yozish")
async def ask_worker_id(msg: types.Message, state: FSMContext):
    await msg.answer("🔢 Ishchi ID raqamini kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FineBonusState.waiting_for_worker_id)


@router.message(FineBonusState.waiting_for_worker_id)
async def choose_type(msg: types.Message, state: FSMContext):
    worker_id = msg.text.strip()

    if not worker_id.isdigit():
        return await msg.answer("⚠️ Faqat raqam kiriting (ishchi ID raqami).")

    conn = db.get_conn()
    cur = conn.cursor()
    check = cur.execute("SELECT id, name FROM workers WHERE id=?", (worker_id,)).fetchone()
    if not check:
        return await msg.answer("❌ Bunday IDdagi ishchi topilmadi.")

    await state.update_data(worker_id=worker_id)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Bonus yozish"), KeyboardButton(text="➖ Jarima yozish")],
            [KeyboardButton(text="↩️ Bekor qilish")],
        ],
        resize_keyboard=True
    )

    await msg.answer(f"👷 Ishchi: {check[1]}\nTanlang:", reply_markup=kb)
    await state.set_state(FineBonusState.choosing_type)


# ➕ Bonus yozish
@router.message(F.text == "➕ Bonus yozish")
async def bonus_reason(msg: types.Message, state: FSMContext):
    await state.update_data(type="bonus")
    await msg.answer("📝 Bonus sababi yozing:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FineBonusState.waiting_for_reason)


# ➖ Jarima yozish
@router.message(F.text == "➖ Jarima yozish")
async def fine_reason(msg: types.Message, state: FSMContext):
    await state.update_data(type="fine")
    await msg.answer("📝 Jarima sababi yozing:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(FineBonusState.waiting_for_reason)


# 📝 Sababni yozish
@router.message(FineBonusState.waiting_for_reason)
async def enter_amount(msg: types.Message, state: FSMContext):
    await state.update_data(reason=msg.text)
    await msg.answer("💰 Miqdorini kiriting (so‘mda):")
    await state.set_state(FineBonusState.waiting_for_amount)


# 💰 Miqdorni yozish va bazaga saqlash
@router.message(FineBonusState.waiting_for_amount)
async def save_fine_or_bonus(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    amount = msg.text.strip()

    if not amount.isdigit():
        return await msg.answer("⚠️ Faqat raqam kiriting (so‘mda miqdor).")

    conn = db.get_conn()
    cur = conn.cursor()

    worker_id = int(data["worker_id"])
    reason = data["reason"]
    created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    filial = cur.execute("SELECT filial_id FROM workers WHERE id=?", (worker_id,)).fetchone()
    if not filial:
        return await msg.answer("❌ Ishchi topilmadi.")
    filial_id = filial[0]

    if data["type"] == "fine":
        cur.execute(
            "INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
            (worker_id, filial_id, reason, int(amount), created_at),
        )
        text = f"⚠️ Jarima yozildi:\n👷 ID: {worker_id}\nSabab: {reason}\nMiqdor: {amount} so‘m"
    else:
        cur.execute(
            "INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
            (worker_id, filial_id, reason, int(amount), created_at),
        )
        text = f"🎉 Bonus yozildi:\n👷 ID: {worker_id}\nSabab: {reason}\nMiqdor: {amount} so‘m"

    conn.commit()
    await msg.answer(f"✅ {text}", reply_markup=admin_menu())
    await state.clear()


# --- 📊 Bugungi hisobotlar ---
@router.message(F.text == "📊 Bugungi hisobotlar")
async def today_reports(msg: types.Message):
    today = datetime.date.today().strftime("%Y-%m-%d")
    conn = db.get_conn()
    cur = conn.cursor()
    admin = cur.execute("SELECT filial_id FROM admins WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not admin:
        return await msg.answer("❌ Siz admin emassiz.")
    reports = cur.execute(
        "SELECT w.name, r.text, r.created_at FROM reports r JOIN workers w ON w.id = r.worker_id WHERE r.filial_id=? AND r.created_at LIKE ?",
        (admin[0], f"{today}%")
    ).fetchall()
    if not reports:
        return await msg.answer("📭 Bugungi hisobotlar yo‘q.")
    text = "📅 <b>Bugungi hisobotlar:</b>\n\n"
    for r in reports:
        text += f"👷 {r[0]}\n🕒 {r[2]}\n🧾 {r[1]}\n\n"
    await msg.answer(text, parse_mode="HTML")


# --- 📈 Umumiy hisobotlar ---
@router.message(F.text == "📈 Umumiy hisobotlar")
async def all_reports(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    admin = cur.execute("SELECT filial_id FROM admins WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not admin:
        return await msg.answer("❌ Siz admin emassiz.")
    reports = cur.execute(
        "SELECT w.name, r.text, r.created_at FROM reports r JOIN workers w ON w.id = r.worker_id WHERE r.filial_id=? ORDER BY r.id DESC LIMIT 20",
        (admin[0],)
    ).fetchall()
    if not reports:
        return await msg.answer("📭 Hisobotlar yo‘q.")
    text = "📊 <b>Oxirgi 20 ta hisobot:</b>\n\n"
    for r in reports:
        text += f"👷 {r[0]}\n🕒 {r[2]}\n🧾 {r[1]}\n\n"
    await msg.answer(text, parse_mode="HTML")
