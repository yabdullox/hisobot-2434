import asyncio
import os
import logging
import aiohttp
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

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================== TOKEN TEKSHIRISH ========================
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN topilmadi! Render Environment Variables yoki .env faylni tekshiring.")
else:
    logger.info(f"✅ BOT_TOKEN yuklandi, uzunligi: {len(BOT_TOKEN)} ta belgi.")
# ================================================================


# Bot va Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Routerlarni ulaymiz
dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(worker_h.router)


# 🟢 Startupda bajariladigan ishlar
async def on_startup():
    try:
        init_db()
        logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.error(f"⚠️ Database xatosi: {e}")

    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Botni ishga tushirish"),
            BotCommand(command="help", description="Yordam")
        ])
        me = await bot.get_me()
        logger.info(f"🤖 Bot username: @{me.username}")
    except aiohttp.ClientResponseError as e:
        logger.error(f"❌ Telegram server javobi: {e.message}")
    except Exception as e:
        logger.error(f"❌ Xatolik yuz berdi: {e}")


# 🔁 Polling funksiyasi
async def run_polling():
    try:
        await on_startup()
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"⚠️ Pollingda xatolik: {e}")
    finally:
        await bot.session.close()


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

    logger.info(f"🌍 Fake web server run on port {port}")


# 🚀 Tokenni to‘g‘riligini test qilish
async def test_token():
    """Telegram API orqali token to‘g‘riligini tekshiradi"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN mavjud emas, tekshiruv o‘tkazilmadi.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data.get("ok"):
                    logger.info(f"✅ Telegram token to‘g‘ri. Bot: @{data['result']['username']}")
                    return True
                else:
                    logger.error(f"❌ Telegram javobi: {data}")
                    return False
    except Exception as e:
        logger.error(f"⚠️ Token testida xatolik: {e}")
        return False


# 🚀 Bosh ishga tushirish
async def main():
    # Tokenni avval tekshirib olaylik
    valid = await test_token()
    if not valid:
        logger.error("❌ BOT_TOKEN noto‘g‘ri yoki Telegram API rad etdi. Iltimos, BotFather’dan yangi token oling.")
        return

    try:
        await asyncio.gather(
            fake_web_server(),
            run_polling()
        )
    except Exception as e:
        logger.error(f"⚠️ Asosiy jarayonda xatolik: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
