import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import load_dotenv
from aiohttp import web

# === Fayllar va konfiguratsiya ===
from database import init_db
from handlers import start as start_h, superadmin as superadmin_h, admin as admin_h, worker as worker_h

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(worker_h.router)


async def check_conflict():
    """Agar boshqa instansiya ishlayotgan bo‘lsa aniqlaydi."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                # agar Telegram polling allaqachon ishlayotgan bo‘lsa
                if "error_code" in data and data["error_code"] == 409:
                    logging.warning("❌ Conflict: Boshqa instansiya ishlayapti.")
                    return True
        except Exception as e:
            logging.error(f"⚠️ getUpdates tekshiruvda xato: {e}")
    return False


async def on_startup():
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish")
    ])
    logging.info("✅ Bot va baza tayyor.")


async def fake_web_server():
    """Render uchun port ochish."""
    async def handle(request):
        return web.Response(text="✅ Hisobot24 bot ishlayapti!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"🌐 Fake web server run on port {port}")


async def run_polling():
    """Polling faqat bitta nusxada ishga tushadi."""
    conflict = await check_conflict()
    if conflict:
        logging.warning("🚫 Polling boshlanmadi, boshqa instance ishlayapti.")
        return

    await on_startup()
    await dp.start_polling(bot)


async def main():
    await asyncio.gather(
        fake_web_server(),
        run_polling()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot to‘xtatildi.")
