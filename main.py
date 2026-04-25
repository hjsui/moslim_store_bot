import telebot
from telebot import types
import sqlite3
from flask import Flask
from threading import Thread
from datetime import datetime
import random
import string
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/MOSLIM_SHOP"

# مخزن الجواهر والأكواد مع الأسعار
codes_inventory = {
    "110": ["5586744925499605", "5510650023494411", "9330820420409597"],
    "231": ["4808931182736381"],
    "583": [],
    "1188": [],
    "2420": []
}

# قائمة الأسعار لتظهر للزبون
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

# تخزين مؤقت لبيانات طلبات الاستعادة
recovery_requests = {}

# دوال مساعدة للخدمة الجديدة
def generate_username():
    return "user" + ''.join(random.choices(string.digits, k=6))

def generate_password():
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(chars, k=10))

def random_country():
    countries = ["Singapore", "Malaysia", "Indonesia", "Philippines", "Thailand"]
    return random.choice(countries)

def automate_garena_registration(email, username, password, country):
    """الدالة التي تتحكم بالمتصفح الآلي - تعمل على Render"""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # مهم لتشغيل على Render
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://sso.garena.com/universal/register?locale=en-SG")
        time.sleep(3)
        
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Username']"))
        )
        username_field.send_keys(username)
        time.sleep(1)
        
        pass_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        pass_field.send_keys(password)
        time.sleep(1)
        
        email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_field.send_keys(email)
        time.sleep(1)
        
        country_dropdown = driver.find_element(By.CSS_SELECTOR, "select")
        country_dropdown.click()
        time.sleep(1)
        
        country_option = driver.find_element(By.XPATH, f"//option[contains(text(), '{country}')]")
        country_option.click()
        time.sleep(1)
        
        get_code_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'GET CODE')]")
        get_code_btn.click()
        time.sleep(3)
        
        driver.quit()
        return True
    except Exception as e:
        print(f"خطأ: {e}")
        if driver:
            driver.quit()
        return False

