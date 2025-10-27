# import os
# import sqlite3
# import shutil
# import aiosqlite

# DB_PATH = "data.db"

# # --- Baza buzilgan bo‘lsa, tiklash ---
# def safe_repair_db(file_name: str):
#     try:
#         conn = sqlite3.connect(file_name)
#         conn.execute("SELECT 1;")
#         conn.close()
#     except sqlite3.DatabaseError:
#         print("⚠️ Baza buzilgan! Tiklanmoqda...")
#         if os.path.exists(file_name):
#             shutil.move(file_name, file_name + ".broken")
#         conn = sqlite3.connect(file_name)
#         conn.close()
#         print("✅ Yangi toza baza yaratildi.")


# # --- Asinxron bazani yaratish (barcha jadvallar bilan) ---
# async def init_db(filename="data.db"):
#     global DB_PATH
#     DB_PATH = filename
#     safe_repair_db(filename)

#     async with aiosqlite.connect(filename) as db:
#         # --- Filiallar
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS filials (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT,
#             filial_id TEXT UNIQUE
#         )
#         """)

#         # --- Adminlar
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS admins (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT,
#             tg_id TEXT UNIQUE,
#             filial_id INTEGER,
#             FOREIGN KEY(filial_id) REFERENCES filials(id)
#         )
#         """)

#         # --- Ishchilar
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS workers (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             name TEXT,
#             tg_id TEXT UNIQUE,
#             filial_id INTEGER,
#             FOREIGN KEY(filial_id) REFERENCES filials(id)
#         )
#         """)

#         # --- Hisobotlar
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS reports (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             worker_id INTEGER,
#             filial_id INTEGER,
#             text TEXT,
#             created_at TEXT DEFAULT (datetime('now', 'localtime')),
#             FOREIGN KEY(worker_id) REFERENCES workers(id)
#         )
#         """)

#         # --- Bonuslar
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS bonuses (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             worker_id INTEGER,
#             filial_id INTEGER,
#             reason TEXT,
#             amount INTEGER,
#             created_at TEXT DEFAULT (datetime('now', 'localtime')),
#             FOREIGN KEY(worker_id) REFERENCES workers(id)
#         )
#         """)

#         # --- Jarimalar
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS fines (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             worker_id INTEGER,
#             filial_id INTEGER,
#             reason TEXT,
#             amount INTEGER,
#             created_at TEXT DEFAULT (datetime('now', 'localtime')),
#             FOREIGN KEY(worker_id) REFERENCES workers(id)
#         )
#         """)

#         # --- Muammolar (rasm bilan)
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS problems (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             worker_id INTEGER,
#             filial_id INTEGER,
#             note TEXT,
#             file_id TEXT,
#             status TEXT DEFAULT 'Yangi',
#             created_at TEXT DEFAULT (datetime('now', 'localtime')),
#             FOREIGN KEY(worker_id) REFERENCES workers(id)
#         )
#         """)

#         # --- Ish boshlash loglari
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS work_start_log (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             worker_id INTEGER,
#             filial_id INTEGER,
#             start_time TEXT
#         )
#         """)

#         # --- Ishchilar mahsulotlari (📦 Mahsulotlarim)
#         await db.execute("""
#         CREATE TABLE IF NOT EXISTS worker_products (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             worker_id INTEGER,
#             product_name TEXT,
#             created_at TEXT DEFAULT (datetime('now', 'localtime')),
#             FOREIGN KEY(worker_id) REFERENCES workers(id)
#         )
#         """)

#         await db.commit()
#         print("✅ Baza muvaffaqiyatli yaratildi va ishga tayyor!")


# # --- Sinxron ulanish (handlerlar uchun kerak bo‘lishi mumkin) ---
# def get_conn():
#     return sqlite3.connect(DB_PATH)import os

import aiosqlite
import os

DB_PATH = os.getenv("DATABASE_FILE", "data.db")

async def init_db(db_path=DB_PATH):
    async with aiosqlite.connect(db_path) as db:
        # Ishchilar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                tg_id INTEGER UNIQUE,
                filial_id INTEGER
            )
        """)

        # Hisobotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                text TEXT,
                created_at TEXT
            )
        """)

        # Bonuslar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                reason TEXT,
                amount INTEGER,
                created_at TEXT
            )
        """)

        # Jarimalar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                reason TEXT,
                amount INTEGER,
                created_at TEXT
            )
        """)

        # Mahsulotlar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                name TEXT
            )
        """)

        # Muammolar jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                worker_id INTEGER,
                filial_id INTEGER,
                photo_id TEXT,
                note TEXT,
                status TEXT,
                created_at TEXT
            )
        """)

        await db.commit()


# 🔹 Yordamchi funksiyalar (soddalashtirilgan foydalanish uchun)
async def execute(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, params)
        await db.commit()

async def fetchone(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        row = await cur.fetchone()
        return row

async def fetchall(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        return rows



