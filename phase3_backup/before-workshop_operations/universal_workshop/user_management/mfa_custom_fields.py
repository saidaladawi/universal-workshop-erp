"""
Custom Fields for MFA Integration
Universal Workshop ERP - User Management
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_mfa_custom_fields():
    """Create custom fields required for MFA functionality"""
    
    mfa_custom_fields = {
        "User": [
            {
                "fieldname": "mfa_section",
                "fieldtype": "Section Break",
                "label": "Multi-Factor Authentication", 
                "insert_after": "new_password",
                "collapsible": 1
            },
            {
                "fieldname": "mfa_settings",
                "fieldtype": "JSON",
                "label": "MFA Settings",
                "insert_after": "mfa_section",
                "hidden": 1,
                "read_only": 1
            },
            {
                "fieldname": "mfa_enabled",
                "fieldtype": "Check",
                "label": "MFA Enabled",
                "insert_after": "mfa_settings", 
                "read_only": 1,
                "default": 0
            },
            {
                "fieldname": "mfa_method",
                "fieldtype": "Select",
                "label": "MFA Method",
                "insert_after": "mfa_enabled",
                "options": "TOTP\nSMS\nWhatsApp\nEmail",
                "read_only": 1,
                "depends_on": "eval:doc.mfa_enabled"
            }
        ]
    }
    
    create_custom_fields(mfa_custom_fields, update=True)
    print("✅ MFA custom fields created successfully")


def execute():
    """Main execution function"""
    create_mfa_custom_fields()
