#!/bin/bash
# السكريپت الرئيسي لتسليم العميل
# الاستخدام: ./deploy_client.sh [العملية] [المعاملات...]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_NAME=""
SITE_NAME=""
LICENSE_TYPE="professional"

# عرض المساعدة
show_help() {
    cat << EOF
🚀 سكريپت تسليم العميل - Universal Workshop ERP v2.0
========================================================

الاستخدام: $0 [العملية] [المعاملات...]

العمليات المتاحة:

📋 إدارة العميل:
  new-client      إنشاء عميل جديد كاملاً
  check-system    فحص حالة النظام
  generate-license إنشاء رخصة للعميل

🔧 إدارة النظام:
  setup-backup    إعداد النسخ الاحتياطية
  restore-backup  استعادة نسخة احتياطية
  monitor         بدء مراقبة النظام

📊 التسليم:
  delivery-check  فحص التسليم النهائي
  full-setup      إعداد كامل للعميل

📚 المساعدة:
  help           عرض هذه المساعدة
  list-sites     عرض المواقع المتاحة
  list-backups   عرض النسخ الاحتياطية

أمثلة:
  $0 new-client "ورشة الفارسي" "alfarsi.local" "professional"
  $0 check-system universal.local
  $0 delivery-check "ورشة الفارسي" alfarsi.local
  $0 monitor universal.local 30

للمزيد من المعلومات راجع: README.md
EOF
}

# دالة لطباعة الرسائل الملونة
print_info() { echo -e "\033[36mℹ️ $1\033[0m"; }
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️ $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_step() { echo -e "\033[35m🔄 $1\033[0m"; }

# دالة للتحقق من وجود السكريپت
check_script() {
    local script_name="$1"
    if [ ! -f "$SCRIPT_DIR/$script_name" ]; then
        print_error "السكريپت غير موجود: $script_name"
        exit 1
    fi
    
    if [ ! -x "$SCRIPT_DIR/$script_name" ]; then
        print_warning "السكريپت غير قابل للتنفيذ، جاري إصلاحه..."
        chmod +x "$SCRIPT_DIR/$script_name"
    fi
}

# دالة إنشاء عميل جديد كاملاً
new_client() {
    CLIENT_NAME="$1"
    SITE_NAME="$2"
    LICENSE_TYPE="${3:-professional}"
    
    if [ -z "$CLIENT_NAME" ] || [ -z "$SITE_NAME" ]; then
        print_error "معاملات مطلوبة: اسم العميل ونطاق الموقع"
        echo "الاستخدام: $0 new-client 'اسم العميل' 'نطاق.local' [نوع الرخصة]"
        exit 1
    fi
    
    print_info "بدء إعداد عميل جديد: $CLIENT_NAME"
    echo "=================================================="
    
    # 1. فحص النظام أولاً
    print_step "فحص حالة النظام..."
    check_script "system_check.sh"
    if ! "$SCRIPT_DIR/system_check.sh" "$SITE_NAME"; then
        print_error "يجب إصلاح مشاكل النظام قبل المتابعة"
        exit 1
    fi
    
    # 2. إنشاء الموقع
    print_step "إنشاء موقع العميل..."
    check_script "create_client_site.sh"
    "$SCRIPT_DIR/create_client_site.sh" "$CLIENT_NAME" "$SITE_NAME"
    
    # 3. إنشاء الرخصة
    print_step "إنشاء رخصة العميل..."
    check_script "generate_license.sh"
    "$SCRIPT_DIR/generate_license.sh" "$CLIENT_NAME" "${CLIENT_NAME// /-}-$(date +%Y%m%d)" "$LICENSE_TYPE"
    
    # 4. إعداد النسخ الاحتياطية
    print_step "إعداد النسخ الاحتياطية..."
    check_script "setup_backup.sh"
    "$SCRIPT_DIR/setup_backup.sh" "$SITE_NAME"
    
    # 5. فحص التسليم
    print_step "فحص التسليم النهائي..."
    check_script "delivery_checklist.sh"
    "$SCRIPT_DIR/delivery_checklist.sh" "$CLIENT_NAME" "$SITE_NAME"
    
    print_success "تم إنشاء العميل بنجاح!"
    echo ""
    print_info "الخطوات التالية:"
    echo "  1. تدريب فريق العميل"
    echo "  2. إدخال البيانات الأولية"
    echo "  3. اختبار النظام مع العميل"
    echo "  4. توقيع التسليم النهائي"
}

