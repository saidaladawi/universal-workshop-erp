#\!/usr/bin/env python3

import frappe
from frappe import _

def reset_to_first_time_setup():
    """Reset the system to first-time setup state"""
    
    frappe.init(site="universal.local")
    frappe.connect()
    
    try:
        print("🔄 Resetting Universal Workshop to first-time setup state...")
        
        # Delete Workshop Profile records
        workshop_profiles = frappe.get_all('Workshop Profile')
        for wp in workshop_profiles:
            try:
                frappe.delete_doc('Workshop Profile', wp.name, force=True)
                print(f"✅ Deleted Workshop Profile: {wp.name}")
            except Exception as e:
                print(f"⚠️  Could not delete Workshop Profile {wp.name}: {e}")
        
        # Delete Onboarding Progress records
        onboarding_records = frappe.get_all('Onboarding Progress')
        for record in onboarding_records:
            try:
                frappe.delete_doc('Onboarding Progress', record.name, force=True)
                print(f"✅ Deleted Onboarding Progress: {record.name}")
            except Exception as e:
                print(f"⚠️  Could not delete Onboarding Progress {record.name}: {e}")
        
        # Delete Onboarding Performance Log records
        perf_logs = frappe.get_all('Onboarding Performance Log')
        for log in perf_logs:
            try:
                frappe.delete_doc('Onboarding Performance Log', log.name, force=True)
                print(f"✅ Deleted Onboarding Performance Log: {log.name}")
            except Exception as e:
                print(f"⚠️  Could not delete Performance Log {log.name}: {e}")
        
        # Commit changes
        frappe.db.commit()
        
        # Check setup status
        from universal_workshop.boot import check_initial_setup_status
        status = check_initial_setup_status()
        
        print("\n📊 Setup Status After Reset:")
        print(f"   Setup Complete: {status.get('setup_complete', False)}")
        print(f"   Workshop Exists: {status.get('workshop_exists', False)}")
        print(f"   Admin Users: {status.get('admin_users_count', 0)}")
        print(f"   Onboarding Completed: {status.get('onboarding_completed', False)}")
        
        if not status.get('setup_complete'):
            print("\n🎉 System successfully reset to first-time setup state\!")
            print("🌐 You can now access the onboarding wizard at:")
            print("   http://localhost:8000/workshop-onboarding")
        else:
            print("\n⚠️  System may still have setup data. Manual cleanup required.")
            
    except Exception as e:
        print(f"❌ Error resetting setup: {e}")
        frappe.log_error(f"Setup reset error: {e}")
    
    finally:
        frappe.destroy()

if __name__ == "__main__":
    reset_to_first_time_setup()
EOF < /dev/null
