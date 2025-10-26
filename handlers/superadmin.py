# from aiogram import Router, types, F
# from aiogram.fsm.context import FSMContext
# from aiogram.filters import Command
# from aiogram.types import ReplyKeyboardRemove
# from keyboards.superadmin_kb import superadmin_menu
# from database import db
# import pandas as pd
# import datetime
# import io
# import os

# router = Router()
# SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID") or 0)

# # --- FSM holatlari ---
# from aiogram.fsm.state import StatesGroup, State


# class AddFilial(StatesGroup):
#     waiting_for_name = State()
#     waiting_for_id = State()


# class DeleteFilial(StatesGroup):
#     waiting_for_id = State()


# class AddAdmin(StatesGroup):
#     waiting_for_name = State()
#     waiting_for_tg_id = State()
#     waiting_for_filial_id = State()


# class DeleteAdmin(StatesGroup):
#     waiting_for_tg_id = State()


# # --- Faqat SuperAdmin uchun ---
# def is_superadmin(user_id: int):
#     return user_id == SUPERADMIN_ID


# # --- /superadmin buyrug‘i bilan menyuni ochish ---
# @router.message(Command("superadmin"))
# async def superadmin_panel(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("❌ Siz SuperAdmin emassiz.")
#     await msg.answer("👑 SuperAdmin menyusi:", reply_markup=superadmin_menu())


# # --- 🏢 Filiallar ro‘yxati ---
# @router.message(F.text == "🏢 Filiallar ro‘yxati")
# async def filial_list(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     cur = db.get_conn().cursor()
#     filials = cur.execute("SELECT name, filial_id FROM filials").fetchall()
#     if not filials:
#         return await msg.answer("📭 Hech qanday filial topilmadi.")
#     text = "🏢 <b>Filiallar ro‘yxati:</b>\n\n"
#     for f in filials:
#         text += f"• {f[0]} — <code>{f[1]}</code>\n"
#     await msg.answer(text, parse_mode="HTML", reply_markup=superadmin_menu())


# # --- ➕ Filial qo‘shish ---
# @router.message(F.text == "➕ Filial qo‘shish")
# async def add_filial_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     await msg.answer("✏️ Filial nomini kiriting:", reply_markup=ReplyKeyboardRemove())
#     await state.set_state(AddFilial.waiting_for_name)


# @router.message(AddFilial.waiting_for_name)
# async def add_filial_ask_id(msg: types.Message, state: FSMContext):
#     name = msg.text.strip()
#     await state.update_data(name=name)
#     await msg.answer("🔢 Endi filial uchun unikal ID kiriting (masalan: ASAKA_001):")
#     await state.set_state(AddFilial.waiting_for_id)


# async def add_filial_finish(msg: types.Message, state: FSMContext):
#     filial_id = msg.text.strip().upper()
#     data = await state.get_data()
#     name = data.get("name")

#     conn = db.get_conn()
#     cur = conn.cursor()
#     check = cur.execute("SELECT id FROM filials WHERE filial_id=?", (filial_id,)).fetchone()
#     if check:
#         return await msg.answer("⚠️ Bu ID allaqachon mavjud. Boshqa ID kiriting.")

#     cur.execute("INSERT INTO filials (name, filial_id) VALUES (?, ?)", (name, filial_id))
#     conn.commit()

#     await msg.answer(
#         f"✅ Filial qo‘shildi:\n<b>{name}</b> (ID: <code>{filial_id}</code>)",
#         parse_mode="HTML",
#         reply_markup=superadmin_menu(),
#     )
#     await state.clear()


# # --- ❌ Filialni o‘chirish ---
# @router.message(F.text == "❌ Filialni o‘chirish")
# async def delete_filial_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")

#     cur = db.get_conn().cursor()
#     filials = cur.execute("SELECT name, filial_id FROM filials").fetchall()
#     if not filials:
#         return await msg.answer("📭 Hech qanday filial mavjud emas.")

#     text = "🗑 O‘chirmoqchi bo‘lgan filialning ID sini kiriting:\n\n"
#     for f in filials:
#         text += f"🏢 {f[0]} — <code>{f[1]}</code>\n"

#     await msg.answer(text, parse_mode="HTML")
#     await state.set_state(DeleteFilial.waiting_for_id)


