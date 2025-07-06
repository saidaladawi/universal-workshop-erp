# Developer Guide | دليل المطور

## 🚀 Universal Workshop ERP Development Guide

Welcome to the Universal Workshop ERP development guide. This documentation will help you understand the codebase, architecture, and development workflow for this Arabic-first ERP solution for Omani automotive workshops.

مرحباً بك في دليل تطوير نظام إدارة الورش الشامل. هذا التوثيق سيساعدك على فهم قاعدة الكود والهيكلة وسير عمل التطوير لهذا الحل العربي الأول لإدارة ورش السيارات العُمانية.

## 📋 Table of Contents | جدول المحتويات

1. [Architecture Overview | نظرة عامة على الهيكلة](#architecture-overview)
2. [Development Environment | بيئة التطوير](#development-environment)
3. [Code Structure | هيكل الكود](#code-structure)
4. [API Reference | مرجع واجهة برمجة التطبيقات](#api-reference)
5. [Database Schema | مخطط قاعدة البيانات](#database-schema)
6. [Arabic Integration | التكامل العربي](#arabic-integration)
7. [Testing Guidelines | إرشادات الاختبار](#testing-guidelines)
8. [Deployment | النشر](#deployment)

## 🏗️ Architecture Overview

### Technology Stack | المكدس التقني

```yaml
Backend Framework: ERPNext v15.65.2 / Frappe Framework
Language: Python 3.10+
Database: MariaDB 10.3+ with UTF8MB4
Cache: Redis 5+
Search: Elasticsearch (optional)
Queue: Redis Queue (RQ)

Frontend:
  - Framework: Vue.js 3 + Frappe UI
  - CSS: Bootstrap 5 with RTL support
  - Icons: Feather Icons + Custom Arabic icons
  - Charts: Chart.js with Arabic labels

Mobile:
  - Progressive Web App (PWA)
  - Offline support with Service Workers
  - Push notifications for Arabic content
```

### System Architecture | هيكلة النظام

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile Client  │    │   API Client    │
│   (Vue.js)      │    │     (PWA)       │    │   (REST/JSON)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │     (Nginx)     │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Frappe Server  │
                    │   (Gunicorn)    │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    MariaDB      │    │     Redis       │    │ Elasticsearch  │
│   (Database)    │    │  (Cache/Queue)  │    │    (Search)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 💻 Development Environment

### Prerequisites | المتطلبات الأساسية

```bash
# System requirements
Ubuntu 20.04+ / macOS 11+ / Windows 10+
Python 3.10+
Node.js 18+
MariaDB 10.3+
Redis 5+
Git 2.20+

# Development tools
VS Code with extensions:
  - Python
  - Pylance  
  - Arabic Language Pack
  - GitLens
  - Docker
```

### Setup Instructions | تعليمات الإعداد

1. **Clone and Setup | النسخ والإعداد**
   ```bash
   git clone https://github.com/saidaladawi/universal-workshop-erp.git
   cd universal-workshop-erp
   ./scripts/install.sh --dev
   ```

2. **Database Configuration | إعداد قاعدة البيانات**
   ```sql
   -- MariaDB configuration for Arabic support
   CREATE DATABASE universal_workshop 
   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- User setup
   CREATE USER 'frappe'@'localhost' IDENTIFIED BY 'frappe';
   GRANT ALL PRIVILEGES ON universal_workshop.* TO 'frappe'@'localhost';
   ```

3. **Environment Variables | متغيرات البيئة**
   ```bash
   # .env.development
   LANG=ar_OM.UTF-8
   TIMEZONE=Asia/Muscat
   CURRENCY=OMR
   VAT_RATE=0.05
   
   # Database
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=universal_workshop
   DB_USER=frappe
   DB_PASSWORD=frappe
   
   # Redis
   REDIS_CACHE=redis://localhost:6379/1
   REDIS_QUEUE=redis://localhost:6379/2
   ```

## 📁 Code Structure

### Directory Layout | تخطيط المجلدات

```
universal-workshop-erp/
├── apps/
│   └── universal_workshop/          # Main application
│       ├── universal_workshop/      # Python package
│       │   ├── __init__.py
│       │   ├── hooks.py            # App hooks and events
│       │   ├── modules.txt         # Module definitions
│       │   ├── patches.txt         # Database patches
│       │   └── config/
│       │       ├── __init__.py
│       │       ├── desktop.py      # Desktop layout
│       │       └── docs.py         # Documentation config
│       │
│       ├── universal_workshop/      # Module directories
│       │   ├── workshop_management/ # Core workshop features
│       │   ├── vehicle_registry/    # Vehicle management
│       │   ├── customer_management/ # CRM features
│       │   ├── inventory_management/# Inventory & parts
│       │   ├── arabic_localization/ # Arabic specific features
│       │   └── oman_compliance/     # Oman regulations
│       │
│       ├── public/                  # Static assets
│       │   ├── js/                 # JavaScript files
│       │   ├── css/                # Stylesheets (RTL support)
│       │   ├── img/                # Images and icons
│       │   └── build.json          # Asset bundling config
│       │
│       └── templates/               # Jinja2 templates
│           ├── pages/              # Page templates
│           ├── includes/           # Reusable components
│           └── emails/             # Email templates
│
├── scripts/                         # Installation & deployment
├── config/                          # Configuration files
├── docs/                           # Documentation
└── tests/                          # Test suites
```

### Module Structure | هيكل الوحدات

Each module follows ERPNext conventions:
كل وحدة تتبع اتفاقيات ERPNext:

```
module_name/
├── __init__.py
├── doctype/                    # Document types
│   └── document_name/
│       ├── __init__.py
│       ├── document_name.py    # Python controller
│       ├── document_name.js    # Client-side logic
│       ├── document_name.json  # DocType definition
│       └── test_document_name.py # Unit tests
│
├── report/                     # Reports
│   └── report_name/
│       ├── __init__.py
│       ├── report_name.py
│       └── report_name.json
│
├── page/                       # Custom pages
│   └── page_name/
│       ├── page_name.py
│       ├── page_name.js
│       └── page_name.html
│
└── web_form/                   # Public forms
    └── form_name/
        ├── form_name.py
        └── form_name.json
```

## 🔌 API Reference

### REST API Endpoints | نقاط اتصال واجهة برمجة التطبيقات

#### Workshop Management | إدارة الورش

```python
# Service Order API
GET    /api/resource/Service Order          # List service orders
POST   /api/resource/Service Order          # Create new service order
GET    /api/resource/Service Order/{id}     # Get specific service order
PUT    /api/resource/Service Order/{id}     # Update service order
DELETE /api/resource/Service Order/{id}     # Delete service order

# Vehicle API
GET    /api/resource/Vehicle                # List vehicles
POST   /api/resource/Vehicle                # Register new vehicle
GET    /api/resource/Vehicle/{id}           # Get vehicle details
PUT    /api/resource/Vehicle/{id}           # Update vehicle
```

#### Customer Management | إدارة العملاء

```python
# Customer API with Arabic support
GET    /api/resource/Customer               # List customers
POST   /api/resource/Customer               # Create new customer
GET    /api/resource/Customer/{id}          # Get customer details

# Example: Create customer with Arabic data
{
    "customer_name": "محمد أحمد الكندي",
    "customer_name_en": "Mohammed Ahmed Al-Kindi", 
    "mobile_no": "+968 9123 4567",
    "email_id": "mohammed@example.com",
    "territory": "Muscat",
    "customer_group": "Individual"
}
```

### Custom API Methods | طرق واجهة برمجة التطبيقات المخصصة

```python
# Arabic text processing
@frappe.whitelist()
def process_arabic_text(text):
    """Process Arabic text for search and indexing"""
    # Remove diacritics, normalize text
    # تتم معالجة النص العربي للبحث والفهرسة
    pass

# VIN decoder
@frappe.whitelist()
def decode_vin(vin_number):
    """Decode Vehicle Identification Number"""
    # Extract manufacturer, year, engine details
    # استخراج معلومات الصانع والسنة وتفاصيل المحرك
    pass

# VAT calculation for Oman
@frappe.whitelist()
def calculate_oman_vat(amount, vat_rate=0.05):
    """Calculate VAT according to Oman regulations"""
    # حساب ضريبة القيمة المضافة وفقاً للوائح العُمانية
    pass
```

## 🗄️ Database Schema

### Core Tables | الجداول الأساسية

```sql
-- Customer table with Arabic support
CREATE TABLE `tabCustomer` (
    `name` varchar(140) PRIMARY KEY,
    `customer_name` text,           -- Arabic name
    `customer_name_en` text,        -- English name  
    `mobile_no` varchar(20),
    `email_id` varchar(140),
    `territory` varchar(140),
    `customer_group` varchar(140),
    `creation` datetime,
    `modified` datetime,
    `owner` varchar(140),
    
    INDEX `idx_territory` (`territory`),
    INDEX `idx_mobile` (`mobile_no`),
    FULLTEXT `idx_search` (`customer_name`, `customer_name_en`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vehicle registry
CREATE TABLE `tabVehicle` (
    `name` varchar(140) PRIMARY KEY,
    `license_plate` varchar(20) UNIQUE,
    `vin_number` varchar(17) UNIQUE,
    `make` varchar(100),
    `model` varchar(100), 
    `year` int(4),
    `color` varchar(50),
    `customer` varchar(140),
    `engine_type` varchar(50),
    `transmission` varchar(50),
    
    FOREIGN KEY (`customer`) REFERENCES `tabCustomer`(`name`),
    INDEX `idx_license_plate` (`license_plate`),
    INDEX `idx_vin` (`vin_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Indexing Strategy | استراتيجية الفهرسة

```sql
-- Arabic text search indexes
-- فهارس البحث في النص العربي
ALTER TABLE `tabCustomer` 
ADD FULLTEXT(`customer_name`, `customer_name_en`);

-- Optimize for Arabic collation
-- تحسين للترتيب العربي  
ALTER TABLE `tabItem`
ADD INDEX `idx_item_name_ar` (`item_name_ar` ASC);

-- Performance indexes for common queries
-- فهارس الأداء للاستعلامات الشائعة
CREATE INDEX `idx_service_date` ON `tabService Order` (`service_date`);
CREATE INDEX `idx_status_date` ON `tabService Order` (`status`, `creation`);
```

## 🌍 Arabic Integration

### RTL Layout Support | دعم تخطيط اتجاه RTL

```css
/* RTL-specific styles */
.rtl-layout {
    direction: rtl;
    text-align: right;
}

/* Arabic form layouts */
.form-group.arabic {
    text-align: right;
    direction: rtl;
}

.form-group.arabic label {
    margin-left: 0;
    margin-right: 15px;
}

/* Mixed content (Arabic + English) */
.mixed-content {
    direction: ltr;
    text-align: left;
}

.mixed-content .arabic-text {
    direction: rtl;
    display: inline-block;
    text-align: right;
}
```

### Arabic Text Processing | معالجة النص العربي

```python
# Arabic text utilities
class ArabicTextProcessor:
    """Utilities for Arabic text processing"""
    
    @staticmethod
    def remove_diacritics(text):
        """Remove Arabic diacritics for search normalization"""
        # إزالة التشكيل للبحث
        diacritics = ''.join([chr(i) for i in range(0x064B, 0x0653)])
        return text.translate(str.maketrans('', '', diacritics))
    
    @staticmethod 
    def normalize_hamza(text):
        """Normalize different forms of Hamza"""
        # توحيد أشكال الهمزة المختلفة
        text = text.replace('آ', 'ا')
        text = text.replace('أ', 'ا') 
        text = text.replace('إ', 'ا')
        text = text.replace('ء', '')
        return text
    
    @staticmethod
    def generate_search_keywords(text):
        """Generate search-friendly keywords from Arabic text"""
        # توليد كلمات مفتاحية صديقة للبحث من النص العربي
        normalized = ArabicTextProcessor.normalize_hamza(
            ArabicTextProcessor.remove_diacritics(text)
        )
        return normalized.split()
```

### Localization Files | ملفات التعريب

```python
# translations/ar.csv
"Workshop Management","إدارة الورش"
"Service Order","أمر خدمة"
"Customer","عميل" 
"Vehicle","مركبة"
"Parts Inventory","مخزون قطع الغيار"
"Invoice","فاتورة"
"VAT","ضريبة القيمة المضافة"
"Total Amount","المبلغ الإجمالي"
```

## 🧪 Testing Guidelines

### Unit Tests | اختبارات الوحدة

```python
# test_arabic_processing.py
import unittest
from universal_workshop.utils.arabic import ArabicTextProcessor

class TestArabicProcessing(unittest.TestCase):
    
    def test_remove_diacritics(self):
        """Test Arabic diacritics removal"""
        text_with_diacritics = "مُحَمَّد"
        expected = "محمد"
        result = ArabicTextProcessor.remove_diacritics(text_with_diacritics)
        self.assertEqual(result, expected)
    
    def test_hamza_normalization(self):
        """Test Hamza normalization"""
        text = "أحمد"
        expected = "احمد"
        result = ArabicTextProcessor.normalize_hamza(text)
        self.assertEqual(result, expected)

# test_oman_vat.py  
class TestOmanVAT(unittest.TestCase):
    
    def test_vat_calculation(self):
        """Test Oman VAT calculation (5%)"""
        amount = 100.0
        expected_vat = 5.0
        expected_total = 105.0
        
        vat, total = calculate_oman_vat(amount)
        self.assertEqual(vat, expected_vat)
        self.assertEqual(total, expected_total)
```

### Integration Tests | اختبارات التكامل

```python
# test_service_order_workflow.py
class TestServiceOrderWorkflow(unittest.TestCase):
    
    def setUp(self):
        """Setup test data"""
        # Create test customer with Arabic name
        self.customer = create_test_customer({
            "customer_name": "أحمد محمد الكندي",
            "mobile_no": "+968 9123 4567"
        })
        
        # Create test vehicle  
        self.vehicle = create_test_vehicle({
            "license_plate": "أ ب ج 1234",
            "customer": self.customer.name
        })
    
    def test_service_order_creation(self):
        """Test creating service order in Arabic"""
        service_order = create_service_order({
            "customer": self.customer.name,
            "vehicle": self.vehicle.name,
            "services": [
                {"service_name": "تغيير زيت المحرك", "amount": 25.0}
            ]
        })
        
        self.assertIsNotNone(service_order.name)
        self.assertEqual(service_order.customer, self.customer.name)
```

## 🚀 Deployment

### Production Deployment | النشر للإنتاج

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  workshop_erp:
    image: universal-workshop-erp:latest
    environment:
      - ENV=production
      - LANG=ar_OM.UTF-8
      - VAT_RATE=0.05
      - CURRENCY=OMR
    volumes:
      - ./sites:/home/frappe/frappe-bench/sites
      - ./logs:/home/frappe/frappe-bench/logs
    ports:
      - "80:8000"
      
  mariadb:
    image: mariadb:10.6
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD}
      - MYSQL_DATABASE=universal_workshop
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    volumes:
      - mariadb_data:/var/lib/mysql
```

### Environment Configuration | إعداد البيئة

```python
# site_config.json
{
    "db_name": "universal_workshop",
    "db_password": "secure_password",
    "default_language": "ar",
    "time_zone": "Asia/Muscat",
    "currency": "OMR",
    "number_format": "#,###.###",
    "date_format": "dd/mm/yyyy",
    "first_day_of_the_week": "Sunday",
    
    # Oman specific settings
    "country": "Oman",
    "vat_settings": {
        "vat_rate": 0.05,
        "vat_number_prefix": "OM"
    },
    
    # Arabic settings
    "rtl_layout": true,
    "arabic_search": true,
    "arabic_reports": true
}
```

### Performance Optimization | تحسين الأداء

```python
# Database optimization for Arabic text
# تحسين قاعدة البيانات للنص العربي

# 1. Index optimization
CREATE INDEX idx_arabic_search ON tabCustomer (customer_name(50));

# 2. Memory settings for MariaDB
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
character_set_server = utf8mb4
collation_server = utf8mb4_unicode_ci

# 3. Redis configuration for Arabic caching
maxmemory 512mb
maxmemory-policy allkeys-lru
```

---

## 📚 Additional Resources | مصادر إضافية

- [ERPNext Developer Guide](https://frappeframework.com/docs/user/en/tutorial)
- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [Arabic Web Development Best Practices](https://www.w3.org/International/articles/inline-bidi-markup/)
- [Oman VAT Guidelines](https://taxoman.gov.om/)

---

*This guide is continuously updated. For the latest information, please visit our repository.*
*هذا الدليل محدث باستمرار. للحصول على أحدث المعلومات، يرجى زيارة مستودعنا.*
