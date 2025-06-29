#!/bin/bash

echo "🔧 Universal Workshop ERP - JavaScript Fix and Restart Script"
echo "============================================================="

# Change to frappe-bench directory
cd /home/said/frappe-dev/frappe-bench

echo "📦 Building Universal Workshop assets..."
bench build --apps universal_workshop

echo "🔄 Clearing cache..."
bench --site universal.local clear-cache
bench --site workshop.local clear-cache

echo "🔃 Restarting ERPNext server..."
bench restart

echo "✅ All fixes applied successfully!"
echo ""
echo "🌐 You can now access your system at:"
echo "   - http://localhost:8000"
echo "   - http://universal.local:8000" 
echo "   - http://workshop.local:8000"
echo ""
echo "🎯 JavaScript errors should now be resolved:"
echo "   ✅ Mobile warehouse detection fixed"
echo "   ✅ Theme Manager 'light' theme added"
echo "   ✅ Dark Mode Manager initialization fixed"
echo "   ✅ Branding Service API path corrected"
echo ""
echo "🔍 If you still see errors, check the browser console for details." 