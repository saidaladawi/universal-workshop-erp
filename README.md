# Universal Workshop ERP v2.0 | نظام إدارة الورش الشامل

<div align="center">

![Universal Workshop ERP](docs/assets/logo.png)

**Arabic-First ERP Solution for Omani Automotive Workshops**  
**حل إدارة الموارد المؤسسية للورش العُمانية**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ERPNext Version](https://img.shields.io/badge/ERPNext-v15.65.2-blue.svg)](https://github.com/frappe/erpnext)
[![Python Version](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Build Status](https://github.com/your-username/universal-workshop-erp/workflows/CI/badge.svg)](https://github.com/your-username/universal-workshop-erp/actions)

[English](#english) | [العربية](#arabic)

</div>

---

## English

### 🚗 About Universal Workshop ERP

Universal Workshop ERP is a comprehensive, Arabic-first enterprise resource planning solution specifically designed for automotive workshops in Oman. Built on the robust ERPNext v15 framework, it provides complete business management capabilities with native Arabic language support and local compliance features.

### ✨ Key Features

- **🌐 Dual Language Support**: Complete Arabic and English interface with RTL layout
- **🔧 Workshop Management**: Service orders, appointment scheduling, technician assignment
- **👥 Customer Management**: CRM integration with loyalty programs and satisfaction tracking
- **🚙 Vehicle Registry**: VIN decoder integration with service history tracking
- **📦 Inventory Management**: Parts catalog with barcode scanning and automated reordering
- **💰 Omani VAT Compliance**: 5% VAT calculation with QR code invoice generation
- **📱 Mobile Interface**: Progressive Web App for technicians with offline capabilities
- **🔐 License Management**: Hardware fingerprinting and business name binding
- **📊 Analytics Dashboard**: KPI tracking and financial reporting
- **♻️ Scrap Management**: Vehicle dismantling and parts extraction planning

### 🛠️ Technology Stack

- **Backend**: ERPNext v15.65.2, Frappe Framework, Python 3.10+
- **Frontend**: Vue.js, Bootstrap, Arabic RTL CSS
- **Database**: MariaDB with Arabic character support
- **Mobile**: Progressive Web App (PWA)
- **Search**: Elasticsearch for Arabic fuzzy search
- **Communication**: SMS/WhatsApp integration via Twilio

### 🚀 Quick Installation

#### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.10+
- Node.js 18+
- MariaDB 10.3+
- Redis 5+

#### One-Command Installation
```bash
curl -fsSL https://raw.githubusercontent.com/your-username/universal-workshop-erp/main/scripts/install.sh | bash
```

#### Manual Installation
```bash
# Clone the repository
git clone https://github.com/your-username/universal-workshop-erp.git
cd universal-workshop-erp

# Run setup script
chmod +x scripts/install.sh
./scripts/install.sh

# Start the application
bench start
```

#### Docker Installation
```bash
docker-compose up -d
```

### 📖 Documentation

- [Installation Guide](docs/en/installation.md)
- [Configuration Manual](docs/en/configuration.md)
- [User Guide](docs/en/user-guide.md)
- [API Documentation](docs/en/api.md)
- [Developer Guide](docs/en/development.md)

### 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 📞 Support

- **Email**: support@universal-workshop.om
- **Phone**: +968 95351993
- **Website**: [universal-workshop.om](https://universal-workshop.om)
- **Issues**: [GitHub Issues](https://github.com/your-username/universal-workshop-erp/issues)

---

## Arabic

### 🚗 حول نظام إدارة الورش الشامل

نظام إدارة الورش الشامل هو حل متكامل لإدارة الموارد المؤسسية مصمم خصيصاً للورش العُمانية. مبني على إطار العمل القوي ERPNext v15، يوفر قدرات إدارة الأعمال الكاملة مع الدعم الأصلي للغة العربية وميزات الامتثال المحلي.

### ✨ الميزات الرئيسية

- **🌐 دعم لغتين**: واجهة كاملة بالعربية والإنجليزية مع تخطيط RTL
- **🔧 إدارة الورش**: أوامر الخدمة، جدولة المواعيد، تعيين الفنيين
- **👥 إدارة العملاء**: تكامل CRM مع برامج الولاء وتتبع الرضا
- **🚙 سجل المركبات**: تكامل فك رموز VIN مع تتبع تاريخ الخدمة
- **📦 إدارة المخزون**: كتالوج القطع مع مسح الباركود والطلب التلقائي
- **💰 امتثال ضريبة القيمة المضافة العُمانية**: حساب 5% مع إنتاج فواتير برمز QR
- **📱 واجهة المحمول**: تطبيق ويب تقدمي للفنيين مع إمكانيات عدم الاتصال
- **🔐 إدارة الرخص**: بصمة الأجهزة وربط اسم الشركة
- **📊 لوحة التحليلات**: تتبع مؤشرات الأداء الرئيسية والتقارير المالية
- **♻️ إدارة الخردة**: تفكيك المركبات وتخطيط استخراج القطع

### 🛠️ التقنيات المستخدمة

- **الخلفية**: ERPNext v15.65.2، إطار Frappe، Python 3.10+
- **الواجهة**: Vue.js، Bootstrap، CSS عربي RTL
- **قاعدة البيانات**: MariaDB مع دعم الأحرف العربية
- **المحمول**: تطبيق ويب تقدمي (PWA)
- **البحث**: Elasticsearch للبحث الضبابي العربي
- **التواصل**: تكامل SMS/WhatsApp عبر Twilio

### 🚀 التثبيت السريع

#### المتطلبات الأساسية
- Ubuntu 20.04+ أو CentOS 8+
- Python 3.10+
- Node.js 18+
- MariaDB 10.3+
- Redis 5+

#### تثبيت بأمر واحد
```bash
curl -fsSL https://raw.githubusercontent.com/your-username/universal-workshop-erp/main/scripts/install.sh | bash
```

#### التثبيت اليدوي
```bash
# استنساخ المستودع
git clone https://github.com/your-username/universal-workshop-erp.git
cd universal-workshop-erp

# تشغيل سكريبت الإعداد
chmod +x scripts/install.sh
./scripts/install.sh

# بدء التطبيق
bench start
```

#### تثبيت Docker
```bash
docker-compose up -d
```

### 📖 الوثائق

- [دليل التثبيت](docs/ar/installation.md)
- [دليل التكوين](docs/ar/configuration.md)
- [دليل المستخدم](docs/ar/user-guide.md)
- [وثائق API](docs/ar/api.md)
- [دليل المطور](docs/ar/development.md)

### 🤝 المساهمة

نرحب بالمساهمات! يرجى قراءة [إرشادات المساهمة](CONTRIBUTING.md) للحصول على تفاصيل حول قواعد السلوك وعملية تقديم طلبات السحب.

### 📄 الرخصة

هذا المشروع مرخص بموجب رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

### 📞 الدعم

- **البريد الإلكتروني**: support@universal-workshop.om
- **الهاتف**: +968 95351993
- **الموقع**: [universal-workshop.om](https://universal-workshop.om)
- **المشاكل**: [GitHub Issues](https://github.com/your-username/universal-workshop-erp/issues)

---

<div align="center">
Made with ❤️ for Omani Workshops | صُنع بحب للورش العُمانية
</div> 