#!/bin/bash
# سكريبت فحص النظام وحل المشاكل
# الاستخدام: ./system_check.sh [نطاق_الموقع]

set -e

SITE_NAME="${1:-universal.local}"

echo "🔍 فحص حالة النظام للموقع: $SITE_NAME"
echo "========================================"

# متغيرات للنتائج
PASSED=0
FAILED=0
WARNINGS=0

# دالة للفحص
check_service() {
    if [ $2 -eq 0 ]; then
        echo "✅ $1"
        ((PASSED++))
        return 0
    else
        echo "❌ $1"
        ((FAILED++))
        return 1
    fi
}

warn_service() {
    echo "⚠️ $1"
    ((WARNINGS++))
}

# 1. فحص الخدمات الأساسية
echo "🔧 فحص الخدمات الأساسية:"

# فحص MariaDB
systemctl is-active mariadb > /dev/null 2>&1
if check_service "MariaDB يعمل" $?; then
    # فحص إمكانية الاتصال
    mysql -u root -e "SELECT 1;" > /dev/null 2>&1
    check_service "يمكن الاتصال بـ MariaDB" $?
else
    echo "🔧 محاولة إصلاح MariaDB..."
    sudo systemctl start mariadb || warn_service "فشل في تشغيل MariaDB"
fi

# فحص Redis
systemctl is-active redis > /dev/null 2>&1
if check_service "Redis يعمل" $?; then
    redis-cli ping > /dev/null 2>&1
    check_service "Redis يستجيب" $?
else
    echo "🔧 محاولة إصلاح Redis..."
    sudo systemctl start redis || warn_service "فشل في تشغيل Redis"
fi

# فحص Python و Frappe
echo ""
echo "🐍 فحص Python و Frappe:"

python3 --version > /dev/null 2>&1
check_service "Python 3 مثبت" $?

if [ -f "env/bin/python" ]; then
    check_service "بيئة Python الافتراضية موجودة" 0
else
    warn_service "بيئة Python الافتراضية مفقودة"
fi

# فحص العمليات
ps aux | grep -E "(frappe|bench)" | grep -v grep > /dev/null
check_service "عمليات Frappe تعمل" $?

# 2. فحص الموقع
echo ""
echo "🌐 فحص الموقع ($SITE_NAME):"

if [ -d "sites/$SITE_NAME" ]; then
    check_service "مجلد الموقع موجود" 0
    
    # فحص ملف التكوين
    if [ -f "sites/$SITE_NAME/site_config.json" ]; then
        check_service "ملف تكوين الموقع موجود" 0
    else
        warn_service "ملف تكوين الموقع مفقود"
    fi
    
    # فحص قاعدة البيانات
    bench --site $SITE_NAME list-apps > /dev/null 2>&1
    check_service "يمكن الاتصال بقاعدة بيانات الموقع" $?
    
else
    warn_service "مجلد الموقع مفقود: sites/$SITE_NAME"
fi

# 3. فحص المنافذ
echo ""
echo "🔌 فحص المنافذ:"

# فحص منفذ Frappe (8000)
if netstat -tuln | grep -q ":8000 "; then
    check_service "منفذ 8000 مفتوح" 0
else
    warn_service "منفذ 8000 مغلق - قد تحتاج لتشغيل bench start"
fi

# فحص منفذ MariaDB (3306)
if netstat -tuln | grep -q ":3306 "; then
    check_service "منفذ MariaDB (3306) مفتوح" 0
else
    warn_service "منفذ MariaDB مغلق"
fi

# فحص منفذ Redis (6379)
if netstat -tuln | grep -q ":6379 "; then
    check_service "منفذ Redis (6379) مفتوح" 0
else
    warn_service "منفذ Redis مغلق"
fi

# 4. فحص المساحة والذاكرة
echo ""
echo "💾 فحص الموارد:"

# فحص المساحة
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    check_service "مساحة القرص كافية (${DISK_USAGE}%)" 0
elif [ "$DISK_USAGE" -lt 90 ]; then
    warn_service "مساحة القرص منخفضة (${DISK_USAGE}%)"
else
    check_service "مساحة القرص ممتلئة (${DISK_USAGE}%)" 1
fi

# فحص الذاكرة
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ "$MEM_USAGE" -lt 80 ]; then
    check_service "استخدام الذاكرة طبيعي (${MEM_USAGE}%)" 0
elif [ "$MEM_USAGE" -lt 90 ]; then
    warn_service "استخدام الذاكرة مرتفع (${MEM_USAGE}%)"
else
    warn_service "استخدام الذاكرة مرتفع جداً (${MEM_USAGE}%)"
fi

# 5. فحص التطبيقات
echo ""
echo "📱 فحص التطبيقات المثبتة:"

if [ -d "sites/$SITE_NAME" ]; then
    APPS=$(bench --site $SITE_NAME list-apps 2>/dev/null || echo "")
    
    if echo "$APPS" | grep -q "frappe"; then
        check_service "Frappe مثبت" 0
    else
        warn_service "Frappe غير مثبت أو لا يعمل"
    fi
    
    if echo "$APPS" | grep -q "erpnext"; then
        check_service "ERPNext مثبت" 0
    else
        warn_service "ERPNext غير مثبت"
    fi
    
    if echo "$APPS" | grep -q "universal_workshop"; then
        check_service "Universal Workshop مثبت" 0
    else
        warn_service "Universal Workshop غير مثبت"
    fi
fi

# 6. اختبار الوصول للموقع
echo ""
echo "🌍 اختبار الوصول للموقع:"

if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000" | grep -q "200\|302"; then
    check_service "الموقع يستجيب على المنفذ 8000" 0
else
    warn_service "الموقع لا يستجيب - تحقق من تشغيل bench start"
fi

# النتيجة النهائية
echo ""
echo "========================================"
echo "📊 ملخص نتائج الفحص:"
echo "✅ نجح: $PASSED"
echo "❌ فشل: $FAILED" 
echo "⚠️ تحذيرات: $WARNINGS"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 النظام يعمل بشكل طبيعي!"
    if [ $WARNINGS -gt 0 ]; then
        echo "💡 يرجى مراجعة التحذيرات أعلاه"
    fi
else
    echo ""
    echo "🔧 المشاكل التي تحتاج إصلاح:"
    echo "   - تحقق من الخدمات المتوقفة"
    echo "   - تأكد من تشغيل bench start"
    echo "   - راجع سجلات الأخطاء: tail -f logs/*.log"
    
    echo ""
    echo "🆘 أوامر الإصلاح السريع:"
    echo "   sudo systemctl start mariadb redis"
    echo "   bench start"
    echo "   bench --site $SITE_NAME migrate"
fi

echo ""
echo "📝 للمزيد من التفاصيل، راجع:"
echo "   - سجلات النظام: tail -f logs/bench.log"
echo "   - سجلات الموقع: tail -f logs/frappe.log"
echo "   - حالة العمليات: bench doctor"
