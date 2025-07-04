# تكوين APIs للحصول على بيانات السيارات

## إعداد مفاتيح APIs

### 1. في ملف site_config.json:

```json
{
  "vehicle_api_keys": {
    "carapi": "your_carapi_key_here",
    "vehicle_database": "your_vehicle_db_key_here"
  }
}
```

### 2. أو في متغيرات البيئة:

```bash
export CARAPI_KEY="your_carapi_key_here"
export VEHICLE_DB_KEY="your_vehicle_db_key_here"
```

## APIs المدعومة

### 1. CarAPI (مدفوع - موصى به)
- **الموقع**: https://carapi.app/
- **التسعير**: يبدأ من $15/شهر
- **الميزات**:
  - تغطية عالمية شاملة
  - دعم فك VIN 
  - بيانات محدثة باستمرار
  - دعم العربية جزئياً

### 2. Vehicle Database API (مدفوع)
- **الموقع**: https://www.vehicle-database.com/
- **التسعير**: يبدأ من $25/شهر  
- **الميزات**:
  - أكثر من 80 مليون سجل
  - 25+ API مختلف
  - صور حقيقية للمركبات
  - تغطية ممتازة للسوق الخليجي

### 3. NHTSA (مجاني - احتياطي)
- **الموقع**: https://vpic.nhtsa.dot.gov/api/
- **التسعير**: مجاني
- **الميزات**:
  - مصدر حكومي موثوق
  - فك VIN مجاني
  - تركيز على السوق الأمريكي
  - بيانات محدودة للسوق العربي

## طريقة الاستخدام

### 1. تفعيل التحديث التلقائي

```python
# تشغيل تحديث فوري
frappe.call({
    method: 'universal_workshop.vehicle_management.api.sync_vehicle_data_from_apis'
})

# جلب الماركات من API
frappe.call({
    method: 'universal_workshop.vehicle_management.api.get_vehicle_makes_from_api',
    args: { force_refresh: true }
})
```

### 2. التحديث اليدوي كخيار احتياطي

عند عدم توفر الإنترنت أو فشل APIs، يمكن إضافة الماركات والموديلات يدوياً:

1. انتقل إلى: **Vehicle Management > Vehicle Make**
2. اضغط **New**
3. قم بتعبئة البيانات باللغتين العربية والإنجليزية
4. حدد خانة **Manual Entry**

### 3. مراقبة حالة التحديث

```javascript
// عرض حالة آخر تحديث
frappe.call({
    method: 'universal_workshop.vehicle_management.api.get_api_sync_status'
})
```

## الفوائد المتوقعة

### ✅ تحسين تجربة المستخدم
- تقليل الأخطاء الإملائية
- توحيد أسماء الماركات والموديلات
- اقتراحات ذكية أثناء الكتابة

### ✅ توفير الوقت
- عدم الحاجة للإدخال اليدوي المستمر
- تحديث تلقائي للموديلات الجديدة
- بحث سريع ودقيق

### ✅ تغطية شاملة
- دعم أكثر من 100 ماركة عالمية
- موديلات من 1900 حتى 2025
- تغطية ممتازة للسوق الخليجي والعماني

### ✅ موثوقية البيانات
- مصادر موثقة ومحدثة
- فك VIN تلقائي للتحقق
- نظام احتياطي في حالة فشل API

## أمثلة للاستخدام

### مثال 1: جلب ماركات تويوتا
```python
makes = get_vehicle_makes_from_api()
toyota_models = get_vehicle_models_from_api("Toyota", 2024)
```

### مثال 2: فحص آخر تحديث
```python
status = get_api_sync_status()
print(f"آخر تحديث: {status['last_sync']['last_sync_time']}")
print(f"عدد الماركات من API: {status['api_makes_count']}")
```

## الدعم الفني

للحصول على مساعدة في إعداد APIs أو حل مشاكل التكامل:
- البريد الإلكتروني: support@universal-workshop.om
- الهاتف: +968 24 123456
- GitHub Issues: https://github.com/universal-workshop/erpnext

## آخر تحديث
**التاريخ**: 21 يونيو 2025  
**الإصدار**: v2.0.0
**المطور**: م. سعيد العدوي 