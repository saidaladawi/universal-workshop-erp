#!/bin/bash
# سكريبت اختبار ترميز اللغة العربية
# يختبر إمكانية التعامل مع النصوص العربية في البيئة الحالية

# تعيين الترميز
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

echo "=== اختبار ترميز اللغة العربية ==="
echo ""

# اختبار الترميز الأساسي
echo "1. اختبار النص العربي:"
echo "   النص: مرحبا بك في Universal Workshop ERP"
echo "   Test: This is Arabic text mixed with English"
echo ""

# اختبار متغيرات Shell
ARABIC_TEXT="ورشة الفارسي للسيارات"
echo "2. اختبار المتغيرات:"
echo "   متغير عربي: $ARABIC_TEXT"
echo "   طول النص: ${#ARABIC_TEXT}"
echo ""

# اختبار استبدال المسافات
SAFE_NAME="${ARABIC_TEXT// /_}"
echo "3. اختبار استبدال المسافات:"
echo "   الأصلي: $ARABIC_TEXT"
echo "   المعدل: $SAFE_NAME"
echo ""

# اختبار إنشاء ملف
TEST_FILE="/tmp/arabic_test_$$"
echo "4. اختبار إنشاء ملف:"
cat > "$TEST_FILE" << 'EOF'
{
  "test": "اختبار النص العربي",
  "workshop": "ورشة الفارسي",
  "mixed": "Mixed Arabic العربية and English text"
}
EOF

if [ -f "$TEST_FILE" ]; then
    echo "   ✅ تم إنشاء الملف بنجاح"
    echo "   محتوى الملف:"
    cat "$TEST_FILE" | sed 's/^/      /'
    rm -f "$TEST_FILE"
else
    echo "   ❌ فشل في إنشاء الملف"
fi
echo ""

# اختبار أدوات التشفير
echo "5. اختبار أدوات التشفير:"
if command -v sha256sum >/dev/null 2>&1; then
    HASH=$(echo -n "$ARABIC_TEXT" | sha256sum | cut -d' ' -f1)
    echo "   SHA256: ${HASH:0:16}..."
else
    echo "   ❌ sha256sum غير متوفر"
fi

if command -v md5sum >/dev/null 2>&1; then
    MD5=$(echo -n "$ARABIC_TEXT" | md5sum | cut -d' ' -f1)
    echo "   MD5: ${MD5:0:16}..."
else
    echo "   ❌ md5sum غير متوفر"
fi
echo ""

# اختبار JSON
echo "6. اختبار JSON:"
if command -v jq >/dev/null 2>&1; then
    JSON_TEST='{"name": "'"$ARABIC_TEXT"'", "type": "test"}'
    echo "   JSON: $JSON_TEST"
    if echo "$JSON_TEST" | jq empty 2>/dev/null; then
        echo "   ✅ JSON صحيح"
    else
        echo "   ❌ JSON غير صحيح"
    fi
else
    echo "   ⚠️  jq غير متوفر - سيتم تثبيته إذا لزم الأمر"
fi
echo ""

echo "=== انتهى الاختبار ==="
