import telebot
import time
from config import BOT_TOKEN
from database import init_db, sync_codes_from_config
from utils import keep_alive
from handlers import register_all_handlers

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# تسجيل جميع المعالجات (handlers)
register_all_handlers(bot)

if __name__ == "__main__":
    # تهيئة قاعدة البيانات
    init_db()
    
    # مزامنة الأكواد من config.py إلى قاعدة البيانات
    sync_codes_from_config()
    
    # تشغيل خادم Flask للحفاظ على البوت حياً على Render
    keep_alive()
    
    # إزالة أي webhook قديم لتجنب خطأ 409 Conflict
    print("🚀 جاري إيقاف أي اتصال سابق للبوت...")
    bot.remove_webhook()
    time.sleep(2)
    
    print("✅ متجر مسلم يعمل بنجاح مع جميع الخدمات (فري فاير، تطبيقات، سوشل ميديا)")
    print("🚀 جاري تشغيل البوت...")
    
    # بدء polling
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
