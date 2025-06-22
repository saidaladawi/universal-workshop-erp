#!/bin/bash
# سكريپت مراقبة النظام
# الاستخدام: ./monitor_system.sh [نطاق_الموقع] [فترة_المراقبة_بالثواني]

set -e

SITE_NAME="${1:-universal.local}"
MONITOR_INTERVAL="${2:-30}"
LOG_FILE="logs/system_monitor_$(date +%Y%m%d).log"

# إنشاء مجلد السجلات إذا لم يكن موجوداً
mkdir -p logs

echo "📊 بدء مراقبة النظام"
echo "===================="
echo "📍 الموقع: $SITE_NAME"
echo "⏱️ فترة المراقبة: $MONITOR_INTERVAL ثانية"
echo "📄 ملف السجل: $LOG_FILE"
echo ""
echo "اضغط Ctrl+C للتوقف"
echo ""

# دالة لكتابة السجل
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_FILE"
}

# دالة لقياس استخدام الموارد
get_resource_usage() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # استخدام المعالج
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | sed 's/%us,//')
    
    # استخدام الذاكرة
    local mem_total=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    local mem_used=$(free -m | awk 'NR==2{printf "%.0f", $3}')
    local mem_percent=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    # استخدام القرص
    local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    local disk_available=$(df -h . | tail -1 | awk '{print $4}')
    
    # عدد العمليات
    local frappe_processes=$(ps aux | grep -E "(frappe|bench)" | grep -v grep | wc -l)
    
    # حالة قاعدة البيانات
    local db_status="متصل"
    if ! mysql -u root -e "SELECT 1;" > /dev/null 2>&1; then
        db_status="منقطع"
    fi
    
    # حالة Redis
    local redis_status="متصل"
    if ! redis-cli ping > /dev/null 2>&1; then
        redis_status="منقطع"
    fi
    
    # حالة الموقع
    local site_status="يعمل"
    local response_time="0"
    if ! bench --site "$SITE_NAME" list-apps > /dev/null 2>&1; then
        site_status="خطأ"
    else
        response_time=$(curl -o /dev/null -s -w '%{time_total}' "http://localhost:8000" 2>/dev/null || echo "0")
    fi
    
    # عدد المستخدمين المتصلين (تقريبي)
    local active_sessions=$(bench --site "$SITE_NAME" execute "
import frappe
try:
    sessions = frappe.db.sql('SELECT COUNT(*) FROM tabSessions WHERE creation > DATE_SUB(NOW(), INTERVAL 1 HOUR)')
    print(sessions[0][0] if sessions else 0)
except:
    print(0)
" 2>/dev/null || echo "0")
    
    # طباعة النتائج
    echo "[$timestamp] 📊 مراقبة النظام:"
    echo "[$timestamp]    💻 المعالج: ${cpu_usage}%"
    echo "[$timestamp]    💾 الذاكرة: ${mem_used}MB/${mem_total}MB (${mem_percent}%)"
    echo "[$timestamp]    💿 القرص: ${disk_usage}% مستخدم، ${disk_available} متاح"
    echo "[$timestamp]    ⚙️ عمليات Frappe: $frappe_processes"
    echo "[$timestamp]    🗃️ قاعدة البيانات: $db_status"
    echo "[$timestamp]    🔴 Redis: $redis_status"
    echo "[$timestamp]    🌐 الموقع: $site_status (${response_time}s)"
    echo "[$timestamp]    👥 المستخدمين النشطين: $active_sessions"
    
    # التحقق من التحذيرات
    local warnings=()
    
    if [ "${cpu_usage%.*}" -gt 80 ]; then
        warnings+=("استخدام المعالج مرتفع (${cpu_usage}%)")
    fi
    
    if [ "$mem_percent" -gt 85 ]; then
        warnings+=("استخدام الذاكرة مرتفع (${mem_percent}%)")
    fi
    
    if [ "$disk_usage" -gt 80 ]; then
        warnings+=("مساحة القرص منخفضة (${disk_usage}%)")
    fi
    
    if [ "$frappe_processes" -lt 3 ]; then
        warnings+=("عدد عمليات Frappe قليل ($frappe_processes)")
    fi
    
    if [ "$db_status" = "منقطع" ]; then
        warnings+=("قاعدة البيانات منقطعة")
    fi
    
    if [ "$redis_status" = "منقطع" ]; then
        warnings+=("Redis منقطع")
    fi
    
    if [ "$site_status" = "خطأ" ]; then
        warnings+=("الموقع لا يعمل بشكل صحيح")
    fi
    
    if [ "$(echo "$response_time > 3" | bc 2>/dev/null || echo 0)" = "1" ]; then
        warnings+=("وقت الاستجابة بطيء (${response_time}s)")
    fi
    
    # طباعة التحذيرات
    if [ ${#warnings[@]} -gt 0 ]; then
        echo "[$timestamp] ⚠️ تحذيرات:"
        for warning in "${warnings[@]}"; do
            echo "[$timestamp]    - $warning"
        done
        
        # إرسال تنبيه (يمكن تخصيصه حسب الحاجة)
        send_alert "${warnings[*]}"
    else
        echo "[$timestamp] ✅ النظام يعمل بشكل طبيعي"
    fi
    
    echo "[$timestamp] ----------------------------------------"
}

# دالة إرسال التنبيهات
send_alert() {
    local message="$1"
    local alert_file="logs/alerts_$(date +%Y%m%d).log"
    
    # تسجيل التنبيه
    echo "$(date '+%Y-%m-%d %H:%M:%S') - تنبيه: $message" >> "$alert_file"
    
    # يمكن إضافة إرسال email أو SMS هنا
    # مثال لإرسال email (يتطلب تكوين sendmail):
    # echo "تنبيه من نظام المراقبة: $message" | mail -s "تنبيه نظام" admin@company.com
    
    echo "⚠️ تم تسجيل التنبيه في: $alert_file"
}

# دالة فحص حالة الخدمات
check_services() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] 🔧 فحص الخدمات:"
    
    # فحص MariaDB
    if systemctl is-active mariadb > /dev/null 2>&1; then
        echo "[$timestamp]    ✅ MariaDB يعمل"
    else
        echo "[$timestamp]    ❌ MariaDB متوقف"
        log_message "محاولة إعادة تشغيل MariaDB..."
        sudo systemctl start mariadb && log_message "تم إعادة تشغيل MariaDB" || log_message "فشل في إعادة تشغيل MariaDB"
    fi
    
    # فحص Redis
    if systemctl is-active redis > /dev/null 2>&1; then
        echo "[$timestamp]    ✅ Redis يعمل"
    else
        echo "[$timestamp]    ❌ Redis متوقف"
        log_message "محاولة إعادة تشغيل Redis..."
        sudo systemctl start redis && log_message "تم إعادة تشغيل Redis" || log_message "فشل في إعادة تشغيل Redis"
    fi
    
    # فحص منافذ الشبكة
    local ports=("3306:MariaDB" "6379:Redis" "8000:Frappe")
    for port_info in "${ports[@]}"; do
        local port="${port_info%:*}"
        local service="${port_info#*:}"
        
        if netstat -tuln | grep -q ":$port "; then
            echo "[$timestamp]    ✅ منفذ $service ($port) مفتوح"
        else
            echo "[$timestamp]    ❌ منفذ $service ($port) مغلق"
        fi
    done
}

