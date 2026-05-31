# handlers.py
from handlers_common import register_common_handlers
from handlers_payment import register_payment_handlers
from handlers_games import register_games_handlers
from handlers_social import register_social_handlers

def register_all_handlers(bot):
    # 1. تسجيل الدوال المشتركة (القوائم الرئيسية، اللغة)
    common_funcs = register_common_handlers(bot)
    
    # 2. تسجيل الدوال الخاصة بالدفع (يجب قبل الألعاب والسوشل)
    payment_funcs = register_payment_handlers(bot)
    
    # 3. تسجيل دوال الألعاب (فري فاير، تطبيقات)
    games_funcs = register_games_handlers(bot, common_funcs, payment_funcs)
    
    # 4. تسجيل دوال السوشل ميديا
    social_funcs = register_social_handlers(bot, common_funcs, payment_funcs)
