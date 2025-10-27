# # from aiogram import Router, types, F
# # from aiogram.fsm.context import FSMContext
# # from aiogram.filters import Command
# # from aiogram.types import ReplyKeyboardRemove
# # from keyboards.superadmin_kb import superadmin_menu
# # from database import db
# # import pandas as pd
# # import datetime
# # import io
# # import os

# # router = Router()
# # SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID") or 0)

# # # --- FSM holatlari ---
# # from aiogram.fsm.state import StatesGroup, State


# # class AddFilial(StatesGroup):
# #     waiting_for_name = State()
# #     waiting_for_id = State()


# # class DeleteFilial(StatesGroup):
# #     waiting_for_id = State()


# # class AddAdmin(StatesGroup):
# #     waiting_for_name = State()
# #     waiting_for_tg_id = State()
# #     waiting_for_filial_id = State()


# # class DeleteAdmin(StatesGroup):
# #     waiting_for_tg_id = State()


# # # --- Faqat SuperAdmin uchun ---
# # def is_superadmin(user_id: int):
# #     return user_id == SUPERADMIN_ID


# # # --- /superadmin buyrug‘i bilan menyuni ochish ---
# # @router.message(Command("superadmin"))
# # async def superadmin_panel(msg: types.Message):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("❌ Siz SuperAdmin emassiz.")
# #     await msg.answer("👑 SuperAdmin menyusi:", reply_markup=superadmin_menu())


# # # --- 🏢 Filiallar ro‘yxati ---
# # @router.message(F.text == "🏢 Filiallar ro‘yxati")
# # async def filial_list(msg: types.Message):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
# #     cur = db.get_conn().cursor()
# #     filials = cur.execute("SELECT name, filial_id FROM filials").fetchall()
# #     if not filials:
# #         return await msg.answer("📭 Hech qanday filial topilmadi.")
# #     text = "🏢 <b>Filiallar ro‘yxati:</b>\n\n"
# #     for f in filials:
# #         text += f"• {f[0]} — <code>{f[1]}</code>\n"
# #     await msg.answer(text, parse_mode="HTML", reply_markup=superadmin_menu())


# # # --- ➕ Filial qo‘shish ---
# # @router.message(F.text == "➕ Filial qo‘shish")
# # async def add_filial_start(msg: types.Message, state: FSMContext):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
# #     await msg.answer("✏️ Filial nomini kiriting:", reply_markup=ReplyKeyboardRemove())
# #     await state.set_state(AddFilial.waiting_for_name)


# # @router.message(AddFilial.waiting_for_name)
# # async def add_filial_ask_id(msg: types.Message, state: FSMContext):
# #     name = msg.text.strip()
# #     await state.update_data(name=name)
# #     await msg.answer("🔢 Endi filial uchun unikal ID kiriting (masalan: ASAKA_001):")
# #     await state.set_state(AddFilial.waiting_for_id)


# # async def add_filial_finish(msg: types.Message, state: FSMContext):
# #     filial_id = msg.text.strip().upper()
# #     data = await state.get_data()
# #     name = data.get("name")

# #     conn = db.get_conn()
# #     cur = conn.cursor()
# #     check = cur.execute("SELECT id FROM filials WHERE filial_id=?", (filial_id,)).fetchone()
# #     if check:
# #         return await msg.answer("⚠️ Bu ID allaqachon mavjud. Boshqa ID kiriting.")

# #     cur.execute("INSERT INTO filials (name, filial_id) VALUES (?, ?)", (name, filial_id))
# #     conn.commit()

# #     await msg.answer(
# #         f"✅ Filial qo‘shildi:\n<b>{name}</b> (ID: <code>{filial_id}</code>)",
# #         parse_mode="HTML",
# #         reply_markup=superadmin_menu(),
# #     )
# #     await state.clear()


# # # --- ❌ Filialni o‘chirish ---
# # @router.message(F.text == "❌ Filialni o‘chirish")
# # async def delete_filial_start(msg: types.Message, state: FSMContext):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")

