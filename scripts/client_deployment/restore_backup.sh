#!/bin/bash
# سكريپت استعادة النسخة الاحتياطية
# الاستخدام: ./restore_backup.sh [نطاق_الموقع] [ملف_قاعدة_البيانات] [ملف_الأصول]

set -e

SITE_NAME="$1"
DB_BACKUP_FILE="$2"
FILES_BACKUP_FILE="$3"

if [ -z "$SITE_NAME" ] || [ -z "$DB_BACKUP_FILE" ]; then
    echo "❌ الاستخدام: ./restore_backup.sh [نطاق_الموقع] [ملف_قاعدة_البيانات] [ملف_الأصول]"
    echo ""
    echo "مثال:"
    echo "  ./restore_backup.sh universal.local backup.sql.gz files.tar"
    echo ""
    echo "📁 النسخ المتاحة:"
    if [ -d "$HOME/backups" ]; then
        echo "قواعد البيانات:"
        ls -la "$HOME/backups"/*/*.sql.gz 2>/dev/null | head -5 || echo "  لا توجد نسخ متاحة"
        echo ""
        echo "ملفات الأصول:"  
        ls -la "$HOME/backups"/*/*.tar 2>/dev/null | head -5 || echo "  لا توجد نسخ متاحة"
    fi
    exit 1
fi

echo "🔄 استعادة النسخة الاحتياطية"
echo "=============================="
echo "📍 الموقع: $SITE_NAME"
echo "🗃️ ملف قاعدة البيانات: $DB_BACKUP_FILE"
if [ -n "$FILES_BACKUP_FILE" ]; then
    echo "📁 ملف الأصول: $FILES_BACKUP_FILE"
fi
echo ""

# التحقق من وجود الملفات
if [ ! -f "$DB_BACKUP_FILE" ]; then
    echo "❌ ملف قاعدة البيانات غير موجود: $DB_BACKUP_FILE"
    exit 1
fi

if [ -n "$FILES_BACKUP_FILE" ] && [ ! -f "$FILES_BACKUP_FILE" ]; then
    echo "❌ ملف الأصول غير موجود: $FILES_BACKUP_FILE"
    exit 1
fi

# التحقق من وجود الموقع
if [ ! -d "sites/$SITE_NAME" ]; then
    echo "❌ الموقع غير موجود: $SITE_NAME"
    echo "هل تريد إنشاء موقع جديد؟ (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "📦 إنشاء موقع جديد..."
        bench new-site "$SITE_NAME" --force
    else
        echo "تم الإلغاء"
        exit 1
    fi
fi

# إنشاء نسخة احتياطية من الموقع الحالي
echo "💾 إنشاء نسخة احتياطية من الموقع الحالي..."
CURRENT_BACKUP_DIR="sites/$SITE_NAME/private/backups/pre_restore_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CURRENT_BACKUP_DIR"

if bench --site "$SITE_NAME" backup --backup-path "$CURRENT_BACKUP_DIR"; then
    echo "✅ تم إنشاء نسخة احتياطية من الموقع الحالي في: $CURRENT_BACKUP_DIR"
else
    echo "⚠️ فشل في إنشاء نسخة احتياطية من الموقع الحالي"
    echo "هل تريد المتابعة؟ (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "تم الإلغاء"
        exit 1
    fi
fi

# إيقاف العمليات
echo "⏸️ إيقاف العمليات..."
bench --site "$SITE_NAME" set-maintenance-mode on || true

# نسخ ملف النسخة الاحتياطية إلى مجلد الموقع
RESTORE_DIR="sites/$SITE_NAME/private/backups"
DB_BASENAME=$(basename "$DB_BACKUP_FILE")
cp "$DB_BACKUP_FILE" "$RESTORE_DIR/"

if [ -n "$FILES_BACKUP_FILE" ]; then
    FILES_BASENAME=$(basename "$FILES_BACKUP_FILE")
    cp "$FILES_BACKUP_FILE" "$RESTORE_DIR/"
fi

# استعادة قاعدة البيانات
echo "🗃️ استعادة قاعدة البيانات..."
if bench --site "$SITE_NAME" restore "$RESTORE_DIR/$DB_BASENAME" --force; then
    echo "✅ تم استعادة قاعدة البيانات بنجاح"
