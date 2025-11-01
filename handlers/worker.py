from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta, time, date
import pytz, os

import database
from config import SUPERADMIN_ID
from keyboards.worker_kb import get_worker_kb, get_bonus_kb
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

# Excel uchun


router = Router()

# --- Sozlamalar ---
UZ_TZ = pytz.timezone("Asia/Tashkent")
WORK_START = time(9, 0, 0)
CUTOFF = time(0, 10, 0)
RATE_PER_HOUR = 10_000


def business_now():
    return datetime.now(UZ_TZ)


def business_date(now=None):
    now = now or business_now()
    return now.date() if now.time() >= CUTOFF else now.date() - timedelta(days=1)


def fmt_sum(v):
    try:
        return f"{float(v):,.0f}".replace(",", " ")
    except:
        return str(v)


def parse_superadmins():
    if isinstance(SUPERADMIN_ID, int):
        return [SUPERADMIN_ID]
    elif isinstance(SUPERADMIN_ID, str):
        return [int(x.strip()) for x in SUPERADMIN_ID.split(",") if x.strip().isdigit()]
    return []

SUPERADMINS = parse_superadmins()


class ReportState(StatesGroup):
    income = State()
    expense = State()
    product_loop = State()
    confirm = State()


# --- 🕘 Ishni boshlash ---
@router.message(F.text == "🕘 Ishni boshladim")
async def start_work(message: Message):
    user_id = message.from_user.id
    now = business_now()
    bdate = business_date(now)
    start_time = now.strftime("%H:%M:%S")

    exists = database.fetchone("SELECT id FROM reports WHERE user_id=:u AND date=:d", {"u": user_id, "d": bdate})
    if exists:
        await message.answer("⚠️ Bugun ishni allaqachon boshlagansiz.")
        return

    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})
    branch_id = user["branch_id"] if user else None

    database.execute("""
        INSERT INTO reports (user_id, branch_id, date, start_time)
        VALUES (:u, :b, :d, :t)
    """, {"u": user_id, "b": branch_id, "d": bdate, "t": start_time})

    await message.answer(f"🕘 Ishni boshladingiz: <b>{start_time}</b>", parse_mode="HTML")


# --- 🏁 Ishni tugatdim ---
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: Message):
    user_id = message.from_user.id
    now = business_now()
    bdate = business_date(now)
    end_time = now.strftime("%H:%M:%S")

    database.execute("UPDATE reports SET end_time=:t WHERE user_id=:u AND date=:d",
                     {"t": end_time, "u": user_id, "d": bdate})

    await message.answer(f"🏁 Ish tugash vaqti saqlandi: <b>{end_time}</b>", parse_mode="HTML")


# --- 🧾 Hisobot yuborish FSM ---
@router.message(F.text == "🧾 Bugungi hisobotni yuborish")
async def start_report(message: Message, state: FSMContext):
    await message.answer("💰 Bugungi daromadni kiriting:")
    await state.set_state(ReportState.income)


@router.message(ReportState.income)
async def get_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except:
        await message.answer("❌ Raqam kiriting.")
        return
    await state.update_data(income=val)
    await message.answer("💸 Bugungi rashodni kiriting:")
    await state.set_state(ReportState.expense)


@router.message(ReportState.expense)
async def get_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except:
        await message.answer("❌ Raqam kiriting.")
        return
    await state.update_data(expense=val)
    user_id = message.from_user.id
    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:t", {"t": user_id})
    if not user:
        await message.answer("⚠️ Filial topilmadi.")
        await state.clear()
        return
    branch_id = user["branch_id"]
    products = database.list_products_by_branch(branch_id)
    await state.update_data(products=products, index=0, sold=[], branch_id=branch_id)

    if not products:
        await message.answer("📦 Omborda mahsulot yo‘q. Hisobotni yuboraymi? (ha/yo‘q)")
        await state.set_state(ReportState.confirm)
        return

    current = products[0]
    await message.answer(f"🛒 {current['product_name']} — nechta sotildi? ({current['unit']})")
    await state.set_state(ReportState.product_loop)


@router.message(ReportState.product_loop)
async def process_products(message: Message, state: FSMContext):
    data = await state.get_data()
    products, index, sold = data["products"], data["index"], data["sold"]

    try:
        amount = float(message.text)
    except:
        await message.answer("❌ Raqam kiriting.")
        return

    current = products[index]
    new_qty = max(float(current["quantity"]) - amount, 0)
    database.execute("UPDATE warehouse SET quantity=:q WHERE id=:i", {"q": new_qty, "i": current["id"]})
    sold.append({"name": current["product_name"], "amount": amount, "unit": current["unit"], "remaining": new_qty})

    index += 1
    if index < len(products):
        await state.update_data(index=index, sold=sold)
        next_p = products[index]
        await message.answer(f"🛒 {next_p['product_name']} — nechta sotildi? ({next_p['unit']})")
    else:
        await state.update_data(sold=sold)
        await message.answer("✅ Hammasi yozildi. Hisobotni yuboraymi? (ha/yo‘q)")
        await state.set_state(ReportState.confirm)


