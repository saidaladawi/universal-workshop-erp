#!/bin/bash
# سكريبت فحص البيئة الشامل لتوليد التراخيص
# يفحص جميع المتطلبات والإعدادات اللازمة

# تعيين الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

print_section() {
    echo -e "\n${BLUE}🔍 $1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "  ${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "  ${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "  ${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "  ${CYAN}ℹ️  $1${NC}"
}

# متغيرات النتائج
OVERALL_STATUS="PASS"
ERRORS=0
WARNINGS=0

check_system_info() {
    print_section "معلومات النظام"
    
    print_info "نظام التشغيل: $(uname -s)"
    print_info "إصدار النظام: $(uname -r)"
    print_info "المعمارية: $(uname -m)"
    print_info "المضيف: $(hostname)"
    print_info "المستخدم: $(whoami)"
    print_info "المجلد الحالي: $(pwd)"
    print_info "التاريخ: $(date)"
}

check_shell_environment() {
    print_section "بيئة Shell"
    
    print_info "Shell المستخدم: $SHELL"
    print_info "إصدار Bash: $BASH_VERSION"
    
    # فحص متغيرات البيئة المهمة
    if [ -n "$LANG" ]; then
        print_success "LANG: $LANG"
    else
        print_warning "متغير LANG غير محدد"
        ((WARNINGS++))
    fi
    
    if [ -n "$LC_ALL" ]; then
        print_success "LC_ALL: $LC_ALL"
    else
        print_info "LC_ALL: غير محدد (هذا طبيعي)"
    fi
    
    # فحص PATH
    if echo "$PATH" | grep -q "/usr/bin"; then
        print_success "PATH يحتوي على /usr/bin"
    else
        print_error "PATH لا يحتوي على /usr/bin"
        ((ERRORS++))
    fi
}

check_locale_support() {
    print_section "دعم اللغات والترميز"
    
    # فحص locale المتاحة
    if command -v locale >/dev/null 2>&1; then
        print_success "أمر locale متوفر"
        
        # البحث عن UTF-8 locales
        local utf8_locales=$(locale -a 2>/dev/null | grep -i utf | head -5)
        if [ -n "$utf8_locales" ]; then
            print_success "UTF-8 locales متوفرة:"
            echo "$utf8_locales" | while read -r line; do
                print_info "  - $line"
            done
        else
            print_warning "لم يتم العثور على UTF-8 locales"
            ((WARNINGS++))
        fi
        
        # فحص locale الحالي
        local current_locale=$(locale 2>/dev/null | grep LANG | cut -d= -f2 | tr -d '"')
        if echo "$current_locale" | grep -qi utf; then
            print_success "Locale الحالي يدعم UTF-8: $current_locale"
        else
            print_warning "Locale الحالي قد لا يدعم UTF-8: $current_locale"
            ((WARNINGS++))
        fi
    else
        print_error "أمر locale غير متوفر"
        ((ERRORS++))
    fi
}

check_required_tools() {
    print_section "الأدوات المطلوبة"
    
    local tools=("jq" "sha256sum" "md5sum" "date" "cat" "mkdir" "echo" "cut" "tr" "sed")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" >/dev/null 2>&1; then
            local version_info=""
            case "$tool" in
                "jq")
                    version_info=" ($(jq --version 2>/dev/null || echo 'version unknown'))"
                    ;;
                "date")
                    version_info=" (GNU coreutils)"
                    ;;
            esac
            print_success "$tool متوفر$version_info"
        else
            print_error "$tool غير متوفر"
            missing_tools+=("$tool")
            ((ERRORS++))
        fi
    done
    
    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "أدوات مفقودة: ${missing_tools[*]}"
        print_info "لتثبيتها: sudo apt-get install ${missing_tools[*]}"
    fi
}

