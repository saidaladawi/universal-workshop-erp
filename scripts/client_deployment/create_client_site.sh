#!/bin/bash
# سكريبت إنشاء موقع جديد للعميل
# الاستخدام: ./create_client_site.sh [اسم_العميل] [نطاق_الموقع]

set -e

CLIENT_NAME="$1"
CLIENT_DOMAIN="$2"

if [ -z "$CLIENT_NAME" ] || [ -z "$CLIENT_DOMAIN" ]; then
    echo "❌ الاستخدام: ./create_client_site.sh [اسم_العميل] [نطاق_الموقع]"
    echo "مثال: ./create_client_site.sh 'ورشة الفارسي' alfarsi.local"
    exit 1
fi

echo "🔄 إنشاء موقع جديد للعميل: $CLIENT_NAME"
echo "🌐 النطاق: $CLIENT_DOMAIN"

# التحقق من وجود bench
if ! command -v bench &> /dev/null; then
    echo "❌ bench غير مثبت"
    exit 1
fi

# التحقق من وجود المجلد
if [ ! -d "sites" ]; then
    echo "❌ يجب تشغيل السكريبت من داخل مجلد frappe-bench"
    exit 1
fi

# إنشاء الموقع
echo "📦 إنشاء الموقع..."
bench new-site $CLIENT_DOMAIN --mariadb-root-password frappe

# تثبيت التطبيقات المطلوبة
echo "📱 تثبيت ERPNext..."
if [ ! -d "apps/erpnext" ]; then
    bench get-app erpnext
fi
bench --site $CLIENT_DOMAIN install-app erpnext

echo "📱 تثبيت Universal Workshop..."
if [ ! -d "apps/universal_workshop" ]; then
    bench get-app https://github.com/universal-workshop/universal_workshop.git
fi
bench --site $CLIENT_DOMAIN install-app universal_workshop

# إعداد البيانات الأساسية
echo "⚙️ إعداد البيانات الأساسية..."
bench --site $CLIENT_DOMAIN execute <<EOF
import frappe

# إنشاء الشركة
if not frappe.db.exists('Company', '$CLIENT_NAME'):
    company = frappe.get_doc({
        'doctype': 'Company',
        'company_name': '$CLIENT_NAME',
        'country': 'Oman',
        'default_currency': 'OMR'
    })
    company.insert()
    frappe.db.commit()

# إعداد النظام
frappe.db.set_value('System Settings', None, 'country', 'Oman')
frappe.db.set_value('System Settings', None, 'language', 'ar')
frappe.db.set_value('System Settings', None, 'time_zone', 'Asia/Muscat')
frappe.db.commit()

print("✅ تم إعداد البيانات الأساسية")
EOF

# إنشاء مستخدم إداري
echo "👤 إنشاء مستخدم إداري..."
bench --site $CLIENT_DOMAIN add-user admin@$CLIENT_DOMAIN "مدير النظام" --password admin123

# بناء الأصول
echo "🔨 بناء الأصول..."
bench build

echo "✅ تم إنشاء الموقع بنجاح: $CLIENT_DOMAIN"
echo "🌐 يمكن الوصول للنظام على: http://$CLIENT_DOMAIN:8000"
echo "👤 المستخدم: admin@$CLIENT_DOMAIN"
echo "🔑 كلمة المرور: admin123"
echo ""
echo "⚠️ لا تنسى:"
echo "   - تغيير كلمة المرور"
echo "   - إنشاء رخصة للعميل"
echo "   - إعداد النسخ الاحتياطية"
