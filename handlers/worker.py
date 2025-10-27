# from aiogram import Router, F, types
# from aiogram.types import ReplyKeyboardRemove
# from keyboards.worker_kb import worker_menu
# from config import SUPERADMIN_ID
# from database import db
# import datetime
# import aiosqlite

# router = Router()

# # --- oddiy holat saqlovchi o‘zgaruvchilar ---
# worker_state = {}
# worker_data = {}

# # ----------------------------
# # 🧾 HISOBOT YUBORISH (3 bosqich)
# # ----------------------------
# @router.message(F.text == "🧾 Hisobot yuborish")
# async def cmd_report_start(msg: types.Message):
#     worker_state[msg.from_user.id] = "report_text"
#     await msg.answer("✏️ Hisobot matnini yuboring:", reply_markup=ReplyKeyboardRemove())


# @router.message(F.text)
# async def report_steps(msg: types.Message):
#     uid = msg.from_user.id
#     state = worker_state.get(uid)

#     if state == "report_text":
#         worker_data[uid] = {"text": msg.text.strip()}
#         worker_state[uid] = "report_sum"
#         await msg.answer("💵 Bugungi savdo summasini kiriting (so‘mda):")
#         return

#     if state == "report_sum":
#         try:
#             summa = int(msg.text.replace(" ", ""))
#         except ValueError:
#             return await msg.answer("❌ Iltimos, faqat raqam kiriting (masalan: 1250000).")

#         worker_data[uid]["sum"] = summa
#         worker_state[uid] = "report_confirm"
#         await msg.answer(
#             f"🧾 Hisobot:\n{worker_data[uid]['text']}\n💵 {summa:,} so‘m\n\n"
#             "Tasdiqlash uchun <b>tasdiqlash</b> deb yozing yoki <b>bekor</b> deb yozing.",
#             parse_mode="HTML"
#         )
#         return

#     if state == "report_confirm":
#         if msg.text.lower() in ["tasdiqlash", "ok", "ha"]:
#             async with aiosqlite.connect(db.DB_PATH) as conn:
#                 async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
#                     worker = await cur.fetchone()

#                 if not worker:
#                     worker_state[uid] = None
#                     return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

#                 wid, fid, name = worker
#                 now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
#                 text = f"{worker_data[uid]['text']}\n💵 {worker_data[uid]['sum']:,} so‘m"

#                 await conn.execute(
#                     "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
#                     (wid, fid, text, now)
#                 )
#                 await conn.commit()

#             try:
#                 await msg.bot.send_message(SUPERADMIN_ID, f"📩 <b>Yangi hisobot:</b>\n👷 {name}\n🕒 {now}\n{text}",
#                                            parse_mode="HTML")
#             except Exception:
#                 pass

#             worker_state[uid] = None
#             await msg.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())

#         elif msg.text.lower() in ["bekor", "cancel"]:
#             worker_state[uid] = None
#             await msg.answer("❌ Hisobot bekor qilindi.", reply_markup=worker_menu())

# # ----------------------------
# # ⏰ ISHNI BOSHLADIM (bonus/jarima)
# # ----------------------------
# @router.message(F.text == "⏰ Ishni boshladim")
# async def start_work(msg: types.Message):
#     uid = msg.from_user.id
#     now = datetime.datetime.now()

#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
#             worker = await cur.fetchone()

#         if not worker:
#             return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

#         wid, fid, name = worker
#         current_minutes = now.hour * 60 + now.minute
#         start_minutes = 9 * 60  # 9:00
#         grace = 10  # 9:10 gacha kechikishsiz

