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


def init_db():
    """Baza bilan bog‘lanishni test qiladi."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("✅ Database connection successful.")
    except Exception as e:
        logging.error(f"❌ Database connection failed: {e}")


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