# @router.message(DeleteFilial.waiting_for_id)
# async def delete_filial_finish(msg: types.Message, state: FSMContext):
#     filial_id = msg.text.strip().upper()
#     conn = db.get_conn()
#     cur = conn.cursor()

#     check = cur.execute("SELECT id FROM filials WHERE filial_id=?", (filial_id,)).fetchone()
#     if not check:
#         return await msg.answer("❌ Bunday filial topilmadi.")

#     cur.execute("DELETE FROM filials WHERE filial_id=?", (filial_id,))
#     conn.commit()
#     await msg.answer(f"✅ Filial o‘chirildi: <code>{filial_id}</code>", parse_mode="HTML", reply_markup=superadmin_menu())
#     await state.clear()


# # --- 👥 Adminlar ro‘yxati ---
# @router.message(F.text == "👥 Adminlar ro‘yxati")
# async def admin_list(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     cur = db.get_conn().cursor()
#     admins = cur.execute("""
#         SELECT a.name, a.tg_id, f.name
#         FROM admins a
#         LEFT JOIN filials f ON f.id = a.filial_id
#     """).fetchall()
#     if not admins:
#         return await msg.answer("📭 Adminlar ro‘yxati bo‘sh.")
#     text = "👥 <b>Adminlar ro‘yxati:</b>\n\n"
#     for a in admins:
#         text += f"🧑 {a[0]} — TG ID: <code>{a[1]}</code> — 🏢 {a[2]}\n"
#     await msg.answer(text, parse_mode="HTML", reply_markup=superadmin_menu())


# # --- ➕ Admin qo‘shish ---
# @router.message(F.text == "➕ Admin qo‘shish")
# async def add_admin_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     await msg.answer("👤 Admin ismini kiriting:", reply_markup=ReplyKeyboardRemove())
#     await state.set_state(AddAdmin.waiting_for_name)


# @router.message(AddAdmin.waiting_for_name)
# async def add_admin_tg_id(msg: types.Message, state: FSMContext):
#     await state.update_data(name=msg.text)
#     await msg.answer("📱 Adminning Telegram ID raqamini kiriting (faqat raqam):")
#     await state.set_state(AddAdmin.waiting_for_tg_id)


# @router.message(AddAdmin.waiting_for_tg_id)
# async def add_admin_filial(msg: types.Message, state: FSMContext):
#     tg_id = msg.text.strip()
#     if not tg_id.isdigit():
#         return await msg.answer("⚠️ Faqat raqam kiriting.")
#     await state.update_data(tg_id=tg_id)

#     cur = db.get_conn().cursor()
#     filials = cur.execute("SELECT id, name FROM filials").fetchall()
#     if not filials:
#         return await msg.answer("❌ Filiallar mavjud emas, avval filial qo‘shing.")

#     text = "🏢 Qaysi filialga biriktirasiz (raqamini kiriting):\n\n"
#     for f in filials:
#         text += f"{f[0]}. {f[1]}\n"
#     await msg.answer(text)
#     await state.set_state(AddAdmin.waiting_for_filial_id)


# @router.message(AddAdmin.waiting_for_filial_id)
# async def add_admin_finish(msg: types.Message, state: FSMContext):
#     data = await state.get_data()
#     try:
#         filial_id = int(msg.text.strip())
#     except ValueError:
#         return await msg.answer("⚠️ Filial raqamini to‘g‘ri kiriting (raqam).")

#     conn = db.get_conn()
#     conn.execute(
#         "INSERT INTO admins (name, tg_id, filial_id) VALUES (?, ?, ?)",
#         (data["name"], data["tg_id"], filial_id),
#     )
#     conn.commit()
#     await msg.answer("✅ Admin muvaffaqiyatli qo‘shildi.", reply_markup=superadmin_menu())
#     await state.clear()


# # --- 🗑 Adminni o‘chirish ---
# @router.message(F.text == "🗑 Adminni o‘chirish")
# async def delete_admin_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     await msg.answer("🗑 O‘chirmoqchi bo‘lgan adminning Telegram ID raqamini kiriting:")
#     await state.set_state(DeleteAdmin.waiting_for_tg_id)


