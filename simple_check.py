#!/usr/bin/env python3

import os
import sys

# Set the correct path for Frappe
os.chdir('/home/said/frappe-dev/frappe-bench')
sys.path.insert(0, '/home/said/frappe-dev/frappe-bench')

def check_setup_status():
    print("🔍 فحص حالة نظام Universal Workshop ERP")
    print("=" * 50)
    
    # Check setup status
    os.system('bench --site universal.local execute frappe.db.get_single_value --args "[\\"System Settings\\", \\"setup_complete\\"]"')

if __name__ == "__main__":
    check_setup_status()
