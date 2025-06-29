# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_context(context):
    """Get context for admin setup page"""
    
    # Check if this is license-based setup
    license_has_data = frappe.db.get_default("license_has_workshop_data") == "1"
    
    if not license_has_data:
        # Redirect to full onboarding if no license
        frappe.local.flags.redirect_location = "/workshop-onboarding"
        raise frappe.Redirect
    
    # Check if setup is already complete
    from universal_workshop.boot import check_initial_setup_status
    setup_status = check_initial_setup_status()
    
    if setup_status.get("setup_complete"):
        frappe.local.flags.redirect_location = "/app"
        raise frappe.Redirect
    
    context.setup_mode = "admin_only"
    context.license_mode = True
    
    # Get workshop data from license for display
    try:
        business_regs = frappe.get_list(
            "Business Registration", 
            filters={"verification_status": "Verified"},
            fields=["*"],
            limit=1
        )
        
        if business_regs:
            business_reg = frappe.get_doc("Business Registration", business_regs[0].name)
            context.license_data = {
                "workshop_name": business_reg.business_name_en,
                "workshop_name_ar": business_reg.business_name_ar,
                "owner_name": business_reg.owner_name_en,
                "owner_name_ar": business_reg.owner_name_ar,
                "business_license": business_reg.business_license_number,
                "phone": business_reg.phone_number,
                "email": business_reg.email,
                "address": business_reg.address,
                "city": business_reg.city,
                "governorate": business_reg.governorate
            }
        else:
            context.license_data = {}
    except Exception as e:
        frappe.log_error(f"Error getting license data: {e}")
        context.license_data = {}
    
    return context


@frappe.whitelist()
def create_admin_and_complete_setup(admin_data):
    """Create admin user and complete license-based setup"""
    try:
        import json
        if isinstance(admin_data, str):
            admin_data = json.loads(admin_data)
            
        # Validate admin data
        from universal_workshop.workshop_management.api.onboarding_wizard import OnboardingWizard
        wizard = OnboardingWizard()
        validation_result = wizard.validate_admin_account(admin_data)
        
        if not validation_result.get("valid"):
            return {
                "success": False,
                "errors": validation_result.get("errors", [])
            }
        
        # Create onboarding progress record
        progress = frappe.new_doc("Onboarding Progress")
        progress.user = frappe.session.user
        progress.current_step = 0
        progress.completed_steps = frappe.as_json(["admin_account"])
        progress.data = frappe.as_json({"admin_account": admin_data})
        progress.insert()
        
        # Complete onboarding
        from universal_workshop.workshop_management.api.onboarding_wizard import complete_onboarding
        result = complete_onboarding(progress.name)
        
        if result.get("success"):
            return {
                "success": True,
                "message": _("Administrator account created successfully"),
                "redirect_url": "/login"
            }
        else:
            return result
            
    except Exception as e:
        frappe.log_error(f"Error in admin setup: {e}")
        return {
            "success": False,
            "errors": [str(e)]
        }