# handlers.py
# الملف الرئيسي لتسجيل جميع معالجات البوت

from handlers_common import register_common_handlers
from handlers_games import register_games_handlers
from handlers_social import register_social_handlers
from handlers_payment import register_payment_handlers

def register_all_handlers(bot):
    """تسجيل جميع معالجات البوت من الملفات المختلفة"""
    
    # 1. تسجيل الدوال المشتركة (القوائم الرئيسية، /start، اللغة)
    common_funcs = register_common_handlers(bot)
    
    # 2. تسجيل دوال الدفع (طرق الدفع، قبول الطلبات) - يجب أن يكون قبل الألعاب
    payment_funcs = register_payment_handlers(bot)
    
    # 3. تسجيل دوال فري فاير (الجواهر، المفاتيح، التطبيقات)
    # ✅ تم إصلاح الخطأ: إضافة payment_funcs كمعامل ثالث
    games_funcs = register_games_handlers(bot, common_funcs, payment_funcs)
    
    # 4. تسجيل دوال السوشل ميديا
    social_funcs = register_social_handlers(bot, common_funcs, payment_funcs)
    
    # يمكن إضافة أي معالجات إضافية هنا مستقبلاً

# جميع الدوال التي تحتاجها الملفات الأخرى يتم تمريرها عبر registration functions
