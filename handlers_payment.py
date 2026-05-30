# handlers_payment.py
# دوال نظام الدفع (طرق الدفع، قبول/رفض الطلبات، إثباتات)

import telebot
from telebot import types
import sqlite3
from datetime import datetime
from config import (
    ADMIN_IDS, LOG_CHANNEL_ID, ADMIN_CONTACT, CHANNEL_PROOFS,
    codes_inventory, keys_inventory, apps_inventory
)
from database import get_lang, update_order_status, get_order, add_purchase_record, create_order
from utils import is_admin
from payment_methods import PAYMENT_METHODS
from languages import T
from social_api import add_order

def register_payment_handlers(bot):
    """تسجيل معالجات نظام الدفع"""

    def show_payment_methods(user_id, product_type, product_id, amount, bot_obj=None):
        lang = get_lang(user_id)
        t = T[lang]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, method in PAYMENT_METHODS.items():
            name = method["name_ar"] if lang == 'ar' else method["name_en"]
            markup.add(types.InlineKeyboardButton(name, callback_data=f"pay_{key}_{product_type}_{product_id}_{amount}"))
        bot.send_message(user_id, t["choose_payment"], reply_markup=markup, parse_mode="Markdown")

    def purchase_ff_package(user_id, pkg, lang, bot_obj=None):
        from config import prices
        amount = prices[pkg]
        show_payment_methods(user_id, 'ff', pkg, amount)

    def purchase_key(user_id, days, lang, bot_obj=None):
        from config import keys_inventory
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
            # رفض الطلب
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

    # ========== معالجات كول باك الدفع ==========
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
        bot.edit_message_text("📸 تم استلام إثبات الدفع! سيتم مراجعته من قبل الإدارة قريباً.", chat_id=user_id, message_id=waiting_msg.message_id, parse_mode="Markdown")

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

    # تصدير الدوال المستخدمة خارجياً
    return {
        'show_payment_methods': show_payment_methods,
        'purchase_ff_package': purchase_ff_package,
        'purchase_key': purchase_key,
        'send_withdrawal_log': send_withdrawal_log,
        'finalize_order': finalize_order
    }
