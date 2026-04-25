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

# ------------------- أكواد الجواهر والأسعار -------------------
codes_inventory = {
    "110": ["5510650023494411", "9330820420409597", "6627018902595942"],
    "231": ["4808931182736381", "0698785582111920"],
    "583": ["9600129739749249", "9614548276115470"],
    "1188": ["2327640609655494", "2244758579935760"],
    "2420": ["5572361327155594"]
}
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

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

def get_total_users():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

# ------------------- ترجمة كاملة لكل عناصر البوت -------------------
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
        "ff_topup": "💎 شحن جواهر فري فاير",
        "other_games": "🎮 شحن ألعاب أخرى",
        "choose_section": "🛒 *أقسام المتجر:*\n━━━━━━━━━━━━\nاختر القسم المناسب:",
        "other_games_text": "🎮 *شحن ألعاب أخرى*\n━━━━━━━━━━━━\n📌 *الألعاب المتوفرة:*\n• ببجي موبايل (UC)\n• كول أوف ديوتي (CP)\n• فري فاير (DA)\n• جينشين إمباكت\n\n📞 *للطلب:* تواصل مع الدعم",
        "ff_packages_title": "💎 *باقات شحن جواهر فري فاير*\n━━━━━━━━━━━━\n✨ *باقات حصرية بأفضل الأسعار*\n⚡ *توصيل فوري خلال دقائق*\n━━━━━━━━━━━━\n*اختر الباقة المناسبة:*",
        "ask_password": "⚠️ *مـتـجـــر مـسـلـــم* 🛍️\nأدخل كلمة المرور لتفعيل المتجر:",
        "wrong_password": "❌ *كلمة مرور خاطئة!* ❌",
        "verified_success": "✅ *تم التفعيل بنجاح!* ✅\n🎉 مرحباً بك في متجر مسلم",
        "user_count": "👥 *عدد المستخدمين المسجلين:* {}",
        "welcome_main": "👋🏻 *أهلاً بك، {}!*\n\n🛍️ *في متجر مسلم - وجهتك الأولى للخدمات الحصرية*\n\n⭐ *أبرز مميزات المتجر:*\n🔑 خدمات رقمية مميزة / شحن فوري\n⚡ سرعة فائقة في التنفيذ\n🔒 متجر محمي وموثق 100%\n💸 أسعار لا تقبل المنافسة\n📢 *قناة الإثباتات:* [انقر هنا لمشاهدة الثقة]({})\n🚀 *اختر من القائمة بالأسفل لبدء التسوق!*",
        "profile_text": "👤 *ملفك الشخصي*\n━━━━━━━━━━━━\n🆔 المعرف: `{}`\n📅 تاريخ التسجيل: {}\n🛍️ *سجل مشترياتك:*\n{}\n━━━━━━━━━━━━\n📢 *شكراً لثقتك بنا* ❤️",
        "support_text": "👨‍💻 *فريق الدعم*\n━━━━━━━━━━━━\n• الرد خلال 24 ساعة\n• الدعم متوفر طوال الأسبوع\n• للمشاكل والاستفسارات\n━━━━━━━━━━━━\n*اختر طريقة التواصل:*",
        "add_balance_text": "💰 *إضافة رصيد*\n━━━━━━━━━━━━\n💵 *طرق الدفع المتاحة:*\n• CIH BANK\n• Binance (USDT)\n• PayPal\n• الاتصال برقم الوا\n\n📌 *خطوات الشحن:*\n1️⃣ تواصل مع الدعم\n2️⃣ أرسل المبلغ المطلوب\n3️⃣ استلم الرصيد فوراً\n\n✨ *خدمة آمنة وسريعة*",
        "how_to_use_text": "📖 *طريقة الاستخدام*\n━━━━━━━━━━━━\n📌 *خطوات الشراء:*\n1️⃣ اختر الباقة المناسبة\n2️⃣ اضغط على زر الشراء\n3️⃣ تواصل مع الدعم للدفع\n4️⃣ استلم كودك فوراً!\n\n⚡ *شحن فوري - خدمة 24 ساعة*\n🔒 *ضمان استرجاع الأموال في حال وجود مشكلة*",
        "proofs_text": "📢 *قناة إثباتات الثقة والمصداقية*\n━━━━━━━━━━━━\n🔍 *شاهد بنفسك آراء العملاء السابقين:*\n✅ أكثر من 100+ عملية موثقة\n⭐ تقييم العملاء: ممتاز جداً\n\n[📢 اضغط هنا لمشاهدة الإثباتات]({})",
        "purchase_success": "✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n💎 الكمية: {} جوهرة\n💰 السعر: {} درهم\n🔑 كود الشحن: `{}`\n━━━━━━━━━━━━\n📞 للاستفسار: [@MOSLIM_SHOP]({})\n📢 لمشاهدة إثباتاتنا: [اضغط هنا]({})",
        "out_of_stock": "❌ عذراً، هذه الباقة غير متوفرة حالياً. جرب باقة أخرى!",
        "confirm_purchase": "🎉 تم الشراء بنجاح! استلم الكود أعلاه"
    },
    "en": {
        "shop_now": "🛍️ Shop Now",
        "services": "🛒 Services",
        "add_balance": "💰 Add Balance",
        "profile": "👤 Profile",
        "how_to_use": "📖 How to use",
        "support": "📞 Support",
        "proofs": "📢 Trust Proofs",
        "back": "🔙 Back to main menu",
        "ff_topup": "💎 Free Fire Diamonds Top-up",
        "other_games": "🎮 Other Games Top-up",
        "choose_section": "🛒 *Store Sections:*\n━━━━━━━━━━━━\nChoose the appropriate section:",
        "other_games_text": "🎮 *Other Games Top-up*\n━━━━━━━━━━━━\n📌 *Available games:*\n• PUBG Mobile (UC)\n• Call of Duty (CP)\n• Free Fire (DA)\n• Genshin Impact\n\n📞 *To order:* Contact support",
        "ff_packages_title": "💎 *Free Fire Diamonds Packages*\n━━━━━━━━━━━━\n✨ *Exclusive packages at best prices*\n⚡ *Instant delivery in minutes*\n━━━━━━━━━━━━\n*Choose your package:*",
        "ask_password": "⚠️ *MOSLIM STORE* 🛍️\nEnter password to activate the store:",
        "wrong_password": "❌ *Wrong password!* ❌",
        "verified_success": "✅ *Activated successfully!* ✅\n🎉 Welcome to Moslim Store",
        "user_count": "👥 *Registered users:* {}",
        "welcome_main": "👋🏻 *Welcome, {}!*\n\n🛍️ *Moslim Store - your first destination for exclusive services*\n\n⭐ *Store features:*\n🔑 Exclusive digital services / instant top-up\n⚡ High-speed execution\n🔒 100% protected and verified store\n💸 Unbeatable prices\n📢 *Proofs channel:* [Click here to see trust]({})\n🚀 *Choose from the menu below to start shopping!*",
        "profile_text": "👤 *Your Profile*\n━━━━━━━━━━━━\n🆔 ID: `{}`\n📅 Registration date: {}\n🛍️ *Your purchases:*\n{}\n━━━━━━━━━━━━\n📢 *Thank you for trusting us* ❤️",
        "support_text": "👨‍💻 *Support Team*\n━━━━━━━━━━━━\n• Response within 24 hours\n• Support available all week\n• For issues and inquiries\n━━━━━━━━━━━━\n*Choose contact method:*",
        "add_balance_text": "💰 *Add Balance*\n━━━━━━━━━━━━\n💵 *Payment methods available:*\n• CIH BANK\n• Binance (USDT)\n• PayPal\n• Contact by WhatsApp\n\n📌 *Steps to add:*\n1️⃣ Contact support\n2️⃣ Send the required amount\n3️⃣ Receive balance instantly\n\n✨ *Secure and fast service*",
        "how_to_use_text": "📖 *How to Use*\n━━━━━━━━━━━━\n📌 *Purchase steps:*\n1️⃣ Choose the appropriate package\n2️⃣ Click the purchase button\n3️⃣ Contact support for payment\n4️⃣ Receive your code instantly!\n\n⚡ *Instant top-up - 24/7 service*\n🔒 *Money-back guarantee if any issue occurs*",
        "proofs_text": "📢 *Trust and Credibility Proofs Channel*\n━━━━━━━━━━━━\n🔍 *See previous customers' reviews:*\n✅ 100+ documented transactions\n⭐ Customer rating: Excellent\n\n[📢 Click here to see proofs]({})",
        "purchase_success": "✅ *Purchase successful!* ✅\n━━━━━━━━━━━━\n💎 Quantity: {} diamonds\n💰 Price: {} MAD\n🔑 Top-up code: `{}`\n━━━━━━━━━━━━\n📞 Inquiries: [@MOSLIM_SHOP]({})\n📢 To see our proofs: [Click here]({})",
        "out_of_stock": "❌ Sorry, this package is currently unavailable. Try another package!",
        "confirm_purchase": "🎉 Purchase successful! Get your code above"
    }
}
# أضف لغات أخرى بنفس الهيكل (fr, es, tr, de, ru, it) إن أردت

