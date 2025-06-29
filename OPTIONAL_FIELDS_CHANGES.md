# تعديلات نظام التراخيص - الحقول الاختيارية

## التغييرات المطبقة

### 1. ملف Business Registration DocType JSON
**الملف**: `apps/universal_workshop/universal_workshop/license_management/doctype/business_registration/business_registration.json`

#### التغييرات:
- **رقم السجل التجاري**: إزالة `"reqd": 1` وتغيير التسمية إلى "Business License Number (Optional)"
- **البريد الإلكتروني**: تغيير التسمية إلى "Email (Optional)"

### 2. ملف Business Registration Python Controller
**الملف**: `apps/universal_workshop/universal_workshop/license_management/doctype/business_registration/business_registration.py`

#### التغييرات:
- **دالة `validate_required_fields()`**: إزالة `"business_license_number"` من قائمة الحقول المطلوبة
- **دالة `validate_business_license_format()`**: 
  - تحديث التوثيق ليوضح أن الحقل اختياري
  - إضافة تنظيف للمسافات والتنسيق
  - تحديث رسالة الخطأ لتوضح "if provided"
- **دالة `generate_verification_hash()`**: تعديل للتعامل مع `business_license_number` الاختياري باستخدام `or ""`

### 3. ملف الاختبارات
**الملف**: `apps/universal_workshop/universal_workshop/license_management/test_business_binding.py`

#### التغييرات:
- **إضافة اختبار جديد**: `test_business_registration_without_license()` للتحقق من إمكانية إنشاء تسجيل أعمال بدون رقم سجل تجاري أو بريد إلكتروني

### 4. سكريبت توليد التراخيص
**الملف**: `scripts/client_deployment/generate_license.sh`

#### التغييرات:
- **إضافة ملاحظة**: في التعليقات توضح أن رقم السجل التجاري والبريد الإلكتروني أصبحا اختياريين
- **تحديث رسالة المساعدة**: إضافة قسمين منفصلين للمتطلبات الإجبارية والاختيارية

## المتطلبات الجديدة لتوليد المفتاح

### 🔸 المتطلبات الإجبارية
1. **اسم الورشة** (عربي + إنجليزي)
2. **اسم المالك** (عربي + إنجليزي)  
3. **رقم الهوية المدنية** (8 أرقام)
4. **رقم الهاتف** (+968 xxxxxxxx)
5. **تاريخ التسجيل**
6. **نوع النشاط التجاري**

### 🔸 المتطلبات الاختيارية
1. **رقم السجل التجاري** (7 أرقام إذا تم توفيره)
2. **البريد الإلكتروني**
3. **العنوان** (عربي + إنجليزي)
4. **المحافظة**
5. **معلومات إضافية**

## الخطوات التالية

### للتطبيق:
1. تشغيل `bench --site universal.local migrate` لتطبيق التغييرات على قاعدة البيانات
2. إعادة تشغيل النظام `bench restart`
3. اختبار إنشاء تسجيل أعمال جديد بدون رقم سجل تجاري

### للتحقق:
1. فتح نموذج Business Registration في الواجهة
2. التأكد من عدم وجود علامة * (مطلوب) بجانب رقم السجل التجاري والبريد الإلكتروني
3. اختبار حفظ تسجيل بدون هذين الحقلين

## ملاحظات مهمة

- **التوافق مع الإصدارات السابقة**: التغييرات متوافقة مع البيانات الموجودة
- **التحقق من الصحة**: لا يزال يتم التحقق من تنسيق رقم السجل التجاري إذا تم توفيره
- **نظام التشفير**: تم تحديث دالة توليد hash للتعامل مع القيم الفارغة
- **الاختبارات**: تمت إضافة اختبارات شاملة للحالات الجديدة

## أمثلة الاستخدام

### مع رقم السجل التجاري
```bash
./generate_license.sh "ورشة النور للسيارات" "ALNOOR001" "professional"
```

### بدون رقم السجل التجاري (الآن مدعوم)
```bash
./generate_license.sh "ورشة النور للسيارات" "ALNOOR001" "professional"
# يمكن ترك حقل business_license_number فارغاً في النموذج
``` 