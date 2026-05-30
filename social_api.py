# social_api.py
# هذا الملف مسؤول عن التواصل مع API موقع xfollowr لخدمات السوشل ميديا
# تمت إضافة دوال للبحث عن الخدمات بواسطة service_id وجلب عدة خدمات دفعة واحدة

import requests
import time
from config import SOCIAL_API_URL, SOCIAL_API_KEY, SOCIAL_PROFIT_PERCENT

# متغيرات التخزين المؤقت للخدمات
_services_cache = None
_services_cache_time = 0
SERVICES_CACHE_TTL = 300  # 5 دقائق

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

def get_services(force_refresh=False):
    """
    جلب قائمة جميع الخدمات من الـ API مع تخزين مؤقت.
    force_refresh: تجاهل التخزين المؤقت وجلب البيانات جديدة.
    """
    global _services_cache, _services_cache_time
    now = time.time()
    if force_refresh or _services_cache is None or now - _services_cache_time > SERVICES_CACHE_TTL:
        _services_cache = api_request('services')
        _services_cache_time = now
    return _services_cache

def get_service_by_id(service_id):
    """
    البحث عن خدمة محددة باستخدام service_id من القائمة المخزنة.
    يعيد كامل بيانات الخدمة (dict) أو None إذا لم توجد.
    """
    services = get_services()
    if not services:
        return None
    for service in services:
        if service.get('service') == service_id:
            return service
    return None

def get_services_by_ids(service_ids):
    """
    استرجاع قائمة الخدمات لمجموعة من service_ids.
    service_ids: قائمة بأرقام الخدمات.
    يعيد قائمة بالخدمات الموجودة فقط.
    """
    services = get_services()
    if not services:
        return []
    # إنشاء قاموس للبحث السريع
    service_dict = {s['service']: s for s in services}
    result = []
    for sid in service_ids:
        if sid in service_dict:
            result.append(service_dict[sid])
    return result

def get_balance():
    """جلب الرصيد المتبقي في حساب الـ API"""
    return api_request('balance')

def add_order(service_id, link, quantity, **kwargs):
    """
    إضافة طلب جديد إلى الـ API
    المعاملات الإجبارية: service_id, link, quantity
    الباقي اختياري حسب نوع الخدمة (runs, interval, comments, ...)
    """
    params = {
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    # إضافة أي معاملات إضافية تم تمريرها
    params.update(kwargs)
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
