# Universal Workshop ERP v2.0 Installation Guide
# دليل تثبيت نظام إدارة الورش الشامل

## Table of Contents / فهرس المحتويات

- [English Documentation](#english-documentation)
- [التوثيق العربي](#التوثيق-العربي)

---

## English Documentation

### 🚗 About Universal Workshop ERP

Universal Workshop ERP v2.0 is a comprehensive Enterprise Resource Planning system specifically designed for automotive workshops in Oman. Built on ERPNext v15, it provides Arabic-first functionality with full RTL (Right-to-Left) support and Omani market-specific features.

### 📋 System Requirements

#### Minimum Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- **Memory (RAM)**: 4GB minimum, 8GB recommended
- **Storage**: 20GB free disk space
- **CPU**: 2 cores minimum, 4 cores recommended
- **Network**: Stable internet connection for installation

#### Software Requirements
- **Python**: 3.10+ (automatically installed on Linux)
- **Node.js**: 18.x LTS (automatically installed on Linux)
- **Database**: MariaDB 10.6+ (automatically configured)
- **Cache**: Redis 6+ (automatically installed)
- **Web Server**: Nginx (for production deployment)

### 🔧 Installation Methods

#### Method 1: One-Command Installation (Linux/macOS)

The fastest way to install Universal Workshop ERP:

```bash
curl -fsSL https://github.com/saidaladawi/universal-workshop-erp/releases/latest/download/install.sh | bash
```

This script will:
- Check system compatibility
- Install all dependencies
- Configure MariaDB with Arabic support
- Setup ERPNext and Universal Workshop
- Create a new site with Arabic localization
- Optionally configure for production

#### Method 2: Docker Installation

For containerized deployment:

```bash
# Clone the repository
git clone https://github.com/saidaladawi/universal-workshop-erp.git
cd universal-workshop-erp

# Copy environment file
cp .env.workshop .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d
```

#### Method 3: Manual Installation

For custom installations or development:

1. **Install frappe-bench**:
   ```bash
   pip3 install frappe-bench
   ```

2. **Initialize bench**:
   ```bash
   bench init --frappe-branch version-15 frappe-bench
   cd frappe-bench
   ```

3. **Get applications**:
   ```bash
   bench get-app --branch version-15 erpnext
   bench get-app https://github.com/saidaladawi/universal-workshop-erp.git
   ```

4. **Create site**:
   ```bash
   bench new-site workshop.local --admin-password admin
   bench --site workshop.local install-app erpnext
   bench --site workshop.local install-app universal_workshop
   ```

5. **Configure Arabic**:
   ```bash
   bench --site workshop.local set-config lang ar
   bench --site workshop.local clear-cache
   ```

#### Method 4: Windows Installation

1. Download and run `install.bat` as Administrator
2. Follow the prompts to install prerequisites
3. Complete database setup manually

### 🌐 Initial Configuration

#### Accessing the System

After installation, access your system at:
- **URL**: `http://workshop.local:8000` or `http://localhost:8000`
- **Username**: Administrator
- **Password**: admin (change immediately after login)

#### First-Time Setup

1. **Login** with Administrator credentials
2. **Change password** for security
3. **Complete Setup Wizard**:
   - Company Information
   - Chart of Accounts (Oman template available)
   - Currency: OMR (Omani Rial)
   - Timezone: Asia/Muscat
   - Language: العربية (Arabic)

#### Creating Users

1. Go to **User** in the system
2. Click **Add User**
3. Fill required information in Arabic/English
4. Assign appropriate roles:
   - `Workshop Manager` - Full workshop operations
   - `Technician` - Service and repair functions
   - `Accounts User` - Financial operations
   - `Sales User` - Customer and sales management

### 🔒 Security Configuration

#### Essential Security Settings

1. **Change default passwords**
2. **Enable two-factor authentication**
3. **Configure SSL certificates** (production)
4. **Set up regular backups**
5. **Configure firewall rules**

#### Backup Configuration

```bash
# Create manual backup
bench --site workshop.local backup --with-files

# Setup automated backups
bench --site workshop.local set-config backup_frequency "Daily"
bench --site workshop.local set-config backup_retention 7
```

### 🚀 Production Deployment

#### Using the built-in production setup:

```bash
cd /home/frappe/frappe-bench
sudo bench setup production frappe
bench --site workshop.local enable-scheduler
```

#### SSL Certificate Setup:

```bash
bench setup lets-encrypt workshop.local
```

### 🛠️ Troubleshooting

#### Common Issues

**Issue**: Site not accessible after installation
**Solution**: Check if bench is running: `bench start`

**Issue**: Arabic text not displaying correctly
**Solution**: Ensure UTF8MB4 charset in database configuration

**Issue**: Permission denied errors
**Solution**: Check file permissions and user ownership

**Issue**: Database connection errors
**Solution**: Verify MariaDB service status and credentials

#### Getting Help

- **GitHub Issues**: [https://github.com/saidaladawi/universal-workshop-erp/issues](https://github.com/saidaladawi/universal-workshop-erp/issues)
- **Email Support**: al.a.dawi@hotmail.com
- **Phone**: +968 95351993

---

## التوثيق العربي

### 🚗 حول نظام إدارة الورش الشامل

نظام إدارة الورش الشامل الإصدار 2.0 هو نظام تخطيط موارد المؤسسات شامل مصمم خصيصاً لورش السيارات في سلطنة عمان. مبني على ERPNext v15، يوفر وظائف تركز على العربية مع دعم كامل لـ RTL (من اليمين إلى اليسار) وميزات خاصة بالسوق العماني.

### 📋 متطلبات النظام

#### الحد الأدنى من المتطلبات
- **نظام التشغيل**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- **الذاكرة**: 4 جيجابايت كحد أدنى، 8 جيجابايت مستحسن
- **التخزين**: 20 جيجابايت مساحة فارغة
- **المعالج**: نواتان كحد أدنى، 4 أنوية مستحسنة
- **الشبكة**: اتصال إنترنت مستقر للتثبيت

#### متطلبات البرمجيات
- **Python**: 3.10+ (يُثبت تلقائياً على Linux)
- **Node.js**: 18.x LTS (يُثبت تلقائياً على Linux)
- **قاعدة البيانات**: MariaDB 10.6+ (تُكوّن تلقائياً)
- **التخزين المؤقت**: Redis 6+ (يُثبت تلقائياً)
- **خادم الويب**: Nginx (للنشر الإنتاجي)

### 🔧 طرق التثبيت

#### الطريقة الأولى: التثبيت بأمر واحد (Linux/macOS)

أسرع طريقة لتثبيت نظام إدارة الورش الشامل:

```bash
curl -fsSL https://github.com/saidaladawi/universal-workshop-erp/releases/latest/download/install.sh | bash
```

هذا النص سيقوم بـ:
- فحص توافق النظام
- تثبيت جميع المتطلبات
- تكوين MariaDB مع دعم العربية
- إعداد ERPNext ونظام الورش الشامل
- إنشاء موقع جديد مع التوطين العربي
- تكوين الإنتاج اختيارياً

#### الطريقة الثانية: تثبيت Docker

للنشر في حاويات:

```bash
# استنساخ المستودع
git clone https://github.com/saidaladawi/universal-workshop-erp.git
cd universal-workshop-erp

# نسخ ملف البيئة
cp .env.workshop .env

# تحرير متغيرات البيئة
nano .env

# بدء جميع الخدمات
docker-compose up -d
```

#### الطريقة الثالثة: التثبيت اليدوي

للتثبيتات المخصصة أو التطوير:

1. **تثبيت frappe-bench**:
   ```bash
   pip3 install frappe-bench
   ```

2. **تهيئة bench**:
   ```bash
   bench init --frappe-branch version-15 frappe-bench
   cd frappe-bench
   ```

3. **الحصول على التطبيقات**:
   ```bash
   bench get-app --branch version-15 erpnext
   bench get-app https://github.com/saidaladawi/universal-workshop-erp.git
   ```

4. **إنشاء موقع**:
   ```bash
   bench new-site workshop.local --admin-password admin
   bench --site workshop.local install-app erpnext
   bench --site workshop.local install-app universal_workshop
   ```

5. **تكوين العربية**:
   ```bash
   bench --site workshop.local set-config lang ar
   bench --site workshop.local clear-cache
   ```

#### الطريقة الرابعة: تثبيت Windows

1. تحميل وتشغيل `install.bat` كمسؤول
2. اتباع التعليمات لتثبيت المتطلبات
3. إكمال إعداد قاعدة البيانات يدوياً

### 🌐 التكوين الأولي

#### الوصول إلى النظام

بعد التثبيت، ادخل إلى نظامك على:
- **الرابط**: `http://workshop.local:8000` أو `http://localhost:8000`
- **اسم المستخدم**: Administrator
- **كلمة المرور**: admin (غيرها فوراً بعد الدخول)

#### الإعداد لأول مرة

1. **تسجيل الدخول** ببيانات المسؤول
2. **تغيير كلمة المرور** للأمان
3. **إكمال معالج الإعداد**:
   - معلومات الشركة
   - دليل الحسابات (قالب عمان متوفر)
   - العملة: ر.ع (الريال العماني)
   - المنطقة الزمنية: Asia/Muscat
   - اللغة: العربية

#### إنشاء المستخدمين

1. اذهب إلى **المستخدم** في النظام
2. انقر **إضافة مستخدم**
3. املأ المعلومات المطلوبة بالعربية/الإنجليزية
4. اسند الأدوار المناسبة:
   - `مدير الورشة` - عمليات الورشة الكاملة
   - `فني` - خدمات الصيانة والإصلاح
   - `مستخدم المحاسبة` - العمليات المالية
   - `مستخدم المبيعات` - إدارة العملاء والمبيعات

### 🔒 تكوين الأمان

#### إعدادات الأمان الأساسية

1. **تغيير كلمات المرور الافتراضية**
2. **تفعيل المصادقة ثنائية المرحلة**
3. **تكوين شهادات SSL** (الإنتاج)
4. **إعداد النسخ الاحتياطية المنتظمة**
5. **تكوين قواعد الجدار الناري**

#### تكوين النسخ الاحتياطي

```bash
# إنشاء نسخة احتياطية يدوية
bench --site workshop.local backup --with-files

# إعداد النسخ الاحتياطية التلقائية
bench --site workshop.local set-config backup_frequency "Daily"
bench --site workshop.local set-config backup_retention 7
```

### 🚀 النشر الإنتاجي

#### استخدام إعداد الإنتاج المدمج:

```bash
cd /home/frappe/frappe-bench
sudo bench setup production frappe
bench --site workshop.local enable-scheduler
```

#### إعداد شهادة SSL:

```bash
bench setup lets-encrypt workshop.local
```

### 🛠️ استكشاف الأخطاء وإصلاحها

#### المشاكل الشائعة

**المشكلة**: الموقع غير قابل للوصول بعد التثبيت
**الحل**: تحقق من تشغيل bench: `bench start`

**المشكلة**: النص العربي لا يظهر بشكل صحيح
**الحل**: تأكد من charset UTF8MB4 في تكوين قاعدة البيانات

**المشكلة**: أخطاء رفض الصلاحية
**الحل**: تحقق من صلاحيات الملفات وملكية المستخدم

**المشكلة**: أخطاء الاتصال بقاعدة البيانات
**الحل**: تحقق من حالة خدمة MariaDB وبيانات الاعتماد

#### الحصول على المساعدة

- **مشاكل GitHub**: [https://github.com/saidaladawi/universal-workshop-erp/issues](https://github.com/saidaladawi/universal-workshop-erp/issues)
- **الدعم عبر البريد الإلكتروني**: al.a.dawi@hotmail.com
- **الهاتف**: +968 95351993 