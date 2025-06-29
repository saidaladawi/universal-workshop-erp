import frappe
from universal_workshop.universal_workshop.utils.data_integrity_checker import run_data_integrity_checks

def execute():
    """Execute comprehensive data integrity checks"""
    
    frappe.log_error("Starting data integrity checks", "Data Integrity")
    
    try:
        results = run_data_integrity_checks()
        
        # Log results to Error Log
        summary = f"""
Data Integrity Check Results:
- Total Checks: {results['total_checks']}
- Passed: {results['passed_checks']}
- Failed: {results['failed_checks']}
- Warnings: {results['warnings']}
- Critical Issues: {results['critical_issues']}
        """
        
        if results['critical_issues'] > 0:
            frappe.log_error(summary, "Data Integrity - Critical Issues")
        elif results['failed_checks'] > 0:
            frappe.log_error(summary, "Data Integrity - Failed Checks")
        else:
            frappe.logger().info(summary)
        
        # Store results in System Settings for dashboard access
        frappe.db.set_value('System Settings', None, 'data_integrity_last_check', frappe.utils.now())
        frappe.db.set_value('System Settings', None, 'data_integrity_results', frappe.as_json(results))
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Data integrity check failed: {str(e)}", "Data Integrity Error")
        raise
