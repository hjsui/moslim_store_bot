# social_structure.py - Bilingual version

SOCIAL_STRUCTURE = {
    "instagram": {
        "name_ar": "انستغرام",
        "name_en": "Instagram",
        "icon": "📷",
        "categories": {
            "followers": {
                "name_ar": "متابعون",
                "name_en": "Followers",
                "icon": "👥",
                "subcategories": {
                    "auto_followers": {
                        "name_ar": "متابعون تلقائيون",
                        "name_en": "Auto Followers",
                        "icon": "⚡",
                        "service_ids": [1, 2, 3]
                    }
                }
            },
            "likes": {
                "name_ar": "إعجابات",
                "name_en": "Likes",
                "icon": "❤️",
                "service_ids": [4, 5]
            }
        }
    },
    "tiktok": {
        "name_ar": "تيك توك",
        "name_en": "TikTok",
        "icon": "🎵",
        "categories": {
            "followers": {
                "name_ar": "متابعون",
                "name_en": "Followers",
                "icon": "👥",
                "service_ids": [10, 11]
            },
            "views": {
                "name_ar": "مشاهدات",
                "name_en": "Views",
                "icon": "👀",
                "service_ids": [12]
            }
        }
    },
    # Add your other platforms and categories similarly
}

def get_platform_name(platform_id, lang):
    """Return platform name in the given language"""
    data = SOCIAL_STRUCTURE.get(platform_id, {})
    return data.get(f"name_{lang}", platform_id)

def get_category_name(platform_id, category_id, lang):
    """Return category name in the given language"""
    platform = SOCIAL_STRUCTURE.get(platform_id, {})
    cat = platform.get("categories", {}).get(category_id, {})
    return cat.get(f"name_{lang}", category_id)

def get_subcategory_name(platform_id, category_id, subcategory_id, lang):
    """Return subcategory name in the given language"""
    platform = SOCIAL_STRUCTURE.get(platform_id, {})
    cat = platform.get("categories", {}).get(category_id, {})
    sub = cat.get("subcategories", {}).get(subcategory_id, {})
    return sub.get(f"name_{lang}", subcategory_id)

def get_categories_list(platform_id, lang):
    """Return list of (category_id, display_name) for a platform in given language"""
    platform = SOCIAL_STRUCTURE.get(platform_id, {})
    categories = platform.get("categories", {})
    result = []
    for cat_id, cat_data in categories.items():
        name = cat_data.get(f"name_{lang}", cat_id)
        icon = cat_data.get("icon", "📂")
        result.append((cat_id, f"{icon} {name}"))
    return result

def get_subcategories_list(platform_id, category_id, lang):
    """Return list of (subcategory_id, display_name) for a category in given language"""
    platform = SOCIAL_STRUCTURE.get(platform_id, {})
    cat = platform.get("categories", {}).get(category_id, {})
    subs = cat.get("subcategories", {})
    result = []
    for sub_id, sub_data in subs.items():
        name = sub_data.get(f"name_{lang}", sub_id)
        icon = sub_data.get("icon", "📌")
        result.append((sub_id, f"{icon} {name}"))
    return result

def get_service_ids_from_structure(platform_id, category_id, subcategory_id=None):
    """Return list of service IDs for a given category or subcategory"""
    platform = SOCIAL_STRUCTURE.get(platform_id, {})
    cat = platform.get("categories", {}).get(category_id, {})
    if subcategory_id:
        sub = cat.get("subcategories", {}).get(subcategory_id, {})
        return sub.get("service_ids", [])
    else:
        return cat.get("service_ids", [])
