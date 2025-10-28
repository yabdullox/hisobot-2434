# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from config import BOT_TOKEN
import database

# handlers (sizning papkangizdagi fayllar)
import handlers.start as start_h
import handlers.superadmin as superadmin_h
import handlers.admin as admin_h
import handlers.worker as worker_h

# Logging sozlamalari
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HISOBOT24")

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Routerlarni ulash
dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(worker_h.router)


async def start_services():
    """
    Dastlabki xizmatlar (masalan, database yoki scheduler) ishga tushiriladi.
    """
    try:
        database.init_db()
        logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.exception("❌ Database initialization error: %s", e)


async def main():
    """
    Asosiy bot jarayoni.
    """
    await start_services()

    # Eski webhookni o‘chirib tashlaymiz — polling uchun shart!
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔧 Old webhook o‘chirildi (polling uchun tayyor).")
    except Exception as e:
        logger.warning(f"⚠️ Webhookni o‘chirib bo‘lmadi: {e}")

    # Asosiy polling loop
    while True:
        try:
            logger.info("🚀 Bot ishga tushmoqda (polling)...")
            await dp.start_polling(bot)
            break  # normal tugasa, chiqamiz
        except TelegramNetworkError as e:
            logger.warning(f"⚠️ TelegramNetworkError: {e} — 10s keyin qayta urinish.")
            await asyncio.sleep(10)
        except Exception as e:
            logger.exception(f"❌ Noma’lum xato: {e} — 5s keyin qayta urinish.")
            await asyncio.sleep(5)
        finally:
            # Sessiyani tozalash
            try:
                await bot.session.close()
            except Exception:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🚪 Bot to‘xtatildi (KeyboardInterrupt).")
    finally:
        pass
