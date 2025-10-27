from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID
from database import db
import datetime
import aiosqlite

router = Router()

# Global holat
worker_state = {}
worker_data = {}


# 🧾 HISOBOT YUBORISH (3 bosqich)
@router.message(F.text == "🧾 Hisobot yuborish")
async def start_report(msg: types.Message):
    await msg.answer("✏️ Bugungi ish hisobotini yozing:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_report_text"


@router.message(F.text, ~F.text.in_(["↩️ Menyuga qaytish"]))
async def handle_report_steps(msg: types.Message):
    user_id = msg.from_user.id
    state = worker_state.get(user_id)

    if state == "waiting_report_text":
        worker_data[user_id] = {"text": msg.text}
        worker_state[user_id] = "waiting_sales_sum"
        await msg.answer("💵 Bugungi savdo summasini kiriting (so‘mda):")
        return

    elif state == "waiting_sales_sum":
        try:
            worker_data[user_id]["sum"] = int(msg.text.replace(" ", ""))
        except:
            return await msg.answer("❌ Iltimos, raqam kiriting (masalan: 1200000).")
        worker_state[user_id] = "waiting_confirm"
        await msg.answer(
            f"✅ Hisobot:\n🧾 {worker_data[user_id]['text']}\n💵 {worker_data[user_id]['sum']:,} so‘m\n\n"
            "Tasdiqlash uchun <b>Tasdiqlash</b> deb yozing."
        )
        return

    elif state == "waiting_confirm" and msg.text.lower() in ["tasdiqlash", "ok", "✅ tasdiqlash"]:
        async with aiosqlite.connect(db.DB_PATH) as conn:
            async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
                worker = await cur.fetchone()
            if not worker:
                return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            text = f"🧾 {worker_data[user_id]['text']}\n💵 Savdo: {worker_data[user_id]['sum']:,} so‘m"
            await conn.execute("""
                INSERT INTO reports (worker_id, filial_id, text, created_at)
                VALUES (?, ?, ?, ?)
            """, (worker[0], worker[1], text, now))
            await conn.commit()

        try:
            await msg.bot.send_message(
                SUPERADMIN_ID,
                f"📩 <b>Yangi hisobot:</b>\n👷 {worker[2]}\n🕒 {now}\n{text}",
                parse_mode="HTML"
            )
        except Exception as e:
            print("⚠️ Superadminga yuborilmadi:", e)

        worker_state[user_id] = None
        await msg.answer("✅ Hisobotingiz yuborildi!", reply_markup=worker_menu())


# ⏰ ISHNI BOSHLADIM
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(msg: types.Message):
    user_id = msg.from_user.id
    now = datetime.datetime.now()

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
            worker = await cur.fetchone()

        if not worker:
            return await msg.answer("❌ Siz tizimda yo‘qsiz.", reply_markup=worker_menu())

        await conn.execute("""
            INSERT INTO work_start_log (worker_id, filial_id, start_time)
            VALUES (?, ?, ?)
        """, (worker[0], worker[1], now.strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    await msg.answer("✅ Ishni boshladingiz. Omad!", reply_markup=worker_menu())


# 🏁 ISHNI TUGATDIM
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(msg: types.Message):
    await msg.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())
    worker_state[msg.from_user.id] = "waiting_final_report"


@router.message(F.text)
async def handle_final_report(msg: types.Message):
    user_id = msg.from_user.id
    if worker_state.get(user_id) != "waiting_final_report":
        return

    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, filial_id, name FROM workers WHERE tg_id=?", (user_id,)) as cur:
            worker = await cur.fetchone()

        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES (?, ?, ?, ?)
        """, (worker[0], worker[1], f"Yakuniy: {msg.text}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        await conn.commit()

    await msg.answer("✅ Yakuniy hisobot yuborildi!", reply_markup=worker_menu())


# 📦 MAHSULOTLARIM
@router.message(F.text == "📦 Mahsulotlarim")
async def products_menu(msg: types.Message):
    await msg.answer(
        "📦 Mahsulotlaringizni boshqarish:\n"
        "➕ Qo‘shish uchun — <b>Mahsulot qo‘shish</b>\n"
        "❌ O‘chirish uchun — <b>Mahsulot o‘chirish</b>\n"
        "📋 Ko‘rish uchun — <b>Mahsulotlarni ko‘rish</b>",
        reply_markup=worker_menu()
    )


# 💰 BONUS/JARIMALAR
@router.message(F.text == "💰 Bonus/Jarimalarim")
async def show_finance(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM workers WHERE tg_id=?", (msg.from_user.id,)) as cur:
            worker = await cur.fetchone()
        if not worker:
            return await msg.answer("❌ Siz tizimda ro‘yxatdan o‘tmagansiz.", reply_markup=worker_menu())

        async with conn.execute("SELECT reason, amount FROM bonuses WHERE worker_id=?", (worker[0],)) as cur:
            bonuses = await cur.fetchall()
        async with conn.execute("SELECT reason, amount FROM fines WHERE worker_id=?", (worker[0],)) as cur:
            fines = await cur.fetchall()

    text = f"💰 <b>{worker[1]} uchun bonus va jarimalar:</b>\n\n"
    if bonuses:
        text += "🎉 Bonuslar:\n" + "\n".join([f"➕ {b[1]} so‘m — {b[0]}" for b in bonuses]) + "\n\n"
    if fines:
        text += "⚠️ Jarimalar:\n" + "\n".join([f"➖ {f[1]} so‘m — {f[0]}" for f in fines])
    if not bonuses and not fines:
        text += "📭 Hozircha ma’lumot yo‘q."

    await msg.answer(text, parse_mode="HTML", reply_markup=worker_menu())


# ↩️ MENYUGA QAYTISH
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    await msg.answer("👷 Ishchi menyusi:", reply_markup=worker_menu())
