import os
from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()

# 🔑 Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🧩 Database URL (PostgreSQL uchun)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")

# 👑 Superadmin ID (faqat bitta)
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID", "0"))