def init_db():
    conn = sqlite3.connect('moslim_store.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, purchases TEXT, join_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- رسالة الترحيب ---
WELCOME_PREVIEW = """
🛍️ *مـتـجـــر مـسـلـــم | MOSLIM STORE* 🛍️
━━━━━━━━━━━━━━━━━━━━
✨ *خدمات رقمية - شحن فوري - اشتراكات* ✨
⚡ *سرعة - ثقة - أسعار لا تقبل المنافسة* ⚡
📢 *آراء العملاء:* قناتنا مليئة بالإثباتات
━━━━━━━━━━━━━━━━━━━━
🔓 *اضغط /start لتفعيل المتجر* 🔓
"""

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

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.row("🛍️ تسوق الآن", "🛒 الخدمات")
    markup.row("💰 إضافة رصيد", "👤 الملف الشخصي")
    markup.row("📖 طريقة الاستخدام", "📞 الدعم الفني")
    markup.row("📢 إثباتات الثقة")
    
    bot.send_message(message.chat.id, get_welcome_message(message.from_user.first_name), 
                     reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
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

    if message.text == "📢 إثباتات الثقة":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 قناة الإثباتات", url=CHANNEL_PROOFS))
        bot.send_message(message.chat.id, f"📢 *قناة الإثباتات:* [اضغط هنا]({CHANNEL_PROOFS})", reply_markup=m, parse_mode="Markdown")
    
    elif message.text in ["🛍️ تسوق الآن", "🛒 الخدمات"]:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        markup.add("💎 شحن جواهر فري فاير")
        markup.add("🎮 شحن ألعاب أخرى")
        markup.add("📧 طلب رمز تحقق بريد الاستعادة")  # الخدمة الجديدة
        markup.add("🔙 العودة للقائمة الرئيسية")
        bot.send_message(message.chat.id, "🛒 *أقسام المتجر:*\n━━━━━━━━━━━━\nاختر القسم المناسب:", 
                         reply_markup=markup, parse_mode="Markdown")
    
    # ========== الخدمة الجديدة ==========
    elif message.text == "📧 طلب رمز تحقق بريد الاستعادة":
        recovery_requests[user_id] = {}
        bot.send_message(message.chat.id, 
                         "✉️ *خدمة طلب رمز تحقق بريد الاستعادة*\n━━━━━━━━━━━━\n"
                         "أرسل لي بريدك الإلكتروني المرتبط بحساب فري فاير:\n\n"
                         "⚠️ *ملاحظة:* البريد سيُستخدم فقط لإرسال رمز التحقق إليه.",
                         parse_mode="Markdown")
        bot.register_next_step_handler(message, process_recovery_email)
    
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
        bot.send_message(message.chat.id, "👨‍💻 *فريق الدعم*\n━━━━━━━━━━━━\n*اختر طريقة التواصل:*", 
                         reply_markup=m, parse_mode="Markdown")
    
    elif message.text == "💰 إضافة رصيد":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("💳 مراسلة الدعم للشحن", url=ADMIN_CONTACT))
        bot.send_message(message.chat.id, 
                         "💰 *إضافة رصيد*\n━━━━━━━━━━━━\n"
                         "💵 *طرق الدفع المتاحة:*\n"
                         "• CIH BANK\n• Binance (USDT)\n• PayPal\n\n"
                         "📌 تواصل مع الدعم لإتمام الشحن.", 
                         reply_markup=m, parse_mode="Markdown")
    
    elif message.text == "📖 طريقة الاستخدام":
        bot.send_message(message.chat.id, 
                         "📖 *طريقة الاستخدام*\n━━━━━━━━━━━━\n"
                         "1️⃣ اختر الباقة المناسبة\n"
                         "2️⃣ اضغط على زر الشراء\n"
                         "3️⃣ تواصل مع الدعم للدفع\n"
                         "4️⃣ استلم كودك فوراً!\n\n"
                         "⚡ *شحن فوري - خدمة 24 ساعة*", 
                         parse_mode="Markdown")
    
    elif message.text == "🔙 العودة للقائمة الرئيسية":
        show_main_menu(message)
    
    else:
        bot.reply_to(message, 
                     "🤖 *مرحباً!* \n━━━━━━━━━━━━\n"
                     "استخدم الأزرار بالأسفل للتنقل في المتجر.",
                     parse_mode="Markdown")

    conn.close()

def process_recovery_email(message):
    user_id = message.from_user.id
    user_email = message.text.strip()
    
    if "@" not in user_email or "." not in user_email:
        bot.send_message(message.chat.id, "❌ بريد إلكتروني غير صالح. أرسل بريداً صحيحاً (مثل: example@gmail.com)")
        bot.register_next_step_handler(message, process_recovery_email)
        return
    
    recovery_requests[user_id]["email"] = user_email
    
    # توليد بيانات مؤقتة
    fake_username = generate_username()
    fake_password = generate_password()
    fake_country = random_country()
    
    waiting_msg = bot.send_message(message.chat.id, 
        "🔄 *جاري معالجة طلبك...*\n━━━━━━━━━━━━\n"
        "⏱️ يرجى الانتظار 10-20 ثانية\n"
        "🌐 جاري الاتصال بخوادم Garena...",
        parse_mode="Markdown")
    
    try:
        success = automate_garena_registration(user_email, fake_username, fake_password, fake_country)
        
        if success:
            bot.edit_message_text(
                "✅ *تم إرسال رمز التحقق إلى بريدك الإلكتروني!* ✅\n━━━━━━━━━━━━\n\n"
                f"📧 تم الإرسال إلى: `{user_email}`\n\n"
                "🔑 **الخطوات التالية:**\n"
                "1️⃣ افتح بريدك الإلكتروني (Gmail أو غيره)\n"
                "2️⃣ ابحث عن رسالة من Garena\n"
                "3️⃣ انسخ رمز التحقيق المكون من 6 أرقام\n"
                "4️⃣ **أدخل الرمز في لعبة فري فاير مباشرة**\n\n"
                "⚠️ **تنبيه أمان هام جداً:**\n"
                "• 🔐 **لا ترسل هذا الرمز لأي شخص** - ولا حتى لي!\n"
                "• 🎮 أدخل الرمز فقط في تطبيق فري فاير نفسه\n"
                "• 👤 حسابك في أمان إذا أدخلته في اللعبة فقط\n\n"
                "🌟 شكراً لاستخدامك متجر مسلم!",
                chat_id=message.chat.id, message_id=waiting_msg.message_id, parse_mode="Markdown")
            
            # إشعار للمدير
            bot.send_message(ADMIN_ID, 
                f"🔔 *طلب رمز تحقق جديد!*\n━━━━━━━━━━━━\n"
                f"👤 المستخدم: @{message.from_user.username}\n"
                f"📧 البريد: {user_email}\n"
                f"👤 الاسم المؤقت: `{fake_username}`\n"
                f"🌍 الدولة: {fake_country}\n"
                f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}",
                parse_mode="Markdown")
        else:
            bot.edit_message_text(
                "❌ *حدث خطأ أثناء معالجة طلبك*\n━━━━━━━━━━━━\n"
                "الرجاء المحاولة مرة أخرى لاحقاً.\n"
                "إذا استمرت المشكلة، تواصل مع الدعم.",
                chat_id=message.chat.id, message_id=waiting_msg.message_id, parse_mode="Markdown")
                
    except Exception as e:
        bot.edit_message_text(
            f"❌ *خطأ تقني*\n━━━━━━━━━━━━\n`{str(e)[:100]}`\nالرجاء المحاولة مرة أخرى.",
            chat_id=message.chat.id, message_id=waiting_msg.message_id, parse_mode="Markdown")

