"""
Audit Trail Custom DocType Setup
Universal Workshop ERP - User Management
"""

import frappe
from frappe import _


def create_security_audit_log_doctype():
    """Create Security Audit Log DocType"""
    
    if frappe.db.exists("DocType", "Security Audit Log"):
        print("Security Audit Log DocType already exists")
        return
    
    try:
        doctype = frappe.new_doc("DocType")
        doctype.name = "Security Audit Log"
        doctype.module = "User Management"
        doctype.custom = 1
        doctype.is_submittable = 0
        doctype.track_changes = 0
        doctype.autoname = "hash"
        doctype.title_field = "event_type"
        doctype.sort_field = "timestamp"
        doctype.sort_order = "DESC"
        
        # Event type options
        event_type_options = """login_success
login_failed
logout
mfa_enabled
mfa_disabled
session_created
session_revoked
role_assigned
permission_granted
suspicious_activity"""
        
        # Severity options
        severity_options = """info
medium
high
critical"""
        
        # Fields
        fields = [
            {
                "fieldname": "event_id",
                "fieldtype": "Data",
                "label": "Event ID",
                "unique": 1,
                "reqd": 1,
                "read_only": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "event_type",
                "fieldtype": "Select",
                "label": "Event Type",
                "options": event_type_options,
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "severity",
                "fieldtype": "Select",
                "label": "Severity",
                "options": severity_options,
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "timestamp",
                "fieldtype": "Datetime",
                "label": "Timestamp",
                "reqd": 1,
                "in_list_view": 1,
                "read_only": 1
            },
            {
                "fieldname": "user_email",
                "fieldtype": "Link",
                "options": "User",
                "label": "User",
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "description",
                "fieldtype": "Text",
                "label": "Description"
            },
            {
                "fieldname": "details",
                "fieldtype": "JSON",
                "label": "Event Details"
            }
        ]

        for field in fields:
            field["parent"] = "Security Audit Log"
            field["parenttype"] = "DocType"
            field["parentfield"] = "fields"
            doctype.append("fields", field)

        # Permissions
        permissions = [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 0
            }
        ]
        
        for perm in permissions:
            perm["parent"] = "Security Audit Log"
            perm["parenttype"] = "DocType"
            perm["parentfield"] = "permissions"
            doctype.append("permissions", perm)

        doctype.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print("Security Audit Log DocType created successfully")
        
    except Exception as e:
        print(f"Error creating Security Audit Log DocType: {e}")


def setup_audit_trail():
    """Setup audit trail extension"""
    print("Setting up audit trail extension...")
    create_security_audit_log_doctype()
    frappe.clear_cache()
    print("Audit trail extension setup completed!")


if __name__ == "__main__":
    setup_audit_trail()
