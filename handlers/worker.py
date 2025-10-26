# from aiogram import Router, types, F, Bot
# from aiogram.types import ReplyKeyboardRemove
# from keyboards.worker_kb import worker_menu
# from database import db
# import datetime
# import os

# router = Router()
# SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID") or 0)
# worker_state = {}


# # --- 🧾 Hisobot yuborish ---
# @router.message(F.text == "🧾 Hisobot yuborish")
# async def start_report(msg: types.Message):
#     await msg.answer("✏️ Hisobotingizni yozing (matn shaklida):", reply_markup=ReplyKeyboardRemove())
#     worker_state[msg.from_user.id] = "waiting_for_report"


# @router.message(F.text, ~F.text.in_(["🧾 Hisobot yuborish", "📷 Muammo yuborish", "⏰ Ishni boshladim", "💸 Bonus/Jarimalarim", "↩️ Menyuga qaytish"]))
# async def save_report(msg: types.Message):
#     if worker_state.get(msg.from_user.id) != "waiting_for_report":
#         return

#     conn = db.get_conn()
#     cur = conn.cursor()
#     worker = cur.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()

#     if not worker:
#         return await msg.answer("❌ Siz ishchilar ro‘yxatida yo‘qsiz.")

#     cur.execute(
#         "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
#         (worker[0], worker[1], msg.text, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
#     )
#     conn.commit()

#     worker_state[msg.from_user.id] = None
#     await msg.answer("✅ Hisobotingiz muvaffaqiyatli yuborildi.", reply_markup=worker_menu())


# # --- ⏰ Ishni boshladim ---
# @router.message(F.text == "⏰ Ishni boshladim")
# async def start_work(msg: types.Message):
#     conn = db.get_conn()
#     cur = conn.cursor()
#     worker = cur.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()

#     if not worker:
#         return await msg.answer("❌ Siz ishchilar ro‘yxatida yo‘qsiz.")

#     now = datetime.datetime.now()
#     hour, minute = now.hour, now.minute

#     start_hour = 9
#     grace_minutes = 10
#     total_minutes = hour * 60 + minute
#     start_minutes = start_hour * 60
#     late_minutes = total_minutes - (start_minutes + grace_minutes)

#     if late_minutes > 0:
#         fine = int((late_minutes / 60) * 10000)
#         cur.execute(
#             "INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
#             (worker[0], worker[1], f"Kechikish ({late_minutes} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M"))
#         )
#         conn.commit()
#         await msg.answer(f"⚠️ Siz kech keldingiz! Jarima: {fine:,} so‘m.")
#     elif total_minutes < start_minutes:
#         early_minutes = start_minutes - total_minutes
#         bonus = int((early_minutes / 60) * 10000)
#         cur.execute(
#             "INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
#             (worker[0], worker[1], f"Erta kelgan ({early_minutes} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M"))
#         )
#         conn.commit()
#         await msg.answer(f"🎉 Siz ertaroq keldingiz! Bonus: +{bonus:,} so‘m.")
#     else:
#         await msg.answer("✅ Siz ishni o‘z vaqtida boshladingiz!")

#     cur.execute(
#         "INSERT INTO work_start_log (worker_id, filial_id, start_time) VALUES (?, ?, ?)",
#         (worker[0], worker[1], now.strftime("%Y-%m-%d %H:%M"))
#     )
#     conn.commit()

#     await msg.answer("⏰ Ish boshlanishi muvaffaqiyatli qayd etildi.", reply_markup=worker_menu())


# # --- 📷 Muammo yuborish ---
# @router.message(F.text == "📷 Muammo yuborish")
# async def ask_problem_photo(msg: types.Message):
#     await msg.answer("📸 Iltimos, muammo rasmini yuboring:", reply_markup=ReplyKeyboardRemove())
#     worker_state[msg.from_user.id] = "waiting_for_problem_photo"


# @router.message(F.photo)
# async def receive_problem_photo(msg: types.Message):
#     if worker_state.get(msg.from_user.id) != "waiting_for_problem_photo":
#         return

#     worker_state[msg.from_user.id] = "waiting_for_problem_note"
#     worker_state[f"{msg.from_user.id}_photo"] = msg.photo[-1].file_id

#     await msg.answer("📝 Endi muammo haqida qisqacha izoh yozing:")


# @router.message(F.text)
# async def receive_problem_note(msg: types.Message):
#     if worker_state.get(msg.from_user.id) != "waiting_for_problem_note":
#         return

#     conn = db.get_conn()
#     cur = conn.cursor()
#     worker = cur.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()

#     if not worker:
#         return await msg.answer("❌ Siz tizimda yo‘qsiz.")

#     file_id = worker_state.get(f"{msg.from_user.id}_photo")
#     note = msg.text.strip()

#     cur.execute(
#         "INSERT INTO problems (worker_id, filial_id, file_id, note, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
#         (worker[0], worker[1], file_id, note, "Yangi", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
#     )
#     conn.commit()

#     worker_state[msg.from_user.id] = None
#     await msg.answer("✅ Muammo yuborildi. Rahmat!", reply_markup=worker_menu())


