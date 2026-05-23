import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread
from datetime import datetime
import random
import string
import os

# ------------------- خادم الاستمرارية -------------------
app = Flask('')

@app.route('/')
def home():
    return "MOSLIM STORE IS ONLINE ✅"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------- إعدادات البوت -------------------
API_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 8530485909  # المدير الرئيسي
ADMIN_IDS = [8530485909, 8615239297]  # وكلاء آخرون للقبول/الرفض (اختياري)
bot = telebot.TeleBot(API_TOKEN)

STORE_PASSWORD = "555451265696++ftytyuiuliyty6654923//fyytu@moslim.com"
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# ------------------- القائمة البيضاء -------------------
WHITELISTED_USERS = [8530485909, 8615239297]  # الأدمن الذين يسحبون مجاناً

def is_whitelisted(user_id):
    return user_id in WHITELISTED_USERS

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ------------------- المنتجات -------------------
codes_inventory = {
    "110": ["4212878473275898", "4662933479894874", "2832586864754929", "2869135500382282"],
    "231": ["8924464665769889"],
    "583": ["5787057855711530"],
    "1188": [],
    "2420": ["6505308166203670"]
}
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

keys_inventory = {
    "dripclient": {
        "name_ar": "DRIP CLIENT APKMOD 👾",
        "name_en": "DRIP CLIENT APKMOD 👾",
        "prices": {"1": 20, "3": 25, "7": 50, "15": 78, "30": 120},
        "codes": {
            "1": [],
            "3": [],
            "7": [],
            "15": [],
            "30": ["6732684380", "7481744555"]
        }
    }
}

apps_inventory = {
    "capcut": {
        "name_ar": "🎬 CapCut PRO",
        "name_en": "🎬 CapCut PRO",
        "price": 20,
        "update_channel": "https://t.me/+zyJW6ZvNp98yMzFk",
        "link": "https://drive.google.com/uc?export=download&id=YOUR_CAPCUT_ID"
    },
    "inshot": {
        "name_ar": "✂️ Inshot PRI",
        "name_en": "✂️ Inshot PRI",
        "price": 15,
        "update_channel": "https://t.me/+fDPaaezCFKNmZmM0",
        "link": "https://drive.google.com/uc?export=download&id=YOUR_INSHOT_ID"
    },
    "picsart": {
        "name_ar": "🖌️ Picsart PRO",
        "name_en": "🖌️ Picsart PRO",
        "price": 25,
        "update_channel": "https://t.me/+-6sCG_0g6Mw3ODI0",
        "link": "https://drive.google.com/uc?export=download&id=YOUR_PICSART_ID"
    }
}

