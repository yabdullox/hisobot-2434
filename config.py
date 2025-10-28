import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPERADMIN_ID = os.getenv("SUPERADMIN_ID")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")