# #     cur = db.get_conn().cursor()
# #     filials = cur.execute("SELECT name, filial_id FROM filials").fetchall()
# #     if not filials:
# #         return await msg.answer("📭 Hech qanday filial mavjud emas.")

# #     text = "🗑 O‘chirmoqchi bo‘lgan filialning ID sini kiriting:\n\n"
# #     for f in filials:
# #         text += f"🏢 {f[0]} — <code>{f[1]}</code>\n"

# #     await msg.answer(text, parse_mode="HTML")
# #     await state.set_state(DeleteFilial.waiting_for_id)


# # @router.message(DeleteFilial.waiting_for_id)
# # async def delete_filial_finish(msg: types.Message, state: FSMContext):
# #     filial_id = msg.text.strip().upper()
# #     conn = db.get_conn()
# #     cur = conn.cursor()

# #     check = cur.execute("SELECT id FROM filials WHERE filial_id=?", (filial_id,)).fetchone()
# #     if not check:
# #         return await msg.answer("❌ Bunday filial topilmadi.")

# #     cur.execute("DELETE FROM filials WHERE filial_id=?", (filial_id,))
# #     conn.commit()
# #     await msg.answer(f"✅ Filial o‘chirildi: <code>{filial_id}</code>", parse_mode="HTML", reply_markup=superadmin_menu())
# #     await state.clear()


# # # --- 👥 Adminlar ro‘yxati ---
# # @router.message(F.text == "👥 Adminlar ro‘yxati")
# # async def admin_list(msg: types.Message):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
# #     cur = db.get_conn().cursor()
# #     admins = cur.execute("""
# #         SELECT a.name, a.tg_id, f.name
# #         FROM admins a
# #         LEFT JOIN filials f ON f.id = a.filial_id
# #     """).fetchall()
# #     if not admins:
# #         return await msg.answer("📭 Adminlar ro‘yxati bo‘sh.")
# #     text = "👥 <b>Adminlar ro‘yxati:</b>\n\n"
# #     for a in admins:
# #         text += f"🧑 {a[0]} — TG ID: <code>{a[1]}</code> — 🏢 {a[2]}\n"
# #     await msg.answer(text, parse_mode="HTML", reply_markup=superadmin_menu())


# # # --- ➕ Admin qo‘shish ---
# # @router.message(F.text == "➕ Admin qo‘shish")
# # async def add_admin_start(msg: types.Message, state: FSMContext):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
# #     await msg.answer("👤 Admin ismini kiriting:", reply_markup=ReplyKeyboardRemove())
# #     await state.set_state(AddAdmin.waiting_for_name)


# # @router.message(AddAdmin.waiting_for_name)
# # async def add_admin_tg_id(msg: types.Message, state: FSMContext):
# #     await state.update_data(name=msg.text)
# #     await msg.answer("📱 Adminning Telegram ID raqamini kiriting (faqat raqam):")
# #     await state.set_state(AddAdmin.waiting_for_tg_id)


# # @router.message(AddAdmin.waiting_for_tg_id)
# # async def add_admin_filial(msg: types.Message, state: FSMContext):
# #     tg_id = msg.text.strip()
# #     if not tg_id.isdigit():
# #         return await msg.answer("⚠️ Faqat raqam kiriting.")
# #     await state.update_data(tg_id=tg_id)

# #     cur = db.get_conn().cursor()
# #     filials = cur.execute("SELECT id, name FROM filials").fetchall()
# #     if not filials:
# #         return await msg.answer("❌ Filiallar mavjud emas, avval filial qo‘shing.")

# #     text = "🏢 Qaysi filialga biriktirasiz (raqamini kiriting):\n\n"
# #     for f in filials:
# #         text += f"{f[0]}. {f[1]}\n"
# #     await msg.answer(text)
# #     await state.set_state(AddAdmin.waiting_for_filial_id)


# # @router.message(AddAdmin.waiting_for_filial_id)
# # async def add_admin_finish(msg: types.Message, state: FSMContext):
# #     data = await state.get_data()
# #     try:
# #         filial_id = int(msg.text.strip())
# #     except ValueError:
# #         return await msg.answer("⚠️ Filial raqamini to‘g‘ri kiriting (raqam).")