#         if current_minutes < start_minutes:
#             diff = start_minutes - current_minutes
#             bonus = int((diff / 60) * 10000)
#             await conn.execute(
#                 "INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
#                 (wid, fid, f"Erta kelish ({diff} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M"))
#             )
#             await msg.answer(f"🎉 Erta keldingiz! Bonus: +{bonus:,} so‘m.", reply_markup=worker_menu())
#         elif current_minutes > start_minutes + grace:
#             diff = current_minutes - (start_minutes + grace)
#             fine = int((diff / 60) * 10000)
#             await conn.execute(
#                 "INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
#                 (wid, fid, f"Kechikish ({diff} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M"))
#             )
#             await msg.answer(f"⚠️ Kech keldingiz. Jarima: -{fine:,} so‘m.", reply_markup=worker_menu())
#         else:
#             await msg.answer("✅ Ishni o‘z vaqtida boshladingiz.", reply_markup=worker_menu())

#         await conn.execute(
#             "INSERT INTO work_start_log (worker_id, filial_id, start_time) VALUES (?, ?, ?)",
#             (wid, fid, now.strftime("%Y-%m-%d %H:%M"))
#         )
#         await conn.commit()

# # ----------------------------
# # 🏁 ISHNI TUGATDIM
# # ----------------------------
# @router.message(F.text == "🏁 Ishni tugatdim")
# async def end_work(msg: types.Message):
#     uid = msg.from_user.id
#     worker_state[uid] = "final_report"
#     await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())


# @router.message(F.text)
# async def handle_final_report(msg: types.Message):
#     uid = msg.from_user.id
#     if worker_state.get(uid) != "final_report":
#         return

#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
#             worker = await cur.fetchone()
#         if not worker:
#             worker_state[uid] = None
#             return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

#         wid, fid, name = worker
#         text = f"Yakuniy hisobot: {msg.text.strip()}"
#         now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
#         await conn.execute(
#             "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
#             (wid, fid, text, now)
#         )
#         await conn.commit()

#     worker_state[uid] = None
#     await msg.answer("✅ Yakuniy hisobot saqlandi.", reply_markup=worker_menu())

#     try:
#         await msg.bot.send_message(SUPERADMIN_ID, f"🏁 {name} yakuniy hisobot yubordi:\n{text}")
#     except Exception:
#         pass

# # ----------------------------
# # 📷 Tozalash rasmi yuborish
# # ----------------------------
# @router.message(F.text == "📷 Tozalash rasmi yuborish")
# async def clean_photo_request(msg: types.Message):
#     worker_state[msg.from_user.id] = "clean_photo"
#     await msg.answer("📸 Tozalangan joy rasmini yuboring:", reply_markup=ReplyKeyboardRemove())


# # ----------------------------
# # 📸 Muammo yuborish
# # ----------------------------
# @router.message(F.text == "📸 Muammo yuborish")
# async def problem_request(msg: types.Message):
#     worker_state[msg.from_user.id] = "problem_photo"
#     await msg.answer("⚠️ Muammo rasmini yoki tavsifini yuboring:", reply_markup=ReplyKeyboardRemove())


# @router.message(F.photo)
# async def handle_photos(msg: types.Message):
#     uid = msg.from_user.id
#     state = worker_state.get(uid)
#     if state not in ["clean_photo", "problem_photo"]:
#         return

#     file_id = msg.photo[-1].file_id
#     caption = msg.caption or ""
#     kind = "Tozalash rasmi" if state == "clean_photo" else "Muammo rasmi"

#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
#             worker = await cur.fetchone()
#         wid, fid, name = worker
#         now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
#         await conn.execute(
#             "INSERT INTO photos (worker_id, filial_id, file_id, note, created_at) VALUES (?, ?, ?, ?, ?)",
#             (wid, fid, file_id, caption, now)
#         )
#         await conn.commit()

#     await msg.bot.send_photo(
#         SUPERADMIN_ID,
#         file_id,
#         caption=f"📸 {kind}\n👷 {name}\n🕒 {now}\n📝 {caption}"
#     )

#     worker_state[uid] = None
#     await msg.answer("✅ Rasm yuborildi!", reply_markup=worker_menu())