# ------------------- قاعدة البيانات -------------------
def init_db():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, 
                  purchases TEXT, join_date TEXT, language TEXT DEFAULT 'ar')''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (order_id TEXT PRIMARY KEY, user_id INTEGER, product_type TEXT, 
                  product_id TEXT, amount REAL, status TEXT, timestamp TEXT,
                  proof_photo_id TEXT, admin_action TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, admin_name TEXT,
                  product_type TEXT, product_id TEXT, code TEXT, action_date TEXT)''')
    conn.commit()
    conn.close()
init_db()

def log_admin_withdrawal(admin_id, admin_name, product_type, product_id, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
              (admin_id, admin_name, product_type, product_id, code, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def add_purchase_record(user_id, record):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE users SET purchases = COALESCE(purchases, '') || ? || '\n' WHERE user_id=?", (record, user_id))
    conn.commit()
    conn.close()

def get_lang(user_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 'ar'

def set_lang(user_id, lang):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE users SET language = ? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()

def get_verified_count():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE verified=1")
    count = c.fetchone()[0]
    conn.close()
    return count

# ------------------- أوامر البوت الأساسية -------------------
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
        # إرسال اختيار اللغة (يمكن تبسيطها لاحقاً)
        bot.send_message(message.chat.id, "مرحباً! أرسل كلمة المرور لتفعيل المتجر.")
        return
    verified, lang = user
    if verified:
        show_main_menu(message, lang)
    else:
        bot.send_message(message.chat.id, "أدخل كلمة المرور:")

def show_main_menu(message, lang):
    t = T[lang]  # اختصار للترجمة (سأضع ترجمة أساسية لاحقاً)
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row("🛍️ تسوق الآن", "🛒 الخدمات")
    markup.row("👤 ملفي", "📢 إثباتات")
    bot.send_message(message.chat.id, "القائمة الرئيسية", reply_markup=markup)

@bot.message_handler(func=lambda msg: True)
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
    if not verified:
        if message.text == STORE_PASSWORD:
            c.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
            conn.commit()
            bot.reply_to(message, "✅ تم التفعيل")
            show_main_menu(message, lang)
        else:
            bot.reply_to(message, "❌ كلمة مرور خاطئة")
        conn.close()
        return
    # تبسيط: التعامل مع الأزرار الأساسية
    if message.text == "🛍️ تسوق الآن":
        show_ff_packages(message, lang)
    elif message.text == "🛒 الخدمات":
        # نعرض قائمة الخدمات الثانوية
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("💎 شحن جواهر", "🔑 مفاتيح هكرات", "📱 تطبيقات")
        bot.send_message(message.chat.id, "اختر الخدمة:", reply_markup=markup)
    elif message.text == "💎 شحن جواهر":
        show_ff_packages(message, lang)
    elif message.text == "🔑 مفاتيح هكرات":
        show_keys_products(message, lang)
    elif message.text == "📱 تطبيقات":
        show_apps_products(message, lang)
    elif message.text == "👤 ملفي":
        c.execute("SELECT purchases, join_date FROM users WHERE user_id=?", (user_id,))
        purchases, join_date = c.fetchone()
        bot.send_message(message.chat.id, f"تاريخ التسجيل: {join_date}\nمشترياتك:\n{purchases or 'لا شيء'}")
    else:
        bot.send_message(message.chat.id, "استخدم الأزرار")
    conn.close()

def show_ff_packages(message, lang):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pkg, price in prices.items():
        if codes_inventory.get(pkg):
            markup.add(types.InlineKeyboardButton(f"💎 {pkg} جوهرة = {price} درهم", callback_data=f"buy_{pkg}"))
    bot.send_message(message.chat.id, "باقات الجواهر:", reply_markup=markup)

def show_keys_products(message, lang):
    markup = types.InlineKeyboardMarkup()
    for days, price in keys_inventory['dripclient']['prices'].items():
        markup.add(types.InlineKeyboardButton(f"{days} يوم = {price} درهم", callback_data=f"key_buy_{days}"))
    bot.send_message(message.chat.id, "اختر المدة:", reply_markup=markup)

def show_apps_products(message, lang):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for app_id, app in apps_inventory.items():
        markup.add(types.InlineKeyboardButton(app["name_ar"], callback_data=f"app_buy_{app_id}"))
    bot.send_message(message.chat.id, "اختر التطبيق:", reply_markup=markup)

# ------------------- عمليات الشراء (مع إشعار الأدمن) -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_buy(call):
    pkg = call.data.split('_')[1]
    user_id = call.from_user.id
    lang = get_lang(user_id)
    if is_whitelisted(user_id):
        # سحب مجاني
        if codes_inventory.get(pkg) and codes_inventory[pkg]:
            code = codes_inventory[pkg].pop(0)
            bot.send_message(user_id, f"✅ تم الشراء مجاناً!\nكودك: `{code}`")
            # إشعار للمدير
            msg = (f"🔔 *سحب أدمن (قائمة بيضاء)*\n"
                   f"👤 الادمن: @{call.from_user.username}\n"
                   f"📦 المنتج: {pkg} جوهرة\n"
                   f"💰 السعر: {prices[pkg]} درهم\n"
                   f"🔑 الكود: `{code}`\n"
                   f"⏰ الوقت: {datetime.now()}")
            try:
                bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
            except:
                pass
            add_purchase_record(user_id, f"سحب مجاني: {pkg} - {code}")
            log_admin_withdrawal(user_id, call.from_user.username, 'ff', pkg, code)
            bot.answer_callback_query(call.id, "تم بنجاح")
        else:
            bot.answer_callback_query(call.id, "المنتج غير متوفر", show_alert=True)
    else:
        # دفع عادي (اختصار: نطلب إرسال إثبات)
        bot.send_message(user_id, "هذا المنتج يتطلب دفع. أرسل صورة الإيصال للحصول عليه.")
        # هنا يمكن إضافة منطق الطلبات، لكن سنختصر للتركيز على الإشعارات

@bot.callback_query_handler(func=lambda call: call.data.startswith('key_buy_'))
def process_key_buy(call):
    days = call.data.split('_')[2]
    user_id = call.from_user.id
    lang = get_lang(user_id)
    if is_whitelisted(user_id):
        if keys_inventory['dripclient']['codes'].get(days) and keys_inventory['dripclient']['codes'][days]:
            code = keys_inventory['dripclient']['codes'][days].pop(0)
            bot.send_message(user_id, f"✅ تم شراء المفتاح مجاناً!\nمفتاح {days} يوم: `{code}`")
            msg = (f"🔔 *سحب أدمن (قائمة بيضاء)*\n"
                   f"👤 الادمن: @{call.from_user.username}\n"
                   f"📦 المنتج: مفتاح DRIP {days} يوم\n"
                   f"💰 السعر: {keys_inventory['dripclient']['prices'][days]} درهم\n"
                   f"🔑 المفتاح: `{code}`\n"
                   f"⏰ الوقت: {datetime.now()}")
            try:
                bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
            except:
                pass
            add_purchase_record(user_id, f"سحب مجاني: مفتاح {days} يوم - {code}")
            log_admin_withdrawal(user_id, call.from_user.username, 'key', f"{days}", code)
            bot.answer_callback_query(call.id, "تم بنجاح")
        else:
            bot.answer_callback_query(call.id, "لا يوجد مفاتيح متاحة", show_alert=True)
    else:
        bot.send_message(user_id, "هذا المنتج يتطلب دفع. أرسل إثبات الدفع.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('app_buy_'))
def process_app_buy(call):
    app_id = call.data.split('_')[2]
    user_id = call.from_user.id
    lang = get_lang(user_id)
    app = apps_inventory.get(app_id)
    if not app:
        bot.answer_callback_query(call.id, "التطبيق غير موجود", show_alert=True)
        return
    if is_whitelisted(user_id):
        product_name = app["name_ar"]
        download_link = app["link"]
        channel_link = app["update_channel"]
        price = app["price"]
        bot.send_message(user_id, f"✅ تم شراء التطبيق مجاناً!\nرابط التحميل: {download_link}\nقناة التحديثات: {channel_link}")
        msg = (f"🔔 *سحب أدمن (قائمة بيضاء)*\n"
               f"👤 الادمن: @{call.from_user.username}\n"
               f"📦 المنتج: {product_name}\n"
               f"💰 السعر: {price} درهم\n"
               f"🔗 رابط التحميل: {download_link}\n"
               f"⏰ الوقت: {datetime.now()}")
        try:
            bot.send_message(ADMIN_ID, msg, parse_mode="Markdown")
        except:
            pass
        add_purchase_record(user_id, f"سحب مجاني: {product_name} - {download_link}")
        log_admin_withdrawal(user_id, call.from_user.username, 'app', app_id, download_link)
        bot.answer_callback_query(call.id, "تم بنجاح")
    else:
        bot.send_message(user_id, "هذا التطبيق يتطلب دفع. أرسل إثبات الدفع.")

# ------------------- أمر لعرض سجل الأدمن -------------------
@bot.message_handler(commands=['adminlogs'])
def show_admin_logs(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "غير مسموح")
        return
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT admin_name, product_type, product_id, code, action_date FROM admin_logs ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    if not rows:
        bot.reply_to(message, "لا توجد سجلات")
        return
    text = "📋 سجل سحب الأدمن:\n"
    for row in rows:
        admin_name, ptype, pid, code, date = row
        text += f"👤 {admin_name} | {ptype} | {pid} | `{code}` | {date[:16]}\n"
    for part in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        bot.send_message(message.chat.id, part, parse_mode="Markdown")

# ------------------- ترجمة مبسطة -------------------
T = {
    "ar": {
        "shop_now": "🛍️ تسوق الآن",
        "services": "🛒 الخدمات",
        "profile": "👤 ملفي",
        "proofs": "📢 إثباتات"
    },
    "en": {
        "shop_now": "🛍️ Shop Now",
        "services": "🛒 Services",
        "profile": "👤 My Profile",
        "proofs": "📢 Proofs"
    }
}

# ------------------- التشغيل -------------------
if __name__ == "__main__":
    keep_alive()
    print("✅ البوت يعمل")
    bot.infinity_polling()
