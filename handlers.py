# handlers.py
# الإصدار النهائي – جميع الخدمات + لوحة التحكم الإدارية + استخدام قاعدة البيانات للمخزون

import telebot
from telebot import types
import sqlite3
from datetime import datetime
import time
from config import (
    ADMIN_IDS, WHITELISTED_USERS, STORE_PASSWORD, CHANNEL_PROOFS, ADMIN_CONTACT,
    prices, keys_inventory, apps_inventory, LOG_CHANNEL_ID,
    USD_TO_MAD, DEFAULT_CURRENCY, OWNER_ID
)
from database import (
    get_lang, set_lang, get_verified_count, add_purchase_record,
    create_order, update_order_status, get_order,
    get_user_currency, set_user_currency,
    get_ff_code, get_key_code
)
from utils import is_admin, is_whitelisted
from payment_methods import PAYMENT_METHODS
from languages import T
from social_api import (
    get_services, add_order, get_order_status, calculate_price_with_profit,
    get_services_by_ids
)
from social_structure import (
    SOCIAL_STRUCTURE, get_categories_list, get_subcategories_list,
    get_service_ids_from_structure
)
from admin_handlers import register_admin_handlers, admin_temp, process_admin_text

user_social_state = {}
_services_cache = None
_services_cache_time = 0
SERVICES_CACHE_TTL = 300

def get_services_cached():
    global _services_cache, _services_cache_time
    now = time.time()
    if _services_cache is None or now - _services_cache_time > SERVICES_CACHE_TTL:
        _services_cache = get_services()
        _services_cache_time = now
    return _services_cache

