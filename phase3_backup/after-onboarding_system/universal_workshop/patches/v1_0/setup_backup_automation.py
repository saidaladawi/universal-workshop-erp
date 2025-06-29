import frappe
from universal_workshop.universal_workshop.utils.backup_automation import run_backup_automation

def execute():
    """Setup comprehensive backup automation for Universal Workshop ERP"""
    
    frappe.log_error("Starting backup automation setup", "Backup Setup")
    
    try:
        # Run backup automation setup
        results = run_backup_automation()
        
        # Update System Settings with backup configuration
        frappe.db.set_value('System Settings', None, 'backup_automation_enabled', 1)
        frappe.db.set_value('System Settings', None, 'backup_automation_setup_date', frappe.utils.now())
        frappe.db.set_value('System Settings', None, 'backup_automation_config', frappe.as_json(results))
        
        frappe.db.commit()
        
        frappe.logger().info("Backup automation setup completed successfully")
        
    except Exception as e:
        frappe.log_error(f"Backup automation setup failed: {str(e)}", "Backup Setup Error")
        raise
