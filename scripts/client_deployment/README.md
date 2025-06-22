# سكريبتات تسليم العميل
## Universal Workshop ERP - Client Deployment Scripts

هذا المجلد يحتوي على جميع السكريبتات المطلوبة لتسليم نظام إدارة الورش الشامل للعملاء.

---

## 📁 محتويات المجلد

### السكريبتات الأساسية:

**🚀 السكريپت الرئيسي الجديد:**
0. **`deploy_client.sh`** - السكريپت الرئيسي الشامل (يجمع كل العمليات)
   ```bash
   ./deploy_client.sh [العملية] [المعاملات...]
   ./deploy_client.sh help  # لعرض جميع العمليات المتاحة
   ```

1. **`create_client_site.sh`** - إنشاء موقع جديد للعميل
   ```bash
   ./create_client_site.sh "اسم العميل" "نطاق.local"
   ```

2. **`generate_license.sh`** - إنشاء رخصة للعميل
   ```bash
   ./generate_license.sh "اسم العميل" "معرف العميل" "نوع الرخصة"
   ```

3. **`system_check.sh`** - فحص شامل لحالة النظام
   ```bash
   ./system_check.sh [نطاق_الموقع]
   ```

4. **`setup_backup.sh`** - إعداد النسخ الاحتياطية التلقائية
   ```bash
   ./setup_backup.sh [نطاق_الموقع] [مسار_النسخ]
   ```

5. **`delivery_checklist.sh`** - قائمة فحص التسليم النهائي
   ```bash
   ./delivery_checklist.sh "اسم العميل" [نطاق_الموقع]
   ```

6. **`restore_backup.sh`** - استعادة النسخة الاحتياطية
   ```bash
   ./restore_backup.sh [نطاق_الموقع] [ملف_قاعدة_البيانات] [ملف_الأصول]
   ```

7. **`monitor_system.sh`** - مراقبة النظام المستمرة
   ```bash
   ./monitor_system.sh [نطاق_الموقع] [فترة_المراقبة_بالثواني]
   ```

---

## 🚀 سير العمل المُوصى به

### 🎯 الطريقة الجديدة (باستخدام السكريپت الرئيسي):

```bash
# 1. إعداد عميل جديد كاملاً (الكل في واحد!)
./deploy_client.sh new-client "ورشة الفارسي" "alfarsi.local" "professional"

# 2. فحص التسليم النهائي
./deploy_client.sh delivery-check "ورشة الفارسي" "alfarsi.local"

# 3. بدء المراقبة
./deploy_client.sh monitor alfarsi.local 30
```

### 📋 الطريقة التقليدية (خطوة بخطوة):

#### 1. التحضير (في المكتب)
```bash
# فحص النظام
./system_check.sh

# إنشاء موقع العميل
./create_client_site.sh "ورشة الفارسي" "alfarsi.local"

# إنشاء الرخصة
./generate_license.sh "ورشة الفارسي" "ALFARSI-001" "professional"
```

#### 2. التثبيت (عند العميل)
```bash
# فحص النظام مرة أخرى
./system_check.sh alfarsi.local

# إعداد النسخ الاحتياطية
./setup_backup.sh alfarsi.local

# فحص التسليم النهائي
./delivery_checklist.sh "ورشة الفارسي" alfarsi.local
```

### 🎮 عمليات إضافية:
```bash
# عرض جميع العمليات المتاحة
./deploy_client.sh help

# عرض المواقع المتاحة
./deploy_client.sh list-sites

# عرض النسخ الاحتياطية
./deploy_client.sh list-backups

# استعادة نسخة احتياطية
./deploy_client.sh restore-backup alfarsi.local backup.sql.gz files.tar
```

---

## 📋 متطلبات النظام

### البرامج المطلوبة:
- Ubuntu/Debian Linux
- Python 3.8+
- Node.js 18+
- MariaDB 10.5+
- Redis 6+
- Git

### الصلاحيات المطلوبة:
- صلاحيات sudo لتثبيت الحزم
- صلاحيات إنشاء مجلدات في /home
- صلاحيات تعديل crontab

---

## 🔧 الاستكشاف وإصلاح الأخطاء

### مشاكل شائعة وحلولها:

#### 1. خطأ "bench: command not found"
```bash
pip3 install frappe-bench
export PATH=$PATH:~/.local/bin
```

#### 2. خطأ في الاتصال بـ MariaDB
```bash
sudo systemctl start mariadb
sudo mysql_secure_installation
```

#### 3. خطأ في Redis
```bash
sudo systemctl start redis
redis-cli ping
```

#### 4. مشكلة في الصلاحيات
```bash
sudo chown -R $(whoami):$(whoami) ~/frappe-bench
chmod -R 755 ~/frappe-bench
```

---

## 📞 الدعم

للحصول على المساعدة:
- 📧 البريد الإلكتروني: support@universal-workshop.om
- 📱 الهاتف: +968 95351993
- 🕐 ساعات العمل: الأحد - الخميس: 8:00 ص - 6:00 م

---

## 📄 الوثائق ذات الصلة

- [دليل المطور التفصيلي](../docs/ar/دليل_المطور_التفصيلي.md)
- [دليل تشغيل النظام](../docs/ar/دليل_تشغيل_النظام.md)
- [خطة تسليم العميل](../docs/ar/خطة_تسليم_العميل.md)

---

*تم إعداد هذه السكريبتات في: ٢٢ يونيو ٢٠٢٥*  
*إصدار النظام: v2.0*
