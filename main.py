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

# الباسورد المحمي
STORE_PASSWORD = "555451265696++ftytyuiuliyty6654923//fyytu@moslim.com"

# روابط مهمة
CHANNEL_PROOFS = "https://t.me/moslim_store1"  # قناة إثباتات الثقة والمصداقية
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# مخزن الجواهر والأكواد مع الأسعار
codes_inventory = {
    "110": ["2729314781983415"،"2990317557543977"],
    "231": ["4187859578853211"],
    "583": ["3827469145294515"،"1619600169344364"],
    "1188": ["1647326962221020"],
    "2420": []  # تركته فارغاً
}

# قائمة الأسعار لتظهر للزبون
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

def init_db():
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, purchases TEXT, join_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- رسالة الترحيب الجذابة قبل /start ---
WELCOME_PREVIEW = """
🛍️ *مـتـجـــر مـسـلـــم | MOSLIM STORE* 🛍️
━━━━━━━━━━━━━━━━━━━━
✨ *خدمات رقمية - شحن فوري - اشتراكات* ✨
⚡ *سرعة - ثقة - أسعار لا تقبل المنافسة* ⚡
📢 *آراء العملاء:* قناتنا مليئة بالإثباتات
━━━━━━━━━━━━━━━━━━━━
🔓 *اضغط /start لتفعيل المتجر* 🔓
"""

# --- رسالة الترحيب بعد التفعيل ---
def get_welcome_message(first_name):
    return f"""
👋🏻 *أهلاً بك، {first_name}!* 

🛍️ *في متجر مسلم - وجهتك الأولى للخدمات الحصرية*

⭐ *أبرز مميزات المتجر:*
🔑 خدمات رقمية مميزة / شحن فوري
⚡ سرعة فائقة في التنفيذ
🔒 متجر محمي وموثق 100%
💸 أسعار لا تقبل المنافسة
📢 *قناة الإثباتات:* [انقر هنا لمشاهدة الثقة]({CHANNEL_PROOFS})

🚀 *اختر من القائمة بالأسفل لبدء التسوق!*
"""

