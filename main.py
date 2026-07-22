import asyncio
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler  # تغییر مهم
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler

# ========== متغیرهای محیطی ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER = os.getenv("AUTHORIZED_USER", "")

# ========== توابع شما (همان کدهای خودتون) ==========
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

# وظایف زمانبندی
def check_reminders_task():
    # ... کد خودتان ...
    pass

def _cleanup_temp_files():
    # ... کد خودتان ...
    pass

def log_metrics_task():
    # ... کد خودتان ...
    pass

# ========== هندلرها ==========
async def start_command(update: Update, context):
    await update.message.reply_text("ربات فعال است! ✅")

async def cancel_command(update: Update, context):
    await update.message.reply_text("لغو شد.")

# ========== تابع اصلی ==========
async def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN یافت نشد!")
        return

    _check_access_config()

    # ساخت اپلیکیشن
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # اضافه کردن هندلرها
    conv_handler = ConversationHandler(
        entry_points=entry_points(),
        states=states(),
        fallbacks=fallbacks(),
        name="my_conversation",
        persistent=False,
        allow_reentry=True,
    )
    application.add_handler(conv_handler)

    # ======== تغییر اصلی اینجاست ========
    # استفاده از BackgroundScheduler به جای AsyncIOScheduler
    scheduler = BackgroundScheduler()
    set_scheduler(scheduler, application)

    # اضافه کردن وظایف
    scheduler.add_job(check_reminders_task, 'interval', minutes=5)
    scheduler.add_job(_cleanup_temp_files, 'interval', hours=1)
    scheduler.add_job(log_metrics_task, 'interval', minutes=5)
    # ... بقیه jobها ...

    # شروع scheduler (این تابع sync هست و در ترد جداگانه اجرا میشه)
    scheduler.start()
    # ========================================

    # اجرای پولینگ (همونطور که باید باشه)
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

# ========== نقطه ورود ==========
if __name__ == "__main__":
    asyncio.run(main())
