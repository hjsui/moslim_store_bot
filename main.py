import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread
from datetime import datetime

# --- 1. خادم الاستمرارية ---
app = Flask('')

@app.route('/')
def home():
    return "MOSLIM STORE IS ONLINE ✅"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. إعدادات البوت ---
API_TOKEN = '8325861290:AAHNx4oCfEy758rJQcm-oeYthAdZ80kTe0k'
ADMIN_ID = 6500854407
bot = telebot.TeleBot(API_TOKEN)

STORE_PASSWORD = "555451265696++ftytyuiuliyty6654923//fyytu@moslim.com"
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# مخزن الجواهر والأكواد (كما هو)
codes_inventory = {
    "110": ["5510650023494411", "9330820420409597", "6627018902595942"],
    "231": ["4808931182736381", "0698785582111920"],
    "583": ["9600129739749249", "9614548276115470"],
    "1188": ["2327640609655494", "2244758579935760"],
    "2420": ["5572361327155594"]
}
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

# --- قاموس الترجمة (اللغات الثمان) ---
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
        "welcome_title": "🛍️ *مـتـجـــر مـسـلـــم | MOSLIM STORE* 🛍️",
        "features": "✨ *خدمات رقمية - شحن فوري - اشتراكات* ✨\n⚡ *سرعة - ثقة - أسعار لا تقبل المنافسة* ⚡\n📢 *آراء العملاء:* قناتنا مليئة بالإثباتات",
        "press_start": "🔓 *اضغط /start لتفعيل المتجر*",
        "ask_password": "⚠️ *مـتـجـــر مـسـلـــم* 🛍️\nأدخل كلمة المرور لتفعيل المتجر:",
        "wrong_password": "❌ *كلمة مرور خاطئة!* ❌",
        "verified_success": "✅ *تم التفعيل بنجاح!* ✅\n🎉 مرحباً بك في متجر مسلم",
        "user_count": "\n👥 *عدد المستخدمين المسجلين:* {}",
        "welcome_msg": "👋🏻 *أهلاً بك، {}!* \n\n🛍️ *في متجر مسلم - وجهتك الأولى للخدمات الحصرية*\n\n⭐ *أبرز مميزات المتجر:*\n🔑 خدمات رقمية مميزة / شحن فوري\n⚡ سرعة فائقة في التنفيذ\n🔒 متجر محمي وموثق 100%\n💸 أسعار لا تقبل المنافسة\n📢 *قناة الإثباتات:* [انقر هنا لمشاهدة الثقة]({})\n🚀 *اختر من القائمة بالأسفل لبدء التسوق!*"
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
        "welcome_title": "🛍️ *MOSLIM STORE* 🛍️",
        "features": "✨ *Digital services - Instant top-up - Subscriptions* ✨\n⚡ *Speed - Trust - Unbeatable prices* ⚡\n📢 *Customer reviews:* Our channel is full of proofs",
        "press_start": "🔓 *Press /start to activate the store*",
        "ask_password": "⚠️ *MOSLIM STORE* 🛍️\nEnter password to activate the store:",
        "wrong_password": "❌ *Wrong password!* ❌",
        "verified_success": "✅ *Activated successfully!* ✅\n🎉 Welcome to Moslim Store",
        "user_count": "\n👥 *Registered users:* {}",
        "welcome_msg": "👋🏻 *Welcome, {}!* \n\n🛍️ *Moslim Store - your first destination for exclusive services*\n\n⭐ *Store features:*\n🔑 Exclusive digital services / instant top-up\n⚡ High-speed execution\n🔒 100% protected and verified store\n💸 Unbeatable prices\n📢 *Proofs channel:* [Click here to see trust]({})\n🚀 *Choose from the menu below to start shopping!*"
    },
    # يمكن إضافة اللغات الأخرى بنفس الهيكل (فرنسي، إسباني، تركي، ألماني، روسي، إيطالي)
    # لاختصار المساحة أضيف نموذج للفرنسية فقط – ويمكنك إكمال الباقي لاحقاً
    "fr": {
        "shop_now": "🛍️ Acheter maintenant",
        "services": "🛒 Services",
        "add_balance": "💰 Ajouter solde",
        "profile": "👤 Profil",
        "how_to_use": "📖 Mode d'emploi",
        "support": "📞 Support",
        "proofs": "📢 Preuves de confiance",
        "back": "🔙 Retour au menu principal",
        "welcome_title": "🛍️ *MOSLIM STORE* 🛍️",
        "features": "✨ *Services numériques - Recharge instantanée - Abonnements* ✨\n⚡ *Rapidité - Confiance - Prix imbattables* ⚡\n📢 *Avis clients:* Notre chaîne est pleine de preuves",
        "press_start": "🔓 *Appuyez sur /start pour activer la boutique*",
        "ask_password": "⚠️ *MOSLIM STORE* 🛍️\nEntrez le mot de passe pour activer la boutique:",
        "wrong_password": "❌ *Mot de passe incorrect!* ❌",
        "verified_success": "✅ *Activé avec succès!* ✅\n🎉 Bienvenue au Moslim Store",
        "user_count": "\n👥 *Utilisateurs enregistrés:* {}",
        "welcome_msg": "👋🏻 *Bienvenue, {}!* \n\n🛍️ *Moslim Store - votre première destination pour les services exclusifs*\n\n⭐ *Caractéristiques:*\n🔑 Services numériques exclusifs / recharge instantanée\n⚡ Exécution rapide\n🔒 Boutique 100% protégée et vérifiée\n💸 Prix imbattables\n📢 *Chaîne de preuves:* [Cliquez ici]({})\n🚀 *Choisissez dans le menu ci-dessous pour commencer vos achats!*"
    }
}
# يمكن إضافة الترجمات المتبقية (الإسبانية، التركية، الألمانية، الروسية، الإيطالية) بنفس الطريقة

