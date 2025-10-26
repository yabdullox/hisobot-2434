import os
import shutil
import sqlite3
import aiosqlite

DB_PATH = "data.db"


def safe_repair_db(file_name: str):
    """Agar baza buzilgan bo‘lsa, uni tiklashga urinish"""
    try:
        conn = sqlite3.connect(file_name)
        conn.execute("SELECT 1;")
        conn.close()
    except sqlite3.DatabaseError:
        print("⚠️ Baza buzilgan, tiklanmoqda...")
        if os.path.exists(file_name):
            shutil.move(file_name, file_name + ".broken")
        conn = sqlite3.connect(file_name)
        conn.close()
        print("✅ Yangi toza baza yaratildi.")


async def init_db(filename="data.db"):
    """Baza jadvallarini yaratadi"""
    global DB_PATH
    DB_PATH = filename
    safe_repair_db(filename)

    async with aiosqlite.connect(filename) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS filials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            filial_id TEXT UNIQUE
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tg_id TEXT UNIQUE,
            filial_id INTEGER,
            FOREIGN KEY(filial_id) REFERENCES filials(id)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tg_id TEXT UNIQUE,
            filial_id INTEGER,
            FOREIGN KEY(filial_id) REFERENCES filials(id)
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            text TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY(worker_id) REFERENCES workers(id)
        )""")

        await db.commit()
        print("✅ Baza tayyor!")


def get_conn():
    """Sync ulanish (kerak joylar uchun)"""
    return sqlite3.connect(DB_PATH)


async def aget_conn():
    """Async ulanish"""
    return await aiosqlite.connect(DB_PATH)
