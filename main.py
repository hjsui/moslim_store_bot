import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread
from datetime import datetime

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
API_TOKEN = '8325861290:AAHNx4oCfEy758rJQcm-oeYthAdZ80kTe0k'
ADMIN_ID = 6500854407
bot = telebot.TeleBot(API_TOKEN)

STORE_PASSWORD = "555451265696++ftytyuiuliyty6654923//fyytu@moslim.com"
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# أكواد الجواهر والأسعار (نفسها)
codes_inventory = {
    "110": ["5510650023494411", "9330820420409597", "6627018902595942"],
    "231": ["4808931182736381", "0698785582111920"],
    "583": ["9600129739749249", "9614548276115470"],
    "1188": ["2327640609655494", "2244758579935760"],
    "2420": ["5572361327155594"]
}
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

# ------------------- قاموس الترجمة -------------------
translations = {
    "ar": {
        "shop_now": "🛍️ تسوق الآن",
        "services": "🛒 الخدمات",
        "add_balance": "💰 إضافة رصيد",
        "profile": "👤 الملف الشخصي",
        "how_to_use": "📖 طريقة الاستخدام",
        "support": "📞 الدعم الفني",
        "proofs": "📢 إثباتات الثقة",
        "back": "🔙 العودة للقائمة الرئيسية",
        "ask_password": "⚠️ *مـتـجـــر مـسـلـــم* 🛍️\nأدخل كلمة المرور لتفعيل المتجر:",
        "wrong_password": "❌ *كلمة مرور خاطئة!* ❌",
        "verified_success": "✅ *تم التفعيل بنجاح!* ✅\n🎉 مرحباً بك في متجر مسلم",
        "user_count": "\n👥 *عدد المستخدمين المسجلين:* {}",
        "welcome_after_lang": "🛍️ *مـتـجـــر مـسـلـــم | MOSLIM STORE* 🛍️\n━━━━━━━━━━━━━━━━━━━━\n✨ *خدمات رقمية - شحن فوري - اشتراكات* ✨\n⚡ *سرعة - ثقة - أسعار لا تقبل المنافسة* ⚡\n📢 *آراء العملاء:* قناتنا مليئة بالإثباتات\n━━━━━━━━━━━━━━━━━━━━\n🔓 *اضغط /start لتفعيل المتجر* 🔓"
    },
    "en": {
        "shop_now": "🛍️ Shop Now",
        "services": "🛒 Services",
        "add_balance": "💰 Add Balance",
        "profile": "👤 Profile",
        "how_to_use": "📖 How to Use",
        "support": "📞 Support",
        "proofs": "📢 Trust Proofs",
        "back": "🔙 Back to Main Menu",
        "ask_password": "⚠️ *MOSLIM STORE* 🛍️\nEnter password to activate the store:",
        "wrong_password": "❌ *Wrong password!* ❌",
        "verified_success": "✅ *Activated successfully!* ✅\n🎉 Welcome to Moslim Store",
        "user_count": "\n👥 *Registered users:* {}",
        "welcome_after_lang": "🛍️ *MOSLIM STORE* 🛍️\n━━━━━━━━━━━━━━━━━━━━\n✨ *Digital services - Instant top-up - Subscriptions* ✨\n⚡ *Speed - Trust - Unbeatable prices* ⚡\n📢 *Customer reviews:* Our channel is full of proofs\n━━━━━━━━━━━━━━━━━━━━\n🔓 *Press /start to activate the store* 🔓"
    }
}
# يمكن إضافة لغات أخرى بنفس القالب

# ------------------- قاعدة البيانات -------------------
def init_db():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, 
                  purchases TEXT, join_date TEXT, language TEXT DEFAULT 'ar')''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ar'")
    except:
        pass
    conn.commit()
    conn.close()
init_db()