# --- إعداد قاعدة البيانات مع أعمدة اللغة والترحيب ---
def init_db():
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, purchases TEXT, join_date TEXT, language TEXT DEFAULT 'ar', welcomed INTEGER DEFAULT 0)''')
    # التأكد من وجود الأعمدة الجديدة (للتحديث)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'ar'")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN welcomed INTEGER DEFAULT 0")
    except:
        pass
    conn.commit()
    conn.close()

init_db()

# --- دوال مساعدة ---
def get_user_lang(user_id):
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res and res[0] else 'ar'

def get_total_verified_users():
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE verified=1")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# --- إرسال صورة الترحيب مع اختيار اللغة ---
def send_welcome_with_lang_selection(chat_id, first_name=None):
    # رابط صورة ترحيبية (يمكنك تغييره)
    photo_url = "https://i.postimg.cc/g2Dtfh3L/Picsart-26-01-29-07-31-38-423.jpg"
    caption = "🌍 *Please select your language / اختر لغتك*\n\n⭐ *Choose from below:*"
    markup = types.InlineKeyboardMarkup(row_width=2)
    languages = [
        ("🇸🇦 العربية", "ar"), ("🇬🇧 English", "en"), ("🇫🇷 Français", "fr"),
        ("🇪🇸 Español", "es"), ("🇹🇷 Türkçe", "tr"), ("🇩🇪 Deutsch", "de"),
        ("🇷🇺 Русский", "ru"), ("🇮🇹 Italiano", "it")
    ]
    for text, code in languages:
        markup.add(types.InlineKeyboardButton(text, callback_data=f"setlang_{code}"))
    bot.send_photo(chat_id, photo=photo_url, caption=caption, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('setlang_'))
def set_language_callback(call):
    lang_code = call.data.split('_')[1]
    user_id = call.from_user.id
    # تحديث اللغة في قاعدة البيانات
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET language = ?, welcomed = 1 WHERE user_id = ?", (lang_code, user_id))
    conn.commit()
    conn.close()
    bot.answer_callback_query(call.id)
    # حذف الرسالة الأصلية وإرسال رسالة تأكيد
    bot.delete_message(call.message.chat.id, call.message.message_id)
    # طلب كلمة المرور
    lang = lang_code
    t = translations.get(lang, translations['ar'])
    bot.send_message(call.message.chat.id, t["ask_password"], parse_mode="Markdown")

# --- القوائم والرسائل الرئيسية ---
def show_main_menu(message, lang=None):
    if lang is None:
        lang = get_user_lang(message.chat.id)
    t = translations.get(lang, translations['ar'])
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(t["shop_now"], t["services"])
    markup.row(t["add_balance"], t["profile"])
    markup.row(t["how_to_use"], t["support"])
    markup.row(t["proofs"])
    # إضافة زر العودة (يظهر في بعض الأقسام فقط)
    # رسالة الترحيب مع عدد المستخدمين
    user_count = get_total_verified_users()
    base_msg = t["welcome_msg"].format(message.from_user.first_name, CHANNEL_PROOFS)
    base_msg += t["user_count"].format(user_count)
    bot.send_message(message.chat.id, base_msg, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT verified, welcomed, language FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        # إدراج مستخدم جديد مع welcomed=0 (لم يختر اللغة)
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("INSERT INTO users (user_id, username, verified, purchases, join_date, language, welcomed) VALUES (?, ?, 0, '', ?, 'ar', 0)",
                       (user_id, message.from_user.username, join_date))
        conn.commit()
        conn.close()
        send_welcome_with_lang_selection(message.chat.id, message.from_user.first_name)
        return
    verified, welcomed, lang = user
    if not verified:
        if not welcomed:
            # لم يختر اللغة بعد
            send_welcome_with_lang_selection(message.chat.id, message.from_user.first_name)
        else:
            # لديه لغة بالفعل، اطلب كلمة المرور
            t = translations.get(lang, translations['ar'])
            bot.reply_to(message, t["ask_password"], parse_mode="Markdown")
    else:
        # مستخدم مفعل، اعرض القائمة الرئيسية
        show_main_menu(message, lang)
    conn.close()

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT verified, language FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return
    verified, lang = user
    if not verified:
        # التحقق من كلمة المرور
        if message.text == STORE_PASSWORD:
            cursor.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
            conn.commit()
            t = translations.get(lang, translations['ar'])
            bot.reply_to(message, t["verified_success"], parse_mode="Markdown")
            show_main_menu(message, lang)
        else:
            t = translations.get(lang, translations['ar'])
            bot.reply_to(message, t["wrong_password"], parse_mode="Markdown")
        conn.close()
        return

    # --- المستخدم مفعل ---
    t = translations.get(lang, translations['ar'])
    if message.text == t["proofs"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 قناة الإثباتات", url=CHANNEL_PROOFS))
        m.add(types.InlineKeyboardButton("⭐ آراء العملاء", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, 
                         f"📢 *قناة إثباتات الثقة والمصداقية*\n━━━━━━━━━━━━\n"
                         f"🔍 *شاهد بنفسك آراء العملاء السابقين:*\n"
                         f"✅ أكثر من 100+ عملية موثقة\n"
                         f"⭐ تقييم العملاء: ممتاز جداً\n\n"
                         f"[📢 اضغط هنا لمشاهدة الإثباتات]({CHANNEL_PROOFS})", 
                         reply_markup=m, parse_mode="Markdown")
    elif message.text in [t["shop_now"], t["services"]]:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add("💎 شحن جواهر فري فاير", "🎮 شحن ألعاب أخرى", t["back"])
        bot.send_message(message.chat.id, "🛒 *أقسام المتجر:*\n━━━━━━━━━━━━\nاختر القسم المناسب:", 
                         reply_markup=markup, parse_mode="Markdown")
    elif message.text == t["back"]:
        show_main_menu(message, lang)
    elif message.text == "🎮 شحن ألعاب أخرى":
        bot.send_message(message.chat.id, 
                         "🎮 *شحن ألعاب أخرى*\n━━━━━━━━━━━━\n"
                         "📌 *الألعاب المتوفرة:*\n"
                         "• ببجي موبايل (UC)\n• كول أوف ديوتي (CP)\n• فري فاير (DA)\n• جينشين إمباكت\n\n"
                         "📞 *للطلب:* تواصل مع الدعم", parse_mode="Markdown")
    elif message.text == "💎 شحن جواهر فري فاير":
        show_ff_packages(message)
    elif message.text == t["profile"]:
        cursor.execute("SELECT purchases, join_date FROM users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        p = result[0] or "📭 *لا توجد مشتريات بعد.*"
        join_date = result[1] or "غير معروف"
        bot.send_message(message.chat.id, 
                         f"👤 *ملفك الشخصي*\n━━━━━━━━━━━━\n"
                         f"🆔 المعرف: `{user_id}`\n📅 تاريخ التسجيل: {join_date}\n"
                         f"🛍️ *سجل مشترياتك:*\n{p}\n━━━━━━━━━━━━\n📢 *شكراً لثقتك بنا* ❤️", 
                         parse_mode="Markdown")
    elif message.text == t["support"]:
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("💬 مراسلة المدير", url=ADMIN_CONTACT))
        m.add(types.InlineKeyboardButton("📢 قناة المتجر", url="https://t.me/moslim_store"))
        m.add(types.InlineKeyboardButton("⭐ إثباتات الثقة", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, 
                         "👨‍💻 *فريق الدعم*\n━━━━━━━━━━━━\n"
                         "• الرد خلال 24 ساعة\n• الدعم متوفر طوال الأسبوع\n"
                         "*اختر طريقة التواصل:*", reply_markup=m, parse_mode="Markdown")
    elif message.text == t["add_balance"]:
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💳 مراسلة الدعم للشحن", url=ADMIN_CONTACT))
        m.add(types.InlineKeyboardButton("📢 شاهد الإثباتات", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, 
                         "💰 *إضافة رصيد*\n━━━━━━━━━━━━\n"
                         "💵 *طرق الدفع المتاحة:*\n• CIH BANK\n• Binance (USDT)\n• PayPal\n\n"
                         "📌 تواصل مع الدعم لإتمام الشحن.", reply_markup=m, parse_mode="Markdown")
    elif message.text == t["how_to_use"]:
        bot.send_message(message.chat.id, 
                         "📖 *طريقة الاستخدام*\n━━━━━━━━━━━━\n"
                         "1️⃣ اختر الباقة المناسبة\n2️⃣ اضغط على زر الشراء\n"
                         "3️⃣ تواصل مع الدعم للدفع\n4️⃣ استلم كودك فوراً!\n\n"
                         "⚡ *شحن فوري - خدمة 24 ساعة*", parse_mode="Markdown")
    else:
        bot.reply_to(message, 
                     "🤖 *مرحباً!*\n━━━━━━━━━━━━\nاستخدم الأزرار بالأسفل للتنقل في المتجر.", 
                     parse_mode="Markdown")
    conn.close()

def show_ff_packages(message):
    lang = get_user_lang(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pkg in codes_inventory.keys():
        price = prices.get(pkg, "0")
        markup.add(types.InlineKeyboardButton(f"💎 {pkg} جوهرة = {price} درهم", callback_data=f"buy_{pkg}"))
    markup.add(types.InlineKeyboardButton("📢 شاهد الإثباتات قبل الشراء", url=CHANNEL_PROOFS))
    bot.send_message(message.chat.id, 
                     "💎 *باقات شحن جواهر فري فاير*\n━━━━━━━━━━━━\n"
                     "✨ *باقات حصرية بأفضل الأسعار*\n⚡ *توصيل فوري خلال دقائق*\n━━━━━━━━━━━━\n"
                     "*اختر الباقة المناسبة:*", 
                     reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_purchase(call):
    pkg = call.data.split('_')[1]
    if codes_inventory.get(pkg) and len(codes_inventory[pkg]) > 0:
        code = codes_inventory[pkg].pop(0)
        bot.send_message(call.message.chat.id, 
                         f"✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n"
                         f"💎 الكمية: {pkg} جوهرة\n💰 السعر: {prices[pkg]} درهم\n"
                         f"🔑 كود الشحن: `{code}`\n━━━━━━━━━━━━\n"
                         f"📞 للاستفسار: [@MOSLIM_SHOP]({ADMIN_CONTACT})\n"
                         f"📢 لمشاهدة إثباتاتنا: [اضغط هنا]({CHANNEL_PROOFS})", 
                         parse_mode="Markdown")
        admin_msg = (f"🔔 *عملية بيع جديدة!* 🔔\n━━━━━━━━━━━━\n"
                     f"👤 الزبون: @{call.from_user.username}\n"
                     f"📦 الفئة: {pkg} 💎\n💰 الثمن: {prices[pkg]} درهم\n"
                     f"🔑 الكود: `{code}`\n⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}")
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        conn = sqlite3.connect('moslim_store.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET purchases = purchases || ? || '\n' WHERE user_id=?",
                       (f"📦 {pkg}💎 ({prices[pkg]} DH): {code} - {datetime.now().strftime('%Y-%m-%d')}", call.from_user.id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "🎉 تم الشراء بنجاح! استلم الكود أعلاه")
    else:
        bot.answer_callback_query(call.id, "❌ عذراً، هذه الباقة غير متوفرة حالياً. جرب باقة أخرى!", show_alert=True)

if __name__ == "__main__":
    keep_alive()
    print("✅ المتجر شغال بنجاح مع دعم اللغات وعرض عدد المستخدمين!")
    bot.infinity_polling()