def show_ff_packages(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pkg in codes_inventory.keys():
        price = prices.get(pkg, "0")
        markup.add(types.InlineKeyboardButton(f"💎 {pkg} جوهرة = {price} درهم", callback_data=f"buy_{pkg}"))
    
    markup.add(types.InlineKeyboardButton("📢 شاهد الإثباتات قبل الشراء", url=CHANNEL_PROOFS))
    
    bot.send_message(message.chat.id, 
                     "💎 *باقات شحن جواهر فري فاير*\n━━━━━━━━━━━━\n"
                     "✨ *باقات حصرية بأفضل الأسعار*\n"
                     "⚡ *توصيل فوري خلال دقائق*\n━━━━━━━━━━━━\n"
                     "*اختر الباقة المناسبة:*", 
                     reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def process_purchase(call):
    pkg = call.data.split('_')[1]
    if codes_inventory.get(pkg) and len(codes_inventory[pkg]) > 0:
        code = codes_inventory[pkg].pop(0)

        bot.send_message(call.message.chat.id, 
                         f"✅ *تم الشراء بنجاح!* ✅\n━━━━━━━━━━━━\n"
                         f"💎 الكمية: {pkg} جوهرة\n"
                         f"💰 السعر: {prices[pkg]} درهم\n"
                         f"🔑 كود الشحن: `{code}`\n━━━━━━━━━━━━\n"
                         f"📞 للاستفسار: [@MOSLIM_SHOP]({ADMIN_CONTACT})", 
                         parse_mode="Markdown")
        
        admin_msg = (f"🔔 *عملية بيع جديدة!* 🔔\n━━━━━━━━━━━━\n"
                     f"👤 الزبون: @{call.from_user.username}\n"
                     f"📦 الفئة: {pkg} 💎\n"
                     f"💰 الثمن: {prices[pkg]} درهم\n"
                     f"🔑 الكود: `{code}`\n"
                     f"⏰ الوقت: {datetime.now().strftime('%H:%M:%S')}")
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")

        conn = sqlite3.connect('moslim_store.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET purchases = purchases || ? || '\n' WHERE user_id=?",
                       (f"📦 {pkg}💎 ({prices[pkg]} DH): {code} - {datetime.now().strftime('%Y-%m-%d')}", 
                        call.from_user.id))
        conn.commit()
        conn.close()
        
        bot.answer_callback_query(call.id, "🎉 تم الشراء بنجاح!")
    else:
        bot.answer_callback_query(call.id, "❌ هذه الباقة غير متوفرة حالياً!", show_alert=True)

if __name__ == "__main__":
    keep_alive()
    print("✅ متجر مسلم شغال بنجاح!")
    print("✅ خدمة طلب رمز تحقق بريد الاستعادة مضافة!")
    bot.infinity_polling()
