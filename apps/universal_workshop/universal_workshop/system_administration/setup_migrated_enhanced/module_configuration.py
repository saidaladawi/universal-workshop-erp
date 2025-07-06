"""
Module Configuration for Universal Workshop
Handles module enablement/disablement during onboarding
"""

import frappe
from frappe import _

@frappe.whitelist()
def get_available_modules():
    """
    Get list of available modules with descriptions
    """
    modules = {
        "core": {
            "workshop_management": {
                "name": _("Workshop Management"),
                "description": _("Core workshop operations, service orders, appointments"),
                "required": True,
                "icon": "🔧"
            },
            "vehicle_management": {
                "name": _("Vehicle Management"), 
                "description": _("VIN decoding, vehicle registry, service history"),
                "required": True,
                "icon": "🚗"
            },
            "customer_management": {
                "name": _("Customer Management"),
                "description": _("CRM with Arabic support, loyalty programs"),
                "required": True,
                "icon": "👥"
            },
            "billing_management": {
                "name": _("Billing Management"),
                "description": _("Omani VAT compliance, financial reporting"),
                "required": True,
                "icon": "💰"
            }
        },
        "optional": {
            "parts_inventory": {
                "name": _("Parts Inventory"),
                "description": _("Inventory management with barcode scanning"),
                "required": False,
                "icon": "📦",
                "license_required": "basic"
            },
            "training_management": {
                "name": _("Training Management"),
                "description": _("Technician training and certification tracking"),
                "required": False,
                "icon": "🎓",
                "license_required": "premium"
            },
            "analytics_reporting": {
                "name": _("Analytics & Reporting"),
                "description": _("KPI dashboards and business intelligence"),
                "required": False,
                "icon": "📊",
                "license_required": "premium"
            },
            "mobile_app": {
                "name": _("Mobile App"),
                "description": _("PWA and mobile interface for technicians"),
                "required": False,
                "icon": "📱",
                "license_required": "enterprise"
            },
            "communication_management": {
                "name": _("Communication Management"),
                "description": _("SMS notifications and customer communication"),
                "required": False,
                "icon": "📞",
                "license_required": "enterprise"
            },
            "user_management": {
                "name": _("User Management"),
                "description": _("Enhanced security and session management"),
                "required": False,
                "icon": "🔐",
                "license_required": "basic"
            }
        }
    }
    
    return modules

@frappe.whitelist()
def configure_modules_for_license(license_type="basic", selected_modules=None):
    """
    Configure modules based on license type and user selection
    """
    if selected_modules:
        selected_modules = frappe.parse_json(selected_modules)
    else:
        selected_modules = []
    
    available_modules = get_available_modules()
    license_permissions = {
        "basic": ["parts_inventory", "user_management"],
        "premium": ["parts_inventory", "user_management", "training_management", "analytics_reporting"],
        "enterprise": ["parts_inventory", "user_management", "training_management", 
                      "analytics_reporting", "mobile_app", "communication_management"]
    }
    
    # Always enable core modules
    enabled_modules = list(available_modules["core"].keys())
    
    # Add optional modules based on license and selection
    allowed_optional = license_permissions.get(license_type, [])
    for module in selected_modules:
        if module in allowed_optional:
            enabled_modules.append(module)
    
    # Update module settings in database
    update_module_settings(enabled_modules)
    
    return {
        "status": "success",
        "enabled_modules": enabled_modules,
        "message": _("Modules configured successfully")
    }

def update_module_settings(enabled_modules):
    """
    Update module settings in Universal Workshop Settings
    """
    try:
        settings = frappe.get_doc("Universal Workshop Settings")
        
        # Create module configuration field if it doesn't exist
        module_config = {}
        for module in enabled_modules:
            module_config[module] = {
                "enabled": True,
                "configured_on": frappe.utils.now(),
                "configured_by": frappe.session.user
            }
        
        settings.module_configuration = frappe.as_json(module_config)
        settings.save(ignore_permissions=True)
        
        # Also update in Module Def if exists
        for module in enabled_modules:
            if frappe.db.exists("Module Def", module):
                frappe.db.set_value("Module Def", module, "disabled", 0)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Module settings update failed: {str(e)}")
        raise

@frappe.whitelist()
def get_module_configuration():
    """
    Get current module configuration
    """
    try:
        settings = frappe.get_doc("Universal Workshop Settings")
        
        if settings.module_configuration:
            config = frappe.parse_json(settings.module_configuration)
        else:
            config = {}
        
        available_modules = get_available_modules()
        
        # Merge with available modules info
        result = {
            "configured_modules": config,
            "available_modules": available_modules,
            "last_updated": settings.modified
        }
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Get module configuration failed: {str(e)}")
        return {
            "configured_modules": {},
            "available_modules": get_available_modules(),
            "error": str(e)
        }

@frappe.whitelist()
def validate_module_dependencies():
    """
    Validate that required module dependencies are met
    """
    dependencies = {
        "training_management": ["user_management"],
        "analytics_reporting": ["workshop_management", "billing_management"],
        "mobile_app": ["workshop_management", "customer_management"],
        "communication_management": ["customer_management"]
    }
    
    try:
        settings = frappe.get_doc("Universal Workshop Settings")
        if not settings.module_configuration:
            return {"status": "success", "message": "No modules configured yet"}
            
        config = frappe.parse_json(settings.module_configuration)
        enabled_modules = [module for module, data in config.items() if data.get("enabled")]
        
        missing_dependencies = {}
        
        for module in enabled_modules:
            if module in dependencies:
                for dependency in dependencies[module]:
                    if dependency not in enabled_modules:
                        if module not in missing_dependencies:
                            missing_dependencies[module] = []
                        missing_dependencies[module].append(dependency)
        
        if missing_dependencies:
            return {
                "status": "warning",
                "missing_dependencies": missing_dependencies,
                "message": _("Some modules have missing dependencies")
            }
        
        return {
            "status": "success", 
            "message": _("All module dependencies are satisfied")
        }
        
    except Exception as e:
        frappe.log_error(f"Module dependency validation failed: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to validate module dependencies")
        }