# # ----------------------------
# # 📅 Bugungi hisobotlarim
# # ----------------------------
# @router.message(F.text == "📅 Bugungi hisobotlarim")
# async def show_today_reports(msg: types.Message):
#     uid = msg.from_user.id
#     today = datetime.datetime.now().strftime("%Y-%m-%d")
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("""
#             SELECT text, created_at FROM reports
#             WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)
#             AND DATE(created_at)=DATE(?)
#             ORDER BY id DESC
#         """, (uid, today)) as cur:
#             rows = await cur.fetchall()

#     if not rows:
#         return await msg.answer("📭 Bugun hech qanday hisobot yo‘q.", reply_markup=worker_menu())

#     text = "📅 <b>Bugungi hisobotlaringiz:</b>\n\n"
#     for r in rows:
#         text += f"🕒 {r[1]}\n{r[0]}\n\n"

#     await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())

# # ----------------------------
# # 💰 Bonus / Jarimalarim
# # ----------------------------
# @router.message(F.text == "💰 Bonus/Jarimalarim")
# async def show_finances(msg: types.Message):
#     uid = msg.from_user.id
#     async with aiosqlite.connect(db.DB_PATH) as conn:
#         async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
#             worker = await cur.fetchone()
#         if not worker:
#             return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
#         wid, name = worker

#         async with conn.execute("SELECT reason, amount, created_at FROM bonuses WHERE worker_id=?", (wid,)) as cur:
#             bonuses = await cur.fetchall()
#         async with conn.execute("SELECT reason, amount, created_at FROM fines WHERE worker_id=?", (wid,)) as cur:
#             fines = await cur.fetchall()

#     text = f"💰 <b>{name}</b> uchun:\n\n"
#     if bonuses:
#         text += "🎉 Bonuslar:\n" + "\n".join([f"+{b[1]:,} so‘m — {b[0]} ({b[2]})" for b in bonuses]) + "\n\n"
#     if fines:
#         text += "⚠️ Jarimalar:\n" + "\n".join([f"-{f[1]:,} so‘m — {f[0]} ({f[2]})" for f in fines]) + "\n\n"
#     if not bonuses and not fines:
#         text += "📭 Hozircha hech narsa yo‘q."

#     await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())

# # ----------------------------
# # ↩️ Menyuga qaytish
# # ----------------------------
# @router.message(F.text == "↩️ Menyuga qaytish")
# async def back_to_menu(msg: types.Message):
#     worker_state[msg.from_user.id] = None
#     await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())

from aiogram import Router, F, types
from keyboards.worker_kb import worker_menu
import datetime, aiosqlite
from database import db
from config import SUPERADMIN_ID

router = Router()
worker_state = {}

# 1️⃣ Ishni boshladim
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    await msg.answer("✅ Ishni boshladingiz. Omad!", reply_markup=worker_menu())

# 2️⃣ Ishni tugatdim
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=worker_menu())

# 3️⃣ Tozalash rasmi
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def send_clean_photo(msg: types.Message):
    await msg.answer("📸 Tozalash rasmini yuboring:", reply_markup=worker_menu())

# 4️⃣ Muammo yuborish
@router.message(F.text == "📸 Muammo yuborish")
async def send_problem_photo(msg: types.Message):
    await msg.answer("⚠️ Muammo haqida rasm/izoh yuboring:", reply_markup=worker_menu())

# 5️⃣ Bugungi hisobotlarim
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def today_reports(msg: types.Message):
    await msg.answer("📅 Bugungi hisobotlaringiz yo‘q yoki tayyor emas.", reply_markup=worker_menu())

# 6️⃣ Bonus/Jarimalarim
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def finance_info(msg: types.Message):
    await msg.answer("💰 Bonus va jarimalaringiz hozircha mavjud emas.", reply_markup=worker_menu())

# 7️⃣ Hisobot yuborish
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report(msg: types.Message):
    await msg.answer("✏️ Hisobot matnini yuboring:", reply_markup=worker_menu())

# 8️⃣ Menyuga qaytish
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
