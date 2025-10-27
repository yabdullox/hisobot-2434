# # main.py — Render Web Service uchun moslashtirilgan

# import asyncio
# import logging
# import os
# from aiogram import Bot, Dispatcher
# from aiogram.client.default import DefaultBotProperties
# from aiogram.enums import ParseMode
# from aiogram.fsm.storage.memory import MemoryStorage
# from dotenv import load_dotenv
# from aiohttp import web
# from database import db
# from handlers import start, superadmin, admin, worker


# # === 🔹 Muhit o‘zgaruvchilarni yuklaymiz ===
# load_dotenv()

# BOT_TOKEN = os.getenv("BOT_TOKEN")
# DATABASE_FILE = os.getenv("DATABASE_FILE", "data.db")
# PORT = int(os.getenv("PORT", 8000))  # Render uchun majburiy

# if not BOT_TOKEN:
#     raise RuntimeError("❌ Iltimos, .env faylga BOT_TOKEN ni yozing.")


# # === 🔹 Logging sozlamalari ===
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger("hisobot24")


# # === 🔹 Bot va Dispatcher ===
# bot = Bot(
#     token=BOT_TOKEN,
#     default=DefaultBotProperties(parse_mode=ParseMode.HTML)
# )
# storage = MemoryStorage()
# dp = Dispatcher(storage=storage)


# # === 🔹 HTTP (web) server ===
# async def start_web_server(port: int):
#     async def handle_root(request):
#         return web.Response(text="HISOBOT24 bot — Running ✅")

#     async def handle_health(request):
#         return web.Response(text="OK")

#     app = web.Application()
#     app.add_routes([
#         web.get("/", handle_root),
#         web.get("/health", handle_health)
#     ])

#     runner = web.AppRunner(app)
#     await runner.setup()
#     site = web.TCPSite(runner, "0.0.0.0", port)
#     await site.start()
#     logger.info(f"🌐 HTTP server started on 0.0.0.0:{port}")


# # === 🔹 Asosiy ishga tushirish funksiyasi ===
# async def main():
#     # 1️⃣ Baza ishga tayyorlash
#     await db.init_db(DATABASE_FILE)
#     logger.info("✅ Baza muvaffaqiyatli ishga tayyor.")

#     # 2️⃣ Routerlarni ulaymiz
#     dp.include_router(start.router)
#     dp.include_router(superadmin.router)
#     dp.include_router(admin.router)
#     dp.include_router(worker.router)
#     logger.info("🔗 Routerlar muvaffaqiyatli ulandi.")

#     # 3️⃣ HTTP serverni fon rejimda ishga tushiramiz
#     asyncio.create_task(start_web_server(PORT))

#     # 4️⃣ Bot pollingni ishga tushiramiz
#     logger.info("🤖 HISOBOT24 bot ishga tushdi! (polling)")
#     await dp.start_polling(bot)


# # === 🔹 Dastur ishga tushishi ===
# if __name__ == "__main__":
#     try:
#         asyncio.run(main())
#     except (KeyboardInterrupt, SystemExit):
#         logger.info("🛑 Bot to‘xtatildi.")
# main.py — Render Web Service uchun to‘liq moslashtirilgan

# main.py — Render Web Service uchun yakuniy, to‘liq ishlaydigan versiya
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiohttp import web
from database import db
from handlers import start, superadmin, admin, worker

# === 🔹 Muhit o‘zgaruvchilarni yuklaymiz ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))  # Render uchun majburiy

if not BOT_TOKEN:
    raise RuntimeError("❌ Iltimos, .env faylga BOT_TOKEN ni yozing.")

# === 🔹 Logging sozlamalari ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("hisobot24")

# === 🔹 Bot va Dispatcher ===
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# === 🔹 HTTP (web) server ===
async def start_web_server(port: int):
    async def handle_root(request):
        return web.Response(text="🤖 HISOBOT24 bot — Running ✅")

    async def handle_health(request):
        return web.Response(text="OK")

    app = web.Application()
    app.add_routes([
        web.get("/", handle_root),
        web.get("/health", handle_health)
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 HTTP server started on port {port}")

# === 🔹 Asosiy ishga tushirish funksiyasi ===
async def main():
    # 1️⃣ Baza ishga tayyorlash
    await db.init_db()  # ✅ argument BERILMAYDI
    logger.info("✅ Baza muvaffaqiyatli ishga tayyor.")

    # 2️⃣ Routerlarni ulaymiz
    dp.include_router(start.router)
    dp.include_router(superadmin.router)
    dp.include_router(admin.router)
    dp.include_router(worker.router)
    logger.info("🔗 Routerlar muvaffaqiyatli ulandi.")

    # 3️⃣ HTTP serverni fon rejimda ishga tushiramiz
    asyncio.create_task(start_web_server(PORT))

    # 4️⃣ Bot pollingni ishga tushiramiz
    logger.info("🤖 HISOBOT24 bot ishga tushdi (polling).")
    await dp.start_polling(bot)

# === 🔹 Dastur ishga tushishi ===
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Bot to‘xtatildi.")




