# handlers.py
# الملف الموحد النهائي لجميع معالجات البوت
# تمت إضافة: زر تغيير اللغة وزر تغيير العملة

import telebot
from telebot import types
import sqlite3
from datetime import datetime
import time
from config import (
    ADMIN_IDS, WHITELISTED_USERS, STORE_PASSWORD, CHANNEL_PROOFS, ADMIN_CONTACT,
    codes_inventory, prices, keys_inventory, apps_inventory, LOG_CHANNEL_ID,
    USD_TO_MAD, DEFAULT_CURRENCY
)
from database import (
    get_lang, set_lang, get_verified_count, add_purchase_record,
    create_order, update_order_status, get_order
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

# ========== متغير عام ==========
user_social_state = {}

# ========== دالة مساعدة لجلب عملة المستخدم ==========
def get_user_currency(user_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT currency FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0] in ['mad', 'usd']:
        return row[0]
    return DEFAULT_CURRENCY

# ========== دالة مساعدة لتحديث عملة المستخدم ==========
def set_user_currency(user_id, currency):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE users SET currency = ? WHERE user_id=?", (currency, user_id))
    conn.commit()
    conn.close()

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
        markup.row(t["how_to_use"], t["support"])
        markup.row(t["proofs"])
        # ✅ إضافة زر اللغة والعملة في صف جديد
        markup.row(t["change_language"], t["change_currency"])
        user_count = get_verified_count()
        msg = t["welcome_main"].format(message.from_user.first_name, CHANNEL_PROOFS) + t["user_count"].format(user_count)
        bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

    def show_services_menu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["games_services"], t["social_media"])
        markup.add(t["apps_service"], t["back_to_main"])
        bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")

    def show_games_menu(message, lang):
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["ff_services"])
        markup.add(t["back_to_sections"])
        bot.send_message(message.chat.id, "🎮 *اختر اللعبة:*", reply_markup=markup, parse_mode="Markdown")

    def show_ff_packages(message, lang):
        t = T[lang]
        user_id = message.from_user.id
        currency = get_user_currency(user_id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pkg in codes_inventory:
            if codes_inventory[pkg]:
                price_mad = int(prices[pkg])
                if currency == 'usd':
                    price_display = round(price_mad / USD_TO_MAD, 2)
                    currency_symbol = "$"
                else:
                    price_display = price_mad
                    currency_symbol = "درهم"
                markup.add(types.InlineKeyboardButton(f"💎 {pkg} {'جوهرة' if lang=='ar' else 'diamonds'} = {price_display} {currency_symbol}", callback_data=f"buy_{pkg}"))
        markup.add(types.InlineKeyboardButton("📢 " + ("شاهد الإثباتات قبل الشراء" if lang=='ar' else "See proofs before buying"), url=CHANNEL_PROOFS))
        markup.add(types.InlineKeyboardButton(t["back_to_games"], callback_data="back_to_games_menu"))
        bot.send_message(message.chat.id, t["ff_packages_title"], reply_markup=markup, parse_mode="Markdown")

    def show_keys_products(message, lang):
        t = T[lang]
        user_id = message.from_user.id
        currency = get_user_currency(user_id)
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
                currency_symbol = "درهم"
            markup.add(types.InlineKeyboardButton(f"{btn_text} - {price_display} {currency_symbol}", callback_data=f"app_buy_{app_id}"))
        bot.send_message(message.chat.id, t["choose_app"], reply_markup=markup, parse_mode="Markdown")

    def show_payment_methods(user_id, product_type, product_id, amount):
        lang = get_lang(user_id)
        currency = get_user_currency(user_id)
        t = T[lang]
        # تحويل المبلغ إلى العملة المختارة (المبلغ قادم بالدرهم)
        if currency == 'usd':
            amount_display = round(amount / USD_TO_MAD, 2)
            currency_symbol = "$"
        else:
            amount_display = amount
            currency_symbol = "درهم"
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, method in PAYMENT_METHODS.items():
            name = method["name_ar"] if lang == 'ar' else method["name_en"]
            markup.add(types.InlineKeyboardButton(name, callback_data=f"pay_{key}_{product_type}_{product_id}_{amount}"))
        # نرسل المبلغ الأصلي (بالدرهم) في callback، لكن نعرضه بالعملة المختارة
        bot.send_message(user_id, t["choose_payment"].format(amount_display, currency_symbol), reply_markup=markup, parse_mode="Markdown")

    def purchase_ff_package(user_id, pkg, lang):
        amount = prices[pkg]
        show_payment_methods(user_id, 'ff', pkg, amount)

    def purchase_key(user_id, days, lang):
        price = keys_inventory['dripclient']['prices'][days]
        show_payment_methods(user_id, 'key', f"dripclient_{days}", price)

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
                if product_id in codes_inventory and codes_inventory[product_id]:
                    code = codes_inventory[product_id].pop(0)
                    success_msg = t["purchase_success"].format(product_id, amount, code, ADMIN_CONTACT, CHANNEL_PROOFS)
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
                    if key_id in keys_inventory and days in keys_inventory[key_id]["codes"] and keys_inventory[key_id]["codes"][days]:
                        code = keys_inventory[key_id]["codes"][days].pop(0)
                        product_name = keys_inventory[key_id]["name_ar"] if lang == 'ar' else keys_inventory[key_id]["name_en"]
                        success_msg = t["keys_purchase_success"].format(product_name, days, amount, code, ADMIN_CONTACT, CHANNEL_PROOFS)
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
                    success_msg = t["order_accepted"].format(product_name, amount, download_link, channel_link, ADMIN_CONTACT, CHANNEL_PROOFS)
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
            markup.add(types.InlineKeyboardButton("🔄 تغيير طريقة الدفع", callback_data=f"change_payment_{order_id}"))
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
        markup.add(types.InlineKeyboardButton("🔙 العودة", callback_data="social_back_to_main"))
        bot.send_message(user_id, t["social_choose_platform"], reply_markup=markup, parse_mode="Markdown")

    def show_social_categories(user_id, platform_id, lang):
        t = T[lang]
        platform_data = SOCIAL_STRUCTURE.get(platform_id)
        if not platform_data:
            bot.send_message(user_id, "⚠️ منصة غير معروفة.")
            return
        categories = get_categories_list(platform_id)
        if not categories:
            bot.send_message(user_id, "⚠️ لا توجد خدمات متاحة لهذه المنصة حالياً.")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for cat_name, cat_icon in categories:
            btn_text = f"{cat_icon} {cat_name}"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_category_{platform_id}_{cat_name}"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع للمنصات", callback_data="social_back_to_platforms"))
        bot.send_message(user_id, f"{platform_data['icon']} *منصة: {platform_data['name']}*\n{t['social_select_category']}", reply_markup=markup, parse_mode="Markdown")

    def show_social_subcategories(user_id, platform_id, category_name, lang):
        t = T[lang]
        platform_data = SOCIAL_STRUCTURE.get(platform_id)
        subcategories = get_subcategories_list(platform_id, category_name)
        service_ids = get_service_ids_from_structure(platform_id, category_name)
        if not service_ids:
            bot.send_message(user_id, "⚠️ لا توجد خدمات في هذا التصنيف.")
            return
        services = get_services_by_ids(service_ids)
        if not services:
            bot.send_message(user_id, "⚠️ لا توجد خدمات متاحة حالياً.")
            return
        if subcategories:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for sub_name, sub_icon in subcategories:
                btn_text = f"{sub_icon} {sub_name}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_subcategory_{platform_id}_{category_name}_{sub_name}"))
            markup.add(types.InlineKeyboardButton("🔙 رجوع للتصنيفات", callback_data=f"social_back_to_categories_{platform_id}"))
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
            bot.send_message(user_id, "⚠️ لا توجد خدمات.")
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
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data=back_callback))
        bot.send_message(user_id, f"{data.get('platform_icon', '📢')} *اختر الخدمة:*", reply_markup=markup, parse_mode="Markdown")

    # ========== معالج /start ==========
    @bot.message_handler(commands=['start'])
    def start(message):
        user_id = message.from_user.id
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        # التحقق من وجود عمود currency، وإضافته إذا لم يكن موجوداً (ترقية قاعدة البيانات)
        try:
            c.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'mad'")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # العمود موجود بالفعل
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

    # ========== معالج اختيار اللغة ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
    def callback_lang(call):
        lang = call.data.split('_')[1]
        set_lang(call.from_user.id, lang)
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, T[lang]["welcome_after_lang"].format(CHANNEL_PROOFS), parse_mode="Markdown")

    # ========== معالج تغيير اللغة (بدون صورة) ==========
    @bot.message_handler(func=lambda msg: msg.text == T[get_lang(msg.from_user.id)].get("change_language", ""))
    def change_language(message):
        user_id = message.from_user.id
        current_lang = get_lang(user_id)
        new_lang = 'en' if current_lang == 'ar' else 'ar'
        set_lang(user_id, new_lang)
        t = T[new_lang]
        bot.send_message(user_id, t["language_changed"])
        show_main_menu(message, new_lang)

    # ========== معالج تغيير العملة ==========
    @bot.message_handler(func=lambda msg: msg.text == T[get_lang(msg.from_user.id)].get("change_currency", ""))
    def change_currency(message):
        user_id = message.from_user.id
        current_currency = get_user_currency(user_id)
        new_currency = 'usd' if current_currency == 'mad' else 'mad'
        set_user_currency(user_id, new_currency)
        lang = get_lang(user_id)
        t = T[lang]
        currency_name = t["currency_usd"] if new_currency == 'usd' else t["currency_mad"]
        bot.send_message(user_id, t["currency_changed"].format(currency_name))
        show_main_menu(message, lang)  # إعادة عرض القائمة لتحديث العملة

    # ========== المعالج الرئيسي للرسائل النصية (الأزرار والنصوص) ==========
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

        # ** معالجة حالة السوشل ميديا (الرابط والكمية) **
        if user_id in user_social_state:
            current_step = user_social_state[user_id].get('step')
            # إذا كان المستخدم يريد الإلغاء في أي خطوة
            if message.text in ['/cancel_social', 'إلغاء', 'رجوع']:
                del user_social_state[user_id]
                bot.send_message(user_id, "❌ تم إلغاء طلب السوشل ميديا. يمكنك البدء من جديد.")
                conn.close()
                return

            if current_step == 'awaiting_link':
                user_social_state[user_id]['link'] = message.text
                user_social_state[user_id]['step'] = 'awaiting_quantity'
                bot.send_message(user_id, t["social_send_quantity"])
                conn.close()
                return

            elif current_step == 'awaiting_quantity':
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
                    # تحويل السعر للعرض بالعملة المختارة
                    currency = get_user_currency(user_id)
                    if currency == 'usd':
                        total_price_display = round(total_price_mad / USD_TO_MAD, 2)
                        currency_symbol = "$"
                    else:
                        total_price_display = total_price_mad
                        currency_symbol = "درهم"
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
                except ValueError:
                    bot.send_message(user_id, t["social_invalid_quantity"])
                    conn.close()
                    return
                except Exception as e:
                    print(f"خطأ في معالجة الكمية: {e}")
                    bot.send_message(user_id, "❌ حدث خطأ أثناء معالجة الكمية. حاول مرة أخرى.")
                    conn.close()
                    return

            elif current_step == 'awaiting_confirmation':
                # في حالة كتابة أي نص آخر وهو في انتظار التأكيد، نذكره بالأوامر
                bot.send_message(user_id, "⚠️ يرجى تأكيد الطلب باستخدام /confirm_social أو إلغاؤه باستخدام /cancel_social")
                conn.close()
                return

        # إذا لم يكن في حالة سوشل ميديا، نكمل معالجة الأزرار العادية
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
            bot.send_message(message.chat.id, "🕹️ *خدمات فري فاير:*\n━━━━━━━━━━━━\nاختر الخدمة:", reply_markup=markup, parse_mode="Markdown")
        elif text == t["shop_now"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(t["games_services"], t["social_media"])
            markup.add(t["apps_service"], t["back_to_main"])
            bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")
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
            currency_display = "الدولار (USD)" if currency == 'usd' else "الدرهم (MAD)"
            profile_msg = t["profile_text"].format(user_id, join_date, purchases) + f"\n💱 العملة المختارة: {currency_display}"
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

    # باقي الكود (كول باك السوشل ميديا، أوامر التأكيد، شراء الجواهر، المفاتيح، التطبيقات، نظام الدفع) لم يتغير
    # ... (تم حذف التكرار للاختصار، ولكن في الملف الكامل يجب أن تبقى كما هي)
