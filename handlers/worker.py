# from aiogram import Router, F, types
# from aiogram.types import ReplyKeyboardRemove
# from keyboards.worker_kb import worker_menu
# from database import db
# from config import SUPERADMIN_ID
# import datetime
# import aiosqlite

# router = Router()

# worker_state = {}
# worker_data = {}

# # === 🧾 HISOBOT YUBORISH BOSHLASH ===
# @router.message(F.text == "🧾 Hisobot yuborish")
# async def start_report(message: types.Message):
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (message.from_user.id,)) as cur:
#             worker = await cur.fetchone()
#     if not worker:
#         return await message.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

#     worker_data[message.from_user.id] = {"worker": worker}
#     worker_state[message.from_user.id] = "waiting_for_main_report"

#     await message.answer(
#         "📤 Iltimos, bugungi ish haqida qisqacha yozing.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
#         reply_markup=ReplyKeyboardRemove()
#     )


# # === 📦 MAHSULOTLARIM ===
# @router.message(F.text == "📦 Mahsulotlarim")
# async def my_products(message: types.Message):
#     user_id = message.from_user.id
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (user_id,)) as cur:
#             worker = await cur.fetchone()
#         if not worker:
#             return await message.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
#         async with conn.execute("SELECT name FROM products WHERE worker_id=?", (worker[0],)) as cur:
#             rows = await cur.fetchall()

#     if not rows:
#         text = "📦 Sizda mahsulot yo‘q.\nNomini yuborib yangi mahsulot qo‘shing."
#     else:
#         text = "📦 Sizning mahsulotlaringiz:\n" + "\n".join([f"• {r[0]}" for r in rows]) + "\n\n➕ Yangi qo‘shish yoki ❌ O‘chirish uchun nomini yuboring."

#     worker_state[user_id] = "waiting_for_product_action"
#     await message.answer(text, reply_markup=ReplyKeyboardRemove())


# # === ⏰ ISHNI BOSHLADIM ===
# @router.message(F.text == "⏰ Ishni boshladim")
# async def start_work(msg: types.Message):
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
#             worker = await cur.fetchone()
#         if not worker:
#             return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

#         now = datetime.datetime.now()
#         start_hour, grace_minutes = 9, 10
#         total_minutes = now.hour * 60 + now.minute
#         start_minutes = start_hour * 60
#         late_minutes = total_minutes - (start_minutes + grace_minutes)

#         if late_minutes > 0:
#             fine = int((late_minutes / 60) * 10000)
#             await conn.execute("INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
#                                (worker[0], worker[1], f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
#             await msg.answer(f"⚠️ Kech keldingiz ({late_minutes} daqiqa). Jarima: {fine:,} so‘m.")
#         elif total_minutes < start_minutes:
#             early = start_minutes - total_minutes
#             bonus = int((early / 60) * 10000)
#             await conn.execute("INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
#                                (worker[0], worker[1], f"Erta kelgan ({early} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
#             await msg.answer(f"🎉 Erta keldingiz! Bonus: +{bonus:,} so‘m.")
#         else:
#             await msg.answer("✅ Siz o‘z vaqtida ishni boshladingiz!")

#         await conn.commit()
#     await msg.answer("↩️ Asosiy menyu:", reply_markup=worker_menu())


# # === 🏁 ISHNI TUGATDIM ===
# @router.message(F.text == "🏁 Ishni tugatdim")
# async def end_work(msg: types.Message):
#     await msg.answer("✅ Ish tugatildi.\n✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())
#     worker_state[msg.from_user.id] = "waiting_for_final_report"


# # === 📷 TOZALASH RASMI ===
# @router.message(F.text == "📷 Tozalash rasmi yuborish")
# async def ask_clean_photo(msg: types.Message):
#     worker_state[msg.from_user.id] = "waiting_for_clean_photo"
#     await msg.answer("📸 Tozalash jarayoni rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


# # === 📸 MUAMMO YUBORISH ===
# @router.message(F.text == "📸 Muammo yuborish")
# async def ask_problem_photo(msg: types.Message):
#     worker_state[msg.from_user.id] = "waiting_for_problem_photo"
#     await msg.answer("📸 Muammo rasmini yuboring va captionga izoh yozing:", reply_markup=ReplyKeyboardRemove())


