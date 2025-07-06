# نظام إدارة الورش الشامل - دليل التثبيت

## متطلبات النظام

### الحد الأدنى من المتطلبات
- **نظام التشغيل:** Ubuntu 20.04+ / CentOS 8+ / Windows 10+ / macOS 11+
- **Python:** الإصدار 3.8 أو أحدث
- **Node.js:** الإصدار 14.0 أو أحدث
- **قاعدة البيانات:** MariaDB 10.3+ أو MySQL 8.0+
- **الذاكرة:** 4 جيجابايت رام كحد أدنى، 8 جيجابايت مُوصى به
- **التخزين:** 20 جيجابايت مساحة فارغة
- **الشبكة:** اتصال إنترنت للتثبيت والتحديثات

### المتطلبات الموصى بها
- **نظام التشغيل:** Ubuntu 22.04 LTS
- **Python:** الإصدار 3.11
- **Node.js:** الإصدار 18.0
- **قاعدة البيانات:** MariaDB 10.11
- **الذاكرة:** 16 جيجابايت رام
- **التخزين:** 50 جيجابايت SSD
- **المعالج:** 4 أنوية أو أكثر

## التثبيت السريع

### التثبيت بأمر واحد (Linux/macOS)
```bash
curl -fsSL https://github.com/saidaladawi/universal-workshop-erp/releases/latest/download/install.sh | bash
```

### تثبيت Docker (جميع المنصات)
```bash
git clone https://github.com/saidaladawi/universal-workshop-erp.git
cd universal-workshop-erp
docker-compose up -d
```

### تثبيت Windows
1. قم بتحميل `install.bat` من أحدث إصدار
2. شغله كمدير (Run as Administrator)
3. اتبع تعليمات التثبيت

## التثبيت اليدوي

### الخطوة الأولى: تحضير النظام

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm mariadb-server redis-server
```

#### CentOS/RHEL
```bash
sudo dnf update
sudo dnf install -y python3 python3-pip nodejs npm mariadb-server redis
```

#### Windows
1. ثبت Python 3.8+ من python.org
2. ثبت Node.js 14+ من nodejs.org
3. ثبت MariaDB من mariadb.org
4. ثبت Redis من redis.io

### الخطوة الثانية: إعداد قاعدة البيانات

#### إعداد MariaDB
```bash
sudo mysql_secure_installation
sudo mysql -u root -p
```

```sql
CREATE DATABASE workshop_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'workshop_user'@'localhost' IDENTIFIED BY 'كلمة_مرور_آمنة';
GRANT ALL PRIVILEGES ON workshop_erp.* TO 'workshop_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### الخطوة الثالثة: تثبيت Frappe Bench

```bash
# تثبيت bench
pip3 install frappe-bench

# تهيئة bench
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench

# إنشاء موقع
bench new-site workshop.local --db-name workshop_erp --db-user workshop_user --db-password كلمة_مرور_آمنة

# تعيين الموقع كافتراضي
bench use workshop.local
```

### الخطوة الرابعة: تثبيت ERPNext

```bash
# الحصول على ERPNext
bench get-app --branch version-15 erpnext

# تثبيت ERPNext
bench --site workshop.local install-app erpnext
```

### الخطوة الخامسة: تثبيت تطبيق الورش الشامل

```bash
# الحصول على تطبيق الورش الشامل
bench get-app https://github.com/saidaladawi/universal-workshop-erp.git

# تثبيت تطبيق الورش الشامل
bench --site workshop.local install-app universal_workshop
```

### الخطوة السادسة: التكوين

```bash
# تفعيل وضع المطور (اختياري)
bench --site workshop.local set-config developer_mode 1

# إيقاف وضع الصيانة
bench --site workshop.local set-maintenance-mode off

# بدء الخدمات
bench start
```

## التكوين

### تكوين الموقع
عدل ملف `sites/workshop.local/site_config.json`:

```json
{
  "db_name": "workshop_erp",
  "db_password": "كلمة_مرور_آمنة",
  "db_user": "workshop_user",
  "developer_mode": 0,
  "maintenance_mode": 0,
  "lang": "ar",
  "time_zone": "Asia/Muscat",
  "currency": "OMR",
  "country": "Oman",
  "auto_email_reports": 1,
  "scheduler_enabled": 1
}
```

### متغيرات البيئة
أنشئ ملف `.env`:

