#!/bin/bash
# سكريبت إنشاء رخصة للعميل - النسخة الآمنة مع دعم الترميز
# الاستخدام: ./generate_license_safe.sh [اسم_العميل] [معرف_العميل] [نوع_الرخصة]
# ملاحظة: رقم السجل التجاري والبريد الإلكتروني أصبحا اختياريين

# تعيين الترميز UTF-8 لدعم اللغة العربية
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

set -e

# متغيرات الألوان للمخرجات
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# دوال المساعدة
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# التحقق من دعم الترميز
check_encoding_support() {
    print_info "فحص دعم الترميز UTF-8..."
    
    # اختبار دعم الترميز العربي
    local test_text="ورشة تجريبية"
    local encoded_length=${#test_text}
    
    if [ "$encoded_length" -eq 0 ]; then
        print_error "فشل في التعامل مع النص العربي"
        print_info "جاري تعيين متغيرات الترميز..."
        export LANG=C.UTF-8
        export LC_ALL=C.UTF-8
    fi
    
    # التحقق من وجود locale UTF-8
    if ! locale -a 2>/dev/null | grep -q "utf8\|UTF-8"; then
        print_warning "UTF-8 locale قد لا يكون متوفراً"
        print_info "استخدام ترميز بديل..."
        export LANG=C.UTF-8
        export LC_ALL=C.UTF-8
    else
        print_success "دعم UTF-8 متوفر"
    fi
}

# التحقق من الأدوات المطلوبة
check_dependencies() {
    local missing_tools=()
    
    if ! command -v jq >/dev/null 2>&1; then
        missing_tools+=("jq")
    fi
    
    if ! command -v sha256sum >/dev/null 2>&1; then
        missing_tools+=("sha256sum")
    fi
    
    if ! command -v md5sum >/dev/null 2>&1; then
        missing_tools+=("md5sum")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        print_info "Please install them using: sudo apt-get install ${missing_tools[*]}"
        exit 1
    fi
}

# عرض المساعدة
show_usage() {
    cat << 'EOF'
🔐 Universal Workshop License Generator - Safe Version

الاستخدام:
./generate_license_safe.sh [اسم_العميل] [معرف_العميل] [نوع_الرخصة]

الأمثلة:
./generate_license_safe.sh "Alfarsi Workshop" ALFARSI-001 professional
./generate_license_safe.sh "ورشة الفارسي" ALFARSI-001 professional

📋 المتطلبات الإجبارية:
   - اسم الورشة (عربي + إنجليزي)
   - اسم المالك (عربي + إنجليزي)  
   - رقم الهوية المدنية (8 أرقام)
   - رقم الهاتف (+968 xxxxxxxx)

📋 المتطلبات الاختيارية:
   - رقم السجل التجاري (7 أرقام)
   - البريد الإلكتروني
   - العنوان

📝 أنواع الرخص المدعومة:
   - basic      (5 users, basic features)
   - professional (25 users, advanced features)
   - enterprise (100 users, full features)

🔧 خيارات إضافية:
   --dry-run    تشغيل تجريبي بدون إنشاء ملفات
   --help       عرض هذه المساعدة
   --check      فحص البيئة والأدوات المطلوبة

EOF
}

# التشغيل التجريبي
dry_run() {
    local client_name="$1"
    local client_id="$2"
    local license_type="$3"
    
    print_info "🧪 تشغيل تجريبي - لن يتم إنشاء أي ملفات"
    echo ""
    print_info "📊 معاينة البيانات التي سيتم إنشاؤها:"
    echo ""
    echo "Client Name: $client_name"
    echo "Client ID: $client_id"
    echo "License Type: $license_type"
    
    # تحديد الميزات حسب نوع الرخصة
    case "$license_type" in
        "basic")
            MAX_USERS=5
            FEATURES='["workshop_management", "basic_inventory"]'
            ;;
        "professional")
            MAX_USERS=25
            FEATURES='["workshop_management", "inventory", "scrap_management", "reports"]'
            ;;
        "enterprise")
            MAX_USERS=100
            FEATURES='["workshop_management", "inventory", "scrap_management", "reports", "api_access", "advanced_analytics"]'
            ;;
        *)
            print_error "نوع رخصة غير معروف: $license_type"
            echo "الأنواع المدعومة: basic, professional, enterprise"
            exit 1
            ;;
    esac
    
    ISSUE_DATE=$(date -Iseconds)
    EXPIRY_DATE=$(date -d "+100 years" -Iseconds)
    SUPPORT_UNTIL=$(date -d "+1 year" -Iseconds)
    
    echo "Max Users: $MAX_USERS"
    echo "Features: $FEATURES"
    echo "Issue Date: $ISSUE_DATE"
    echo "Expiry Date: $EXPIRY_DATE"
    echo "Support Until: $SUPPORT_UNTIL"
    echo ""
    
    # معاينة التوقيع
    signature=$(echo -n "$client_id$ISSUE_DATE" | sha256sum | cut -d' ' -f1)
    hash_value=$(echo -n "$client_name$client_id$license_type" | md5sum | cut -d' ' -f1)
    
    echo "Signature: $signature"
    echo "Hash: $hash_value"
    echo ""
    
    # معاينة أسماء الملفات
    license_file="licenses/${client_name// /_}_license.json"
    license_info_file="licenses/${client_name// /_}_license_info.txt"
    
    echo "License File: $license_file"
    echo "License Info File: $license_info_file"
    echo ""
    
    print_success "✅ التشغيل التجريبي مكتمل بنجاح"
    print_info "💡 لإنشاء الملفات الفعلية، قم بتشغيل السكريبت بدون --dry-run"
}

