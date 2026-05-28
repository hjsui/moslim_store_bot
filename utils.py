from flask import Flask
from threading import Thread
from config import ADMIN_IDS, WHITELISTED_USERS

# دوال المساعدة
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_whitelisted(user_id):
    return user_id in WHITELISTED_USERS

# خادم Flask للبقاء حياً على Render
app = Flask('')

@app.route('/')
def home():
    return "MOSLIM STORE IS ONLINE ✅"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
