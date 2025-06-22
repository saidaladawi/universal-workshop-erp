#!/bin/bash
# سكريپت إعداد النسخ الاحتياطية التلقائية
# الاستخدام: ./setup_backup.sh [نطاق_الموقع] [مسار_النسخ_الاحتياطية]

set -e

SITE_NAME="${1:-universal.local}"
BACKUP_PATH="${2:-/home/$(whoami)/backups}"

echo "💾 إعداد النسخ الاحتياطية التلقائية"
echo "📍 الموقع: $SITE_NAME"
echo "📁 مسار الحفظ: $BACKUP_PATH"

# إنشاء مجلد النسخ الاحتياطية
mkdir -p "$BACKUP_PATH"
mkdir -p "$BACKUP_PATH/daily"
mkdir -p "$BACKUP_PATH/weekly"
mkdir -p "$BACKUP_PATH/monthly"

echo "✅ تم إنشاء مجلدات النسخ الاحتياطية"

# إنشاء سكريپت النسخ الاحتياطي اليومي
DAILY_BACKUP_SCRIPT="$HOME/daily_backup.sh"
cat > "$DAILY_BACKUP_SCRIPT" << EOF
#!/bin/bash
# سكريپت النسخ الاحتياطي اليومي
# تم إنشاؤه تلقائياً في $(date)

set -e

SITE_NAME="$SITE_NAME"
BACKUP_PATH="$BACKUP_PATH"
BENCH_PATH="$(pwd)"
DATE_STAMP=\$(date +%Y%m%d_%H%M%S)
LOG_FILE="\$BACKUP_PATH/backup.log"

# دالة لكتابة السجل
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S'): \$1" | tee -a "\$LOG_FILE"
}

log_message "🔄 بدء النسخ الاحتياطي اليومي للموقع: \$SITE_NAME"

cd "\$BENCH_PATH"

# التحقق من وجود الموقع
if [ ! -d "sites/\$SITE_NAME" ]; then
    log_message "❌ الموقع غير موجود: \$SITE_NAME"
    exit 1
fi

# إنشاء نسخة احتياطية
log_message "📦 إنشاء نسخة احتياطية من قاعدة البيانات..."
if bench --site \$SITE_NAME backup --with-files; then
    log_message "✅ تم إنشاء النسخة الاحتياطية بنجاح"
else
    log_message "❌ فشل في إنشاء النسخة الاحتياطية"
    exit 1
fi

# نسخ الملفات إلى مجلد الحفظ
log_message "📁 نسخ الملفات إلى مجلد الحفظ..."

