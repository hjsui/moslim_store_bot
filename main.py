import telebot
import time
from config import BOT_TOKEN
from database import init_db
from utils import keep_alive
from handlers import register_all_handlers

bot = telebot.TeleBot(BOT_TOKEN)

# تسجيل جميع المعالجات
register_all_handlers(bot)

if __name__ == "__main__":
    init_db()
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    print("✅ متجر مسلم يعمل بنجاح مع إدارة الملفات وخدمات السوشل ميديا")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
