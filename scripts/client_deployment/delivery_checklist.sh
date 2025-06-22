#!/bin/bash
# قائمة فحص التسليم النهائي للعميل
# الاستخدام: ./delivery_checklist.sh [اسم_العميل] [نطاق_الموقع]

set -e

CLIENT_NAME="$1"
SITE_NAME="${2:-universal.local}"

if [ -z "$CLIENT_NAME" ]; then
    echo "❌ الاستخدام: ./delivery_checklist.sh [اسم_العميل] [نطاق_الموقع]"
    echo "مثال: ./delivery_checklist.sh 'ورشة الفارسي' alfarsi.local"
    exit 1
fi

echo "📋 قائمة فحص التسليم النهائي"
echo "=============================="
echo "👤 العميل: $CLIENT_NAME"
echo "🌐 الموقع: $SITE_NAME"
echo "📅 التاريخ: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# متغيرات للنتائج
PASSED=0
FAILED=0
WARNINGS=0

# دالة الفحص
check_item() {
    local status=$1
    local description="$2"
    local fix_command="$3"
    
    if [ $status -eq 0 ]; then
        echo "✅ $description"
        ((PASSED++))
        return 0
    else
        echo "❌ $description"
        if [ -n "$fix_command" ]; then
            echo "   🔧 لإصلاحه: $fix_command"
        fi
        ((FAILED++))
        return 1
    fi
}

warn_item() {
    echo "⚠️ $1"
    ((WARNINGS++))
}

info_item() {
    echo "ℹ️ $1"
}

# ===== 1. فحص البنية التحتية =====
echo "🏗️ فحص البنية التحتية:"

# فحص نظام التشغيل
if command -v lsb_release &> /dev/null; then
    OS_INFO=$(lsb_release -d | cut -f2)
    info_item "نظام التشغيل: $OS_INFO"
fi

# فحص Python
python3 --version > /dev/null 2>&1
check_item $? "Python 3 مثبت ويعمل" "sudo apt install python3 python3-pip"

# فحص Node.js
node --version > /dev/null 2>&1
check_item $? "Node.js مثبت ويعمل" "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install nodejs"

# فحص Git
git --version > /dev/null 2>&1
check_item $? "Git مثبت ويعمل" "sudo apt install git"

# فحص MariaDB
systemctl is-active mariadb > /dev/null 2>&1
if check_item $? "MariaDB يعمل" "sudo systemctl start mariadb"; then
    mysql -u root -e "SELECT 1;" > /dev/null 2>&1
    check_item $? "يمكن الاتصال بـ MariaDB" "sudo mysql_secure_installation"
fi

# فحص Redis
systemctl is-active redis > /dev/null 2>&1
if check_item $? "Redis يعمل" "sudo systemctl start redis"; then
    redis-cli ping > /dev/null 2>&1
    check_item $? "Redis يستجيب" "sudo systemctl restart redis"
fi

echo ""

# ===== 2. فحص Frappe Framework =====
echo "🖥️ فحص Frappe Framework:"

# فحص وجود bench
command -v bench &> /dev/null
check_item $? "Bench مثبت" "pip3 install frappe-bench"

# فحص وجود المجلد
[ -d "sites" ]
check_item $? "مجلد frappe-bench صحيح" "bench init frappe-bench"

# فحص البيئة الافتراضية
[ -f "env/bin/python" ]
check_item $? "بيئة Python الافتراضية موجودة" "python3 -m venv env"

# فحص عمليات Frappe
ps aux | grep -E "(frappe|bench)" | grep -v grep > /dev/null
check_item $? "عمليات Frappe تعمل" "bench start"

echo ""

# ===== 3. فحص الموقع =====
echo "🌐 فحص الموقع ($SITE_NAME):"

