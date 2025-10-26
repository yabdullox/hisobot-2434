import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database import db
from handlers import start, superadmin, admin, worker

# 🔹 .env fayldan sozlamalarni yuklaymiz
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_FILE = os.getenv("DATABASE_FILE", "data.db")

if not BOT_TOKEN:
    raise RuntimeError("❌ Iltimos, .env faylga BOT_TOKEN ni yozing.")

# 🔹 Logging sozlamalari (chiroyli chiqish uchun)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hisobot24")

# 🔹 Bot va Dispatcher yaratamiz
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    """
    HISOBOT24 botni ishga tushirish funksiyasi.
    """
    # 🔹 Baza yaratish yoki tayyorlash
    db.init_db(DATABASE_FILE)
    logger.info("✅ Baza muvaffaqiyatli ishga tayyor.")

    # 🔹 Routerlarni ulash
    dp.include_router(start.router)
    dp.include_router(superadmin.router)
    dp.include_router(admin.router)
    dp.include_router(worker.router)

    # 🔹 Botni ishga tushirish
    logger.info("🤖 HISOBOT24 bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to‘xtatildi.")
