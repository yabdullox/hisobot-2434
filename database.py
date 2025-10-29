import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# ==========================
# 🔌 Ulanuvchi funksiyalar
# ==========================
def get_connection():
    if IS_SQLITE:
        path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# ==========================
# 🧱 Barcha jadvallarni yaratish
# ==========================
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 👤 Foydalanuvchilar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            full_name TEXT,
            role TEXT,
            branch_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 📋 Ish hisobotlari
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            date DATE NOT NULL,
            start_time TEXT,
            end_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 💰 Bonuslar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonuses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT,
            created_by BIGINT,
            auto BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ❌ Jarimalar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT,
            created_by BIGINT,
            auto BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 🧹 Tozalash rasmlari
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaning_photos (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            report_id BIGINT,
            file_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ⚠️ Muammolar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS problems (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 🗒️ Eslatmalar
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully (PostgreSQL/SQLite auto).")


# ==========================
# 🔁 Umumiy CRUD funksiyalar
# ==========================
def execute(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()

    if IS_SQLITE:
        cursor.execute(query, params or {})
    else:
        cursor.execute(query, params or {})

    conn.commit()
    conn.close()


def fetchone(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()

    if IS_SQLITE:
        cursor.execute(query, params or {})
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    else:
        cursor.execute(query, params or {})
        result = cursor.fetchone()
        conn.close()
        return result


def fetchall(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()

    if IS_SQLITE:
        cursor.execute(query, params or {})
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    else:
        cursor.execute(query, params or {})
        rows = cursor.fetchall()
        conn.close()
        return rows
