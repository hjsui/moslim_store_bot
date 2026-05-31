# handlers_social.py
# دوال السوشل ميديا (الهيكل الهرمي، التصنيفات، التدفق)

import telebot
from telebot import types
from languages import T
from database import get_lang, create_order
from social_api import get_services_by_ids, calculate_price_with_profit
from social_structure import SOCIAL_STRUCTURE, get_categories_list, get_subcategories_list, get_service_ids_from_structure

# متغير عالمي لحالة المستخدمين (يتم مشاركته بين الملفات)
user_social_state = {}

def register_social_handlers(bot, common_funcs, payment_funcs):
    """تسجيل معالجات السوشل ميديا"""
    show_main_menu = common_funcs['show_main_menu']
    show_payment_methods = payment_funcs['show_payment_methods']

    def show_social_platforms(user_id, lang, bot_obj=None):
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

    # ========== معالجات كول باك السوشل ميديا ==========
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
            bot.answer_callback_query(call.id, "❌ لا توجد خدمات في هذا التصنيف.", show_alert=True)
            return
        services = get_services_by_ids(service_ids)
        if not services:
            bot.answer_callback_query(call.id, "❌ لا توجد خدمات متاحة حالياً.", show_alert=True)
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
        bot.send_message(user_id, "❌ تم إلغاء جميع العمليات. يمكنك البدء من جديد.")
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

    # ========== معالجات النصوص (الرابط والكمية) ==========
    @bot.message_handler(func=lambda msg: True, content_types=['text'])
    def handle_social_text(message):
        user_id = message.from_user.id
        if user_id not in user_social_state:
            return
        step = user_social_state[user_id].get('step')
        lang = get_lang(user_id)
        t = T[lang]
        if step == 'awaiting_link':
            user_social_state[user_id]['link'] = message.text
            user_social_state[user_id]['step'] = 'awaiting_quantity'
            bot.send_message(user_id, t["social_send_quantity"])
        elif step == 'awaiting_quantity':
            try:
                qty = int(message.text)
                if qty < 1:
                    raise ValueError
                user_social_state[user_id]['quantity'] = qty
                service = user_social_state[user_id]['selected_service']
                total_price = calculate_price_with_profit(float(service['rate']) * qty)
                user_social_state[user_id]['total_price'] = total_price
                summary = t["social_order_summary"].format(
                    user_social_state[user_id].get('platform_name', ''),
                    service['name'],
                    user_social_state[user_id]['link'],
                    qty,
                    total_price
                )
                bot.send_message(user_id, summary, parse_mode="Markdown")
                user_social_state[user_id]['step'] = 'awaiting_confirmation'
            except ValueError:
                bot.send_message(user_id, t["social_invalid_quantity"])

    # ========== أوامر السوشل ميديا ==========
    @bot.message_handler(commands=['confirm_social'])
    def confirm_social_order(message):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        t = T[lang]
        if user_id not in user_social_state or user_social_state[user_id].get('step') != 'awaiting_confirmation':
            bot.send_message(user_id, "⚠️ لا يوجد طلب قيد الانتظار للتأكيد.")
            return
        data = user_social_state[user_id]
        service = data['selected_service']
        link = data['link']
        qty = data['quantity']
        total = data['total_price']
        platform_name = data.get('platform_name', '')
        api_payload = f"social|{service['service']}|{link}|{qty}"
        order_id = create_order(user_id, 'social', api_payload, float(total))
        del user_social_state[user_id]
        bot.send_message(user_id, f"✅ *تم إنشاء طلب رقم `{order_id}` بنجاح!*\n💰 المبلغ: {total} درهم\n📱 المنصة: {platform_name}\n📌 الخدمة: {service['name']}\n\nاختر طريقة الدفع:", parse_mode="Markdown")
        show_payment_methods(user_id, 'social', api_payload, total, bot)

    @bot.message_handler(commands=['cancel_social'])
    def cancel_social_order(message):
        user_id = message.from_user.id
        if user_id in user_social_state:
            del user_social_state[user_id]
            bot.send_message(user_id, "❌ تم إلغاء الطلب.")
        else:
            bot.send_message(user_id, "⚠️ لا يوجد طلب نشط.")

    @bot.message_handler(commands=['social_status'])
    def social_status(message):
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(message.chat.id, "❗ الاستخدام: /social_status <api_order_id>")
            return
        try:
            api_id = int(args[1])
        except:
            bot.send_message(message.chat.id, "❌ معرف الطلب يجب أن يكون رقماً.")
            return
        from social_api import get_order_status
        status = get_order_status(api_id)
        if status and 'status' in status:
            msg = f"📊 *حالة الطلب {api_id}:*\n📌 الحالة: {status.get('status')}\n💵 المتبقي: {status.get('remains',0)}\n⚡ بدء العد: {status.get('start_count',0)}"
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "❌ لم نتمكن من جلب الحالة.")

    # معالج خاص لزر السوشل ميديا في القائمة الرئيسية
    @bot.message_handler(func=lambda msg: msg.text == T[get_lang(msg.from_user.id)]["social_media"])
    def social_media_button(message):
        user_id = message.from_user.id
        lang = get_lang(user_id)
        show_social_platforms(user_id, lang)

    return {'user_social_state': user_social_state}