# # === 💰 BONUS/JARIMALARIM ===
# @router.message(F.text == "💰 Bonus/Jarimalarim")
# async def show_finance(msg: types.Message):
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
#             worker = await cur.fetchone()
#         async with conn.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=?", (worker[0],)) as cur:
#             bonuses = await cur.fetchall()
#         async with conn.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=?", (worker[0],)) as cur:
#             fines = await cur.fetchall()

#     text = f"💰 <b>{worker[1]} uchun bonus va jarimalar:</b>\n\n"
#     if bonuses:
#         text += "🎉 <b>Bonuslar:</b>\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]} ({b[2]})" for b in bonuses]) + "\n\n"
#     if fines:
#         text += "⚠️ <b>Jarimalar:</b>\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]} ({f[2]})" for f in fines])
#     if not bonuses and not fines:
#         text += "📭 Hozircha bonus yoki jarima yo‘q."
#     await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# # === 📅 BUGUNGI HISOBOTLARIM ===
# @router.message(F.text == "📅 Bugungi hisobotlarim")
# async def show_today_reports(msg: types.Message):
#     today = datetime.datetime.now().strftime("%Y-%m-%d")
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("""
#             SELECT text, created_at FROM reports
#             WHERE worker_id = (SELECT id FROM workers WHERE tg_id = ?)
#             AND DATE(created_at) = DATE(?)
#         """, (msg.from_user.id, today)) as cur:
#             reports = await cur.fetchall()

#     if not reports:
#         return await msg.answer("📭 Bugun hisobot kelmagan.", reply_markup=worker_menu())
#     text = "🗓 <b>Bugungi hisobotlaringiz:</b>\n" + "\n".join([f"🕒 {r[1]} — {r[0]}" for r in reports])
#     await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# # === RASMLARNI QABUL QILISH ===
# @router.message(F.photo)
# async def handle_photo(msg: types.Message):
#     state = worker_state.get(msg.from_user.id)
#     file_id = msg.photo[-1].file_id
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
#             worker = await cur.fetchone()

#     if state == "waiting_for_clean_photo":
#         caption = f"🧹 Tozalash rasmi\n👷 {worker[0]}\n🆔 {msg.from_user.id}"
#     elif state == "waiting_for_problem_photo":
#         caption = f"🚨 Muammo rasmi\n👷 {worker[0]}\n🆔 {msg.from_user.id}\n📝 {msg.caption or ''}"
#     else:
#         return

#     await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=caption)
#     worker_state[msg.from_user.id] = None
#     await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# # === UMUMIY MATN — HISOBOT / MAHSULOT HOLATLARI ===
# @router.message(F.text)
# async def text_handler(message: types.Message):
#     user_id = message.from_user.id
#     state = worker_state.get(user_id)

#     # Yakuniy hisobot
#     if state == "waiting_for_final_report":
#         async with aiosqlite.connect(db.DB_PATH) as conn:
#             async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
#                 worker = await cur.fetchone()
#             await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
#                                (worker[0], worker[1], f"Yakuniy hisobot: {message.text}",
#                                 datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
#             await conn.commit()
#         await message.answer("✅ Yakuniy hisobot yuborildi!", reply_markup=worker_menu())
#         worker_state[user_id] = None
#         return

#     # Mahsulotlar
#     if state == "waiting_for_product_action":
#         prod = message.text.strip()
#         async with aiosqlite.connect(db.DB_PATH) as conn:
#             async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (user_id,)) as cur:
#                 worker = await cur.fetchone()
#             async with conn.execute("SELECT id FROM products WHERE worker_id=? AND name=?", (worker[0], prod)) as cur:
#                 exists = await cur.fetchone()
#             if exists:
#                 await conn.execute("DELETE FROM products WHERE id=?", (exists[0],))
#                 await message.answer(f"❌ '{prod}' o‘chirildi.", reply_markup=worker_menu())
#             else:
#                 await conn.execute("INSERT INTO products (worker_id, name) VALUES (?, ?)", (worker[0], prod))
#                 await message.answer(f"✅ '{prod}' qo‘shildi.", reply_markup=worker_menu())
#             await conn.commit()
#         worker_state[user_id] = None
from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu, product_menu, confirm_end_work_menu
from config import SUPERADMIN_ID
from database import db
import datetime
import aiosqlite

