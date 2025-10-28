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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HISOBOT24")

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Routerlarni ulang
dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(worker_h.router)

async def start_services():
    """
    DB va boshqa boshlang'ich xizmatlar (scheduler va hokazo) shu yerga qo'yilsin.
    """
    # DB ni init qilish (agar sizning database.py da bunday funksiya bo'lsa)
    try:
        database.init_db()
        logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.exception("❌ Database initialization error: %s", e)
        # agar DB fail bo'lsa ham davom etish yoki to'xtatish sizga bog'liq;
        # hozir davom ettiramiz, lekin ehtiyot bo'ling.
    # Agar sizda scheduler yoki boshqa background joblar bo'lsa, shu yerda ishga tushiring.

async def main():
    await start_services()

    while True:
        try:
            logger.info("🚀 Bot ishga tushmoqda... (polling)")
            # start_polling qaytguncha bloklaydi — agar exception bo'lsa, except ga tushadi
            await dp.start_polling(bot)
            # agar dp.start_polling normal tugasa (masalan stop), chiqamiz
            break
        except TelegramNetworkError as e:
            logger.warning("⚠️ TelegramNetworkError: %s — 10s keyin qayta urinish.", e)
            await asyncio.sleep(10)
        except Exception as e:
            logger.exception("❌ Kutilmagan xato: %s — 5s keyin qayta urinish.", e)
            await asyncio.sleep(5)
        finally:
            # har safar qayta urinayotganda eski bot sessiyasini tozalab qo'yish foydali:
            try:
                await bot.session.close()
            except Exception:
                pass
async def main():
    while True:
        try:
            print("🚀 Bot ishlayapti...")
            await dp.start_polling(bot)
        except TelegramNetworkError as e:
            logging.warning(f"⚠️ Telegram tarmoq xatosi: {e}. 10 soniyadan so‘ng qayta ulanadi.")
            await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"❌ Noma’lum xato: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🚪 Bot to'xtatildi (KeyboardInterrupt).")
    finally:
        # qo'shimcha tozalash talab qilinsa shu yerga qo'shing
        pass
