# src/alter_columns.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://hisobot24_user:LiNrfaWDVW2FbBwJD1DzONOxsaqbjEyj@dpg-d40h4549c44c73barm10-a.frankfurt-postgres.render.com/hisobot24"

engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # Fix all ID columns that might store large Telegram IDs
    migrations = [
        "ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT USING telegram_id::bigint",
        "ALTER TABLE reports ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint",
        "ALTER TABLE fines ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint",
        "ALTER TABLE fines ALTER COLUMN created_by TYPE BIGINT USING created_by::bigint",
        "ALTER TABLE bonuses ALTER COLUMN user_id TYPE BIGINT USING user_id::bigint",
        "ALTER TABLE bonuses ALTER COLUMN created_by TYPE BIGINT USING created_by::bigint"
    ]
    
    for migration in migrations:
        try:
            conn.execute(text(migration))
            print(f"✅ {migration}")
        except Exception as e:
            print(f"⚠️ {migration} - {e}")

print("\n✅ All columns updated to BIGINT!")
