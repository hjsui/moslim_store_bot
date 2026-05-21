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
API_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 8530485909
bot = telebot.TeleBot(API_TOKEN)

STORE_PASSWORD = "555451265696++ftytyuiuliyty6654923//fyytu@moslim.com"
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# ------------------- 3. القائمة البيضاء -------------------
WHITELISTED_USERS = [8530485909, 8615239297]  # ضع معرفات أصدقائك هنا

def is_whitelisted(user_id):
    return user_id in WHITELISTED_USERS

# ------------------- 4. أكواد الجواهر والمفاتيح -------------------
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

# ------------------- 5. خدمة اشتراكات التطبيقات (منتوج مستقل) -------------------
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

# ------------------- 6. قاعدة البيانات -------------------
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
    conn.commit()
    conn.close()
init_db()

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

# ------------------- 7. دوال إدارة الطلبات -------------------
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

# ------------------- 8. بيانات طرق الدفع -------------------
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

# ------------------- 9. قاموس الترجمة -------------------
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
        "ff_topup": "💎 شحن جواهر فري فاير",
        "keys_service": "🔑 إنشاء مفاتيح الهكرات",
        "apps_service": "📱 اشتراكات التطبيقات",
        "choose_product": "🔍 *اختر نوع المنتج:*",
        "choose_validity": "📅 *اختر المدة:*",
        "choose_payment": "💳 *اختر طريقة الدفع:*",
        "ask_proof": "📸 *أرسل صورة إثبات الدفع الآن* (لقطة شاشة من تطبيق البنك أو المحفظة)",
        "proof_received": "✅ تم استلام إثبات الدفع! جاري تسليم منتجك 📦",
        "order_rejected": "❌ <b>عذراً، تم رفض طلبك</b> لأن الدفع لم يصل أو الإثبات غير واضح.\n💰 <b>المنتج:</b> {}\n📞 يمكنك التواصل مع الدعم: @MOSLIM_SHOP\n💡 يمكنك الضغط على الزر أدناه لتغيير طريقة الدفع.",
        "already_paid": "⚠️ لديك طلب قيد المراجعة بالفعل. يرجى الانتظار أو التواصل مع الدعم.",
        "keys_purchase_success": "✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n📦 المنتج: {}\n🗓️ المدة: {} يوم\n💰 السعر: {} 💰\n🔑 مفتاحك: `{}`\n━━━━━━━━━━━━\n📞 للاستفسار: [@MOSLIM_SHOP]({})\n📢 لمشاهدة إثباتاتنا: [اضغط هنا]({})",
        "app_purchase_success": "✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n📦 التطبيق: {}\n💰 السعر: {} درهم\n🔗 رابط التحميل: [اضغط هنا]({})\n📢 لمتابعة التحديثات: [انضم للقناة]({})\n━━━━━━━━━━━━\n📞 للاستفسار: [@MOSLIM_SHOP]({})\n📢 لمشاهدة إثباتاتنا: [اضغط هنا]({})",
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
        "inline_proofs_btn": "📢 قناة الإثباتات"
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
        "ff_topup": "💎 Free Fire Diamonds Top-up",
        "keys_service": "🔑 Create Hacker Keys",
        "apps_service": "📱 App Subscriptions",
        "choose_product": "🔍 *Choose product type:*",
        "choose_validity": "📅 *Choose duration:*",
        "choose_payment": "💳 *Choose payment method:*",
        "ask_proof": "📸 *Send your payment proof screenshot now*",
        "proof_received": "✅ Payment proof received! Delivering your product 📦",
        "order_rejected": "❌ <b>Order rejected</b> because payment was not received or proof is unclear.\n💰 <b>Product:</b> {}\n📞 Contact support: @MOSLIM_SHOP\n💡 Press the button below to change payment method.",
        "already_paid": "⚠️ You have a pending order. Please wait or contact support.",
        "keys_purchase_success": "✅ *Purchase successful!* ✅\n━━━━━━━━━━━━\n📦 Product: {}\n🗓️ Duration: {} days\n💰 Price: {} 💰\n🔑 Your key: `{}`\n━━━━━━━━━━━━\n📞 Inquiries: [@MOSLIM_SHOP]({})\n📢 See our proofs: [Click here]({})",
        "app_purchase_success": "✅ *Purchase successful!* ✅\n━━━━━━━━━━━━\n📦 App: {}\n💰 Price: {} MAD\n🔗 Download link: [Click here]({})\n📢 For updates: [Join channel]({})\n━━━━━━━━━━━━\n📞 Inquiries: [@MOSLIM_SHOP]({})\n📢 See proofs: [Click here]({})",
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
        "inline_proofs_btn": "📢 Proofs Channel"
    }
}

