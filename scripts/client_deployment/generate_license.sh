#!/bin/bash
# سكريبت إنشاء رخصة للعميل
# الاستخدام: ./generate_license.sh [اسم_العميل] [معرف_العميل] [نوع_الرخصة]

set -e

CLIENT_NAME="$1"
CLIENT_ID="$2"
LICENSE_TYPE="${3:-professional}"

if [ -z "$CLIENT_NAME" ]; then
    echo "❌ الاستخدام: ./generate_license.sh [اسم_العميل] [معرف_العميل] [نوع_الرخصة]"
    echo "مثال: ./generate_license.sh 'ورشة الفارسي' ALFARSI-001 professional"
    exit 1
fi

# إنشاء معرف العميل إذا لم يتم توفيره
if [ -z "$CLIENT_ID" ]; then
    CLIENT_ID="${CLIENT_NAME// /-}-$(date +%Y%m%d)"
    CLIENT_ID=$(echo "$CLIENT_ID" | tr '[:lower:]' '[:upper:]')
fi

echo "🔐 إنشاء رخصة جديدة للعميل: $CLIENT_NAME"
echo "🆔 معرف العميل: $CLIENT_ID"
echo "📝 نوع الرخصة: $LICENSE_TYPE"

# إنشاء مجلد الرخص إذا لم يكن موجوداً
mkdir -p licenses

# الحصول على التاريخ الحالي وتاريخ انتهاء الصلاحية
ISSUE_DATE=$(date -Iseconds)
EXPIRY_DATE=$(date -d "+100 years" -Iseconds)
SUPPORT_UNTIL=$(date -d "+1 year" -Iseconds)

# تحديد الميزات حسب نوع الرخصة
if [ "$LICENSE_TYPE" = "basic" ]; then
    MAX_USERS=5
    FEATURES='["workshop_management", "basic_inventory"]'
elif [ "$LICENSE_TYPE" = "professional" ]; then
    MAX_USERS=25
    FEATURES='["workshop_management", "inventory", "scrap_management", "reports"]'
elif [ "$LICENSE_TYPE" = "enterprise" ]; then
    MAX_USERS=100
    FEATURES='["workshop_management", "inventory", "scrap_management", "reports", "api_access", "advanced_analytics"]'
else
    echo "❌ نوع رخصة غير معروف: $LICENSE_TYPE"
    echo "الأنواع المدعومة: basic, professional, enterprise"
    exit 1
fi

# إنشاء ملف الرخصة
LICENSE_FILE="licenses/${CLIENT_NAME// /_}_license.json"
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
    "created_at": "$ISSUE_DATE"
  }
}
EOF

# إنشاء ملف معلومات الرخصة المقروء
LICENSE_INFO_FILE="licenses/${CLIENT_NAME// /_}_license_info.txt"
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
EOF

echo "✅ تم إنشاء الرخصة بنجاح:"
echo "   📄 ملف الرخصة: $LICENSE_FILE"
echo "   📋 معلومات الرخصة: $LICENSE_INFO_FILE"
echo ""
echo "📋 ملخص الرخصة:"
echo "   👤 العميل: $CLIENT_NAME"
echo "   🆔 المعرف: $CLIENT_ID"
echo "   📝 النوع: $LICENSE_TYPE"
echo "   👥 المستخدمين: $MAX_USERS"
echo "   ⏰ الصلاحية: دائمة"
echo ""
echo "🚀 الخطوة التالية: نسخ ملف الرخصة إلى موقع العميل"
