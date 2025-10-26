# 🤖 HISOBOT24 — Telegram Hisobot Bot (Aiogram 3.x)

**HISOBOT24** — bu kompaniya yoki filial ishchilari uchun ishlab chiqilgan avtomatik hisobot tizimi.  
Bot orqali ishchilar kunlik hisobot yuboradi, superadmin esa barcha ma’lumotlarni avtomatik ravishda qabul qiladi.  

---

## ⚙️ Asosiy imkoniyatlar

- 🧾 **Hisobot yuborish** — ishchi kunlik hisobotni bot orqali yuboradi  
- ⏰ **Ishni boshlash** — ishchi ishni boshlanganini bildiradi  
- 📷 **Tozalash yoki muammo rasmi yuborish**  
- 🧑‍💼 **Filial adminlar** — ishchilarni kuzatish va nazorat qilish  
- 👑 **SuperAdmin** — barcha filiallar faoliyatini kuzatadi  
- 💾 **SQLite (aiosqlite)** bazada barcha ma’lumotlar saqlanadi  

---

## 🧰 Texnologiyalar

| Texnologiya | Tavsif |
|--------------|--------|
| [Python 3.11+](https://www.python.org/downloads/) | Dasturlash tili |
| [Aiogram 3.x](https://docs.aiogram.dev/) | Telegram Bot Framework |
| [SQLite + aiosqlite](https://docs.python.org/3/library/sqlite3.html) | Ma’lumotlar bazasi |
| [Render.com](https://render.com) | 24/7 deploy uchun hosting |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | `.env` konfiguratsiya fayli uchun |

---

## 📦 O‘rnatish (Localda)

1. **Repository** ni klon qiling:
   ```bash
   git clone https://github.com/<sizning_user>/<hisobot24-bot>.git
   cd hisobot24-bot
Kutubxonalarni o‘rnating:  pip install -r requirements.txt



.env fayl yarating (misol uchun .env.example dan nusxa oling):

BOT_TOKEN=1234567890:YOUR_TOKEN_HERE
SUPERADMIN_ID=1112223333
DATABASE_FILE=data.db



Botni ishga tushiring:  python main.py