router = Router()
worker_state = {}
worker_data = {}

# === 🧾 HISOBOT YUBORISH (3 bosqich) ===
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(message: types.Message):
    await message.answer(
        "📋 Iltimos, bugungi ish hisobotini yozing.\nMasalan: 'Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.'",
        reply_markup=ReplyKeyboardRemove()
    )
    worker_state[message.from_user.id] = "waiting_for_main_report"
    worker_data[message.from_user.id] = {}


@router.message(F.text)
async def handle_report_steps(message: types.Message):
    user_id = message.from_user.id
    state = worker_state.get(user_id)

    # 1️⃣ Asosiy hisobot matni
    if state == "waiting_for_main_report":
        worker_data[user_id]["main_report"] = message.text
        worker_state[user_id] = "waiting_for_sales_sum"
        return await message.answer("💰 Bugungi umumiy savdo summasini kiriting (so‘mda):")

    # 2️⃣ Savdo summasi
    elif state == "waiting_for_sales_sum":
        try:
            amount = int(message.text.replace(" ", ""))
            worker_data[user_id]["sales_sum"] = amount
        except ValueError:
            return await message.answer("❌ Faqat raqam kiriting. Masalan: 850000")
        worker_state[user_id] = "ready_to_submit"
        return await message.answer("✅ Hisobot tayyor. Yuborish uchun '✅ Tasdiqlash' deb yozing.")

    # 3️⃣ Tasdiqlash
    elif state == "ready_to_submit" and message.text.lower() in ["✅ tasdiqlash", "tasdiqlash", "ok", "ha"]:
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
                worker = await cur.fetchone()
            if not worker:
                return await message.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

            full_report = (
                f"📊 <b>Yangi hisobot</b>\n"
                f"👷 Ishchi: {worker[2]}\n📍 Filial ID: {worker[1]}\n"
                f"🧾 Hisobot: {worker_data[user_id]['main_report']}\n"
                f"💵 Savdo summasi: {worker_data[user_id]['sales_sum']:,} so‘m\n"
                f"🕒 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            await conn.execute(
                "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                (worker[0], worker[1], full_report, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            await conn.commit()

        await message.bot.send_message(SUPERADMIN_ID, full_report, parse_mode="HTML")
        worker_state[user_id] = None
        worker_data[user_id] = {}
        return await message.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())


