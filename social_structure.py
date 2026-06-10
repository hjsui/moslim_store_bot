# social_structure.py
# هيكل خدمات السوشل ميديا لجميع المنصات (نسخة كاملة ومحدثة)
# يتوافق مع services_mapping.py ويحتوي على جميع service_ids المطلوبة

SOCIAL_STRUCTURE = {
    'facebook': {
        'icon': '📘',
        'name': 'فيسبوك',
        'categories': [
            {
                'name': 'مشاهدات',
                'icon': '👁️‍🗨️',
                'subcategories': [
                    {'name': 'مشاهدات بث مباشر', 'service_ids': [1170, 1171, 2261, 1172, 1173, 1174, 2262, 1175, 2263, 2205, 2264, 2206, 2265, 2266]},
                    {'name': 'مشاهدات ريلز', 'service_ids': [1635, 1482, 1638]},
                    {'name': 'مشاهدات الفيديو', 'service_ids': [1681, 1311, 2357]},
                    {'name': 'مشاهدات ستوري', 'service_ids': [1506]}
                ]
            },
            {
                'name': 'لايكات',
                'icon': '👍🏻',
                'service_ids': [1606, 1803]
            },
            {
                'name': 'متابعين',
                'icon': '👤',
                'subcategories': [
                    {'name': 'متابعين حساب', 'service_ids': [987, 1523, 1771, 1524, 2131]},
                    {'name': 'متابعين صفحة', 'service_ids': [2486, 2487, 2488, 2489]},
                    {'name': 'متابعين (حساب وصفحة)', 'service_ids': [1155, 2255, 2429, 2430, 2431, 2064, 2335, 2254]}
                ]
            },
            {
                'name': 'تعليقات',
                'icon': '💬',
                'service_ids': [2215]
            },
            {
                'name': 'اعضاء جروب فيسبوك',
                'icon': '🧑‍🧑‍🧒',
                'service_ids': [2013, 1518, 1874, 1875, 1876, 1877, 1878, 1402, 1636, 1328, 1505]
            },
            {
                'name': 'توثيق فيسبوك شهري',
                'icon': '✔️',
                'service_ids': [2136]
            }
        ]
    },
    'tiktok': {
        'icon': '🎵',
        'name': 'تيك توك',
        'categories': [
            {
                'name': 'مشاهدات',
                'icon': '👁️‍🗨️',
                'subcategories': [
                    {'name': 'مشاهدات البث المباشر', 'service_ids': [1223, 1224, 1225, 1226, 1227, 1228]},
                    {'name': 'مشاهدات الريلز', 'service_ids': [1495]}
                ]
            },
            {
                'name': 'لايكات',
                'icon': '👍🏻',
                'subcategories': [
                    {'name': 'لايكات الريلز', 'service_ids': [1494, 1792, 1794, 1829, 1189]},
                    {'name': 'لايكات البث المباشر', 'service_ids': [1229, 2014]}
                ]
            },
            {
                'name': 'متابعين',
                'icon': '👤',
                'service_ids': [1894, 2607, 2608, 2609, 2610, 2611, 2612, 1195, 1531, 2026]
            },
            {
                'name': 'تعليقات',
                'icon': '💬',
                'subcategories': [
                    {'name': 'تعليقات الريلز', 'service_ids': [1818, 2170, 1196, 2501]},
                    {'name': 'تعليقات البث المباشر', 'service_ids': [1232, 1231, 1230]}
                ]
            },
            {
                'name': 'ريبوست',
                'icon': '🔄',
                'service_ids': [2627, 2628, 2629, 2630, 2631, 2632]
            }
        ]
    },
    'telegram': {
        'icon': '✈️',
        'name': 'تلجرام',
        'categories': [
            {'name': 'نجوم تلجرام', 'icon': '🌟', 'service_ids': [2679]},
            {'name': 'اعضاء تلجرام', 'icon': '🧑‍🧑‍🧒', 'service_ids': [1986, 1486, 2090, 1443, 1485, 2327]},
            {'name': 'اعضاء بريميوم', 'icon': '⭐', 'service_ids': [1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975]},
            {'name': 'توثيق تلجرام', 'icon': '✔️', 'service_ids': [1496, 1497, 1498]}
        ]
    },
    'instagram': {
        'icon': '📷',
        'name': 'انستغرام',
        'categories': [
            {'name': 'متابعين', 'icon': '👤', 'service_ids': [2328, 2329, 2330, 2331, 2332, 1886, 938, 1992, 1993, 2033, 2034, 1664, 1991]},
            {'name': 'لايكات', 'icon': '👍🏻', 'service_ids': []},
            {'name': 'تعليقات', 'icon': '💬', 'service_ids': []},
            {'name': 'مشاهدات', 'icon': '👁️‍🗨️', 'service_ids': []}
        ]
    },
    'youtube': {
        'icon': '▶️',
        'name': 'يوتيوب',
        'categories': [
            {'name': 'مشتركين', 'icon': '👤', 'service_ids': [1752]},
            {'name': 'مشاهدات', 'icon': '👁️‍🗨️', 'service_ids': []},
            {'name': 'لايكات', 'icon': '👍🏻', 'service_ids': []}
        ]
    },
    'twitter': {
        'icon': '🐦',
        'name': 'تويتر',
        'categories': [
            {'name': 'متابعين', 'icon': '👤', 'service_ids': []},
            {'name': 'لايكات', 'icon': '👍🏻', 'service_ids': []},
            {'name': 'تعليقات', 'icon': '💬', 'service_ids': []},
            {'name': 'ريتويت', 'icon': '🔄', 'service_ids': []}
        ]
    },
    'linkedin': {
        'icon': '🔗',
        'name': 'لينكد إن',
        'categories': [
            {'name': 'متابعين', 'icon': '👤', 'service_ids': []}
        ]
    },
    'snapchat': {
        'icon': '👻',
        'name': 'سناب شات',
        'categories': [
            {'name': 'متابعين', 'icon': '👤', 'service_ids': [1600]}
        ]
    },
    'whatsapp': {
        'icon': '💬',
        'name': 'واتساب',
        'categories': [
            {'name': 'اعضاء قناة', 'icon': '🧑‍🧑‍🧒', 'service_ids': [1386, 2106, 2107, 2108, 2109, 2110]}
        ]
    },
    'kwai': {
        'icon': '🎬',
        'name': 'كواي',
        'categories': [
            {'name': 'متابعين', 'icon': '👤', 'service_ids': [1333, 2411, 2412, 1618]},
            {'name': 'لايكات', 'icon': '👍🏻', 'service_ids': [1880, 2720]}
        ]
    },
    'games': {
        'icon': '🎮',
        'name': 'ألعاب واشتراكات',
        'categories': [
            {'name': 'اشتراكات', 'icon': '🎟️', 'service_ids': []},
            {'name': 'شحن ألعاب', 'icon': '⚡', 'service_ids': []}
        ]
    },
    'other': {
        'icon': '📁',
        'name': 'أخرى',
        'categories': [
            {'name': 'خدمات متنوعة', 'icon': '🔧', 'service_ids': []}
        ]
    }
}

