# social_api.py
# هذا الملف مسؤول عن التواصل مع API موقع xfollowr لخدمات السوشل ميديا
# تم تعديله لاستخدام قاعدة بيانات ثابتة للخدمات (services_mapping.py) لضمان تصنيف دقيق.

import requests
from config import SOCIAL_API_URL, SOCIAL_API_KEY, SOCIAL_PROFIT_PERCENT
from services_mapping import SERVICE_TO_PLATFORM

def api_request(action, params=None):
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
    return api_request('services')

def get_balance():
    return api_request('balance')

def add_order(service_id, link, quantity, **kwargs):
    params = {'service': service_id, 'link': link, 'quantity': quantity}
    params.update(kwargs)
    return api_request('add', params)

def get_order_status(order_id):
    return api_request('status', {'order': order_id})

def get_orders_status(order_ids):
    ids_str = ','.join(str(i) for i in order_ids)
    return api_request('status', {'orders': ids_str})

def calculate_price_with_profit(original_price):
    return round(original_price * (1 + SOCIAL_PROFIT_PERCENT / 100), 2)

# ---------- قائمة المنصات الكاملة (12 منصة) مع أيقوناتها ----------
PLATFORMS_MAP = {
    'facebook': {'name': 'فيسبوك', 'icon': '📘', 'keywords': []},
    'instagram': {'name': 'انستغرام', 'icon': '📷', 'keywords': []},
    'tiktok': {'name': 'تيك توك', 'icon': '🎵', 'keywords': []},
    'telegram': {'name': 'تلجرام', 'icon': '✈️', 'keywords': []},
    'youtube': {'name': 'يوتيوب', 'icon': '▶️', 'keywords': []},
    'twitter': {'name': 'تويتر', 'icon': '🐦', 'keywords': []},
    'linkedin': {'name': 'لينكد إن', 'icon': '🔗', 'keywords': []},
    'snapchat': {'name': 'سناب شات', 'icon': '👻', 'keywords': []},
    'whatsapp': {'name': 'واتساب', 'icon': '💬', 'keywords': []},
    'kwai': {'name': 'كواي', 'icon': '🎬', 'keywords': []},
    'games': {'name': 'ألعاب واشتراكات', 'icon': '🎮', 'keywords': []},
    'other': {'name': 'أخرى', 'icon': '📁', 'keywords': []}
}

def organize_services_by_platform(services_list):
    """
    تصنيف الخدمات حسب المنصة باستخدام:
    1. التعيين المباشر من SERVICE_TO_PLATFORM (الأولوية الأولى).
    2. إذا لم يتم العثور على تعيين، نستخدم الكلمات المفتاحية (لكننا سنلغيها لعدم دقتها، ونضعها في 'other').
    """
    # إنشاء هيكل لكل المنصات مسبقاً
    organized = {}
    for plat_id, plat_info in PLATFORMS_MAP.items():
        organized[plat_id] = {
            'name': plat_info['name'],
            'icon': plat_info['icon'],
            'services': []
        }

    # تصنيف كل خدمة
    for service in services_list:
        service_id = service.get('service')
        assigned_platform = None
        
        # 1. التعيين المباشر من SERVICE_TO_PLATFORM
        if service_id in SERVICE_TO_PLATFORM:
            assigned_platform = SERVICE_TO_PLATFORM[service_id]
        else:
            # 2. إذا لم نجد تعييناً، نضع الخدمة في 'other' (لا نستخدم الكلمات المفتاحية لتفادي الأخطاء)
            # ولكن يمكننا اختيارياً الاحتفاظ ببعض الكلمات المفتاحية الأساسية لمنصات معروفة،
            # لكن الأفضل إضافة service_id لاحقاً يدوياً.
            assigned_platform = 'other'
        
        # إضافة الخدمة إلى المنصة المخصصة
        if assigned_platform in organized:
            organized[assigned_platform]['services'].append(service)
        else:
            organized['other']['services'].append(service)
    
    return organized

def get_platforms_list(organized_services):
    """إرجاع قائمة المنصات مع أيقوناتها وعدد الخدمات"""
    platforms = []
    for plat_id, data in organized_services.items():
        platforms.append({
            'id': plat_id,
            'name': data['name'],
            'icon': data['icon'],
            'service_count': len(data['services'])
        })
    return platforms

def get_all_services_by_platform(organized_services, platform_id):
    """إرجاع قائمة الخدمات لمنصة معينة"""
    if platform_id in organized_services:
        return organized_services[platform_id]['services']
    return []
