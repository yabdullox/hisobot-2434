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
from config import SUPERADMIN_ID
from database import db
import datetime

router = Router()

# Ishchi holati
worker_state = {}

# 🧾 HISOBOT yuborish
@router.message(F.text == "🧾 Hisobot yuborish")
async def ask_report(msg: types.Message):
    await msg.answer("✏️ Hisobotingizni kiriting:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_for_report"


@router.message(F.text & ~F.text.in_(["🧾 Hisobot yuborish", "⏰ Ishni boshladim", "🏁 Ishni tugatdim"]))
async def save_report(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "waiting_for_report":
        return

    text = msg.text.strip()
    conn = db.get_conn()
    cur = conn.cursor()

    worker = cur.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (msg.from_user.id,)).fetchone()
    if not worker:
        return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                (worker[0], worker[1], text, now))
    conn.commit()
    conn.close()

    worker_state[msg.from_user.id] = None

    # SuperAdmin’ga yuborish
    try:
        await msg.bot.send_message(
            SUPERADMIN_ID,
            f"📩 <b>Yangi hisobot:</b>\n👷 {msg.from_user.full_name}\n🕒 {now}\n🧾 {text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print("⚠️ Superadminga yuborilmadi:", e)

    await msg.answer("✅ Hisobotingiz qabul qilindi.", reply_markup=worker_menu())


# ⏰ ISHNI BOSHLADIM
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    user_id = msg.from_user.id
    now = datetime.datetime.now()
    hour, minute = now.hour, now.minute

    # 9:00 ni solishtirish
    start_hour = 9
    grace_minutes = 10  # 9:10 gacha kechikishsiz
    total_minutes = hour * 60 + minute
    base_minutes = start_hour * 60

    conn = db.get_conn()
    cur = conn.cursor()
    worker = cur.execute("SELECT id, filial_id FROM workers WHERE tg_id=?", (user_id,)).fetchone()
    if not worker:
        return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.")

    # Bonus yoki jarima hisoblash
    diff = total_minutes - base_minutes

    if diff > grace_minutes:
        # kechikish
        soat = diff / 60
        fine = int(soat * 10000)
        cur.execute("""
            INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (worker[0], worker[1], f"Kechikish ({diff} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))
        await msg.answer(f"⚠️ Siz {diff} daqiqa kechikdingiz.\nJarima: {fine:,} so‘m.")
    elif diff < 0:
        # ertaroq kelish
        early = abs(diff)
        soat = early / 60
        bonus = int(soat * 10000)
        cur.execute("""
            INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (worker[0], worker[1], f"Erta kelgan ({early} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
        await msg.answer(f"🎉 Siz {early} daqiqa ertaroq keldingiz!\nBonus: +{bonus:,} so‘m.")
    else:
        await msg.answer("✅ Siz ishni o‘z vaqtida boshladingiz!")

    conn.commit()
    conn.close()

    worker_state[user_id] = "working"
    await msg.answer("🕒 Ish boshlanishi qayd etildi.\n\nTugatgach “🏁 Ishni tugatdim” tugmasini bosing.")


# 🏁 ISHNI TUGATDIM
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    if worker_state.get(msg.from_user.id) != "working":
        return await msg.answer("❗ Siz hali ishni boshlamagan bo‘lishingiz mumkin.")

    worker_state[msg.from_user.id] = None
    await msg.answer("✅ Ish tugatildi!\n\nEndi 🧾 <b>Hisobot yuboring</b> tugmasini bosing.", parse_mode="HTML")

