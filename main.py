import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

# ====================================================
# بخش ثابت - تمام متغیرها و توابع کمکی خودتان را اینجا قرار دهید
# (این بخش دقیقاً مثل فایل قبلی شماست، نیازی به تغییر ندارد)
# ====================================================

# متغیرهای محیطی و تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER = os.getenv("AUTHORIZED_USER", "")
ALLOW_ALL_USERS = os.getenv("ALLOW_ALL_USERS", "false").lower() == "true"
REMINDER_CHECK_INTERVAL_MINUTES = int(os.getenv("REMINDER_CHECK_INTERVAL_MINUTES", "5"))
# ... بقیه متغیرهای env شما ...

# توابع کمکی (همان کدهای خودتان)
def _check_access_config():
    # ... کد خودتان ...
    pass

def set_scheduler(scheduler, application):
    # ... کد خودتان ...
    pass

def post_init(application):
    # ... کد خودتان ...
    pass

def post_shutdown(application):
    # ... کد خودتان ...
    pass

def entry_points():
    # ... کد خودتان ...
    return [CommandHandler("start", start_command)]

def states():
    # ... کد خودتان ...
    return {}

def fallbacks():
    # ... کد خودتان ...
    return [CommandHandler("cancel", cancel_command)]

# وظایف زمان‌بندی‌شده (Scheduler Jobs)
def check_reminders_task():
    # ... کد خودتان ...
    pass

def _cleanup_temp_files_async():
    # ... کد خودتان ...
    pass

def log_metrics_task():
    # ... کد خودتان ...
    pass

def weekly_summary_task():
    # ... کد خودتان ...
    pass

def check_url_monitors_task():
    # ... کد خودتان ...
    pass

def daily_briefing_task():
    # ... کد خودتان ...
    pass

async def inline_query_handler(update: Update, context):
    # ... کد خودتان ...
    pass

async def start_command(update: Update, context):
    # ... کد خودتان ...
    pass

async def cancel_command(update: Update, context):
    # ... کد خودتان ...
    pass

# ====================================================
# تابع اصلی - بدون asyncio.run()
# ====================================================

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    _check_access_config()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=entry_points(),
        states=states(),
        fallbacks=fallbacks(),
        name="gemini_conversation",
        persistent=False,
        allow_reentry=True,
    )
    application.add_handler(conv_handler)
    application.add_handler(InlineQueryHandler(inline_query_handler))

    # ساخت زمان‌بند
    scheduler = AsyncIOScheduler()
    set_scheduler(scheduler, application)

    scheduler.add_job(check_reminders_task, 'interval',
                      minutes=REMINDER_CHECK_INTERVAL_MINUTES)
    scheduler.add_job(_cleanup_temp_files_async, 'interval', hours=1)
    scheduler.add_job(log_metrics_task, 'interval', minutes=5)
    scheduler.add_job(weekly_summary_task, 'cron', day_of_week='sun', hour=10, minute=0)
    scheduler.add_job(check_url_monitors_task, 'interval', minutes=30)
    scheduler.add_job(daily_briefing_task, 'cron', minute='*')

    # شروع کردن scheduler در حلقه‌ی رویداد جاری
    # (این کار باید قبل از run_polling انجام بشه)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scheduler.start())

    # حالا run_polling رو صدا می‌زنیم - این تابع خودش حلقه‌ی رویداد رو مدیریت می‌کنه
    # و تا زمانی که ربات متوقف نشه، به کار خودش ادامه میده
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