# #     conn = db.get_conn()
# #     conn.execute(
# #         "INSERT INTO admins (name, tg_id, filial_id) VALUES (?, ?, ?)",
# #         (data["name"], data["tg_id"], filial_id),
# #     )
# #     conn.commit()
# #     await msg.answer("✅ Admin muvaffaqiyatli qo‘shildi.", reply_markup=superadmin_menu())
# #     await state.clear()


# # # --- 🗑 Adminni o‘chirish ---
# # @router.message(F.text == "🗑 Adminni o‘chirish")
# # async def delete_admin_start(msg: types.Message, state: FSMContext):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
# #     await msg.answer("🗑 O‘chirmoqchi bo‘lgan adminning Telegram ID raqamini kiriting:")
# #     await state.set_state(DeleteAdmin.waiting_for_tg_id)


# # @router.message(DeleteAdmin.waiting_for_tg_id)
# # async def delete_admin_finish(msg: types.Message, state: FSMContext):
# #     tg_id = msg.text.strip()
# #     conn = db.get_conn()
# #     cur = conn.cursor()
# #     check = cur.execute("SELECT id FROM admins WHERE tg_id=?", (tg_id,)).fetchone()
# #     if not check:
# #         return await msg.answer("❌ Bunday admin topilmadi.")
# #     cur.execute("DELETE FROM admins WHERE tg_id=?", (tg_id,))
# #     conn.commit()
# #     await msg.answer("✅ Admin o‘chirildi.", reply_markup=superadmin_menu())
# #     await state.clear()


# # # --- 📦 Export (Excel) ---
# # @router.message(F.text == "📦 Export (Excel)")
# # async def export_reports(msg: types.Message):
# #     if not is_superadmin(msg.from_user.id):
# #         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
# #     conn = db.get_conn()
# #     df = pd.read_sql_query("SELECT * FROM reports", conn)
# #     if df.empty:
# #         return await msg.answer("📭 Hisobotlar mavjud emas.")
# #     filename = f"hisobot_{datetime.date.today()}.xlsx"
# #     buffer = io.BytesIO()
# #     df.to_excel(buffer, index=False)
# #     buffer.seek(0)
# #     await msg.answer_document(types.input_file.BufferedInputFile(buffer.read(), filename))


# # # --- ⚠️ Muammolar ro‘yxati ---
# # @router.message(F.text == "⚠️ Muammolar ro‘yxati")
# # async def superadmin_problems(msg: types.Message):
# #     cur = db.get_conn().cursor()
# #     problems = cur.execute("""
# #         SELECT f.name, w.name, p.note, p.file_id, p.created_at
# #         FROM problems p
# #         JOIN workers w ON w.id = p.worker_id
# #         JOIN filials f ON f.id = p.filial_id
# #         ORDER BY p.id DESC LIMIT 20
# #     """).fetchall()

# #     if not problems:
# #         return await msg.answer("✅ Hozircha muammo yo‘q.")

# #     for pr in problems:
# #         await msg.answer_photo(
# #             pr[3],
# #             caption=f"🏢 Filial: <b>{pr[0]}</b>\n👷 Ishchi: {pr[1]}\n🕒 {pr[4]}\n\n📝 Izoh: {pr[2]}",
# #             parse_mode="HTML",
# #         )

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

# # --- FSM holatlari uchun klass ---
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


# # --- Faqat SuperAdmin kirishi ---
# def is_superadmin(user_id: int):
#     return user_id == SUPERADMIN_ID


# # --- 🔹 /superadmin yoki menyu orqali ---
# @router.message(Command("superadmin"))
# async def superadmin_panel(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("❌ Siz SuperAdmin emassiz.")
#     await msg.answer("👑 SuperAdmin menyusi:", reply_markup=superadmin_menu())