# دالة الإعداد الكامل
full_setup() {
    CLIENT_NAME="$1"
    SITE_NAME="$2"
    
    if [ -z "$CLIENT_NAME" ] || [ -z "$SITE_NAME" ]; then
        print_error "معاملات مطلوبة: اسم العميل ونطاق الموقع"
        exit 1
    fi
    
    print_info "بدء الإعداد الكامل للعميل: $CLIENT_NAME"
    
    # تشغيل جميع السكريپتات
    new_client "$CLIENT_NAME" "$SITE_NAME" "$LICENSE_TYPE"
    
    # بدء المراقبة في الخلفية
    print_step "بدء مراقبة النظام..."
    check_script "monitor_system.sh"
    nohup "$SCRIPT_DIR/monitor_system.sh" "$SITE_NAME" 60 > /dev/null 2>&1 &
    MONITOR_PID=$!
    
    print_success "تم الإعداد الكامل بنجاح!"
    print_info "PID لمراقبة النظام: $MONITOR_PID"
    echo "لإيقاف المراقبة: kill $MONITOR_PID"
}

# دالة عرض المواقع المتاحة
list_sites() {
    print_info "المواقع المتاحة:"
    
    if [ -d "sites" ]; then
        for site in sites/*/; do
            if [ -d "$site" ]; then
                site_name=$(basename "$site")
                if [ "$site_name" != "assets" ] && [ "$site_name" != "apps" ]; then
                    # التحقق من حالة الموقع
                    if bench --site "$site_name" list-apps > /dev/null 2>&1; then
                        status="✅ يعمل"
                    else
                        status="❌ خطأ"
                    fi
                    
                    echo "  📍 $site_name - $status"
                fi
            fi
        done
    else
        print_warning "مجلد sites غير موجود"
    fi
}

# دالة عرض النسخ الاحتياطية
list_backups() {
    print_info "النسخ الاحتياطية المتاحة:"
    
    BACKUP_DIR="$HOME/backups"
    if [ -d "$BACKUP_DIR" ]; then
        for backup_type in daily weekly monthly; do
            if [ -d "$BACKUP_DIR/$backup_type" ]; then
                echo "  📁 $backup_type:"
                ls -la "$BACKUP_DIR/$backup_type"/*.sql.gz 2>/dev/null | head -3 | while read -r line; do
                    echo "    $line"
                done
                echo ""
            fi
        done
    else
        print_warning "مجلد النسخ الاحتياطية غير موجود: $BACKUP_DIR"
    fi
}

# المعالج الرئيسي
main() {
    local operation="$1"
    shift
    
    # التحقق من وجود bench
    if ! command -v bench &> /dev/null; then
        print_error "bench غير مثبت أو غير متاح في PATH"
        exit 1
    fi
    
    # التحقق من وجود مجلد frappe-bench
    if [ ! -d "sites" ]; then
        print_error "يجب تشغيل السكريپت من داخل مجلد frappe-bench"
        exit 1
    fi
    
    case "$operation" in
        "new-client")
            new_client "$@"
            ;;
        "check-system")
            check_script "system_check.sh"
            "$SCRIPT_DIR/system_check.sh" "$@"
            ;;
        "generate-license")
            check_script "generate_license.sh"
            "$SCRIPT_DIR/generate_license.sh" "$@"
            ;;
        "setup-backup")
            check_script "setup_backup.sh"
            "$SCRIPT_DIR/setup_backup.sh" "$@"
            ;;
        "restore-backup")
            check_script "restore_backup.sh"
            "$SCRIPT_DIR/restore_backup.sh" "$@"
            ;;
        "monitor")
            check_script "monitor_system.sh"
            "$SCRIPT_DIR/monitor_system.sh" "$@"
            ;;
        "delivery-check")
            check_script "delivery_checklist.sh"
            "$SCRIPT_DIR/delivery_checklist.sh" "$@"
            ;;
        "full-setup")
            full_setup "$@"
            ;;
        "list-sites")
            list_sites
            ;;
        "list-backups")
            list_backups
            ;;
        "help"|"--help"|"-h"|"")
            show_help
            ;;
        *)
            print_error "عملية غير معروفة: $operation"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# تشغيل المعالج الرئيسي
main "$@"