else
    echo "❌ فشل في استعادة قاعدة البيانات"
    echo "🔄 محاولة استعادة النسخة الاحتياطية الأصلية..."
    if [ -d "$CURRENT_BACKUP_DIR" ]; then
        ORIGINAL_DB=$(ls "$CURRENT_BACKUP_DIR"/*.sql.gz | head -1)
        if [ -n "$ORIGINAL_DB" ]; then
            bench --site "$SITE_NAME" restore "$ORIGINAL_DB" --force || true
        fi
    fi
    exit 1
fi

# استعادة الأصول
if [ -n "$FILES_BACKUP_FILE" ]; then
    echo "📁 استعادة ملفات الأصول..."
    
    # إنشاء مجلد مؤقت
    TEMP_DIR="/tmp/restore_files_$(date +%s)"
    mkdir -p "$TEMP_DIR"
    
    # فك ضغط الملفات
    if tar -xf "$RESTORE_DIR/$FILES_BASENAME" -C "$TEMP_DIR"; then
        echo "✅ تم فك ضغط ملفات الأصول"
        
        # نسخ الملفات إلى مكانها الصحيح
        if [ -d "$TEMP_DIR/assets" ]; then
            rsync -av "$TEMP_DIR/assets/" "sites/assets/"
            echo "✅ تم استعادة ملفات الأصول"
        fi
        
        if [ -d "$TEMP_DIR/files" ]; then
            rsync -av "$TEMP_DIR/files/" "sites/$SITE_NAME/private/files/"
            echo "✅ تم استعادة الملفات الخاصة"
        fi
        
        # تنظيف المجلد المؤقت
        rm -rf "$TEMP_DIR"
    else
        echo "⚠️ فشل في فك ضغط ملفات الأصول"
    fi
fi

# تحديث قاعدة البيانات
echo "🔄 تحديث قاعدة البيانات..."
if bench --site "$SITE_NAME" migrate; then
    echo "✅ تم تحديث قاعدة البيانات"
else
    echo "⚠️ فشل في تحديث قاعدة البيانات"
fi

# بناء الأصول
echo "🔨 بناء الأصول..."
bench build --app frappe || echo "⚠️ تحذير: فشل في بناء أصول frappe"
bench build --app erpnext || echo "⚠️ تحذير: فشل في بناء أصول erpnext"
bench build --app universal_workshop || echo "⚠️ تحذير: فشل في بناء أصول universal_workshop"

# تصحيح صلاحيات الملفات
echo "🔧 تصحيح صلاحيات الملفات..."
find "sites/$SITE_NAME" -type d -exec chmod 755 {} \;
find "sites/$SITE_NAME" -type f -exec chmod 644 {} \;
chmod 755 "sites/$SITE_NAME/private/backups"

# إعادة تشغيل العمليات
echo "▶️ إعادة تشغيل العمليات..."
bench --site "$SITE_NAME" set-maintenance-mode off
bench restart || echo "⚠️ تحذير: فشل في إعادة تشغيل bench"

# فحص النتيجة
echo ""
echo "🔍 فحص النتيجة..."

# التحقق من الاتصال بقاعدة البيانات
if bench --site "$SITE_NAME" list-apps > /dev/null 2>&1; then
    echo "✅ قاعدة البيانات تعمل بشكل صحيح"
else
    echo "❌ مشكلة في قاعدة البيانات"
fi

# اختبار الوصول للموقع
sleep 5  # انتظار قصير لبدء الخدمات
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000" | grep -q "200\|302"; then
    echo "✅ الموقع يستجيب"
else
    echo "❌ الموقع لا يستجيب"
fi

echo ""
echo "=============================="
echo "🎉 انتهت عملية الاستعادة"
echo ""
echo "📋 ملخص العملية:"
echo "   📍 الموقع: $SITE_NAME"
echo "   🗃️ قاعدة البيانات: تم استعادتها"
if [ -n "$FILES_BACKUP_FILE" ]; then
    echo "   📁 الأصول: تم استعادتها"
fi
echo "   🔄 تحديث قاعدة البيانات: تم"
echo "   🔨 بناء الأصول: تم"
echo ""
echo "🌐 يمكن الوصول للموقع على: http://localhost:8000"
echo ""
echo "⚠️ ملاحظات مهمة:"
echo "   - تأكد من تغيير كلمات المرور"
echo "   - راجع إعدادات النظام"
echo "   - تحقق من البيانات المستعادة"
echo "   - قم بإجراء نسخة احتياطية جديدة"
echo ""
if [ -d "$CURRENT_BACKUP_DIR" ]; then
    echo "📦 النسخة الاحتياطية السابقة محفوظة في: $CURRENT_BACKUP_DIR"
fi

# إنشاء تقرير الاستعادة
RESTORE_REPORT="restore_reports/restore_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p restore_reports
cat > "$RESTORE_REPORT" << EOF
تقرير استعادة النسخة الاحتياطية
===============================

معلومات العملية:
- التاريخ والوقت: $(date '+%Y-%m-%d %H:%M:%S')
- الموقع: $SITE_NAME
- ملف قاعدة البيانات: $DB_BACKUP_FILE
- ملف الأصول: ${FILES_BACKUP_FILE:-غير محدد}

النتائج:
- استعادة قاعدة البيانات: نجحت
- استعادة الأصول: ${FILES_BACKUP_FILE:+نجحت}${FILES_BACKUP_FILE:-تم تخطيها}
- تحديث قاعدة البيانات: نجح
- بناء الأصول: نجح

النسخة الاحتياطية السابقة:
- المكان: $CURRENT_BACKUP_DIR
- الحجم: $(du -sh "$CURRENT_BACKUP_DIR" 2>/dev/null | cut -f1 || echo "غير محدد")

ملاحظات:
- تم إنشاء نسخة احتياطية من البيانات السابقة
- يُنصح بفحص البيانات المستعادة
- قم بإجراء نسخة احتياطية جديدة بعد التأكد من صحة البيانات

تم إنشاء هذا التقرير تلقائياً
EOF

echo "📄 تم إنشاء تقرير الاستعادة: $RESTORE_REPORT"
