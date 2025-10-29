from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import DATABASE_URL


# Single engine for the app
engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)


def execute(query: str, params: dict | None = None):
    """Run INSERT/UPDATE/DELETE — commits automatically."""
    with engine.begin() as conn:
        conn.execute(text(query), params or {})


def execute_returning(query: str, params: dict | None = None):
    """Run INSERT ... RETURNING and return first column of first row if any."""
    with engine.begin() as conn:
        res = conn.execute(text(query), params or {})
        row = res.fetchone()
        return row[0] if row else None


def fetchall(query: str, params: dict | None = None):
    """Return list[dict] for SELECT queries."""
    with engine.connect() as conn:
        res = conn.execute(text(query), params or {})
        return [dict(r._mapping) for r in res.fetchall()]


def fetchone(query: str, params: dict | None = None):
    """Return single row as dict or None."""
    with engine.connect() as conn:
        res = conn.execute(text(query), params or {})
        row = res.fetchone()
        return dict(row._mapping) if row else None


def init_db():
    """Create tables if missing and apply lightweight migrations.

    Uses textual SQL and named parameters so it fits the rest of the code.
    """
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
            user_id BIGINT NOT NULL,
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
            user_id BIGINT NOT NULL,
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
            user_id BIGINT NOT NULL,
            branch_id INTEGER,
            report_id INTEGER,
            file_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS fines (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            branch_id INTEGER,
            amount REAL NOT NULL,
            reason TEXT,
            created_by BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            auto INTEGER DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS bonuses (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            branch_id INTEGER,
            amount REAL NOT NULL,
            reason TEXT,
            created_by BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            auto INTEGER DEFAULT 0
        )
        """,
    ]

    try:
        with engine.begin() as conn:
            for s in stmts:
                conn.execute(text(s))

            # unique index to avoid duplicate reports per day
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_user_date ON reports(user_id, date)"))

            # Attempt to coerce types for older DBs (safe: errors are ignored)
            fix_types = [
                "ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT USING telegram_id::bigint",
                "ALTER TABLE reports ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint",
                "ALTER TABLE fines ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint",
                "ALTER TABLE fines ALTER COLUMN created_by TYPE BIGINT USING created_by::bigint",
                "ALTER TABLE bonuses ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint",
                "ALTER TABLE bonuses ALTER COLUMN created_by TYPE BIGINT USING created_by::bigint",
            ]
            for fix in fix_types:
                try:
                    conn.execute(text(fix))
                except Exception:
                    pass

            # Ensure problems table has expected columns (safe no-op if present)
            schema_patches = [
                "ALTER TABLE problems ADD COLUMN IF NOT EXISTS branch_id INTEGER",
                "ALTER TABLE problems ADD COLUMN IF NOT EXISTS report_id INTEGER",
                "ALTER TABLE problems ADD COLUMN IF NOT EXISTS description TEXT",
                "ALTER TABLE problems ADD COLUMN IF NOT EXISTS photo_file_id TEXT",
            ]
            for patch in schema_patches:
                try:
                    conn.execute(text(patch))
                except Exception:
                    pass

        print("✅ Database initialized successfully.")
    except SQLAlchemyError as e:
        print("❌ Database initialization error:", e)


if __name__ == "__main__":
    init_db()
