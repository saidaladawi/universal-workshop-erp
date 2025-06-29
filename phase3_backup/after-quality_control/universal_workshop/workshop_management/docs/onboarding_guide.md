# دليل إعداد ورشة العمل - Universal Workshop ERP
# Workshop Onboarding Guide - Universal Workshop ERP

## نظرة عامة / Overview

يوفر Universal Workshop ERP نظام إعداد شامل ومتقدم للورش الأوتوماتيكية في سلطنة عُمان. يدعم النظام اللغة العربية كلغة أساسية مع دعم كامل للإنجليزية.

Universal Workshop ERP provides a comprehensive and advanced onboarding system for automotive workshops in the Sultanate of Oman. The system supports Arabic as the primary language with full English support.

## المتطلبات المسبقة / Prerequisites

### التقنية / Technical
- ERPNext v15.65.2 أو أحدث / or newer
- Python 3.11+
- MariaDB 10.6+
- Node.js 18+
- Redis 6+

### التشغيلية / Operational
- رخصة تجارية صالحة في عُمان (7 أرقام) / Valid Oman business license (7 digits)
- رقم ضريبة القيمة المضافة (اختياري) / VAT number (optional): OM + 15 digits
- رقم هاتف عُماني / Oman phone number: +968 + 8 digits
- عنوان بريد إلكتروني صالح / Valid email address

## بدء عملية الإعداد / Starting the Onboarding Process

### 1. الوصول إلى النظام / System Access

```url
https://your-domain.com/workshop-onboarding
```

أو من خلال لوحة التحكم / Or through the desk:
- انتقل إلى "ورشة العمل" / Navigate to "Workshop Management"
- اختر "إعداد ورشة جديدة" / Select "New Workshop Setup"

### 2. اختيار اللغة / Language Selection

سيتم اكتشاف لغة المتصفح تلقائياً. يمكنك التبديل بين العربية والإنجليزية في أي وقت.

Browser language will be detected automatically. You can switch between Arabic and English at any time.

## خطوات الإعداد / Setup Steps

### الخطوة 1: المعلومات الأساسية / Step 1: Basic Information

**المطلوب / Required:**
- اسم الورشة (عربي) / Workshop Name (Arabic) ✓
- اسم الورشة (إنجليزي) / Workshop Name (English) ✓
- رقم الرخصة التجارية / Business License Number ✓
- رقم ضريبة القيمة المضافة (اختياري) / VAT Number (optional)

**التحقق / Validation:**
- رقم الرخصة: 7 أرقام بالضبط / License: exactly 7 digits
- رقم الضريبة: OM متبوعة بـ 15 رقم / VAT: OM followed by 15 digits
- النصوص العربية: التحقق من وجود أحرف عربية / Arabic text: validation of Arabic characters

### الخطوة 2: معلومات العمل / Step 2: Business Information

**المطلوب / Required:**
- اسم الشخص المسؤول (عربي/إنجليزي) / Contact Person (Arabic/English) ✓
- المنصب أو الصفة / Position/Title
- نوع الورشة / Workshop Type
- سنة التأسيس / Establishment Year

### الخطوة 3: معلومات الاتصال / Step 3: Contact Information

**المطلوب / Required:**
- البريد الإلكتروني / Email Address ✓
- رقم الهاتف / Phone Number ✓
- العنوان (عربي/إنجليزي) / Address (Arabic/English) ✓
- المدينة والولاية / City and Governorate ✓

**تنسيق رقم الهاتف / Phone Format:**
```
+968 XXXXXXXX
```

### الخطوة 4: التفاصيل التشغيلية / Step 4: Operational Details

**المطلوب / Required:**
- ساعات العمل / Working Hours ✓
- أيام الإجازة / Weekend Days ✓
- الخدمات المقدمة / Services Offered ✓
- عدد الفنيين / Number of Technicians

**ساعات العمل الافتراضية في عُمان / Default Oman Working Hours:**
- الأحد - الخميس: 8:00 صباحاً - 6:00 مساءً / Sunday - Thursday: 8:00 AM - 6:00 PM
- الجمعة والسبت: إجازة / Friday - Saturday: Weekend

### الخطوة 5: المعلومات المالية / Step 5: Financial Information

**المطلوب / Required:**
- اسم البنك / Bank Name ✓
- رقم الآيبان / IBAN Number ✓
- رأس المال الأولي / Initial Capital ✓
- العملة / Currency (OMR - ريال عُماني)

**تنسيق الآيبان العُماني / Oman IBAN Format:**
```
OM## #### ################ (23 digits after OM)
```

## الميزات المتقدمة / Advanced Features

### 1. الحفظ التلقائي / Auto-Save

يتم حفظ البيانات تلقائياً كل 30 ثانية. يمكنك إغلاق النافذة والعودة لاحقاً لإكمال الإعداد.

Data is automatically saved every 30 seconds. You can close the window and return later to complete the setup.

