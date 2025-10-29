import os
from dotenv import load_dotenv

# .env faylni yuklash (lokalda)
load_dotenv()

# 🧠 Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN topilmadi! Render Environment Variables yoki .env faylni tekshiring.")

# 💾 Database URL (PostgreSQL yoki lokal SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")

# 👑 SuperAdmin ID
# .env dan SUPERADMIN_ID ni o‘qish (bir nechta ID bo‘lishi mumkin)
SUPERADMIN_ID = [s.strip() for s in os.getenv("SUPERADMIN_ID", "").split(",") if s.strip()]


# 👨‍💼 Filial Admin ID (qo‘shimcha)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
