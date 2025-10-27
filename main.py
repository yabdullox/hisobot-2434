import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from dotenv import load_dotenv

from database import db
from handlers import start, worker, admin, superadmin

# === Muhit o‘zgaruvchilarni yuklash ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not BOT_TOKEN:
    raise RuntimeError("❌ .env faylda BOT_TOKEN yo‘q")

# === Loglar ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Hisobot24")

# === Bot va Dispatcher ===
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# === HTTP server ===
async def start_web_server(port: int):
    async def health(request):
        return web.Response(text="🤖 HISOBOT24 ishlayapti ✅")

    app = web.Application()
    app.add_routes([web.get("/", health)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 HTTP server started on {port}")

# === Asosiy funksiya ===
async def main():
    await db.init_db()

    dp.include_router(start.router)
    dp.include_router(worker.router)
    dp.include_router(admin.router)
    dp.include_router(superadmin.router)

    asyncio.create_task(start_web_server(PORT))
    logger.info("🤖 Bot ishga tushdi!")

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to‘xtatildi.")
