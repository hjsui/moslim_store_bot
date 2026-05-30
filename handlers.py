# handlers.py
# الملف الرئيسي لتسجيل جميع معالجات البوت (يستورد من الملفات الأخرى)

from handlers_common import register_common_handlers
from handlers_games import register_games_handlers
from handlers_social import register_social_handlers, user_social_state as social_state
from handlers_payment import register_payment_handlers

# هذا المتغير سيتم تعيينه عند استدعاء register_all_handlers
_user_social_state = social_state

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

    # ملاحظة: المتغير _user_social_state يشير إلى نفس الكائن داخل handlers_social
    # يمكنك الوصول إليه من الخارج إذا أردت

    # يمكن إضافة أي معالجات إضافية هنا مستقبلاً

# لضمان تصدير register_all_handlers
__all__ = ['register_all_handlers']
