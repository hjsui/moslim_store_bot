# admin_handlers.py
# جميع دوال لوحة التحكم الإدارية (للمدير فقط)

import telebot
from telebot import types
from config import OWNER_ID
from database import (
    get_ff_stock, add_ff_code, del_ff_code,
    get_key_stock, add_key_code, del_key_code
)

# متغيرات مؤقتة لتخزين حالة المدير أثناء إضافة/حذف
admin_temp = {}

def register_admin_handlers(bot):
    """تسجيل جميع معالجات لوحة التحكم الإدارية"""

    @bot.callback_query_handler(func=lambda call: call.data == "admin_ff")
    def admin_ff_menu(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        stock = get_ff_stock()
        if not stock:
            stock_text = "📦 *مخزون الجواهر فارغ*"
        else:
            lines = ["📊 *مخزون جواهر فري فاير:*"]
            for qty, count in stock:
                lines.append(f"💎 {qty} جوهرة : {count} كود")
            stock_text = "\n".join(lines)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إضافة كود", callback_data="admin_ff_add"))
        markup.add(types.InlineKeyboardButton("➖ حذف كود", callback_data="admin_ff_del"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
        bot.edit_message_text(stock_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_keys")
    def admin_keys_menu(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        stock = get_key_stock()
        if not stock:
            stock_text = "📦 *مخزون المفاتيح فارغ*"
        else:
            lines = ["📊 *مخزون مفاتيح DRIP CLIENT:*"]
            for prod, dur, count in stock:
                lines.append(f"🔑 {prod} - {dur} يوم : {count} مفتاح")
            stock_text = "\n".join(lines)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("➕ إضافة مفتاح", callback_data="admin_keys_add"))
        markup.add(types.InlineKeyboardButton("➖ حذف مفتاح", callback_data="admin_keys_del"))
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="admin_back"))
        bot.edit_message_text(stock_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_ff_add")
    def admin_ff_add_prompt(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        admin_temp[user_id] = {'action': 'ff_add', 'step': 'awaiting_code'}
        bot.edit_message_text("📝 *أرسل الكمية والكود بالصيغة:*\n`الكمية الكود`\nمثال: `110 ABC123`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_ff_del")
    def admin_ff_del_prompt(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        admin_temp[user_id] = {'action': 'ff_del', 'step': 'awaiting_code'}
        bot.edit_message_text("🗑️ *أرسل الكمية والكود المراد حذفه:*\n`الكمية الكود`\nمثال: `110 ABC123`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_keys_add")
    def admin_keys_add_prompt(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        admin_temp[user_id] = {'action': 'keys_add', 'step': 'awaiting_code'}
        bot.edit_message_text("📝 *أرسل المدة والكود بالصيغة:*\n`المدة الكود`\nالمدة: 1,3,7,15,30\nمثال: `7 KEY789`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_keys_del")
    def admin_keys_del_prompt(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        admin_temp[user_id] = {'action': 'keys_del', 'step': 'awaiting_code'}
        bot.edit_message_text("🗑️ *أرسل المدة والكود المراد حذفه:*\n`المدة الكود`\nمثال: `7 KEY789`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    @bot.callback_query_handler(func=lambda call: call.data == "admin_back")
    def admin_back(call):
        user_id = call.from_user.id
        if user_id != OWNER_ID:
            bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("📊 إدارة جواهر فري فاير", callback_data="admin_ff"))
        markup.add(types.InlineKeyboardButton("🔑 إدارة مفاتيح DRIP CLIENT", callback_data="admin_keys"))
        bot.edit_message_text("🛠️ *لوحة التحكم الإدارية*\nاختر القسم الذي تريد إدارته:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)


# ========== دالة معالجة الرسائل النصية للإدارة (تُستدعى من handle_messages) ==========
def process_admin_text(bot, message):
    """معالجة الرسائل النصية للمدير أثناء جلسة الإضافة/الحذف"""
    user_id = message.from_user.id
    if user_id not in admin_temp:
        return
    data = admin_temp[user_id]
    action = data['action']
    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❌ الصيغة غير صحيحة. أرسل: `الكمية الكود` (لإدارة الجواهر) أو `المدة الكود` (لإدارة المفاتيح)", parse_mode="Markdown")
        return
    first, second = parts[0], parts[1]
    if action == 'ff_add':
        add_ff_code(first, second)
        bot.reply_to(message, f"✅ تم إضافة الكود `{second}` للكمية {first}")
        del admin_temp[user_id]
    elif action == 'ff_del':
        if del_ff_code(first, second):
            bot.reply_to(message, f"✅ تم حذف الكود `{second}` للكمية {first}")
        else:
            bot.reply_to(message, f"❌ الكود غير موجود أو مستخدم بالفعل")
        del admin_temp[user_id]
    elif action == 'keys_add':
        if first not in ['1', '3', '7', '15', '30']:
            bot.reply_to(message, "❌ المدة غير صالحة. اختر: 1, 3, 7, 15, 30")
            return
        add_key_code('dripclient', first, second)
        bot.reply_to(message, f"✅ تم إضافة المفتاح `{second}` لمدة {first} أيام")
        del admin_temp[user_id]
    elif action == 'keys_del':
        if first not in ['1', '3', '7', '15', '30']:
            bot.reply_to(message, "❌ المدة غير صالحة. اختر: 1, 3, 7, 15, 30")
            return
        if del_key_code('dripclient', first, second):
            bot.reply_to(message, f"✅ تم حذف المفتاح `{second}` لمدة {first} أيام")
        else:
            bot.reply_to(message, f"❌ المفتاح غير موجود")
        del admin_temp[user_id]
    else:
        bot.reply_to(message, "⚠️ حدث خطأ غير متوقع. أعد المحاولة.")
        del admin_temp[user_id]
