# main.py
import asyncio
import logging
import os
from typing import Callable

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# config.py ichida BOT_TOKEN, SUPERADMIN_ID, DATABASE_URL va boshqalar bo'lishi kerak
from config import BOT_TOKEN

# Lokal database util
import database

# handlers routerlarini import qilamiz (har biri `router = Router()` bo'lishi kerak)
# Agar handler fayllarida modul nomlari boshqacha bo'lsa shu joyni moslashtir
from handlers import start as start_h
from handlers import superadmin as superadmin_h
from handlers import admin as admin_h
from handlers import worker as worker_h

# ixtiyoriy: scheduler modul (agar mavjud bo'lsa)
try:
    import scheduler as scheduler_mod
except Exception:
    scheduler_mod = None

# logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("HISOBOT24")


async def _maybe_start_scheduler(bot: Bot):
    """
    Agar projectda `scheduler.start_scheduler` mavjud bo'lsa chaqirishga harakat qiladi.
    Funksiya bot argumentini kutishi yoki kutmasligi mumkin — ikkala holatni qoplaymiz.
    """
    if not scheduler_mod:
        logger.info("Scheduler modul topilmadi — o'tkazib yuborilyapti.")
        return

    start_fn = getattr(scheduler_mod, "start_scheduler", None)
    if not start_fn or not isinstance(start_fn, Callable):
        logger.info("scheduler.start_scheduler topilmadi yoki callable emas.")
        return

    try:
        # Avval botni argument bilan chaqirib ko'ramiz (agar u qabul qilsa)
        logger.info("Schedulerni bot bilan ishga tushurishga harakat qilinmoqda...")
        maybe = start_fn(bot)
        # Agar start_fn sync bo'lsa va natija coroutine bo'lsa await qilamiz
        if asyncio.iscoroutine(maybe):
            await maybe
        logger.info("Scheduler ishga tushirildi (bot argument bilan).")
        return
    except TypeError:
        # Funksiya bot argumentini qabul qilmaydi — argumentsiz chaqiramiz
        try:
            logger.info("Schedulerni argumentsiz ishga tushurishga harakat qilinmoqda...")
            maybe = start_fn()
            if asyncio.iscoroutine(maybe):
                await maybe
            logger.info("Scheduler ishga tushirildi (argumentsiz).")
            return
        except Exception as e:
            logger.exception("Schedulerni ishga tushirishda xato (argumentsiz): %s", e)
            return
    except Exception as e:
        logger.exception("Schedulerni ishga tushirishda xato: %s", e)
        return


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi. .env yoki config.py ni tekshiring.")
        return

    # Database jadvallarini yaratish / init
    try:
        database.init_db()
    except Exception as e:
        logger.exception("Database initda xato: %s", e)
        # Agar init xato bersa ham davom ettirmoqchi bo'lsangiz, pass qilishingiz mumkin.
        # return

    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Routerlarni ro'yxatdan o'tkazamiz
    try:
        dp.include_router(start_h.router)
    except Exception as e:
        logger.exception("start routerni qo'shishda xato: %s", e)

    try:
        dp.include_router(superadmin_h.router)
    except Exception as e:
        logger.exception("superadmin routerni qo'shishda xato: %s", e)

    try:
        dp.include_router(admin_h.router)
    except Exception as e:
        logger.exception("admin routerni qo'shishda xato: %s", e)

    try:
        dp.include_router(worker_h.router)
    except Exception as e:
        logger.exception("worker routerni qo'shishda xato: %s", e)

    # Agar boshqa universal routerlar bor bo'lsa shu yerda qo'sh

    # Scheduler (agar bo'lsa) ishga tushuramiz
    try:
        await _maybe_start_scheduler(bot)
    except Exception as e:
        logger.exception("Schedulerni ishga tushirishda umumiy xato: %s", e)

    # Pollingni boshlash
    try:
        logger.info("🚀 HISOBOT24 BOT ishga tushmoqda (polling)...")
        await dp.start_polling(bot)
    finally:
        # Shutdown
        try:
            await bot.session.close()
        except Exception:
            pass
        await storage.close()
        logger.info("Bot to'xtadi, storage yopildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Dastur to'xtatildi.")
    except Exception as e:
        logger.exception("main.run da xato: %s", e)
