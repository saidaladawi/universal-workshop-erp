# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def get_context(context):
    """Get context for workshop onboarding web form"""
    
    # Check if this is license-based setup
    license_has_data = frappe.db.get_default("license_has_workshop_data") == "1"
    
    context['license_mode'] = license_has_data
    context['setup_mode'] = "admin_only" if license_has_data else "full"
    
    if license_has_data:
        # Get workshop data from license for display
        try:
            business_reg = frappe.get_doc(
                "Business Registration", 
                {"verification_status": "Verified"}
            )
            context['license_data'] = {
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
        except Exception as e:
            frappe.log_error(f"Error getting license data: {e}")
            context['license_data'] = {}
    
    return context


@frappe.whitelist()
def create_admin_and_complete_setup(admin_data):
    """Create admin user and complete license-based setup"""
    try:
        # Validate admin data
        wizard = frappe.get_module("universal_workshop.workshop_management.api.onboarding_wizard")
        validation_result = wizard.OnboardingWizard().validate_admin_account(admin_data)
        
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
        result = wizard.complete_onboarding(progress.name)
        
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