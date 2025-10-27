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

# ========== ⏰ ISHNI BOSHLADIM ==========
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    now = datetime.datetime.now()
    uid = msg.from_user.id

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()

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
            await conn.execute("INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                               (wid, fid, f"Erta kelish ({diff} daqiqa)", bonus, now.strftime("%Y-%m-%d %H:%M")))
        elif current_minutes > start_minutes + grace_minutes:
            diff = current_minutes - (start_minutes + grace_minutes)
            fine = int((diff / 60) * 10000)
            await conn.execute("INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                               (wid, fid, f"Kechikish ({diff} daqiqa)", fine, now.strftime("%Y-%m-%d %H:%M")))

        await conn.commit()

    text = f"✅ Ishni boshladingiz.\n🕒 {now.strftime('%H:%M')}"
    if bonus:
        text += f"\n🎉 Bonus: +{bonus:,} so‘m"
    if fine:
        text += f"\n⚠️ Jarima: -{fine:,} so‘m"

    await msg.answer(text, reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"🕒 {worker[2]} ishni boshladi.\n{text}", parse_mode="HTML")


# ========== 🏁 ISHNI TUGATDIM ==========
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
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if worker:
            wid, fid, wname = worker
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                               (wid, fid, f"Yakuniy hisobot: {text}", now))
            await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"🏁 <b>{wname}</b> yakuniy hisobot yubordi:\n{text}", parse_mode="HTML")


# ========== 📷 TOZALASH RASMI ==========
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
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if worker:
            wid, fid, wname = worker
            await conn.execute("INSERT INTO photos (worker_id, filial_id, file_id, note, created_at) VALUES (?, ?, ?, ?, ?)",
                               (wid, fid, file_id, caption, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Rasm yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=f"🧹 Tozalash rasmi — {wname}\n{caption}")


# ========== 📸 MUAMMO YUBORISH ==========
@router.message(F.text == "📸 Muammo yuborish")
async def problem_start(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_problem_photo"
    await msg.answer("⚠️ Muammo rasm/izoh bilan yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message(F.photo)
async def receive_problem_photo(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_problem_photo":
        return
    file_id = msg.photo[-1].file_id
    caption = msg.caption or ""
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if worker:
            wid, fid, wname = worker
            await conn.execute("INSERT INTO problems (worker_id, filial_id, note, file_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                               (wid, fid, caption, file_id, "new", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Muammo yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_photo(SUPERADMIN_ID, file_id, caption=f"⚠️ Muammo — {wname}\n{caption}")


# ========== 📅 BUGUNGI HISOBOTLARIM ==========
@router.message(F.text == "📅 Bugungi hisobotlarim")
async def today_reports(msg: types.Message):
    uid = msg.from_user.id
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT id, text, created_at FROM reports
            WHERE worker_id=(SELECT id FROM workers WHERE tg_id=?)
            AND DATE(created_at)=DATE(?)
            ORDER BY id DESC
        """, (uid, today)) as cur:
            reports = await cur.fetchall()
    if not reports:
        return await msg.answer("📭 Bugun hech qanday hisobot yo‘q.", reply_markup=worker_menu())

    text = "📅 Bugungi hisobotlaringiz:\n\n"
    for r in reports:
        text += f"🆔 {r[0]} — {r[2]}\n{r[1]}\n\n"
    text += "✏️ Tahrirlash uchun: tahrir <ID>"
    await msg.answer(text, reply_markup=worker_menu())


# ========== 💰 BONUS/JARIMALARIM ==========
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finances(msg: types.Message):
    uid = msg.from_user.id
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, wname = worker
        async with conn.execute("SELECT reason, amount FROM bonuses WHERE worker_id=?", (wid,)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount FROM fines WHERE worker_id=?", (wid,)) as cur:
            fines = await cur.fetchall()

    text = f"💰 <b>{wname}</b> uchun:\n\n"
    if bonuses:
        text += "🎉 Bonuslar:\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]}" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ Jarimalar:\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]}" for f in fines])
    if not bonuses and not fines:
        text += "📭 Ma’lumot yo‘q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"💰 <b>{wname}</b> bonus/jarima hisobotini ko‘rdi.", parse_mode="HTML")


# ========== ↩️ MENYUGA QAYTISH ==========
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
