# services_mapping.py
# هذا الملف يحدد المنصة الصحيحة لكل خدمة بناءً على service_id المعروف من API.
# تم إنشاؤه يدوياً بناءً على البيانات التي قدمها صاحب المتجر.

# قاموس يحول service_id -> platform_id (من بين الـ 12 منصة المعرفة)
SERVICE_TO_PLATFORM = {
    # فيسبوك
    1155: 'facebook',
    2255: 'facebook',
    2429: 'facebook',
    2430: 'facebook',
    2431: 'facebook',
    2064: 'facebook',
    2335: 'facebook',
    2254: 'facebook',
    1732: 'facebook',
    1606: 'facebook',
    1803: 'facebook',
    2136: 'facebook',
    
    # تيك توك
    1494: 'tiktok',
    1522: 'tiktok',
    1559: 'tiktok',
    1560: 'tiktok',
    1545: 'tiktok',
    1422: 'tiktok',
    1423: 'tiktok',
    1178: 'tiktok',
    
    # تلجرام
    1497: 'telegram',
    1498: 'telegram',
    # باقي خدمات تلجرام (بدون service_id واضح) سيتم تصنيفها عبر الكلمات المفتاحية
    
    # انستغرام
    2328: 'instagram',
    2329: 'instagram',
    2330: 'instagram',
    2331: 'instagram',
    2332: 'instagram',
    1886: 'instagram',
    938: 'instagram',
    1992: 'instagram',
    1993: 'instagram',
    2033: 'instagram',
    2034: 'instagram',
    1664: 'instagram',
    1991: 'instagram',
    
    # يوتيوب
    1752: 'youtube',
    
    # كواي
    1333: 'kwai',
    2411: 'kwai',
    2412: 'kwai',
    1618: 'kwai',
    1880: 'kwai',
    2720: 'kwai',
    
    # واتساب
    1386: 'whatsapp',
    2106: 'whatsapp',
    2107: 'whatsapp',
    2108: 'whatsapp',
    2109: 'whatsapp',
    2110: 'whatsapp',
    
    # لينكد إن
    # (لم يظهر service_id واضح، سيتم استخدام الكلمات المفتاحية)
    
    # سناب شات
    1600: 'snapchat',  # من البيانات: متابعين سناب شات عرب (1600)
    
    # ألعاب واشتراكات (بدون service_id واضح، سيتم استخدام الكلمات المفتاحية)
}

# يمكن إضافة المزيد من المعرفات يدوياً مستقبلاً عند ظهور خدمات جديدة.
