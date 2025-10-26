from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from database import db
from config import SUPERADMIN_ID
import datetime
import aiosqlite

router = Router()

worker_state = {}
worker_data = {}

# === 🧾 HISOBOT YUBORISH BOSHLASH ===
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(message: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (message.from_user.id,)) as cur:
            worker = await cur.fetchone()
    if not worker:
        return await message.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

    worker_data[message.from_user.id] = {"worker": worker}
    worker_state[message.from_user.id] = "waiting_for_main_report"

    await message.answer(
        "📤 Iltimos, bugungi ish haqida qisqacha yozing.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
        reply_markup=ReplyKeyboardRemove()
    )


# === 📦 MAHSULOTLARIM ===
@router.message(F.text == "📦 Mahsulotlarim")
async def my_products(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (user_id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await message.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
        async with conn.execute("SELECT name FROM products WHERE worker_id=?", (worker[0],)) as cur:
            rows = await cur.fetchall()

    if not rows:
        text = "📦 Sizda mahsulot yo‘q.\nNomini yuborib yangi mahsulot qo‘shing."
    else:
        text = "📦 Sizning mahsulotlaringiz:\n" + "\n".join([f"• {r[0]}" for r in rows]) + "\n\n➕ Yangi qo‘shish yoki ❌ O‘chirish uchun nomini yuboring."

    worker_state[user_id] = "waiting_for_product_action"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())


# === ⏰ ISHNI BOSHLADIM ===
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        now = datetime.datetime.now()
        start_hour, grace_minutes = 9, 10
        total_minutes = now.hour * 60 + now.minute
        start_minutes = start_hour * 60
        late_minutes = total_minutes - (start_minutes + grace_minutes)

        if late_minutes > 0:
            fine = int((late_minutes / 60) * 10000)
            await conn.execute("INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                               (worker[0], worker[1], f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
            await msg.answer(f"⚠️ Kech keldingiz ({late_minutes} daqiqa). Jarima: {fine:,} so‘m.")
        elif total_minutes < start_minutes:
            early = start_minutes - total_minutes
            bonus = int((early / 60) * 10000)
            await conn.execute("INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                               (worker[0], worker[1], f"Erta kelgan ({early} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
            await msg.answer(f"🎉 Erta keldingiz! Bonus: +{bonus:,} so‘m.")
        else:
            await msg.answer("✅ Siz o‘z vaqtida ishni boshladingiz!")

        await conn.commit()
    await msg.answer("↩️ Asosiy menyu:", reply_markup=worker_menu())


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✅ Ish tugatildi.\n✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_final_report"


# === 📷 TOZALASH RASMI ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_for_clean_photo"
    await msg.answer("📸 Tozalash jarayoni rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


# === 📸 MUAMMO YUBORISH ===
@router.message(F.text == "📸 Muammo yuborish")
async def ask_problem_photo(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_for_problem_photo"
    await msg.answer("📸 Muammo rasmini yuboring va captionga izoh yozing:", reply_markup=ReplyKeyboardRemove())


# === 💰 BONUS/JARIMALARIM ===
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finance(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        async with conn.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=?", (worker[0],)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=?", (worker[0],)) as cur:
            fines = await cur.fetchall()

    text = f"💰 <b>{worker[1]} uchun bonus va jarimalar:</b>\n\n"
    if bonuses:
        text += "🎉 <b>Bonuslar:</b>\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]} ({b[2]})" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ <b>Jarimalar:</b>\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]} ({f[2]})" for f in fines])
    if not bonuses and not fines:
        text += "📭 Hozircha bonus yoki jarima yo‘q."
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# === 📅 BUGUNGI HISOBOTLARIM ===
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def show_today_reports(msg: types.Message):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT text, created_at FROM reports
            WHERE worker_id = (SELECT id FROM workers WHERE tg_id = ?)
            AND DATE(created_at) = DATE(?)
        """, (msg.from_user.id, today)) as cur:
            reports = await cur.fetchall()

    if not reports:
        return await msg.answer("📭 Bugun hisobot kelmagan.", reply_markup=worker_menu())
    text = "🗓 <b>Bugungi hisobotlaringiz:</b>\n" + "\n".join([f"🕒 {r[1]} — {r[0]}" for r in reports])
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# === RASMLARNI QABUL QILISH ===
@router.message(F.photo)
async def handle_photo(msg: types.Message):
    state = worker_state.get(msg.from_user.id)
    file_id = msg.photo[-1].file_id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

    if state == "waiting_for_clean_photo":
        caption = f"🧹 Tozalash rasmi\n👷 {worker[0]}\n🆔 {msg.from_user.id}"
    elif state == "waiting_for_problem_photo":
        caption = f"🚨 Muammo rasmi\n👷 {worker[0]}\n🆔 {msg.from_user.id}\n📝 {msg.caption or ''}"
    else:
        return

    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=caption)
    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# === UMUMIY MATN — HISOBOT / MAHSULOT HOLATLARI ===
@router.message(F.text)
async def text_handler(message: types.Message):
    user_id = message.from_user.id
    state = worker_state.get(user_id)

    # Yakuniy hisobot
    if state == "waiting_for_final_report":
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
                worker = await cur.fetchone()
            await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                               (worker[0], worker[1], f"Yakuniy hisobot: {message.text}",
                                datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
        await message.answer("✅ Yakuniy hisobot yuborildi!", reply_markup=worker_menu())
        worker_state[user_id] = None
        return

    # Mahsulotlar
    if state == "waiting_for_product_action":
        prod = message.text.strip()
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (user_id,)) as cur:
                worker = await cur.fetchone()
            async with conn.execute("SELECT id FROM products WHERE worker_id=? AND name=?", (worker[0], prod)) as cur:
                exists = await cur.fetchone()
            if exists:
                await conn.execute("DELETE FROM products WHERE id=?", (exists[0],))
                await message.answer(f"❌ '{prod}' o‘chirildi.", reply_markup=worker_menu())
            else:
                await conn.execute("INSERT INTO products (worker_id, name) VALUES (?, ?)", (worker[0], prod))
                await message.answer(f"✅ '{prod}' qo‘shildi.", reply_markup=worker_menu())
            await conn.commit()
        worker_state[user_id] = None
