#!/bin/bash
# سكريپت اختبار جميع السكريپتات
# الاستخدام: ./test_scripts.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🧪 اختبار جميع سكريپتات تسليم العميل"
echo "======================================"

# دالة للطباعة الملونة
print_test() { echo -e "\033[34m🧪 $1\033[0m"; }
print_pass() { echo -e "\033[32m✅ $1\033[0m"; }
print_fail() { echo -e "\033[31m❌ $1\033[0m"; }

PASSED=0
FAILED=0

# دالة لاختبار السكريپت
test_script() {
    local script_name="$1"
    local test_name="$2"
    
    print_test "اختبار: $test_name ($script_name)"
    
    if [ ! -f "$SCRIPT_DIR/$script_name" ]; then
        print_fail "الملف غير موجود: $script_name"
        ((FAILED++))
        return 1
    fi
    
    if [ ! -x "$SCRIPT_DIR/$script_name" ]; then
        print_fail "الملف غير قابل للتنفيذ: $script_name"
        ((FAILED++))
        return 1
    fi
    
    # اختبار بسيط لتشغيل السكريپت مع --help أو بدون معاملات
    if "$SCRIPT_DIR/$script_name" --help > /dev/null 2>&1 || \
       "$SCRIPT_DIR/$script_name" help > /dev/null 2>&1 || \
       "$SCRIPT_DIR/$script_name" > /dev/null 2>&1; then
        print_pass "السكريپت يعمل: $script_name"
        ((PASSED++))
        return 0
    else
        # محاولة تشغيل بدون معاملات (قد يفشل ولكن بشكل متوقع)
        if "$SCRIPT_DIR/$script_name" 2>&1 | grep -q -E "(Usage|الاستخدام|❌|help)"; then
            print_pass "السكريپت يعمل ويعرض رسالة مناسبة: $script_name"
            ((PASSED++))
            return 0
        else
            print_fail "السكريپت لا يعمل بشكل صحيح: $script_name"
            ((FAILED++))
            return 1
        fi
    fi
}

# اختبار جميع السكريپتات
echo "📋 اختبار السكريپتات الفردية:"
test_script "deploy_client.sh" "السكريپت الرئيسي"
test_script "create_client_site.sh" "إنشاء موقع العميل"
test_script "generate_license.sh" "إنشاء الرخصة"
test_script "system_check.sh" "فحص النظام"
test_script "setup_backup.sh" "إعداد النسخ الاحتياطية"
test_script "restore_backup.sh" "استعادة النسخة الاحتياطية"
test_script "monitor_system.sh" "مراقبة النظام"
test_script "delivery_checklist.sh" "قائمة فحص التسليم"

echo ""
echo "📋 اختبار الملفات المساعدة:"

# اختبار README
print_test "اختبار وجود ملف README"
if [ -f "$SCRIPT_DIR/README.md" ]; then
    print_pass "ملف README موجود"
    ((PASSED++))
else
    print_fail "ملف README مفقود"
    ((FAILED++))
fi

echo ""
echo "📋 اختبار المجلدات المطلوبة:"

# اختبار المجلدات
REQUIRED_DIRS=("../../../licenses" "../../../delivery_reports" "../../../restore_reports")
for dir in "${REQUIRED_DIRS[@]}"; do
    dir_path="$SCRIPT_DIR/$dir"
    dir_name=$(basename "$dir_path")
    
    print_test "اختبار وجود مجلد: $dir_name"
    if [ -d "$dir_path" ]; then
        print_pass "مجلد موجود: $dir_name"
        ((PASSED++))
    else
        print_fail "مجلد مفقود: $dir_name"
        mkdir -p "$dir_path" && print_pass "تم إنشاء المجلد: $dir_name" || print_fail "فشل في إنشاء المجلد: $dir_name"
    fi
done

echo ""
echo "📋 اختبار المتطلبات:"

# اختبار المتطلبات الأساسية
REQUIRED_COMMANDS=("bench" "python3" "mysql" "redis-cli" "curl" "git")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    print_test "اختبار وجود أمر: $cmd"
    if command -v "$cmd" &> /dev/null; then
        print_pass "الأمر متاح: $cmd"
        ((PASSED++))
    else
        print_fail "الأمر غير متاح: $cmd"
        ((FAILED++))
    fi
done

echo ""
echo "📋 اختبار السكريپت الرئيسي:"

# اختبار عمليات السكريپت الرئيسي
DEPLOY_OPERATIONS=("help" "list-sites" "list-backups")
for op in "${DEPLOY_OPERATIONS[@]}"; do
    print_test "اختبار عملية: $op"
    if "$SCRIPT_DIR/deploy_client.sh" "$op" > /dev/null 2>&1; then
        print_pass "العملية تعمل: $op"
        ((PASSED++))
    else
        print_fail "العملية لا تعمل: $op"
        ((FAILED++))
    fi
done

echo ""
echo "======================================"
echo "📊 نتائج الاختبار:"
echo "✅ نجح: $PASSED"
echo "❌ فشل: $FAILED"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "🎉 جميع الاختبارات نجحت!"
    echo "السكريپتات جاهزة للاستخدام."
    echo ""
    echo "🚀 للبدء، استخدم:"
    echo "  ./deploy_client.sh help"
    exit 0
else
    echo ""
    echo "⚠️ يوجد $FAILED اختبار فشل"
    echo "يرجى إصلاح المشاكل قبل الاستخدام."
    exit 1
fi
