# API Documentation | توثيق واجهة برمجة التطبيقات

## 🔌 Universal Workshop ERP API Reference

Complete API documentation for Universal Workshop ERP with Arabic language support and Oman-specific business requirements.

توثيق كامل لواجهة برمجة التطبيقات لنظام إدارة الورش الشامل مع دعم اللغة العربية ومتطلبات الأعمال الخاصة بعُمان.

## 📋 Table of Contents | جدول المحتويات

1. [Authentication | المصادقة](#authentication)
2. [Error Handling | معالجة الأخطاء](#error-handling)
3. [Customer Management API | واجهة إدارة العملاء](#customer-management-api)
4. [Vehicle Registry API | واجهة سجل المركبات](#vehicle-registry-api)
5. [Service Order API | واجهة أوامر الخدمة](#service-order-api)
6. [Inventory Management API | واجهة إدارة المخزون](#inventory-management-api)
7. [Invoicing & VAT API | واجهة الفواتير وضريبة القيمة المضافة](#invoicing-vat-api)
8. [Reports API | واجهة التقارير](#reports-api)
9. [Arabic Utilities API | واجهة الأدوات العربية](#arabic-utilities-api)

## 🔐 Authentication | المصادقة

### API Key Authentication | مصادقة مفتاح واجهة برمجة التطبيقات

```http
# All API requests require authentication
# جميع طلبات واجهة برمجة التطبيقات تتطلب مصادقة

POST /api/method/login
Content-Type: application/json

{
    "usr": "user@example.com",
    "pwd": "password"
}

# Response
{
    "message": "Logged In",
    "home_page": "/desk",
    "full_name": "محمد أحمد الكندي"
}
```

### Token-based Authentication | المصادقة القائمة على الرموز

```http
# Generate API token
# توليد رمز واجهة برمجة التطبيقات

GET /api/method/frappe.auth.get_logged_user
Authorization: token api_key:api_secret

# Use token in subsequent requests
# استخدام الرمز في الطلبات اللاحقة

GET /api/resource/Customer
Authorization: token your_api_key:your_api_secret
```

## ❌ Error Handling | معالجة الأخطاء

### Standard Error Response | استجابة الخطأ القياسية

```json
{
    "exc_type": "ValidationError",
    "exception": "رقم الهاتف المحمول مطلوب",
    "exception_en": "Mobile number is required",
    "message": "خطأ في التحقق من صحة البيانات",
    "message_en": "Data validation error",
    "indicator": "red"
}
```

### Common HTTP Status Codes | رموز حالة HTTP الشائعة

| Code | Status | Arabic | Description |
|------|--------|--------|-------------|
| 200 | OK | نجح | Request successful |
| 201 | Created | تم الإنشاء | Resource created |
| 400 | Bad Request | طلب خاطئ | Invalid request data |
| 401 | Unauthorized | غير مخول | Authentication required |
| 403 | Forbidden | محظور | Insufficient permissions |
| 404 | Not Found | غير موجود | Resource not found |
| 422 | Validation Error | خطأ في التحقق | Data validation failed |
| 500 | Server Error | خطأ في الخادم | Internal server error |

## 👥 Customer Management API

### Create Customer | إنشاء عميل

```http
POST /api/resource/Customer
Content-Type: application/json

{
    "customer_name": "محمد أحمد الكندي",
    "customer_name_en": "Mohammed Ahmed Al-Kindi",
    "customer_type": "Individual",
    "mobile_no": "+968 9123 4567",
    "email_id": "mohammed@example.com",
    "territory": "Muscat",
    "customer_group": "Commercial",
    "language": "ar",
    "address_line1": "شارع السلام، الخوير",
    "address_line1_en": "Al-Salam Street, Al-Khuwair",
    "city": "مسقط",
    "country": "Oman",
    "custom_national_id": "12345678"
}
```

**Response:**
```json
{
    "data": {
        "name": "CUST-2025-00001",
        "customer_name": "محمد أحمد الكندي",
        "customer_name_en": "Mohammed Ahmed Al-Kindi",
        "creation": "2025-06-21 10:30:00",
        "modified": "2025-06-21 10:30:00"
    }
}
```

### Get Customer List | الحصول على قائمة العملاء

```http
GET /api/resource/Customer?fields=["name","customer_name","mobile_no","territory"]&limit_page_length=20

# Search by Arabic name
# البحث بالاسم العربي
GET /api/resource/Customer?filters=[["customer_name","like","%محمد%"]]

# Filter by territory
# التصفية حسب المنطقة  
GET /api/resource/Customer?filters=[["territory","=","Muscat"]]
```

### Update Customer | تحديث العميل

```http
PUT /api/resource/Customer/CUST-2025-00001
Content-Type: application/json

{
    "mobile_no": "+968 9987 6543",
    "email_id": "mohammed.new@example.com"
}
```

## 🚙 Vehicle Registry API

### Register Vehicle | تسجيل مركبة

```http
POST /api/resource/Vehicle
Content-Type: application/json

{
    "license_plate": "أ ب ج 1234", 
    "license_plate_en": "A B C 1234",
    "vin_number": "WVWZZZ1JZ3W386752",
    "customer": "CUST-2025-00001",
    "make": "تويوتا",
    "make_en": "Toyota", 
    "model": "كامري",
    "model_en": "Camry",
    "year": 2023,
    "color": "أبيض",
    "color_en": "White",
    "engine_type": "بنزين",
    "engine_type_en": "Gasoline",
    "engine_capacity": "2.5L",
    "transmission": "أوتوماتيك",
    "transmission_en": "Automatic",
    "fuel_type": "بنزين 95",
    "mileage": 15000
}
```

### VIN Decoder | مفكك رقم الهيكل

```http
POST /api/method/universal_workshop.api.decode_vin
Content-Type: application/json

{
    "vin": "WVWZZZ1JZ3W386752"
}
```

**Response:**
```json
{
    "message": {
        "manufacturer": "Volkswagen",
        "manufacturer_ar": "فولكس فاجن",
        "year": 2023,
        "country": "Germany", 
        "country_ar": "ألمانيا",
        "engine_type": "Gasoline",
        "engine_type_ar": "بنزين",
        "body_style": "Sedan",
        "body_style_ar": "سيدان"
    }
}
```

### Get Vehicle Service History | الحصول على تاريخ خدمة المركبة

```http
GET /api/method/universal_workshop.api.get_vehicle_history?vehicle=VEH-2025-00001
```

## 🔧 Service Order API

### Create Service Order | إنشاء أمر خدمة

```http
POST /api/resource/Service Order
Content-Type: application/json

{
    "customer": "CUST-2025-00001",
    "vehicle": "VEH-2025-00001", 
    "service_date": "2025-06-21",
    "estimated_completion": "2025-06-21 17:00:00",
    "status": "Draft",
    "priority": "Medium",
    "complaint": "صوت غريب من المحرك",
    "complaint_en": "Strange noise from engine",
    "service_advisor": "احمد محمد",
    "technician": "سالم علي",
    "services": [
        {
            "service_name": "تغيير زيت المحرك",
            "service_name_en": "Engine Oil Change",
            "description": "تغيير زيت المحرك مع الفلتر",
            "quantity": 1,
            "rate": 25.000,
            "amount": 25.000
        },
        {
            "service_name": "فحص الفرامل",
            "service_name_en": "Brake Inspection", 
            "description": "فحص شامل لنظام الفرامل",
            "quantity": 1,
            "rate": 15.000,
            "amount": 15.000
        }
    ],
    "parts": [
        {
            "item_code": "OIL-5W30-5L",
            "item_name": "زيت محرك 5W-30",
            "quantity": 5,
            "rate": 8.000,
            "amount": 40.000
        }
    ]
}
```

### Update Service Status | تحديث حالة الخدمة

```http
PUT /api/resource/Service Order/SRV-2025-00001
Content-Type: application/json

{
    "status": "Work In Progress",
    "actual_start_time": "2025-06-21 09:00:00",
    "technician_notes": "تم البدء في تغيير الزيت",
    "technician_notes_en": "Started oil change procedure"
}
```

### Service Order Workflow | سير عمل أمر الخدمة

```http
# Submit service order
# تقديم أمر الخدمة
POST /api/method/frappe.model.workflow.apply_workflow
{
    "doc": "Service Order",
    "docname": "SRV-2025-00001",
    "action": "Submit"
}

# Complete service  
# إكمال الخدمة
POST /api/method/frappe.model.workflow.apply_workflow
{
    "doc": "Service Order", 
    "docname": "SRV-2025-00001",
    "action": "Complete"
}
```

## 📦 Inventory Management API

### Create Item | إنشاء صنف

```http
POST /api/resource/Item
Content-Type: application/json

{
    "item_code": "BP-12V-70AH",
    "item_name": "بطارية سيارة 12 فولت 70 أمبير",
    "item_name_en": "Car Battery 12V 70AH",
    "item_group": "قطع غيار",
    "item_group_en": "Spare Parts",
    "description": "بطارية سيارة عالية الجودة",
    "description_en": "High quality car battery",
    "is_sales_item": 1,
    "is_purchase_item": 1,
    "is_stock_item": 1,
    "stock_uom": "عدد",
    "purchase_uom": "عدد",
    "sales_uom": "عدد",
    "valuation_rate": 45.000,
    "standard_rate": 65.000,
    "item_defaults": [
        {
            "company": "Universal Workshop",
            "default_warehouse": "المخزن الرئيسي - UW"
        }
    ]
}
```

### Stock Management | إدارة المخزون

```http
# Stock Entry
POST /api/resource/Stock Entry
{
    "stock_entry_type": "Material Receipt",
    "purpose": "Material Receipt", 
    "posting_date": "2025-06-21",
    "items": [
        {
            "item_code": "BP-12V-70AH",
            "qty": 10,
            "basic_rate": 45.000,
            "t_warehouse": "المخزن الرئيسي - UW"
        }
    ]
}

# Check stock balance
# فحص رصيد المخزون  
GET /api/method/erpnext.stock.utils.get_stock_balance?item_code=BP-12V-70AH&warehouse=المخزن الرئيسي - UW
```

### Barcode Scanning | مسح الباركود

```http
POST /api/method/universal_workshop.api.scan_barcode
{
    "barcode": "123456789012",
    "warehouse": "المخزن الرئيسي - UW"
}
```

## 💰 Invoicing & VAT API

### Create Sales Invoice | إنشاء فاتورة مبيعات

```http
POST /api/resource/Sales Invoice
Content-Type: application/json

{
    "customer": "CUST-2025-00001",
    "posting_date": "2025-06-21",
    "due_date": "2025-06-21",
    "currency": "OMR",
    "language": "ar",
    "items": [
        {
            "item_code": "SRV-OIL-CHANGE",
            "item_name": "تغيير زيت المحرك", 
            "description": "تغيير زيت المحرك مع الفلتر",
            "qty": 1,
            "rate": 25.000,
            "amount": 25.000
        },
        {
            "item_code": "BP-12V-70AH",
            "item_name": "بطارية سيارة 12 فولت",
            "qty": 1, 
            "rate": 65.000,
            "amount": 65.000
        }
    ],
    "taxes_and_charges": "ضريبة القيمة المضافة - عُمان",
    "taxes": [
        {
            "charge_type": "On Net Total",
            "account_head": "ضريبة القيمة المضافة - UW",
            "description": "ضريبة القيمة المضافة @ 5%",
            "rate": 5,
            "tax_amount": 4.500
        }
    ]
}
```

### Oman VAT Calculation | حساب ضريبة القيمة المضافة العُمانية

```http
POST /api/method/universal_workshop.api.calculate_oman_vat
{
    "net_amount": 90.000,
    "vat_rate": 0.05
}
```

**Response:**
```json
{
    "message": {
        "net_amount": 90.000,
        "vat_amount": 4.500, 
        "total_amount": 94.500,
        "vat_rate": 5,
        "currency": "OMR",
        "in_words": "أربعة وتسعون ريالاً عُمانياً وخمسمائة بيسة",
        "in_words_en": "Ninety Four Omani Rials and Five Hundred Baisa"
    }
}
```

### QR Code Generation | توليد رمز QR

```http
POST /api/method/universal_workshop.api.generate_invoice_qr
{
    "invoice_number": "INV-2025-00001",
    "company_vat_number": "OM123456789",
    "invoice_date": "2025-06-21",
    "total_amount": 94.500,
    "vat_amount": 4.500
}
```

## 📊 Reports API

### Sales Report | تقرير المبيعات

```http
POST /api/method/frappe.desk.query_report.run
{
    "report_name": "تقرير المبيعات اليومي",
    "filters": {
        "from_date": "2025-06-01",
        "to_date": "2025-06-21", 
        "customer": "",
        "territory": "Muscat"
    }
}
```

### Customer Analysis | تحليل العملاء

```http
GET /api/method/universal_workshop.reports.customer_analysis
?from_date=2025-06-01&to_date=2025-06-21&territory=Muscat
```

**Response:**
```json
{
    "message": {
        "total_customers": 156,
        "new_customers": 23,
        "returning_customers": 133,
        "top_customers": [
            {
                "name": "CUST-2025-00001",
                "customer_name": "محمد أحمد الكندي",
                "total_revenue": 450.750,
                "visit_count": 5
            }
        ],
        "customer_satisfaction": {
            "average_rating": 4.7,
            "total_reviews": 89,
            "positive_reviews": 81
        }
    }
}
```

### Service Performance | أداء الخدمات

```http
GET /api/method/universal_workshop.reports.service_performance
?period=monthly&year=2025&month=6
```

## 🌍 Arabic Utilities API

### Text Processing | معالجة النص

```http
POST /api/method/universal_workshop.api.process_arabic_text
{
    "text": "مُحَمَّد أَحْمَد الكِنْدِي",
    "remove_diacritics": true,
    "normalize_hamza": true
}
```

**Response:**
```json
{
    "message": {
        "original_text": "مُحَمَّد أَحْمَد الكِنْدِي",
        "processed_text": "محمد احمد الكندي", 
        "search_keywords": ["محمد", "احمد", "الكندي"],
        "character_count": 17,
        "word_count": 3
    }
}
```

### Arabic Search | البحث العربي

```http
POST /api/method/universal_workshop.api.arabic_search
{
    "query": "محمد",
    "doctype": "Customer",
    "fields": ["customer_name", "customer_name_en"],
    "limit": 20
}
```

### Number to Words (Arabic) | تحويل الأرقام إلى كلمات

```http
POST /api/method/universal_workshop.api.number_to_words_arabic
{
    "number": 94.500,
    "currency": "OMR"
}
```

**Response:**
```json
{
    "message": {
        "number": 94.500,
        "in_words_ar": "أربعة وتسعون ريالاً عُمانياً وخمسمائة بيسة",
        "in_words_en": "Ninety Four Omani Rials and Five Hundred Baisa",
        "currency": "OMR"
    }
}
```

## 📱 Mobile API | واجهة الهاتف المحمول

### PWA Configuration | إعداد تطبيق الويب التقدمي

```http
GET /api/method/universal_workshop.api.get_pwa_config
```

**Response:**
```json
{
    "message": {
        "app_name": "نظام إدارة الورش الشامل",
        "app_name_en": "Universal Workshop ERP",
        "theme_color": "#1f4e79", 
        "background_color": "#ffffff",
        "display": "standalone",
        "orientation": "any",
        "lang": "ar",
        "dir": "rtl",
        "icons": [
            {
                "src": "/assets/universal_workshop/images/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            }
        ]
    }
}
```

### Offline Sync | المزامنة بدون اتصال

```http
POST /api/method/universal_workshop.api.sync_offline_data
{
    "data": {
        "service_orders": [...],
        "customers": [...],
        "items": [...]
    },
    "last_sync": "2025-06-21 08:00:00"
}
```

---

## 🔄 Webhooks | خطافات الويب

### Service Order Events | أحداث أوامر الخدمة

```python
# Webhook configuration
{
    "webhook_doctype": "Service Order",
    "webhook_docevent": "on_update", 
    "request_url": "https://your-app.com/webhooks/service-order",
    "request_structure": "Form URL-Encoded",
    "condition": "doc.status == 'Completed'",
    "webhook_headers": [
        {
            "key": "Authorization",
            "value": "Bearer your-token"
        }
    ]
}
```

### Webhook Payload Example | مثال على حمولة خطاف الويب

```json
{
    "doctype": "Service Order",
    "name": "SRV-2025-00001",
    "customer": "CUST-2025-00001",
    "customer_name": "محمد أحمد الكندي",
    "vehicle": "VEH-2025-00001",
    "status": "Completed",
    "total_amount": 94.500,
    "completion_date": "2025-06-21 16:30:00"
}
```

---

## 📚 SDK Examples | أمثلة حزمة تطوير البرامج

### Python SDK | حزمة تطوير Python

```python
import requests
from datetime import datetime

class UniversalWorkshopAPI:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.auth = (api_key, api_secret)
    
    def create_customer(self, customer_data):
        """Create new customer with Arabic support"""
        url = f"{self.base_url}/api/resource/Customer"
        response = requests.post(url, json=customer_data, auth=self.auth)
        return response.json()
    
    def search_customers_arabic(self, query):
        """Search customers by Arabic name"""
        url = f"{self.base_url}/api/resource/Customer"
        filters = [["customer_name", "like", f"%{query}%"]]
        params = {"filters": str(filters)}
        response = requests.get(url, params=params, auth=self.auth)
        return response.json()

# Usage example
api = UniversalWorkshopAPI(
    "https://workshop.example.com",
    "your_api_key", 
    "your_api_secret"
)

# Create customer
customer = api.create_customer({
    "customer_name": "سالم أحمد المعمري",
    "mobile_no": "+968 9876 5432"
})

# Search customers
results = api.search_customers_arabic("سالم")
```

### JavaScript SDK | حزمة تطوير JavaScript

```javascript
class UniversalWorkshopAPI {
    constructor(baseUrl, apiKey, apiSecret) {
        this.baseUrl = baseUrl;
        this.auth = btoa(`${apiKey}:${apiSecret}`);
    }
    
    async createServiceOrder(orderData) {
        const response = await fetch(`${this.baseUrl}/api/resource/Service Order`, {
            method: 'POST',
            headers: {
                'Authorization': `Basic ${this.auth}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(orderData)
        });
        return response.json();
    }
    
    async getArabicCustomers(query) {
        const filters = [["customer_name", "like", `%${query}%`]];
        const url = `${this.baseUrl}/api/resource/Customer?filters=${encodeURIComponent(JSON.stringify(filters))}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Basic ${this.auth}`
            }
        });
        return response.json();
    }
}

// Usage
const api = new UniversalWorkshopAPI(
    'https://workshop.example.com',
    'your_api_key',
    'your_api_secret'
);

// Create service order
api.createServiceOrder({
    customer: 'CUST-2025-00001',
    services: [
        {
            service_name: 'تغيير زيت المحرك',
            amount: 25.000
        }
    ]
}).then(result => console.log(result));
```

---

*API documentation is updated regularly. For the latest endpoints and features, please refer to the live API documentation at your instance.*

*توثيق واجهة برمجة التطبيقات محدث بانتظام. للحصول على أحدث نقاط الاتصال والميزات، يرجى الرجوع إلى توثيق واجهة برمجة التطبيقات المباشر في مثيلك.*
