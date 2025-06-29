# Universal Workshop ERP - User Guide

## مرحباً بكم في نظام إدارة الورش الشامل
## Welcome to Universal Workshop ERP

This guide will help you get started with Universal Workshop ERP, designed specifically for automotive workshops in Oman with complete Arabic language support.

---

## Table of Contents / جدول المحتويات

1. [Getting Started / البدء](#getting-started--البدء)
2. [Workshop Profile Setup / إعداد ملف الورشة](#workshop-profile-setup--إعداد-ملف-الورشة)
3. [Customer Management / إدارة العملاء](#customer-management--إدارة-العملاء)
4. [Vehicle Registration / تسجيل المركبات](#vehicle-registration--تسجيل-المركبات)
5. [Service Orders / أوامر الخدمة](#service-orders--أوامر-الخدمة)
6. [Daily Operations / العمليات اليومية](#daily-operations--العمليات-اليومية)
7. [Reports and Analytics / التقارير والتحليلات](#reports-and-analytics--التقارير-والتحليلات)
8. [Troubleshooting / حل المشاكل](#troubleshooting--حل-المشاكل)

---

## Getting Started / البدء

### System Requirements / متطلبات النظام

- **Internet Connection**: Stable internet for cloud access
- **Browser**: Chrome, Firefox, Safari, or Edge (latest versions)
- **Language**: Arabic and English support
- **Mobile**: Responsive design for tablets and smartphones

### First Login / تسجيل الدخول الأول

1. **Access the System / الوصول للنظام**
   - Open your web browser
   - Navigate to your workshop's ERP URL
   - Enter your username and password

2. **Language Selection / اختيار اللغة**
   - Click on language selector (top right)
   - Choose Arabic (العربية) or English
   - System will remember your preference

3. **Dashboard Overview / نظرة عامة على لوحة التحكم**
   - View daily statistics
   - Check pending service orders
   - Monitor workshop performance

---

## Workshop Profile Setup / إعداد ملف الورشة

### Initial Setup / الإعداد الأولي

#### Step 1: Basic Information / الخطوة الأولى: المعلومات الأساسية

1. **Navigate to Workshop Profile**
   - Go to: Setup → Workshop Profile
   - Click "New Workshop Profile"

2. **Enter Workshop Details / أدخل تفاصيل الورشة**
   - **Workshop Name (English)**: Enter your workshop name
   - **اسم الورشة (العربية)**: أدخل اسم الورشة بالعربية
   - **Workshop Code**: Auto-generated (WS-2024-0001)
   - **Status**: Set to "Active"

#### Step 2: Business Compliance / الخطوة الثانية: الامتثال التجاري

**Important for Oman Workshops / مهم للورش العمانية**

1. **Business License / الرخصة التجارية**
   - Enter 7-digit business license number
   - Example: 1234567
   - System validates Oman format automatically

2. **VAT Registration / تسجيل ضريبة القيمة المضافة**
   - Enter VAT number (if applicable)
   - Format: OMxxxxxxxxxxxxxxx
   - 5% VAT rate automatically applied

3. **Commercial Registration / السجل التجاري**
   - Enter commercial registration number
   - Municipality license number
   - Ministry approval reference

#### Step 3: Contact Information / الخطوة الثالثة: معلومات الاتصال

1. **Owner Details / تفاصيل المالك**
   - **Owner Name**: Enter in English
   - **اسم المالك**: أدخل بالعربية
   - **Phone**: +968 format (e.g., +968 24123456)
   - **Email**: Business email address

2. **Workshop Address / عنوان الورشة**
   - **Address**: Enter in English
   - **العنوان**: أدخل بالعربية
   - **Governorate**: Select from Oman governorates
   - **City**: Enter city name
   - **Postal Code**: Enter postal code

#### Step 4: Operational Settings / الخطوة الرابعة: الإعدادات التشغيلية

1. **Workshop Capacity / سعة الورشة**
   - **Daily Vehicle Capacity**: Number of vehicles per day
   - **Service Bays**: Number of service bays
   - **Workshop Type**: Select specialization

2. **Working Hours / ساعات العمل**
   - **Start Time**: Opening time (e.g., 08:00)
   - **End Time**: Closing time (e.g., 18:00)
   - **Working Days**: Sunday-Thursday (Oman standard)

3. **Financial Settings / الإعدادات المالية**
   - **Default Currency**: OMR (Omani Rial)
   - **VAT Rate**: 5.0% (Oman standard)
   - **Payment Terms**: Set default payment terms

---

## Customer Management / إدارة العملاء

### Adding New Customers / إضافة عملاء جدد

#### Quick Customer Registration / التسجيل السريع للعملاء

1. **Navigate to Customers**
   - Go to: Customers → Customer List
   - Click "New Customer"

2. **Customer Information / معلومات العميل**
   - **Customer Name**: Enter in English
   - **اسم العميل**: أدخل بالعربية (Required)
   - **Phone**: +968 format
   - **Email**: Customer email (optional)

3. **Address Details / تفاصيل العنوان**
   - **Address**: Enter in English
   - **العنوان**: أدخل بالعربية
   - **City**: Customer's city
   - **Governorate**: Select governorate

#### Customer Types / أنواع العملاء

- **Individual / فردي**: Personal customers
- **Company / شركة**: Corporate customers
- **Government / حكومي**: Government entities

### Customer Search / البحث عن العملاء

1. **Search Methods / طرق البحث**
   - By name (Arabic or English)
   - By phone number
   - By customer code
   - By vehicle license plate

2. **Advanced Filters / المرشحات المتقدمة**
   - Customer type
   - Registration date
   - Last service date
   - Outstanding balance

---

## Vehicle Registration / تسجيل المركبات

### Adding Vehicles / إضافة المركبات

#### Step 1: Vehicle Identification / الخطوة الأولى: تحديد هوية المركبة

1. **VIN Entry / إدخال رقم الهيكل**
   - **VIN Number**: Enter 17-character VIN
   - System automatically decodes vehicle information
   - Response time: Under 5 seconds

2. **License Plate / لوحة الترخيص**
   - **License Plate**: Enter in English
   - **لوحة الترخيص**: أدخل بالعربية
   - **Registration Date**: Vehicle registration date

#### Step 2: Vehicle Specifications / الخطوة الثانية: مواصفات المركبة

**Auto-populated from VIN (if available) / يتم ملؤها تلقائياً من رقم الهيكل**

1. **Basic Specifications / المواصفات الأساسية**
   - **Make**: Vehicle manufacturer
   - **الصانع**: اسم الصانع بالعربية
   - **Model**: Vehicle model
   - **الطراز**: طراز المركبة بالعربية
   - **Year**: Manufacturing year
   - **Color**: Vehicle color
   - **اللون**: لون المركبة بالعربية

2. **Technical Details / التفاصيل التقنية**
   - **Engine Type**: Engine specification
   - **Transmission**: Manual/Automatic/CVT
   - **Fuel Type**: Petrol/Diesel/Hybrid/Electric
   - **Engine Capacity**: Displacement in liters

#### Step 3: Customer Linking / الخطوة الثالثة: ربط العميل

1. **Customer Assignment / تعيين العميل**
   - **Customer**: Link to existing customer (Required)
   - **Purchase Date**: When customer bought the vehicle
   - **Previous Owner**: Previous owner information (if any)

2. **Registration Details / تفاصيل التسجيل**
   - **Registration Number**: Government registration
   - **Registration Expiry**: Expiry date
   - **Current Mileage**: Odometer reading

#### Step 4: Insurance & Warranty / الخطوة الرابعة: التأمين والضمان

1. **Insurance Information / معلومات التأمين**
   - **Insurance Company**: Provider name
   - **Policy Number**: Insurance policy number
   - **Insurance Expiry**: Policy expiry date

2. **Warranty Details / تفاصيل الضمان**
   - **Warranty Status**: Active/Expired/Extended
   - **Warranty Expiry**: Warranty end date

---

## Service Orders / أوامر الخدمة

### Creating Service Orders / إنشاء أوامر الخدمة

#### Step 1: Order Information / الخطوة الأولى: معلومات الطلب

1. **Basic Details / التفاصيل الأساسية**
   - **Customer**: Select customer from list
   - **Vehicle**: Select customer's vehicle
   - **Service Date**: Scheduled service date
   - **Priority**: Low/Medium/High/Urgent

2. **Service Description / وصف الخدمة**
   - **Service Type**: Select from predefined types
   - **نوع الخدمة**: أدخل بالعربية
   - **Description**: Detailed service description
   - **الوصف**: وصف مفصل بالعربية

#### Step 2: Resource Assignment / الخطوة الثانية: تعيين الموارد

1. **Technician Assignment / تعيين الفني**
   - **Assigned Technician**: Primary technician
   - **Supervisor**: Supervising technician
   - **Service Bay**: Assigned work bay

2. **Time Estimation / تقدير الوقت**
   - **Estimated Duration**: Expected hours
   - **Labor Rate**: Hourly rate
   - **Labor Cost**: Automatically calculated

#### Step 3: Parts and Materials / الخطوة الثالثة: القطع والمواد

1. **Parts Required / القطع المطلوبة**
   - Add required parts from inventory
   - Specify quantities
   - System checks availability

2. **Cost Calculation / حساب التكلفة**
   - **Parts Cost**: Total parts cost
   - **Labor Cost**: Total labor cost
   - **Subtotal**: Before VAT
   - **VAT (5%)**: Automatically calculated
   - **Total**: Final amount

### Service Order Workflow / سير عمل أوامر الخدمة

#### Status Progression / تطور الحالة

1. **Draft / مسودة**
   - Initial creation
   - All fields editable
   - No resource commitment

2. **In Progress / قيد التنفيذ**
   - Work started
   - Resources assigned
   - Time tracking active

3. **Completed / مكتمل**
   - Work finished
   - Quality check done
   - Customer approval obtained

4. **Cancelled / ملغى**
   - Order cancelled
   - Resources released

#### Status Updates / تحديثات الحالة

1. **Starting Work / بدء العمل**
   - Change status to "In Progress"
   - Start time automatically recorded
   - Technician notified

2. **Progress Updates / تحديثات التقدم**
   - Add work notes
   - Update actual time spent
   - Record parts used

3. **Completion / الإنجاز**
   - Change status to "Completed"
   - Completion time recorded
   - Generate invoice

---

## Daily Operations / العمليات اليومية

### Morning Checklist / قائمة الصباح

1. **Check Pending Orders / فحص الطلبات المعلقة**
   - Review today's scheduled services
   - Confirm technician assignments
   - Verify parts availability

2. **Workshop Preparation / تحضير الورشة**
   - Check service bay availability
   - Ensure tools and equipment ready
   - Review special instructions

### Service Execution / تنفيذ الخدمات

#### Starting Service / بدء الخدمة

1. **Customer Check-in / تسجيل وصول العميل**
   - Verify customer identity
   - Confirm vehicle details
   - Review service requirements

2. **Vehicle Inspection / فحص المركبة**
   - Record current mileage
   - Note vehicle condition
   - Document any pre-existing issues

#### During Service / أثناء الخدمة

1. **Progress Tracking / تتبع التقدم**
   - Update service status regularly
   - Record actual time spent
   - Document any issues found

2. **Parts Management / إدارة القطع**
   - Record parts used
   - Update inventory
   - Request additional parts if needed

#### Service Completion / إنجاز الخدمة

1. **Quality Check / فحص الجودة**
   - Perform quality inspection
   - Test vehicle functionality
   - Document quality notes

2. **Customer Handover / تسليم العميل**
   - Explain work performed
   - Provide maintenance recommendations
   - Obtain customer signature

### End of Day / نهاية اليوم

1. **Daily Summary / الملخص اليومي**
   - Review completed services
   - Check pending work
   - Update workshop statistics

2. **Preparation for Next Day / التحضير لليوم التالي**
   - Review tomorrow's schedule
   - Prepare required parts
   - Plan resource allocation

---

## Reports and Analytics / التقارير والتحليلات

### Daily Reports / التقارير اليومية

1. **Service Summary / ملخص الخدمات**
   - Services completed today
   - Revenue generated
   - Average service time

2. **Technician Performance / أداء الفنيين**
   - Services per technician
   - Time efficiency
   - Quality ratings

### Weekly Reports / التقارير الأسبوعية

1. **Workshop Performance / أداء الورشة**
   - Total services completed
   - Revenue trends
   - Customer satisfaction

2. **Inventory Analysis / تحليل المخزون**
   - Parts usage
   - Stock levels
   - Reorder requirements

### Monthly Reports / التقارير الشهرية

1. **Financial Summary / الملخص المالي**
   - Total revenue
   - Profit margins
   - VAT calculations

2. **Customer Analytics / تحليل العملاء**
   - New customers acquired
   - Customer retention rate
   - Service frequency

---

## Troubleshooting / حل المشاكل

### Common Issues / المشاكل الشائعة

#### Login Problems / مشاكل تسجيل الدخول

**Problem**: Cannot access the system
**الحل**: 
1. Check internet connection
2. Verify URL is correct
3. Clear browser cache
4. Try different browser
5. Contact system administrator

#### VIN Decoder Issues / مشاكل فك تشفير رقم الهيكل

**Problem**: VIN not recognized
**الحل**:
1. Verify VIN is 17 characters
2. Check for typing errors
3. Use manual entry if decoder fails
4. Contact support for assistance

#### Arabic Text Display / عرض النص العربي

**Problem**: Arabic text appears incorrect
**الحل**:
1. Check browser language settings
2. Ensure Arabic fonts installed
3. Verify UTF-8 encoding
4. Refresh the page

### Performance Issues / مشاكل الأداء

#### Slow Loading / التحميل البطيء

**Problem**: System loads slowly
**الحل**:
1. Check internet speed
2. Close unnecessary browser tabs
3. Clear browser cache
4. Restart browser
5. Contact IT support

#### Form Submission Errors / أخطاء إرسال النماذج

**Problem**: Cannot save data
**الحل**:
1. Check all required fields completed
2. Verify data format (phone, email, etc.)
3. Check internet connection
4. Try again after few minutes
5. Contact support if persistent

### Getting Help / الحصول على المساعدة

#### Support Contacts / جهات الاتصال للدعم

1. **Technical Support / الدعم التقني**
   - Email: support@universal-workshop.om
   - Phone: +968 24 567890
   - Hours: Sunday-Thursday, 8:00-17:00

2. **Training Support / دعم التدريب**
   - Email: training@universal-workshop.om
   - Phone: +968 24 567891
   - Available for on-site training

3. **Emergency Support / الدعم الطارئ**
   - Phone: +968 99 123456
   - Available 24/7 for critical issues

#### Documentation / الوثائق

1. **Online Help / المساعدة الإلكترونية**
   - Access through Help menu
   - Available in Arabic and English
   - Searchable knowledge base

2. **Video Tutorials / دروس الفيديو**
   - Available on company website
   - Step-by-step instructions
   - Arabic and English versions

---

## Best Practices / أفضل الممارسات

### Data Entry / إدخال البيانات

1. **Consistency / الاتساق**
   - Use consistent naming conventions
   - Always fill Arabic fields
   - Verify phone number format

2. **Accuracy / الدقة**
   - Double-check VIN numbers
   - Verify customer information
   - Confirm service details

### System Security / أمان النظام

1. **Password Security / أمان كلمة المرور**
   - Use strong passwords
   - Change passwords regularly
   - Don't share login credentials

2. **Data Protection / حماية البيانات**
   - Log out when finished
   - Don't leave system unattended
   - Report security concerns immediately

### Backup and Recovery / النسخ الاحتياطي والاستعادة

1. **Regular Backups / النسخ الاحتياطية المنتظمة**
   - System automatically backs up daily
   - Critical data backed up hourly
   - Verify backup completion

2. **Data Recovery / استعادة البيانات**
   - Contact support for data recovery
   - Provide specific details of lost data
   - Recovery typically within 24 hours

---

## Appendices / الملاحق

### Appendix A: Keyboard Shortcuts / اختصارات لوحة المفاتيح

- **Ctrl + N**: New record
- **Ctrl + S**: Save record
- **Ctrl + F**: Search
- **Ctrl + P**: Print
- **F1**: Help

### Appendix B: Field Validation Rules / قواعد التحقق من الحقول

- **Business License**: Exactly 7 digits
- **Phone Number**: +968 format
- **VIN**: Exactly 17 characters
- **Email**: Valid email format
- **VAT Number**: OMxxxxxxxxxxxxxxx format

### Appendix C: System Limits / حدود النظام

- **Maximum Users**: Unlimited
- **Storage**: 1TB included
- **Backup Retention**: 1 year
- **API Calls**: 10,000 per hour
- **File Upload**: 10MB per file

---

*For additional support, contact our team at support@universal-workshop.om*  
*للحصول على دعم إضافي، اتصل بفريقنا على support@universal-workshop.om*

**Last Updated**: 2025-06-24  
**Document Version**: 1.0  
**Universal Workshop ERP v2.0** 