import sqlite3, os

def init_db(filename="data.db"):
    # Eski buzilgan bazani avtomatik tozalash
    if os.path.exists(filename):
        try:
            conn = sqlite3.connect(filename)
            conn.execute("SELECT 1;")
            conn.close()
        except sqlite3.DatabaseError:
            os.remove(filename)
            print("⚠️ Eski baza buzilgan edi, yangidan yaratildi.")
    conn = sqlite3.connect(filename)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS filials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        filial_id TEXT UNIQUE
    )
    """)
    # boshqa jadvallar ham shu yerda...
    conn.commit()
    conn.close()
