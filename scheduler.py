# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
sched = AsyncIOScheduler()


def start_scheduler():
    """Render server uchun mustaqil scheduler"""
    sched.add_job(warn_missing_reports, 'cron', hour=22, minute=0)  # Har kuni soat 22:00
    sched.add_job(saturday_cleaning_penalty, 'cron', day_of_week='sat', hour=0, minute=5)
    sched.add_job(sunday_report_summary, 'cron', day_of_week='sun', hour=8, minute=0)
    sched.start()
    logger.info("✅ Scheduler ishga tushdi (Render-ready)")


# === Quyidagi funksiya namunaviy ish logikasi ===
def warn_missing_reports():
    logger.info("📢 Eslatma yuborish funksiyasi ishladi (mock)")


def saturday_cleaning_penalty():
    logger.info("🧹 Tozalash rasmi yo‘qligiga avtomatik jarima (mock)")


def sunday_report_summary():
    logger.info("📊 Yakshanba umumiy hisobot (mock)")
