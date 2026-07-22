import asyncio
import logging
import os
import threading
import json
import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# ========== تنظیمات لاگ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== تنظیمات اولیه ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER = os.getenv("AUTHORIZED_USER", "")
ALLOW_ALL_USERS = os.getenv("ALLOW_ALL_USERS", "false").lower() == "true"

# کلیدهای API
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")  # برای Grok
ZAI_API_KEY = os.getenv("ZAI_API_KEY")

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
    app_flask.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ========== توابع کمکی ==========
def is_authorized(user_id):
    if ALLOW_ALL_USERS:
        return True
    if not AUTHORIZED_USER:
        return False
    return str(user_id) in AUTHORIZED_USER.split(',')

def get_available_models():
    models = []
    if GROQ_API_KEY:
        models.append(("Groq", "groq"))
    if XAI_API_KEY:
        models.append(("Grok (xAI)", "grok"))
    if ZAI_API_KEY:
        models.append(("Z.ai", "zai"))
    return models

# ========== هندلرهای تلگرام ==========
async def start_command(update: Update, context):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("شما دسترسی به این ربات ندارید.")
        return
    
    models = get_available_models()
    if not models:
        await update.message.reply_text("هیچ مدل هوش مصنوعی فعالی یافت نشد. لطفاً با ادمین تماس بگیرید.")
        return
    
    keyboard = []
    for name, key in models:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"model_{key}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "به ربات هوش مصنوعی خوش آمدید!\nلطفاً یکی از مدل‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def model_selection(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_authorized(user_id):
        await query.edit_message_text("شما دسترسی به این ربات ندارید.")
        return
    
    model_key = query.data.replace("model_", "")
    context.user_data['selected_model'] = model_key
    
    model_names = {
        "groq": "Groq",
        "grok": "Grok (xAI)",
        "zai": "Z.ai"
    }
    
    await query.edit_message_text(
        f"مدل {model_names.get(model_key, model_key)} انتخاب شد.\n"
        "حالا می‌توانید پیام خود را ارسال کنید."
    )

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("شما دسترسی به این ربات ندارید.")
        return
    
    selected_model = context.user_data.get('selected_model')
    if not selected_model:
        await update.message.reply_text(
            "لطفاً ابتدا یک مدل را با دستور /start انتخاب کنید."
        )
        return
    
    user_message = update.message.text
    logger.info(f"پیام دریافتی از {user_id}: {user_message} (مدل: {selected_model})")
    
    # ======== اتصال به APIهای مختلف ========
    try:
        if selected_model == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.1-70b-versatile",
                "messages": [{"role": "user", "content": user_message}]
            }
        
        elif selected_model == "grok":
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "grok-2-1212",
                "messages": [{"role": "user", "content": user_message}]
            }
        
        elif selected_model == "zai":
            url = "https://api.z.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {ZAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "zai-1",
                "messages": [{"role": "user", "content": user_message}]
            }
        
        else:
            await update.message.reply_text("مدل انتخاب شده نامعتبر است.")
            return
        
        logger.info(f"ارسال درخواست به {url}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response Text: {response.text[:500]}")
            
            if response.status_code != 200:
                await update.message.reply_text(
                    f"خطا در ارتباط با API (کد {response.status_code}):\n"
                    f"{response.text[:200]}"
                )
                return
            
            result = response.json()
            reply = result.get("choices", [{}])[0].get("message", {}).get("content", "خطا در دریافت پاسخ.")
            
            if not reply:
                reply = "پاسخی از سمت API دریافت نشد. لطفاً دوباره تلاش کنید."
            
            await update.message.reply_text(reply)
        
    except httpx.TimeoutException:
        logger.error("Timeout در ارتباط با API")
        await update.message.reply_text("زمان پاسخ‌دهی API به پایان رسید. لطفاً دوباره تلاش کنید.")
    except json.JSONDecodeError as e:
        logger.error(f"خطا در پردازش JSON: {e}")
        await update.message.reply_text(f"پاسخ دریافتی معتبر نیست: {str(e)[:100]}")
    except Exception as e:
        logger.error(f"خطای ناشناخته: {e}")
        await update.message.reply_text(f"خطا در ارتباط با API: {str(e)[:200]}")

# ========== تابع اصلی ==========
def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN یافت نشد!")
        return

    logger.info("ربات در حال راه‌اندازی...")
    logger.info(f"مدل‌های فعال: {[m[0] for m in get_available_models()]}")

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(model_selection, pattern="^model_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ======== راه‌اندازی Scheduler ========
    scheduler = BackgroundScheduler()
    scheduler.start()
    logger.info("Scheduler راه‌اندازی شد.")

    # ======== راه‌اندازی وب‌سرویس Flask در یک ترد جداگانه ========
    thread = threading.Thread(target=run_web_server, daemon=True)
    thread.start()
    logger.info("وب‌سرویس Flask در ترد جداگانه راه‌اندازی شد.")

    # ======== راه‌اندازی ربات ========
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        logger.info("در حال پاک کردن Webhook قبلی...")
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        logger.info("Webhook پاک شد. شروع پولینگ...")
        loop.run_until_complete(application.run_polling(allowed_updates=Update.ALL_TYPES))
    except KeyboardInterrupt:
        logger.info("ربات توسط کاربر متوقف شد.")
    except Exception as e:
        logger.error(f"خطا در اجرای ربات: {e}")
    finally:
        try:
            loop.run_until_complete(application.shutdown())
            logger.info("ربات به درستی خاموش شد.")
        except Exception as e:
            logger.warning(f"خطا در زمان خاموش کردن اپلیکیشن: {e}")
        finally:
            loop.close()

if __name__ == "__main__":
    main()