# فحص وجود الموقع
[ -d "sites/$SITE_NAME" ]
if check_item $? "مجلد الموقع موجود" "bench new-site $SITE_NAME"; then
    
    # فحص ملف التكوين
    [ -f "sites/$SITE_NAME/site_config.json" ]
    check_item $? "ملف تكوين الموقع موجود"
    
    # فحص قاعدة البيانات
    bench --site $SITE_NAME list-apps > /dev/null 2>&1
    check_item $? "يمكن الاتصال بقاعدة بيانات الموقع" "bench --site $SITE_NAME migrate"
    
    # فحص التطبيقات المثبتة
    INSTALLED_APPS=$(bench --site $SITE_NAME list-apps 2>/dev/null || echo "")
    
    echo "$INSTALLED_APPS" | grep -q "frappe"
    check_item $? "Frappe مثبت" "bench --site $SITE_NAME install-app frappe"
    
    echo "$INSTALLED_APPS" | grep -q "erpnext"
    check_item $? "ERPNext مثبت" "bench get-app erpnext && bench --site $SITE_NAME install-app erpnext"
    
    echo "$INSTALLED_APPS" | grep -q "universal_workshop"
    check_item $? "Universal Workshop مثبت" "bench get-app universal_workshop && bench --site $SITE_NAME install-app universal_workshop"
fi

echo ""

# ===== 4. فحص التكوين =====
echo "⚙️ فحص التكوين:"

if [ -d "sites/$SITE_NAME" ]; then
    # فحص إعدادات النظام
    COUNTRY=$(bench --site $SITE_NAME execute "import frappe; print(frappe.db.get_value('System Settings', None, 'country'))" 2>/dev/null || echo "")
    [ "$COUNTRY" = "Oman" ]
    check_item $? "البلد مضبوط على عمان" "bench --site $SITE_NAME execute frappe.db.set_value --args \"['System Settings', None, 'country', 'Oman']\""
    
    LANGUAGE=$(bench --site $SITE_NAME execute "import frappe; print(frappe.db.get_value('System Settings', None, 'language'))" 2>/dev/null || echo "")
    [ "$LANGUAGE" = "ar" ]
    check_item $? "اللغة مضبوطة على العربية" "bench --site $SITE_NAME execute frappe.db.set_value --args \"['System Settings', None, 'language', 'ar']\""
    
    TIMEZONE=$(bench --site $SITE_NAME execute "import frappe; print(frappe.db.get_value('System Settings', None, 'time_zone'))" 2>/dev/null || echo "")
    [ "$TIMEZONE" = "Asia/Muscat" ]
    check_item $? "المنطقة الزمنية مضبوطة على مسقط" "bench --site $SITE_NAME execute frappe.db.set_value --args \"['System Settings', None, 'time_zone', 'Asia/Muscat']\""
fi

echo ""

# ===== 5. فحص الرخصة =====
echo "🔐 فحص الرخصة:"

# البحث عن ملف الرخصة
LICENSE_FILE="licenses/${CLIENT_NAME// /_}_license.json"
[ -f "$LICENSE_FILE" ]
check_item $? "ملف الرخصة موجود" "./generate_license.sh '$CLIENT_NAME'"

if [ -f "$LICENSE_FILE" ]; then
    # التحقق من صحة ملف الرخصة
    python3 -c "import json; json.load(open('$LICENSE_FILE'))" > /dev/null 2>&1
    check_item $? "ملف الرخصة صالح (JSON)"
    
    # التحقق من بيانات الرخصة
    CLIENT_IN_LICENSE=$(python3 -c "import json; print(json.load(open('$LICENSE_FILE'))['license_data']['client_name'])" 2>/dev/null || echo "")
    [ "$CLIENT_IN_LICENSE" = "$CLIENT_NAME" ]
    check_item $? "اسم العميل صحيح في الرخصة"
fi

echo ""

# ===== 6. فحص الشبكة والمنافذ =====
echo "🔌 فحص الشبكة والمنافذ:"

# فحص منفذ Frappe
netstat -tuln | grep -q ":8000 "
check_item $? "منفذ Frappe (8000) مفتوح" "bench start"

# فحص منفذ MariaDB
netstat -tuln | grep -q ":3306 "
check_item $? "منفذ MariaDB (3306) مفتوح" "sudo systemctl start mariadb"

# فحص منفذ Redis
netstat -tuln | grep -q ":6379 "
check_item $? "منفذ Redis (6379) مفتوح" "sudo systemctl start redis"

# اختبار الوصول للموقع
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000" 2>/dev/null || echo "000")
[ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]
check_item $? "الموقع يستجيب (HTTP $HTTP_CODE)" "bench start"

echo ""

# ===== 7. فحص الأمان =====
echo "🔒 فحص الأمان:"

