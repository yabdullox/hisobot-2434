import os
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# .env fayldan ma’lumotlarni yuklaymiz
load_dotenv()

# 🔹 Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔹 Superadmin ID (faqat boshqaruv uchun)
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID", 0))

# 🔹 Ma’lumotlar bazasi
DB_PATH = os.getenv("DATABASE_FILE", "data.db")

# 🔹 Aiogram sozlamalari
default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)

# 🔹 Konsolga foydali chiqish
print("✅ CONFIG yuklandi:")
print(f"🤖 BOT_TOKEN: {BOT_TOKEN[:10]}...")  # xavfsizlik uchun faqat bir qismi
print(f"👑 SUPERADMIN_ID: {SUPERADMIN_ID}")
print(f"💾 DATABASE_FILE: {DB_PATH}")
