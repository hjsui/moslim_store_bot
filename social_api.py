import requests
import json
from config import SOCIAL_API_URL, SOCIAL_API_KEY, SOCIAL_PROFIT_PERCENT

def api_request(action, params=None):
    """إرسال طلب إلى API xfollowr"""
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
    """جلب قائمة الخدمات من API"""
    return api_request('services')

def get_balance():
    """جلب الرصيد المتبقي في حساب API"""
    return api_request('balance')

def add_order(service_id, link, quantity, runs=None, interval=None, comments=None, username=None, min_val=None, max_val=None, posts=None, old_posts=None, delay=None, expiry=None):
    """إضافة طلب جديد إلى API"""
    params = {
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    if runs:
        params['runs'] = runs
    if interval:
        params['interval'] = interval
    if comments:
        params['comments'] = comments
    if username:
        params['username'] = username
    if min_val:
        params['min'] = min_val
    if max_val:
        params['max'] = max_val
    if posts is not None:
        params['posts'] = posts
    if old_posts is not None:
        params['old_posts'] = old_posts
    if delay:
        params['delay'] = delay
    if expiry:
        params['expiry'] = expiry
    return api_request('add', params)

def get_order_status(order_id):
    """الحصول على حالة طلب معين"""
    return api_request('status', {'order': order_id})

def get_orders_status(order_ids):
    """الحصول على حالة عدة طلبات"""
    ids_str = ','.join(str(i) for i in order_ids)
    return api_request('status', {'orders': ids_str})

def calculate_price_with_profit(original_price):
    """حساب السعر بعد إضافة نسبة الربح"""
    return original_price * (1 + SOCIAL_PROFIT_PERCENT / 100)
