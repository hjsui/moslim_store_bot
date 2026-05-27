import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread
from datetime import datetime
import time
import random
import string
import os
import requests
import json
from collections import defaultdict

# ------------------- 1. خادم الاستمرارية -------------------
app = Flask('')

@app.route('/')
def home():
    return "MOSLIM STORE IS ONLINE ✅"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------- 2. إعدادات البوت -------------------
# ضع التوكن الحقيقي بدلاً من هذا المثال
BOT_TOKEN = "8325861290:AAEz_RWg1sFCyvw7brpzY4vWqgZl7tzan6U"   # <--- استبدله بتوكن البوت الحقيقي

ADMIN_IDS = [int(x.strip()) for x in os.environ.get('ADMIN_IDS', '').split(',') if x.strip()]
WHITELISTED_USERS = [int(x.strip()) for x in os.environ.get('WHITELISTED_USERS', '').split(',') if x.strip()]
STORE_PASSWORD = os.environ.get('STORE_PASSWORD', 'default123')
LOG_CHANNEL_ID = os.environ.get('LOG_CHANNEL_ID')
if LOG_CHANNEL_ID:
    LOG_CHANNEL_ID = int(LOG_CHANNEL_ID)

# AI settings
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
AI_MODEL = os.environ.get('AI_MODEL', 'llama3-70b-8192')
AI_API_URL = "https://api.groq.com/openai/v1/chat/completions"

bot = telebot.TeleBot(BOT_TOKEN)
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# Rate limiting
user_last_msg = defaultdict(float)
RATE_LIMIT_SEC = 10  # seconds between messages

def is_rate_limited(user_id):
    now = time.time()
    if now - user_last_msg[user_id] < RATE_LIMIT_SEC:
        return True
    user_last_msg[user_id] = now
    return False

# ------------------- 3. دوال المساعد -----------------------------------
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_whitelisted(user_id):
    return user_id in WHITELISTED_USERS

