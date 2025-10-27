import aiosqlite

DB_PATH = "data.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            tg_id INTEGER UNIQUE,
            filial_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            text TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            note TEXT,
            file_id TEXT,
            created_at TEXT
        );
        """)
        await db.commit()
