import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tg_id INTEGER UNIQUE,
            filial_id INTEGER
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            text TEXT,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            file_id TEXT,
            note TEXT,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        )""")

        await db.commit()