# دالة إنشاء تقرير يومي
generate_daily_report() {
    local date_str=$(date +%Y%m%d)
    local report_file="logs/daily_report_${date_str}.txt"
    
    cat > "$report_file" << EOF
تقرير يومي لمراقبة النظام
========================

التاريخ: $(date '+%Y-%m-%d')
الموقع: $SITE_NAME

إحصائيات اليوم:
$(tail -100 "$LOG_FILE" | grep "$(date '+%Y-%m-%d')" | wc -l) فحص تم إجراؤه

التحذيرات:
$(grep "$(date '+%Y-%m-%d')" "logs/alerts_$(date +%Y%m%d).log" 2>/dev/null | wc -l) تحذير

آخر حالة للنظام:
$(tail -20 "$LOG_FILE")

انتهى التقرير في: $(date '+%Y-%m-%d %H:%M:%S')
EOF

    echo "📄 تم إنشاء التقرير اليومي: $report_file"
}

# معالج الإشارات للخروج الآمن
cleanup() {
    echo ""
    log_message "🛑 تم إيقاف المراقبة"
    generate_daily_report
    echo "👋 شكراً لاستخدام نظام المراقبة"
    exit 0
}

trap cleanup SIGINT SIGTERM

# بدء المراقبة
log_message "🚀 بدء مراقبة النظام للموقع: $SITE_NAME"

# فحص أولي للخدمات
check_services

echo ""
echo "📊 بدء المراقبة المستمرة..."
echo ""

# حلقة المراقبة الرئيسية
while true; do
    get_resource_usage
    echo ""
    
    # فحص الخدمات كل 5 دقائق (10 دورات × 30 ثانية)
    if [ $(($(date +%s) % 300)) -lt "$MONITOR_INTERVAL" ]; then
        check_services
        echo ""
    fi
    
    sleep "$MONITOR_INTERVAL"
done
