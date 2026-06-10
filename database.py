import sqlite3
import random
import string
from datetime import datetime

def init_db():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    # إنشاء جدول users مع عمود currency (إذا لم يكن موجوداً)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, 
                  purchases TEXT, join_date TEXT, language TEXT DEFAULT 'ar')''')
    # إضافة عمود currency إذا لم يكن موجوداً (ترقية)
    try:
        c.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'mad'")
    except sqlite3.OperationalError:
        pass  # العمود موجود بالفعل
    
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (order_id TEXT PRIMARY KEY, user_id INTEGER, product_type TEXT, 
                  product_id TEXT, amount REAL, status TEXT, timestamp TEXT,
                  proof_photo_id TEXT, admin_action TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS admin_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, admin_name TEXT,
                  product_type TEXT, product_id TEXT, code TEXT, action_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS social_orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, service_id INTEGER,
                  link TEXT, quantity INTEGER, amount REAL, api_order_id INTEGER,
                  status TEXT, created_at TEXT)''')
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

def add_purchase_record(user_id, record):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE users SET purchases = COALESCE(purchases, '') || ? || '\n' WHERE user_id=?", (record, user_id))
    conn.commit()
    conn.close()

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

# دوال لجدول social_orders
def save_social_order(user_id, service_id, link, quantity, amount, api_order_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO social_orders (user_id, service_id, link, quantity, amount, api_order_id, status, created_at) VALUES (?,?,?,?,?,?,?,?)",
              (user_id, service_id, link, quantity, amount, api_order_id, 'pending', datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_social_order_status(api_order_id, status):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE social_orders SET status=? WHERE api_order_id=?", (status, api_order_id))
    conn.commit()
    conn.close()

# ✅ دوال جديدة للعملة
def get_user_currency(user_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    try:
        c.execute("SELECT currency FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row[0] if row and row[0] in ['mad', 'usd'] else 'mad'
    except sqlite3.OperationalError:
        conn.close()
        return 'mad'

def set_user_currency(user_id, currency):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE users SET currency = ? WHERE user_id=?", (currency, user_id))
        conn.commit()
    except sqlite3.OperationalError:
        # إذا كان العمود غير موجود، نضيفه ثم نحاول مرة أخرى
        c.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'mad'")
        c.execute("UPDATE users SET currency = ? WHERE user_id=?", (currency, user_id))
        conn.commit()
    conn.close()
