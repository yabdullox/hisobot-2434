import os
import asyncio
import logging
import aiohttp
from aiohttp import web
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

# === LOKAL FAYLLAR ===
from database import init_db
from handlers import start as start_h, superadmin as superadmin_h, admin as admin_h
import handlers.admin_branch_link as admin_branch_link_h
from handlers import worker as worker_h  # ✅ faqat bitta import

# === ENV SOZLAMALAR ===
load_dotenv()
database.ensure_reports_columns()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === AIROGRAM OBYEKTLAR ===
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")  # ✅ yangi, xavfsiz usul
)
dp = Dispatcher()

# === ROUTERLARNI ULASH ===
dp.include_router(start_h.router)
dp.include_router(superadmin_h.router)
dp.include_router(admin_h.router)
dp.include_router(admin_branch_link_h.router)
dp.include_router(worker_h.router)

# === POLLING KONFLIKTINI TEKSHIRISH ===
async def check_conflict():
    """Agar boshqa instansiya ishlayotgan bo‘lsa aniqlaydi."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                data = await resp.json()
                if "error_code" in data and data["error_code"] == 409:
                    logging.warning("❌ Conflict: Boshqa instansiya ishlayapti.")
                    return True
        except Exception as e:
            logging.error(f"⚠️ getUpdates tekshiruvda xato: {e}")
    return False

# === ON STARTUP ===
async def on_startup():
    """Bot ishga tushganda baza va komandalarni tayyorlash."""
    init_db()
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="help", description="Yordam / Ma'lumot")
    ])
    logging.info("✅ Bot va baza tayyor.")

# === FAKE WEB SERVER (Render uchun port ochish) ===
async def fake_web_server():
    """Render server doimiy ishda bo‘lishi uchun port ochish."""
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

# === POLLING ISHGA TUSHURISH ===
async def run_polling():
    """Polling faqat bitta nusxada ishga tushadi."""
    conflict = await check_conflict()
    if conflict:
        logging.warning("🚫 Polling boshlanmadi, boshqa instance ishlayapti.")
        return

    await on_startup()
    await dp.start_polling(bot)

# === ASOSIY LOOP ===
async def main():
    """Render uchun parallel web server va pollingni ishga tushiradi."""
    await asyncio.gather(
        fake_web_server(),
        run_polling()
    )

# === ENTRY POINT ===
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Bot to‘xtatildi.")