# ------------------- إرسال صورة الترحيب واختيار اللغة -------------------
def send_lang_selection(chat_id):
    photo_url = "https://i.postimg.cc/g2Dtfh3L/Picsart-26-01-29-07-31-38-423.jpg"
    caption = "🌍 *Please select your language / اختر لغتك*\n\n⭐ *Choose from below:*"
    markup = types.InlineKeyboardMarkup(row_width=2)  # صفين ✅
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
    # بعد اختيار اللغة، تظهر رسالة الترحيب الجذابة
    welcome_msg = """🛍️ *مـتـجـــر مـسـلـــم | MOSLIM STORE* 🛍️
━━━━━━━━━━━━━━━━━━━━
✨ *خدمات رقمية - شحن فوري - اشتراكات* ✨
⚡ *سرعة - ثقة - أسعار لا تقبل المنافسة* ⚡
📢 *آراء العملاء:* قناتنا مليئة بالإثباتات
━━━━━━━━━━━━━━━━━━━━
🔓 *اضغط /start لتفعيل المتجر* 🔓"""
    if lang == 'en':
        welcome_msg = """🛍️ *MOSLIM STORE* 🛍️
━━━━━━━━━━━━━━━━━━━━
✨ *Digital services - Instant top-up - Subscriptions* ✨
⚡ *Speed - Trust - Unbeatable prices* ⚡
📢 *Customer reviews:* Our channel is full of proofs
━━━━━━━━━━━━━━━━━━━━
🔓 *Press /start to activate the store* 🔓"""
    bot.send_message(call.message.chat.id, welcome_msg, parse_mode="Markdown")

