import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# --- Modullar ---
from database import db
from handlers import start, superadmin, admin, worker


# --- .env fayldan sozlamalarni yuklaymiz ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_FILE = os.getenv("DATABASE_FILE", "data.db")
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID", "0"))

# --- Token tekshiruv ---
if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN .env faylida ko‘rsatilmagan. Iltimos, to‘g‘ri token kiriting.")

# --- Logging sozlamalari ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)
logger = logging.getLogger("hisobot24")


# --- Bot va Dispatcher yaratish ---
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def on_startup():
    """
    🔹 Loyihani ishga tayyorlash funksiyasi
    """
    logger.info("🔧 Baza tayyorlanmoqda...")
    await db.init_db(DATABASE_FILE)
    logger.info("✅ Baza tayyor!")
    logger.info("🔗 Routerlar ulanmoqda...")

    dp.include_router(start.router)
    dp.include_router(superadmin.router)
    dp.include_router(admin.router)
    dp.include_router(worker.router)

    logger.info("🤖 HISOBOT24 bot to‘liq tayyor ishlashga!")


async def main():
    """
    🔹 Asosiy ishga tushirish
    """
    await on_startup()
    logger.info("🚀 Bot ishga tushdi! Endi foydalanuvchilarni kutmoqda...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Botda xatolik: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to‘xtatildi.")
