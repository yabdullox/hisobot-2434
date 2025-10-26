# main.py  — Render Web Service bilan moslashtirilgan
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

# HTTP server uchun aiohttp
from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_FILE = os.getenv("DATABASE_FILE", "data.db")
# Render ushbu $PORT muhit o'zgaruvchisini beradi (yoki 8000 default)
PORT = int(os.getenv("PORT", 8000))

if not BOT_TOKEN:
    raise RuntimeError("❌ Iltimos, .env faylga BOT_TOKEN ni yozing.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hisobot24")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def start_web_server(port: int):
    async def handle_root(request):
        return web.Response(text="HISOBOT24 bot — Running")

    async def handle_health(request):
        return web.Response(text="OK")

    app = web.Application()
    app.add_routes([web.get("/", handle_root), web.get("/health", handle_health)])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 HTTP server started on 0.0.0.0:{port}")


async def main():
    # DB init
    db.init_db(DATABASE_FILE)
    logger.info("✅ Baza muvaffaqiyatli ishga tayyor.")

    # Routerni ulash
    dp.include_router(start.router)
    dp.include_router(superadmin.router)
    dp.include_router(admin.router)
    dp.include_router(worker.router)

    # HTTP serverni ishga tushiramiz (fon process)
    await start_web_server(PORT)

    # Bot polling - bu funksiyani bloklovchi, u ishlayotganda web server ham ishlaydi
    logger.info("🤖 HISOBOT24 bot ishga tushdi! (polling)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to‘xtatildi.")
