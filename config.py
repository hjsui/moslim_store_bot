import os

# ------------------- متغيرات البيئة -------------------
BOT_TOKEN = os.environ.get('BOT_TOKEN')
LOG_CHANNEL_ID = os.environ.get('LOG_CHANNEL_ID')
if LOG_CHANNEL_ID:
    LOG_CHANNEL_ID = int(LOG_CHANNEL_ID)
else:
    LOG_CHANNEL_ID = None

# ------------------- ثوابت المتجر -------------------
ADMIN_IDS = [8530485909]          # قائمة المديرين (قبول الطلبات)
OWNER_ID = 8530485909             # المالك الوحيد (للأوامر الإدارية مثل /meow)
WHITELISTED_USERS = [8615239297]   # قائمة الوكلاء الذين يسحبون مجاناً
STORE_PASSWORD = "555451265696++ftytyuiuliyty6654923//fyytu@moslim.com"
CHANNEL_PROOFS = "https://t.me/moslim_store1"
ADMIN_CONTACT = "https://t.me/Mibel_Store"

# ------------------- المخزون الحالي -------------------
codes_inventory = {
    "110": ["2869135500382282", "8772380136887137", "9317053383056636", "8344827763739908"],
    "231": ["5582470301677821"],
    "583": [],
    "1188": ["2514893008691065", "9405455819525108"],
    "2420": ["8054042222321677", "7801845005665882", "7240425674452852"]
}
prices = {"110": "11", "231": "21", "583": "52", "1188": "100", "2420": "222"}

keys_inventory = {
    "dripclient": {
        "name_ar": "DRIP CLIENT APKMOD 👾",
        "name_en": "DRIP CLIENT APKMOD 👾",
        "prices": {"1": 20, "3": 25, "7": 50, "15": 78, "30": 120},
        "codes": {
            "1": ["8704258740"],
            "3": [],
            "7": [],
            "15": [],
            "30": ["6732684380", "7481744555"]
        }
    }
}

apps_inventory = {
    "capcut": {
        "name_ar": "🎬 CapCut PRO",
        "name_en": "🎬 CapCut PRO",
        "price": 20,
        "update_channel": "https://t.me/+zyJW6ZvNp98yMzFk",
        "link": "https://t.me/+zyJW6ZvNp98yMzFk"
    },
    "inshot": {
        "name_ar": "✂️ Inshot PRI",
        "name_en": "✂️ Inshot PRI",
        "price": 15,
        "update_channel": "https://t.me/+fDPaaezCFKNmZmM0",
        "link": "https://t.me/+fDPaaezCFKNmZmM0"
    },
    "picsart": {
        "name_ar": "🖌️ Picsart PRO",
        "name_en": "🖌️ Picsart PRO",
        "price": 25,
        "update_channel": "https://t.me/+-6sCG_0g6Mw3ODI0",
        "link": "https://t.me/+-6sCG_0g6Mw3ODI0"
    }
}

# ------------------- إعدادات API السوشل ميديا -------------------
SOCIAL_API_URL = "https://xfollowr.com/api/v2"
SOCIAL_API_KEY = "cae8f1e5da7b2c5db19d5c44a3e55c81"
SOCIAL_PROFIT_PERCENT = 25   # نسبة الربح 25%

# ------------------- إعدادات العملة -------------------
DEFAULT_CURRENCY = 'mad'      # العملة الافتراضية (mad أو usd)
USD_TO_MAD = 10.0             # سعر صرف الدولار إلى الدرهم (1 دولار = 10 دراهم)
