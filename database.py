import os
import sqlite3
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")

is_postgres = DATABASE_URL.startswith("postgres")

# =========================
# 🔌 Ulanish funksiyasi
# =========================
def get_connection():
    if is_postgres:
        return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=psycopg2.extras.RealDictCursor)
    else:
        path = DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn


# =========================
# 💾 Execute (INSERT, UPDATE, DELETE)
# =========================
def execute(query: str, params: dict = None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if is_postgres:
            # PostgreSQL uchun parametrlarni %s formatga o‘zgartiramiz
            if params:
                q = query
                for key in params.keys():
                    q = q.replace(f":{key}", "%s")
                cur.execute(q, tuple(params.values()))
            else:
                cur.execute(query)
        else:
            cur.execute(query, params or {})

        conn.commit()
    finally:
        cur.close()
        conn.close()


# =========================
# 🔍 fetchone (1 ta natija)
# =========================
def fetchone(query: str, params: dict = None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if is_postgres:
            q = query
            if params:
                for key in params.keys():
                    q = q.replace(f":{key}", "%s")
                cur.execute(q, tuple(params.values()))
            else:
                cur.execute(query)
        else:
            cur.execute(query, params or {})

        result = cur.fetchone()
        return dict(result) if result else None
    finally:
        cur.close()
        conn.close()


# =========================
# 📋 fetchall (ko‘p natija)
# =========================
def fetchall(query: str, params: dict = None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if is_postgres:
            q = query
            if params:
                for key in params.keys():
                    q = q.replace(f":{key}", "%s")
                cur.execute(q, tuple(params.values()))
            else:
                cur.execute(query)
        else:
            cur.execute(query, params or {})

        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()


# =========================
# 🧱 init_db (faqat SQLite uchun)
# =========================
def init_db():
    if not is_postgres:
        conn = get_connection()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE,
            full_name TEXT,
            role TEXT,
            branch_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT,
            date DATE,
            start_time TEXT,
            end_time TEXT
        );

        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT,
            branch_id INTEGER,
            amount INTEGER,
            reason TEXT,
            created_by BIGINT,
            auto BOOLEAN DEFAULT FALSE,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT,
            branch_id INTEGER,
            amount INTEGER,
            reason TEXT,
            created_by BIGINT,
            auto BOOLEAN DEFAULT FALSE,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cleaning_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT,
            report_id INTEGER,
            file_id TEXT
        );

        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT,
            text TEXT,
            has_photo BOOLEAN,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT,
            content TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        cur.close()
        conn.close()