# # --- 💸 BONUS / JARIMALAR ---
# @router.message(F.text == "💸 Bonus/Jarimalarim")
# async def show_finance(msg: types.Message):
#     conn = db.get_conn()
#     cur = conn.cursor()

#     # Ishchini aniqlaymiz
#     worker = cur.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()
#     if not worker:
#         return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")

#     worker_id = worker[0]

#     # Jadval mavjudligini tekshiramiz
#     try:
#         fines = cur.execute(
#             "SELECT reason, amount, created_at FROM fines WHERE worker_id=? ORDER BY id DESC LIMIT 10",
#             (worker_id,)
#         ).fetchall()
#     except Exception:
#         fines = []

#     try:
#         bonuses = cur.execute(
#             "SELECT reason, amount, created_at FROM bonuses WHERE worker_id=? ORDER BY id DESC LIMIT 10",
#             (worker_id,)
#         ).fetchall()
#     except Exception:
#         bonuses = []

#     # Javob matni
#     text = f"💰 <b>{worker[1]} uchun Bonus va Jarimalar:</b>\n\n"

#     if bonuses:
#         text += "🎉 <b>Bonuslar:</b>\n"
#         for b in bonuses:
#             text += f"➕ {int(b[1]):,} so‘m — {b[0]} ({b[2]})\n"

#     if fines:
#         text += "\n⚠️ <b>Jarimalar:</b>\n"
#         for f in fines:
#             text += f"➖ {int(f[1]):,} so‘m — {f[0]} ({f[2]})\n"

#     if not fines and not bonuses:
#         text += "📭 Sizda hozircha bonus yoki jarima mavjud emas."

#     await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())

# # --- ↩️ Menyuga qaytish ---
# @router.message(F.text == "↩️ Menyuga qaytish")
# async def back_to_menu(msg: types.Message):
#     await msg.answer("👷 Ishchi menyusi:", reply_markup=worker_menu())


from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from database import db
from config import SUPERADMIN_ID
import datetime

router = Router()


# 🧾 HISOBOT YUBORISH (boshlanishi)
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report_prompt(message: types.Message):
    await message.answer(
        "📤 Iltimos, hisobot matnini yuboring.\n\nMasalan:\n<b>Bugun 5 ta mijoz, 3 ta tozalash, 1 muammo.</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


# 🧾 HISOBOTNI QABUL QILISH
@router.message(F.text & ~F.text.in_(["🧾 Hisobot yuborish", "⏰ Ishni boshladim", "🐝 Bonus/Jarimalarim", "🔙 Menyuga qaytish",
                                      "📷 Tozalash rasmi yuborish", "📷 Muammo rasmi yuborish"]))
async def receive_report(message: types.Message):
    report_text = message.text.strip()

    conn = db.get_conn()
    cur = conn.cursor()

    # Ishchini bazadan topamiz
    worker = cur.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (message.from_user.id,)).fetchone()

    if not worker:
        return await message.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")

    # Hisobotni bazaga yozamiz
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
        (worker[0], worker[1], report_text, now)
    )
    conn.commit()
    conn.close()

    # Superadminga yuboramiz
    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            f"📩 <b>Yangi hisobot</b>\n👷‍♂️ Ishchi: {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>\n\n🧾 {report_text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Superadminga hisobot yuborishda xato: {e}")

    await message.answer("✅ Hisobot yuborildi! Rahmat 👌", reply_markup=worker_menu())


# ⏰ ISHNI BOSHLADIM
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(message: types.Message):
    await message.answer("✅ Siz ishni boshladingiz 💪", reply_markup=worker_menu)
    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            f"🕒 Ishchi ishni boshladi:\n👷‍♂️ {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Ish boshlash haqida yuborishda xato: {e}")


# 📷 TOZALASH RASMI YUBORISH
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def send_clean_photo_instruction(message: types.Message):
    await message.answer("📸 Iltimos, tozalash jarayoni rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


# 📷 RASMLARNI QABUL QILISH (tozalash / muammo)
@router.message(F.photo)
async def receive_photo(message: types.Message):
    try:
        file_id = message.photo[-1].file_id
        if message.caption:
            caption = f"🚨 <b>Muammo rasmi:</b>\n👷‍♂️ {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>\n📝 {message.caption}"
        else:
            caption = f"🧹 <b>Tozalash rasmi:</b>\n👷‍♂️ {message.from_user.full_name}\n🆔 <code>{message.from_user.id}</code>"

        await message.bot.send_photo(SUPERADMIN_ID, photo=file_id, caption=caption, parse_mode="HTML")
        await message.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())
    except Exception as e:
        print(f"⚠️ Rasmni yuborishda xato: {e}")
        await message.answer("❌ Rasm yuborishda xatolik yuz berdi.", reply_markup=worker_menu())


# 💸 BONUS / JARIMALARIM
@router.message(F.text == "🐝 Bonus/Jarimalarim")
async def bonus_info(message: types.Message):
    await message.answer("💸 Sizda hozircha bonus yoki jarimalar mavjud emas.", reply_markup=worker_menu())


# 🔙 MENYUGA QAYTISH
@router.message(F.text == "🔙 Menyuga qaytish")
async def back_to_menu(message: types.Message):
    await message.answer("🔄 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())

