import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# .env fayldan sozlamalarni yuklaymiz
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL env faylda ko‘rsatilmagan!")

# PostgreSQL ulanish
engine: Engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# ===============================
# 🔹 BAZANI TAYYORLASH
# ===============================
def init_db():
    """Barcha kerakli jadvallarni yaratadi (agar mavjud bo‘lmasa)."""
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))

            # Filiallar
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS branches (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
            """))

            # Foydalanuvchilar
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                full_name VARCHAR(255),
                role VARCHAR(50),
                branch_id INT REFERENCES branches(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))

            # Ombor (mahsulotlar)
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS warehouse (
                id SERIAL PRIMARY KEY,
                branch_id INT REFERENCES branches(id),
                product_name VARCHAR(255) NOT NULL,
                quantity NUMERIC DEFAULT 0,
                unit VARCHAR(20),
                price NUMERIC DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))

            # Sotilgan mahsulotlar
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sold_products (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id),
                branch_id INT REFERENCES branches(id),
                product_id INT REFERENCES warehouse(id),
                amount NUMERIC,
                unit VARCHAR(20),
                price NUMERIC,
                sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))

            # Hisobotlar
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(telegram_id),
                branch_id INT REFERENCES branches(id),
                date DATE,
                income NUMERIC,
                expense NUMERIC,
                remaining NUMERIC,
                sold_items TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))

            # Admin ↔ Filial bog‘lanmasi
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS admin_branches (
                id SERIAL PRIMARY KEY,
                admin_id BIGINT NOT NULL,
                branch_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (admin_id, branch_id)
            );
            """))

            # Eslatmalar (notes)
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notes (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            """))

        logging.info("✅ Database connected and all tables initialized successfully.")

    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")

# ===============================
# 🔹 ODDIY SQL FUNKSIYALAR
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


def fetchall(query: str, params: dict = None):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            rows = result.mappings().fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"⚠️ fetchall error: {e}")
        return []


def execute(query: str, params: dict = None):
    try:
        with engine.begin() as conn:
            conn.execute(text(query), params or {})
    except Exception as e:
        logging.error(f"⚠️ execute error: {e}")


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
# 🔹 ADMIN ↔ FILIAL FUNKSIYALARI
# ===============================
def add_admin_to_branch(admin_id: int, branch_id: int):
    count = fetchone("SELECT COUNT(*) AS c FROM admin_branches WHERE admin_id=:a", {"a": admin_id})
    if count and count["c"] >= 5:
        raise Exception("❌ Bu admin allaqachon 5 ta filialga biriktirilgan.")

    execute("""
        INSERT INTO admin_branches (admin_id, branch_id)
        VALUES (:a, :b)
        ON CONFLICT (admin_id, branch_id) DO NOTHING
    """, {"a": admin_id, "b": branch_id})


def get_admin_branches(admin_id: int):
    return fetchall("""
        SELECT b.id, b.name
        FROM admin_branches ab
        JOIN branches b ON ab.branch_id = b.id
        WHERE ab.admin_id = :aid
    """, {"aid": admin_id})

# ===============================
# 🔹 OMBOR FUNKSIYALARI
# ===============================
def add_product_to_warehouse(branch_id: int, product_name: str, quantity, unit: str = "dona", price: int = 0):
    """Omborga yangi mahsulot qo‘shadi."""
    try:
        execute("""
            INSERT INTO warehouse (branch_id, product_name, quantity, unit, price)
            VALUES (:br, :pn, :q, :u, :p)
        """, {"br": branch_id, "pn": product_name, "q": quantity, "u": unit, "p": price})
        return True
    except Exception as e:
        logging.error(f"⚠️ add_product_to_warehouse error: {e}")
        return False


def remove_product_from_warehouse(product_id: int):
    """Ombordan mahsulotni o‘chiradi."""
    try:
        execute("DELETE FROM warehouse WHERE id=:id", {"id": product_id})
        return True
    except Exception as e:
        logging.error(f"⚠️ remove_product_from_warehouse error: {e}")
        return False


def list_products_by_branch(branch_id: int):
    """Filial omboridagi barcha mahsulotlarni chiqaradi."""
    try:
        return fetchall("""
            SELECT id, product_name, quantity, unit, price
            FROM warehouse
            WHERE branch_id=:b
            ORDER BY id
        """, {"b": branch_id})
    except Exception as e:
        logging.error(f"⚠️ list_products_by_branch error: {e}")
        return []


def get_product(product_id: int):
    """Bitta mahsulot ma’lumotini olish."""
    try:
        return fetchone("""
            SELECT id, product_name, quantity, unit, price, branch_id
            FROM warehouse
            WHERE id=:id
        """, {"id": product_id})
    except Exception as e:
        logging.error(f"⚠️ get_product error: {e}")
        return None


def sell_product(user_id: int, branch_id: int, product_id: int, amount, unit: str = None, price: int = None):
    """
    Ombordan mahsulotni sotish:
    1️⃣ Ombordagi miqdorni kamaytiradi
    2️⃣ Sotilgan mahsulotlar jadvaliga yozadi
    """
    try:
        prod = get_product(product_id)
        if not prod:
            raise Exception("Mahsulot topilmadi")

        cur_qty = float(prod["quantity"] or 0)
        if float(amount) > cur_qty:
            raise Exception("Omborda yetarli mahsulot yo‘q")

        new_qty = cur_qty - float(amount)
        execute("UPDATE warehouse SET quantity=:q WHERE id=:id", {"q": new_qty, "id": product_id})

        unit_use = unit or prod.get("unit")
        price_use = price if price is not None else prod.get("price", 0)

        execute("""
            INSERT INTO sold_products (user_id, branch_id, product_id, amount, unit, price)
            VALUES (:u, :b, :pid, :amt, :unit, :price)
        """, {"u": user_id, "b": branch_id, "pid": product_id, "amt": amount, "unit": unit_use, "price": price_use})

        return True
    except Exception as e:
        logging.error(f"⚠️ sell_product error: {e}")
        return False
def get_all_products(branch_id: int):
    """Ishchining filialiga tegishli ombor mahsulotlarini qaytaradi."""
    try:
        rows = fetchall("""
            SELECT id, product_name AS name, quantity, unit, price
            FROM warehouse
            WHERE branch_id = :b
            ORDER BY id
        """, {"b": branch_id})
        return rows
    except Exception as e:
        logging.error(f"⚠️ get_all_products error: {e}")
        return []
# ===============================
# 🔹 Eslatmalar (NOTES)
# ===============================
def add_note(telegram_id: int, text: str):
    try:
        execute("INSERT INTO notes (telegram_id, text) VALUES (:t, :txt)", {"t": telegram_id, "txt": text})
        return True
    except Exception as e:
        logging.error(f"⚠️ add_note error: {e}")
        return False


def list_notes(telegram_id: int):
    try:
        return fetchall("SELECT id, text, created_at FROM notes WHERE telegram_id=:t ORDER BY id DESC", {"t": telegram_id})
    except Exception as e:
        logging.error(f"⚠️ list_notes error: {e}")
        return []
def ensure_reports_columns():
    """reports jadvalida yangi ustunlar mavjudligini tekshiradi va yo‘q bo‘lsa qo‘shadi."""
    columns_to_add = [
        ("income", "NUMERIC"),
        ("expense", "NUMERIC"),
        ("remaining", "NUMERIC"),
        ("sold_items", "TEXT"),
        ("notes", "TEXT")
    ]

    try:
        with engine.begin() as conn:
            for col, col_type in columns_to_add:
                conn.execute(text(f"""
                    ALTER TABLE reports
                    ADD COLUMN IF NOT EXISTS {col} {col_type};
                """))
        print("✅ reports jadvali ustunlari tekshirildi va keraklisi qo‘shildi.")
    except Exception as e:
        print(f"⚠️ reports ustunlarini qo‘shishda xato: {e}")

# ===============================
# 🚀 Ishga tushirish testi
# ===============================
if __name__ == "__main__":
    init_db()
    ensure_reports_columns()  # 🔥 yangi qo‘shimcha
    print("✅ Database and all tables initialized successfully.")

