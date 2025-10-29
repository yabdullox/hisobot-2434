from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database

router = Router()


# ===== FSM holatlar =====
class AdminBranchLink(StatesGroup):
    choosing_admin = State()
    choosing_branches = State()


# ===== 1. Boshlanish: Adminni tanlash =====
@router.message(F.text == "🏢➕ Adminni filialga biriktirish")
async def start_link_process(message: types.Message, state: FSMContext):
    admins = database.fetchall("SELECT id, full_name FROM users WHERE role='admin'")
    if not admins:
        await message.answer("⚠️ Hech qanday admin topilmadi.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=admin["full_name"], callback_data=f"select_admin:{admin['id']}")]
            for admin in admins
        ]
    )

    await message.answer("👥 Qaysi adminni filial(lar)ga biriktirmoqchisiz?", reply_markup=keyboard)
    await state.set_state(AdminBranchLink.choosing_admin)


# ===== 2. Filiallarni tanlash =====
@router.callback_query(AdminBranchLink.choosing_admin, F.data.startswith("select_admin:"))
async def select_admin(callback: types.CallbackQuery, state: FSMContext):
    admin_id = int(callback.data.split(":")[1])
    await state.update_data(admin_id=admin_id)

    branches = database.fetchall("SELECT id, name FROM branches")
    if not branches:
        await callback.message.edit_text("⚠️ Filiallar mavjud emas.")
        return

    keyboard = [
        [InlineKeyboardButton(text=f"🏢 {b['name']}", callback_data=f"branch_toggle:{b['id']}")] for b in branches
    ]
    keyboard.append([InlineKeyboardButton(text="✅ Saqlash", callback_data="save_branches")])
    keyboard.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_link")])

    await callback.message.edit_text(
        "🏢 Filiallarni tanlang (5 tagacha). So‘ng ‘✅ Saqlash’ni bosing:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.update_data(selected_branches=[])
    await state.set_state(AdminBranchLink.choosing_branches)


# ===== 3. Filiallarni tanlash — toggle qilish =====
@router.callback_query(AdminBranchLink.choosing_branches, F.data.startswith("branch_toggle:"))
async def toggle_branch(callback: types.CallbackQuery, state: FSMContext):
    branch_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    selected = data.get("selected_branches", [])

    if branch_id in selected:
        selected.remove(branch_id)
    else:
        if len(selected) >= 5:
            await callback.answer("⚠️ 5 tadan ortiq filial tanlash mumkin emas.", show_alert=True)
            return
        selected.append(branch_id)

    await state.update_data(selected_branches=selected)
    await callback.answer("✅ Tanlov yangilandi.")


# ===== 4. Saqlash =====
@router.callback_query(AdminBranchLink.choosing_branches, F.data == "save_branches")
async def save_branches(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    admin_id = data.get("admin_id")
    selected = data.get("selected_branches", [])

    if not selected:
        await callback.answer("⚠️ Hech narsa tanlanmadi.", show_alert=True)
        return

    database.execute("DELETE FROM admin_branches WHERE admin_id=:a", {"a": admin_id})

    for bid in selected:
        database.execute("INSERT INTO admin_branches (admin_id, branch_id) VALUES (:a, :b)", {"a": admin_id, "b": bid})

    await callback.message.edit_text(f"✅ Admin {len(selected)} ta filialga biriktirildi!")
    await state.clear()


# ===== 5. Bekor qilish =====
@router.callback_query(AdminBranchLink.choosing_branches, F.data == "cancel_link")
async def cancel_link(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Biriktirish bekor qilindi.")
    await state.clear()
