#!/usr/bin/env python3
"""
Simple system status check
"""
import os
import sys

# Add bench path
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench")
os.chdir("/home/said/frappe-dev/frappe-bench")

# Set environment
os.environ['FRAPPE_SITE'] = 'universal.local'

try:
    import frappe
    frappe.init(site="universal.local", sites_path="sites")
    frappe.connect()
    
    print("🔍 فحص حالة النظام:")
    print("=" * 50)
    
    # Simple database queries
    result = frappe.db.sql("SELECT COUNT(*) as count FROM tabUser WHERE user_type='System User'", as_dict=True)
    admin_count = result[0]['count'] if result else 0
    print(f"📊 عدد المستخدمين الإداريين: {admin_count}")
    
    # Check if Administrator exists
    admin_exists = frappe.db.sql("SELECT name FROM tabUser WHERE name='Administrator'")
    print(f"👑 المستخدم Administrator موجود: {bool(admin_exists)}")
    
    # Check companies
    companies = frappe.db.sql("SELECT COUNT(*) as count FROM tabCompany", as_dict=True)
    company_count = companies[0]['count'] if companies else 0
    print(f"🏢 عدد الشركات: {company_count}")
    
    # Check DocTypes
    workshop_doctype = frappe.db.sql("SELECT name FROM tabDocType WHERE name='Workshop Profile'")
    print(f"🏪 DocType Workshop Profile: {bool(workshop_doctype)}")
    
    onboarding_doctype = frappe.db.sql("SELECT name FROM tabDocType WHERE name='Workshop Onboarding Form'")
    print(f"📋 DocType Workshop Onboarding Form: {bool(onboarding_doctype)}")
    
    frappe.destroy()
    print("\n✅ فحص النظام مكتمل")
    
except Exception as e:
    print(f"💥 خطأ: {e}")
    import traceback
    traceback.print_exc()
