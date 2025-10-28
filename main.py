# main.py
import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv
from aiohttp import web

# Fayllarni import qilamiz
from database import init_db
from handlers import start as start_h, superadmin as superadmin_h, admin as admin_h, worker as worker_h

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Handlers ro‘yxati
dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(worker_h.router)


async def on_startup():
    init_db()
    logging.info("✅ Database initialized successfully.")
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish")
    ])


async def run_polling():
    """Asosiy polling jarayoni."""
    await on_startup()
    await dp.start_polling(bot)


async def fake_web_server():
    """Render uchun “port ochildi” deb ko‘rsatadigan soxta web server."""
    async def handle(request):
        return web.Response(text="✅ Hisobot24 bot ishlayapti!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))  # Render portni shu o‘zi beradi
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 Fake web server run on port {port}")


async def main():
    """Polling va soxta web serverni parallel ishga tushiramiz."""
    await asyncio.gather(
        fake_web_server(),  # Render uchun port ochish
        run_polling()       # Telegram uchun polling
    )


if __name__ == "__main__":
    asyncio.run(main())
