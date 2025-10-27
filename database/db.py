# src/database/db.py
import aiosqlite
import os

# 🔹 Baza fayli yo‘li (Render yoki lokalda)
DB_PATH = os.getenv("DATABASE_FILE", "data.db")

async def init_db(db_path: str = DB_PATH):
    """Bazani yaratish va jadvallarni tekshirish (agar bo‘lmasa)"""
    async with aiosqlite.connect(db_path) as db:
        # --- Ishchilar jadvali ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tg_id INTEGER UNIQUE,
            filial_id INTEGER
        )
        """)

        # --- Hisobotlar ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            text TEXT,
            created_at TEXT
        )
        """)

        # --- Bonuslar ---
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

        # --- Jarimalar ---
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

        # --- Tozalash rasmlari ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            file_id TEXT,
            note TEXT,
            created_at TEXT
        )
        """)

        # --- Muammolar ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            note TEXT,
            file_id TEXT,
            status TEXT,
            created_at TEXT
        )
        """)

        # --- Mahsulotlar ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            name TEXT,
            created_at TEXT
        )
        """)

        # --- Mahsulot savdosi ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS product_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            worker_id INTEGER,
            quantity TEXT,
            created_at TEXT
        )
        """)

        # --- Ish boshlanish logi ---
        await db.execute("""
        CREATE TABLE IF NOT EXISTS work_start_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            start_time TEXT
        )
        """)

        await db.commit()

    print("✅ Database initialized successfully!")
