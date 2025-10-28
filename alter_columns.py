# src/alter_columns.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://hisobot24_user:LiNrfaWDVW2FbBwJD1DzONOxsaqbjEyj@dpg-d40h4549c44c73barm10-a.frankfurt-postgres.render.com/hisobot24"

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE bonuses ALTER COLUMN created_by TYPE BIGINT"))
    conn.execute(text("ALTER TABLE bonuses ALTER COLUMN user_id TYPE BIGINT"))
    conn.execute(text("ALTER TABLE bonuses ALTER COLUMN branch_id TYPE BIGINT"))

print("✅ Columns updated successfully to BIGINT!")
