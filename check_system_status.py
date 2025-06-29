#!/usr/bin/env python3
"""
Script to check Universal Workshop system status
"""
import os
import sys

# Add bench path
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench")
os.chdir("/home/said/frappe-dev/frappe-bench")

try:
    import frappe
    from frappe import _
    
    # Initialize frappe for the site
    frappe.init(site="universal.local", sites_path="sites")
    frappe.connect()
    
    print("🔍 فحص حالة النظام:")
    print("=" * 50)
    
    # Check admin users
    try:
        users = frappe.get_all('User', 
                              filters={'user_type': 'System User'}, 
                              fields=['name', 'full_name', 'enabled'])
        print(f"📊 عدد المستخدمين الإداريين: {len(users)}")
        for user in users[:5]:
            status = "فعال" if user.enabled else "معطل"
            print(f"   👤 {user.name}: {user.full_name} ({status})")
    except Exception as e:
        print(f"❌ خطأ في جلب المستخدمين: {e}")
    
    # Check setup completion
    try:
        setup_complete = frappe.db.get_single_value('System Settings', 'setup_complete')
        print(f"✅ حالة اكتمال الإعداد: {setup_complete}")
    except Exception as e:
        print(f"❌ خطأ في فحص الإعداد: {e}")
        
    # Check if Workshop Profile exists
    try:
        workshop_exists = frappe.db.exists('DocType', 'Workshop Profile')
        print(f"🏪 نوع مستند Workshop Profile موجود: {bool(workshop_exists)}")
        
        if workshop_exists:
            workshop_profiles = frappe.get_all('Workshop Profile', fields=['name', 'workshop_name'])
            print(f"📝 عدد ملفات الورش: {len(workshop_profiles)}")
            for profile in workshop_profiles[:3]:
                print(f"   🔧 {profile.name}: {profile.workshop_name}")
    except Exception as e:
        print(f"❌ خطأ في فحص Workshop Profile: {e}")
    
    # Check onboarding forms
    try:
        onboarding_forms = frappe.get_all('Workshop Onboarding Form', fields=['name', 'workshop_name'])
        print(f"📋 عدد نماذج الإعداد: {len(onboarding_forms)}")
        for form in onboarding_forms[:3]:
            print(f"   📝 {form.name}: {form.workshop_name}")
    except Exception as e:
        print(f"❌ خطأ في فحص نماذج الإعداد: {e}")
    
    # Check if first run is complete
    try:
        # Check for any system settings that indicate completion
        company_count = len(frappe.get_all('Company'))
        print(f"🏢 عدد الشركات المسجلة: {company_count}")
        
        if company_count > 0:
            companies = frappe.get_all('Company', fields=['name', 'company_name'])
            for company in companies[:3]:
                print(f"   🏭 {company.name}: {company.company_name}")
                
    except Exception as e:
        print(f"❌ خطأ في فحص الشركات: {e}")
    
    print("\n🎯 تحليل الحالة:")
    print("-" * 30)
    
    # Determine system state
    has_admin = False
    try:
        admin_exists = frappe.db.exists('User', 'Administrator')
        has_admin = bool(admin_exists)
        print(f"👑 المستخدم Administrator موجود: {has_admin}")
    except:
        pass
        
    print("\n📊 ملخص التقييم:")
    print("=" * 50)
    
    # System readiness assessment
    readiness_score = 0
    total_checks = 4
    
    if has_admin:
        readiness_score += 1
        print("✅ المستخدم الإداري - جاهز")
    else:
        print("❌ المستخدم الإداري - غير جاهز")
        
    if len(users) > 0:
        readiness_score += 1
        print("✅ قاعدة المستخدمين - جاهزة")
    else:
        print("❌ قاعدة المستخدمين - فارغة")
        
    if workshop_exists:
        readiness_score += 1
        print("✅ نوع مستند الورشة - موجود")
    else:
        print("❌ نوع مستند الورشة - مفقود")
        
    if company_count > 0:
        readiness_score += 1
        print("✅ إعداد الشركة - مكتمل")
    else:
        print("❌ إعداد الشركة - غير مكتمل")
    
    percentage = (readiness_score / total_checks) * 100
    print(f"\n🎯 نسبة جاهزية النظام: {percentage:.1f}% ({readiness_score}/{total_checks})")
    
    if percentage >= 75:
        print("🟢 النظام جاهز للاستخدام")
    elif percentage >= 50:
        print("🟡 النظام يحتاج إعداد إضافي")
    else:
        print("🔴 النظام يحتاج إعداد أساسي")
    
    frappe.destroy()
    
except Exception as e:
    print(f"💥 خطأ عام في النظام: {e}")
    import traceback
    traceback.print_exc()