# معالجة المعاملات
CLIENT_NAME="$1"
CLIENT_ID="$2"
LICENSE_TYPE="${3:-professional}"
DRY_RUN=false

# التحقق من الخيارات الخاصة
for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        --check)
            print_info "🔍 فحص البيئة..."
            check_encoding_support
            check_dependencies
            print_success "✅ البيئة جاهزة للاستخدام"
            exit 0
            ;;
    esac
done

# التحقق من المعاملات المطلوبة
if [ -z "$CLIENT_NAME" ]; then
    print_error "اسم العميل مطلوب"
    show_usage
    exit 1
fi

# إنشاء معرف العميل إذا لم يتم توفيره
if [ -z "$CLIENT_ID" ]; then
    CLIENT_ID="${CLIENT_NAME// /-}-$(date +%Y%m%d)"
    CLIENT_ID=$(echo "$CLIENT_ID" | tr '[:lower:]' '[:upper:]')
fi

print_info "🔐 إنشاء رخصة جديدة للعميل: $CLIENT_NAME"
print_info "🆔 معرف العميل: $CLIENT_ID"
print_info "📝 نوع الرخصة: $LICENSE_TYPE"
echo ""

# فحص البيئة والأدوات
print_info "🔍 فحص البيئة..."
check_encoding_support
check_dependencies

# التشغيل التجريبي إذا تم طلبه
if [ "$DRY_RUN" = true ]; then
    dry_run "$CLIENT_NAME" "$CLIENT_ID" "$LICENSE_TYPE"
    exit 0
fi

# إنشاء مجلد الرخص إذا لم يكن موجوداً
mkdir -p licenses

# الحصول على التاريخ الحالي وتاريخ انتهاء الصلاحية
ISSUE_DATE=$(date -Iseconds)
EXPIRY_DATE=$(date -d "+100 years" -Iseconds)
SUPPORT_UNTIL=$(date -d "+1 year" -Iseconds)

# تحديد الميزات حسب نوع الرخصة
case "$LICENSE_TYPE" in
    "basic")
        MAX_USERS=5
        FEATURES='["workshop_management", "basic_inventory"]'
        ;;
    "professional")
        MAX_USERS=25
        FEATURES='["workshop_management", "inventory", "scrap_management", "reports"]'
        ;;
    "enterprise")
        MAX_USERS=100
        FEATURES='["workshop_management", "inventory", "scrap_management", "reports", "api_access", "advanced_analytics"]'
        ;;
    *)
        print_error "نوع رخصة غير معروف: $LICENSE_TYPE"
        echo "الأنواع المدعومة: basic, professional, enterprise"
        exit 1
        ;;
