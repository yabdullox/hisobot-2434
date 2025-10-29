import os
import sqlite3
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///hisobot24.db")

# is_postgres = DATABASE_URL.startswith("postgres")

# # =========================
# # 🔌 Ulanish funksiyasi
# # =========================
# def get_connection():
#     if is_postgres:
#         return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=psycopg2.extras.RealDictCursor)
#     else:
#         path = DATABASE_URL.replace("sqlite:///", "")
#         conn = sqlite3.connect(path)
#         conn.row_factory = sqlite3.Row
#         return conn


# # =========================
# # 💾 Execute (INSERT, UPDATE, DELETE)
# # =========================
# def execute(query: str, params: dict = None):
#     conn = get_connection()
#     cur = conn.cursor()
#     try:
#         if is_postgres:
#             # PostgreSQL uchun parametrlarni %s formatga o‘zgartiramiz
#             if params:
#                 q = query
#                 for key in params.keys():
#                     q = q.replace(f":{key}", "%s")
#                 cur.execute(q, tuple(params.values()))
#             else:
#                 cur.execute(query)
#         else:
#             cur.execute(query, params or {})

#         conn.commit()
#     finally:
#         cur.close()
#         conn.close()


# # =========================
# # 🔍 fetchone (1 ta natija)
# # =========================
# def fetchone(query: str, params: dict = None):
#     conn = get_connection()
#     cur = conn.cursor()
#     try:
#         if is_postgres:
#             q = query
#             if params:
#                 for key in params.keys():
#                     q = q.replace(f":{key}", "%s")
#                 cur.execute(q, tuple(params.values()))
#             else:
#                 cur.execute(query)
#         else:
#             cur.execute(query, params or {})

#         result = cur.fetchone()
#         return dict(result) if result else None
#     finally:
#         cur.close()
#         conn.close()


# # =========================
# # 📋 fetchall (ko‘p natija)
# # =========================
# def fetchall(query: str, params: dict = None):
#     conn = get_connection()
#     cur = conn.cursor()
#     try:
#         if is_postgres:
#             q = query
#             if params:
#                 for key in params.keys():
#                     q = q.replace(f":{key}", "%s")
#                 cur.execute(q, tuple(params.values()))
#             else:
#                 cur.execute(query)
#         else:
#             cur.execute(query, params or {})

#         result = cur.fetchall()
#         return [dict(r) for r in result]
#     finally:
#         cur.close()
#         conn.close()


# # =========================
# # 🧱 init_db (faqat SQLite uchun)
# # =========================
# def init_db():
#     if not is_postgres:
#         conn = get_connection()
#         cur = conn.cursor()
#         cur.executescript("""
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             telegram_id BIGINT UNIQUE,
#             full_name TEXT,
#             role TEXT,
#             branch_id INTEGER
#         );

#         CREATE TABLE IF NOT EXISTS reports (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id BIGINT,
#             date DATE,
#             start_time TEXT,
#             end_time TEXT
#         );

#         CREATE TABLE IF NOT EXISTS bonuses (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id BIGINT,
#             branch_id INTEGER,
#             amount INTEGER,
#             reason TEXT,
#             created_by BIGINT,
#             auto BOOLEAN DEFAULT FALSE,
#             date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );

#         CREATE TABLE IF NOT EXISTS fines (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id BIGINT,
#             branch_id INTEGER,
#             amount INTEGER,
#             reason TEXT,
#             created_by BIGINT,
#             auto BOOLEAN DEFAULT FALSE,
#             date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );

#         CREATE TABLE IF NOT EXISTS cleaning_photos (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id BIGINT,
#             report_id INTEGER,
#             file_id TEXT
#         );

#         CREATE TABLE IF NOT EXISTS problems (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             user_id BIGINT,
#             text TEXT,
#             has_photo BOOLEAN,
#             date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );

#         CREATE TABLE IF NOT EXISTS notes (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             telegram_id BIGINT,
#             content TEXT,
#             date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );
#         """)
#         conn.commit()
#         cur.close()
#         conn.close()
import psycopg2
from psycopg2.extras import RealDictCursor
import os

# ============================
# 🔧 Postgres ulanishi
# ============================

DB_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
cursor = conn.cursor()


# ============================
# 🧱 Bazani yaratish
# ============================

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT UNIQUE NOT NULL,
        full_name TEXT,
        role TEXT DEFAULT 'worker',
        branch_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        note TEXT,
        start_time TEXT,
        end_time TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cleaning_photos (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        report_id INTEGER,
        file_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bonuses (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        branch_id INTEGER,
        amount INTEGER NOT NULL,
        reason TEXT,
        created_by BIGINT,
        auto BOOLEAN DEFAULT FALSE,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fines (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        branch_id INTEGER,
        amount INTEGER NOT NULL,
        reason TEXT,
        created_by BIGINT,
        auto BOOLEAN DEFAULT FALSE,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()


# ============================
# 🔹 Universal funksiyalar
# ============================

def execute(query, params=None):
    """INSERT/UPDATE/DELETE uchun"""
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    cursor.close()


def fetchone(query, params=None):
    """Bitta natija olish uchun"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, params or ())
    result = cursor.fetchone()
    cursor.close()
    return result


def fetchall(query, params=None):
    """Bir nechta natijalarni olish uchun"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query, params or ())
    result = cursor.fetchall()
    cursor.close()
    return result


# ============================
# 💾 Hisobot (report) funksiyasi
# ============================

def add_report(telegram_id, date, note):
    """Bugungi hisobotni qo‘shish"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (telegram_id, date, note)
        VALUES (%s, %s, %s)
    """, (telegram_id, date, note))
    conn.commit()
    cursor.close()


# ============================
# 💬 Eslatma funksiyasi
# ============================

def add_note(user_id, content):
    """Ishchi o‘ziga eslatma yozadi"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notes (user_id, content)
        VALUES (%s, %s)
    """, (user_id, content))
    conn.commit()
    cursor.close()


def get_notes(user_id):
    """Ishchining barcha eslatmalarini olish"""
    return fetchall("SELECT * FROM notes WHERE user_id=%s ORDER BY created_at DESC", (user_id,))


# ============================
# ✅ Foydalanuvchi tekshirish
# ============================

def get_user(telegram_id):
    """Foydalanuvchini topish"""
    return fetchone("SELECT * FROM users WHERE telegram_id=%s", (telegram_id,))


def add_user(telegram_id, full_name, role="worker", branch_id=None):
    """Yangi foydalanuvchi qo‘shish"""
    execute("""
        INSERT INTO users (telegram_id, full_name, role, branch_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (telegram_id) DO NOTHING
    """, (telegram_id, full_name, role, branch_id))


# ============================
# 🚀 Startda bazani yaratish
# ============================

init_db()
print("✅ DATABASE tayyor — jadval va funksiyalar ishga tushdi.")
