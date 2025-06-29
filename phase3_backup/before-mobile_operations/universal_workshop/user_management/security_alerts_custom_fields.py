"""
Security Alerts Custom DocType Setup
Universal Workshop ERP - User Management
"""

import frappe
from frappe import _


def create_security_alert_log_doctype():
    """Create Security Alert Log DocType"""
    
    if frappe.db.exists("DocType", "Security Alert Log"):
        print("Security Alert Log DocType already exists")
        return
    
    try:
        doctype = frappe.new_doc("DocType")
        doctype.name = "Security Alert Log"
        doctype.module = "User Management"
        doctype.custom = 1
        doctype.is_submittable = 0
        doctype.track_changes = 0
        doctype.autoname = "hash"
        doctype.title_field = "description"
        doctype.sort_field = "timestamp"
        doctype.sort_order = "DESC"
        
        # Alert type options
        alert_type_options = "\n".join([
            "failed_login",
            "multiple_failed_logins", 
            "permission_change",
            "suspicious_activity",
            "mfa_disabled",
            "session_anomaly"
        ])
        
        # Severity options
        severity_options = "\n".join([
            "info",
            "medium",
            "high", 
            "critical"
        ])
        
        # Escalation level options
        escalation_options = "\n".join([
            "none",
            "supervisor",
            "manager",
            "administrator",
            "emergency"
        ])
        
        # Define fields
        fields = [
            {
                "fieldname": "alert_id",
                "fieldtype": "Data",
                "label": "Alert ID",
                "unique": 1,
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "alert_type", 
                "fieldtype": "Select",
                "label": "Alert Type",
                "options": alert_type_options,
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
                "in_list_view": 1
            },
            {
                "fieldname": "user_email",
                "fieldtype": "Data",
                "label": "User Email",
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "source_ip",
                "fieldtype": "Data",
                "label": "Source IP"
            },
            {
                "fieldname": "description",
                "fieldtype": "Small Text",
                "label": "Description",
                "reqd": 1
            },
            {
                "fieldname": "details",
                "fieldtype": "Long Text",
                "label": "Event Details (JSON)"
            },
            {
                "fieldname": "escalation_level",
                "fieldtype": "Select",
                "label": "Escalation Level",
                "options": escalation_options
            },
            {
                "fieldname": "notifications_sent",
                "fieldtype": "Long Text", 
                "label": "Notifications Sent (JSON)"
            },
            {
                "fieldname": "is_resolved",
                "fieldtype": "Check",
                "label": "Is Resolved",
                "default": 0
            },
            {
                "fieldname": "resolved_by",
                "fieldtype": "Link",
                "label": "Resolved By",
                "options": "User"
            },
            {
                "fieldname": "resolved_at",
                "fieldtype": "Datetime",
                "label": "Resolved At"
            },
            {
                "fieldname": "resolution_notes",
                "fieldtype": "Text",
                "label": "Resolution Notes"
            }
        ]
        
        # Add fields to DocType
        for field_dict in fields:
            field = frappe.new_doc("DocField")
            field.update(field_dict)
            doctype.fields.append(field)
        
        # Insert DocType
        doctype.insert()
        frappe.db.commit()
        
        print(f"Created Security Alert Log DocType successfully")
        
    except Exception as e:
        print(f"Error creating Security Alert Log DocType: {e}")
        frappe.log_error(f"Error creating Security Alert Log DocType: {e}")


def create_security_alert_settings_doctype():
    """Create Security Alert Settings single DocType for configuration"""
    
    if frappe.db.exists("DocType", "Security Alert Settings"):
        print("Security Alert Settings DocType already exists")
        return
    
    try:
        doctype = frappe.new_doc("DocType")
        doctype.name = "Security Alert Settings"
        doctype.module = "User Management"
        doctype.custom = 1
        doctype.is_submittable = 0
        doctype.issingle = 1
        doctype.track_changes = 1
        
        # Define fields
        fields = [
            {
                "fieldname": "alert_thresholds",
                "fieldtype": "Long Text",
                "label": "Alert Thresholds (JSON)",
                "description": "JSON configuration for alert thresholds"
            },
            {
                "fieldname": "notification_settings",
                "fieldtype": "Section Break",
                "label": "Notification Settings"
            },
            {
                "fieldname": "enable_email_alerts",
                "fieldtype": "Check",
                "label": "Enable Email Alerts",
                "default": 1
            },
            {
                "fieldname": "enable_sms_alerts",
                "fieldtype": "Check", 
                "label": "Enable SMS Alerts",
                "default": 1
            },
            {
                "fieldname": "enable_whatsapp_alerts",
                "fieldtype": "Check",
                "label": "Enable WhatsApp Alerts", 
                "default": 1
            },
            {
                "fieldname": "enable_in_app_alerts",
                "fieldtype": "Check",
                "label": "Enable In-App Alerts",
                "default": 1
            }
        ]
        
        # Add fields to DocType
        for field_dict in fields:
            field = frappe.new_doc("DocField")
            field.update(field_dict)
            doctype.fields.append(field)
        
        # Insert DocType
        doctype.insert()
        frappe.db.commit()
        
        print(f"Created Security Alert Settings DocType successfully")
        
    except Exception as e:
        print(f"Error creating Security Alert Settings DocType: {e}")
        frappe.log_error(f"Error creating Security Alert Settings DocType: {e}")


def setup_security_alerts():
    """Setup security alerts system"""
    
    print("Setting up Security Alerts system...")
    
    # Create DocTypes
    create_security_alert_log_doctype()
    create_security_alert_settings_doctype()
    
    print("Security Alerts setup completed successfully!")


if __name__ == "__main__":
    setup_security_alerts()
