import datetime
import aiosqlite
from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from database import db
from config import SUPERADMIN_ID

router = Router()
worker_state = {}
worker_data = {}

# === 🧾 HISOBOT YUBORISH ===
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_report_text"
    await msg.answer("🖋 Hisobot matnini kiriting:", reply_markup=ReplyKeyboardRemove())

@router.message()
async def handle_report(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)

    if state == "waiting_report_text":
        worker_data[uid] = {"text": msg.text.strip()}
        worker_state[uid] = "waiting_sum"
        return await msg.answer("💰 Bugungi savdo summasini kiriting (so‘mda):")

    elif state == "waiting_sum":
        try:
            summa = int(msg.text.replace(" ", ""))
        except:
            return await msg.answer("❌ Faqat raqam kiriting (masalan: 200000).")
        worker_data[uid]["sum"] = summa
        worker_state[uid] = "confirm_report"
        return await msg.answer(
            f"✅ Hisobot tayyor:\n\n🧾 {worker_data[uid]['text']}\n💵 {summa:,} so‘m\n\n"
            f"Tasdiqlash uchun <b>tasdiqlash</b>, bekor qilish uchun <b>bekor</b> yozing.",
            parse_mode="HTML"
        )

    elif state == "confirm_report":
        text = msg.text.lower()
        if text == "tasdiqlash":
            async with aiosqlite.connect(db.DB_PATH) as conn:
                worker = await conn.execute_fetchone(
                    "SELECT id, filial_id, name FROM workers WHERE tg_id=?",
                    (uid,)
                )
                if not worker:
                    return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

                wid, fid, wname = worker
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                text_full = f"{worker_data[uid]['text']}\n💵 {worker_data[uid]['sum']:,} so‘m"

                await conn.execute(
                    "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                    (wid, fid, text_full, now)
                )
                await conn.commit()

            await msg.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())
            await msg.bot.send_message(
                SUPERADMIN_ID,
                f"📩 <b>Yangi hisobot</b>\n👷 {wname}\n🕒 {now}\n{text_full}",
                parse_mode="HTML"
            )
            worker_state.pop(uid, None)
            worker_data.pop(uid, None)

        elif text == "bekor":
            worker_state.pop(uid, None)
            worker_data.pop(uid, None)
            await msg.answer("❌ Hisobot bekor qilindi.", reply_markup=worker_menu())


# === ⏰ ISHNI BOSHLADIM ===
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    now = datetime.datetime.now()
    uid = msg.from_user.id

    async with aiosqlite.connect(db.DB_PATH) as conn:
        worker = await conn.execute_fetchone(
            "SELECT id, filial_id, name FROM workers WHERE tg_id=?",
            (uid,)
        )
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        start_minutes = 9 * 60
        grace_minutes = 10
        current_minutes = now.hour * 60 + now.minute
        bonus, fine = 0, 0

        if current_minutes < start_minutes:
            diff = start_minutes - current_minutes
            bonus = int((diff / 60) * 10000)
            await conn.execute(
                "INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                (wid, fid, f"Erta kelish ({diff} daqiqa)", bonus, now)
            )
        elif current_minutes > start_minutes + grace_minutes:
            diff = current_minutes - (start_minutes + grace_minutes)
            fine = int((diff / 60) * 10000)
            await conn.execute(
                "INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                (wid, fid, f"Kechikish ({diff} daqiqa)", fine, now)
            )

        await conn.commit()

    text = f"✅ Ishni boshladingiz.\n🕒 {now.strftime('%H:%M')}"
    if bonus:
        text += f"\n🎉 Bonus: +{bonus:,} so‘m"
    if fine:
        text += f"\n⚠️ Jarima: -{fine:,} so‘m"

    await msg.answer(text, reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"🕒 {wname} ishni boshladi.\n{text}")


# === 🏁 ISHNI TUGATDIM ===
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_final_report"
    await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message()
async def handle_final_report(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_final_report":
        return
    text = msg.text
    async with aiosqlite.connect(db.DB_PATH) as conn:
        worker = await conn.execute_fetchone(
            "SELECT id, filial_id, name FROM workers WHERE tg_id=?",
            (uid,)
        )
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        await conn.execute(
            "INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
            (wid, fid, f"🏁 Yakuniy hisobot: {text}", now)
        )
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"🏁 <b>{wname}</b> yakuniy hisobot yubordi:\n{text}", parse_mode="HTML")


# === 📷 TOZALASH RASMI ===
@router.message(F.text == "📷 Tozalash rasmi yuborish")
async def clean_photo_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_clean_photo"
    await msg.answer("📸 Tozalash rasmini yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message(F.photo)
async def receive_clean_photo(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_clean_photo":
        return
    file_id = msg.photo[-1].file_id
    caption = msg.caption or ""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        worker = await conn.execute_fetchone(
            "SELECT id, filial_id, name FROM workers WHERE tg_id=?",
            (uid,)
        )
        if worker:
            wid, fid, wname = worker
            await conn.execute(
                "INSERT INTO photos (worker_id, filial_id, file_id, note, created_at) VALUES (?, ?, ?, ?, ?)",
                (wid, fid, file_id, caption, datetime.datetime.now())
            )
            await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Rasm yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=f"🧹 Tozalash rasmi — {wname}\n{caption}")


# === 📸 MUAMMO YUBORISH ===
@router.message(F.text == "📸 Muammo yuborish")
async def problem_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_problem_photo"
    await msg.answer("⚠️ Muammo rasm yoki izoh bilan yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message(F.photo)
async def receive_problem_photo(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_problem_photo":
        return
    file_id = msg.photo[-1].file_id
    caption = msg.caption or ""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        worker = await conn.execute_fetchone(
            "SELECT id, filial_id, name FROM workers WHERE tg_id=?",
            (uid,)
        )
        if worker:
            wid, fid, wname = worker
            await conn.execute(
                "INSERT INTO problems (worker_id, filial_id, note, file_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (wid, fid, caption, file_id, "new", datetime.datetime.now())
            )
            await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Muammo yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=f"⚠️ Muammo — {wname}\n{caption}")


# === 📅 BUGUNGI HISOBOTLARIM ===
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def today_reports(msg: types.Message):
    uid = msg.from_user.id
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        reports = await conn.execute_fetchall(
            """
            SELECT id, text, created_at FROM reports
            WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)
            AND DATE(created_at)=DATE(?)
            ORDER BY id DESC
            """,
            (uid, today)
        )
    if not reports:
        return await msg.answer("📭 Bugun hech qanday hisobot yo‘q.", reply_markup=worker_menu())

    text = "📅 Bugungi hisobotlaringiz:\n\n"
    for r in reports:
        text += f"🆔 {r[0]} — {r[2]}\n{r[1]}\n\n"
    await msg.answer(text, reply_markup=worker_menu())


# === 💰 BONUS/JARIMALARIM ===
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finances(msg: types.Message):
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        worker = await conn.execute_fetchone("SELECT id, name FROM workers WHERE tg_id=?", (uid,))
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, wname = worker
        bonuses = await conn.execute_fetchall("SELECT reason, amount FROM bonuses WHERE worker_id=?", (wid,))
        fines = await conn.execute_fetchall("SELECT reason, amount FROM fines WHERE worker_id=?", (wid,))

    text = f"💰 <b>{wname}</b> uchun:\n\n"
    if bonuses:
        text += "🎉 Bonuslar:\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]}" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ Jarimalar:\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]}" for f in fines])
    if not bonuses and not fines:
        text += "📭 Ma’lumot yo‘q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# === ↩️ MENYUGA QAYTISH ===
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