esac

# إنشاء ملف الرخصة
LICENSE_FILE="licenses/${CLIENT_NAME// /_}_license.json"
print_info "📄 إنشاء ملف الرخصة: $LICENSE_FILE"

cat > "$LICENSE_FILE" << EOF
{
  "license_data": {
    "client_name": "$CLIENT_NAME",
    "client_id": "$CLIENT_ID",
    "license_type": "$LICENSE_TYPE",
    "max_users": $MAX_USERS,
    "features": $FEATURES,
    "issue_date": "$ISSUE_DATE",
    "expiry_date": "$EXPIRY_DATE",
    "is_permanent": true,
    "version": "2.0",
    "support_until": "$SUPPORT_UNTIL"
  },
  "signature": "$(echo -n "$CLIENT_ID$ISSUE_DATE" | sha256sum | cut -d' ' -f1)",
  "hash": "$(echo -n "$CLIENT_NAME$CLIENT_ID$LICENSE_TYPE" | md5sum | cut -d' ' -f1)",
  "metadata": {
    "created_by": "$(whoami)",
    "created_on": "$(hostname)",
    "created_at": "$ISSUE_DATE",
    "script_version": "2.0-safe",
    "encoding": "UTF-8"
  }
}
EOF

# التحقق من صحة ملف JSON
if ! jq empty "$LICENSE_FILE" 2>/dev/null; then
    print_error "فشل في إنشاء ملف JSON صحيح"
    exit 1
fi

# إنشاء ملف معلومات الرخصة المقروء
LICENSE_INFO_FILE="licenses/${CLIENT_NAME// /_}_license_info.txt"
print_info "📋 إنشاء ملف معلومات الرخصة: $LICENSE_INFO_FILE"

cat > "$LICENSE_INFO_FILE" << EOF
معلومات رخصة العميل
==================

اسم العميل: $CLIENT_NAME
معرف العميل: $CLIENT_ID
نوع الرخصة: $LICENSE_TYPE
الحد الأقصى للمستخدمين: $MAX_USERS

تاريخ الإصدار: $(date -d "$ISSUE_DATE" '+%Y-%m-%d %H:%M:%S')
تاريخ انتهاء الصلاحية: دائمة
الدعم حتى: $(date -d "$SUPPORT_UNTIL" '+%Y-%m-%d')

الميزات المدعومة:
$(echo "$FEATURES" | jq -r '.[]' | sed 's/^/- /')

ملف الرخصة: $LICENSE_FILE

---
معلومات تقنية:
- إصدار السكريبت: 2.0-safe
- الترميز: UTF-8
- التوقيع: $(echo -n "$CLIENT_ID$ISSUE_DATE" | sha256sum | cut -d' ' -f1)
- الهاش: $(echo -n "$CLIENT_NAME$CLIENT_ID$LICENSE_TYPE" | md5sum | cut -d' ' -f1)
EOF

echo ""
print_success "✅ تم إنشاء الرخصة بنجاح:"
echo "   📄 ملف الرخصة: $LICENSE_FILE"
echo "   📋 معلومات الرخصة: $LICENSE_INFO_FILE"
echo ""
print_info "📋 ملخص الرخصة:"
echo "   👤 العميل: $CLIENT_NAME"
echo "   🆔 المعرف: $CLIENT_ID"
echo "   📝 النوع: $LICENSE_TYPE"
echo "   👥 المستخدمين: $MAX_USERS"
echo "   ⏰ الصلاحية: دائمة"
echo ""
print_success "🚀 الخطوة التالية: نسخ ملف الرخصة إلى موقع العميل"

# تسجيل العملية
echo "$(date -Iseconds): License created for $CLIENT_NAME ($CLIENT_ID) - Type: $LICENSE_TYPE" >> licenses/generation_log.txt
