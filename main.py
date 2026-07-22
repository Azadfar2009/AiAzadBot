import asyncio
import logging
import os
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ConversationHandler

# ========== تنظیمات اولیه ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER = os.getenv("AUTHORIZED_USER", "")

# ========== ساخت وب‌سرویس Flask ==========
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "ربات فعال است! ✅", 200

@app_flask.route('/health')
def health():
    return "OK", 200

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    # استفاده از debug=False و use_reloader=False برای جلوگیری از مشکلات threading
    app_flask.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== توابع ربات (همان کدهای خودتان) ==========
def _check_access_config():
    # ... کد خودتان ...
    pass

def set_scheduler(scheduler, application):
    # ... کد خودتان ...
    pass

def entry_points():
    return [CommandHandler("start", start_command)]

def states():
    return {}

def fallbacks():
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

# ========== هندلرهای تلگرام ==========
async def start_command(update: Update, context):
    await update.message.reply_text("ربات فعال است! ✅")

async def cancel_command(update: Update, context):
    await update.message.reply_text("لغو شد.")

# ========== تابع اصلی ==========
def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN یافت نشد!")
        return

    _check_access_config()

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
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

    # ======== راه‌اندازی Scheduler ========
    scheduler = BackgroundScheduler()
    set_scheduler(scheduler, application)

    scheduler.add_job(check_reminders_task, 'interval', minutes=5)
    scheduler.add_job(_cleanup_temp_files, 'interval', hours=1)
    scheduler.add_job(log_metrics_task, 'interval', minutes=5)
    scheduler.start()

    # ======== راه‌اندازی وب‌سرویس Flask در یک ترد جداگانه ========
    thread = threading.Thread(target=run_web_server, daemon=True)
    thread.start()

    # ======== راه‌اندازی ربات با مدیریت دستی حلقه رویداد ========
    # یک حلقه رویداد جدید ایجاد می‌کنیم
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # پاک کردن webhookهای قبلی برای جلوگیری از خطای Conflict
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        # اجرای پولینگ با گزینه close_loop=False تا حلقه بسته نشود
        # این کار از بروز خطای "Event loop is closed" جلوگیری می‌کند [reference:7][reference:8]
        loop.run_until_complete(application.run_polling(allowed_updates=Update.ALL_TYPES))
    except KeyboardInterrupt:
        logging.info("ربات توسط کاربر متوقف شد.")
    finally:
        # پاکسازی و بستن حلقه
        try:
            loop.run_until_complete(application.shutdown())
        except Exception as e:
            logging.warning(f"خطا در زمان خاموش کردن اپلیکیشن: {e}")
        finally:
            loop.close()

if __name__ == "__main__":
    main()
