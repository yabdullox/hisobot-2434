from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import DATABASE_URL

# ⚙️ PostgreSQL ulanish
# SQLite emas, endi PostgreSQL ishlatiladi
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)


def execute(query: str, params: dict = None):
    """INSERT / UPDATE / DELETE uchun yordamchi (commit bilan)."""
    with engine.begin() as conn:
        conn.execute(text(query), params or {})


def fetchall(query: str, params: dict = None):
    """Ko‘p qatorli SELECT — list[dict] qaytaradi."""
    with engine.connect() as conn:
        res = conn.execute(text(query), params or {})
        return [dict(r._mapping) for r in res.fetchall()]


def fetchone(query: str, params: dict = None):
    """Bitta qator SELECT — dict yoki None qaytaradi."""
    with engine.connect() as conn:
        res = conn.execute(text(query), params or {})
        row = res.fetchone()
        return dict(row._mapping) if row else None


def init_db():
    """PostgreSQL uchun jadvallarni yaratish."""
    stmts = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE,
            full_name TEXT,
            role TEXT NOT NULL,
            branch_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS branches (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            branch_id INTEGER,
            date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            text TEXT,
            cleaning_photo_id TEXT,
            problem_photo_id TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS problems (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            branch_id INTEGER,
            report_id INTEGER,
            description TEXT,
            photo_file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS cleaning_photos (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            branch_id INTEGER,
            report_id INTEGER,
            file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS fines (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            branch_id INTEGER,
            amount NUMERIC(12,2) NOT NULL,
            reason TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            auto BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS bonuses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            branch_id INTEGER,
            amount NUMERIC(12,2) NOT NULL,
            reason TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            auto BOOLEAN DEFAULT FALSE
        )
        """
    ]

    try:
        with engine.begin() as conn:
            for s in stmts:
                conn.execute(text(s))
            conn.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_user_date ON reports(user_id, date)")
            )
        print("✅ PostgreSQL Database initialized successfully.")
    except SQLAlchemyError as e:
        print("❌ Database initialization error:", e)