```bash
# قاعدة البيانات
DB_HOST=localhost
DB_PORT=3306
DB_NAME=workshop_erp
DB_USER=workshop_user
DB_PASSWORD=كلمة_مرور_آمنة

# Redis
REDIS_CACHE_HOST=localhost
REDIS_CACHE_PORT=6379
REDIS_QUEUE_HOST=localhost
REDIS_QUEUE_PORT=6380

# البريد الإلكتروني
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=كلمة_مرور_التطبيق

# الأمان
ENCRYPTION_KEY=مفتاح_التشفير_32_حرف
```

## النشر في بيئة الإنتاج

### استخدام Docker Compose

1. استنسخ المستودع:
```bash
git clone https://github.com/saidaladawi/universal-workshop-erp.git
cd universal-workshop-erp
```

2. كوّن البيئة:
```bash
cp .env.production.example .env.production
# عدل .env.production بإعداداتك
```

3. انشر:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### استخدام Kubernetes

1. طبق المانيفستات:
```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl apply -f deployment/kubernetes/storage.yaml
kubectl apply -f deployment/kubernetes/deployment.yaml
kubectl apply -f deployment/kubernetes/services.yaml
```

2. كوّن الـ ingress وشهادات SSL حسب الحاجة.

## التحديثات والصيانة

### التحديثات التلقائية
```bash
# تحديث إلى أحدث إصدار
./scripts/update.sh

# تحديث إلى إصدار محدد
./scripts/update.sh v2.1.0
```

### التحديثات اليدوية
```bash
cd frappe-bench
bench update --reset
bench --site workshop.local migrate
bench restart
```

### النسخ الاحتياطي والاستعادة

#### إنشاء نسخة احتياطية
```bash
bench --site workshop.local backup
```

#### استعادة نسخة احتياطية
```bash
bench --site workshop.local restore backup_file.sql.gz
```

## حل المشاكل

### المشاكل الشائعة

#### خطأ اتصال قاعدة البيانات
- تحقق من بيانات اعتماد قاعدة البيانات في site_config.json
- تأكد من تشغيل MariaDB: `sudo systemctl status mariadb`
- اختبر الاتصال: `mysql -u workshop_user -p workshop_erp`

#### أخطاء الصلاحيات
- إصلاح صلاحيات الملفات: `sudo chown -R $USER:$USER frappe-bench`
- إعادة تعيين الصلاحيات: `bench setup socketio`

#### تعارض المنافذ
- غيّر المنفذ في `sites/common_site_config.json`
- المنافذ الافتراضية: 8000 (ويب)، 9000 (socketio)

#### مشاكل الذاكرة
- زيادة الذاكرة الافتراضية: `sudo sysctl vm.max_map_count=262144`
- أضف swap space إذا لزم الأمر

### تحسين الأداء

#### تحسين قاعدة البيانات
```sql
-- إضافة فهارس لتحسين الأداء
ALTER TABLE `tabCustomer` ADD INDEX `idx_customer_name` (`customer_name`);
ALTER TABLE `tabItem` ADD INDEX `idx_item_code` (`item_code`);
```

#### تكوين Redis
عدل `/etc/redis/redis.conf`:
```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### ملفات السجل
- سجلات Frappe: `logs/frappe.log`
- سجلات الأخطاء: `logs/error.log`
- سجلات Nginx: `/var/log/nginx/`

## الأمان

### إعداد شهادة SSL
```bash
# استخدام Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### تكوين جدار الحماية
```bash
sudo ufw enable
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
```

### تحديثات الأمان المنتظمة
```bash
# تحديث حزم النظام
sudo apt update && sudo apt upgrade

# تحديث Frappe/ERPNext
bench update
```

## الدعم

### دعم المجتمع
- مشاكل GitHub: https://github.com/saidaladawi/universal-workshop-erp/issues
- المناقشات: https://github.com/saidaladawi/universal-workshop-erp/discussions
- مجتمع ERPNext: https://discuss.erpnext.com

### الوثائق
- دليل المستخدم: `/docs/ar/user-manual.md`
- وثائق API: `/docs/ar/api-documentation.md`
- دليل المطور: `/docs/ar/developer-guide.md`

### الدعم المهني
للدعم المؤسسي وخدمات التخصيص، اتصل بـ:
- البريد الإلكتروني: support@workshop-erp.com
- الموقع: https://workshop-erp.com

## الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف LICENSE للتفاصيل.

## المساهمة

يرجى قراءة CONTRIBUTING.md للحصول على تفاصيل حول مدونة السلوك الخاصة بنا وعملية تقديم طلبات السحب.
