# 🔧 Fix: Integer Out of Range Error

## Muammo
Serverda quyidagi xato yuz bermoqda:
```
psycopg2.errors.NumericValueOutOfRange: integer out of range
```

Bu xato `bonuses` va `fines` jadvallaridagi `user_id` va `created_by` ustunlarida yuzaga keladi.

## Sabab
Telegram user ID'lari juda katta raqamlar bo'lishi mumkin (masalan: `8020655627`, `7404485920`).

PostgreSQL'da:
- **INTEGER** tipida maksimal qiymat: `2,147,483,647` (32-bit)
- **BIGINT** tipida maksimal qiymat: `9,223,372,036,854,775,807` (64-bit)

Telegram ID'lari ko'pincha INTEGER maksimal qiymatidan katta bo'ladi, shuning uchun **BIGINT** ishlatish kerak.

## Yechim

### 1-usul: Migratsiya skriptini ishga tushirish

Serverda quyidagi buyruqni bajaring:

```bash
cd /opt/render/project/src
source .venv/bin/activate
python alter_columns.py
```

Bu barcha kerakli ustunlarni BIGINT ga o'zgartiradi.

### 2-usul: Botni qayta ishga tushirish

Bot ishga tushganda `database.py` fayli avtomatik ravishda migratsiyani bajaradi. Shunchaki botni restart qiling:

```bash
# Render.com dashboard'da:
# Manual Deploy > Clear build cache & deploy
```

yoki

```bash
git push origin main
```

## Tekshirish

Migratsiya muvaffaqiyatli bo'lganligini tekshirish uchun:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('bonuses', 'fines', 'users', 'reports')
  AND column_name IN ('user_id', 'telegram_id', 'created_by')
ORDER BY table_name, column_name;
```

Barcha `user_id`, `telegram_id`, va `created_by` ustunlari **bigint** tipida bo'lishi kerak.

## O'zgartirilgan fayllar

1. **database.py** - `created_by` ustuni uchun migratsiya qo'shildi
2. **alter_columns.py** - To'liq va batafsilroq migratsiya skripti

## Muhim eslatma

Bu muammo faqat production serverda yuzaga kelishi mumkin, chunki:
- SQLite (local development) da INTEGER cheksiz o'lchamdagi raqamlarni saqlaydi
- PostgreSQL (production) da INTEGER 32-bit bilan cheklangan
