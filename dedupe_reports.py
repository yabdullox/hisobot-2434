# dedupe_reports.py
from sqlalchemy import create_engine, text
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)

with engine.begin() as conn:
    # 1) Duplicatelarni o'chirish (id bo'yicha eng kichik qoladi)
    conn.execute(text("""
        DELETE FROM reports
        WHERE id NOT IN (
            SELECT MIN(id) FROM reports GROUP BY user_id, date
        )
    """))
    # 2) UNIQUE index yaratish
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_reports_user_date ON reports(user_id, date)"))

print("✅ Duplicates removed (if any) and unique index created.")