# ------------------- 4. قاعدة البيانات المتطورة -------------------
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
    c.execute('''CREATE TABLE IF NOT EXISTS ff_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, quantity TEXT, code TEXT, used INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS key_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, duration TEXT, code TEXT, used INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# ترحيل الأكواد القديمة (مرة واحدة)
def migrate_old_codes():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ff_codes")
    if c.fetchone()[0] == 0:
        old_ff = {
            "110": ["2832586864754929", "2869135500382282", "8772380136887137", "0510503734238548", "9317053383056636", "8344827763739908"],
            "231": ["8924464665769889", "7222546102183551", "6019105566204732", "6266884345783498", "5934678521152776", "5582470301677821"],
            "583": ["5665636272178740", "8171354030947632", "0689246122768008", "2191436437180436", "2409185512395486", "4479277919446726"],
            "1188": ["0157588037982228", "2514893008691065", "9405455819525108"],
            "2420": ["8054042222321677", "7801845005665882", "7240425674452852"]
        }
        for qty, codes in old_ff.items():
            for code in codes:
                c.execute("INSERT INTO ff_codes (quantity, code, used) VALUES (?,?,0)", (qty, code))
        old_keys = {"dripclient": {"1": ["8704258740"], "30": ["6732684380", "7481744555"]}}
        for prod_id, dur_dict in old_keys.items():
            for dur, codes in dur_dict.items():
                for code in codes:
                    c.execute("INSERT INTO key_codes (product_id, duration, code, used) VALUES (?,?,?,0)", (prod_id, dur, code))
        conn.commit()
    conn.close()

migrate_old_codes()

# دوال المخزون
def get_ff_code(quantity):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT id, code FROM ff_codes WHERE quantity=? AND used=0 LIMIT 1", (quantity,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE ff_codes SET used=1 WHERE id=?", (row[0],))
        conn.commit()
        conn.close()
        return row[1]
    conn.close()
    return None

def add_ff_code(quantity, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO ff_codes (quantity, code, used) VALUES (?,?,0)", (quantity, code))
    conn.commit()
    conn.close()

def del_ff_code(quantity, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("DELETE FROM ff_codes WHERE quantity=? AND code=? AND used=0 LIMIT 1", (quantity, code))
    conn.commit()
    conn.close()
    return c.rowcount > 0

def get_ff_stock():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT quantity, COUNT(*) FROM ff_codes WHERE used=0 GROUP BY quantity")
    rows = c.fetchall()
    conn.close()
    return rows

def get_key_code(product_id, duration):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT id, code FROM key_codes WHERE product_id=? AND duration=? AND used=0 LIMIT 1", (product_id, duration))
    row = c.fetchone()
    if row:
        c.execute("UPDATE key_codes SET used=1 WHERE id=?", (row[0],))
        conn.commit()
        conn.close()
        return row[1]
    conn.close()
    return None

def add_key_code(product_id, duration, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO key_codes (product_id, duration, code, used) VALUES (?,?,?,0)", (product_id, duration, code))
    conn.commit()
    conn.close()

def del_key_code(product_id, duration, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("DELETE FROM key_codes WHERE product_id=? AND duration=? AND code=? AND used=0 LIMIT 1", (product_id, duration, code))
    conn.commit()
    conn.close()
    return c.rowcount > 0

def get_key_stock():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT product_id, duration, COUNT(*) FROM key_codes WHERE used=0 GROUP BY product_id, duration")
    rows = c.fetchall()
    conn.close()
    return rows

# ------------------- 5. دوال القاعدة العامة -------------------
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

def add_purchase_record(user_id, record):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE users SET purchases = COALESCE(purchases, '') || ? || '\n' WHERE user_id=?", (record, user_id))
    conn.commit()
    conn.close()

# ------------------- 6. الطلبات -------------------
def generate_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_order(user_id, product_type, product_id, amount):
    order_id = generate_order_id()
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO orders (order_id, user_id, product_type, product_id, amount, status, timestamp) VALUES (?,?,?,?,?,?,?)",
              (order_id, user_id, product_type, product_id, amount, 'pending', datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status, proof_photo_id=None, admin_action=None):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    if proof_photo_id:
        c.execute("UPDATE orders SET status=?, proof_photo_id=? WHERE order_id=?", (status, proof_photo_id, order_id))
    elif admin_action:
        c.execute("UPDATE orders SET status=?, admin_action=? WHERE order_id=?", (status, admin_action, order_id))
    else:
        c.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
    conn.commit()
    conn.close()

def get_order(order_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT * FROM orders WHERE order_id=?", (order_id,))
    row = c.fetchone()
    conn.close()
    return row

# ------------------- 7. طرق الدفع -------------------
PAYMENT_METHODS = {
    "cih": {
        "name_ar": "🏦 CIH BANK",
        "name_en": "🏦 CIH BANK",
        "details_ar": "الاسم: MOSLIM STORE\nRIB: <code>6899904211035500</code>\nR.I.P BANCAIRE: <code>230480689990421103550036</code>",
        "details_en": "Name: MOSLIM STORE\nRIB: <code>6899904211035500</code>\nR.I.P: <code>230480689990421103550036</code>",
    },
    "barid": {
        "name_ar": "🏦 BARID BANK",
        "name_en": "🏦 BARID BANK",
        "details_ar": "الاسم: MOSLIM ELOMARI\nرقم الحساب: <code>13958215</code>",
        "details_en": "Name: MOSLIM ELOMARI\nAccount: <code>13958215</code>",
    },
    "cashplus": {
        "name_ar": "🏦 CASH PLUS",
        "name_en": "🏦 CASH PLUS",
        "details_ar": "رقم الحساب: <code>0723644027</code>",
        "details_en": "Account: <code>0723644027</code>",
    },
    "binance": {
        "name_ar": "💰 Binance",
        "name_en": "💰 Binance",
        "details_ar": "𝙄𝘿: <code>1208575784</code>\n𝙉𝘼𝙈𝙀: مـتـجـــر مـسـلـــم",
        "details_en": "ID: <code>1208575784</code>\nNAME: MOSLIM STORE",
    }
}

# ------------------- 8. الترجمة -------------------
T = {
    "ar": {
        "shop_now": "🛍️ تسوق الآن",
        "services": "🛒 الخدمات",
        "add_balance": "💰 إضافة رصيد",
        "profile": "👤 الملف الشخصي",
        "how_to_use": "📖 طريقة الاستخدام",
        "support": "📞 الدعم الفني",
        "proofs": "📢 إثباتات الثقة",
        "back_to_main": "🔙 العودة للقائمة الرئيسية",
        "back_to_sections": "🔙 العودة لأقسام المتجر",
        "back_to_ff_services": "🔙 العودة لخدمات فري فاير",
        "back_to_products": "🔙 العودة للمنتجات",
        "ff_services": "🎮 خدمات فري فاير",
        "other_games": "🎮 شحن ألعاب أخرى",
        "apps_service": "📱 اشتراكات التطبيقات",
        "ff_topup": "💎 شحن جواهر فري فاير",
        "keys_service": "🔑 إنشاء مفاتيح الهكرات",
        "choose_product": "🔍 *اختر نوع المنتج:*",
        "choose_validity": "📅 *اختر المدة:*",
        "choose_app": "🔍 *اختر التطبيق الذي تريده:*",
        "choose_payment": "💳 *اختر طريقة الدفع:*",
        "ask_proof": "📸 *أرسل صورة إثبات الدفع الآن*",
        "proof_received": "📸 تم استلام إثبات الدفع بنجاح!\n🔄 جاري معالجة طلبك آلياً... سيتم التسليم خلال دقائق.\n💚 شكراً لانتظارك، نحن نعمل بسرعة لإرضائك.",
        "order_accepted": "✅ *تم قبول طلبك بنجاح!* ✅\n━━━━━━━━━━━━\n📦 المنتج: {}\n💰 السعر: {} درهم\n🔗 رابط التحميل: [اضغط هنا]({})\n📢 لمتابعة التحديثات: [انضم للقناة]({})\n━━━━━━━━━━━━\n📞 للاستفسار: [@MOSLIM_SHOP]({})\n📢 لمشاهدة إثباتاتنا: [اضغط هنا]({})",
        "order_rejected": "❌ *عذراً، تم رفض طلبك* ❌\n━━━━━━━━━━━━\n📦 المنتج: {}\n⚠️ يرجى التحقق من صحة إثبات الدفع وإعادة المحاولة.\n━━━━━━━━━━━━\n💡 يمكنك الضغط على الزر أدناه لتغيير طريقة الدفع.",
        "already_paid": "⚠️ لديك طلب قيد المراجعة بالفعل. يرجى الانتظار أو التواصل مع الدعم.",
        "keys_purchase_success": "✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n📦 المنتج: {}\n🗓️ المدة: {} يوم\n💰 السعر: {} 💰\n🔑 مفتاحك: `{}`\n━━━━━━━━━━━━\n📞 للاستفسار: [@MOSLIM_SHOP]({})\n📢 لمشاهدة إثباتاتنا: [اضغط هنا]({})",
        "no_stock": "❌ عذراً، لا توجد مفاتيح متوفرة لهذه المدة حالياً.",
        "app_no_stock": "❌ هذا التطبيق غير متوفر حالياً. جرب تطبيقاً آخر.",
        "choose_section": "🛒 *أقسام المتجر:*\n━━━━━━━━━━━━\nاختر القسم المناسب:",
        "other_games_text": "🎮 *شحن ألعاب أخرى*\n━━━━━━━━━━━━\n📌 *الألعاب المتوفرة:*\n• ببجي موبايل (UC)\n• كول أوف ديوتي (CP)\n• فري فاير (DA)\n• جينشين إمباكت\n\n📞 *للطلب:* تواصل مع الدعم",
        "ff_packages_title": "💎 *باقات شحن جواهر فري فاير*\n━━━━━━━━━━━━\n✨ *باقات حصرية بأفضل الأسعار*\n⚡ *توصيل فوري خلال دقائق*\n━━━━━━━━━━━━\n*اختر الباقة المناسبة:*",
        "ask_password": "⚠️ *مـتـجـــر مـسـلـــم* 🛍️\nأدخل كلمة المرور لتفعيل المتجر:",
        "wrong_password": "❌ *كلمة مرور خاطئة!* ❌",
        "verified_success": "✅ *تم التفعيل بنجاح!* ✅\n🎉 مرحباً بك في متجر مسلم",
        "user_count": "\n👥 *عدد المستخدمين المسجلين:* {}",
        "welcome_main": "👋🏻 *أهلاً بك، {}!*\n\n🛍️ *في متجر مسلم - وجهتك الأولى للخدمات الحصرية*\n\n⭐ *أبرز مميزات المتجر:*\n🔑 خدمات رقمية مميزة / شحن فوري\n⚡ سرعة فائقة في التنفيذ\n🔒 متجر محمي وموثق 100%\n💸 أسعار لا تقبل المنافسة\n📢 *قناة الإثباتات:* [انقر هنا لمشاهدة الثقة]({})\n🚀 *اختر من القائمة بالأسفل لبدء التسوق!*",
        "profile_text": "👤 *ملفك الشخصي*\n━━━━━━━━━━━━\n🆔 المعرف: `{}`\n📅 تاريخ التسجيل: {}\n🛍️ *سجل مشترياتك:*\n{}\n━━━━━━━━━━━━\n📢 *شكراً لثقتك بنا* ❤️",
        "support_text": "👨‍💻 *فريق الدعم*\n━━━━━━━━━━━━\n• الرد خلال 24 ساعة\n• الدعم متوفر طوال الأسبوع\n• للمشاكل والاستفسارات\n━━━━━━━━━━━━\n*اختر طريقة التواصل:*",
        "add_balance_text": "💰 *إضافة رصيد*\n━━━━━━━━━━━━\n💵 *طرق الدفع المتاحة:*\n• CIH BANK\n• Binance (USDT)\n• PayPal\n• واتساب\n\n📌 *خطوات الشحن:*\n1️⃣ تواصل مع الدعم\n2️⃣ أرسل المبلغ المطلوب\n3️⃣ استلم الرصيد فوراً\n\n✨ *خدمة آمنة وسريعة*",
        "how_to_use_text": "📖 *طريقة الاستخدام*\n━━━━━━━━━━━━\n📌 *خطوات الشراء:*\n1️⃣ اختر الباقة المناسبة\n2️⃣ اضغط على زر الشراء\n3️⃣ اختر طريقة الدفع\n4️⃣ أرسل صورة الإثبات\n5️⃣ بعد الموافقة، استلم منتجك\n\n⚡ *شحن فوري - خدمة 24 ساعة*\n🔒 *ضمان استرجاع الأموال في حال وجود مشكلة*",
        "proofs_text": "📢 *قناة إثباتات الثقة والمصداقية*\n━━━━━━━━━━━━\n🔍 *شاهد بنفسك آراء العملاء السابقين:*\n✅ أكثر من 100+ عملية موثقة\n⭐ تقييم العملاء: ممتاز جداً\n\n[📢 اضغط هنا لمشاهدة الإثباتات]({})",
        "purchase_success": "✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n💎 الكمية: {} جوهرة\n💰 السعر: {} درهم\n🔑 كود الشحن: `{}`\n━━━━━━━━━━━━\n📞 للاستفسار: [@MOSLIM_SHOP]({})\n📢 لمشاهدة إثباتاتنا: [اضغط هنا]({})",
        "out_of_stock": "❌ عذراً، هذه الباقة غير متوفرة حالياً. جرب باقة أخرى!",
        "confirm_purchase": "🎉 تم الشراء بنجاح! استلم الكود أعلاه",
        "welcome_after_lang": "🛍️ *مـتـجـــر مـسـلـــم | MOSLIM STORE* 🛍️\n━━━━━━━━━━━━━━━━━━━━\n✨ *خدمات رقمية - شحن فوري - اشتراكات* ✨\n⚡ *سرعة - ثقة - أسعار لا تقبل المنافسة* ⚡\n📢 *آراء العملاء:* [قناتنا مليئة بالإثباتات]({})\n━━━━━━━━━━━━━━━━━━━━\n🔓 *اضغط /start لتفعيل المتجر* 🔓",
        "default_reply": "🤖 *مرحباً!*\n━━━━━━━━━━━━\nاستخدم الأزرار بالأسفل للتنقل في المتجر.\n📢 وللتأكد من مصداقيتنا: [شاهد الإثباتات]({})",
        "inline_proofs_btn": "📢 قناة الإثباتات",
        "ai_chat": "💬 اسأل المساعد الذكي",
        "ai_welcome": "🧠 *مرحباً بك في المساعد الذكي لمتجر مسلم!*\nيمكنك سؤالي عن أي منتج، طريقة الشراء، أو حتى طلب مساعدة.\n\n📌 *أمثلة:*\n- كيف أشحن جواهر فري فاير؟\n- ما هي أسعار التطبيقات؟\n- ساعدني في اختيار باقة\n\n✍️ *اكتب سؤالك الآن (أو /exit للخروج)*",
        "ai_processing": "🤔 *جاري التفكير...*",
        "ai_error": "⚠️ عذراً، الذكاء الاصطناعي غير متاح حالياً. تواصل مع الدعم.",
        "ai_exit": "🔚 تم الخروج من وضع المساعد. يمكنك العودة بالضغط على الزر."
    },
    "en": {
        "shop_now": "🛍️ Shop Now",
        "services": "🛒 Services",
        "add_balance": "💰 Add Balance",
        "profile": "👤 Profile",
        "how_to_use": "📖 How to use",
        "support": "📞 Support",
        "proofs": "📢 Trust Proofs",
        "back_to_main": "🔙 Back to Main Menu",
        "back_to_sections": "🔙 Back to Store Sections",
        "back_to_ff_services": "🔙 Back to Free Fire Services",
        "back_to_products": "🔙 Back to Products",
        "ff_services": "🎮 Free Fire Services",
        "other_games": "🎮 Other Games Top-up",
        "apps_service": "📱 App Subscriptions",
        "ff_topup": "💎 Free Fire Diamonds Top-up",
        "keys_service": "🔑 Create Hacker Keys",
        "choose_product": "🔍 *Choose product type:*",
        "choose_validity": "📅 *Choose duration:*",
        "choose_app": "🔍 *Choose the app you want:*",
        "choose_payment": "💳 *Choose payment method:*",
        "ask_proof": "📸 *Send your payment proof screenshot now*",
        "proof_received": "📸 Payment proof received successfully!\n🔄 Automatically processing your order... Delivery within minutes.\n💚 Thank you for waiting, we work fast for you.",
        "order_accepted": "✅ *Your order has been accepted!* ✅\n━━━━━━━━━━━━\n📦 Product: {}\n💰 Price: {} MAD\n🔗 Download link: [Click here]({})\n📢 For updates: [Join channel]({})\n━━━━━━━━━━━━\n📞 Inquiries: [@MOSLIM_SHOP]({})\n📢 See proofs: [Click here]({})",
        "order_rejected": "❌ *Sorry, your order has been rejected* ❌\n━━━━━━━━━━━━\n📦 Product: {}\n⚠️ Please check your payment proof and try again.\n━━━━━━━━━━━━\n💡 Press the button below to change payment method.",
        "already_paid": "⚠️ You have a pending order. Please wait or contact support.",
        "keys_purchase_success": "✅ *Purchase successful!* ✅\n━━━━━━━━━━━━\n📦 Product: {}\n🗓️ Duration: {} days\n💰 Price: {} 💰\n🔑 Your key: `{}`\n━━━━━━━━━━━━\n📞 Inquiries: [@MOSLIM_SHOP]({})\n📢 See our proofs: [Click here]({})",
        "no_stock": "❌ Sorry, no keys available for this duration.",
        "app_no_stock": "❌ This app is currently unavailable. Try another app.",
        "choose_section": "🛒 *Store Sections:*\n━━━━━━━━━━━━\nChoose the appropriate section:",
        "other_games_text": "🎮 *Other Games Top-up*\n━━━━━━━━━━━━\n📌 *Available games:*\n• PUBG Mobile (UC)\n• Call of Duty (CP)\n• Free Fire (DA)\n• Genshin Impact\n\n📞 *To order:* Contact support",
        "ff_packages_title": "💎 *Free Fire Diamonds Packages*\n━━━━━━━━━━━━\n✨ *Exclusive packages at best prices*\n⚡ *Instant delivery in minutes*\n━━━━━━━━━━━━\n*Choose your package:*",
        "ask_password": "⚠️ *MOSLIM STORE* 🛍️\nEnter password to activate the store:",
        "wrong_password": "❌ *Wrong password!* ❌",
        "verified_success": "✅ *Activated successfully!* ✅\n🎉 Welcome to Moslim Store",
        "user_count": "\n👥 *Registered users:* {}",
        "welcome_main": "👋🏻 *Welcome, {}!*\n\n🛍️ *Moslim Store - your first destination for exclusive services*\n\n⭐ *Store features:*\n🔑 Exclusive digital services / instant top-up\n⚡ High-speed execution\n🔒 100% protected and verified store\n💸 Unbeatable prices\n📢 *Proofs channel:* [Click here to see trust]({})\n🚀 *Choose from the menu below to start shopping!*",
        "profile_text": "👤 *Your Profile*\n━━━━━━━━━━━━\n🆔 ID: `{}`\n📅 Registration date: {}\n🛍️ *Your purchases:*\n{}\n━━━━━━━━━━━━\n📢 *Thank you for trusting us* ❤️",
        "support_text": "👨‍💻 *Support Team*\n━━━━━━━━━━━━\n• Response within 24 hours\n• Support available all week\n• For issues and inquiries\n━━━━━━━━━━━━\n*Choose contact method:*",
        "add_balance_text": "💰 *Add Balance*\n━━━━━━━━━━━━\n💵 *Payment methods available:*\n• CIH BANK\n• Binance (USDT)\n• PayPal\n• WhatsApp\n\n📌 *Steps to add:*\n1️⃣ Contact support\n2️⃣ Send the required amount\n3️⃣ Receive balance instantly\n\n✨ *Secure and fast service*",
        "how_to_use_text": "📖 *How to Use*\n━━━━━━━━━━━━\n📌 *Purchase steps:*\n1️⃣ Choose package\n2️⃣ Click buy\n3️⃣ Choose payment method\n4️⃣ Send proof screenshot\n5️⃣ After approval, receive product\n\n⚡ *24/7 support*\n🔒 *Money-back guarantee*",
        "proofs_text": "📢 *Trust and Credibility Proofs Channel*\n━━━━━━━━━━━━\n🔍 *See previous customers' reviews:*\n✅ 100+ documented transactions\n⭐ Customer rating: Excellent\n\n[📢 Click here to see proofs]({})",
        "purchase_success": "✅ *Purchase successful!* ✅\n━━━━━━━━━━━━\n💎 Quantity: {} diamonds\n💰 Price: {} MAD\n🔑 Top-up code: `{}`\n━━━━━━━━━━━━\n📞 Inquiries: [@MOSLIM_SHOP]({})\n📢 To see our proofs: [Click here]({})",
        "out_of_stock": "❌ Sorry, this package is currently unavailable. Try another package!",
        "confirm_purchase": "🎉 Purchase successful! Get your code above",
        "welcome_after_lang": "🛍️ *MOSLIM STORE* 🛍️\n━━━━━━━━━━━━━━━━━━━━\n✨ *Digital services - Instant top-up - Subscriptions* ✨\n⚡ *Speed - Trust - Unbeatable prices* ⚡\n📢 *Customer reviews:* [Our channel is full of proofs]({})\n━━━━━━━━━━━━━━━━━━━━\n🔓 *Press /start to activate the store* 🔓",
        "default_reply": "🤖 *Hello!*\n━━━━━━━━━━━━\nUse the buttons below to navigate the store.\n📢 To verify our credibility: [See proofs]({})",
        "inline_proofs_btn": "📢 Proofs Channel",
        "ai_chat": "💬 Ask AI Assistant",
        "ai_welcome": "🧠 *Welcome to Moslim Store AI Assistant!*\nAsk me about products, purchase steps, or help.\n\n📌 *Examples:*\n- How to top up Free Fire diamonds?\n- App prices?\n- Help me choose a package\n\n✍️ *Type your question now (or /exit to quit)*",
        "ai_processing": "🤔 *Thinking...*",
        "ai_error": "⚠️ AI assistant is temporarily unavailable. Contact support.",
        "ai_exit": "🔚 Exited AI mode. You can return by pressing the button."
    }
}

# ------------------- 9. الذكاء الاصطناعي (Groq API) -------------------
user_ai_mode = set()

def ai_chat(user_message):
    if not GROQ_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    system_prompt = (
        "أنت مساعد ودود لمتجر Moslim Store الرقمي. المتجر يبيع: جواهر فري فاير، مفاتيح برامج، اشتراكات تطبيقات (CapCut, Inshot, Picsart). "
        "ساعد المستخدم بلطف، شجعه على الشراء، اشرح له الخطوات، لكن لا تغيره بطريقة تنويم مغناطيسي. قدم معلومات دقيقة عن الأسعار والمنتجات. "
        "إذا سأل عن شيء خارج المتجر، اعتذر بلطف ووجهه للدعم البشري. استخدم العربية أو الإنجليزية حسب لغة المستخدم."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 500
    }
    try:
        response = requests.post(AI_API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"AI error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"AI exception: {e}")
        return None

# ------------------- 10. واجهة المستخدم -------------------
def send_lang_selection(chat_id):
    photo_url = "https://i.postimg.cc/g2Dtfh3L/Picsart-26-01-29-07-31-38-423.jpg"
    caption = "🌍 *Please select your language / اختر لغتك*"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🇲🇦 العربية", callback_data="lang_ar"),
               types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"))
    bot.send_photo(chat_id, photo=photo_url, caption=caption, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def callback_lang(call):
    lang = call.data.split('_')[1]
    set_lang(call.from_user.id, lang)
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, T[lang]["welcome_after_lang"].format(CHANNEL_PROOFS), parse_mode="Markdown")

def show_main_menu(message, lang):
    t = T[lang]
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row(t["shop_now"], t["services"])
    markup.row(t["add_balance"], t["profile"])
    markup.row(t["how_to_use"], t["support"])
    markup.row(t["proofs"], t["ai_chat"])
    user_count = get_verified_count()
    msg = t["welcome_main"].format(message.from_user.first_name, CHANNEL_PROOFS) + t["user_count"].format(user_count)
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

def show_ai_welcome(message, lang):
    t = T[lang]
    user_ai_mode.add(message.from_user.id)
    bot.send_message(message.chat.id, t["ai_welcome"], parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    if is_rate_limited(message.from_user.id):
        return
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

# ------------------- 11. معالج الرسائل العامة -------------------
@bot.message_handler(func=lambda msg: True)
def handle_messages(message):
    if is_rate_limited(message.from_user.id):
        return
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

    if user_id in user_ai_mode:
        if message.text == '/exit':
            user_ai_mode.discard(user_id)
            bot.send_message(user_id, t["ai_exit"], parse_mode="Markdown")
            conn.close()
            return
        processing_msg = bot.send_message(user_id, t["ai_processing"], parse_mode="Markdown")
        ai_response = ai_chat(message.text)
        if ai_response:
            bot.edit_message_text(ai_response, chat_id=user_id, message_id=processing_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text(t["ai_error"], chat_id=user_id, message_id=processing_msg.message_id, parse_mode="Markdown")
        conn.close()
        return

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

    if text == t["ai_chat"]:
        show_ai_welcome(message, lang)
        conn.close()
        return

    if text in [t["shop_now"], t["services"]]:
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
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["other_games"], t["ff_services"])
        markup.add(t["back_to_main"], t["apps_service"])
        bot.send_message(message.chat.id, t["choose_section"], reply_markup=markup, parse_mode="Markdown")
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

# ------------------- 12. عرض المنتجات -------------------
def show_ff_packages(message, lang):
    t = T[lang]
    markup = types.InlineKeyboardMarkup(row_width=2)
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT quantity FROM ff_codes WHERE used=0")
    quantities = [row[0] for row in c.fetchall()]
    conn.close()
    prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}
    for qty in quantities:
        price = prices.get(qty, "?")
        markup.add(types.InlineKeyboardButton(f"💎 {qty} {'جوهرة' if lang=='ar' else 'diamonds'} = {price} {'درهم' if lang=='ar' else 'MAD'}", callback_data=f"buy_{qty}"))
    markup.add(types.InlineKeyboardButton("📢 " + ("شاهد الإثباتات قبل الشراء" if lang=='ar' else "See proofs before buying"), url=CHANNEL_PROOFS))
    bot.send_message(message.chat.id, t["ff_packages_title"], reply_markup=markup, parse_mode="Markdown")

def show_keys_products(message, lang):
    t = T[lang]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("🔑 DRIP CLIENT APKMOD 👾", callback_data="key_prod_dripclient"))
    bot.send_message(message.chat.id, t["choose_product"], reply_markup=markup, parse_mode="Markdown")

def show_apps_products(message, lang):
    t = T[lang]
    apps_inventory = {
        "capcut": {"name_ar": "🎬 CapCut PRO", "name_en": "🎬 CapCut PRO", "price": 20},
        "inshot": {"name_ar": "✂️ Inshot PRI", "name_en": "✂️ Inshot PRI", "price": 15},
        "picsart": {"name_ar": "🖌️ Picsart PRO", "name_en": "🖌️ Picsart PRO", "price": 25}
    }
    markup = types.InlineKeyboardMarkup(row_width=2)
    for app_id, app_data in apps_inventory.items():
        btn_text = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"app_buy_{app_id}"))
    bot.send_message(message.chat.id, t["choose_app"], reply_markup=markup, parse_mode="Markdown")

# ------------------- 13. نظام الدفع -------------------
def show_payment_methods(user_id, product_type, product_id, amount):
    lang = get_lang(user_id)
    t = T[lang]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, method in PAYMENT_METHODS.items():
        name = method["name_ar"] if lang == 'ar' else method["name_en"]
        markup.add(types.InlineKeyboardButton(name, callback_data=f"pay_{key}_{product_type}_{product_id}_{amount}"))
    bot.send_message(user_id, t["choose_payment"], reply_markup=markup, parse_mode="Markdown")

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
        app_data = {"capcut":"CapCut","inshot":"Inshot","picsart":"Picsart"}.get(product_id, "تطبيق")
        product_name = app_data

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
    bot.edit_message_text("📸 تم استلام إثبات الدفع! جاري مراجعته من قبل الإدارة قريباً.", chat_id=user_id, message_id=waiting_msg.message_id, parse_mode="Markdown")

# ------------------- 14. قبول ورفض الطلبات -------------------
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
            code = get_ff_code(product_id)
            if code:
                success_msg = t["purchase_success"].format(product_id, amount, code, ADMIN_CONTACT, CHANNEL_PROOFS)
                bot.send_message(user_id, success_msg, parse_mode="Markdown")
                add_purchase_record(user_id, f"📦 {product_id}💎 ({amount} DH): {code} - {datetime.now()}")
                update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                send_withdrawal_log(f"admin_{admin_id}", f"{product_id} جوهرة", amount, code_or_link=code)
            else:
                bot.send_message(user_id, t["out_of_stock"], parse_mode="Markdown")
                update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
        elif product_type == 'key':
            parts = product_id.split('_')
            if len(parts) == 2:
                key_id, days = parts[0], parts[1]
                code = get_key_code(key_id, days)
                if code:
                    product_name = "DRIP CLIENT APKMOD"
                    success_msg = t["keys_purchase_success"].format(product_name, days, amount, code, ADMIN_CONTACT, CHANNEL_PROOFS)
                    bot.send_message(user_id, success_msg, parse_mode="Markdown")
                    add_purchase_record(user_id, f"🔑 {product_name} ({days} يوم) - {amount} 💰: {code} - {datetime.now()}")
                    update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                    send_withdrawal_log(f"admin_{admin_id}", product_name, amount, extra_info=f"🗓️ المدة: {days} يوم\n", code_or_link=code)
                else:
                    bot.send_message(user_id, t["no_stock"], parse_mode="Markdown")
                    update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
            else:
                bot.send_message(user_id, t["no_stock"], parse_mode="Markdown")
                update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
        elif product_type == 'app':
            apps_links = {
                "capcut": {"link": "https://t.me/+zyJW6ZvNp98yMzFk", "channel": "https://t.me/+zyJW6ZvNp98yMzFk", "name_ar": "CapCut PRO", "name_en": "CapCut PRO"},
                "inshot": {"link": "https://t.me/+fDPaaezCFKNmZmM0", "channel": "https://t.me/+fDPaaezCFKNmZmM0", "name_ar": "Inshot PRI", "name_en": "Inshot PRI"},
                "picsart": {"link": "https://t.me/+-6sCG_0g6Mw3ODI0", "channel": "https://t.me/+-6sCG_0g6Mw3ODI0", "name_ar": "Picsart PRO", "name_en": "Picsart PRO"}
            }
            app = apps_links.get(product_id)
            if app:
                product_name = app["name_ar"] if lang=='ar' else app["name_en"]
                success_msg = t["order_accepted"].format(product_name, amount, app["link"], app["channel"], ADMIN_CONTACT, CHANNEL_PROOFS)
                bot.send_message(user_id, success_msg, parse_mode="Markdown")
                add_purchase_record(user_id, f"📱 {product_name} ({amount} DH): تم التحميل - {datetime.now()}")
                update_order_status(order_id, 'completed', admin_action=f'accept_by_{admin_id}')
                send_withdrawal_log(f"admin_{admin_id}", product_name, amount, code_or_link=app["link"])
            else:
                bot.send_message(user_id, t["app_no_stock"], parse_mode="Markdown")
                update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
    else:
        product_name = "المنتج"
        reject_msg = t["order_rejected"].format(product_name)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغيير طريقة الدفع", callback_data=f"change_payment_{order_id}"))
        bot.send_message(user_id, reject_msg, reply_markup=markup, parse_mode="Markdown")
        update_order_status(order_id, 'rejected', admin_action=f'reject_by_{admin_id}')

def purchase_ff_package(user_id, pkg, lang):
    amount = {"110":"11","231":"21","583":"52","1188":"100","2420":"222"}.get(pkg, "0")
    show_payment_methods(user_id, 'ff', pkg, amount)

def purchase_key(user_id, days, lang):
    price = {"1":20,"3":25,"7":50,"15":78,"30":120}.get(days,0)
    show_payment_methods(user_id, 'key', f"dripclient_{days}", price)

# ------------------- 15. إرسال التقرير لقناة السجلات -------------------
def send_withdrawal_log(admin_username, product_name, price, extra_info="", code_or_link=None):
    if not LOG_CHANNEL_ID:
        return
    msg = f"📋 *تقرير سحب (قائمة بيضاء أو قبول إداري)*\n━━━━━━━━━━━━\n👤 الوكيل/المدير: @{admin_username}\n📦 المنتج: {product_name}\n💰 السعر: {price} درهم\n"
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
        print(f"فشل إرسال التقرير إلى القناة: {e}")

# ------------------- 16. شراء القائمة البيضاء -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_purchase(call):
    pkg = call.data.split('_')[1]
    user_id = call.from_user.id
    lang = get_lang(user_id)
    t = T[lang]
    if is_whitelisted(user_id):
        code = get_ff_code(pkg)
        if code:
            price_map = {"110":"11","231":"21","583":"52","1188":"100","2420":"222"}
            bot.send_message(user_id, t["purchase_success"].format(pkg, price_map[pkg], code, ADMIN_CONTACT, CHANNEL_PROOFS), parse_mode="Markdown")
            add_purchase_record(user_id, f"📦 {pkg}💎 ({price_map[pkg]} DH): {code} - {datetime.now()}")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'ff', pkg, code, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, f"{pkg} جوهرة", price_map[pkg], code_or_link=code)
            bot.answer_callback_query(call.id, t["confirm_purchase"])
        else:
            bot.answer_callback_query(call.id, t["out_of_stock"], show_alert=True)
    else:
        purchase_ff_package(user_id, pkg, lang)
        bot.answer_callback_query(call.id)

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
    if is_whitelisted(user_id):
        code = get_key_code(prod_id, days)
        if code:
            product_name = "DRIP CLIENT APKMOD"
            price = {"1":20,"3":25,"7":50,"15":78,"30":120}[days]
            bot.send_message(user_id, t["keys_purchase_success"].format(product_name, days, price, code, ADMIN_CONTACT, CHANNEL_PROOFS), parse_mode="Markdown")
            add_purchase_record(user_id, f"🔑 {product_name} ({days} يوم): {code} - {datetime.now()}")
            conn = sqlite3.connect('moslim_store.db')
            c = conn.cursor()
            c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                      (user_id, call.from_user.username, 'key', f"{prod_id}_{days}", code, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            send_withdrawal_log(call.from_user.username, product_name, price, extra_info=f"🗓️ المدة: {days} يوم\n", code_or_link=code)
            bot.answer_callback_query(call.id, t["confirm_purchase"])
        else:
            bot.answer_callback_query(call.id, t["no_stock"], show_alert=True)
    else:
        purchase_key(user_id, days, lang)
        bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('key_prod_'))
def choose_duration(call):
    prod_id = call.data.split('_')[2]
    lang = get_lang(call.from_user.id)
    t = T[lang]
    markup = types.InlineKeyboardMarkup(row_width=2)
    durations = {"1":20, "3":25, "7":50, "15":78, "30":120}
    for days, price in durations.items():
        markup.add(types.InlineKeyboardButton(f"{days} DAYS = {price} DH 💰", callback_data=f"key_buy_{prod_id}_{days}"))
    markup.add(types.InlineKeyboardButton(t["back_to_products"], callback_data="back_to_key_products"))
    bot.send_message(call.message.chat.id, t["choose_validity"], reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('app_buy_'))
def process_app_purchase(call):
    app_id = call.data.split('_')[2]
    user_id = call.from_user.id
    lang = get_lang(user_id)
    t = T[lang]
    apps_info = {
        "capcut": {"name_ar": "CapCut PRO", "name_en": "CapCut PRO", "price": 20, "link": "https://t.me/+zyJW6ZvNp98yMzFk", "channel": "https://t.me/+zyJW6ZvNp98yMzFk"},
        "inshot": {"name_ar": "Inshot PRI", "name_en": "Inshot PRI", "price": 15, "link": "https://t.me/+fDPaaezCFKNmZmM0", "channel": "https://t.me/+fDPaaezCFKNmZmM0"},
        "picsart": {"name_ar": "Picsart PRO", "name_en": "Picsart PRO", "price": 25, "link": "https://t.me/+-6sCG_0g6Mw3ODI0", "channel": "https://t.me/+-6sCG_0g6Mw3ODI0"}
    }
    app = apps_info.get(app_id)
    if not app:
        bot.answer_callback_query(call.id, t["app_no_stock"], show_alert=True)
        return
    if is_whitelisted(user_id):
        product_name = app["name_ar"] if lang == 'ar' else app["name_en"]
        success_msg = t["order_accepted"].format(product_name, app["price"], app["link"], app["channel"], ADMIN_CONTACT, CHANNEL_PROOFS)
        bot.send_message(user_id, success_msg, parse_mode="Markdown")
        conn = sqlite3.connect('moslim_store.db')
        c = conn.cursor()
        c.execute("INSERT INTO admin_logs (admin_id, admin_name, product_type, product_id, code, action_date) VALUES (?,?,?,?,?,?)",
                  (user_id, call.from_user.username, 'app', app_id, app["link"], datetime.now().isoformat()))
        conn.commit()
        conn.close()
        send_withdrawal_log(call.from_user.username, product_name, app["price"], code_or_link=app["link"])
        bot.answer_callback_query(call.id, "🎉 تم تسليم التطبيق بنجاح!")
    else:
        show_payment_methods(user_id, 'app', app_id, app["price"])
        bot.answer_callback_query(call.id)

# ------------------- 17. أوامر الإدارة -------------------
@bot.message_handler(commands=['add_ff'])
def add_ff_command(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❗ الاستخدام: /add_ff <الكمية> <الكود>\nمثال: /add_ff 110 ABC123")
        return
    quantity, code = args[1], args[2]
    add_ff_code(quantity, code)
    bot.reply_to(message, f"✅ تم إضافة الكود `{code}` للكمية {quantity}")

@bot.message_handler(commands=['del_ff'])
def del_ff_command(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "❗ الاستخدام: /del_ff <الكمية> <الكود>")
        return
    quantity, code = args[1], args[2]
    if del_ff_code(quantity, code):
        bot.reply_to(message, f"✅ تم حذف الكود `{code}` للكمية {quantity}")
    else:
        bot.reply_to(message, f"❌ الكود غير موجود أو مستخدم بالفعل")

@bot.message_handler(commands=['stock_ff'])
def stock_ff_command(message):
    if not is_admin(message.from_user.id):
        return
    stock = get_ff_stock()
    if not stock:
        bot.reply_to(message, "📦 مخزون فري فاير فارغ")
        return
    lines = ["📊 *مخزون الجواهر:*"]
    for qty, count in stock:
        lines.append(f"💎 {qty} جوهرة : {count} كود")
    bot.reply_to(message, "\n".join(lines), parse_mode="Markdown")

@bot.message_handler(commands=['add_key'])
def add_key_command(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "❗ الاستخدام: /add_key <product_id> <المدة> <الكود>\nمثال: /add_key dripclient 30 KEY123")
        return
    prod_id, duration, code = args[1], args[2], args[3]
    add_key_code(prod_id, duration, code)
    bot.reply_to(message, f"✅ تم إضافة مفتاح {prod_id} مدة {duration} يوم")

@bot.message_handler(commands=['del_key'])
def del_key_command(message):
    if not is_admin(message.from_user.id):
        return
    args = message.text.split()
    if len(args) != 4:
        bot.reply_to(message, "❗ الاستخدام: /del_key <product_id> <المدة> <الكود>")
        return
    prod_id, duration, code = args[1], args[2], args[3]
    if del_key_code(prod_id, duration, code):
        bot.reply_to(message, f"✅ تم حذف المفتاح {code}")
    else:
        bot.reply_to(message, "❌ المفتاح غير موجود")

@bot.message_handler(commands=['stock_key'])
def stock_key_command(message):
    if not is_admin(message.from_user.id):
        return
    stock = get_key_stock()
    if not stock:
        bot.reply_to(message, "📦 مخزون المفاتيح فارغ")
        return
    lines = ["📊 *مخزون المفاتيح:*"]
    for prod, dur, count in stock:
        lines.append(f"🔑 {prod} - {dur} يوم : {count} مفتاح")
    bot.reply_to(message, "\n".join(lines), parse_mode="Markdown")

# ------------------- 18. أزرار العودة -------------------
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
    markup.add(types.InlineKeyboardButton("🔑 DRIP CLIENT APKMOD 👾", callback_data="key_prod_dripclient"))
    bot.edit_message_text(t["choose_product"], chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# ------------------- 19. تشغيل البوت -------------------
if __name__ == "__main__":
    keep_alive()
    print("✅ متجر مسلم يعمل بكفاءة مع جميع الخدمات، AI، وإدارة المخزون.")
    bot.delete_webhook()   # يحل مشكلة 409 conflict
    bot.infinity_polling()
