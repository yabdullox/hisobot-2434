import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID", "0"))
DB_PATH = "data.db"

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN topilmadi! .env faylni tekshiring.")
