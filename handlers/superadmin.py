from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp, db  # db = database modulida sqlite uchun
from keyboards.superadmin_menu import superadmin_menu

# 🔹 State – admin qo‘shish bosqichlari
class AddAdminState(StatesGroup):
    waiting_for_name = State()
    waiting_for_tg_id = State()

# 🔹 1-qadam: Tugma bosilganda
@dp.message_handler(text="➕ Admin qo‘shish")
async def add_admin_start(message: types.Message):
    await message.answer("👤 Yangi adminning to‘liq ismini kiriting:")
    await AddAdminState.waiting_for_name.set()

# 🔹 2-qadam: Ismni qabul qilish
@dp.message_handler(state=AddAdminState.waiting_for_name)
async def add_admin_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📱 Endi yangi adminning Telegram ID raqamini yuboring:")
    await AddAdminState.waiting_for_tg_id.set()

# 🔹 3-qadam: ID ni qabul qilish va bazaga yozish
@dp.message_handler(state=AddAdminState.waiting_for_tg_id)
async def add_admin_tg_id(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    tg_id = message.text

    try:
        # 🔸 Bazaga yozish (sqlite uchun misol)
        await db.execute(
            "INSERT INTO admins (full_name, tg_id) VALUES (?, ?)",
            (name, tg_id)
        )
        await message.answer(
            f"✅ Admin muvaffaqiyatli qo‘shildi!\n\n👤 Ism: {name}\n🆔 ID: {tg_id}",
            reply_markup=superadmin_menu()
        )
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

    await state.finish()
