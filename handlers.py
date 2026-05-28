# handlers.py
# جميع معالجات البوت (Callbacks, Message handlers, Commands)

import telebot
from telebot import types
import sqlite3
from datetime import datetime
import time
from config import (
    ADMIN_IDS, WHITELISTED_USERS, STORE_PASSWORD, CHANNEL_PROOFS, ADMIN_CONTACT,
    codes_inventory, prices, keys_inventory, apps_inventory, LOG_CHANNEL_ID
)
from database import (
    get_lang, set_lang, get_verified_count, add_purchase_record,
    create_order, update_order_status, get_order, save_social_order
)
from utils import is_admin, is_whitelisted
from payment_methods import PAYMENT_METHODS
from languages import T
from social_api import get_services, add_order, get_order_status, calculate_price_with_profit

# متغيرات مؤقتة لحالة المستخدمين أثناء طلب خدمات السوشل ميديا
user_social_temp = {}

# متغير لتخزين الخدمات مع التخزين المؤقت وتقسيم الصفحات
services_cache = None
services_cache_time = 0
SERVICES_CACHE_TTL = 300  # 5 دقائق
SERVICES_PER_PAGE = 10

def get_services_cached():
    global services_cache, services_cache_time
    now = time.time()
    if services_cache is None or now - services_cache_time > SERVICES_CACHE_TTL:
        services_cache = get_services()
        services_cache_time = now
    return services_cache

