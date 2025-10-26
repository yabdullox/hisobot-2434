from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu, confirm_end_work_menu
from database import db
from config import SUPERADMIN_ID
import datetime
import aiosqlite

router = Router()
worker_state = {}
worker_data = {}


# === 🧾 HISOBOT YUBORISH (AVTOMAT) ===
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(message: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (message.from_user.id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

    worker_data[message.from_user.id] = {"worker": worker}
    worker_state[message.from_user.id] = "waiting_for_main_report"

    await message.answer(
        "📤 Iltimos, bugungi ish haqida qisqacha yozing.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text)
async def report_steps(message: types.Message):
    user_id = message.from_user.id
    state = worker_state.get(user_id)

    # 1️⃣ Asosiy matn
    if state == "waiting_for_main_report":
        worker_data[user_id]["main"] = message.text
        worker_state[user_id] = "waiting_for_sales_sum"
        return await message.answer("💵 Bugungi umumiy savdo summasini kiriting (so‘mda):")

    # 2️⃣ Savdo summasi
    elif state == "waiting_for_sales_sum":
        try:
            worker_data[user_id]["sales"] = int(message.text.replace(" ", ""))
        except ValueError:
            return await message.answer("❌ Faqat raqam kiriting. Masalan: 850000")
        worker_state[user_id] = "waiting_for_products"
        return await message.answer("📦 Sotilgan mahsulotlarni kiriting (vergul bilan ajrating):\nMasalan: Johori, Kiyim, Krossovka")

    # 3️⃣ Mahsulotlar
    elif state == "waiting_for_products":
        products = [p.strip() for p in message.text.split(",") if p.strip()]
        worker_data[user_id]["products"] = products
        worker_data[user_id]["quantities"] = {}
        worker_state[user_id] = f"waiting_for_qty_{products[0]}"
        return await message.answer(f"🧮 '{products[0]}' dan qancha sotdingiz? (Masalan: 18kg yoki 5 dona)")

    # 4️⃣ Har bir mahsulot miqdorini ketma-ket so‘rash
    elif state and state.startswith("waiting_for_qty_"):
        product = state.replace("waiting_for_qty_", "")
        worker_data[user_id]["quantities"][product] = message.text

        products = worker_data[user_id]["products"]
        index = products.index(product)

        if index + 1 < len(products):
            next_p = products[index + 1]
            worker_state[user_id] = f"waiting_for_qty_{next_p}"
            return await message.answer(f"📦 '{next_p}' dan qancha sotdingiz?")
        else:
            worker_state[user_id] = "ready_to_submit"
            return await message.answer("✅ Hisobot tayyor! Yuborish uchun '✅ Tasdiqlash' deb yozing.")

    # 5️⃣ Hisobotni yakunlash
    elif state == "ready_to_submit" and message.text.lower() in ["✅ tasdiqlash", "tasdiqlash", "ok", "ha"]:
        worker = worker_data[user_id]["worker"]

        # Hisobot matnini shakllantirish
        text = (
            f"📊 <b>Yangi hisobot</b>\n"
            f"👷 Ishchi: {worker[2]}\n🆔 {user_id}\n📍 Filial ID: {worker[1]}\n"
            f"🧾 {worker_data[user_id]['main']}\n"
            f"💵 Savdo summasi: {worker_data[user_id]['sales']:,} so‘m\n\n"
            f"📦 Sotilgan mahsulotlar:\n"
        )
        for p, q in worker_data[user_id]["quantities"].items():
            text += f"  • {p}: {q}\n"

        text += f"\n🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Bazaga saqlash
        async with aiosqlite.connect(db.DB_PATH) as conn:
            await conn.execute("""
                INSERT INTO reports (worker_id, filial_id, text, created_at)
                VALUES (?, ?, ?, ?)
            """, (worker[0], worker[1], text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            await conn.commit()

        try:
            await message.bot.send_message(SUPERADMIN_ID, text, parse_mode="HTML")
        except Exception as e:
            print(f"⚠️ Hisobot yuborishda xato: {e}")

        worker_state[user_id] = None
        worker_data[user_id] = {}
        return await message.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())

    elif state:
        await message.answer("❌ Noto‘g‘ri buyruq. Hisobot bosqichma-bosqich to‘ldirilyapti.")


# === 📦 MAHSULOTLARIM ===
@router.message(F.text == "📦 Mahsulotlarim")
async def my_products(message: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (message.from_user.id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        async with conn.execute("SELECT name FROM products WHERE worker_id=?", (worker[0],)) as cur:
            rows = await cur.fetchall()

    if not rows:
        text = "📦 Sizda hali mahsulot yo‘q.\n➕ Yangi mahsulot qo‘shish uchun nomini yuboring."
    else:
        text = "📦 Sizning mahsulotlaringiz:\n" + "\n".join([f"• {r[0]}" for r in rows]) + "\n\n➕ Qo‘shish yoki ❌ O‘chirish uchun nomini yuboring."

    worker_state[message.from_user.id] = "waiting_for_product_action"
    await message.answer(text, reply_markup=ReplyKeyboardRemove())


@router.message(F.text)
async def handle_product_action(message: types.Message):
    user_id = message.from_user.id
    state = worker_state.get(user_id)

    if state == "waiting_for_product_action":
        prod_name = message.text.strip()
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (user_id,)) as cur:
                worker = await cur.fetchone()
            async with conn.execute("SELECT id FROM products WHERE worker_id=? AND name=?", (worker[0], prod_name)) as cur:
                exists = await cur.fetchone()

            if exists:
                await conn.execute("DELETE FROM products WHERE id=?", (exists[0],))
                await conn.commit()
                await message.answer(f"❌ '{prod_name}' o‘chirildi.", reply_markup=worker_menu())
            else:
                await conn.execute("INSERT INTO products (worker_id, name) VALUES (?, ?)", (worker[0], prod_name))
                await conn.commit()
                await message.answer(f"✅ '{prod_name}' qo‘shildi.", reply_markup=worker_menu())

        worker_state[user_id] = None


# === ⏰ ISHNI BOSHLADIM ===
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        now = datetime.datetime.now()
        start_hour = 9
        grace_minutes = 10
        total_minutes = now.hour * 60 + now.minute
        start_minutes = start_hour * 60
        late_minutes = total_minutes - (start_minutes + grace_minutes)

        worker_id, filial_id, name = worker

        if late_minutes > 0:
            fine = int((late_minutes / 60) * 10000)
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker_id, filial_id, f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
            await msg.answer(f"⚠️ Siz kech keldingiz ({late_minutes} daqiqa). Jarima: {fine:,} so‘m.")
        elif total_minutes < start_minutes:
            early_minutes = start_minutes - total_minutes
            bonus = int((early_minutes / 60) * 10000)
            await conn.execute("""
                INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker_id, filial_id, f"Erta kelgan ({early_minutes} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
            await msg.answer(f"🎉 Siz ertaroq keldingiz! Bonus: +{bonus:,} so‘m.")
        else:
            await msg.answer("✅ Siz ishni o‘z vaqtida boshladingiz!")

    await msg.answer("↩️ Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✅ Ishni tugatganingiz qayd etildi.\n📩 Endi yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_final_report"


@router.message(F.text)
async def receive_final_report(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_final_report":
        return

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (worker[0], worker[1], f"Yakuniy hisobot: {msg.text}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    await msg.answer("✅ Yakuniy hisobot yuborildi! Rahmat 👏", reply_markup=worker_menu())


# === 📷 TOZALASH RASMI ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    await msg.answer("📸 Tozalash jarayoni rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_clean_photo"


@router.message(F.photo)
async def receive_photo(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_clean_photo":
        return

    file_id = msg.photo[-1].file_id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()

    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=f"🧹 Tozalash rasmi\n👷 {worker[0]}\n🆔 {msg.from_user.id}")
    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# === 📅 BUGUNGI HISOBOTLARIM ===
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def show_today_reports(msg: types.Message):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT text, created_at FROM reports
            WHERE worker_id = (SELECT id FROM workers WHERE tg_id = ?)
            AND DATE(created_at) = DATE(?)
            ORDER BY id DESC
        """, (msg.from_user.id, today)) as cur:
            reports = await cur.fetchall()

    if not reports:
        return await msg.answer("📭 Bugun hech qanday hisobot kelmagan.", reply_markup=worker_menu())

    text = "🗓 <b>Bugungi hisobotlaringiz:</b>\n\n" + "\n".join(
        [f"🕒 {r[1]} — {r[0]}" for r in reports])
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())
