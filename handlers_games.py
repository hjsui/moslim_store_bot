# handlers_games.py
# دوال فري فاير (الجواهر، المفاتيح، التطبيقات)

import telebot
from telebot import types
import sqlite3
from datetime import datetime
from config import (
    ADMIN_IDS, CHANNEL_PROOFS, ADMIN_CONTACT,
    codes_inventory, prices, keys_inventory, apps_inventory
)
from database import add_purchase_record, get_lang
from utils import is_whitelisted
from languages import T
from handlers_payment import purchase_ff_package, purchase_key, send_withdrawal_log

def register_games_handlers(bot, common_funcs):
    """تسجيل معالجات فري فاير"""

    def show_ff_packages(message, lang, bot_obj=None):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=2)
        for pkg in codes_inventory:
            if codes_inventory[pkg]:
                price = prices[pkg]
                markup.add(types.InlineKeyboardButton(f"💎 {pkg} {'جوهرة' if lang=='ar' else 'diamonds'} = {price} {'درهم' if lang=='ar' else 'MAD'}", callback_data=f"buy_{pkg}"))
        markup.add(types.InlineKeyboardButton("📢 " + ("شاهد الإثباتات قبل الشراء" if lang=='ar' else "See proofs before buying"), url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, t["ff_packages_title"], reply_markup=markup, parse_mode="Markdown")

    def show_keys_products(message, lang, bot_obj=None):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for prod_id, prod_data in keys_inventory.items():
            btn_text = prod_data["name_ar"] if lang == 'ar' else prod_data["name_en"]
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"key_prod_{prod_id}"))
        bot.send_message(message.chat.id, t["choose_product"], reply_markup=markup, parse_mode="Markdown")

    def show_apps_products(message, lang, bot_obj=None):
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=2)
        for app_id, app_data in apps_inventory.items():
            btn_text = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"app_buy_{app_id}"))
        bot.send_message(message.chat.id, t["choose_app"], reply_markup=markup, parse_mode="Markdown")

    # معالجات شراء الجواهر
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
            purchase_ff_package(user_id, pkg, lang, bot)
            bot.answer_callback_query(call.id)

    # معالجات اختيار مدة المفتاح
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

    # معالجات شراء المفتاح
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
            purchase_key(user_id, days, lang, bot)
            bot.answer_callback_query(call.id)

    # معالجات شراء التطبيقات
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
            from handlers_payment import show_payment_methods
            show_payment_methods(user_id, 'app', app_id, price, bot)
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

    # تصدير الدوال المستخدمة خارجياً
    return {
        'show_ff_packages': show_ff_packages,
        'show_keys_products': show_keys_products,
        'show_apps_products': show_apps_products
    }
