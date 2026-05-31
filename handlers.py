# handlers.py
# الملف الرئيسي لتسجيل جميع معالجات البوت

from handlers_common import register_common_handlers
from handlers_games import register_games_handlers
from handlers_social import register_social_handlers
from handlers_payment import register_payment_handlers

def register_all_handlers(bot):
    """تسجيل جميع معالجات البوت من الملفات المختلفة"""
    # تسجيل الدوال المشتركة (القوائم الرئيسية، /start، اللغة)
    common_funcs = register_common_handlers(bot)
    
    # تسجيل دوال فري فاير (الجواهر، المفاتيح، التطبيقات)
    games_funcs = register_games_handlers(bot, common_funcs)
    
    # تسجيل دوال الدفع (طرق الدفع، قبول الطلبات)
    payment_funcs = register_payment_handlers(bot)
    
    # تسجيل دوال السوشل ميديا (تمرير دوال الدفع المشتركة)
    social_funcs = register_social_handlers(bot, common_funcs, payment_funcs)
    
    # يمكن إضافة أي معالجات إضافية هنا مستقبلاً

# جميع الدوال التي تحتاجها الملفات الأخرى يتم تمريرها عبر registration functions
