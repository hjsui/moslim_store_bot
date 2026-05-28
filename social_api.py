# social_api.py
# هذا الملف مسؤول عن التواصل مع API موقع xfollowr لخدمات السوشل ميديا
import requests
from config import SOCIAL_API_URL, SOCIAL_API_KEY, SOCIAL_PROFIT_PERCENT

def api_request(action, params=None):
    """
    إرسال طلب إلى API xfollowr
    action: الإجراء المطلوب (services, add, status, balance, ...)
    params: قاموس المعاملات الخاصة بالإجراء
    """
    if params is None:
        params = {}
    params['key'] = SOCIAL_API_KEY
    params['action'] = action
    try:
        response = requests.post(SOCIAL_API_URL, data=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"API exception: {e}")
        return None

def get_services():
    """جلب قائمة جميع الخدمات من الـ API"""
    return api_request('services')

def get_balance():
    """جلب الرصيد المتبقي في حساب الـ API"""
    return api_request('balance')

def add_order(service_id, link, quantity, runs=None, interval=None, comments=None, username=None, min_val=None, max_val=None, posts=None, old_posts=None, delay=None, expiry=None):
    """
    إضافة طلب جديد إلى الـ API
    المعاملات الإجبارية: service_id, link, quantity
    الباقي اختياري حسب نوع الخدمة
    """
    params = {
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    if runs is not None:
        params['runs'] = runs
    if interval is not None:
        params['interval'] = interval
    if comments is not None:
        params['comments'] = comments
    if username is not None:
        params['username'] = username
    if min_val is not None:
        params['min'] = min_val
    if max_val is not None:
        params['max'] = max_val
    if posts is not None:
        params['posts'] = posts
    if old_posts is not None:
        params['old_posts'] = old_posts
    if delay is not None:
        params['delay'] = delay
    if expiry is not None:
        params['expiry'] = expiry
    return api_request('add', params)

def get_order_status(order_id):
    """الحصول على حالة طلب معين باستخدام رقم الطلب من الـ API"""
    return api_request('status', {'order': order_id})

def get_orders_status(order_ids):
    """الحصول على حالة عدة طلبات باستخدام قائمة بالأرقام"""
    ids_str = ','.join(str(i) for i in order_ids)
    return api_request('status', {'orders': ids_str})

def calculate_price_with_profit(original_price):
    """
    حساب السعر النهائي بعد إضافة نسبة الربح المحددة في config.py
    original_price: السعر الأصلي بالدولار أو العملة التي يعطيها الـ API
    يعيد السعر بالدرهم المغربي (MAD) مع تقريب لأقرب رقمين عشريين
    """
    return round(original_price * (1 + SOCIAL_PROFIT_PERCENT / 100), 2)

# ========== دوال تنظيم الخدمات حسب المنصة (للبوت) ==========

def organize_services_by_platform(services_list):
    """
    يأخذ قائمة الخدمات من الـ API ويعيدها منظمة حسب المنصة.
    يتم استخراج المنصة من اسم الخدمة باستخدام كلمات مفتاحية شائعة.
    """
    # قائمة المنصات والكلمات المفتاحية المرتبطة بها
    platforms = {
        'facebook': ['facebook', 'fb', 'meta', 'page', 'post', 'video', 'reel', 'like', 'follow', 'share'],
        'instagram': ['instagram', 'insta', 'ig', 'reel', 'story', 'igtv', 'followers', 'likes', 'views', 'comments'],
        'tiktok': ['tiktok', 'tk', 'followers', 'likes', 'views', 'hearts'],
        'telegram': ['telegram', 'tg', 'members', 'views', 'channel', 'group'],
        'youtube': ['youtube', 'yt', 'views', 'subscribers', 'likes', 'comments', 'shares'],
        'twitter': ['twitter', 'x', 'tweet', 'retweet', 'followers', 'likes'],
        'linkedin': ['linkedin', 'in', 'connections', 'followers', 'views'],
        'snapchat': ['snapchat', 'snap', 'views', 'score', 'friends'],
        'whatsapp': ['whatsapp', 'wa', 'group', 'members', 'status'],
        'kwai': ['kwai', 'followers', 'views', 'likes'],
        'other_games': ['pubg', 'freefire', 'cod', 'genshin', 'capcut', 'chatgpt', 'kick', 'game']
    }
    
    organized = {}  # الهيكل النهائي
    
    for service in services_list:
        service_name = service.get('name', '').lower()
        assigned = False
        
        for platform, keywords in platforms.items():
            if any(keyword in service_name for keyword in keywords):
                if platform not in organized:
                    organized[platform] = {
                        'name': platform,
                        'services': []
                    }
                organized[platform]['services'].append(service)
                assigned = True
                break
        
        # إذا لم يتم تصنيف الخدمة ضمن أي منصة معروفة، نضعها في قسم "أخرى"
        if not assigned:
            if 'other' not in organized:
                organized['other'] = {
                    'name': 'أخرى',
                    'services': []
                }
            organized['other']['services'].append(service)
    
    return organized

def get_platforms_list(organized_services):
    """
    إرجاع قائمة المنصات المتاحة مع عدد الخدمات لكل منصة
    """
    platforms = []
    for key, data in organized_services.items():
        platforms.append({
            'id': key,
            'name': data['name'],
            'service_count': len(data['services'])
        })
    return platforms

def get_all_services_by_platform(organized_services, platform_id):
    """
    إرجاع قائمة بجميع خدمات منصة معينة (بدون تقسيم إلى تصنيفات)
    """
    if platform_id in organized_services:
        return organized_services[platform_id]['services']
    return []