# --- القائمة الرئيسية ---
def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row("🛍️ تسوق الآن", "🛒 الخدمات")
    markup.row("💰 إضافة رصيد", "👤 الملف الشخصي")
    markup.row("📖 طريقة الاستخدام", "📞 الدعم الفني")
    markup.row("📢 إثباتات الثقة")  # زر جديد
    
    bot.send_message(message.chat.id, get_welcome_message(message.from_user.first_name), 
                     reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    # إرسال الرسالة التعريفية الجذابة أولاً
    bot.send_message(message.chat.id, WELCOME_PREVIEW, parse_mode="Markdown")
    
    user_id = message.from_user.id
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        join_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("INSERT INTO users VALUES (?, ?, 0, '', ?)", 
                       (user_id, message.from_user.username, join_date))
        conn.commit()
        bot.reply_to(message, "⚠️ *مـتـجـــر مـسـلـــم* 🛍️\nأدخل كلمة المرور لتفعيل المتجر:", parse_mode="Markdown")
    elif user[0] == 0:
        bot.reply_to(message, "🔒 *المتجر محمي* 🔒\nأدخل كلمة المرور:", parse_mode="Markdown")
    else:
        show_main_menu(message)
    conn.close()

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT verified FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return

    if user[0] == 0:
        if message.text == STORE_PASSWORD:
            cursor.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
            conn.commit()
            bot.reply_to(message, "✅ *تم التفعيل بنجاح!* ✅\n🎉 مرحباً بك في متجر مسلم", parse_mode="Markdown")
            show_main_menu(message)
        else:
            bot.reply_to(message, "❌ *كلمة مرور خاطئة!* ❌", parse_mode="Markdown")
        conn.close()
        return

    # زر إثباتات الثقة الجديد
    if message.text == "📢 إثباتات الثقة":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 قناة الإثباتات", url=CHANNEL_PROOFS))
        m.add(types.InlineKeyboardButton("⭐ آراء العملاء", url=f"{CHANNEL_PROOFS}"))
        bot.send_message(message.chat.id, 
                         f"📢 *قناة إثباتات الثقة والمصداقية*\n━━━━━━━━━━━━\n"
                         f"🔍 *شاهد بنفسك آراء العملاء السابقين:*\n"
                         f"✅ أكثر من 100+ عملية موثقة\n"
                         f"⭐ تقييم العملاء: ممتاز جداً\n\n"
                         f"[📢 اضغط هنا لمشاهدة الإثباتات]({CHANNEL_PROOFS})", 
                         reply_markup=m, parse_mode="Markdown")
    
    elif message.text in ["🛍️ تسوق الآن", "🛒 الخدمات"]:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add("💎 شحن جواهر فري فاير", "🎮 شحن ألعاب أخرى", "🔙 العودة للقائمة الرئيسية")
        bot.send_message(message.chat.id, "🛒 *أقسام المتجر:*\n━━━━━━━━━━━━\nاختر القسم المناسب:", 
                         reply_markup=markup, parse_mode="Markdown")
    
    elif message.text == "🎮 شحن ألعاب أخرى":
        bot.send_message(message.chat.id, 
                         "🎮 *شحن ألعاب أخرى*\n━━━━━━━━━━━━\n"
                         "📌 *الألعاب المتوفرة:*\n"
                         "• ببجي موبايل (UC)\n"
                         "• كول أوف ديوتي (CP)\n"
                         "• فري فاير (DA)\n"
                         "• جينشين إمباكت\n\n"
                         "📞 *للطلب:* تواصل مع الدعم", 
                         parse_mode="Markdown")
    
    elif message.text == "💎 شحن جواهر فري فاير":
        show_ff_packages(message)
    
    elif message.text == "👤 الملف الشخصي":
        cursor.execute("SELECT purchases, join_date FROM users WHERE user_id=?", (user_id,))
        result = cursor.fetchone()
        p = result[0] or "📭 *لا توجد مشتريات بعد.*"
        join_date = result[1] or "غير معروف"
        bot.send_message(message.chat.id, 
                         f"👤 *ملفك الشخصي*\n━━━━━━━━━━━━\n"
                         f"🆔 المعرف: `{user_id}`\n"
                         f"📅 تاريخ التسجيل: {join_date}\n"
                         f"🛍️ *سجل مشترياتك:*\n{p}\n━━━━━━━━━━━━\n"
                         f"📢 *شكراً لثقتك بنا* ❤️", 
                         parse_mode="Markdown")
    
    elif message.text == "📞 الدعم الفني":
        m = types.InlineKeyboardMarkup(row_width=1)
        m.add(types.InlineKeyboardButton("💬 مراسلة المدير", url=ADMIN_CONTACT))
        m.add(types.InlineKeyboardButton("📢 قناة المتجر", url="https://t.me/moslim_store"))
        m.add(types.InlineKeyboardButton("⭐ إثباتات الثقة", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, 
                         "👨‍💻 *فريق الدعم*\n━━━━━━━━━━━━\n"
                         "• الرد خلال 24 ساعة\n"
                         "• الدعم متوفر طوال الأسبوع\n"
                         "• للمشاكل والاستفسارات\n━━━━━━━━━━━━\n"
                         "*اختر طريقة التواصل:*", 
                         reply_markup=m, parse_mode="Markdown")
    
    elif message.text == "💰 إضافة رصيد":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💳 مراسلة الدعم للشحن", url=ADMIN_CONTACT))
        m.add(types.InlineKeyboardButton("📢 شاهد الإثباتات", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, 
                         "💰 *إضافة رصيد*\n━━━━━━━━━━━━\n"
                         "💵 *طرق الدفع المتاحة:*\n"
                         "• CIH BANK\n"
                         "• Binance (USDT)\n"
                         "• PayPal\n"
                         "• الاتصال برقم الوا\n\n"
                         "📌 *خطوات الشحن:*\n"
                         "1️⃣ تواصل مع الدعم\n"
                         "2️⃣ أرسل المبلغ المطلوب\n"
                         "3️⃣ استلم الرصيد فوراً\n\n"
                         "✨ *خدمة آمنة وسريعة*", 
                         reply_markup=m, parse_mode="Markdown")
    
    elif message.text == "📖 طريقة الاستخدام":
        bot.send_message(message.chat.id, 
                         "📖 *طريقة الاستخدام*\n━━━━━━━━━━━━\n"
                         "📌 *خطوات الشراء:*\n"
                         "1️⃣ اختر الباقة المناسبة\n"
                         "2️⃣ اضغط على زر الشراء\n"
                         "3️⃣ تواصل مع الدعم للدفع\n"
                         "4️⃣ استلم كودك فوراً!\n\n"
                         "⚡ *شحن فوري - خدمة 24 ساعة*\n"
                         "🔒 *ضمان استرجاع الأموال في حال وجود مشكلة*\n\n"
                         "📢 *قبل الشراء:* [شاهد إثباتاتنا]({CHANNEL_PROOFS})", 
                         parse_mode="Markdown")
    
    elif message.text == "🔙 العودة للقائمة الرئيسية":
        show_main_menu(message)
    
    else:
        # ردود ذكية للرسائل العشوائية
        bot.reply_to(message, 
                     "🤖 *مرحباً!* \n━━━━━━━━━━━━\n"
                     "استخدم الأزرار بالأسفل للتنقل في المتجر.\n"
                     f"📢 وللتأكد من مصداقيتنا: [شاهد الإثباتات]({CHANNEL_PROOFS})", 
                     parse_mode="Markdown")

    conn.close()

def show_ff_packages(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pkg in codes_inventory.keys():
        price = prices.get(pkg, "0")
        markup.add(types.InlineKeyboardButton(f"💎 {pkg} جوهرة = {price} درهم", callback_data=f"buy_{pkg}"))
    
    # زر إضافي لإثباتات الثقة
    markup.add(types.InlineKeyboardButton("📢 شاهد الإثباتات قبل الشراء", url=CHANNEL_PROOFS))
    
    bot.send_message(message.chat.id, 
                     "💎 *باقات شحن جواهر فري فاير*\n━━━━━━━━━━━━\n"
                     "✨ *باقات حصرية بأفضل الأسعار*\n"
                     "⚡ *توصيل فوري خلال دقائق*\n"
                     f"📢 *للتأكد من المصداقية:* [قناة الإثباتات]({CHANNEL_PROOFS})\n━━━━━━━━━━━━\n"
                     "*اختر الباقة المناسبة:*", 
                     reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_purchase(call):
    pkg = call.data.split('_')[1]
    if codes_inventory.get(pkg) and len(codes_inventory[pkg]) > 0:
        code = codes_inventory[pkg].pop(0)

        # رسالة للزبون
        bot.send_message(call.message.chat.id, 
                         f"✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n"
                         f"💎 الكمية: {pkg} جوهرة\n"
                         f"💰 السعر: {prices[pkg]} درهم\n"
                         f"🔑 كود الشحن: `{code}`\n━━━━━━━━━━━━\n"
                         f"📞 للاستفسار: [@MOSLIM_SHOP]({ADMIN_CONTACT})\n"
                         f"📢 لمشاهدة إثباتاتنا: [اضغط هنا]({CHANNEL_PROOFS})", 
                         parse_mode="Markdown")
        
        # إشعار فوري للإدمن مع رابط القناة
        admin_msg = (f"🔔 *عملية بيع جديدة!* 🔔\n━━━━━━━━━━━━\n"
                     f"👤 الزبون: @{call.from_user.username}\n"
                     f"🆔 المعرف: `{call.from_user.id}`\n"
                     f"📦 الفئة: {pkg} 💎\n"
                     f"💰 الثمن: {prices[pkg]} درهم\n"
                     f"🔑 الكود: `{code}`\n"
                     f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}\n━━━━━━━━━━━━\n"
                     f"✅ *تم التسليم آلياً*\n"
                     f"📢 قناة الإثباتات: {CHANNEL_PROOFS}")
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

        conn = sqlite3.connect('moslim_store.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET purchases = purchases || ? || '\n' WHERE user_id=?",
                       (f"📦 {pkg}💎 ({prices[pkg]} DH): {code} - {datetime.now().strftime('%Y-%m-%d')}", 
                        call.from_user.id))
        conn.commit()
        conn.close()
        
        # تأكيد للزبون بصوت منبثق
        bot.answer_callback_query(call.id, "🎉 تم الشراء بنجاح! استلم الكود أعلاه")
    else:
        bot.answer_callback_query(call.id, "❌ عذراً، هذه الباقة غير متوفرة حالياً. جرب باقة أخرى!", show_alert=True)

if __name__ == "__main__":
    keep_alive()
    print("✅ المتجر شغال بنجاح!")
    print(f"📢 قناة الإثباتات: {CHANNEL_PROOFS}")
    bot.infinity_polling()
