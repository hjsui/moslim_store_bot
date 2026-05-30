# social_structure.py
# هذا الملف يحدد الهيكل الهرمي لخدمات السوشل ميديا لكل منصة.

SOCIAL_STRUCTURE = {
    'facebook': {
        'icon': '📘',
        'name': 'فيسبوك',
        'categories': [
            {
                'name': 'مشاهدات',
                'icon': '👁️‍🗨️',
                'subcategories': [
                    {
                        'name': 'مشاهدات بث مباشر',
                        'service_ids': [1170, 1171, 2261, 1172, 1173, 1174, 2262, 1175, 2263, 2205, 2264, 2206, 2265, 2266]
                    },
                    {
                        'name': 'مشاهدات ريلز',
                        'service_ids': [1635, 1482, 1638]
                    },
                    {
                        'name': 'مشاهدات الفيديو',
                        'service_ids': [1681, 1311, 2357]
                    },
                    {
                        'name': 'مشاهدات ستوري',
                        'service_ids': [1506]
                    }
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
                    {
                        'name': 'متابعين حساب',
                        'service_ids': [987, 1523, 1771, 1524, 2131]
                    },
                    {
                        'name': 'متابعين صفحة',
                        'service_ids': [2486, 2487, 2488, 2489]
                    },
                    {
                        'name': 'متابعين (حساب وصفحة)',
                        'service_ids': [1155, 2255, 2429, 2430, 2431, 2064, 2335, 2254]
                    }
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
                    {
                        'name': 'مشاهدات البث المباشر',
                        'service_ids': [1223, 1224, 1225, 1226, 1227, 1228]
                    },
                    {
                        'name': 'مشاهدات الريلز',
                        'service_ids': [1495]
                    }
                ]
            },
            {
                'name': 'لايكات',
                'icon': '👍🏻',
                'subcategories': [
                    {
                        'name': 'لايكات الريلز',
                        'service_ids': [1494, 1792, 1794, 1829, 1189]
                    },
                    {
                        'name': 'لايكات البث المباشر',
                        'service_ids': [1229, 2014]
                    }
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
                    {
                        'name': 'تعليقات الريلز',
                        'service_ids': [1818, 2170, 1196, 2501]
                    },
                    {
                        'name': 'تعليقات البث المباشر',
                        'service_ids': [1232, 1231, 1230]
                    }
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
            {
                'name': 'نجوم تلجرام',
                'icon': '🌟',
                'service_ids': [2679]
            },
            {
                'name': 'اعضاء تلجرام',
                'icon': '🧑‍🧑‍🧒',
                'service_ids': [1986, 1486, 2090, 1443, 1485, 2327]
            },
            {
                'name': 'اعضاء بريميوم',
                'icon': '⭐',
                'service_ids': [1965, 1966, 1967, 1968, 1969, 1970, 1971, 1972, 1973, 1974, 1975]
            },
            {
                'name': 'توثيق تلجرام',
                'icon': '✔️',
                'service_ids': [1496, 1497, 1498]
            }
        ]
    },
    'instagram': {
        'icon': '📷',
        'name': 'انستغرام',
        'categories': []  # سيتم تركها فارغة الآن، يمكن إضافتها لاحقاً
    },
    'youtube': {
        'icon': '▶️',
        'name': 'يوتيوب',
        'categories': []
    },
    'twitter': {
        'icon': '🐦',
        'name': 'تويتر',
        'categories': []
    },
    'linkedin': {
        'icon': '🔗',
        'name': 'لينكد إن',
        'categories': []
    },
    'snapchat': {
        'icon': '👻',
        'name': 'سناب شات',
        'categories': []
    },
    'whatsapp': {
        'icon': '💬',
        'name': 'واتساب',
        'categories': []
    },
    'kwai': {
        'icon': '🎬',
        'name': 'كواي',
        'categories': []
    },
    'games': {
        'icon': '🎮',
        'name': 'ألعاب واشتراكات',
        'categories': []
    },
    'other': {
        'icon': '📁',
        'name': 'أخرى',
        'categories': []
    }
}

def get_service_ids_from_structure(platform_id, category_name=None, subcategory_name=None):
    """استرجاع قائمة service_ids من الهيكل بناءً على المسار."""
    platform = SOCIAL_STRUCTURE.get(platform_id)
    if not platform:
        return []
    for cat in platform.get('categories', []):
        if category_name is None or cat['name'] == category_name:
            if 'service_ids' in cat:
                return cat['service_ids']
            if subcategory_name is not None:
                for sub in cat.get('subcategories', []):
                    if sub['name'] == subcategory_name:
                        return sub['service_ids']
            else:
                # إذا لم نحدد تحت تصنيف، نجمع كل service_ids من التصنيفات الفرعية
                all_ids = []
                for sub in cat.get('subcategories', []):
                    all_ids.extend(sub.get('service_ids', []))
                return all_ids
    return []

def get_categories_list(platform_id):
    """إرجاع قائمة التصنيفات الرئيسية لمنصة معينة."""
    platform = SOCIAL_STRUCTURE.get(platform_id)
    if not platform:
        return []
    return [(cat['name'], cat['icon']) for cat in platform.get('categories', [])]

def get_subcategories_list(platform_id, category_name):
    """إرجاع قائمة التصنيفات الفرعية لتصنيف معين."""
    platform = SOCIAL_STRUCTURE.get(platform_id)
    if not platform:
        return []
    for cat in platform.get('categories', []):
        if cat['name'] == category_name:
            if 'subcategories' in cat:
                return [(sub['name'], sub['icon']) for sub in cat['subcategories']]
    return []