@router.message(ReportState.confirm)
async def finish_report(message: Message, state: FSMContext):
    if message.text.lower() not in ("ha", "xa", "yes"):
        await message.answer("❌ Hisobot bekor qilindi.")
        await state.clear()
        return

    data = await state.get_data()
    user_id = message.from_user.id
    bdate = business_date()

    branch_id = data.get("branch_id")
    income = data.get("income", 0)
    expense = data.get("expense", 0)
    remaining = income - expense
    sold = data.get("sold", [])

    sold_text = "\n".join([f"- {s['name']} — {s['amount']} {s['unit']}" for s in sold]) or "—"
    remain_text = "\n".join([f"- {s['name']} — {s['remaining']} {s['unit']}" for s in sold]) or "—"

    database.execute("""
        INSERT INTO reports (user_id, branch_id, date, income, expense, remaining, sold_items, notes)
        VALUES (:u, :b, :d, :i, :e, :r, :s, :n)
    """, {"u": user_id, "b": branch_id, "d": bdate, "i": income, "e": expense, "r": remaining,
          "s": sold_text, "n": remain_text})

    # 📤 Superadminlarga yuborish
    branch = database.fetchone("SELECT name FROM branches WHERE id=:id", {"id": branch_id})
    bname = branch["name"] if branch else "-"
    report_text = (f"📅 {bdate}\n🏢 {bname}\n👤 {message.from_user.full_name}\n\n"
                   f"💰 {fmt_sum(income)} | 💸 {fmt_sum(expense)} | 💵 {fmt_sum(remaining)}\n\n"
                   f"🛒 Sotilganlar:\n{sold_text}\n\n📦 Qolgan:\n{remain_text}")

    # Excel yaratish
    wb = Workbook()
    ws = wb.active
    ws.title = "Hisobot"
    ws.append(["Mahsulot", "Sotilgan", "Qolgan"])
    for s in sold:
        ws.append([s["name"], s["amount"], s["remaining"]])
    file_path = f"/tmp/hisobot_{bname}_{bdate}.xlsx".replace(" ", "_")
    wb.save(file_path)

    for admin in SUPERADMINS:
        try:
            await message.bot.send_message(admin, report_text)
            await message.bot.send_document(admin, FSInputFile(file_path), caption="📊 Excel hisobot")
        except Exception:
            pass

    if os.path.exists(file_path):
        os.remove(file_path)
    await state.clear()
    await message.answer("✅ Hisobot yuborildi va bazaga saqlandi.")


# --- 📋 Ombor holati ---
@router.message(F.text == "📋 Ombor holati")
async def show_warehouse(message: Message):
    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:t", {"t": message.from_user.id})
    if not user:
        await message.answer("⚠️ Filial topilmadi.")
        return
    products = database.list_products_by_branch(user["branch_id"])
    if not products:
        await message.answer("📦 Omborda mahsulot yo‘q.")
        return
    text = "📋 <b>Ombor holati:</b>\n\n"
    for p in products:
        text += f"• {p['product_name']} — {fmt_sum(p['quantity'])} {p['unit']}\n"
    await message.answer(text, parse_mode="HTML")

# ===============================
# 💰 Bonus / Jarimalar
# ===============================
@router.message(F.text == "💰 Bonus / Jarimalarim")
async def open_bonus_menu(message: Message):
    ensure_bonus_tables()
    await message.answer("💰 Bonus yoki jarimalarni tanlang:", reply_markup=get_bonus_kb())


@router.message(F.text == "📅 Bugungi")
async def show_today_bonus(message: Message):
    today = business_date()
    user = message.from_user.id
    b = database.fetchall("SELECT * FROM bonuses WHERE user_id=:u AND DATE(created_at)=:d", {"u": user, "d": today})
    f = database.fetchall("SELECT * FROM fines WHERE user_id=:u AND DATE(created_at)=:d", {"u": user, "d": today})

    txt = f"📅 <b>Bugungi ({today}) bonus va jarimalar:</b>\n\n"
    if not b and not f:
        txt += "📭 Hozircha yozuv yo‘q."
    else:
        if b:
            txt += "✅ Bonuslar:\n" + "\n".join([f"➕ {fmt_sum(x['amount'])} — {x['reason']}" for x in b]) + "\n\n"
        if f:
            txt += "❌ Jarimalar:\n" + "\n".join([f"➖ {fmt_sum(x['amount'])} — {x['reason']}" for x in f])
    await message.answer(txt, parse_mode="HTML")


@router.message(F.text == "📊 Umumiy")
async def show_all_bonus(message: Message):
    user = message.from_user.id
    b = database.fetchall("SELECT * FROM bonuses WHERE user_id=:u ORDER BY created_at DESC LIMIT 30", {"u": user})
    f = database.fetchall("SELECT * FROM fines WHERE user_id=:u ORDER BY created_at DESC LIMIT 30", {"u": user})
    txt = "📊 <b>So‘nggi 30 ta bonus/jarima:</b>\n\n"
    if not b and not f:
        txt += "📭 Yozuv yo‘q."
    else:
        if b:
            txt += "✅ Bonuslar:\n" + "\n".join([f"➕ {fmt_sum(x['amount'])} — {x['reason']}" for x in b]) + "\n\n"
        if f:
            txt += "❌ Jarimalar:\n" + "\n".join([f"➖ {fmt_sum(x['amount'])} — {x['reason']}" for x in f])
    await message.answer(txt, parse_mode="HTML")


# ===============================
# ⬅️ Orqaga
# ===============================
@router.message(F.text == "⬅️ Orqaga")
async def back(message: Message):
    await message.answer("🏠 Asosiy ishchi menyu:", reply_markup=get_worker_kb())
