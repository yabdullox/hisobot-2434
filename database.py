import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# .env fayldan sozlamalarni yuklaymiz
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# PostgreSQL ulanish
engine: Engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


# ===============================
# 🔹 Baza bilan bog‘lanishni test qiladi
# ===============================
def init_db():
    """Baza bilan bog‘lanishni test qiladi va kerakli jadvallarni yaratadi."""
    try:
        with engine.begin() as conn:
            # Oddiy test
            conn.execute(text("SELECT 1"))

            # NOTES jadvali
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS notes (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT NOT NULL,
                    text TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # ADMIN ↔ BRANCH jadvali
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS admin_branches (
                    id SERIAL PRIMARY KEY,
                    admin_id BIGINT NOT NULL,
                    branch_id INTEGER NOT NULL,
                    UNIQUE (admin_id, branch_id)
                )
            """))

        logging.info("✅ Database connected and verified successfully.")
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")


# ===============================
# 🔹 Ma’lumot olish — bitta natija
# ===============================
def fetchone(query: str, params: dict = None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            row = result.mappings().fetchone()
            return dict(row) if row else None
    except Exception as e:
        logging.error(f"⚠️ fetchone error: {e}")
        return None


# ===============================
# 🔹 Ma’lumot olish — ko‘p natija
# ===============================
def fetchall(query: str, params: dict = None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = result.mappings().fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"⚠️ fetchall error: {e}")
        return []


# ===============================
# 🔹 Ma’lumot qo‘shish / o‘chirish / yangilash
# ===============================
def execute(query: str, params: dict = None):
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
    except Exception as e:
        logging.error(f"⚠️ execute error: {e}")


# ===============================
# 🔹 ID yoki qaytuvchi qiymat olish uchun
# ===============================
def execute_returning(query: str, params: dict = None):
    try:
        with engine.begin() as conn:
            result = conn.execute(text(query), params or {})
            row = result.mappings().fetchone()
            return dict(row) if row else None
    except Exception as e:
        logging.error(f"⚠️ execute_returning error: {e}")
        return None


# ===============================
# 🔹 Adminni filialga bog‘lash (maks. 5 ta limit)
# ===============================
def add_admin_to_branch(admin_id: int, branch_id: int):
    """Adminni filialga qo‘shadi (maksimal 5 ta)."""
    count = fetchone(
        "SELECT COUNT(*) AS c FROM admin_branches WHERE admin_id=:a",
        {"a": admin_id}
    )
    if count and count["c"] >= 5:
        raise Exception("❌ Bu admin allaqachon 5 ta filialga biriktirilgan.")

    execute("""
        INSERT INTO admin_branches (admin_id, branch_id)
        VALUES (:a, :b)
        ON CONFLICT (admin_id, branch_id) DO NOTHING
    """, {"a": admin_id, "b": branch_id})


# ===============================
# 🔹 Adminning filiallari ro‘yxatini olish
# ===============================
def get_admin_branches(admin_id: int):
    """Admin qaysi filiallarga biriktirilganini qaytaradi."""
    return fetchall("""
        SELECT b.id, b.name
        FROM admin_branches ab
        JOIN branches b ON ab.branch_id = b.id
        WHERE ab.admin_id = :aid
    """, {"aid": admin_id})


# ===============================
# 🔹 Notes jadvalini yaratish (alohida chaqirish mumkin)
# ===============================
def create_notes_table():
    query = """
    CREATE TABLE IF NOT EXISTS notes (
        id BIGSERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        text TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """
    execute(query)
    logging.info("✅ Notes table checked or created successfully.")


# ===============================
# 🔹 Barcha jadvallarni ishga tushirish
# ===============================
if __name__ == "__main__":
    init_db()
    create_notes_table()
    print("✅ Database and tables initialized successfully.")
