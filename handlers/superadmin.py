from telegram import Update
from telegram.ext import ContextTypes
from keyboards.superadmin_kb import superadmin_menu
from config import SUPERADMIN_ID
from database import db
import pandas as pd
import io

# SuperAdmin menyu tugmalariga ishlovchi funksiya
async def handle_superadmin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # SuperAdmin tekshiruvi
    if user_id != SUPERADMIN_ID:
        await update.message.reply_text("⛔️ Sizda bu bo‘limga kirish huquqi yo‘q.")
        return

    # 🏢 Filiallar ro‘yxati
    if text == "🏢 Filiallar ro‘yxati":
        branches = await db.fetchall("SELECT id, name FROM branches")
        if branches:
            msg = "🏢 Filiallar ro‘yxati:\n\n" + "\n".join([f"{b[0]}. {b[1]}" for b in branches])
        else:
            msg = "📭 Hozircha filial mavjud emas."
        await update.message.reply_text(msg, reply_markup=superadmin_menu())

    # ➕ Filial qo‘shish
    elif text == "➕ Filial qo‘shish":
        await update.message.reply_text("Yangi filial nomini kiriting:")
        context.user_data["adding_branch"] = True

    elif context.user_data.get("adding_branch"):
        name = text.strip()
        await db.execute("INSERT INTO branches (name) VALUES (?)", (name,))
        await update.message.reply_text(f"✅ Filial '{name}' qo‘shildi.", reply_markup=superadmin_menu())
        context.user_data.pop("adding_branch", None)

    # 👥 Adminlar ro‘yxati
    elif text == "👥 Adminlar ro‘yxati":
        admins = await db.fetchall("SELECT tg_id, full_name FROM admins")
        if admins:
            msg = "👥 Adminlar ro‘yxati:\n\n" + "\n".join([f"{a[1]} ({a[0]})" for a in admins])
        else:
            msg = "📭 Hozircha adminlar yo‘q."
        await update.message.reply_text(msg, reply_markup=superadmin_menu())

    # ➕ Admin qo‘shish
    elif text == "➕ Admin qo‘shish":
        await update.message.reply_text("Iltimos, yangi adminning Telegram ID raqamini yuboring:")
        context.user_data["adding_admin"] = True

    elif context.user_data.get("adding_admin"):
        try:
            tg_id = int(text)
            await db.execute("INSERT INTO admins (tg_id, full_name) VALUES (?, ?)", (tg_id, f"Admin {tg_id}"))
            await update.message.reply_text("✅ Admin muvaffaqiyatli qo‘shildi.", reply_markup=superadmin_menu())
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        context.user_data.pop("adding_admin", None)

    # ❌ Adminni o‘chirish
    elif text == "❌ Adminni o‘chirish":
        await update.message.reply_text("O‘chiriladigan adminning Telegram ID raqamini yuboring:")
        context.user_data["deleting_admin"] = True

    elif context.user_data.get("deleting_admin"):
        try:
            tg_id = int(text)
            await db.execute("DELETE FROM admins WHERE tg_id = ?", (tg_id,))
            await update.message.reply_text("🗑️ Admin muvaffaqiyatli o‘chirildi.", reply_markup=superadmin_menu())
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        context.user_data.pop("deleting_admin", None)

    # 📊 Hisobotlar
    elif text == "📊 Hisobotlar":
        reports = await db.fetchall("SELECT * FROM reports")
        if not reports:
            await update.message.reply_text("📭 Hisobotlar mavjud emas.", reply_markup=superadmin_menu())
            return

        msg = "📊 Oxirgi 5 ta hisobot:\n\n"
        for r in reports[-5:]:
            msg += f"🧑 {r[1]} | {r[2]} | {r[3]}\n"
        await update.message.reply_text(msg, reply_markup=superadmin_menu())

    # 📦 Export (Excel)
    elif text == "📦 Export (Excel)":
        data = await db.fetchall("SELECT * FROM reports")
        if not data:
            await update.message.reply_text("📭 Export uchun ma’lumot yo‘q.", reply_markup=superadmin_menu())
            return

        df = pd.DataFrame(data, columns=["id", "name", "report", "date"])
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)

        await update.message.reply_document(document=buffer, filename="hisobotlar.xlsx")
        await update.message.reply_text("✅ Excel fayl jo‘natildi.", reply_markup=superadmin_menu())

    # ⚠️ Muammolar ro‘yxati
    elif text == "⚠️ Muammolar ro‘yxati":
        problems = await db.fetchall("SELECT * FROM problems")
        if not problems:
            await update.message.reply_text("📭 Muammolar mavjud emas.", reply_markup=superadmin_menu())
            return

        msg = "⚠️ Muammolar ro‘yxati:\n\n"
        for p in problems:
            msg += f"🧍 {p[1]} | 📅 {p[2]} | 📝 {p[3]}\n"
        await update.message.reply_text(msg, reply_markup=superadmin_menu())

    # 🔙 Orqaga
    elif text == "🔙 Orqaga":
        await update.message.reply_text("🔙 Bosh menyuga qaytdingiz.", reply_markup=superadmin_menu())

    else:
        await update.message.reply_text("❓ Noma’lum buyruq. Iltimos, menyudan tanlang.", reply_markup=superadmin_menu())
