import sqlite3
import random
import string
from datetime import datetime

def init_db():
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, verified INTEGER, 
                  purchases TEXT, join_date TEXT, language TEXT DEFAULT 'ar')''')
    # ✅ إضافة عمود العملة (إذا لم يكن موجوداً)
    try:
        c.execute("ALTER TABLE users ADD COLUMN currency TEXT DEFAULT 'mad'")
    except sqlite3.OperationalError:
        pass
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
    # ✅ جداول إدارة المخزون
    c.execute('''CREATE TABLE IF NOT EXISTS ff_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, quantity TEXT, code TEXT, used INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS key_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, duration TEXT, code TEXT, used INTEGER DEFAULT 0)''')
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

# دوال العملة
def get_user_currency(user_id):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT currency FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 'mad'

def set_user_currency(user_id, currency):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("UPDATE users SET currency = ? WHERE user_id=?", (currency, user_id))
    conn.commit()
    conn.close()

# ========== دوال إدارة المخزون (للوحة التحكم الإدارية) ==========

# جواهر فري فاير
def get_ff_stock():
    """إرجاع قائمة بكميات الجواهر وعدد الأكواد غير المستخدمة"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT quantity, COUNT(*) FROM ff_codes WHERE used=0 GROUP BY quantity")
    rows = c.fetchall()
    conn.close()
    return rows

def add_ff_code(quantity, code):
    """إضافة كود جديد لجواهر فري فاير"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO ff_codes (quantity, code, used) VALUES (?,?,0)", (quantity, code))
    conn.commit()
    conn.close()

def del_ff_code(quantity, code):
    """حذف كود جواهر فري فاير (غير مستخدم)"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("DELETE FROM ff_codes WHERE quantity=? AND code=? AND used=0 LIMIT 1", (quantity, code))
    conn.commit()
    conn.close()
    return c.rowcount > 0

# مفاتيح DRIP CLIENT
def get_key_stock():
    """إرجاع قائمة بمعرف المنتج والمدة وعدد المفاتيح غير المستخدمة"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT product_id, duration, COUNT(*) FROM key_codes WHERE used=0 GROUP BY product_id, duration")
    rows = c.fetchall()
    conn.close()
    return rows

def add_key_code(product_id, duration, code):
    """إضافة مفتاح جديد لـ DRIP CLIENT"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("INSERT INTO key_codes (product_id, duration, code, used) VALUES (?,?,?,0)", (product_id, duration, code))
    conn.commit()
    conn.close()

def del_key_code(product_id, duration, code):
    """حذف مفتاح DRIP CLIENT (غير مستخدم)"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("DELETE FROM key_codes WHERE product_id=? AND duration=? AND code=? AND used=0 LIMIT 1", (product_id, duration, code))
    conn.commit()
    conn.close()
    return c.rowcount > 0