check_arabic_text_support() {
    print_section "دعم النصوص العربية"
    
    # اختبار النص العربي الأساسي
    local arabic_text="ورشة الفارسي للسيارات"
    local text_length=${#arabic_text}
    
    if [ "$text_length" -gt 0 ]; then
        print_success "يمكن التعامل مع النص العربي (طول: $text_length)"
        print_info "نص الاختبار: $arabic_text"
    else
        print_error "فشل في التعامل مع النص العربي"
        ((ERRORS++))
    fi
    
    # اختبار استبدال المسافات
    local safe_name="${arabic_text// /_}"
    if [ "$safe_name" != "$arabic_text" ]; then
        print_success "استبدال المسافات يعمل: $safe_name"
    else
        print_warning "مشكلة في استبدال المسافات"
        ((WARNINGS++))
    fi
    
    # اختبار التشفير
    if command -v sha256sum >/dev/null 2>&1; then
        local hash=$(echo -n "$arabic_text" | sha256sum 2>/dev/null | cut -d' ' -f1)
        if [ ${#hash} -eq 64 ]; then
            print_success "تشفير SHA256 للنص العربي: ${hash:0:16}..."
        else
            print_error "فشل في تشفير النص العربي"
            ((ERRORS++))
        fi
    fi
}

check_json_creation() {
    print_section "إنشاء ملفات JSON"
    
    local test_file="/tmp/license_test_$$"
    local test_name="ورشة اختبار"
    local test_id="TEST-001"
    
    # إنشاء ملف JSON اختباري
    cat > "$test_file" << EOF
{
  "license_data": {
    "client_name": "$test_name",
    "client_id": "$test_id",
    "license_type": "test",
    "max_users": 5,
    "features": ["test_feature"],
    "issue_date": "$(date -Iseconds)",
    "is_permanent": true
  },
  "signature": "$(echo -n "${test_id}$(date -Iseconds)" | sha256sum 2>/dev/null | cut -d' ' -f1)",
  "hash": "$(echo -n "${test_name}${test_id}test" | md5sum 2>/dev/null | cut -d' ' -f1)"
}
EOF
    
    if [ -f "$test_file" ]; then
        print_success "تم إنشاء ملف اختباري"
        
        # فحص صحة JSON
        if command -v jq >/dev/null 2>&1; then
            if jq empty "$test_file" 2>/dev/null; then
                print_success "ملف JSON صحيح"
            else
                print_error "ملف JSON غير صحيح"
                ((ERRORS++))
            fi
        else
            print_warning "لا يمكن فحص صحة JSON - jq غير متوفر"
            ((WARNINGS++))
        fi
        
        # عرض محتوى الملف
        print_info "محتوى الملف:"
        if command -v jq >/dev/null 2>&1; then
            jq . "$test_file" 2>/dev/null | head -10 | sed 's/^/    /'
        else
            head -10 "$test_file" | sed 's/^/    /'
        fi
        
        # حذف الملف الاختباري
        rm -f "$test_file"
    else
        print_error "فشل في إنشاء ملف اختباري"
        ((ERRORS++))
    fi
}

check_file_permissions() {
    print_section "صلاحيات الملفات"
    
    local current_dir=$(pwd)
    if [ -w "$current_dir" ]; then
        print_success "يمكن الكتابة في المجلد الحالي"
    else
        print_error "لا يمكن الكتابة في المجلد الحالي"
        ((ERRORS++))
    fi
    
    # فحص مجلد licenses
    if [ -d "licenses" ]; then
        if [ -w "licenses" ]; then
            print_success "يمكن الكتابة في مجلد licenses"
        else
            print_error "لا يمكن الكتابة في مجلد licenses"
            ((ERRORS++))
        fi
    else
        print_info "مجلد licenses غير موجود (سيتم إنشاؤه)"
        if mkdir -p licenses 2>/dev/null; then
            print_success "تم إنشاء مجلد licenses بنجاح"
            rmdir licenses 2>/dev/null
        else
            print_error "فشل في إنشاء مجلد licenses"
            ((ERRORS++))
        fi
    fi
}

check_script_files() {
    print_section "ملفات السكريبت"
    
    local scripts=("generate_license.sh" "generate_license_safe.sh")
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                print_success "$script موجود وقابل للتنفيذ"
            else
                print_warning "$script موجود لكن غير قابل للتنفيذ"
                print_info "لإصلاحه: chmod +x $script"
                ((WARNINGS++))
            fi
        else
            print_info "$script غير موجود"
        fi
    done
}

generate_report() {
    print_header "تقرير النتائج النهائي"
    
    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        print_success "جميع الفحوصات مرت بنجاح! البيئة جاهزة تماماً"
        OVERALL_STATUS="EXCELLENT"
    elif [ $ERRORS -eq 0 ]; then
        print_warning "هناك $WARNINGS تحذير(ات) لكن البيئة قابلة للاستخدام"
        OVERALL_STATUS="GOOD"
    else
        print_error "هناك $ERRORS خطأ(أخطاء) يجب إصلاحها"
        OVERALL_STATUS="NEEDS_FIXES"
    fi
    
    echo ""
    print_info "ملخص النتائج:"
    print_info "  - الأخطاء: $ERRORS"
    print_info "  - التحذيرات: $WARNINGS"
    print_info "  - الحالة العامة: $OVERALL_STATUS"
    
    if [ $ERRORS -gt 0 ]; then
        echo ""
        print_error "يُنصح بإصلاح الأخطاء قبل استخدام سكريبت توليد التراخيص"
    fi
}

# تشغيل جميع الفحوصات
main() {
    print_header "فحص البيئة الشامل لتوليد التراخيص"
    
    check_system_info
    check_shell_environment
    check_locale_support
    check_required_tools
    check_arabic_text_support
    check_json_creation
    check_file_permissions
    check_script_files
    
    generate_report
}

# تشغيل الفحص
main "$@"