### 2. التحقق المباشر / Real-time Validation

- التحقق من صحة البيانات أثناء الكتابة / Validation while typing
- رسائل خطأ واضحة بالعربية والإنجليزية / Clear error messages in Arabic and English
- إرشادات مساعدة لكل حقل / Help guidance for each field

### 3. التصميم المتجاوب / Responsive Design

- يعمل على جميع الأجهزة / Works on all devices
- دعم كامل للمس / Full touch support
- تخطيط متكيف للشاشات الصغيرة / Adaptive layout for small screens

### 4. دعم RTL / RTL Support

- اتجاه نص من اليمين لليسار للعربية / Right-to-left text direction for Arabic
- تخطيط واجهة متكيف / Adaptive interface layout
- خطوط عربية محسنة / Optimized Arabic fonts

## استكشاف الأخطاء / Troubleshooting

### مشاكل شائعة / Common Issues

#### 1. خطأ في رقم الرخصة التجارية / Business License Error
```
خطأ: رقم الرخصة التجارية يجب أن يكون 7 أرقام
Error: Business license must be 7 digits
```
**الحل / Solution:** تأكد من إدخال 7 أرقام بالضبط بدون مسافات أو أحرف / Ensure exactly 7 digits without spaces or letters

#### 2. خطأ في رقم الهاتف / Phone Number Error
```
خطأ: تنسيق رقم الهاتف العُماني غير صحيح
Error: Invalid Oman phone format
```
**الحل / Solution:** استخدم التنسيق +968 XXXXXXXX / Use format +968 XXXXXXXX

#### 3. خطأ في النص العربي / Arabic Text Error
```
خطأ: يجب أن يحتوي الحقل العربي على أحرف عربية
Error: Arabic field must contain Arabic characters
```
**الحل / Solution:** تأكد من استخدام الأحرف العربية في الحقول المطلوبة / Ensure Arabic characters in required Arabic fields

### رسائل الحالة / Status Messages

#### نجح / Success
```
✅ تم حفظ البيانات بنجاح
✅ Data saved successfully
```

#### تحذير / Warning
```
⚠️ يرجى ملء جميع الحقول المطلوبة
⚠️ Please fill all required fields
```

#### خطأ / Error
```
❌ حدث خطأ في الخادم. يرجى المحاولة مرة أخرى
❌ Server error occurred. Please try again
```

## الأمان وحماية البيانات / Security and Data Protection

### 1. تشفير البيانات / Data Encryption
- جميع البيانات المرسلة مشفرة بـ HTTPS / All data transmitted via HTTPS
- كلمات المرور مشفرة بـ bcrypt / Passwords encrypted with bcrypt
- رموز الجلسة آمنة / Secure session tokens

### 2. حماية CSRF / CSRF Protection
- رموز CSRF لجميع النماذج / CSRF tokens for all forms
- التحقق من المنشأ / Origin verification
- انتهاء صلاحية الجلسة / Session expiration

### 3. سياسة الخصوصية / Privacy Policy
- البيانات محفوظة محلياً في عُمان / Data stored locally in Oman
- عدم مشاركة البيانات مع أطراف ثالثة / No third-party data sharing
- إمكانية حذف البيانات / Data deletion capability

## الدعم الفني / Technical Support

### معلومات الاتصال / Contact Information
- البريد الإلكتروني / Email: support@universal-workshop.om
- الهاتف / Phone: +968 24 123456
- ساعات الدعم / Support Hours: الأحد - الخميس 8:00 - 18:00 / Sunday - Thursday 8:00 - 18:00

### الموارد الإضافية / Additional Resources
- [دليل المستخدم الكامل / Complete User Guide](docs/user-guide.md)
- [الأسئلة الشائعة / FAQ](docs/faq.md)
- [تحديثات النظام / System Updates](docs/updates.md)

## متطلبات الأداء / Performance Requirements

### أهداف الأداء / Performance Targets
- إكمال الإعداد: أقل من 30 دقيقة / Setup completion: under 30 minutes
- استجابة الصفحة: أقل من 3 ثوانِ / Page response: under 3 seconds
- حفظ البيانات: أقل من 2 ثانية / Data saving: under 2 seconds

### اختبار الأداء / Performance Testing
- يتم قياس الأداء تلقائياً / Performance measured automatically
- تقارير الأداء متاحة للإدارة / Performance reports available to management
- تحسينات مستمرة بناءً على البيانات / Continuous improvements based on data

---

**إشعار هام / Important Notice:**
هذا النظام مصمم خصيصاً للورش الأوتوماتيكية في سلطنة عُمان ويتوافق مع القوانين والأنظمة المحلية.

This system is specifically designed for automotive workshops in the Sultanate of Oman and complies with local laws and regulations.

**الإصدار / Version:** 2.0
**تاريخ التحديث / Last Updated:** June 18, 2024
**المطور / Developer:** Eng. Said Al-Adawi 