# ------------------- دوال مساعدة -------------------
def get_lang(user_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res and res[0] else 'ar'

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

# ------------------- اختيار اللغة -------------------
def send_lang_selection(chat_id):
    photo_url = "https://i.postimg.cc/g2Dtfh3L/Picsart-26-01-29-07-31-38-423.jpg"
    caption = "🌍 *Please select your language / اختر لغتك*\n\n⭐ *Choose from below:*"
    markup = types.InlineKeyboardMarkup(row_width=2)
    langs = [
        ("🇸🇦 العربية", "ar"), ("🇬🇧 English", "en"), ("🇫🇷 Français", "fr"),
        ("🇪🇸 Español", "es"), ("🇹🇷 Türkçe", "tr"), ("🇩🇪 Deutsch", "de"),
        ("🇷🇺 Русский", "ru"), ("🇮🇹 Italiano", "it")
    ]
    for text, code in langs:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"lang_{code}"))
    bot.send_photo(chat_id, photo=photo_url, caption=caption, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    lang = call.data.split('_')[1]
    user_id = call.from_user.id
    set_lang(user_id, lang)
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    # إرسال رسالة الترحيب الجديدة بعد اختيار اللغة
    t = translations.get(lang, translations['ar'])
    bot.send_message(call.message.chat.id, t["welcome_after_lang"], parse_mode="Markdown")

# ------------------- أوامر البوت -------------------
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
    t = translations.get(lang, translations['ar'])
    
    if verified == 0:
        bot.send_message(message.chat.id, t["ask_password"], parse_mode="Markdown")
    else:
        show_main_menu(message, lang)
    conn.close()

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
    t = translations.get(lang, translations['ar'])
    
    if verified == 0:
        if message.text == STORE_PASSWORD:
            c.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
            conn.commit()
            bot.reply_to(message, t["verified_success"], parse_mode="Markdown")
            show_main_menu(message, lang)
        else:
            bot.reply_to(message, t["wrong_password"], parse_mode="Markdown")
        conn.close()
        return
    
    # ------------------- القائمة الرئيسية -------------------
    if message.text == t["proofs"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 قناة الإثباتات", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, f"📢 *قناة الإثباتات:* [اضغط هنا]({CHANNEL_PROOFS})", reply_markup=m, parse_mode="Markdown")
    
    elif message.text in [t["shop_now"], t["services"]]:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add("💎 شحن جواهر فري فاير", "🎮 شحن ألعاب أخرى", t["back"])
        bot.send_message(message.chat.id, "🛒 *أقسام المتجر:*\n━━━━━━━━━━━━\nاختر القسم المناسب:", reply_markup=markup, parse_mode="Markdown")
    
    elif message.text == "🎮 شحن ألعاب أخرى":
        bot.send_message(message.chat.id, "🎮 *شحن ألعاب أخرى*\n━━━━━━━━━━━━\n📞 تواصل مع الدعم.", parse_mode="Markdown")
    
    elif message.text == "💎 شحن جواهر فري فاير":
        show_ff_packages(message, lang)
    
    elif message.text == t["profile"]:
        c.execute("SELECT purchases, join_date FROM users WHERE user_id=?", (user_id,))
        purchases, join_date = c.fetchone()
        purchases = purchases or "📭 لا توجد مشتريات"
        bot.send_message(message.chat.id, f"👤 *ملفك الشخصي*\n━━━━━━━━━━━━\n📅 تاريخ التسجيل: {join_date}\n🛍️ مشترياتك:\n{purchases}", parse_mode="Markdown")
    
    elif message.text == t["support"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💬 مراسلة المدير", url=ADMIN_CONTACT))
        bot.send_message(message.chat.id, "👨‍💻 *فريق الدعم*", reply_markup=m, parse_mode="Markdown")
    
    elif message.text == t["add_balance"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💳 مراسلة الدعم", url=ADMIN_CONTACT))
        bot.send_message(message.chat.id, "💰 *إضافة رصيد*\nتواصل مع الدعم.", reply_markup=m, parse_mode="Markdown")
    
    elif message.text == t["how_to_use"]:
        bot.send_message(message.chat.id, "📖 *طريقة الاستخدام*\n1️⃣ اختر الباقة\n2️⃣ اضغط شراء\n3️⃣ تواصل للدفع\n4️⃣ استلم الكود", parse_mode="Markdown")
    
    elif message.text == t["back"]:
        show_main_menu(message, lang)
    
    else:
        bot.reply_to(message, "🤖 استخدم الأزرار بالأسفل.", parse_mode="Markdown")
    
    conn.close()

# ------------------- عرض باقات الجواهر -------------------
def show_ff_packages(message, lang):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pkg in codes_inventory.keys():
        price = prices[pkg]
        markup.add(types.InlineKeyboardButton(f"💎 {pkg} جوهرة = {price} درهم", callback_data=f"buy_{pkg}"))
    bot.send_message(message.chat.id, "💎 *اختر الباقة:*", reply_markup=markup, parse_mode="Markdown")

# ------------------- عملية الشراء -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_buy(call):
    pkg = call.data.split('_')[1]
    if codes_inventory.get(pkg) and len(codes_inventory[pkg]) > 0:
        code = codes_inventory[pkg].pop(0)
        bot.send_message(call.message.chat.id, f"✅ *تم الشراء!*\n🔑 الكود: `{code}`", parse_mode="Markdown")
        # إشعار للأدمن
        bot.send_message(ADMIN_ID, f"🔔 بيع جديد: {pkg} جوهرة\n👤 {call.from_user.username}\n🔑 {code}")
        # حفظ في قاعدة البيانات
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        c.execute("UPDATE users SET purchases = purchases || ? || '\n' WHERE user_id=?", 
                  (f"{pkg}💎: {code} - {datetime.now()}", call.from_user.id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "🎉 تم الشراء!")
    else:
        bot.answer_callback_query(call.id, "❌ الباقة غير متوفرة", show_alert=True)

# ------------------- عرض القائمة الرئيسية -------------------
def show_main_menu(message, lang):
    t = translations.get(lang, translations['ar'])
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(t["shop_now"], t["services"])
    markup.row(t["add_balance"], t["profile"])
    markup.row(t["how_to_use"], t["support"])
    markup.row(t["proofs"])
    user_count = get_verified_count()
    msg = f"👋🏻 *أهلاً بك {message.from_user.first_name}!*\n\n🛍️ *متجر مسلم - وجهتك الأولى*\n⭐ *الخدمات:*\n🔑 شحن فوري\n⚡ سرعة فائقة\n🔒 متجر موثق\n💸 أسعار ممتازة\n📢 [قناة الإثباتات]({CHANNEL_PROOFS}){t['user_count'].format(user_count)}\n🚀 *اختر من القائمة:*"
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

# ------------------- التشغيل -------------------
if __name__ == "__main__":
    keep_alive()
    print("✅ متجر مسلم يعمل بكفاءة مع اللغات وبدون أخطاء")
    bot.infinity_polling()
