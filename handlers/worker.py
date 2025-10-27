from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from keyboards.worker_kb import worker_menu
from config import SUPERADMIN_ID
import datetime
import aiosqlite
from database import db

router = Router()
worker_state = {}

# 🧾 HISOBOT YUBORISH
@router.message(F.text == "🧾 Hisobot yuborish")
async def send_report_prompt(message: types.Message):
    await message.answer(
        "🧾 Hisobot matnini yuboring (masalan: 5 ta mijoz, 3 ta tozalash, 1 muammo):",
        reply_markup=ReplyKeyboardRemove()
    )
    worker_state[message.from_user.id] = "waiting_report_text"


@router.message(F.text)
async def receive_report(message: types.Message):
    uid = message.from_user.id
    state = worker_state.get(uid)

    if state != "waiting_report_text":
        return

    report_text = message.text.strip()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # bazaga yozish
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("""
            INSERT INTO reports (worker_id, filial_id, text, created_at)
            VALUES ((SELECT id FROM workers WHERE tg_id=?), 
                    (SELECT filial_id FROM workers WHERE tg_id=?),
                    ?, ?)
        """, (uid, uid, report_text, now))
        await conn.commit()

    worker_state[uid] = None
    await message.answer("✅ Hisobot yuborildi!", reply_markup=worker_menu())

    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            f"📩 <b>Yangi hisobot</b>\n👷 {message.from_user.full_name}\n🕒 {now}\n🧾 {report_text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print("⚠️ Superadminga yuborishda xato:", e)


# ⏰ ISHNI BOSHLADIM — BONUS / JARIMA
@router.message(F.text == "⏰ Ishni boshladim")
async def start_work(message: types.Message):
    now = datetime.datetime.now()
    uid = message.from_user.id

    start_time = 9 * 60  # 09:00
    grace_time = 9 * 60 + 10  # 09:10
    current_time = now.hour * 60 + now.minute

    bonus, fine = 0, 0
    if current_time < start_time:
        diff = start_time - current_time
        bonus = int((diff / 60) * 10000)
        reason = f"Erta kelish ({diff} daqiqa)"
        await db.add_bonus(uid, reason, bonus)
    elif current_time > grace_time:
        diff = current_time - grace_time
        fine = int((diff / 60) * 10000)
        reason = f"Kechikish ({diff} daqiqa)"
        await db.add_fine(uid, reason, fine)

    text = f"✅ Ishni boshladingiz ({now.strftime('%H:%M')})"
    if bonus:
        text += f"\n🎉 Bonus: +{bonus:,} so‘m"
    elif fine:
        text += f"\n⚠️ Jarima: -{fine:,} so‘m"

    await message.answer(text, reply_markup=worker_menu())

    try:
        await message.bot.send_message(
            SUPERADMIN_ID,
            f"🕒 Ishchi {message.from_user.full_name} ishni boshladi.\n{text}"
        )
    except:
        pass


# 🏁 ISHNI TUGATDIM — HISOBOT
@router.message(F.text == "🏁 Ishni tugatdim")
async def end_work(message: types.Message):
    await message.answer("✏️ Yakuniy hisobotni yozing:", reply_markup=ReplyKeyboardRemove())
    worker_state[message.from_user.id] = "waiting_final_report"


@router.message(F.text)
async def receive_final_report(message: types.Message):
    uid = message.from_user.id
    if worker_state.get(uid) != "waiting_final_report":
        return

    text = message.text
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    await db.add_report(uid, f"Yakuniy hisobot: {text}", now)
    worker_state[uid] = None

    await message.answer("
