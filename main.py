import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiohttp import web
from dotenv import load_dotenv

# Ichki fayllar
from config import BOT_TOKEN
from database import init_db
from handlers import start as start_h, superadmin as superadmin_h, admin as admin_h, worker as worker_h

# ENV yuklash
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Routerlarni qo‘shish
dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(worker_h.router)


# 🟢 Startupda bajariladigan ishlar
async def on_startup():
    init_db()
    logging.info("✅ Database initialized successfully.")

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="help", description="Yordam")
    ])

    me = await bot.get_me()
    logging.info(f"🤖 Bot username: @{me.username}")


# 🔁 Polling funksiyasi
async def run_polling():
    await on_startup()
    await dp.start_polling(bot)


# 🌐 Render uchun “fake” web server
async def fake_web_server():
    async def handle(request):
        return web.Response(text="✅ Hisobot24 bot ishlayapti!")

    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logging.info(f"🌍 Fake web server run on port {port}")


# 🚀 Bosh ishga tushirish
async def main():
    try:
        await asyncio.gather(
            fake_web_server(),
            run_polling()
        )
    except Exception as e:
        logging.error(f"⚠️ Xatolik yuz berdi: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
