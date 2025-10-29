import os
from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()

# 🔑 Telegram bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🧩 Database URL (Render PostgreSQL uchun)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")

# 👑 Superadminlar (vergul bilan ajratilgan ID lar)
# Masalan: SUPERADMINS=8020655627,123456789
SUPERADMINS = [int(x) for x in os.getenv("SUPERADMINS", "").split(",") if x.strip()]

# 👨‍💼 Filial adminlar (ixtiyoriy, shunday formatda)
# Masalan: ADMINS=7404485920,987654321
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip()]

# Eski kodlar bilan moslik uchun
SUPERADMIN_ID = SUPERADMINS[0] if SUPERADMINS else None
