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

# 🧾 HISOBOT YUBORISH (avtomatik bonus/jarima bilan)
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_report_text"
    worker_data[msg.from_user.id] = {}
    await msg.answer("✏️ Hisobot matnini yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message()
async def handle_report_steps(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if state == "waiting_report_text":
        worker_data[uid]["text"] = msg.text.strip()
        worker_state[uid] = "waiting_report_sum"
        await msg.answer("💰 Bugungi umumiy savdo summasini kiriting (so‘mda):")
        return

    elif state == "waiting_report_sum":
        try:
            amount = int(msg.text.replace(" ", ""))
        except:
            return await msg.answer("❌ Faqat raqam kiriting (masalan: 1200000).")
        worker_data[uid]["sum"] = amount
        worker_state[uid] = "waiting_report_confirm"
        await msg.answer(
            f"✅ Hisobot:\n🧾 {worker_data[uid]['text']}\n💵 {amount:,} so‘m\n"
            f"Tasdiqlash uchun 'tasdiqlash', bekor qilish uchun 'bekor' deb yozing."
        )
        return

    elif state == "waiting_report_confirm":
        text = msg.text.lower()
        if text not in ["tasdiqlash", "ok", "ha", "bekor"]:
            return await msg.answer("❗ Tasdiqlash uchun 'tasdiqlash' yoki 'bekor' deb yozing.")
        if text == "bekor":
            worker_state[uid] = None
            return await msg.answer("❌ Hisobot bekor qilindi.", reply_markup=worker_menu())

        # hisobotni DB ga yozish
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
                worker = await cur.fetchone()
            if not worker:
                return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
            wid, fid, wname = worker
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            text = f"{worker_data[uid]['text']}\n💵 Savdo: {worker_data[uid]['sum']:,} so‘m"
            await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                               (wid, fid, text, now))
            await conn.commit()

        # superadminga yuborish
        await msg.bot.send_message(SUPERADMIN_ID, f"📩 <b>Yangi hisobot</b>\n👷 {wname}\n🕒 {now}\n{text}",
                                   parse_mode="HTML")

        worker_state[uid] = None
        worker_data[uid] = {}
        await msg.answer("✅ Hisobot yuborildi.", reply_markup=worker_menu())


# ⏰ ISHNI BOSHLADIM — avtomatik bonus/jarima
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    uid = msg.from_user.id
    now = datetime.datetime.now()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        wid, fid, wname = worker
        start_time = now.strftime("%Y-%m-%d %H:%M")
        current_minutes = now.hour * 60 + now.minute
        start_minutes = 9 * 60
        grace_minutes = 10

        bonus, fine = 0, 0
        if current_minutes < start_minutes:  # erta keldi
            early_minutes = start_minutes - current_minutes
            bonus = int((early_minutes / 60) * 10000)
            reason = f"Erta kelish ({early_minutes} daqiqa)"
            await conn.execute("INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                               (wid, fid, reason, bonus, start_time))
        elif current_minutes > start_minutes + grace_minutes:  # kechikish
            late_minutes = current_minutes - (start_minutes + grace_minutes)
            fine = int((late_minutes / 60) * 10000)
            reason = f"Kechikish ({late_minutes} daqiqa)"
            await conn.execute("INSERT INTO fines (worker_id, filial_id, reason, amount, created_at) VALUES (?, ?, ?, ?, ?)",
                               (wid, fid, reason, fine, start_time))

        await conn.execute("INSERT INTO work_start_log (worker_id, filial_id, start_time) VALUES (?, ?, ?)",
                           (wid, fid, start_time))
        await conn.commit()

    msg_text = f"✅ Ishni boshladingiz.\n🕒 {start_time}"
    if bonus > 0:
        msg_text += f"\n🎉 Bonus: +{bonus:,} so‘m"
    if fine > 0:
        msg_text += f"\n⚠️ Jarima: -{fine:,} so‘m"

    await msg.answer(msg_text, reply_markup=worker_menu())

    # superadminga xabar
    await msg.bot.send_message(SUPERADMIN_ID, f"🕒 <b>{wname}</b> ishni boshladi.\n{msg_text}", parse_mode="HTML")


# 🏁 ISHNI TUGATDIM — yakuniy hisobot yuborish
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    worker_state[msg.from_user.id] = "waiting_final_report"
    await msg.answer("🖋 Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message()
async def receive_final_report(msg: types.Message):
    uid = msg.from_user.id
    if worker_state.get(uid) != "waiting_final_report":
        return
    text = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (uid,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())
        wid, fid, wname = worker
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        await conn.execute("INSERT INTO reports (worker_id, filial_id, text, created_at) VALUES (?, ?, ?, ?)",
                           (wid, fid, f"🏁 Yakuniy hisobot: {text}", now))
        await conn.commit()

    worker_state[uid] = None
    await msg.answer("✅ Yakuniy hisobot yuborildi.", reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"🏁 <b>{wname}</b> yakuniy hisobot yubordi:\n{text}", parse_mode="HTML")


# 📅 BUGUNGI HISOBOTLAR + TAHRIRLASH
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
        text += f"🆔 <b>{r[0]}</b> — {r[2]}\n{r[1]}\n\n"
    text += "✏️ Tahrirlash uchun 'tahrir <ID>' deb yozing."
    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())

@router.message(F.text.startswith("tahrir "))
async def edit_report(msg: types.Message):
    uid = msg.from_user.id
    try:
        rid = int(msg.text.split()[1])
    except:
        return await msg.answer("❌ To‘g‘ri format: tahrir <ID>")
    worker_state[uid] = f"edit_{rid}"
    await msg.answer("✏️ Yangi matnni yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message()
async def save_edit(msg: types.Message):
    uid = msg.from_user.id
    state = worker_state.get(uid)
    if not state or not state.startswith("edit_"):
        return
    rid = int(state.split("_")[1])
    new_text = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("UPDATE reports SET text=? WHERE id=? AND worker_id=(SELECT id FROM workers WHERE tg_id=?)",
                           (new_text, rid, uid))
        await conn.commit()
    worker_state[uid] = None
    await msg.answer("✅ Hisobot yangilandi.", reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"✏️ <b>Hisobot ID {rid}</b> tahrirlandi:\n{new_text}", parse_mode="HTML")


# 💰 BONUS/JARIMALAR — superadminga ham jo‘natiladi
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
        text += "🎉 Bonuslar:\n" + "\n".join([f"➕ {b[1]:,} so‘m — {b[0]}" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ Jarimalar:\n" + "\n".join([f"➖ {f[1]:,} so‘m — {f[0]}" for f in fines])
    if not bonuses and not fines:
        text += "📭 Ma’lumot yo‘q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())
    await msg.bot.send_message(SUPERADMIN_ID, f"💰 <b>{wname}</b> bonus/jarima hisobotini ko‘rdi:\n{text}", parse_mode="HTML")


# ↩️ MENYUGA QAYTISH
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_menu(msg: types.Message):
    worker_state[msg.from_user.id] = None
    await msg.answer("👷 Asosiy menyuga qaytdingiz.", reply_markup=worker_menu())
