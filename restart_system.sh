#!/bin/bash

echo "🔄 إعادة تشغيل نظام Universal Workshop ERP..."

# التنقل إلى مجلد frappe-bench
cd /home/said/frappe-dev/frappe-bench

# إيقاف الخدمات
echo "⏹️ إيقاف الخدمات..."
bench stop

# إعادة تشغيل الخدمات
echo "▶️ بدء الخدمات..."
bench start &

# انتظار قليل للتأكد من بدء الخدمات
sleep 5

echo "✅ تم إعادة تشغيل النظام بنجاح!"
echo "🌐 يمكنك الآن زيارة: http://localhost:8000"
echo "🔗 أو: http://universal.local:8000" 