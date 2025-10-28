# HISOBOT24 — Aiogram 3.x Telegram Bot

Bu loyiha HISOBOT24 Telegram botining to'liq, toza va ishlaydigan versiyasidir.
Loyihaning barcha maxfiy parametrlari `.env` orqali olinadi (python-dotenv orqali).

## Asosiy fayllar
- `main.py` — botni ishga tushiradi.
- `config.py` — .env dan konfiguratsiyalarni yuklaydi.
- `database.py` — SQLAlchemy engine va jadval yaratish SQL skripti.
- `scheduler.py` — APScheduler yordamida cron ishlarini bajaradi.
- `handlers/` — start, superadmin, admin, worker routerlari.
- `keyboards/` — superadmin, admin, worker uchun ReplyKeyboardMarkup'lar.
- `requirements.txt` — pip paketlar.
- `.env.example` — .env namunasi (TOKEN va chat_id larni yozmang!).

## Ishga tushirish
1. Virtual muhitingizni yarating va faollashtiring.
2. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env` faylini `.env.example` ga mos to'ldiring.
4. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## Muhim eslatma
- `.env` faylida `BOT_TOKEN` va `SUPERADMIN_ID` mavjud bo'lishi shart.
- Faqat bitta Super Admin bo'ladi (SUPERADMIN_ID orqali aniqlanadi). Super Admin adminlarni bot orqali qo'shadi.
- Barcha fayl va tokenlarni xavfsiz joyda saqlang.