# فحص جدار الحماية
if command -v ufw &> /dev/null; then
    ufw status | grep -q "Status: active"
    if [ $? -eq 0 ]; then
        info_item "جدار الحماية مفعل"
    else
        warn_item "جدار الحماية غير مفعل"
    fi
fi

# فحص صلاحيات الملفات
[ "$(stat -c %a sites/$SITE_NAME 2>/dev/null)" = "755" ] 2>/dev/null
if [ $? -eq 0 ]; then
    info_item "صلاحيات مجلد الموقع صحيحة"
else
    warn_item "تحقق من صلاحيات مجلد الموقع"
fi

echo ""

# ===== 8. فحص النسخ الاحتياطية =====
echo "💾 فحص النسخ الاحتياطية:"

# فحص وجود سكريپت النسخ الاحتياطي
[ -f "$HOME/daily_backup.sh" ]
check_item $? "سكريپت النسخ الاحتياطي موجود" "./setup_backup.sh $SITE_NAME"

# فحص المهام المجدولة
crontab -l 2>/dev/null | grep -q "backup.sh"
check_item $? "النسخ الاحتياطي التلقائي مفعل" "crontab -e"

# فحص مجلد النسخ الاحتياطية
BACKUP_DIR="$HOME/backups"
[ -d "$BACKUP_DIR" ]
check_item $? "مجلد النسخ الاحتياطية موجود" "mkdir -p $BACKUP_DIR"

echo ""

# ===== 9. فحص الأداء =====
echo "⚡ فحص الأداء:"

# فحص استخدام القرص
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    check_item 0 "مساحة القرص كافية (${DISK_USAGE}%)"
elif [ "$DISK_USAGE" -lt 90 ]; then
    warn_item "مساحة القرص منخفضة (${DISK_USAGE}%)"
else
    check_item 1 "مساحة القرص ممتلئة (${DISK_USAGE}%)" "تنظيف الملفات غير المطلوبة"
fi

# فحص استخدام الذاكرة
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEM_USAGE" -lt 80 ]; then
    check_item 0 "استخدام الذاكرة طبيعي (${MEM_USAGE}%)"
elif [ "$MEM_USAGE" -lt 90 ]; then
    warn_item "استخدام الذاكرة مرتفع (${MEM_USAGE}%)"
else
    warn_item "استخدام الذاكرة مرتفع جداً (${MEM_USAGE}%)"
fi

# فحص سرعة الاستجابة
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000 2>/dev/null || echo "0")
RESPONSE_MS=$(echo "$RESPONSE_TIME * 1000" | bc 2>/dev/null || echo "0")
if [ "$(echo "$RESPONSE_TIME < 2" | bc 2>/dev/null)" = "1" ]; then
    info_item "سرعة الاستجابة جيدة (${RESPONSE_MS%.*}ms)"
else
    warn_item "سرعة الاستجابة بطيئة (${RESPONSE_MS%.*}ms)"
fi

echo ""

# ===== 10. اختبار الوظائف الأساسية =====
echo "🧪 اختبار الوظائف الأساسية:"

