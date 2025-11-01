from aiogram import Router, F, types
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date, time, timedelta
import pytz
import os

from config import SUPERADMIN_ID
import database
from keyboards.worker_kb import get_worker_kb, get_bonus_kb

# Excel uchun
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

router = Router()

# --- Sozlamalar ---
UZ_TZ = pytz.timezone("Asia/Tashkent")
WORK_START = time(9, 0, 0)
CUTOFF = time(0, 10, 0)
RATE_PER_HOUR = 10_000  # Bonus/jarima stavkasi


# --- SUPERADMIN ro‘yxati ---
def parse_superadmins():
    try:
        if isinstance(SUPERADMIN_ID, int):
            return [SUPERADMIN_ID]
        elif isinstance(SUPERADMIN_ID, str):
            return [int(x.strip()) for x in SUPERADMIN_ID.split(",") if x.strip().isdigit()]
    except Exception:
        return []
    return []

SUPERADMINS = parse_superadmins()


# --- Foydali funksiyalar ---
def business_now():
    return datetime.now(UZ_TZ)


def business_date(now_dt=None):
    now_dt = now_dt or business_now()
    bdate = now_dt.date()
    if now_dt.time() < CUTOFF:
        return bdate - timedelta(days=1)
    return bdate


def fmt_sum(v):
    try:
        return f"{float(v):,.0f}".replace(",", " ")
    except:
        return str(v)


def ensure_bonus_tables():
    try:
        database.execute("""
            CREATE TABLE IF NOT EXISTS bonuses (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                amount NUMERIC,
                reason TEXT,
                auto BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        database.execute("""
            CREATE TABLE IF NOT EXISTS fines (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                amount NUMERIC,
                reason TEXT,
                auto BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    except Exception:
        pass


# --- FSM holatlar ---
class ReportState(StatesGroup):
    income = State()
    expense = State()
    product_loop = State()
    confirm = State()


# ===============================
# 🕘 Ishni boshladim
# ===============================
@router.message(F.text == "🕘 Ishni boshladim")
async def start_work(message: Message):
    ensure_bonus_tables()
    user_id = message.from_user.id
    now = business_now()
    bdate = business_date(now)
    start_time = now.strftime("%H:%M:%S")

    existing = database.fetchone(
        "SELECT start_time FROM reports WHERE user_id=:u AND date=:d",
        {"u": user_id, "d": bdate}
    )

    if existing:
        prev = existing["start_time"]
        await message.answer(f"⚠️ Bugun ishni allaqachon boshlagansiz.\n🕘 Boshlagan vaqt: <b>{prev}</b>", parse_mode="HTML")
        return

    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})
    branch_id = user["branch_id"] if user else None

    database.execute("""
        INSERT INTO reports (user_id, branch_id, date, start_time)
        VALUES (:u, :b, :d, :t)
    """, {"u": user_id, "b": branch_id, "d": bdate, "t": start_time})

    # Bonus/Jarima
    diff_min = (now - datetime.combine(bdate, WORK_START, tzinfo=UZ_TZ)).total_seconds() / 60
    txt = f"🕘 Ish boshladingiz: <b>{start_time}</b>\n"

    if diff_min > 10:
        penalty = round((diff_min / 60) * RATE_PER_HOUR)
        database.execute("""
            INSERT INTO fines (user_id, amount, reason, auto)
            VALUES (:u, :a, :r, TRUE)
        """, {"u": user_id, "a": penalty, "r": f"{diff_min:.0f} daqiqa kech kelgan"})
        txt += f"❌ Jarima: {fmt_sum(penalty)} so‘m\n🔴 {diff_min:.0f} daqiqa kech keldingiz."
    elif diff_min < -5:
        bonus = round((abs(diff_min) / 60) * RATE_PER_HOUR)
        database.execute("""
            INSERT INTO bonuses (user_id, amount, reason, auto)
            VALUES (:u, :a, :r, TRUE)
        """, {"u": user_id, "a": bonus, "r": f"{abs(diff_min):.0f} daqiqa erta kelgan"})
        txt += f"✅ Bonus: {fmt_sum(bonus)} so‘m\n🟢 {abs(diff_min):.0f} daqiqa erta keldingiz."
    else:
        txt += "👍 O‘z vaqtida keldingiz."

    await message.answer(txt, parse_mode="HTML")


