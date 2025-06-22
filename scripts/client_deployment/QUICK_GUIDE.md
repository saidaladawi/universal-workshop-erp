# 🚀 دليل المطور السريع
## Universal Workshop ERP - Client Deployment

---

## ⚡ البدء السريع

```bash
# 1. الانتقال لمجلد السكريپتات
cd scripts/client_deployment

# 2. اختبار السكريپتات
./test_scripts.sh

# 3. إنشاء عميل جديد (الكل في واحد!)
./deploy_client.sh new-client "ورشة الفارسي" "alfarsi.local" "professional"

# 4. فحص التسليم النهائي
./deploy_client.sh delivery-check "ورشة الفارسي" "alfarsi.local"
```

---

## 📋 قائمة فحص سريعة للمطور

### قبل زيارة العميل:
- [ ] تشغيل `./test_scripts.sh` للتأكد من عمل جميع السكريپتات
- [ ] تحضير البيانات الأساسية للعميل
- [ ] طباعة الوثائق المطلوبة
- [ ] نسخ السكريپتات على جهاز محمول

### عند العميل:
- [ ] فحص البنية التحتية: `./deploy_client.sh check-system`
- [ ] إنشاء العميل الجديد: `./deploy_client.sh new-client "اسم العميل" "نطاق.local"`
- [ ] إعداد النسخ الاحتياطية: `./deploy_client.sh setup-backup`
- [ ] تدريب المستخدمين
- [ ] اختبار النظام مع العميل
- [ ] فحص التسليم النهائي: `./deploy_client.sh delivery-check`

### بعد التسليم:
- [ ] بدء المراقبة: `./deploy_client.sh monitor نطاق.local`
- [ ] تسليم تقرير التسليم النهائي
- [ ] تدوين أي ملاحظات للمتابعة
- [ ] جدولة زيارة المتابعة

---

## 🔧 أوامر مفيدة للمطور

```bash
# عرض جميع العمليات المتاحة
./deploy_client.sh help

# عرض المواقع الموجودة
./deploy_client.sh list-sites

# عرض النسخ الاحتياطية
./deploy_client.sh list-backups

# فحص النظام فقط
./deploy_client.sh check-system universal.local

# إنشاء رخصة فقط
./deploy_client.sh generate-license "اسم العميل" "معرف العميل" "professional"

# استعادة نسخة احتياطية
./deploy_client.sh restore-backup site.local backup.sql.gz files.tar

# مراقبة النظام (كل 30 ثانية)
./deploy_client.sh monitor site.local 30
```

---

## 🐛 حل المشاكل السريع

### خطأ "bench: command not found"
```bash
pip3 install frappe-bench
export PATH=$PATH:~/.local/bin
```

### خطأ في قاعدة البيانات
```bash
sudo systemctl start mariadb
mysql -u root -e "SELECT 1;"
```

### خطأ في Redis
```bash
sudo systemctl start redis
redis-cli ping
```

### مشكلة في الصلاحيات
```bash
sudo chown -R $(whoami):$(whoami) ~/frappe-bench
chmod -R 755 ~/frappe-bench
```

### النظام بطيء
```bash
# فحص الموارد
./deploy_client.sh monitor site.local 10

# تنظيف الملفات المؤقتة
bench clear-cache
bench build
```

---

## 📞 الدعم والمساعدة

- 📧 البريد الإلكتروني: support@universal-workshop.om
- 📱 الهاتف: +968 95351993
- 🕐 ساعات العمل: الأحد - الخميس: 8:00 ص - 6:00 م

---

## 📚 الوثائق الكاملة

- [دليل المطور التفصيلي](../../docs/ar/دليل_المطور_التفصيلي.md)
- [دليل تشغيل النظام](../../docs/ar/دليل_تشغيل_النظام.md)
- [خطة تسليم العميل](../../docs/ar/خطة_تسليم_العميل.md)
- [نموذج العقد](../../docs/ar/نموذج_العقد.md)

---

*دليل سريع للمطورين - إصدار v2.0*  
*تم التحديث في: ٢٢ يونيو ٢٠٢٥*
