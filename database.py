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
    c.execute('''CREATE TABLE IF NOT EXISTS ff_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, quantity TEXT, code TEXT, used INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS key_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, duration TEXT, code TEXT, used INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()
    # تأكد من ترحيل الأكواد من config.py إذا كانت موجودة (مرة واحدة)
    migrate_ff_codes()
    migrate_key_codes()

def migrate_ff_codes():
    """نقل الأكواد من config.py إلى ff_codes (إذا كان الجدول فارغاً)"""
    try:
        from config import codes_inventory
        if not codes_inventory:
            return
    except ImportError:
        return
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ff_codes")
    count = c.fetchone()[0]
    if count == 0:
        for qty, codes in codes_inventory.items():
            for code in codes:
                if code and code.strip():
                    c.execute("INSERT INTO ff_codes (quantity, code, used) VALUES (?,?,0)", (str(qty), code))
        conn.commit()
        print("✅ تم ترحيل أكواد الجواهر إلى قاعدة البيانات")
    conn.close()

def migrate_key_codes():
    try:
        from config import keys_inventory
    except ImportError:
        return
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM key_codes")
    if c.fetchone()[0] == 0:
        for prod_id, prod_data in keys_inventory.items():
            for duration, codes in prod_data["codes"].items():
                for code in codes:
                    if code and code.strip():
                        c.execute("INSERT INTO key_codes (product_id, duration, code, used) VALUES (?,?,?,0)", (prod_id, str(duration), code))
        conn.commit()
        print("✅ تم ترحيل المفاتيح إلى قاعدة البيانات")
    conn.close()

# دوال المستخدم
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

# ========== دوال المخزون (الأساسية) ==========
def get_ff_code(quantity):
    """استرجاع كود غير مستخدم من الكمية المطلوبة وتمييزه كمستخدم"""
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    qty_str = str(quantity)
    c.execute("SELECT id, code FROM ff_codes WHERE quantity=? AND used=0 LIMIT 1", (qty_str,))
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
    c.execute("INSERT INTO ff_codes (quantity, code, used) VALUES (?,?,0)", (str(quantity), code))
    conn.commit()
    conn.close()

def del_ff_code(quantity, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("DELETE FROM ff_codes WHERE quantity=? AND code=? AND used=0 LIMIT 1", (str(quantity), code))
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
    dur_str = str(duration)
    c.execute("SELECT id, code FROM key_codes WHERE product_id=? AND duration=? AND used=0 LIMIT 1", (product_id, dur_str))
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
    c.execute("INSERT INTO key_codes (product_id, duration, code, used) VALUES (?,?,?,0)", (product_id, str(duration), code))
    conn.commit()
    conn.close()

def del_key_code(product_id, duration, code):
    conn = sqlite3.connect('moslim_store.db')
    c = conn.cursor()
    c.execute("DELETE FROM key_codes WHERE product_id=? AND duration=? AND code=? AND used=0 LIMIT 1", (product_id, str(duration), code))
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