# ------------------- 10. دوال واجهة المستخدم -------------------
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
    markup.row(t["proofs"])
    markup.row(t["apps_service"])  # خدمة مستقلة في القائمة الرئيسية
    user_count = get_verified_count()
    msg = t["welcome_main"].format(message.from_user.first_name, CHANNEL_PROOFS) + t["user_count"].format(user_count)
    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="Markdown")

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

# ------------------- 11. معالج الرسائل العامة -------------------
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
    t = T[lang]

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
    if text in [t["shop_now"], t["services"]]:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["other_games"], t["ff_services"])
        markup.add(t["back_to_main"])
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
    elif text == t["ff_topup"]:
        show_ff_packages(message, lang)
    elif text == t["keys_service"]:
        show_keys_products(message, lang)
    elif text == t["apps_service"]:
        show_apps_products(message, lang)
    elif text == t["back_to_main"]:
        show_main_menu(message, lang)
    elif text == t["back_to_sections"]:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(t["other_games"], t["ff_services"])
        markup.add(t["back_to_main"])
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
    for pkg in codes_inventory:
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

# ------------------- 13. دوال نظام الدفع -------------------
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
        product_name = f"مفتاح DRIP CLIENT - {product_id} يوم"
    else:
        app_data = apps_inventory.get(product_id, {})
        product_name = app_data.get("name_ar", "تطبيق") if lang == 'ar' else app_data.get("name_en", "App")

    admin_msg = (f"<b>🔔 طلب دفع جديد</b>\n━━━━━━━━━━━━\n"
                 f"<b>🆔 الطلب:</b> <code>{order_id}</code>\n"
                 f"<b>👤 المستخدم:</b> @{message.from_user.username}\n"
                 f"<b>📦 المنتج:</b> {product_name}\n"
                 f"<b>💰 المبلغ:</b> {amount} درهم\n"
                 f"<b>📸 <a href='tg://user?id={user_id}'>إثبات الدفع</a></b>")
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ قبول الطلب", callback_data=f"admin_accept_{order_id}"),
        types.InlineKeyboardButton("❌ رفض الطلب", callback_data=f"admin_reject_{order_id}")
    )
    bot.send_photo(ADMIN_ID, photo_id, caption=admin_msg, reply_markup=markup, parse_mode="HTML")
    bot.send_message(user_id, t["proof_received"], parse_mode="HTML")

