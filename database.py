import sqlite3

DB_PATH = "hisobot24.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Barcha jadvallarni yaratadi"""
    conn = get_connection()
    cursor = conn.cursor()

    # 👥 Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE,
            full_name TEXT,
            role TEXT,
            branch_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 📋 Ish hisobotlari jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            date DATE NOT NULL,
            start_time TEXT,
            end_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 💰 Bonuslar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            branch_id INTEGER,
            amount INTEGER NOT NULL,
            reason TEXT,
            created_by BIGINT,
            auto BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ❌ Jarimalar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            branch_id INTEGER,
            amount INTEGER NOT NULL,
            reason TEXT,
            created_by BIGINT,
            auto BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 🧹 Tozalash rasmlari jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaning_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            report_id BIGINT,
            file_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 🗒️ Eslatmalar jadvali (ishchi yozgan eslatmalar o‘zida saqlanadi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully (SQLite).")


def execute(query, params=None):
    """INSERT, UPDATE, DELETE"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or {})
    conn.commit()
    conn.close()


def fetchone(query, params=None):
    """Bitta natijani olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or {})
    result = cursor.fetchone()
    conn.close()
    return result


def fetchall(query, params=None):
    """Bir nechta natijani olish"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or {})
    result = cursor.fetchall()
    conn.close()
    return result