# ------------------- القائمة الرئيسية المترجمة -------------------
def show_main_menu(message, lang=None):
    if lang is None:
        lang = get_lang(message.chat.id)
    t = translations.get(lang, translations['ar'])
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(t["shop_now"], t["services"])
    markup.row(t["add_balance"], t["profile"])
    markup.row(t["how_to_use"], t["support"])
    markup.row(t["proofs"])
    user_count = get_verified_count()
    welcome_text = t["welcome_main"].format(message.from_user.first_name, CHANNEL_PROOFS)
    welcome_text += f"\n\n{t['user_count'].format(user_count)}"
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

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
    if verified == 0:
        t = translations.get(lang, translations['ar'])
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
    
    # ------------------- معالجة الأزرار المترجمة -------------------
    if message.text == t["proofs"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 قناة الإثباتات", url=CHANNEL_PROOFS))
        m.add(types.InlineKeyboardButton("⭐ آراء العملاء", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, t["proofs_text"].format(CHANNEL_PROOFS), reply_markup=m, parse_mode="Markdown")
    
    elif message.text in [t["shop_now"], t["services"]]:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add(t["ff_topup"], t["other_games"], t["back"])
        bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")
    
    elif message.text == t["other_games"]:
        bot.send_message(message.chat.id, t["other_games_text"], parse_mode="Markdown")
    
    elif message.text == t["ff_topup"]:
        show_ff_packages(message, lang)
    
    elif message.text == t["profile"]:
        c.execute("SELECT purchases, join_date FROM users WHERE user_id=?", (user_id,))
        purchases, join_date = c.fetchone()
        purchases = purchases or "📭 " + ("لا توجد مشتريات بعد." if lang=='ar' else "No purchases yet.")
        bot.send_message(message.chat.id, t["profile_text"].format(user_id, join_date, purchases), parse_mode="Markdown")
    
    elif message.text == t["support"]:
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("💬 مراسلة المدير", url=ADMIN_CONTACT))
        m.add(types.InlineKeyboardButton("📢 قناة المتجر", url="https://t.me/moslim_store"))
        m.add(types.InlineKeyboardButton("⭐ إثباتات الثقة", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, t["support_text"], reply_markup=m, parse_mode="Markdown")
    
    elif message.text == t["add_balance"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💳 مراسلة الدعم للشحن", url=ADMIN_CONTACT))
        m.add(types.InlineKeyboardButton("📢 شاهد الإثباتات", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, t["add_balance_text"], reply_markup=m, parse_mode="Markdown")
    
    elif message.text == t["how_to_use"]:
        bot.send_message(message.chat.id, t["how_to_use_text"], parse_mode="Markdown")
    
    elif message.text == t["back"]:
        show_main_menu(message, lang)
    
    else:
        bot.reply_to(message, "🤖 " + ("مرحباً! استخدم الأزرار بالأسفل للتنقل." if lang=='ar' else "Hello! Use the buttons below to navigate."), parse_mode="Markdown")
    
    conn.close()

def show_ff_packages(message, lang):
    t = translations.get(lang, translations['ar'])
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pkg in codes_inventory.keys():
        price = prices[pkg]
        # عرض الباقة باللغة المختارة (الأرقام تبقى كما هي)
        markup.add(types.InlineKeyboardButton(f"💎 {pkg} " + ("جوهرة" if lang=='ar' else "diamonds") + f" = {price} " + ("درهم" if lang=='ar' else "MAD"), callback_data=f"buy_{pkg}"))
    markup.add(types.InlineKeyboardButton("📢 " + ("شاهد الإثباتات قبل الشراء" if lang=='ar' else "See proofs before buying"), url=CHANNEL_PROOFS))
    bot.send_message(message.chat.id, t["ff_packages_title"], reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_purchase(call):
    pkg = call.data.split('_')[1]
    lang = get_lang(call.from_user.id)
    t = translations.get(lang, translations['ar'])
    
    if codes_inventory.get(pkg) and len(codes_inventory[pkg]) > 0:
        code = codes_inventory[pkg].pop(0)
        bot.send_message(call.message.chat.id, t["purchase_success"].format(pkg, prices[pkg], code, ADMIN_CONTACT, CHANNEL_PROOFS), parse_mode="Markdown")
        
        admin_msg = (f"🔔 *عملية بيع جديدة!* 🔔\n━━━━━━━━━━━━\n"
                     f"👤 الزبون: @{call.from_user.username}\n"
                     f"📦 الفئة: {pkg} 💎\n"
                     f"💰 الثمن: {prices[pkg]} درهم\n"
                     f"🔑 الكود: `{code}`\n"
                     f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}\n━━━━━━━━━━━━\n"
                     f"✅ *تم التسليم آلياً*")
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        
        conn = sqlite3.connect('moslim_store.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET purchases = purchases || ? || '\n' WHERE user_id=?",
                       (f"📦 {pkg}💎 ({prices[pkg]} DH): {code} - {datetime.now().strftime('%Y-%m-%d')}", call.from_user.id))
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(call.id, t["confirm_purchase"])
    else:
        bot.answer_callback_query(call.id, t["out_of_stock"], show_alert=True)

if __name__ == "__main__":
    keep_alive()
    print("✅ متجر مسلم يعمل بكفاءة مع ترجمة كاملة واختيار لغة أفقي!")
    bot.infinity_polling()