# # --- 🔹 Filiallar ro‘yxati ---
# @router.message(F.text == "🏢 Filiallar ro‘yxati")
# async def filial_list(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     cur = db.get_conn().cursor()
#     filials = cur.execute("SELECT id, name, filial_id FROM filials").fetchall()
#     if not filials:
#         return await msg.answer("📭 Filiallar mavjud emas.")
#     text = "🏢 <b>Filiallar ro‘yxati:</b>\n\n"
#     for f in filials:
#         text += f"📍 {f[1]} — ID: <code>{f[2]}</code>\n"
#     await msg.answer(text, parse_mode="HTML", reply_markup=superadmin_menu())


# # --- 🔹 Filial qo‘shish ---
# @router.message(F.text == "➕ Filial qo‘shish")
# async def add_filial_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     await msg.answer("✏️ Filial nomini kiriting:", reply_markup=ReplyKeyboardRemove())
#     await state.set_state(AddFilial.waiting_for_name)

# @router.message(AddFilial.waiting_for_name)
# async def ask_filial_id(msg: types.Message, state: FSMContext):
#     name = msg.text.strip()
#     await state.update_data(name=name)
#     await msg.answer("🔢 Endi filial uchun unikal ID kiriting (masalan: ASAKA_001):")
#     await state.set_state(AddFilial.waiting_for_id)

# @router.message(AddFilial.waiting_for_id)
# async def add_filial_finish(msg: types.Message, state: FSMContext):
#     data = await state.get_data()
#     name = data.get("name")
#     filial_id = msg.text.strip().upper()

#     conn = db.get_conn()
#     cur = conn.cursor()

#     check = cur.execute("SELECT id FROM filials WHERE filial_id=?", (filial_id,)).fetchone()
#     if check:
#         return await msg.answer("⚠️ Bu ID allaqachon mavjud. Boshqa ID kiriting.")

#     cur.execute("INSERT INTO filials (name, filial_id) VALUES (?, ?)", (name, filial_id))
#     conn.commit()
#     await msg.answer(f"✅ Filial qo‘shildi:\n<b>{name}</b> (ID: <code>{filial_id}</code>)",
#                      parse_mode="HTML", reply_markup=superadmin_menu())
#     await state.clear()


# # --- 🔹 Filialni o‘chirish ---
# @router.message(F.text == "❌ Filialni o‘chirish")
# async def delete_filial_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
    
#     cur = db.get_conn().cursor()
#     filials = cur.execute("SELECT filial_id, name FROM filials").fetchall()
#     if not filials:
#         return await msg.answer("📭 Filiallar mavjud emas.")
    
#     text = "🗑 O‘chirmoqchi bo‘lgan filial ID sini kiriting:\n\n"
#     for f in filials:
#         text += f"🏢 {f[1]} — <code>{f[0]}</code>\n"
    
#     await msg.answer(text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
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
#     await msg.answer(f"✅ Filial o‘chirildi: <code>{filial_id}</code>", parse_mode="HTML",
#                      reply_markup=superadmin_menu())
#     await state.clear()


# # --- 🔹 Adminlar ro‘yxati ---
# @router.message(F.text == "👥 Adminlar ro‘yxati")
# async def admin_list(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     cur = db.get_conn().cursor()
#     cur.execute("""
#         SELECT a.id, a.name, a.tg_id, f.name 
#         FROM admins a LEFT JOIN filials f ON a.filial_id = f.id
#     """)
#     admins = cur.fetchall()
#     if not admins:
#         return await msg.answer("📭 Adminlar yo‘q.")
#     text = "👥 <b>Adminlar ro‘yxati:</b>\n\n"
#     for a in admins:
#         text += f"🧑 {a[1]} (TG ID: <code>{a[2]}</code>) — 🏢 {a[3]}\n"
#     await msg.answer(text, parse_mode="HTML", reply_markup=superadmin_menu())


# # --- 🔹 Admin qo‘shish ---
# @router.message(F.text == "➕ Admin qo‘shish")
# async def add_admin_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     await msg.answer("🧑 Admin ismini kiriting:", reply_markup=ReplyKeyboardRemove())
#     await state.set_state(AddAdmin.waiting_for_name)