def get_categories_list(platform_id):
    """إرجاع قائمة التصنيفات الرئيسية لمنصة معينة"""
    platform = SOCIAL_STRUCTURE.get(platform_id)
    if not platform:
        return []
    return [(cat['name'], cat['icon']) for cat in platform.get('categories', [])]

def get_subcategories_list(platform_id, category_name):
    """إرجاع قائمة التصنيفات الفرعية لتصنيف معين"""
    platform = SOCIAL_STRUCTURE.get(platform_id)
    if not platform:
        return []
    for cat in platform.get('categories', []):
        if cat['name'] == category_name and 'subcategories' in cat:
            return [(sub['name'], sub['icon']) for sub in cat['subcategories']]
    return []

def get_service_ids_from_structure(platform_id, category_name=None, subcategory_name=None):
    """إرجاع قائمة service_ids للمسار المحدد"""
    platform = SOCIAL_STRUCTURE.get(platform_id)
    if not platform:
        return []
    for cat in platform.get('categories', []):
        if category_name is None or cat['name'] == category_name:
            if subcategory_name is not None and 'subcategories' in cat:
                for sub in cat['subcategories']:
                    if sub['name'] == subcategory_name:
                        return sub.get('service_ids', [])
            elif 'service_ids' in cat:
                return cat['service_ids']
            elif 'subcategories' in cat:
                all_ids = []
                for sub in cat['subcategories']:
                    all_ids.extend(sub.get('service_ids', []))
                return all_ids
    return []