def register_all_handlers(bot):
    """تسجيل جميع معالجات البوت"""

    # ========== دوال مساعدة ==========
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
        markup.row(t["change_language"], t["change_currency"])
        markup.row(t["how_to_use"], t["support"])
        markup.row(t["proofs"])
        user_count = get_verified_count()
        msg = t["welcome_main"].format(message.from_user.first_name, CHANNEL_PROOFS) + t["user_count"].format(user_count)
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

    def show_services_menu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["apps_service"], t["games_services"])
        markup.add(t["back_to_main"], t["social_media"])
        bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")

    def show_games_menu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["ff_services"])
        markup.add(t["back_to_sections"])
        bot.send_message(message.chat.id, "🎮 *" + t.get("choose_game", "اختر اللعبة:") + "*", reply_markup=markup, parse_mode="Markdown")

    def show_language_selector(user_id, lang):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton(t["language_arabic"], callback_data="set_lang_ar"),
                   types.InlineKeyboardButton(t["language_english"], callback_data="set_lang_en"))
        bot.send_message(user_id, t["select_language"], reply_markup=markup, parse_mode="Markdown")

    def show_currency_selector(user_id, lang):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton(t["currency_mad"], callback_data="set_currency_mad"),
                   types.InlineKeyboardButton(t["currency_usd"], callback_data="set_currency_usd"))
        bot.send_message(user_id, t["select_currency"], reply_markup=markup, parse_mode="Markdown")

    def show_ff_packages(message, lang):
        t = T[lang]
        user_id = message.from_user.id
        currency = get_user_currency(user_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pkg in prices:
            price_mad = int(prices[pkg])
            if currency == 'usd':
                price_display = round(price_mad / USD_TO_MAD, 2)
                currency_symbol = "$"
            else:
                price_display = price_mad
                currency_symbol = t.get("currency_mad", "درهم")
            markup.add(types.InlineKeyboardButton(f"💎 {pkg} {'جوهرة' if lang=='ar' else 'diamonds'} = {price_display} {currency_symbol}", callback_data=f"buy_{pkg}"))
        markup.add(types.InlineKeyboardButton("📢 " + ("شاهد الإثباتات قبل الشراء" if lang=='ar' else "See proofs before buying"), url=CHANNEL_PROOFS))
        markup.add(types.InlineKeyboardButton(t["back_to_games"], callback_data="back_to_games_menu"))
        bot.send_message(message.chat.id, t["ff_packages_title"], reply_markup=markup, parse_mode="Markdown")

    def show_keys_products(message, lang):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for prod_id, prod_data in keys_inventory.items():
            btn_text = prod_data["name_ar"] if lang == 'ar' else prod_data["name_en"]
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"key_prod_{prod_id}"))
        bot.send_message(message.chat.id, t["choose_product"], reply_markup=markup, parse_mode="Markdown")

    def show_apps_products(message, lang):
        t = T[lang]
        user_id = message.from_user.id
        currency = get_user_currency(user_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        for app_id, app_data in apps_inventory.items():
            btn_text = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
            price_mad = app_data["price"]
            if currency == 'usd':
                price_display = round(price_mad / USD_TO_MAD, 2)
                currency_symbol = "$"
            else:
                price_display = price_mad
                currency_symbol = t.get("currency_mad", "درهم")
            markup.add(types.InlineKeyboardButton(f"{btn_text} - {price_display} {currency_symbol}", callback_data=f"app_buy_{app_id}"))
        bot.send_message(message.chat.id, t["choose_app"], reply_markup=markup, parse_mode="Markdown")

    def show_payment_methods(user_id, product_type, product_id, amount):
        lang = get_lang(user_id)
        currency = get_user_currency(user_id)
        t = T[lang]
        if currency == 'usd':
            amount_display = round(amount / USD_TO_MAD, 2)
            currency_symbol = "$"
        else:
            amount_display = amount
            currency_symbol = t.get("currency_mad", "درهم")
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, method in PAYMENT_METHODS.items():
            name = method["name_ar"] if lang == 'ar' else method["name_en"]
            markup.add(types.InlineKeyboardButton(name, callback_data=f"pay_{key}_{product_type}_{product_id}_{amount}"))
        msg = f"<b>{t['payment_method_label']}</b>\n━━━━━━━━━━━━\n<b>{t['amount']}</b> {amount_display} {currency_symbol}\n\n{t['payment_instructions']}"
        bot.send_message(user_id, msg, reply_markup=markup, parse_mode="HTML")

    def send_withdrawal_log(admin_username, product_name, price, extra_info="", code_or_link=None):
        if not LOG_CHANNEL_ID:
            return
        msg = f"📋 *تقرير سحب (قائمة بيضاء)*\n━━━━━━━━━━━━\n👤 الوكيل: @{admin_username}\n📦 المنتج: {product_name}\n💰 السعر: {price} درهم\n"
        if code_or_link:
            if "http" in str(code_or_link):
                msg += f"🔗 رابط: [اضغط هنا]({code_or_link})\n"
            else:
                msg += f"🔑 الكود: `{code_or_link}`\n"
        msg += extra_info
        msg += f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n━━━━━━━━━━━━"
        try:
            bot.send_message(LOG_CHANNEL_ID, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"فشل إرسال التقرير: {e}")

    def finalize_order(order_id, accepted, admin_id=None):
        order = get_order(order_id)
        if not order:
            return
        user_id = order[1]
        product_type = order[2]
        product_id = order[3]
        amount = order[4]
        lang = get_lang(user_id)
        t = T[lang]
        if accepted:
            if product_type == 'ff':
                code = get_ff_code(product_id)
                if code:
                    currency = get_user_currency(user_id)
                    if currency == 'usd':
                        amount_display = round(amount / USD_TO_MAD, 2)
                        currency_symbol = "$"
                    else:
                        amount_display = amount
                        currency_symbol = t.get("currency_mad", "درهم")
                    success_msg = t["purchase_success"].format(product_id, amount_display, currency_symbol, code, ADMIN_CONTACT, CHANNEL_PROOFS)
                    bot.send_message(user_id, success_msg, parse_mode="Markdown")
                    add_purchase_record(user_id, f"📦 {product_id}💎 ({amount} DH): {code} - {datetime.now()}")
                    for admin in ADMIN_IDS:
                        try:
                            bot.send_message(admin, f"✅ تم قبول الطلب {order_id} وتسليم الكود: {code}")
                        except:
                            pass
                    update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                else:
                    bot.send_message(user_id, t["out_of_stock"], parse_mode="Markdown")
                    update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
            elif product_type == 'key':
                parts = product_id.split('_')
                if len(parts) == 2:
                    key_id, days = parts[0], parts[1]
                    code = get_key_code(key_id, days)
                    if code:
                        product_name = keys_inventory[key_id]["name_ar"] if lang == 'ar' else keys_inventory[key_id]["name_en"]
                        currency = get_user_currency(user_id)
                        if currency == 'usd':
                            amount_display = round(amount / USD_TO_MAD, 2)
                            currency_symbol = "$"
                        else:
                            amount_display = amount
                            currency_symbol = t.get("currency_mad", "درهم")
                        success_msg = t["keys_purchase_success"].format(product_name, days, amount_display, currency_symbol, code, ADMIN_CONTACT, CHANNEL_PROOFS)
                        bot.send_message(user_id, success_msg, parse_mode="Markdown")
                        add_purchase_record(user_id, f"🔑 {product_name} ({days} يوم) - {amount} 💰: {code} - {datetime.now()}")
                        for admin in ADMIN_IDS:
                            try:
                                bot.send_message(admin, f"✅ تم قبول الطلب {order_id} وتسليم المفتاح: {code}")
                            except:
                                pass
                        update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                    else:
                        bot.send_message(user_id, t["no_stock"], parse_mode="Markdown")
                        update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
                else:
                    bot.send_message(user_id, t["no_stock"], parse_mode="Markdown")
                    update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
            elif product_type == 'app':
                app_data = apps_inventory.get(product_id)
                if app_data:
                    product_name = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
                    download_link = app_data.get("link", "")
                    channel_link = app_data.get("update_channel", "")
                    currency = get_user_currency(user_id)
                    if currency == 'usd':
                        amount_display = round(amount / USD_TO_MAD, 2)
                        currency_symbol = "$"
                    else:
                        amount_display = amount
                        currency_symbol = t.get("currency_mad", "درهم")
                    success_msg = t["order_accepted"].format(product_name, amount_display, currency_symbol, download_link, channel_link, ADMIN_CONTACT, CHANNEL_PROOFS)
                    bot.send_message(user_id, success_msg, parse_mode="Markdown")
                    add_purchase_record(user_id, f"📱 {product_name} ({amount} DH): تم التحميل - {datetime.now()}")
                    for admin in ADMIN_IDS:
                        try:
                            bot.send_message(admin, f"✅ تم قبول الطلب {order_id} (تطبيق {product_name})")
                        except:
                            pass
                    update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                else:
                    bot.send_message(user_id, t["app_no_stock"], parse_mode="Markdown")
                    update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
            elif product_type == 'social':
                try:
                    parts = product_id.split('|')
                    if len(parts) == 4:
                        _, service_id_str, link, quantity_str = parts
                        service_id = int(service_id_str)
                        quantity = int(quantity_str)
                        result = add_order(service_id, link, quantity)
                        if result and 'order' in result:
                            api_order_id = result['order']
                            bot.send_message(user_id, f"✅ *تم تنفيذ طلبك بنجاح!*\n🆔 رقم طلب API: `{api_order_id}`\nيمكنك متابعة الحالة عبر /social_status {api_order_id}", parse_mode="Markdown")
                            add_purchase_record(user_id, f"🌐 طلب سوشل ميديا (API ID: {api_order_id}) - {amount} DH")
                            update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                        else:
                            error_msg = result.get('error', 'خطأ غير معروف') if result else 'فشل الاتصال بالـ API'
                            bot.send_message(user_id, f"❌ *فشل تنفيذ الطلب*\nالسبب: {error_msg}\nتم إبلاغ المدير.", parse_mode="Markdown")
                            update_order_status(order_id, 'failed', admin_action='api_error')
                    else:
                        bot.send_message(user_id, "❌ بيانات الطلب غير صالحة. تم إبلاغ المدير.")
                        update_order_status(order_id, 'failed', admin_action='invalid_data')
                except Exception as e:
                    print(f"خطأ في معالجة طلب السوشل ميديا: {e}")
                    bot.send_message(user_id, "❌ حدث خطأ داخلي. تم إبلاغ المدير.")
                    update_order_status(order_id, 'failed', admin_action='internal_error')
        else:
            if product_type == 'ff':
                product_name = f"جواهر فري فاير ({product_id} جوهرة)"
            elif product_type == 'key':
                parts = product_id.split('_')
                product_name = f"مفتاح DRIP CLIENT - {parts[1] if len(parts)>1 else product_id} يوم"
            elif product_type == 'app':
                app_data = apps_inventory.get(product_id, {})
                product_name = app_data.get("name_ar", "تطبيق") if lang == 'ar' else app_data.get("name_en", "App")
            elif product_type == 'social':
                product_name = "خدمة سوشل ميديا"
            else:
                product_name = "المنتج"
            reject_msg = t["order_rejected"].format(product_name)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🔄 " + ("تغيير طريقة الدفع" if lang=='ar' else "Change payment method"), callback_data=f"change_payment_{order_id}"))
            bot.send_message(user_id, reject_msg, reply_markup=markup, parse_mode="Markdown")
            update_order_status(order_id, 'rejected', admin_action=f'reject_by_{admin_id}')
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, f"❌ تم رفض الطلب {order_id}")
                except:
                    pass

    # ========== دوال السوشل ميديا ==========
    def show_social_platforms(user_id, lang):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=2)
        for platform_id, data in SOCIAL_STRUCTURE.items():
            icon = data['icon']
            name = data['name']
            btn_text = f"{icon} {name}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_platform_{platform_id}"))
        markup.add(types.InlineKeyboardButton("🔙 " + ("العودة" if lang=='ar' else "Back"), callback_data="social_back_to_main"))
        bot.send_message(user_id, t["social_choose_platform"], reply_markup=markup, parse_mode="Markdown")

    def show_social_categories(user_id, platform_id, lang):
        t = T[lang]
        platform_data = SOCIAL_STRUCTURE.get(platform_id)
        if not platform_data:
            bot.send_message(user_id, "⚠️ " + ("منصة غير معروفة." if lang=='ar' else "Unknown platform."))
            return
        categories = get_categories_list(platform_id)
        if not categories:
            bot.send_message(user_id, "⚠️ " + ("لا توجد خدمات متاحة لهذه المنصة حالياً." if lang=='ar' else "No services available for this platform."))
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for cat_name, cat_icon in categories:
            btn_text = f"{cat_icon} {cat_name}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_category_{platform_id}_{cat_name}"))
        markup.add(types.InlineKeyboardButton("🔙 " + ("رجوع للمنصات" if lang=='ar' else "Back to platforms"), callback_data="social_back_to_platforms"))
        bot.send_message(user_id, f"{platform_data['icon']} *{platform_data['name']}*\n{t['social_select_category']}", reply_markup=markup, parse_mode="Markdown")

    def show_social_subcategories(user_id, platform_id, category_name, lang):
        t = T[lang]
        platform_data = SOCIAL_STRUCTURE.get(platform_id)
        subcategories = get_subcategories_list(platform_id, category_name)
        service_ids = get_service_ids_from_structure(platform_id, category_name)
        if not service_ids:
            bot.send_message(user_id, "⚠️ " + ("لا توجد خدمات في هذا التصنيف." if lang=='ar' else "No services in this category."))
            return
        services = get_services_by_ids(service_ids)
        if not services:
            bot.send_message(user_id, "⚠️ " + ("لا توجد خدمات متاحة حالياً." if lang=='ar' else "No services available at the moment."))
            return
        if subcategories:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for sub_name, sub_icon in subcategories:
                btn_text = f"{sub_icon} {sub_name}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_subcategory_{platform_id}_{category_name}_{sub_name}"))
            markup.add(types.InlineKeyboardButton("🔙 " + ("رجوع للتصنيفات" if lang=='ar' else "Back to categories"), callback_data=f"social_back_to_categories_{platform_id}"))
            bot.send_message(user_id, f"{platform_data['icon']} *{platform_data['name']} / {category_name}*\n{t['social_select_subcategory']}", reply_markup=markup, parse_mode="Markdown")
        else:
            user_social_state[user_id] = {
                'platform_id': platform_id,
                'platform_name': platform_data['name'],
                'platform_icon': platform_data['icon'],
                'services': services,
                'step': 'selecting_service',
                'category_name': category_name
            }
            show_services_list(user_id, lang)

    def show_services_list(user_id, lang):
        t = T[lang]
        data = user_social_state.get(user_id, {})
        services = data.get('services', [])
        if not services:
            bot.send_message(user_id, "⚠️ " + ("لا توجد خدمات." if lang=='ar' else "No services."))
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for svc in services:
            btn_text = f"{svc['name']} - {svc['rate']} USD"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_service_{svc['service']}"))
        if data.get('subcategory_name'):
            back_callback = f"social_back_to_subcategories_{data['platform_id']}_{data['category_name']}"
        elif data.get('category_name'):
            back_callback = f"social_back_to_categories_{data['platform_id']}"
        else:
            back_callback = "social_back_to_platforms"
        markup.add(types.InlineKeyboardButton("🔙 " + ("رجوع" if lang=='ar' else "Back"), callback_data=back_callback))
        bot.send_message(user_id, f"{data.get('platform_icon', '📢')} *" + t.get("social_select_service", "اختر الخدمة:") + "*", reply_markup=markup, parse_mode="Markdown")

    # ========== معالج /start ==========
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        try:
            c.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'mad'")
            conn.commit()
        except:
            pass
        c.execute("SELECT verified, language FROM users WHERE user_id=?", (user_id,))
        user = c.fetchone()
        if not user:
            join_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO users (user_id, username, verified, purchases, join_date, language, currency) VALUES (?, ?, 0, '', ?, 'ar', 'mad')",
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

    # ========== أمر المدير /meow ==========
    @bot.message_handler(commands=['meow'])
    def admin_panel(message):
        user_id = message.from_user.id
        if user_id != OWNER_ID:
            bot.reply_to(message, "⚠️ هذا الأمر متاح فقط لمدير المتجر.")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📊 إدارة جواهر فري فاير", callback_data="admin_ff"))
        markup.add(types.InlineKeyboardButton("🔑 إدارة مفاتيح DRIP CLIENT", callback_data="admin_keys"))
        bot.reply_to(message, "🛠️ *لوحة التحكم الإدارية*\nاختر القسم الذي تريد إدارته:", reply_markup=markup, parse_mode="Markdown")

    # ========== اختيار اللغة الأولية ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
    def callback_lang(call):
        lang = call.data.split('_')[1]
        set_lang(call.from_user.id, lang)
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, T[lang]["welcome_after_lang"].format(CHANNEL_PROOFS), parse_mode="Markdown")

    # ========== تغيير اللغة (قائمة اختيار) ==========
    @bot.message_handler(func=lambda msg: msg.text == T[get_lang(msg.from_user.id)].get("change_language", ""))
    def change_language_button(message):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        show_language_selector(user_id, lang)

    @bot.callback_query_handler(func=lambda call: call.data == "set_lang_ar")
    def set_lang_ar(call):
        user_id = call.from_user.id
        set_lang(user_id, 'ar')
        bot.answer_callback_query(call.id, "✅ تم تغيير اللغة إلى العربية")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message, 'ar')

    @bot.callback_query_handler(func=lambda call: call.data == "set_lang_en")
    def set_lang_en(call):
        user_id = call.from_user.id
        set_lang(user_id, 'en')
        bot.answer_callback_query(call.id, "✅ Language changed to English")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message, 'en')

    # ========== تغيير العملة (قائمة اختيار) ==========
    @bot.message_handler(func=lambda msg: msg.text == T[get_lang(msg.from_user.id)].get("change_currency", ""))
    def change_currency_button(message):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        show_currency_selector(user_id, lang)

    @bot.callback_query_handler(func=lambda call: call.data == "set_currency_mad")
    def set_currency_mad(call):
        user_id = call.from_user.id
        set_user_currency(user_id, 'mad')
        lang = get_lang(user_id)
        t = T[lang]
        bot.answer_callback_query(call.id, t["currency_changed"].format(t["currency_mad"]))
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message, lang)

    @bot.callback_query_handler(func=lambda call: call.data == "set_currency_usd")
    def set_currency_usd(call):
        user_id = call.from_user.id
        set_user_currency(user_id, 'usd')
        lang = get_lang(user_id)
        t = T[lang]
        bot.answer_callback_query(call.id, t["currency_changed"].format(t["currency_usd"]))
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message, lang)

    # ========== المعالج الرئيسي للرسائل النصية (مع دمج معالجة الإدارة) ==========
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

        # ========== الأولوية القصوى: التعامل مع الإدارة إذا كان المستخدم هو المالك وهناك عملية إدارة نشطة ==========
        if user_id == OWNER_ID and user_id in admin_temp:
            process_admin_text(bot, message)
            conn.close()
            return

        # معالجة السوشل ميديا
        if user_id in user_social_state:
            step = user_social_state[user_id].get('step')
            if message.text in ['/cancel_social', 'إلغاء', 'رجوع', 'Cancel', 'Back']:
                del user_social_state[user_id]
                bot.send_message(user_id, "❌ " + ("تم إلغاء طلب السوشل ميديا." if lang=='ar' else "Social media order canceled."))
                conn.close()
                return
            if step == 'awaiting_link':
                user_social_state[user_id]['link'] = message.text
                user_social_state[user_id]['step'] = 'awaiting_quantity'
                bot.send_message(user_id, t["social_send_quantity"])
                conn.close()
                return
            elif step == 'awaiting_quantity':
                try:
                    quantity = int(message.text)
                    if quantity < 1:
                        raise ValueError
                    user_social_state[user_id]['quantity'] = quantity
                    service = user_social_state[user_id]['selected_service']
                    original_price = float(service['rate'])
                    total_price_mad = calculate_price_with_profit(original_price * quantity)
                    user_social_state[user_id]['total_price'] = total_price_mad
                    platform_name = user_social_state[user_id].get('platform_name', '')
                    currency = get_user_currency(user_id)
                    if currency == 'usd':
                        total_price_display = round(total_price_mad / USD_TO_MAD, 2)
                        currency_symbol = "$"
                    else:
                        total_price_display = total_price_mad
                        currency_symbol = t.get("currency_mad", "درهم")
                    summary = t["social_order_summary"].format(
                        platform_name,
                        service['name'],
                        user_social_state[user_id]['link'],
                        quantity,
                        total_price_display,
                        currency_symbol
                    )
                    bot.send_message(user_id, summary, parse_mode="Markdown")
                    user_social_state[user_id]['step'] = 'awaiting_confirmation'
                    conn.close()
                    return
                except:
                    bot.send_message(user_id, t["social_invalid_quantity"])
                    conn.close()
                    return
            elif step == 'awaiting_confirmation':
                bot.send_message(user_id, "⚠️ " + ("يرجى تأكيد الطلب باستخدام /confirm_social أو إلغاؤه باستخدام /cancel_social" if lang=='ar' else "Please confirm with /confirm_social or cancel with /cancel_social"))
                conn.close()
                return

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
            show_social_platforms(user_id, lang)
            conn.close()
            return
        elif text == t["games_services"]:
            show_games_menu(message, lang)
        elif text == t["ff_services"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(t["keys_service"], t["ff_topup"])
            markup.add(t["back_to_games"])
            bot.send_message(message.chat.id, "🕹️ *" + t.get("choose_service", "اختر الخدمة:") + "*", reply_markup=markup, parse_mode="Markdown")
        elif text == t["shop_now"]:
            show_services_menu(message, lang)
        elif text == t["apps_service"]:
            show_apps_products(message, lang)
        elif text == t["ff_topup"]:
            show_ff_packages(message, lang)
        elif text == t["keys_service"]:
            show_keys_products(message, lang)
        elif text == t["back_to_main"]:
            show_main_menu(message, lang)
        elif text == t["back_to_sections"]:
            show_services_menu(message, lang)
        elif text == t["back_to_games"]:
            show_games_menu(message, lang)
        elif text == t["proofs"]:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(t.get("inline_proofs_btn", "📢 قناة الإثباتات"), url=CHANNEL_PROOFS))
            bot.send_message(message.chat.id, t["proofs_text"].format(CHANNEL_PROOFS), reply_markup=markup, parse_mode="Markdown")
        elif text == t["profile"]:
            c.execute("SELECT purchases, join_date, currency FROM users WHERE user_id=?", (user_id,))
            row = c.fetchone()
            purchases, join_date, currency = row
            if not purchases:
                purchases = "📭 " + ("لا توجد مشتريات بعد." if lang=='ar' else "No purchases yet.")
            currency_display = t["currency_usd"] if currency == 'usd' else t["currency_mad"]
            profile_msg = t["profile_text"].format(user_id, join_date, purchases) + f"\n💱 {t['current_currency'].format(currency_display)}"
            bot.send_message(message.chat.id, profile_msg, parse_mode="Markdown")
        elif text == t["support"]:
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(types.InlineKeyboardButton("💬 " + ("مراسلة المدير" if lang=='ar' else "Contact Manager"), url=ADMIN_CONTACT))
            markup.add(types.InlineKeyboardButton("📢 " + ("قناة المتجر" if lang=='ar' else "Store Channel"), url="https://chat.whatsapp.com/KhbuyOvojIX7FjKs7K0CfV"))
            markup.add(types.InlineKeyboardButton("⭐ " + ("إثباتات الثقة" if lang=='ar' else "Trust Proofs"), url=CHANNEL_PROOFS))
            bot.send_message(message.chat.id, t["support_text"], reply_markup=markup, parse_mode="Markdown")
        elif text == t["add_balance"]:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💳 " + ("مراسلة الدعم للشحن" if lang=='ar' else "Contact support for payment"), url=ADMIN_CONTACT))
            bot.send_message(message.chat.id, t["add_balance_text"], reply_markup=markup, parse_mode="Markdown")
        elif text == t["how_to_use"]:
            bot.send_message(message.chat.id, t["how_to_use_text"], parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, t["default_reply"].format(CHANNEL_PROOFS), parse_mode="Markdown")
        conn.close()

    # ========== كول باك السوشل ميديا ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_platform_'))
    def social_platform_selected(call):
        user_id = call.from_user.id
        platform_id = call.data.split('_')[2]
        lang = get_lang(user_id)
        if user_id in user_social_state:
            del user_social_state[user_id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_social_categories(user_id, platform_id, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_category_'))
    def social_category_selected(call):
        parts = call.data.split('_')
        platform_id = parts[2]
        category_name = '_'.join(parts[3:])
        user_id = call.from_user.id
        lang = get_lang(user_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_social_subcategories(user_id, platform_id, category_name, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_subcategory_'))
    def social_subcategory_selected(call):
        parts = call.data.split('_')
        platform_id = parts[2]
        category_name = parts[3]
        subcategory_name = '_'.join(parts[4:])
        user_id = call.from_user.id
        lang = get_lang(user_id)
        service_ids = get_service_ids_from_structure(platform_id, category_name, subcategory_name)
        if not service_ids:
            bot.answer_callback_query(call.id, "❌ " + ("لا توجد خدمات في هذا التصنيف." if lang=='ar' else "No services in this category."), show_alert=True)
            return
        services = get_services_by_ids(service_ids)
        if not services:
            bot.answer_callback_query(call.id, "❌ " + ("لا توجد خدمات متاحة حالياً." if lang=='ar' else "No services available."), show_alert=True)
            return
        platform_data = SOCIAL_STRUCTURE.get(platform_id, {})
        user_social_state[user_id] = {
            'platform_id': platform_id,
            'platform_name': platform_data.get('name', ''),
            'platform_icon': platform_data.get('icon', '📢'),
            'category_name': category_name,
            'subcategory_name': subcategory_name,
            'services': services,
            'step': 'selecting_service'
        }
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_services_list(user_id, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_service_'))
    def social_service_selected(call):
        service_id = int(call.data.split('_')[2])
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        data = user_social_state.get(user_id, {})
        services = data.get('services', [])
        service = next((s for s in services if s['service'] == service_id), None)
        if not service:
            bot.answer_callback_query(call.id, t["social_service_selected_error"], show_alert=True)
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        user_social_state[user_id]['selected_service'] = service
        user_social_state[user_id]['step'] = 'awaiting_link'
        bot.send_message(user_id, t["social_send_link"])
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_back_to_categories_'))
    def social_back_to_categories(call):
        parts = call.data.split('_')
        platform_id = parts[4]
        user_id = call.from_user.id
        lang = get_lang(user_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_social_categories(user_id, platform_id, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_back_to_subcategories_'))
    def social_back_to_subcategories(call):
        parts = call.data.split('_')
        platform_id = parts[4]
        category_name = '_'.join(parts[5:])
        user_id = call.from_user.id
        lang = get_lang(user_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_social_subcategories(user_id, platform_id, category_name, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "social_back_to_platforms")
    def social_back_to_platforms(call):
        user_id = call.from_user.id
        lang = get_lang(user_id)
        if user_id in user_social_state:
            del user_social_state[user_id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_social_platforms(user_id, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "social_cancel_all")
    def social_cancel_all(call):
        user_id = call.from_user.id
        if user_id in user_social_state:
            del user_social_state[user_id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, "❌ " + ("تم إلغاء جميع العمليات." if get_lang(user_id)=='ar' else "All operations cancelled."))
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "social_back_to_main")
    def social_back_to_main(call):
        user_id = call.from_user.id
        lang = get_lang(user_id)
        if user_id in user_social_state:
            del user_social_state[user_id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_main_menu(call.message, lang)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_games_menu")
    def back_to_games_menu(call):
        lang = get_lang(call.from_user.id)
        show_games_menu(call.message, lang)
        bot.answer_callback_query(call.id)

    # ========== أوامر السوشل ميديا ==========
    @bot.message_handler(commands=['confirm_social'])
    def confirm_social_order(message):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        if user_id not in user_social_state or user_social_state[user_id].get('step') != 'awaiting_confirmation':
            bot.send_message(user_id, "⚠️ " + ("لا يوجد طلب قيد الانتظار للتأكيد." if lang=='ar' else "No pending order to confirm."))
            return
        data = user_social_state[user_id]
        service = data.get('selected_service')
        link = data.get('link')
        quantity = data.get('quantity')
        total_price_mad = data.get('total_price')
        platform_name = data.get('platform_name', '')
        if not all([service, link, quantity, total_price_mad]):
            bot.send_message(user_id, "⚠️ " + ("البيانات ناقصة. يرجى إعادة اختيار الخدمة." if lang=='ar' else "Incomplete data. Please select the service again."))
            del user_social_state[user_id]
            return
        user_social_state[user_id]['temp_order'] = {
            'service': service,
            'link': link,
            'quantity': quantity,
            'total_price_mad': total_price_mad,
            'platform_name': platform_name
        }
        show_payment_methods(user_id, 'social', f"temp_{user_id}", total_price_mad)

    @bot.message_handler(commands=['cancel_social'])
    def cancel_social_order(message):
        user_id = message.from_user.id
        if user_id in user_social_state:
            del user_social_state[user_id]
            bot.send_message(user_id, "❌ " + ("تم إلغاء طلب السوشل ميديا." if get_lang(user_id)=='ar' else "Social media order canceled."))
        else:
            bot.send_message(user_id, "⚠️ " + ("لا يوجد طلب نشط لإلغائه." if get_lang(user_id)=='ar' else "No active order to cancel."))

    @bot.message_handler(commands=['social_status'])
    def social_status(message):
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "❗ " + ("الاستخدام: /social_status <api_order_id>" if get_lang(message.chat.id)=='ar' else "Usage: /social_status <api_order_id>"))
            return
        try:
            api_id = int(args[1])
        except:
            bot.send_message(message.chat.id, "❌ " + ("معرف الطلب يجب أن يكون رقماً." if get_lang(message.chat.id)=='ar' else "Order ID must be a number."))
            return
        status_data = get_order_status(api_id)
        if status_data and 'status' in status_data:
            msg = f"📊 *" + ("حالة الطلب" if get_lang(message.chat.id)=='ar' else "Order Status") + f" {api_id}:*\n📌 " + ("الحالة" if get_lang(message.chat.id)=='ar' else "Status") + f": {status_data.get('status')}\n💵 " + ("المتبقي" if get_lang(message.chat.id)=='ar' else "Remaining") + f": {status_data.get('remains',0)}\n⚡ " + ("بدء العد" if get_lang(message.chat.id)=='ar' else "Start count") + f": {status_data.get('start_count',0)}"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ " + ("لم نتمكن من جلب حالة الطلب." if get_lang(message.chat.id)=='ar' else "Could not fetch order status."))

    # ========== شراء الجواهر (للقائمة البيضاء والدفع) ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def process_purchase(call):
        pkg = call.data.split('_')[1]
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        code = get_ff_code(pkg)
        if not code:
            bot.answer_callback_query(call.id, t["out_of_stock"], show_alert=True)
            return
        if is_whitelisted(user_id):
            currency = get_user_currency(user_id)
            if currency == 'usd':
                price_display = round(int(prices[pkg]) / USD_TO_MAD, 2)
                currency_symbol = "$"
            else:
                price_display = int(prices[pkg])
                currency_symbol = t.get("currency_mad", "درهم")
            msg = t["purchase_success"].format(pkg, price_display, currency_symbol, code, ADMIN_CONTACT, CHANNEL_PROOFS)
            bot.send_message(user_id, msg, parse_mode="Markdown")
            add_purchase_record(user_id, f"📦 {pkg}💎 ({prices[pkg]} DH): {code} - {datetime.now()}")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'ff', pkg, code, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, f"{pkg} جوهرة", prices[pkg], code_or_link=code)
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, f"🔄 الوكيل @{call.from_user.username} سحب {pkg} جوهرة (كود: {code})")
                except:
                    pass
            bot.answer_callback_query(call.id, t["confirm_purchase"])
        else:
            show_payment_methods(user_id, 'ff', pkg, int(prices[pkg]))
            bot.answer_callback_query(call.id)

    # ========== اختيار مدة المفتاح ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('key_prod_'))
    def choose_duration(call):
        prod_id = call.data.split('_')[2]
        lang = get_lang(call.from_user.id)
        t = T[lang]
        prod_data = keys_inventory.get(prod_id)
        if not prod_data:
            bot.answer_callback_query(call.id, "❌ " + ("المنتج غير موجود" if lang=='ar' else "Product not found"), show_alert=True)
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        for days, price_mad in prod_data["prices"].items():
            currency = get_user_currency(call.from_user.id)
            if currency == 'usd':
                price_display = round(price_mad / USD_TO_MAD, 2)
                currency_symbol = "$"
            else:
                price_display = price_mad
                currency_symbol = t.get("currency_mad", "درهم")
            markup.add(types.InlineKeyboardButton(f"{days} DAYS = {price_display} {currency_symbol} 💰", callback_data=f"key_buy_{prod_id}_{days}_{price_mad}"))
        markup.add(types.InlineKeyboardButton(t["back_to_products"], callback_data="back_to_key_products"))
        bot.send_message(call.message.chat.id, t["choose_validity"], reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    @bot.callback_query_handler(func=lambda call: call.data.startswith('key_buy_'))
    def handle_key_buy(call):
        parts = call.data.split('_')
        if len(parts) < 5:
            bot.answer_callback_query(call.id, "❌ " + ("خطأ" if get_lang(call.from_user.id)=='ar' else "Error"), show_alert=True)
            return
        prod_id = parts[2]
        days = parts[3]
        try:
            price_mad = int(parts[4])
        except:
            bot.answer_callback_query(call.id, "❌ " + ("خطأ في السعر" if get_lang(call.from_user.id)=='ar' else "Price error"), show_alert=True)
            return
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        code = get_key_code(prod_id, days)
        if not code:
            bot.answer_callback_query(call.id, t["no_stock"], show_alert=True)
            return
        if is_whitelisted(user_id):
            product_name = keys_inventory[prod_id]["name_ar"] if lang == 'ar' else keys_inventory[prod_id]["name_en"]
            currency = get_user_currency(user_id)
            if currency == 'usd':
                price_display = round(price_mad / USD_TO_MAD, 2)
                currency_symbol = "$"
            else:
                price_display = price_mad
                currency_symbol = t.get("currency_mad", "درهم")
            msg = t["keys_purchase_success"].format(product_name, days, price_display, currency_symbol, code, ADMIN_CONTACT, CHANNEL_PROOFS)
            bot.send_message(user_id, msg, parse_mode="Markdown")
            add_purchase_record(user_id, f"🔑 {product_name} ({days} يوم): {code} - {datetime.now()}")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'key', f"{prod_id}_{days}", code, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, product_name, price_mad, extra_info=f"🗓️ المدة: {days} يوم\n", code_or_link=code)
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, f"🔄 الوكيل @{call.from_user.username} سحب مفتاح {product_name} مدة {days} أيام (كود: {code})")
                except:
                    pass
            bot.answer_callback_query(call.id, t["confirm_purchase"])
        else:
            show_payment_methods(user_id, 'key', f"dripclient_{days}", price_mad)
            bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('app_buy_'))
    def process_app_purchase(call):
        app_id = call.data.split('_')[2]
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        app_data = apps_inventory.get(app_id)
        if not app_data:
            bot.answer_callback_query(call.id, t["app_no_stock"], show_alert=True)
            return
        if is_whitelisted(user_id):
            product_name = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
            download_link = app_data.get("link", "")
            channel_link = app_data.get("update_channel", "")
            price_mad = app_data["price"]
            currency = get_user_currency(user_id)
            if currency == 'usd':
                price_display = round(price_mad / USD_TO_MAD, 2)
                currency_symbol = "$"
            else:
                price_display = price_mad
                currency_symbol = t.get("currency_mad", "درهم")
            msg = t["order_accepted"].format(product_name, price_display, currency_symbol, download_link, channel_link, ADMIN_CONTACT, CHANNEL_PROOFS)
            bot.send_message(user_id, msg, parse_mode="Markdown")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'app', app_id, download_link, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, product_name, price_mad, extra_info=f"📢 قناة التحديثات: [انضم]({channel_link})\n", code_or_link=download_link)
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, f"🔄 الوكيل @{call.from_user.username} سحب تطبيق {product_name}")
                except:
                    pass
            bot.answer_callback_query(call.id, "🎉 " + ("تم تسليم التطبيق بنجاح!" if lang=='ar' else "App delivered successfully!"))
        else:
            show_payment_methods(user_id, 'app', app_id, app_data["price"])
            bot.answer_callback_query(call.id)

    # ========== معالجات الدفع الرئيسية ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
    def handle_payment_method(call):
        parts = call.data.split('_', 4)
        if len(parts) < 5:
            bot.answer_callback_query(call.id, "❌ " + ("خطأ في البيانات" if get_lang(call.from_user.id)=='ar' else "Data error"), show_alert=True)
            return
        method_key, product_type, product_id, amount_str = parts[1], parts[2], parts[3], parts[4]
        amount = float(amount_str)
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        c.execute("SELECT order_id FROM orders WHERE user_id=? AND status IN ('pending', 'waiting_admin')", (user_id,))
        if c.fetchone():
            bot.answer_callback_query(call.id, t["already_paid"], show_alert=True)
            conn.close()
            return
        conn.close()
        order_id = None
        if product_type == 'ff':
            order_id = create_order(user_id, 'ff', product_id, amount)
        elif product_type == 'key':
            order_id = create_order(user_id, 'key', product_id, amount)
        elif product_type == 'app':
            order_id = create_order(user_id, 'app', product_id, amount)
        elif product_type == 'social':
            if user_id in user_social_state and 'temp_order' in user_social_state[user_id]:
                temp = user_social_state[user_id]['temp_order']
                api_payload = f"social|{temp['service']['service']}|{temp['link']}|{temp['quantity']}"
                order_id = create_order(user_id, 'social', api_payload, float(temp['total_price_mad']))
                del user_social_state[user_id]['temp_order']
            else:
                bot.answer_callback_query(call.id, "❌ " + ("بيانات غير مكتملة" if lang=='ar' else "Incomplete data"), show_alert=True)
                return
        else:
            bot.answer_callback_query(call.id, "❌ " + ("نوع منتج غير معروف" if lang=='ar' else "Unknown product type"), show_alert=True)
            return
        method = PAYMENT_METHODS.get(method_key)
        if not method:
            bot.answer_callback_query(call.id, "❌ " + ("طريقة دفع غير معروفة" if lang=='ar' else "Unknown payment method"), show_alert=True)
            return
        currency = get_user_currency(user_id)
        if currency == 'usd':
            amount_display = round(amount / USD_TO_MAD, 2)
            currency_symbol = "$"
        else:
            amount_display = amount
            currency_symbol = t.get("currency_mad", "درهم")
        instructions = (f"<b>{t['payment_method_label']}</b> {method['name_ar'] if lang=='ar' else method['name_en']}\n"
                        f"━━━━━━━━━━━━\n{method['details_ar'] if lang=='ar' else method['details_en']}\n\n"
                        f"<b>{t['amount']}</b> {amount_display} {currency_symbol}\n"
                        f"<b>{t['order_id_label']}</b> <code>{order_id}</code>\n\n"
                        f"{t['payment_instructions']}")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📸 " + ("أرسل الإيصال" if lang=='ar' else "Send receipt"), callback_data=f"send_proof_{order_id}"))
        markup.add(types.InlineKeyboardButton("🔄 " + ("تغيير طريقة الدفع" if lang=='ar' else "Change payment method"), callback_data=f"change_payment_{order_id}"))
        bot.edit_message_text(instructions, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('change_payment_'))
    def change_payment_method(call):
        order_id = call.data.split('_', 2)[2]
        user_id = call.from_user.id
        order = get_order(order_id)
        lang = get_lang(user_id)
        t = T[lang]
        if not order or order[1] != user_id or order[5] not in ('pending', 'waiting_admin', 'rejected'):
            bot.answer_callback_query(call.id, "❌ " + ("لا يمكن تغيير طريقة الدفع الآن" if lang=='ar' else "Cannot change payment method now"), show_alert=True)
            return
        update_order_status(order_id, 'cancelled', admin_action='user_cancelled')
        product_type, product_id, amount = order[2], order[3], order[4]
        show_payment_methods(user_id, product_type, product_id, amount)
        bot.answer_callback_query(call.id, "✅ " + ("يمكنك اختيار طريقة دفع جديدة" if lang=='ar' else "You can choose a new payment method"))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('send_proof_'))
    def ask_for_proof(call):
        order_id = call.data.split('_', 2)[2]
        lang = get_lang(call.from_user.id)
        t = T[lang]
        bot.answer_callback_query(call.id)
        bot.send_message(call.from_user.id, t["ask_proof"], parse_mode="Markdown")
        bot.register_next_step_handler_by_chat_id(call.from_user.id, lambda msg: process_proof_photo(msg, order_id))

    def process_proof_photo(message, order_id):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        if not message.photo:
            bot.send_message(user_id, "❌ " + ("يرجى إرسال صورة وليس نصاً. أعد المحاولة." if lang=='ar' else "Please send a photo, not text. Try again."))
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: process_proof_photo(msg, order_id))
            return
        waiting_msg = bot.send_message(user_id, t["proof_received"], parse_mode="Markdown")
        photo_id = message.photo[-1].file_id
        update_order_status(order_id, 'waiting_admin', proof_photo_id=photo_id)
        order = get_order(order_id)
        if not order:
            bot.send_message(user_id, "❌ " + ("حدث خطأ في الطلب." if lang=='ar' else "Order error."))
            return
        product_type, product_id, amount = order[2], order[3], order[4]
        if product_type == 'ff':
            product_name = f"جواهر فري فاير ({product_id} جوهرة)"
        elif product_type == 'key':
            parts = product_id.split('_')
            product_name = f"مفتاح DRIP CLIENT - {parts[1] if len(parts)>1 else product_id} يوم"
        elif product_type == 'app':
            app_data = apps_inventory.get(product_id, {})
            product_name = app_data.get("name_ar", "تطبيق") if lang == 'ar' else app_data.get("name_en", "App")
        elif product_type == 'social':
            product_name = "خدمة سوشل ميديا"
        else:
            product_name = "منتج غير معروف"
        admin_msg = (f"<b>🔔 طلب دفع جديد</b>\n━━━━━━━━━━━━\n"
                     f"<b>🆔 الطلب:</b> <code>{order_id}</code>\n"
                     f"<b>👤 المستخدم:</b> @{message.from_user.username}\n"
                     f"<b>📦 المنتج:</b> {product_name}\n"
                     f"<b>💰 المبلغ:</b> {amount} درهم\n"
                     f"<b>📸 <a href='tg://user?id={user_id}'>إثبات الدفع</a></b>")
        markup_admin = types.InlineKeyboardMarkup(row_width=2)
        markup_admin.add(
            types.InlineKeyboardButton("✅ قبول الطلب", callback_data=f"admin_accept_{order_id}"),
            types.InlineKeyboardButton("❌ رفض الطلب", callback_data=f"admin_reject_{order_id}")
        )
        for admin in ADMIN_IDS:
            try:
                bot.send_photo(admin, photo_id, caption=admin_msg, reply_markup=markup_admin, parse_mode="HTML")
            except:
                pass
        bot.edit_message_text("📸 " + ("تم استلام إثبات الدفع! سيتم مراجعته من قبل الإدارة قريباً." if lang=='ar' else "Payment proof received! It will be reviewed by admin soon."), chat_id=user_id, message_id=waiting_msg.message_id, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_accept_'))
    def admin_accept_order(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ " + ("غير مسموح" if get_lang(call.from_user.id)=='ar' else "Not allowed"), show_alert=True)
            return
        order_id = call.data.split('_', 2)[2]
        finalize_order(order_id, accepted=True, admin_id=call.from_user.id)
        bot.answer_callback_query(call.id, "✅ " + ("تم قبول الطلب" if get_lang(call.from_user.id)=='ar' else "Order accepted"))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_reject_'))
    def admin_reject_order(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "❌ " + ("غير مسموح" if get_lang(call.from_user.id)=='ar' else "Not allowed"), show_alert=True)
            return
        order_id = call.data.split('_', 2)[2]
        finalize_order(order_id, accepted=False, admin_id=call.from_user.id)
        bot.answer_callback_query(call.id, "❌ " + ("تم رفض الطلب" if get_lang(call.from_user.id)=='ar' else "Order rejected"))

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_key_products")
    def back_to_key_products(call):
        lang = get_lang(call.from_user.id)
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for prod_id, prod_data in keys_inventory.items():
            btn_text = prod_data["name_ar"] if lang == 'ar' else prod_data["name_en"]
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"key_prod_{prod_id}"))
        bot.edit_message_text(t["choose_product"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    # ========== تسجيل معالجات لوحة التحكم الإدارية ==========
    register_admin_handlers(bot)