# ===============================
# 🏁 Ishni tugatdim
# ===============================
@router.message(F.text == "🏁 Ishni tugatdim")
async def finish_work(message: Message):
    user_id = message.from_user.id
    now = business_now()
    bdate = business_date(now)
    end_time = now.strftime("%H:%M:%S")

    database.execute("UPDATE reports SET end_time=:t WHERE user_id=:u AND date=:d",
                     {"t": end_time, "u": user_id, "d": bdate})

    await message.answer(
        f"🏁 Ish tugash vaqti saqlandi: <b>{end_time}</b>\n"
        f"ℹ️ 00:10 dan keyin yangi kun ochiladi.",
        parse_mode="HTML"
    )


# ===============================
# 🧾 Bugungi hisobot (FSM)
# ===============================
@router.message(F.text == "🧾 Bugungi hisobotni yuborish")
async def start_report(message: Message, state: FSMContext):
    await message.answer("💰 Bugungi daromadni kiriting:")
    await state.set_state(ReportState.income)


@router.message(ReportState.income)
async def get_income(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except ValueError:
        await message.answer("❌ Raqam kiriting, masalan: 1200000")
        return
    await state.update_data(income=val)
    await message.answer("💸 Bugungi rashodni kiriting:")
    await state.set_state(ReportState.expense)


@router.message(ReportState.expense)
async def get_expense(message: Message, state: FSMContext):
    try:
        val = float(message.text)
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting.")
        return

    await state.update_data(expense=val)
    user_id = message.from_user.id
    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:tid", {"tid": user_id})

    if not user:
        await message.answer("⚠️ Sizning filial topilmadi.")
        await state.clear()
        return

    branch_id = user["branch_id"]
    products = database.list_products_by_branch(branch_id)

    if not products:
        await message.answer("📦 Omborda mahsulotlar yo‘q.")
        await state.update_data(products=[], index=0, sold=[], branch_id=branch_id)
        await message.answer("✅ Hisobotni yuboraymi? (ha/yo‘q)")
        await state.set_state(ReportState.confirm)
        return

    await state.update_data(products=products, index=0, sold=[], branch_id=branch_id)
    current = products[0]
    await message.answer(f"🛒 {current['product_name']} — nechta sotildi? ({current['unit']})")
    await state.set_state(ReportState.product_loop)


@router.message(ReportState.product_loop)
async def process_products(message: Message, state: FSMContext):
    data = await state.get_data()
    products, index, sold = data["products"], data["index"], data["sold"]

    try:
        sold_amount = float(message.text)
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting.")
        return

    current = products[index]
    product_id = current["id"]
    old_qty = float(current["quantity"])
    new_qty = max(old_qty - sold_amount, 0)
    database.execute("UPDATE warehouse SET quantity=:q WHERE id=:id", {"q": new_qty, "id": product_id})

    sold.append({"name": current["product_name"], "amount": sold_amount, "unit": current["unit"], "remaining": new_qty})
    index += 1

    if index < len(products):
        next_p = products[index]
        await state.update_data(index=index, sold=sold)
        await message.answer(f"🛒 {next_p['product_name']} — nechta sotildi? ({next_p['unit']})")
    else:
        await state.update_data(sold=sold)
        await message.answer("✅ Hammasi yozildi! Hisobotni yuboraymi? (ha/yo‘q)")
        await state.set_state(ReportState.confirm)


@router.message(ReportState.confirm)
async def finish_report(message: Message, state: FSMContext):
    if message.text.lower() not in ("ha", "xa", "yes"):
        await message.answer("❌ Hisobot bekor qilindi.")
        await state.clear()
        return

    data = await state.get_data()
    user_id = message.from_user.id
    now = business_now()
    bdate = business_date(now)

    branch_id = data.get("branch_id")
    income = data.get("income", 0)
    expense = data.get("expense", 0)
    remaining = income - expense
    sold = data.get("sold", [])

    sold_text = "\n".join([f"- {s['name']} — {s['amount']} {s['unit']}" for s in sold]) or "—"
    remain_text = "\n".join([f"- {s['name']} — {s['remaining']} {s['unit']}" for s in sold]) or "—"

    # 🔹 Hisobotni bazaga yozamiz (duplikat bo‘lsa yangilaydi)
    database.execute("""
        INSERT INTO reports (user_id, branch_id, date, income, expense, remaining, sold_items, notes)
        VALUES (:u, :b, :d, :i, :e, :r, :s, :n)
        ON CONFLICT (user_id, date)
        DO UPDATE SET
            income=EXCLUDED.income,
            expense=EXCLUDED.expense,
            remaining=EXCLUDED.remaining,
            sold_items=EXCLUDED.sold_items,
            notes=EXCLUDED.notes
    """, {"u": user_id, "b": branch_id, "d": bdate, "i": income, "e": expense, "r": remaining,
          "s": sold_text, "n": remain_text})

    pretty = bdate.strftime("%d.%m.%Y")
    txt = (f"🧾 <b>Bugungi hisobot ({pretty})</b>\n\n"
           f"💰 Daromad: <b>{fmt_sum(income)}</b>\n💸 Rashod: <b>{fmt_sum(expense)}</b>\n"
           f"💵 Qolgan: <b>{fmt_sum(remaining)}</b>\n\n"
           f"🛒 Sotilganlar:\n{sold_text}\n\n📦 Qolgan:\n{remain_text}")

    await message.answer(txt, parse_mode="HTML")

    # --- Superadminlarga yuborish + Excel ---
    branch = database.fetchone("SELECT name FROM branches WHERE id=:id", {"id": branch_id})
    bname = branch["name"] if branch else "-"

    report_text = (f"📅 {pretty}\n🏢 Filial: {bname}\n👤 {message.from_user.full_name}\n\n"
                   f"💰 {fmt_sum(income)} | 💸 {fmt_sum(expense)} | 💵 {fmt_sum(remaining)}\n\n"
                   f"🛒 Sotilganlar:\n{sold_text}\n\n📦 Qolgan:\n{remain_text}")

    wb = Workbook()
    ws = wb.active
    ws.title = "Hisobot"
    ws.append(["Mahsulot", "Sotilgan", "Qolgan"])
    for s in sold:
        ws.append([s["name"], s["amount"], s["remaining"]])
    file = f"/tmp/hisobot_{bname}_{bdate}.xlsx".replace(" ", "_")
    wb.save(file)

    for admin in SUPERADMINS:
        try:
            await message.bot.send_message(admin, report_text)
            await message.bot.send_document(admin, FSInputFile(file), caption="📊 Excel")
        except Exception:
            pass

    if os.path.exists(file):
        os.remove(file)
    await state.clear()


# ===============================
# 📋 Ombor holati
# ===============================
@router.message(F.text == "📋 Ombor holati")
async def show_warehouse(message: Message):
    user = database.fetchone("SELECT branch_id FROM users WHERE telegram_id=:tid", {"tid": message.from_user.id})
    if not user:
        await message.answer("⚠️ Sizning filial aniqlanmadi.")
        return
    products = database.list_products_by_branch(user["branch_id"])
    if not products:
        await message.answer("📦 Omborda mahsulot yo‘q.")
        return

    txt = "📋 <b>Ombor holati:</b>\n\n"
    for p in products:
        q = float(p["quantity"])
        txt += f"• {p['product_name']} — {int(q) if q.is_integer() else q} {p['unit']}\n"
    await message.answer(txt, parse_mode="HTML")


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