# @router.message(AddAdmin.waiting_for_name)
# async def add_admin_tg_id(msg: types.Message, state: FSMContext):
#     await state.update_data(name=msg.text)
#     await msg.answer("📱 Adminning Telegram ID raqamini kiriting:")
#     await state.set_state(AddAdmin.waiting_for_tg_id)

# @router.message(AddAdmin.waiting_for_tg_id)
# async def add_admin_filial(msg: types.Message, state: FSMContext):
#     await state.update_data(tg_id=msg.text)
#     cur = db.get_conn().cursor()
#     filials = cur.execute("SELECT id, name FROM filials").fetchall()
#     text = "🏢 Filialni tanlang (raqamini kiriting):\n\n"
#     for f in filials:
#         text += f"{f[0]}. {f[1]}\n"
#     await msg.answer(text)
#     await state.set_state(AddAdmin.waiting_for_filial_id)

# @router.message(AddAdmin.waiting_for_filial_id)
# async def add_admin_finish(msg: types.Message, state: FSMContext):
#     data = await state.get_data()
#     try:
#         filial_id = int(msg.text)
#     except ValueError:
#         return await msg.answer("❌ Raqam kiriting.")
#     conn = db.get_conn()
#     conn.execute(
#         "INSERT INTO admins (name, tg_id, filial_id) VALUES (?, ?, ?)",
#         (data['name'], data['tg_id'], filial_id)
#     )
#     conn.commit()
#     await msg.answer("✅ Admin qo‘shildi!", reply_markup=superadmin_menu())
#     await state.clear()


# # --- 🔹 Adminni o‘chirish ---
# @router.message(F.text == "🗑 Adminni o‘chirish")
# async def delete_admin_start(msg: types.Message, state: FSMContext):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     await msg.answer("🆔 O‘chirmoqchi bo‘lgan adminning Telegram ID sini kiriting:")
#     await state.set_state(DeleteAdmin.waiting_for_tg_id)

# @router.message(DeleteAdmin.waiting_for_tg_id)
# async def delete_admin_finish(msg: types.Message, state: FSMContext):
#     conn = db.get_conn()
#     conn.execute("DELETE FROM admins WHERE tg_id=?", (msg.text,))
#     conn.commit()
#     await msg.answer("✅ Admin o‘chirildi.", reply_markup=superadmin_menu())
#     await state.clear()


# # --- 📅 Bugungi hisobotlar ---
# @router.message(F.text == "📅 Bugungi hisobotlar")
# async def today_reports(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")

#     today = datetime.date.today().strftime("%Y-%m-%d")
#     conn = db.get_conn()
#     cur = conn.cursor()

#     reports = cur.execute("""
#         SELECT f.name, w.name, r.text, r.created_at
#         FROM reports r
#         JOIN workers w ON w.id = r.worker_id
#         JOIN filials f ON f.filial_id = r.filial_id
#         WHERE r.created_at LIKE ?
#         ORDER BY r.id DESC
#     """, (f"{today}%",)).fetchall()

#     if not reports:
#         return await msg.answer("📭 Bugun hech qanday hisobot kelmagan.")

#     text = "📅 <b>Bugungi hisobotlar:</b>\n\n"
#     for r in reports:
#         text += f"🏢 {r[0]}\n👷 {r[1]}\n🕒 {r[3]}\n🧾 {r[2]}\n\n"

#     await msg.answer(text, parse_mode="HTML")


# # --- 📊 Umumiy hisobotlar ---
# @router.message(F.text == "📊 Umumiy hisobotlar")
# async def all_reports(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")

#     conn = db.get_conn()
#     cur = conn.cursor()

#     reports = cur.execute("""
#         SELECT f.name, w.name, r.text, r.created_at
#         FROM reports r
#         JOIN workers w ON w.id = r.worker_id
#         JOIN filials f ON f.filial_id = r.filial_id
#         ORDER BY r.id DESC LIMIT 30
#     """).fetchall()

#     if not reports:
#         return await msg.answer("📭 Hisobotlar mavjud emas.")

#     text = "📊 <b>So‘nggi 30 ta hisobot:</b>\n\n"
#     for r in reports:
#         text += f"🏢 {r[0]}\n👷 {r[1]}\n🕒 {r[3]}\n🧾 {r[2]}\n\n"

