import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database import db
from handlers import start, worker, admin, superadmin

# --- .env fayldan sozlamalarni yuklaymiz ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_FILE = os.getenv("DATABASE_FILE", "data.db")

if not BOT_TOKEN:
    raise RuntimeError("❌ Iltimos, .env faylga BOT_TOKEN ni yozing.")

# --- Loglar sozlamasi ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("hisobot24")

# --- Bot va dispatcher yaratish ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    """
    🔹 Asosiy ishga tushirish funksiyasi
    """
    logger.info("🔧 Baza tayyorlanmoqda...")
    await db.init_db(DATABASE_FILE)
    logger.info("✅ Baza ishga tayyor!")

    # --- Routerlarni ulash ---
    dp.include_router(start.router)
    dp.include_router(worker.router)
    dp.include_router(admin.router)
    dp.include_router(superadmin.router)

    # --- Ishga tushirish ---
    logger.info("🤖 HISOBOT24 bot ishga tushdi!")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Xatolik yuz berdi: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to‘xtatildi.")
