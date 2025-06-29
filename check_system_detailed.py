#!/usr/bin/env python3
"""
فحص حالة نظام Universal Workshop ERP
"""

import os
import sys

# Add frappe-bench to path
sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

def check_system_status():
    """فحص حالة النظام الحالية"""
    print("🔍 فحص حالة نظام Universal Workshop ERP")
    print("=" * 50)
    
    try:
        # Check if bench is running
        os.chdir('/home/said/frappe-dev/frappe-bench')
        
        # Use bench execute to run frappe commands
        print("\n1️⃣ فحص حالة الإعداد الأساسي...")
        cmd1 = 'bench --site universal.local execute "import frappe; print(f\'Setup Complete: {frappe.db.get_single_value(\\\"System Settings\\\", \\\"setup_complete\\\")}\'); print(f\'Users Count: {len(frappe.get_all(\\\"User\\\", filters={\\\"user_type\\\": \\\"System User\\\"}))}\'); frappe.db.commit()"'
        print(f"تشغيل: {cmd1}")
        
        print("\n2️⃣ فحص وجود DocTypes الأساسية...")
        cmd2 = 'bench --site universal.local execute "import frappe; doctypes = [\'Workshop Profile\', \'Service Order\', \'Vehicle\']; results = {dt: frappe.db.exists(\'DocType\', dt) for dt in doctypes}; print(f\'DocTypes Status: {results}\'); frappe.db.commit()"'
        print(f"تشغيل: {cmd2}")
        
        print("\n3️⃣ فحص بيانات الرخصة...")
        cmd3 = 'bench --site universal.local execute "import frappe; import os; license_path = \'/home/said/frappe-dev/frappe-bench/licenses/workshop_license.json\'; print(f\'License File Exists: {os.path.exists(license_path)}\'); frappe.db.commit()"'
        print(f"تشغيل: {cmd3}")
        
        print("\n4️⃣ فحص حالة المستخدمين...")
        cmd4 = 'bench --site universal.local execute "import frappe; users = frappe.get_all(\'User\', filters={\'user_type\': \'System User\'}, fields=[\'name\', \'full_name\', \'enabled\']); print(f\'System Users: {len(users)}\'); [print(f\'  - {u.name}: {u.full_name} (Active: {u.enabled})\') for u in users[:5]]; frappe.db.commit()"'
        print(f"تشغيل: {cmd4}")
        
        print("\n📝 يرجى تشغيل هذه الأوامر واحداً تلو الآخر وإرسال النتائج:")
        print(cmd1)
        print("\n" + "="*20)
        print(cmd2)
        print("\n" + "="*20)
        print(cmd3)
        print("\n" + "="*20)
        print(cmd4)
        
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    check_system_status()
