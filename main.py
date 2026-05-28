import telebot
import time
from config import BOT_TOKEN
from database import init_db
from utils import keep_alive
from handlers import register_all_handlers

# إنشاء البوت
bot = telebot.TeleBot(BOT_TOKEN)

# تسجيل جميع المعالجات (handlers) من ملف handlers.py
register_all_handlers(bot)

if __name__ == "__main__":
    # تهيئة قاعدة البيانات
    init_db()
    
    # تشغيل خادم Flask للحفاظ على البوت حياً على Render
    keep_alive()
    
    # إزالة أي webhook قديم لتجنب خطأ 409 Conflict
    bot.remove_webhook()
    time.sleep(2)  # انتظار حتى يتم تطبيق إزالة الـ webhook
    
    print("✅ متجر مسلم يعمل بنجاح مع جميع الخدمات (فري فاير، تطبيقات، سوشل ميديا)")
    print("🚀 جاري تشغيل البوت...")
    
    # بدء polling مع إعدادات مناسبة
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
