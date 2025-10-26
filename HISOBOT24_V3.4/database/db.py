import sqlite3, os, shutil

DB_FILE = "data.db"

def safe_repair_db(file_name):
    """Agar baza buzilgan bo‘lsa, uni tiklashga harakat qiladi"""
    try:
        # Baza o‘qilsa – muammo yo‘q
        conn = sqlite3.connect(file_name)
        conn.execute("SELECT 1;")
        conn.close()
        return
    except sqlite3.DatabaseError:
        print("⚠️ Baza buzilgan. Tiklashga urinyapmiz...")

        # Zaxira nusxa olish
        if os.path.exists(file_name):
            shutil.move(file_name, file_name + ".broken")

        # Yangi baza yaratish
        conn = sqlite3.connect(file_name)
        conn.close()
        print("✅ Yangi toza baza yaratildi.")


def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db(filename="data.db"):
    global DB_FILE
    DB_FILE = filename

    safe_repair_db(filename)  # 🔹 Shu joy eng muhim!

    conn = sqlite3.connect(filename)
    cur = conn.cursor()

    # --- Filiallar
    cur.execute("""
    CREATE TABLE IF NOT EXISTS filials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        filial_id TEXT UNIQUE
    )
    """)

    # --- Adminlar
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        tg_id TEXT UNIQUE,
        filial_id INTEGER,
        FOREIGN KEY(filial_id) REFERENCES filials(id)
    )
    """)

    # --- Ishchilar
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        tg_id TEXT UNIQUE,
        filial_id INTEGER,
        FOREIGN KEY(filial_id) REFERENCES filials(id)
    )
    """)

    # --- Hisobotlar
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        filial_id INTEGER,
        text TEXT,
        created_at TEXT
    )
    """)

    # --- Bonus va Jarimalar
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bonuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        filial_id INTEGER,
        reason TEXT,
        amount INTEGER,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        filial_id INTEGER,
        reason TEXT,
        amount INTEGER,
        created_at TEXT
    )
    """)

    # --- Muammolar
    cur.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id INTEGER,
        filial_id INTEGER,
        note TEXT,
        file_id TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

     # --- Jarimalar jadvali ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        )
    """)

    # --- Bonuslar jadvali ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER,
            filial_id INTEGER,
            reason TEXT,
            amount INTEGER,
            created_at TEXT
        )
    """)

    conn.commit()
    print("✅ Baza muvaffaqiyatli ishga tayyor.")