def register_all_handlers(bot):
    """تسجيل جميع معالجات البوت (يتم استدعاؤها من main.py)"""
    
    # ========== دوال مساعدة داخلية ==========
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
        markup.add(t["other_games"], t["ff_services"])
        markup.add(t["social_media"], t["apps_service"])
        markup.add(t["back_to_main"])
        bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")

    def show_ff_packages(message, lang):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pkg in codes_inventory:
            if codes_inventory[pkg]:
                price = prices[pkg]
                markup.add(types.InlineKeyboardButton(f"💎 {pkg} {'جوهرة' if lang=='ar' else 'diamonds'} = {price} {'درهم' if lang=='ar' else 'MAD'}", callback_data=f"buy_{pkg}"))
        markup.add(types.InlineKeyboardButton("📢 " + ("شاهد الإثباتات قبل الشراء" if lang=='ar' else "See proofs before buying"), url=CHANNEL_PROOFS))
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
        markup = types.InlineKeyboardMarkup(row_width=2)
        for app_id, app_data in apps_inventory.items():
            btn_text = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"app_buy_{app_id}"))
        bot.send_message(message.chat.id, t["choose_app"], reply_markup=markup, parse_mode="Markdown")

    def show_payment_methods(user_id, product_type, product_id, amount):
        lang = get_lang(user_id)
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, method in PAYMENT_METHODS.items():
            name = method["name_ar"] if lang == 'ar' else method["name_en"]
            markup.add(types.InlineKeyboardButton(name, callback_data=f"pay_{key}_{product_type}_{product_id}_{amount}"))
        bot.send_message(user_id, t["choose_payment"], reply_markup=markup, parse_mode="Markdown")

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
        else:
            # رفض الطلب
            if product_type == 'ff':
                product_name = f"جواهر فري فاير ({product_id} جوهرة)"
            elif product_type == 'key':
                parts = product_id.split('_')
                product_name = f"مفتاح DRIP CLIENT - {parts[1] if len(parts)>1 else product_id} يوم"
            else:
                app_data = apps_inventory.get(product_id, {})
                product_name = app_data.get("name_ar", "تطبيق") if lang == 'ar' else app_data.get("name_en", "App")
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

        # التعامل مع الحالة المؤقتة لطلب سوشل ميديا
        if user_id in user_social_temp:
            state = user_social_temp[user_id].get('state')
            if state == 'awaiting_link':
                user_social_temp[user_id]['link'] = message.text
                user_social_temp[user_id]['state'] = 'awaiting_quantity'
                bot.send_message(user_id, t["social_send_quantity"])
                conn.close()
                return
            elif state == 'awaiting_quantity':
                try:
                    quantity = int(message.text)
                    if quantity < 1:
                        raise ValueError
                    user_social_temp[user_id]['quantity'] = quantity
                    service = user_social_temp[user_id]['service']
                    original_price = float(service['rate'])
                    total_price = calculate_price_with_profit(original_price * quantity)
                    user_social_temp[user_id]['total_price'] = total_price
                    msg = t["social_price_calc"].format(total_price)
                    bot.send_message(user_id, msg, parse_mode="Markdown")
                    conn.close()
                    return
                except ValueError:
                    bot.send_message(user_id, "❌ يرجى إدخال رقم صحيح للكمية.")
                    conn.close()
                    return

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

        # قائمة الخدمات (services) - تم تعديلها لتظهر زر السوشل ميديا
        if text == t["services"]:
            show_services_menu(message, lang)
        elif text == t["social_media"]:
            # عرض خدمات السوشل ميديا بالصفحات
            loading_msg = bot.send_message(user_id, t["social_loading"])
            services = get_services_cached()
            if services and isinstance(services, list):
                if user_id not in user_social_temp:
                    user_social_temp[user_id] = {}
                user_social_temp[user_id]['services_list'] = services
                user_social_temp[user_id]['services_page'] = 0
                show_services_page(user_id, lang, 0)
                bot.delete_message(user_id, loading_msg.message_id)
            else:
                bot.edit_message_text("⚠️ لا يمكن تحميل الخدمات حالياً. حاول لاحقاً.", user_id, loading_msg.message_id)
            conn.close()
            return
        elif text == t["shop_now"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(t["other_games"], t["ff_services"])
            markup.add(t["back_to_main"], t["apps_service"])
            bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")
        elif text == t["ff_services"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(t["keys_service"], t["ff_topup"])
            markup.add(t["back_to_sections"])
            bot.send_message(message.chat.id, "🎮 *خدمات فري فاير:*\n━━━━━━━━━━━━\nاختر الخدمة:", reply_markup=markup, parse_mode="Markdown")
        elif text == t["other_games"]:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(t["back_to_sections"])
            bot.send_message(message.chat.id, t["other_games_text"], reply_markup=markup, parse_mode="Markdown")
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

    # دالة عرض صفحة الخدمات مع أزرار التنقل
    def show_services_page(user_id, lang, page):
        t = T[lang]
        data = user_social_temp.get(user_id, {})
        services = data.get('services_list', [])
        if not services:
            bot.send_message(user_id, "❌ لا توجد خدمات متاحة.")
            return
        total_pages = (len(services) - 1) // SERVICES_PER_PAGE + 1
        start = page * SERVICES_PER_PAGE
        end = start + SERVICES_PER_PAGE
        page_services = services[start:end]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for svc in page_services:
            btn_text = f"{svc['name']} - {svc['rate']} USD"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"social_svc_{svc['service']}_{page}"))
        # أزرار التنقل
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("◀️ السابق", callback_data=f"social_page_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("التالي ▶️", callback_data=f"social_page_{page+1}"))
        if nav_buttons:
            markup.row(*nav_buttons)
        markup.add(types.InlineKeyboardButton("🔙 إلغاء", callback_data="social_cancel"))
        bot.send_message(user_id, t["social_choose_service"], reply_markup=markup, parse_mode="Markdown")

    # معالج التنقل بين الصفحات
    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_page_'))
    def social_change_page(call):
        user_id = call.from_user.id
        page = int(call.data.split('_')[2])
        lang = get_lang(user_id)
        if user_id not in user_social_temp or 'services_list' not in user_social_temp[user_id]:
            bot.answer_callback_query(call.id, "انتهت الجلسة، يرجى اختيار الخدمات من القائمة الرئيسية.")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            return
        user_social_temp[user_id]['services_page'] = page
        bot.delete_message(call.message.chat.id, call.message.message_id)
        show_services_page(user_id, lang, page)
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "social_cancel")
    def social_cancel(call):
        user_id = call.from_user.id
        if user_id in user_social_temp:
            del user_social_temp[user_id]
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, "❌ تم إلغاء اختيار الخدمة.")
        bot.answer_callback_query(call.id)

    # معالج اختيار خدمة من الصفحة
    @bot.callback_query_handler(func=lambda call: call.data.startswith('social_svc_'))
    def social_choose_service(call):
        parts = call.data.split('_')
        service_id = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        services = get_services_cached()
        if not services:
            bot.answer_callback_query(call.id, "⚠️ خطأ في تحميل الخدمات", show_alert=True)
            return
        service = next((s for s in services if s['service'] == service_id), None)
        if not service:
            bot.answer_callback_query(call.id, "❌ الخدمة غير موجودة", show_alert=True)
            return
        user_social_temp[user_id] = {
            'service': service,
            'state': 'awaiting_link'
        }
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, t["social_send_link"])
        bot.answer_callback_query(call.id)

    # ========== أوامر السوشل ميديا ==========
    @bot.message_handler(commands=['confirm_social'])
    def confirm_social_order(message):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        if user_id not in user_social_temp or 'service' not in user_social_temp[user_id]:
            bot.send_message(user_id, "⚠️ لا يوجد طلب قيد الانتظار. ابدأ باختيار خدمة من قسم السوشل ميديا.")
            return
        data = user_social_temp[user_id]
        service = data['service']
        link = data.get('link')
        quantity = data.get('quantity')
        if not link or not quantity:
            bot.send_message(user_id, "⚠️ البيانات ناقصة. يرجى إعادة اختيار الخدمة.")
            del user_social_temp[user_id]
            return
        # إنشاء طلب في API
        result = add_order(service['service'], link, quantity)
        if result and 'order' in result:
            api_order_id = result['order']
            total_price = data.get('total_price', 0)
            save_social_order(user_id, service['service'], link, quantity, total_price, api_order_id)
            bot.send_message(user_id, t["social_order_success"].format(api_order_id), parse_mode="Markdown")
            add_purchase_record(user_id, f"🌐 {service['name']} ({quantity}) - {total_price} DH - طلب API: {api_order_id}")
            del user_social_temp[user_id]
        else:
            bot.send_message(user_id, t["social_order_failed"], parse_mode="Markdown")
            del user_social_temp[user_id]

    @bot.message_handler(commands=['cancel_social'])
    def cancel_social_order(message):
        user_id = message.from_user.id
        if user_id in user_social_temp:
            del user_social_temp[user_id]
            bot.send_message(user_id, "❌ تم إلغاء الطلب.")
        else:
            bot.send_message(user_id, "⚠️ لا يوجد طلب قيد الانتظار.")

    @bot.message_handler(commands=['social_status'])
    def social_status(message):
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "❗ الاستخدام: /social_status <api_order_id>")
            return
        try:
            api_order_id = int(args[1])
        except:
            bot.send_message(message.chat.id, "❌ معرف الطلب يجب أن يكون رقماً.")
            return
        status_data = get_order_status(api_order_id)
        if status_data and 'status' in status_data:
            lang = get_lang(message.from_user.id)
            t = T[lang]
            msg = f"📊 *حالة الطلب {api_order_id}:*\n" + \
                  f"📌 الحالة: {status_data.get('status', 'غير معروف')}\n" + \
                  f"💵 المتبقي: {status_data.get('remains', 0)}\n" + \
                  f"⚡ بدء العد: {status_data.get('start_count', 0)}"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ لم نتمكن من جلب حالة الطلب.")

    # ========== معالجات شراء المنتجات (جواهر، مفاتيح، تطبيقات) ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def process_purchase(call):
        pkg = call.data.split('_')[1]
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        if pkg not in codes_inventory or not codes_inventory[pkg]:
            bot.answer_callback_query(call.id, t["out_of_stock"], show_alert=True)
            return
        if is_whitelisted(user_id):
            code = codes_inventory[pkg].pop(0)
            bot.send_message(user_id, t["purchase_success"].format(pkg, prices[pkg], code, ADMIN_CONTACT, CHANNEL_PROOFS), parse_mode="Markdown")
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
            purchase_ff_package(user_id, pkg, lang)
            bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('key_prod_'))
    def choose_duration(call):
        prod_id = call.data.split('_')[2]
        lang = get_lang(call.from_user.id)
        t = T[lang]
        prod_data = keys_inventory.get(prod_id)
        if not prod_data:
            bot.answer_callback_query(call.id, "❌ المنتج غير موجود", show_alert=True)
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        for days, price in prod_data["prices"].items():
            markup.add(types.InlineKeyboardButton(f"{days} DAYS = {price} DH 💰", callback_data=f"key_buy_{prod_id}_{days}"))
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
        if len(parts) < 4:
            bot.answer_callback_query(call.id, "خطأ", show_alert=True)
            return
        prod_id = parts[2]
        days = parts[3]
        user_id = call.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        if prod_id not in keys_inventory or days not in keys_inventory[prod_id]["codes"] or not keys_inventory[prod_id]["codes"][days]:
            bot.answer_callback_query(call.id, t["no_stock"], show_alert=True)
            return
        if is_whitelisted(user_id):
            code = keys_inventory[prod_id]["codes"][days].pop(0)
            product_name = keys_inventory[prod_id]["name_ar"] if lang == 'ar' else keys_inventory[prod_id]["name_en"]
            bot.send_message(user_id, t["keys_purchase_success"].format(product_name, days, keys_inventory[prod_id]["prices"][days], code, ADMIN_CONTACT, CHANNEL_PROOFS), parse_mode="Markdown")
            add_purchase_record(user_id, f"🔑 {product_name} ({days} يوم): {code} - {datetime.now()}")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'key', f"{prod_id}_{days}", code, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, product_name, keys_inventory[prod_id]["prices"][days], extra_info=f"🗓️ المدة: {days} يوم\n", code_or_link=code)
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, f"🔄 الوكيل @{call.from_user.username} سحب مفتاح {product_name} مدة {days} أيام (كود: {code})")
                except:
                    pass
            bot.answer_callback_query(call.id, t["confirm_purchase"])
        else:
            purchase_key(user_id, days, lang)
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
            price = app_data["price"]
            success_msg = t["order_accepted"].format(product_name, price, download_link, channel_link, ADMIN_CONTACT, CHANNEL_PROOFS)
            bot.send_message(user_id, success_msg, parse_mode="Markdown")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'app', app_id, download_link, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, product_name, price, extra_info=f"📢 قناة التحديثات: [انضم]({channel_link})\n", code_or_link=download_link)
            for admin in ADMIN_IDS:
                try:
                    bot.send_message(admin, f"🔄 الوكيل @{call.from_user.username} سحب تطبيق {product_name}")
                except:
                    pass
            bot.answer_callback_query(call.id, "🎉 تم تسليم التطبيق بنجاح!")
        else:
            price = app_data["price"]
            show_payment_methods(user_id, 'app', app_id, price)
            bot.answer_callback_query(call.id)

    # ========== معالجات نظام الدفع ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
    def handle_payment_method(call):
        parts = call.data.split('_', 4)
        if len(parts) < 5:
            bot.answer_callback_query(call.id, "خطأ في البيانات", show_alert=True)
            return
        method_key, product_type, product_id, amount = parts[1], parts[2], parts[3], parts[4]
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
        order_id = create_order(user_id, product_type, product_id, float(amount))
        method = PAYMENT_METHODS.get(method_key)
        if not method:
            bot.answer_callback_query(call.id, "طريقة دفع غير معروفة", show_alert=True)
            return
        details = method["details_ar"] if lang == 'ar' else method["details_en"]
        instructions = (f"<b>📌 طريقة الدفع:</b> {method['name_ar'] if lang=='ar' else method['name_en']}\n"
                        f"━━━━━━━━━━━━\n{details}\n\n<b>💰 المبلغ:</b> {amount} درهم\n<b>🆔 رقم الطلب:</b> <code>{order_id}</code>\n\n"
                        f"⚠️ بعد التحويل، أرسل صورة الإيصال بالضغط على الزر أدناه.")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📸 أرسل الإيصال", callback_data=f"send_proof_{order_id}"))
        markup.add(types.InlineKeyboardButton("🔄 تغيير طريقة الدفع", callback_data=f"change_payment_{order_id}"))
        bot.send_message(user_id, instructions, reply_markup=markup, parse_mode="HTML")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('change_payment_'))
    def change_payment_method(call):
        order_id = call.data.split('_', 2)[2]
        user_id = call.from_user.id
        order = get_order(order_id)
        if not order or order[1] != user_id or order[5] not in ('pending', 'waiting_admin', 'rejected'):
            bot.answer_callback_query(call.id, "لا يمكن تغيير طريقة الدفع الآن", show_alert=True)
            return
        update_order_status(order_id, 'cancelled', admin_action='user_cancelled')
        product_type, product_id, amount = order[2], order[3], order[4]
        show_payment_methods(user_id, product_type, product_id, amount)
        bot.answer_callback_query(call.id, "✅ يمكنك اختيار طريقة دفع جديدة")

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
            bot.send_message(user_id, "❌ يرجى إرسال صورة وليس نصاً. أعد المحاولة.")
            bot.register_next_step_handler_by_chat_id(user_id, lambda msg: process_proof_photo(msg, order_id))
            return
        waiting_msg = bot.send_message(user_id, t["proof_received"], parse_mode="Markdown")
        photo_id = message.photo[-1].file_id
        update_order_status(order_id, 'waiting_admin', proof_photo_id=photo_id)
        order = get_order(order_id)
        if not order:
            bot.send_message(user_id, "❌ حدث خطأ في الطلب.")
            return
        product_type, product_id, amount = order[2], order[3], order[4]
        if product_type == 'ff':
            product_name = f"جواهر فري فاير ({product_id} جوهرة)"
        elif product_type == 'key':
            parts = product_id.split('_')
            product_name = f"مفتاح DRIP CLIENT - {parts[1] if len(parts)>1 else product_id} يوم"
        else:
            app_data = apps_inventory.get(product_id, {})
            product_name = app_data.get("name_ar", "تطبيق") if lang == 'ar' else app_data.get("name_en", "App")
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
        bot.edit_message_text("📸 تم استلام إثبات الدفع! سيتم مراجعته من قبل الإدارة قريباً.", chat_id=user_id, message_id=waiting_msg.message_id, parse_mode="Markdown")

    # ========== قبول ورفض الطلبات ==========
    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_accept_'))
    def admin_accept_order(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        order_id = call.data.split('_', 2)[2]
        finalize_order(order_id, accepted=True, admin_id=call.from_user.id)
        bot.answer_callback_query(call.id, "✅ تم قبول الطلب")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('admin_reject_'))
    def admin_reject_order(call):
        if not is_admin(call.from_user.id):
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        order_id = call.data.split('_', 2)[2]
        finalize_order(order_id, accepted=False, admin_id=call.from_user.id)
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")

    # ========== أزرار العودة ==========
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_ff_services")
    def back_to_ff_services(call):
        lang = get_lang(call.from_user.id)
        t = T[lang]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(t["ff_topup"], t["keys_service"])
        markup.add(t["back_to_sections"])
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🎮 *خدمات فري فاير:*\n━━━━━━━━━━━━\nاختر الخدمة:", reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

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