# @router.message(DeleteAdmin.waiting_for_tg_id)
# async def delete_admin_finish(msg: types.Message, state: FSMContext):
#     tg_id = msg.text.strip()
#     conn = db.get_conn()
#     cur = conn.cursor()
#     check = cur.execute("SELECT id FROM admins WHERE tg_id=?", (tg_id,)).fetchone()
#     if not check:
#         return await msg.answer("❌ Bunday admin topilmadi.")
#     cur.execute("DELETE FROM admins WHERE tg_id=?", (tg_id,))
#     conn.commit()
#     await msg.answer("✅ Admin o‘chirildi.", reply_markup=superadmin_menu())
#     await state.clear()


# # --- 📦 Export (Excel) ---
# @router.message(F.text == "📦 Export (Excel)")
# async def export_reports(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     conn = db.get_conn()
#     df = pd.read_sql_query("SELECT * FROM reports", conn)
#     if df.empty:
#         return await msg.answer("📭 Hisobotlar mavjud emas.")
#     filename = f"hisobot_{datetime.date.today()}.xlsx"
#     buffer = io.BytesIO()
#     df.to_excel(buffer, index=False)
#     buffer.seek(0)
#     await msg.answer_document(types.input_file.BufferedInputFile(buffer.read(), filename))


# # --- ⚠️ Muammolar ro‘yxati ---
# @router.message(F.text == "⚠️ Muammolar ro‘yxati")
# async def superadmin_problems(msg: types.Message):
#     cur = db.get_conn().cursor()
#     problems = cur.execute("""
#         SELECT f.name, w.name, p.note, p.file_id, p.created_at
#         FROM problems p
#         JOIN workers w ON w.id = p.worker_id
#         JOIN filials f ON f.id = p.filial_id
#         ORDER BY p.id DESC LIMIT 20
#     """).fetchall()

#     if not problems:
#         return await msg.answer("✅ Hozircha muammo yo‘q.")

#     for pr in problems:
#         await msg.answer_photo(
#             pr[3],
#             caption=f"🏢 Filial: <b>{pr[0]}</b>\n👷 Ishchi: {pr[1]}\n🕒 {pr[4]}\n\n📝 Izoh: {pr[2]}",
#             parse_mode="HTML",
#         )
import datetime
import sqlite3
import pandas as pd
from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardRemove
from database import db
from keyboards.superadmin_kb import superadmin_menu

router = Router()