# ------------------- 14. قبول ورفض الطلبات مع حذف الأكواد -------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_accept_'))
def admin_accept_order(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
        return
    order_id = call.data.split('_', 2)[2]
    finalize_order(order_id, accepted=True)
    bot.answer_callback_query(call.id, "✅ تم قبول الطلب")

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_reject_'))
def admin_reject_order(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "غير مسموح", show_alert=True)
        return
    order_id = call.data.split('_', 2)[2]
    finalize_order(order_id, accepted=False)
    bot.answer_callback_query(call.id, "❌ تم رفض الطلب")

def finalize_order(order_id, accepted):
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
                # حذف الكود (إزالته من المخزون نهائياً)
                code = codes_inventory[product_id].pop(0)
                success_msg = t["purchase_success"].format(product_id, amount, code, ADMIN_CONTACT, CHANNEL_PROOFS)
                bot.send_message(user_id, success_msg, parse_mode="Markdown")
                add_purchase_record(user_id, f"📦 {product_id}💎 ({amount} DH): {code} - {datetime.now()}")
                bot.send_message(ADMIN_ID, f"✅ تم قبول الطلب {order_id} وتسليم الكود: {code}")
                update_order_status(order_id, 'completed', admin_action='accept')
            else:
                bot.send_message(user_id, t["out_of_stock"], parse_mode="Markdown")
                update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
        elif product_type == 'key':
            prod_data = keys_inventory.get('dripclient')
            if prod_data and product_id in prod_data["codes"] and prod_data["codes"][product_id]:
                # حذف المفتاح من المخزون
                code = prod_data["codes"][product_id].pop(0)
                product_name = prod_data["name_ar"] if lang == 'ar' else prod_data["name_en"]
                success_msg = t["keys_purchase_success"].format(product_name, product_id, amount, code, ADMIN_CONTACT, CHANNEL_PROOFS)
                bot.send_message(user_id, success_msg, parse_mode="Markdown")
                add_purchase_record(user_id, f"🔑 {product_name} ({product_id} يوم) - {amount} 💰: {code} - {datetime.now()}")
                bot.send_message(ADMIN_ID, f"✅ تم قبول الطلب {order_id} وتسليم المفتاح: {code}")
                update_order_status(order_id, 'completed', admin_action='accept')
            else:
                bot.send_message(user_id, t["no_stock"], parse_mode="Markdown")
                update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
        elif product_type == 'app':
            app_data = apps_inventory.get(product_id)
            if app_data:
                product_name = app_data["name_ar"] if lang == 'ar' else app_data["name_en"]
                download_link = app_data.get("link", "")
                channel_link = app_data.get("update_channel", "")
                success_msg = t["app_purchase_success"].format(product_name, amount, download_link, channel_link, ADMIN_CONTACT, CHANNEL_PROOFS)
                bot.send_message(user_id, success_msg, parse_mode="Markdown")
                add_purchase_record(user_id, f"📱 {product_name} ({amount} DH): تم التحميل - {datetime.now()}")
                bot.send_message(ADMIN_ID, f"✅ تم قبول الطلب {order_id} (تطبيق {product_name})")
                update_order_status(order_id, 'completed', admin_action='accept')
            else:
                bot.send_message(user_id, t["app_no_stock"], parse_mode="Markdown")
                update_order_status(order_id, 'failed', admin_action='accept_out_of_stock')
    else:
        if product_type == 'ff':
            product_name = f"جواهر فري فاير ({product_id} جوهرة)"
        elif product_type == 'key':
            product_name = f"مفتاح DRIP CLIENT - {product_id} يوم"
        else:
            app_data = apps_inventory.get(product_id, {})
            product_name = app_data.get("name_ar", "تطبيق") if lang == 'ar' else app_data.get("name_en", "App")
        reject_msg = t["order_rejected"].format(product_name)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغيير طريقة الدفع", callback_data=f"change_payment_{order_id}"))
        bot.send_message(user_id, reject_msg, reply_markup=markup, parse_mode="HTML")
        update_order_status(order_id, 'rejected', admin_action='reject')
        bot.send_message(ADMIN_ID, f"❌ تم رفض الطلب {order_id}")

def purchase_ff_package(user_id, pkg, lang):
    amount = prices[pkg]
    show_payment_methods(user_id, 'ff', pkg, amount)

def purchase_key(user_id, days, lang):
    price = keys_inventory['dripclient']['prices'][days]
    show_payment_methods(user_id, 'key', days, price)

# ------------------- 15. عمليات الشراء -------------------
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
        admin_msg = f"🔔 *شراء مباشر (قائمة بيضاء)*\n👤 @{call.from_user.username}\n📦 {pkg}💎\n💰 {prices[pkg]} درهم\n🔑 {code}"
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        add_purchase_record(user_id, f"📦 {pkg}💎 ({prices[pkg]} DH): {code} - {datetime.now()}")
        bot.answer_callback_query(call.id, t["confirm_purchase"])
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
    if prod_id not in keys_inventory or days not in keys_inventory[prod_id]["codes"] or not keys_inventory[prod_id]["codes"][days]:
        bot.answer_callback_query(call.id, t["no_stock"], show_alert=True)
        return
    if is_whitelisted(user_id):
        code = keys_inventory[prod_id]["codes"][days].pop(0)
        product_name = keys_inventory[prod_id]["name_ar"] if lang == 'ar' else keys_inventory[prod_id]["name_en"]
        bot.send_message(user_id, t["keys_purchase_success"].format(product_name, days, keys_inventory[prod_id]["prices"][days], code, ADMIN_CONTACT, CHANNEL_PROOFS), parse_mode="Markdown")
        admin_msg = f"🔔 *شراء مفتاح مباشر (قائمة بيضاء)*\n👤 @{call.from_user.username}\n📦 {product_name}\n🗓️ {days} يوم\n🔑 {code}"
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        add_purchase_record(user_id, f"🔑 {product_name} ({days} يوم): {code} - {datetime.now()}")
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
    price = app_data["price"]
    show_payment_methods(user_id, 'app', app_id, price)
    bot.answer_callback_query(call.id)

# ------------------- 16. أزرار العودة -------------------
@bot.callback_query_handler(func=lambda call: call.data == "back_to_ff_services")
def back_to_ff_services(call):
    lang = get_lang(call.from_user.id)
    t = T[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(t["ff_topup"], t["keys_service"], t["back_to_sections"])
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

# ------------------- 17. التشغيل -------------------
if __name__ == "__main__":
    keep_alive()
    print("✅ متجر مسلم يعمل بكفاءة مع جميع الخدمات (جواهر، مفاتيح، تطبيقات).")
    bot.infinity_polling()