# === ⏰ ISHNI BOSHLADIM ===
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    user_id = msg.from_user.id
    now = datetime.datetime.now()
    hour, minute = now.hour, now.minute
    start_hour = 9
    grace_minutes = 10
    total_minutes = hour * 60 + minute
    start_minutes = start_hour * 60

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        diff = total_minutes - (start_minutes + grace_minutes)

        if diff > 0:
            fine = int((diff / 60) * 10000)
            await conn.execute("""
                INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker[0], worker[1], f"Kechikish ({diff} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
            await msg.answer(f"⚠️ Kech keldingiz ({diff} daqiqa). Jarima: {fine:,} so‘m.")
        elif diff < -10:
            bonus = int((abs(diff) / 60) * 10000)
            await conn.execute("""
                INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (worker[0], worker[1], f"Erta kelgan ({abs(diff)} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
            await msg.answer(f"🎉 Erta keldingiz! Bonus: +{bonus:,} so‘m.")
        else:
            await msg.answer("✅ Siz o‘z vaqtida ishni boshladingiz!")

        await conn.commit()

    await msg.answer("🕒 Ish boshlanishi qayd etildi.", reply_markup=worker_menu())


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("📩 Yakuniy hisobotni yuboring:", reply_markup=confirm_end_work_menu())
    worker_state[msg.from_user.id] = "waiting_for_final"


@router.message(F.text == "📤 Yakuniy hisobotni yuborish")
async def final_report(msg: types.Message):
    await msg.answer("✏️ Yakuniy hisobot matnini kiriting:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_final_text"


@router.message(F.text)
async def receive_final_report(msg: types.Message):
    user_id = msg.from_user.id
    if worker_state.get(user_id) != "waiting_for_final_text":
        return

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
            worker = await cur.fetchone()
        report_text = f"🏁 <b>{worker[2]}</b> ishni tugatdi.\n🧾 Yakuniy hisobot:\n{msg.text}"
        await conn.execute(
            "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
            (worker[0], worker[1], report_text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        await conn.commit()

    await msg.bot.send_message(SUPERADMIN_ID, report_text, parse_mode="HTML")
    worker_state[user_id] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi!", reply_markup=worker_menu())


# === 📷 TOZALASH RASMI YUBORISH ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def ask_clean_photo(msg: types.Message):
    await msg.answer("📸 Tozalash joyining rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_clean_photo"


@router.message(F.photo)
async def receive_clean_photo(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_clean_photo":
        return
    photo_id = msg.photo[-1].file_id
    await msg.bot.send_photo(SUPERADMIN_ID, photo=photo_id, caption=f"🧹 {msg.from_user.full_name} tozalash rasmi yubordi.")
    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())


# === 📸 MUAMMO YUBORISH ===
@router.message(F.text == "📸 Muammo yuborish")
async def ask_problem_photo(msg: types.Message):
    await msg.answer("⚠️ Muammo rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_problem_photo"


@router.message(F.photo)
async def receive_problem_photo(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_problem_photo":
        return
    worker_state[msg.from_user.id] = "waiting_for_problem_note"
    worker_state[f"{msg.from_user.id}_photo"] = msg.photo[-1].file_id
    await msg.answer("📝 Muammo haqida qisqacha yozing:")


@router.message(F.text)
async def receive_problem_note(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_problem_note":
        return
    photo_id = worker_state.get(f"{msg.from_user.id}_photo")
    await msg.bot.send_photo(SUPERADMIN_ID, photo=photo_id, caption=f"🚨 Muammo: {msg.text}")
    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Muammo yuborildi!", reply_markup=worker_menu())


# === 📦 MAHSULOTLARIM (KO‘RISH / QO‘SHISH / O‘CHIRISH) ===
@router.message(F.text == "📦 Mahsulotlarim")
async def show_products(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        async with conn.execute("SELECT name FROM products WHERE worker_id=?", (worker[0],)) as cur:
            products = await cur.fetchall()
    if not products:
        return await msg.answer("📦 Sizda hali mahsulot yo‘q.", reply_markup=product_menu())
    text = "📋 Sizdagi mahsulotlar:\n" + "\n".join([f"• {p[0]}" for p in products])
    await msg.answer(text, reply_markup=product_menu())


@router.message(F.text == "➕ Mahsulot qo‘shish")
async def add_product_prompt(msg: types.Message):
    await msg.answer("🆕 Mahsulot nomini kiriting:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_product_name"


@router.message(F.text)
async def add_product_name(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_product_name":
        return
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        await conn.execute("INSERT INTO products (worker_id, name) VALUES (?, ?)", (worker[0], msg.text))
        await conn.commit()
    worker_state[msg.from_user.id] = None
    await msg.answer(f"✅ '{msg.text}' qo‘shildi!", reply_markup=product_menu())


@router.message(F.text == "❌ Mahsulotni o‘chirish")
async def delete_product_prompt(msg: types.Message):
    await msg.answer("🗑 O‘chirmoqchi bo‘lgan mahsulot nomini kiriting:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_delete_product"


@router.message(F.text)
async def delete_product_name(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_delete_product":
        return
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        await conn.execute("DELETE FROM products WHERE worker_id=? AND name=?", (worker[0], msg.text))
        await conn.commit()
    worker_state[msg.from_user.id] = None
    await msg.answer(f"🗑 '{msg.text}' o‘chirildi!", reply_markup=product_menu())


# === 💰 BONUS/JARIMALARIM ===
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finance(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        async with conn.execute("SELECT reason, amount FROM bonuses WHERE worker_id=?", (worker[0],)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount FROM fines WHERE worker_id=?", (worker[0],)) as cur:
            fines = await cur.fetchall()

    text = f"💰 <b>{worker[1]} uchun Bonus va Jarimalar:</b>\n\n"
    if bonuses:
        text += "🎉 Bonuslar:\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]}" for b in bonuses]) + "\n"
    if fines:
        text += "\n⚠️ Jarimalar:\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]}" for f in fines])
    if not bonuses and not fines:
        text += "📭 Hozircha bonus yoki jarima yo‘q."
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# === ↩️ MENYUGA QAYTISH ===
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    await msg.answer("👷 Ishchi menyusiga qaytdingiz.", reply_markup=worker_menu())