# 🏢 FILIALLAR RO‘YXATI
@router.message(F.text == "🏢 Filiallar ro‘yxati")
async def filial_list(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    filials = cur.execute("SELECT id, name, filial_id FROM filials").fetchall()
    conn.close()

    if not filials:
        await msg.answer("🏢 Hech qanday filial mavjud emas.")
        return

    text = "🏢 <b>Filiallar ro‘yxati:</b>\n\n"
    for f in filials:
        text += f"{f[0]}. {f[1]} — ID: <code>{f[2]}</code>\n"
    await msg.answer(text, parse_mode="HTML")

# ➕ FILIAL QO‘SHISH
@router.message(F.text == "➕ Filial qo‘shish")
async def add_filial_start(msg: types.Message):
    await msg.answer("🏢 Yangi filial nomini kiriting:", reply_markup=ReplyKeyboardRemove())
    router._add_filial = True

@router.message()
async def add_filial_finish(msg: types.Message):
    if getattr(router, "_add_filial", False):
        name = msg.text.strip()
        conn = db.get_conn()
        cur = conn.cursor()
        filial_id = name.lower().replace(" ", "_")
        cur.execute("INSERT INTO filials (name, filial_id) VALUES (?, ?)", (name, filial_id))
        conn.commit()
        conn.close()
        router._add_filial = False
        await msg.answer(f"✅ Filial '{name}' muvaffaqiyatli qo‘shildi.", reply_markup=superadmin_menu())

# ❌ FILIALNI O‘CHIRISH
@router.message(F.text == "❌ Filialni o‘chirish")
async def delete_filial(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    filials = cur.execute("SELECT id, name FROM filials").fetchall()

    if not filials:
        await msg.answer("📭 O‘chirish uchun filial yo‘q.")
        return

    text = "❌ O‘chirmoqchi bo‘lgan filial raqamini yuboring:\n\n"
    for f in filials:
        text += f"{f[0]}. {f[1]}\n"

    await msg.answer(text)
    router._delete_filial = True

@router.message()
async def confirm_delete_filial(msg: types.Message):
    if getattr(router, "_delete_filial", False):
        try:
            filial_id = int(msg.text.strip())
        except ValueError:
            await msg.answer("⚠️ Iltimos, filial raqamini to‘g‘ri kiriting.")
            return

        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM filials WHERE id=?", (filial_id,))
        conn.commit()
        conn.close()
        router._delete_filial = False
        await msg.answer("✅ Filial muvaffaqiyatli o‘chirildi.", reply_markup=superadmin_menu())

# 👥 ADMINLAR RO‘YXATI
@router.message(F.text == "👥 Adminlar ro‘yxati")
async def admin_list(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    admins = cur.execute("""
        SELECT a.id, a.name, a.tg_id, f.name 
        FROM admins a 
        LEFT JOIN filials f ON f.id = a.filial_id
    """).fetchall()
    conn.close()

    if not admins:
        await msg.answer("📭 Adminlar ro‘yxati bo‘sh.")
        return

    text = "👥 <b>Adminlar ro‘yxati:</b>\n\n"
    for a in admins:
        text += f"🧑 {a[1]} — ID: <code>{a[2]}</code> — 🏢 {a[3]}\n"

    await msg.answer(text, parse_mode="HTML")

# ➕ ADMIN QO‘SHISH
@router.message(F.text == "➕ Admin qo‘shish")
async def add_admin_start(msg: types.Message):
    await msg.answer("🧑 Admin ismini kiriting:", reply_markup=ReplyKeyboardRemove())
    router._admin_step = "name"

@router.message()
async def add_admin_process(msg: types.Message):
    step = getattr(router, "_admin_step", None)
    if step == "name":
        router._admin_name = msg.text.strip()
        router._admin_step = "tg_id"
        await msg.answer("📱 Adminning Telegram ID raqamini kiriting:")
    elif step == "tg_id":
        router._admin_tg_id = msg.text.strip()
        conn = db.get_conn()
        cur = conn.cursor()
        filials = cur.execute("SELECT id, name FROM filials").fetchall()
        conn.close()

        if not filials:
            await msg.answer("❌ Filiallar yo‘q, avval filial qo‘shing.")
            router._admin_step = None
            return

        text = "🏢 Qaysi filialga biriktirasiz (raqamini kiriting):\n\n"
        for f in filials:
            text += f"{f[0]}. {f[1]}\n"
        await msg.answer(text)
        router._admin_step = "filial"
    elif step == "filial":
        try:
            filial_id = int(msg.text.strip())
        except ValueError:
            await msg.answer("⚠️ Iltimos, raqam kiriting.")
            return

        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO admins (name, tg_id, filial_id) VALUES (?, ?, ?)",
                    (router._admin_name, router._admin_tg_id, filial_id))
        conn.commit()
        conn.close()
        router._admin_step = None
        await msg.answer("✅ Admin muvaffaqiyatli qo‘shildi!", reply_markup=superadmin_menu())

# 🗑 ADMINNI O‘CHIRISH
@router.message(F.text == "🗑 Adminni o‘chirish")
async def delete_admin(msg: types.Message):
    await msg.answer("🆔 O‘chirmoqchi bo‘lgan adminning Telegram ID sini yuboring:")
    router._delete_admin = True

@router.message()
async def confirm_delete_admin(msg: types.Message):
    if getattr(router, "_delete_admin", False):
        tg_id = msg.text.strip()
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM admins WHERE tg_id=?", (tg_id,))
        conn.commit()
        conn.close()
        router._delete_admin = False
        await msg.answer("✅ Admin o‘chirildi.", reply_markup=superadmin_menu())

# 📅 BUGUNGI HISOBOTLAR
@router.message(F.text == "📅 Bugungi hisobotlar")
async def show_today_reports(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    reports = cur.execute("""
        SELECT w.name, r.text, r.created_at
        FROM reports r
        JOIN workers w ON w.id = r.worker_id
        WHERE DATE(r.created_at) = ?
        ORDER BY r.id DESC
    """, (today,)).fetchall()
    conn.close()

    if not reports:
        await msg.answer("📄 Bugun hech qanday hisobot kelmagan.")
        return

    text = f"📅 <b>Bugungi hisobotlar — {today}</b>\n\n"
    for name, rep_text, created in reports:
        text += f"👷‍♂️ <b>{name}</b>\n🕒 {created}\n🧾 {rep_text}\n\n"

    await msg.answer(text, parse_mode="HTML")

# 📊 UMUMIY HISOBOTLAR
@router.message(F.text == "📊 Umumiy hisobotlar")
async def show_all_reports(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    reports = cur.execute("""
        SELECT w.name, r.text, r.created_at
        FROM reports r
        JOIN workers w ON w.id = r.worker_id
        ORDER BY r.id DESC
        LIMIT 30
    """).fetchall()
    conn.close()

    if not reports:
        await msg.answer("📚 Hozircha umumiy hisobotlar mavjud emas.")
        return

    text = "📊 <b>So‘nggi 30 ta hisobot:</b>\n\n"
    for name, rep_text, created in reports:
        text += f"👷‍♂️ <b>{name}</b>\n🕒 {created}\n🧾 {rep_text}\n\n"

    await msg.answer(text, parse_mode="HTML")

# ⚠️ MUAMMOLAR RO‘YXATI
@router.message(F.text == "⚠️ Muammolar ro‘yxati")
async def show_problems(msg: types.Message):
    conn = db.get_conn()
    cur = conn.cursor()
    problems = cur.execute("""
        SELECT w.name, p.note, p.status, p.created_at
        FROM problems p
        JOIN workers w ON w.id = p.worker_id
        ORDER BY p.id DESC LIMIT 20
    """).fetchall()
    conn.close()

    if not problems:
        await msg.answer("✅ Hozircha muammolar yo‘q.")
        return

    text = "⚠️ <b>Oxirgi muammolar:</b>\n\n"
    for name, note, status, created in problems:
        text += f"👷‍♂️ {name}\n🕒 {created}\n📄 {note}\n📌 Holat: {status}\n\n"

    await msg.answer(text, parse_mode="HTML")

# 📦 EXPORT (EXCEL)
@router.message(F.text == "📦 Export (Excel)")
async def export_excel(msg: types.Message):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()

    reports = cur.execute("""
        SELECT w.name AS Ishchi, f.name AS Filial, r.text AS Hisobot, r.created_at AS Sana
        FROM reports r
        JOIN workers w ON w.id = r.worker_id
        JOIN filials f ON f.id = r.filial_id
        ORDER BY r.id DESC
    """).fetchall()

    bonuses = cur.execute("""
        SELECT w.name AS Ishchi, f.name AS Filial, b.reason AS Sabab, b.amount AS Miqdor, b.created_at AS Sana
        FROM bonuses b
        JOIN workers w ON w.id = b.worker_id
        JOIN filials f ON f.id = b.filial_id
        ORDER BY b.id DESC
    """).fetchall()

    fines = cur.execute("""
        SELECT w.name AS Ishchi, f.name AS Filial, f2.reason AS Sabab, f2.amount AS Miqdor, f2.created_at AS Sana
        FROM fines f2
        JOIN workers w ON w.id = f2.worker_id
        JOIN filials f ON f.id = f2.filial_id
        ORDER BY f2.id DESC
    """).fetchall()

    conn.close()

    with pd.ExcelWriter("hisobotlar.xlsx", engine="xlsxwriter") as writer:
        pd.DataFrame(reports, columns=["Ishchi", "Filial", "Hisobot", "Sana"]).to_excel(writer, sheet_name="Hisobotlar", index=False)
        pd.DataFrame(bonuses, columns=["Ishchi", "Filial", "Sabab", "Miqdor", "Sana"]).to_excel(writer, sheet_name="Bonuslar", index=False)
        pd.DataFrame(fines, columns=["Ishchi", "Filial", "Sabab", "Miqdor", "Sana"]).to_excel(writer, sheet_name="Jarimalar", index=False)

    await msg.answer_document(open("hisobotlar.xlsx", "rb"), caption="📦 Hisobotlar Excel faylga eksport qilindi!")