# نسخ ملفات قاعدة البيانات
if ls sites/\$SITE_NAME/private/backups/*\${DATE_STAMP:0:8}*.sql.gz 1> /dev/null 2>&1; then
    cp sites/\$SITE_NAME/private/backups/*\${DATE_STAMP:0:8}*.sql.gz "\$BACKUP_PATH/daily/"
    log_message "✅ تم نسخ ملف قاعدة البيانات"
fi

# نسخ ملفات الموقع
if ls sites/\$SITE_NAME/private/backups/*\${DATE_STAMP:0:8}*-files.tar 1> /dev/null 2>&1; then
    cp sites/\$SITE_NAME/private/backups/*\${DATE_STAMP:0:8}*-files.tar "\$BACKUP_PATH/daily/"
    log_message "✅ تم نسخ ملفات الموقع"
fi

# حذف النسخ القديمة (أكثر من 30 يوم)
log_message "🧹 حذف النسخ القديمة..."
find "\$BACKUP_PATH/daily" -name "*.sql.gz" -mtime +30 -delete 2>/dev/null || true
find "\$BACKUP_PATH/daily" -name "*-files.tar" -mtime +30 -delete 2>/dev/null || true

# حذف النسخ من مجلد الموقع (أكثر من 7 أيام)
find "sites/\$SITE_NAME/private/backups" -name "*.sql.gz" -mtime +7 -delete 2>/dev/null || true
find "sites/\$SITE_NAME/private/backups" -name "*-files.tar" -mtime +7 -delete 2>/dev/null || true

# إحصائيات
BACKUP_COUNT=\$(ls "\$BACKUP_PATH/daily"/*.sql.gz 2>/dev/null | wc -l)
BACKUP_SIZE=\$(du -sh "\$BACKUP_PATH/daily" | cut -f1)

log_message "📊 إحصائيات النسخ الاحتياطية:"
log_message "   📈 عدد النسخ: \$BACKUP_COUNT"
log_message "   💾 المساحة المستخدمة: \$BACKUP_SIZE"

log_message "✅ انتهى النسخ الاحتياطي اليومي بنجاح"
EOF

chmod +x "$DAILY_BACKUP_SCRIPT"
echo "✅ تم إنشاء سكريپت النسخ الاحتياطي اليومي: $DAILY_BACKUP_SCRIPT"

# إنشاء سكريپت النسخ الاحتياطي الأسبوعي
WEEKLY_BACKUP_SCRIPT="$HOME/weekly_backup.sh"
cat > "$WEEKLY_BACKUP_SCRIPT" << EOF
#!/bin/bash
# سكريپت النسخ الاحتياطي الأسبوعي
# تم إنشاؤه تلقائياً في $(date)

set -e

BACKUP_PATH="$BACKUP_PATH"
DATE_STAMP=\$(date +%Y%m%d)
LOG_FILE="\$BACKUP_PATH/backup.log"

# دالة لكتابة السجل
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S'): \$1" | tee -a "\$LOG_FILE"
}

log_message "📅 بدء النسخ الاحتياطي الأسبوعي"

# نسخ أحدث نسخة يومية إلى المجلد الأسبوعي
LATEST_DB=\$(ls -t "\$BACKUP_PATH/daily"/*.sql.gz 2>/dev/null | head -1)
LATEST_FILES=\$(ls -t "\$BACKUP_PATH/daily"/*-files.tar 2>/dev/null | head -1)

if [ -n "\$LATEST_DB" ]; then
    cp "\$LATEST_DB" "\$BACKUP_PATH/weekly/weekly_\${DATE_STAMP}_database.sql.gz"
    log_message "✅ تم نسخ قاعدة البيانات الأسبوعية"
fi

if [ -n "\$LATEST_FILES" ]; then
    cp "\$LATEST_FILES" "\$BACKUP_PATH/weekly/weekly_\${DATE_STAMP}_files.tar"
    log_message "✅ تم نسخ ملفات الموقع الأسبوعية"
fi

# حذف النسخ الأسبوعية القديمة (أكثر من 12 أسبوع)
find "\$BACKUP_PATH/weekly" -name "weekly_*.sql.gz" -mtime +84 -delete 2>/dev/null || true
find "\$BACKUP_PATH/weekly" -name "weekly_*-files.tar" -mtime +84 -delete 2>/dev/null || true

log_message "✅ انتهى النسخ الاحتياطي الأسبوعي"
EOF

chmod +x "$WEEKLY_BACKUP_SCRIPT"
echo "✅ تم إنشاء سكريپت النسخ الاحتياطي الأسبوعي: $WEEKLY_BACKUP_SCRIPT"

# إنشاء سكريپت النسخ الاحتياطي الشهري
MONTHLY_BACKUP_SCRIPT="$HOME/monthly_backup.sh"
cat > "$MONTHLY_BACKUP_SCRIPT" << EOF
#!/bin/bash
# سكريپت النسخ الاحتياطي الشهري
# تم إنشاؤه تلقائياً في $(date)

set -e

BACKUP_PATH="$BACKUP_PATH"
DATE_STAMP=\$(date +%Y%m)
LOG_FILE="\$BACKUP_PATH/backup.log"

# دالة لكتابة السجل
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S'): \$1" | tee -a "\$LOG_FILE"
}

log_message "📆 بدء النسخ الاحتياطي الشهري"

# نسخ أحدث نسخة أسبوعية إلى المجلد الشهري
LATEST_DB=\$(ls -t "\$BACKUP_PATH/weekly"/weekly_*.sql.gz 2>/dev/null | head -1)
LATEST_FILES=\$(ls -t "\$BACKUP_PATH/weekly"/weekly_*-files.tar 2>/dev/null | head -1)

if [ -n "\$LATEST_DB" ]; then
    cp "\$LATEST_DB" "\$BACKUP_PATH/monthly/monthly_\${DATE_STAMP}_database.sql.gz"
    log_message "✅ تم نسخ قاعدة البيانات الشهرية"
fi

if [ -n "\$LATEST_FILES" ]; then
    cp "\$LATEST_FILES" "\$BACKUP_PATH/monthly/monthly_\${DATE_STAMP}_files.tar"
    log_message "✅ تم نسخ ملفات الموقع الشهرية"
fi

# حذف النسخ الشهرية القديمة (أكثر من سنة)
find "\$BACKUP_PATH/monthly" -name "monthly_*.sql.gz" -mtime +365 -delete 2>/dev/null || true
find "\$BACKUP_PATH/monthly" -name "monthly_*-files.tar" -mtime +365 -delete 2>/dev/null || true

log_message "✅ انتهى النسخ الاحتياطي الشهري"
EOF

chmod +x "$MONTHLY_BACKUP_SCRIPT"
echo "✅ تم إنشاء سكريپت النسخ الاحتياطي الشهري: $MONTHLY_BACKUP_SCRIPT"

# إعداد المهام المجدولة (Cron Jobs)
echo "⏰ إعداد المهام المجدولة..."

# إزالة المهام القديمة المتعلقة بالنسخ الاحتياطية
crontab -l 2>/dev/null | grep -v "backup.sh" | crontab - 2>/dev/null || true

# إضافة المهام الجديدة
(crontab -l 2>/dev/null; cat << EOF
# النسخ الاحتياطية التلقائية لـ Universal Workshop ERP
# النسخ اليومي - كل يوم في الساعة 2:00 صباحاً
0 2 * * * $DAILY_BACKUP_SCRIPT

# النسخ الأسبوعي - كل يوم أحد في الساعة 3:00 صباحاً
0 3 * * 0 $WEEKLY_BACKUP_SCRIPT

# النسخ الشهري - اليوم الأول من كل شهر في الساعة 4:00 صباحاً
0 4 1 * * $MONTHLY_BACKUP_SCRIPT
EOF
) | crontab -

echo "✅ تم إعداد المهام المجدولة"

# إنشاء سكريپت فحص النسخ الاحتياطية
CHECK_BACKUP_SCRIPT="$HOME/check_backup.sh"
cat > "$CHECK_BACKUP_SCRIPT" << EOF
#!/bin/bash
# سكريپت فحص حالة النسخ الاحتياطية

BACKUP_PATH="$BACKUP_PATH"

echo "📊 تقرير حالة النسخ الاحتياطية"
echo "================================="

# فحص المجلدات
for folder in daily weekly monthly; do
    if [ -d "\$BACKUP_PATH/\$folder" ]; then
        count=\$(ls "\$BACKUP_PATH/\$folder"/*.sql.gz 2>/dev/null | wc -l)
        size=\$(du -sh "\$BACKUP_PATH/\$folder" 2>/dev/null | cut -f1)
        latest=\$(ls -t "\$BACKUP_PATH/\$folder"/*.sql.gz 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo "لا توجد نسخ")
        
        echo "📁 \$folder:"
        echo "   📈 العدد: \$count"
        echo "   💾 الحجم: \$size"
        echo "   🕐 الأحدث: \$latest"
        echo ""
    fi
done

# فحص السجل
if [ -f "\$BACKUP_PATH/backup.log" ]; then
    echo "📋 آخر 5 إدخالات في السجل:"
    tail -5 "\$BACKUP_PATH/backup.log"
else
    echo "⚠️ ملف السجل غير موجود"
fi

echo ""
echo "📅 المهام المجدولة:"
crontab -l | grep backup || echo "لا توجد مهام مجدولة"
EOF

chmod +x "$CHECK_BACKUP_SCRIPT"
echo "✅ تم إنشاء سكريپت فحص النسخ الاحتياطية: $CHECK_BACKUP_SCRIPT"

# تشغيل النسخة الاحتياطية الأولى كاختبار
echo "🧪 تشغيل النسخة الاحتياطية الأولى كاختبار..."
if "$DAILY_BACKUP_SCRIPT"; then
    echo "✅ النسخة الاحتياطية التجريبية نجحت"
else
    echo "❌ النسخة الاحتياطية التجريبية فشلت"
fi

echo ""
echo "🎉 تم إعداد النسخ الاحتياطية التلقائية بنجاح!"
echo ""
echo "📋 الملفات المُنشأة:"
echo "   📄 النسخ اليومي: $DAILY_BACKUP_SCRIPT"
echo "   📄 النسخ الأسبوعي: $WEEKLY_BACKUP_SCRIPT"  
echo "   📄 النسخ الشهري: $MONTHLY_BACKUP_SCRIPT"
echo "   📄 فحص النسخ: $CHECK_BACKUP_SCRIPT"
echo ""
echo "📁 مجلدات النسخ الاحتياطية:"
echo "   📂 يومي: $BACKUP_PATH/daily"
echo "   📂 أسبوعي: $BACKUP_PATH/weekly"
echo "   📂 شهري: $BACKUP_PATH/monthly"
echo ""
echo "⏰ جدولة النسخ:"
echo "   🌅 يومي: الساعة 2:00 صباحاً"
echo "   📅 أسبوعي: يوم الأحد الساعة 3:00 صباحاً"
echo "   📆 شهري: اليوم الأول من الشهر الساعة 4:00 صباحاً"
echo ""
echo "🔧 أوامر مفيدة:"
echo "   فحص النسخ: $CHECK_BACKUP_SCRIPT"
echo "   نسخ يدوي: $DAILY_BACKUP_SCRIPT"
echo "   عرض السجل: tail -f $BACKUP_PATH/backup.log"