#     await msg.answer(text, parse_mode="HTML")


# # --- 📦 Export (Excel) ---
# @router.message(F.text == "📦 Export (Excel)")
# async def export_excel(msg: types.Message):
#     if not is_superadmin(msg.from_user.id):
#         return await msg.answer("⛔ Sizda ruxsat yo‘q.")
#     conn = db.get_conn()
#     df = pd.read_sql_query("SELECT * FROM reports", conn)
#     if df.empty:
#         return await msg.answer("📭 Hisobotlar mavjud emas.")
#     now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
#     buffer = io.BytesIO()
#     df.to_excel(buffer, index=False)
#     buffer.seek(0)
#     await msg.answer_document(types.input_file.BufferedInputFile(buffer.read(), f"hisobot_{now}.xlsx"))


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
#             caption=f"🏢 Filial: <b>{pr[0]}</b>\n👷 Ishchi: {pr[1]}\n🕒 {pr[4]}\n📝 Izoh: {pr[2]}",
#             parse_mode="HTML"
#         )

















from aiogram import Router, F, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import aiosqlite
import datetime
from database import db

router = Router()

# === 🔹 Superadmin menyusi ===
def superadmin_menu():
    kb = [
        [KeyboardButton(text="🏢 Filiallar ro‘yxati"), KeyboardButton(text="➕ Filial qo‘shish")],
        [KeyboardButton(text="👥 Adminlar ro‘yxati"), KeyboardButton(text="➕ Admin qo‘shish")],
        [KeyboardButton(text="❌ Adminni o‘chirish"), KeyboardButton(text="📊 Hisobotlar")],
        [KeyboardButton(text="💰 Bonuslar/Jarimalar"), KeyboardButton(text="↩️ Menyuga qaytish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# === 🏢 Filiallar ro‘yxati ===
@router.message(F.text == "🏢 Filiallar ro‘yxati")
async def filial_list(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT id, name FROM filial") as cur:
            rows = await cur.fetchall()
    if not rows:
        return await msg.answer("📭 Hozircha filiallar yo‘q.")
    text = "🏢 <b>Filiallar ro‘yxati:</b>\n" + "\n".join([f"{r[0]}. {r[1]}" for r in rows])
    await msg.answer(text, parse_mode="HTML")

# === ➕ Filial qo‘shish ===
admin_state = {}  # bu fayl boshida bo‘lishi kerak

@router.message(F.text == "➕ Filial qo‘shish")
async def filial_add_start(msg: types.Message):
    admin_state[msg.from_user.id] = "add_filial"
    await msg.answer("🏢 Yangi filial nomini kiriting:", reply_markup=ReplyKeyboardRemove())

@router.message(F.text)
async def filial_add(msg: types.Message):
    uid = msg.from_user.id
    if uid not in admin_state or admin_state[uid] != "add_filial":
        return  # boshqa holatlarda qaytamiz

    filial_name = msg.text.strip()
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("INSERT INTO filial (name) VALUES (?)", (filial_name,))
        await conn.commit()

    admin_state[uid] = None
    await msg.answer(f"✅ Filial '{filial_name}' qo‘shildi.", reply_markup=superadmin_menu())

# === 👥 Adminlar ro‘yxati ===
@router.message(F.text == "👥 Adminlar ro‘yxati")
async def admin_list(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT a.id, a.name, f.name 
            FROM admin a 
            LEFT JOIN filial f ON a.filial_id = f.id
        """) as cur:
            rows = await cur.fetchall()
    if not rows:
        return await msg.answer("📭 Hozircha adminlar yo‘q.")
    text = "👥 <b>Adminlar ro‘yxati:</b>\n"
    for r in rows:
        text += f"🆔 {r[0]} — {r[1]} ({r[2] or 'Filialsiz'})\n"
    await msg.answer(text, parse_mode="HTML")

# === ➕ Admin qo‘shish ===
@router.message(F.text == "➕ Admin qo‘shish")
async def add_admin(msg: types.Message):
    await msg.answer("👤 Admin nomini yuboring:", reply_markup=ReplyKeyboardRemove())
    msg.conf["state"] = "add_admin_name"

@router.message(F.text)
async def process_add_admin(msg: types.Message):
    if msg.conf.get("state") != "add_admin_name":
        return
    name = msg.text.strip()
    msg.conf["temp_name"] = name
    await msg.answer("📱 Endi admin Telegram ID sini yuboring:")
    msg.conf["state"] = "add_admin_id"

@router.message(F.text)
async def save_admin(msg: types.Message):
    if msg.conf.get("state") != "add_admin_id":
        return
    try:
        tg_id = int(msg.text.strip())
    except:
        return await msg.answer("❌ Iltimos, faqat raqam kiriting (Telegram ID).")

    name = msg.conf.get("temp_name")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("INSERT INTO admin (name, tg_id) VALUES (?, ?)", (name, tg_id))
        await conn.commit()

    msg.conf["state"] = None
    msg.conf["temp_name"] = None
    await msg.answer(f"✅ Admin '{name}' ({tg_id}) muvaffaqiyatli qo‘shildi.", reply_markup=superadmin_menu())

# === ❌ Adminni o‘chirish ===
@router.message(F.text == "❌ Adminni o‘chirish")
async def remove_admin_start(msg: types.Message):
    await msg.answer("🆔 O‘chirmoqchi bo‘lgan adminning ID raqamini yuboring:", reply_markup=ReplyKeyboardRemove())
    msg.conf["state"] = "remove_admin"

@router.message(F.text)
async def remove_admin(msg: types.Message):
    if msg.conf.get("state") != "remove_admin":
        return
    try:
        admin_id = int(msg.text.strip())
    except:
        return await msg.answer("❌ ID raqam bo‘lishi kerak.")

    async with aiosqlite.connect(db.DB_PATH) as conn:
        await conn.execute("DELETE FROM admin WHERE id=?", (admin_id,))
        await conn.commit()
    msg.conf["state"] = None
    await msg.answer(f"🗑 Admin ID:{admin_id} o‘chirildi.", reply_markup=superadmin_menu())

# === 💰 Bonuslar/Jarimalar ===
@router.message(F.text == "💰 Bonuslar/Jarimalar")
async def finance_overview(msg: types.Message):
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("SELECT COUNT(*), SUM(amount) FROM bonuses") as cur:
            bcount, bsum = await cur.fetchone()
        async with conn.execute("SELECT COUNT(*), SUM(amount) FROM fines") as cur:
            fcount, fsum = await cur.fetchone()

    text = (
        f"💰 <b>Umumiy bonuslar va jarimalar:</b>\n\n"
        f"🎉 Bonuslar: {bcount or 0} ta — {bsum or 0:,} so‘m\n"
        f"⚠️ Jarimalar: {fcount or 0} ta — {fsum or 0:,} so‘m"
    )
    await msg.answer(text, parse_mode="HTML")

# === 📊 Hisobotlar ===
@router.message(F.text == "📊 Hisobotlar")
async def show_reports(msg: types.Message):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(db.DB_PATH) as conn:
        async with conn.execute("""
            SELECT w.name, r.text, r.created_at 
            FROM reports r
            JOIN workers w ON r.worker_id = w.id
            WHERE DATE(r.created_at)=DATE(?)
            ORDER BY r.id DESC
        """, (today,)) as cur:
            rows = await cur.fetchall()

    if not rows:
        return await msg.answer("📭 Bugun hech qanday hisobot kelmagan.")

    text = f"📅 <b>{today} — bugungi hisobotlar:</b>\n\n"
    for r in rows:
        text += f"👷 <b>{r[0]}</b>\n🕒 {r[2]}\n{r[1]}\n\n"
    await msg.answer(text, parse_mode="HTML")

# === ↩️ Menyuga qaytish ===
@router.message(F.text == "↩️ Menyuga qaytish")
async def back_to_menu(msg: types.Message):
    await msg.answer("🔙 Superadmin menyusi:", reply_markup=superadmin_menu())




