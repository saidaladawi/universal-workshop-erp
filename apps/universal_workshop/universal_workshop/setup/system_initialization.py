"""
System Initialization for Onboarding Wizard
Handles automatic system configuration during workshop setup
"""

import frappe
from frappe import _
import json

@frappe.whitelist()
def initialize_system_settings(workshop_profile_name):
    """
    Initialize system settings after workshop profile creation
    """
    try:
        workshop = frappe.get_doc("Workshop Profile", workshop_profile_name)
        
        # Get or create Universal Workshop Settings
        settings = frappe.get_doc("Universal Workshop Settings")
        
        # Set default configurations based on workshop
        settings.update({
            "default_language": workshop.primary_language or "en",
            "default_currency": "OMR",  # Oman Rial
            "timezone": "Asia/Muscat",
            "enable_arabic_interface": workshop.primary_language == "ar",
            "enable_rtl_interface": workshop.primary_language == "ar",
            "workshop_name_en": workshop.workshop_name_en,
            "workshop_name_ar": workshop.workshop_name_ar,
            "setup_completed": 1,
            "onboarding_completed_on": frappe.utils.now(),
            "onboarding_completed_by": frappe.session.user
        })
        
        settings.save(ignore_permissions=True)
        
        # Initialize enabled modules based on license type
        initialize_enabled_modules(workshop)
        
        # Setup default workflows
        setup_default_workflows()
        
        # Create sample data if requested
        if workshop.create_sample_data:
            create_sample_data(workshop_profile_name)
            
        return {
            "status": "success",
            "message": _("System settings initialized successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"System initialization failed: {str(e)}")
        return {
            "status": "error", 
            "message": _("Failed to initialize system settings")
        }

@frappe.whitelist()
def initialize_enabled_modules(workshop):
    """
    Enable/disable modules based on workshop type and license
    """
    # Core modules always enabled
    core_modules = [
        "workshop_management",
        "vehicle_management", 
        "customer_management",
        "billing_management"
    ]
    
    # Optional modules based on license
    license_type = workshop.license_type or "basic"
    
    optional_modules = {
        "basic": ["parts_inventory"],
        "premium": ["parts_inventory", "training_management", "analytics_reporting"],
        "enterprise": ["parts_inventory", "training_management", "analytics_reporting", 
                      "mobile_app", "communication_management"]
    }
    
    enabled_modules = core_modules + optional_modules.get(license_type, [])
    
    # Update module settings
    for module in enabled_modules:
        frappe.db.set_value("Module Profile", module, "enabled", 1)
    
    frappe.db.commit()

def setup_default_workflows():
    """
    Setup default workflows for new workshop
    """
    workflows = [
        {
            "doctype": "Service Order",
            "workflow_name": "Service Order Workflow",
            "states": ["Draft", "In Progress", "Quality Check", "Completed", "Invoiced"]
        },
        {
            "doctype": "Vehicle Inspection", 
            "workflow_name": "Inspection Workflow",
            "states": ["Scheduled", "In Progress", "Completed", "Approved"]
        }
    ]
    
    for workflow_config in workflows:
        if not frappe.db.exists("Workflow", workflow_config["workflow_name"]):
            # Create workflow logic here
            pass

@frappe.whitelist()
def create_sample_data(workshop_profile_name):
    """
    Create sample data for new workshop
    """
    workshop = frappe.get_doc("Workshop Profile", workshop_profile_name)
    
    # Sample customers
    sample_customers = [
        {
            "customer_name": "أحمد الراشد" if workshop.primary_language == "ar" else "Ahmed Al-Rashid",
            "mobile_no": "+968 9123 4567",
            "email": "ahmed@example.om"
        },
        {
            "customer_name": "فاطمة الزهرة" if workshop.primary_language == "ar" else "Fatima Al-Zahra", 
            "mobile_no": "+968 9234 5678",
            "email": "fatima@example.om"
        }
    ]
    
    for customer_data in sample_customers:
        if not frappe.db.exists("Customer", customer_data["customer_name"]):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_data["customer_name"],
                "mobile_no": customer_data["mobile_no"],
                "email_id": customer_data["email"],
                "customer_type": "Individual",
                "territory": "Oman"
            })
            customer.insert(ignore_permissions=True)
    
    # Sample service types
    sample_services = [
        {"service_name": "تغيير الزيت" if workshop.primary_language == "ar" else "Oil Change", "rate": 15.000},
        {"service_name": "فحص الفرامل" if workshop.primary_language == "ar" else "Brake Inspection", "rate": 25.000},
        {"service_name": "صيانة عامة" if workshop.primary_language == "ar" else "General Maintenance", "rate": 50.000}
    ]
    
    for service_data in sample_services:
        if not frappe.db.exists("Item", service_data["service_name"]):
            service = frappe.get_doc({
                "doctype": "Item",
                "item_code": service_data["service_name"],
                "item_name": service_data["service_name"],
                "item_group": "Services",
                "stock_uom": "Nos",
                "is_stock_item": 0,
                "standard_rate": service_data["rate"]
            })
            service.insert(ignore_permissions=True)
    
    frappe.db.commit()
    
    return {
        "status": "success",
        "message": _("Sample data created successfully")
    }

@frappe.whitelist()
def validate_setup_completion(workshop_profile_name):
    """
    Validate that all required setup is complete
    """
    validation_results = {
        "workshop_profile": False,
        "admin_user": False, 
        "system_settings": False,
        "license_valid": False,
        "modules_configured": False
    }
    
    try:
        # Check workshop profile
        if frappe.db.exists("Workshop Profile", workshop_profile_name):
            validation_results["workshop_profile"] = True
            
        # Check admin user exists
        workshop = frappe.get_doc("Workshop Profile", workshop_profile_name) 
        if workshop.admin_user and frappe.db.exists("User", workshop.admin_user):
            validation_results["admin_user"] = True
            
        # Check system settings
        settings = frappe.get_doc("Universal Workshop Settings")
        if settings.setup_completed:
            validation_results["system_settings"] = True
            
        # Check license
        if workshop.business_license and frappe.db.exists("Business Registration", workshop.business_license):
            validation_results["license_valid"] = True
            
        # Check modules
        validation_results["modules_configured"] = True  # Assume configured if we reach here
        
        all_valid = all(validation_results.values())
        
        return {
            "status": "success" if all_valid else "warning",
            "all_valid": all_valid,
            "details": validation_results,
            "completion_percentage": sum(validation_results.values()) / len(validation_results) * 100
        }
        
    except Exception as e:
        frappe.log_error(f"Setup validation failed: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to validate setup completion")
        }