import aiosqlite
import os

DB_PATH = os.getenv("DATABASE_FILE", "data.db")

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
            filial_id INTEGER,
            text TEXT,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            file_id TEXT,
            note TEXT,
            created_at TEXT
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            note TEXT,
            file_id TEXT,
            created_at TEXT
        )""")

        await db.commit()
    print("✅ Database initialized successfully!")

# Qo‘shimcha qulay funksiyalar
async def add_bonus(tg_id, reason, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO bonuses (worker_id, filial_id, reason, amount, created_at)
        VALUES ((SELECT id FROM workers WHERE tg_id=?),
                (SELECT filial_id FROM workers WHERE tg_id=?),
                ?, ?, datetime('now'))
        """, (tg_id, tg_id, reason, amount))
        await db.commit()

async def add_fine(tg_id, reason, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO fines (worker_id, filial_id, reason, amount, created_at)
        VALUES ((SELECT id FROM workers WHERE tg_id=?),
                (SELECT filial_id FROM workers WHERE tg_id=?),
                ?, ?, datetime('now'))
        """, (tg_id, tg_id, reason, amount))
        await db.commit()

async def add_report(tg_id, text, created_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO reports (worker_id, filial_id, text, created_at)
        VALUES ((SELECT id FROM workers WHERE tg_id=?),
                (SELECT filial_id FROM workers WHERE tg_id=?),
                ?, ?)
        """, (tg_id, tg_id, text, created_at))
        await db.commit()

async def add_photo(tg_id, file_id, note):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO photos (worker_id, filial_id, file_id, note, created_at)
        VALUES ((SELECT id FROM workers WHERE tg_id=?),
                (SELECT filial_id FROM workers WHERE tg_id=?),
                ?, ?, datetime('now'))
        """, (tg_id, tg_id, file_id, note))
        await db.commit()

async def add_problem(tg_id, file_id, note):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO problems (worker_id, filial_id, note, file_id, created_at)
        VALUES ((SELECT id FROM workers WHERE tg_id=?),
                (SELECT filial_id FROM workers WHERE tg_id=?),
                ?, ?, datetime('now'))
        """, (tg_id, tg_id, note, file_id))
        await db.commit()