if [ -d "sites/$SITE_NAME" ]; then
    # اختبار إنشاء عميل
    TEST_CUSTOMER_RESULT=$(bench --site $SITE_NAME execute "
import frappe
try:
    doc = frappe.get_doc({
        'doctype': 'Customer',
        'customer_name': 'عميل تجريبي للاختبار',
        'customer_group': 'Individual',
        'territory': 'Oman'
    })
    doc.insert()
    frappe.db.rollback()
    print('success')
except Exception as e:
    print('error')
" 2>/dev/null || echo "error")
    
    [ "$TEST_CUSTOMER_RESULT" = "success" ]
    check_item $? "يمكن إنشاء عملاء"
    
    # اختبار الوصول للواجهة
    LOGIN_TEST=$(curl -s -X POST -d "usr=Administrator&pwd=admin" http://localhost:8000/api/method/login 2>/dev/null | grep -q "message" && echo "success" || echo "error")
    [ "$LOGIN_TEST" = "success" ]
    check_item $? "واجهة تسجيل الدخول تعمل"
fi

echo ""

# ===== النتيجة النهائية =====
echo "=============================="
echo "📊 ملخص نتائج الفحص:"
echo "✅ نجح: $PASSED"
echo "❌ فشل: $FAILED"
echo "⚠️ تحذيرات: $WARNINGS"

echo ""
if [ $FAILED -eq 0 ]; then
    echo "🎉 النظام جاهز للتسليم!"
    echo ""
    echo "📋 المعلومات النهائية:"
    echo "   👤 العميل: $CLIENT_NAME"
    echo "   🌐 رابط النظام: http://$(hostname -I | awk '{print $1}'):8000"
    echo "   🔗 الموقع المحلي: http://$SITE_NAME:8000"
    echo "   👨‍💼 المستخدم الإداري: Administrator"
    echo "   🔑 كلمة المرور: admin (يجب تغييرها)"
    echo ""
    echo "📞 معلومات الدعم:"
    echo "   📧 البريد الإلكتروني: support@universal-workshop.om"
    echo "   📱 الهاتف: +968 95351993"
    echo "   🕐 ساعات العمل: الأحد - الخميس: 8:00 ص - 6:00 م"
    echo ""
    echo "📄 الوثائق المطلوبة:"
    echo "   □ توقيع العميل على التسليم"
    echo "   □ تسليم ملف الرخصة"
    echo "   □ تسليم دليل المستخدم"
    echo "   □ تسليم دليل الصيانة"
    echo "   □ تدريب فريق العميل"
    
    # إنشاء تقرير التسليم
    create_delivery_report
    
else
    echo "⚠️ يوجد $FAILED مشكلة يجب إصلاحها قبل التسليم"
    echo ""
    echo "🔧 خطوات الإصلاح الموصى بها:"
    echo "   1. راجع الأخطاء أعلاه واتبع تعليمات الإصلاح"
    echo "   2. شغل السكريپت مرة أخرى للتأكد"
    echo "   3. راجع سجلات النظام: tail -f logs/*.log"
    echo "   4. استشر فريق الدعم عند الحاجة"
    
    exit 1
fi

# دالة إنشاء تقرير التسليم
create_delivery_report() {
    REPORT_FILE="delivery_reports/${CLIENT_NAME// /_}_delivery_report_$(date +%Y%m%d).txt"
    mkdir -p delivery_reports
    
    cat > "$REPORT_FILE" << EOF
تقرير تسليم نظام إدارة الورش الشامل
===================================

معلومات العميل:
- الاسم: $CLIENT_NAME
- الموقع: $SITE_NAME
- تاريخ التسليم: $(date '+%Y-%m-%d %H:%M:%S')
- رقم المشروع: UW-$(date +%Y)-${CLIENT_NAME// /-}

معلومات النظام:
- الإصدار: Universal Workshop ERP v2.0
- إصدار Frappe: $(bench version 2>/dev/null | head -1 || echo "غير محدد")
- نظام التشغيل: $(lsb_release -d 2>/dev/null | cut -f2 || uname -a)

معلومات الوصول:
- الرابط: http://$(hostname -I | awk '{print $1}'):8000
- المستخدم الإداري: Administrator
- كلمة المرور الأولية: admin (يجب تغييرها فوراً)

التكوين:
- البلد: عمان
- العملة: ريال عماني (OMR)
- اللغة: العربية
- المنطقة الزمنية: آسيا/مسقط

الرخصة:
- ملف الرخصة: $LICENSE_FILE
- نوع الرخصة: دائمة
- الميزات: إدارة الورش، المخزون، إدارة الخردة، التقارير

النسخ الاحتياطية:
- النسخ اليومي: 2:00 صباحاً
- النسخ الأسبوعي: الأحد 3:00 صباحاً  
- النسخ الشهري: اليوم الأول من الشهر 4:00 صباحاً

نتائج الفحص:
- نجح: $PASSED عنصر
- فشل: $FAILED عنصر
- تحذيرات: $WARNINGS عنصر

ملاحظات مهمة:
1. يجب تغيير كلمة المرور فور الدخول الأول
2. تأكد من إجراء النسخ الاحتياطية بانتظام
3. تواصل مع الدعم عند الحاجة

معلومات الدعم:
- البريد الإلكتروني: support@universal-workshop.om
- الهاتف: +968 95351993
- ساعات العمل: الأحد - الخميس: 8:00 ص - 6:00 م

تم إعداد هذا التقرير تلقائياً في: $(date '+%Y-%m-%d %H:%M:%S')
EOF

    echo "📄 تم إنشاء تقرير التسليم: $REPORT_FILE"
}
