# handlers_common.py
# الدوال المشتركة (القوائم الرئيسية، اختيار اللغة، العرض العام)

import telebot
from telebot import types
import sqlite3
from datetime import datetime
from config import CHANNEL_PROOFS, STORE_PASSWORD
from database import get_lang, set_lang, get_verified_count
from languages import T

def register_common_handlers(bot):
    """تسجيل الدوال المشتركة (غير مرتبطة بمنتجات محددة)"""

    def send_lang_selection(chat_id):
        photo_url = "https://i.postimg.cc/g2Dtfh3L/Picsart-26-01-29-07-31-38-423.jpg"
        caption = "🌍 *Please select your language / اختر لغتك*"
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("🇲🇦 العربية", callback_data="lang_ar"),
                   types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
        bot.send_photo(chat_id, photo=photo_url, caption=caption, parse_mode="Markdown", reply_markup=markup)

    def show_main_menu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.row(t["shop_now"], t["services"])
        markup.row(t["add_balance"], t["profile"])
        markup.row(t["how_to_use"], t["support"])
        markup.row(t["proofs"])
        user_count = get_verified_count()
        msg = t["welcome_main"].format(message.from_user.first_name, CHANNEL_PROOFS) + t["user_count"].format(user_count)
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

    def show_services_menu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["games_services"], t["social_media"])
        markup.add(t["apps_service"], t["back_to_main"])
        bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")

    def show_games_submenu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["ff_services"])
        markup.add(t["back_to_games"])
        bot.send_message(message.chat.id, "🎮 *اختر اللعبة:*", reply_markup=markup, parse_mode="Markdown")

    # ========== معالج /start ==========
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        c.execute("SELECT verified, language FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        if not user:
            join_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO users (user_id, username, verified, purchases, join_date, language) VALUES (?, ?, 0, '', ?, 'ar')",
                      (user_id, message.from_user.username, join_date))
            conn.commit()
            conn.close()
            send_lang_selection(message.chat.id)
            return
        verified, lang = user
        if verified:
            show_main_menu(message, lang)
        else:
            bot.send_message(message.chat.id, T[lang]["ask_password"], parse_mode="Markdown")
        conn.close()

    # ========== معالج اختيار اللغة ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
    def callback_lang(call):
        lang = call.data.split('_')[1]
        set_lang(call.from_user.id, lang)
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, T[lang]["welcome_after_lang"].format(CHANNEL_PROOFS), parse_mode="Markdown")

    # ========== معالج الرسائل العامة (الأزرار الرئيسية) ==========
    @bot.message_handler(func=lambda msg: True, content_types=['text'])
    def handle_messages(message):
        user_id = message.from_user.id
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        c.execute("SELECT verified, language FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        if not user:
            conn.close()
            return
        verified, lang = user
        t = T[lang]

        # التحقق من كلمة المرور
        if not verified:
            if message.text == STORE_PASSWORD:
                c.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
                conn.commit()
                bot.reply_to(message, t["verified_success"], parse_mode="Markdown")
                show_main_menu(message, lang)
            else:
                bot.reply_to(message, t["wrong_password"], parse_mode="Markdown")
            conn.close()
            return

        text = message.text
        if text == t["services"]:
            show_services_menu(message, lang)
        elif text == t["social_media"]:
            from handlers_social import show_social_platforms
            show_social_platforms(user_id, lang, bot)
            conn.close()
            return
        elif text == t["games_services"]:
            show_games_submenu(message, lang)
        elif text == t["ff_services"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(t["keys_service"], t["ff_topup"])
            markup.add(t["back_to_games"])
            bot.send_message(message.chat.id, "🕹️ *خدمات فري فاير:*\n━━━━━━━━━━━━\nاختر الخدمة:", reply_markup=markup, parse_mode="Markdown")
        elif text == t["shop_now"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(t["games_services"], t["social_media"])
            markup.add(t["apps_service"], t["back_to_main"])
            bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")
        elif text == t["apps_service"]:
            from handlers_games import show_apps_products
            show_apps_products(message, lang, bot)
        elif text == t["ff_topup"]:
            from handlers_games import show_ff_packages
            show_ff_packages(message, lang, bot)
        elif text == t["keys_service"]:
            from handlers_games import show_keys_products
            show_keys_products(message, lang, bot)
        elif text == t["back_to_main"]:
            show_main_menu(message, lang)
        elif text == t["back_to_sections"]:
            show_services_menu(message, lang)
        elif text == t["back_to_games"]:
            show_games_submenu(message, lang)
        elif text == t["proofs"]:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(t.get("inline_proofs_btn", "📢 قناة الإثباتات"), url=CHANNEL_PROOFS))
            bot.send_message(message.chat.id, t["proofs_text"].format(CHANNEL_PROOFS), reply_markup=markup, parse_mode="Markdown")
        elif text == t["profile"]:
            c.execute("SELECT purchases, join_date FROM users WHERE user_id=?", (user_id,))
            purchases, join_date = c.fetchone()
            if not purchases:
                purchases = "📭 " + ("لا توجد مشتريات بعد." if lang=='ar' else "No purchases yet.")
            bot.send_message(message.chat.id, t["profile_text"].format(user_id, join_date, purchases), parse_mode="Markdown")
        elif text == t["support"]:
            from config import ADMIN_CONTACT
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("💬 " + ("مراسلة المدير" if lang=='ar' else "Contact Manager"), url=ADMIN_CONTACT))
            markup.add(types.InlineKeyboardButton("📢 " + ("قناة المتجر" if lang=='ar' else "Store Channel"), url="https://chat.whatsapp.com/KhbuyOvojIX7FjKs7K0CfV"))
            markup.add(types.InlineKeyboardButton("⭐ " + ("إثباتات الثقة" if lang=='ar' else "Trust Proofs"), url=CHANNEL_PROOFS))
            bot.send_message(message.chat.id, t["support_text"], reply_markup=markup, parse_mode="Markdown")
        elif text == t["add_balance"]:
            from config import ADMIN_CONTACT
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💳 " + ("مراسلة الدعم للشحن" if lang=='ar' else "Contact support for payment"), url=ADMIN_CONTACT))
            bot.send_message(message.chat.id, t["add_balance_text"], reply_markup=markup, parse_mode="Markdown")
        elif text == t["how_to_use"]:
            bot.send_message(message.chat.id, t["how_to_use_text"], parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, t["default_reply"].format(CHANNEL_PROOFS), parse_mode="Markdown")
        conn.close()

    # إعادة الدوال التي قد تحتاجها الملفات الأخرى
    return {
        'show_main_menu': show_main_menu,
        'show_services_menu': show_services_menu,
        'show_games_submenu': show_games_submenu
    }
