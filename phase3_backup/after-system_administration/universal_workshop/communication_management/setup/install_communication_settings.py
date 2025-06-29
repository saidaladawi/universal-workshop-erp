# -*- coding: utf-8 -*-
"""
Install Communication Settings for Universal Workshop ERP
Sets up Twilio configuration and default templates
"""

import frappe
from frappe import _


def install_communication_settings():
    """Install communication management settings and templates"""
    try:
        frappe.logger().info("Installing Universal Workshop Communication Settings...")

        # Create Communication Settings DocType if it doesn't exist
        create_communication_settings_doctype()

        # Set up default communication settings
        setup_default_communication_settings()

        # Create default SMS and WhatsApp templates
        create_default_templates()

        # Set up custom fields for communication tracking
        setup_communication_custom_fields()

        frappe.logger().info("Communication Settings installation completed successfully")

    except Exception as e:
        frappe.logger().error(f"Error installing communication settings: {str(e)}")
        raise


def create_communication_settings_doctype():
    """Create Communication Settings DocType for Twilio configuration"""
    try:
        if frappe.db.exists("DocType", "Communication Settings"):
            return

        # Create Communication Settings DocType
        communication_settings = frappe.new_doc("DocType")
        communication_settings.name = "Communication Settings"
        communication_settings.module = "Communication Management"
        communication_settings.custom = 1
        communication_settings.issingle = 1
        communication_settings.istable = 0
        communication_settings.is_virtual = 0
        communication_settings.track_changes = 1
        communication_settings.fields = [
            {
                "fieldname": "twilio_section",
                "fieldtype": "Section Break",
                "label": "Twilio Configuration",
                "collapsible": 0,
            },
            {
                "fieldname": "twilio_account_sid",
                "fieldtype": "Data",
                "label": "Twilio Account SID",
                "reqd": 1,
                "description": "Your Twilio Account SID",
            },
            {
                "fieldname": "twilio_auth_token",
                "fieldtype": "Password",
                "label": "Twilio Auth Token",
                "reqd": 1,
                "description": "Your Twilio Auth Token",
            },
            {"fieldname": "col_break_1", "fieldtype": "Column Break"},
            {
                "fieldname": "twilio_from_phone",
                "fieldtype": "Data",
                "label": "Twilio Phone Number",
                "reqd": 1,
                "description": "Your Twilio phone number (e.g., +1234567890)",
            },
            {
                "fieldname": "twilio_whatsapp_from",
                "fieldtype": "Data",
                "label": "WhatsApp From Number",
                "description": "WhatsApp Business number (e.g., whatsapp:+1234567890)",
            },
            {
                "fieldname": "oman_compliance_section",
                "fieldtype": "Section Break",
                "label": "Oman Compliance Settings",
                "collapsible": 0,
            },
            {
                "fieldname": "sender_registration_required",
                "fieldtype": "Check",
                "label": "Sender Registration Required",
                "default": 1,
                "description": "Require sender registration for Oman compliance",
            },
            {
                "fieldname": "content_filtering_enabled",
                "fieldtype": "Check",
                "label": "Enable Content Filtering",
                "default": 1,
                "description": "Filter content for Oman/UAE compliance",
            },
            {"fieldname": "col_break_2", "fieldtype": "Column Break"},
            {
                "fieldname": "business_hours_start",
                "fieldtype": "Time",
                "label": "Business Hours Start",
                "default": "07:00:00",
                "description": "Start time for promotional messages",
            },
            {
                "fieldname": "business_hours_end",
                "fieldtype": "Time",
                "label": "Business Hours End",
                "default": "21:00:00",
                "description": "End time for promotional messages",
            },
            {
                "fieldname": "default_settings_section",
                "fieldtype": "Section Break",
                "label": "Default Settings",
                "collapsible": 0,
            },
            {
                "fieldname": "default_language",
                "fieldtype": "Select",
                "label": "Default Language",
                "options": "ar\\nen",
                "default": "ar",
                "description": "Default language for communications",
            },
            {
                "fieldname": "auto_send_invoice_sms",
                "fieldtype": "Check",
                "label": "Auto Send Invoice SMS",
                "default": 1,
                "description": "Automatically send SMS when invoice is submitted",
            },
            {"fieldname": "col_break_3", "fieldtype": "Column Break"},
            {
                "fieldname": "auto_send_appointment_confirmation",
                "fieldtype": "Check",
                "label": "Auto Send Appointment Confirmation",
                "default": 1,
                "description": "Automatically send confirmation when appointment is created",
            },
            {
                "fieldname": "auto_send_service_completion",
                "fieldtype": "Check",
                "label": "Auto Send Service Completion",
                "default": 1,
                "description": "Automatically notify when service is completed",
            },
        ]

        communication_settings.insert()
        frappe.db.commit()

        frappe.logger().info("Communication Settings DocType created successfully")

    except Exception as e:
        frappe.logger().error(f"Error creating Communication Settings DocType: {str(e)}")
        raise


def setup_default_communication_settings():
    """Set up default communication settings"""
    try:
        # Create default Communication Settings record
        if not frappe.db.exists("Communication Settings", "Communication Settings"):
            settings = frappe.new_doc("Communication Settings")
            settings.name = "Communication Settings"
            settings.default_language = "ar"
            settings.business_hours_start = "07:00:00"
            settings.business_hours_end = "21:00:00"
            settings.sender_registration_required = 1
            settings.content_filtering_enabled = 1
            settings.auto_send_invoice_sms = 1
            settings.auto_send_appointment_confirmation = 1
            settings.auto_send_service_completion = 1
            settings.insert()

            frappe.logger().info("Default Communication Settings created")

    except Exception as e:
        frappe.logger().error(f"Error setting up default communication settings: {str(e)}")
        raise


def create_default_templates():
    """Create default SMS and WhatsApp templates"""
    try:
        # Create SMS Template DocType if it doesn't exist
        create_sms_template_doctype()

        # Create WhatsApp Template DocType if it doesn't exist
        create_whatsapp_template_doctype()

        # Create default templates
        create_default_sms_templates()
        create_default_whatsapp_templates()

    except Exception as e:
        frappe.logger().error(f"Error creating default templates: {str(e)}")
        raise


def create_sms_template_doctype():
    """Create SMS Template DocType"""
    try:
        if frappe.db.exists("DocType", "SMS Template"):
            return

        sms_template = frappe.new_doc("DocType")
        sms_template.name = "SMS Template"
        sms_template.module = "Communication Management"
        sms_template.custom = 1
        sms_template.naming_rule = "By fieldname"
        sms_template.autoname = "field:template_name"
        sms_template.fields = [
            {
                "fieldname": "template_name",
                "fieldtype": "Data",
                "label": "Template Name",
                "reqd": 1,
                "unique": 1,
            },
            {
                "fieldname": "language",
                "fieldtype": "Select",
                "label": "Language",
                "options": "ar\\nen",
                "default": "ar",
                "reqd": 1,
            },
            {
                "fieldname": "template_type",
                "fieldtype": "Select",
                "label": "Template Type",
                "options": "appointment\\ninvoice\\nquotation\\nservice_completion\\nreminder",
                "reqd": 1,
            },
            {
                "fieldname": "template_content",
                "fieldtype": "Long Text",
                "label": "Template Content",
                "reqd": 1,
                "description": "Use {{variable_name}} for dynamic content",
            },
            {"fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "default": 1},
            {"fieldname": "description", "fieldtype": "Text", "label": "Description"},
        ]

        sms_template.insert()
        frappe.db.commit()

        frappe.logger().info("SMS Template DocType created successfully")

    except Exception as e:
        frappe.logger().error(f"Error creating SMS Template DocType: {str(e)}")
        raise


def create_whatsapp_template_doctype():
    """Create WhatsApp Template DocType"""
    try:
        if frappe.db.exists("DocType", "WhatsApp Template"):
            return

        whatsapp_template = frappe.new_doc("DocType")
        whatsapp_template.name = "WhatsApp Template"
        whatsapp_template.module = "Communication Management"
        whatsapp_template.custom = 1
        whatsapp_template.naming_rule = "By fieldname"
        whatsapp_template.autoname = "field:template_name"
        whatsapp_template.fields = [
            {
                "fieldname": "template_name",
                "fieldtype": "Data",
                "label": "Template Name",
                "reqd": 1,
                "unique": 1,
            },
            {
                "fieldname": "language",
                "fieldtype": "Select",
                "label": "Language",
                "options": "ar\\nen",
                "default": "ar",
                "reqd": 1,
            },
            {
                "fieldname": "template_type",
                "fieldtype": "Select",
                "label": "Template Type",
                "options": "appointment_confirmation\\ninvoice_with_qr\\nservice_quotation\\nvehicle_ready",
                "reqd": 1,
            },
            {
                "fieldname": "template_content",
                "fieldtype": "Long Text",
                "label": "Template Content",
                "reqd": 1,
                "description": "Use {{variable_name}} for dynamic content",
            },
            {
                "fieldname": "is_approved",
                "fieldtype": "Check",
                "label": "Is Approved",
                "default": 0,
                "description": "WhatsApp template must be approved by Meta",
            },
            {"fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "default": 1},
            {"fieldname": "description", "fieldtype": "Text", "label": "Description"},
        ]

        whatsapp_template.insert()
        frappe.db.commit()

        frappe.logger().info("WhatsApp Template DocType created successfully")

    except Exception as e:
        frappe.logger().error(f"Error creating WhatsApp Template DocType: {str(e)}")
        raise


def create_default_sms_templates():
    """Create default SMS templates in Arabic and English"""
    try:
        templates = [
            # Arabic Templates
            {
                "template_name": "appointment_reminder_ar",
                "language": "ar",
                "template_type": "appointment",
                "template_content": "مرحباً {{customer_name}}، نذكركم بموعد الخدمة يوم {{appointment_date}} الساعة {{appointment_time}} لخدمة {{service_type}}. ورشة {{workshop_name}} - {{workshop_phone}}",
                "description": "Arabic appointment reminder template",
            },
            {
                "template_name": "invoice_notification_ar",
                "language": "ar",
                "template_type": "invoice",
                "template_content": "عزيزنا {{customer_name}}، تم إصدار فاتورة رقم {{invoice_number}} بمبلغ {{total_amount}} {{currency}} للمركبة {{vehicle_number}}. ورشة {{workshop_name}}",
                "description": "Arabic invoice notification template",
            },
            {
                "template_name": "service_completion_ar",
                "language": "ar",
                "template_type": "service_completion",
                "template_content": "مرحباً {{customer_name}}، تم إنجاز خدمة {{service_completed}} للمركبة {{vehicle_number}}. يمكنكم استلام المركبة. المبلغ الإجمالي: {{final_amount}} {{currency}}. ورشة {{workshop_name}}",
                "description": "Arabic service completion template",
            },
            # English Templates
            {
                "template_name": "appointment_reminder_en",
                "language": "en",
                "template_type": "appointment",
                "template_content": "Hello {{customer_name}}, reminder for your {{service_type}} appointment on {{appointment_date}} at {{appointment_time}}. {{workshop_name}} - {{workshop_phone}}",
                "description": "English appointment reminder template",
            },
            {
                "template_name": "invoice_notification_en",
                "language": "en",
                "template_type": "invoice",
                "template_content": "Dear {{customer_name}}, invoice {{invoice_number}} has been generated for {{total_amount}} {{currency}} for vehicle {{vehicle_number}}. {{workshop_name}}",
                "description": "English invoice notification template",
            },
            {
                "template_name": "service_completion_en",
                "language": "en",
                "template_type": "service_completion",
                "template_content": "Hello {{customer_name}}, service {{service_completed}} completed for vehicle {{vehicle_number}}. Ready for pickup. Total amount: {{final_amount}} {{currency}}. {{workshop_name}}",
                "description": "English service completion template",
            },
        ]

        for template_data in templates:
            if not frappe.db.exists("SMS Template", template_data["template_name"]):
                template = frappe.new_doc("SMS Template")
                template.update(template_data)
                template.insert()

        frappe.db.commit()
        frappe.logger().info("Default SMS templates created successfully")

    except Exception as e:
        frappe.logger().error(f"Error creating default SMS templates: {str(e)}")
        raise


def create_default_whatsapp_templates():
    """Create default WhatsApp templates (need Meta approval)"""
    try:
        templates = [
            # Arabic WhatsApp Templates
            {
                "template_name": "appointment_confirmation_ar",
                "language": "ar",
                "template_type": "appointment_confirmation",
                "template_content": "مرحباً {{customer_name}}، تم تأكيد موعد الخدمة:\\nالتاريخ: {{appointment_date}}\\nالوقت: {{appointment_time}}\\nنوع الخدمة: {{service_type}}\\nرقم المركبة: {{vehicle_number}}\\nالورشة: {{workshop_name}}\\nالعنوان: {{workshop_address}}\\nللاستفسار: {{workshop_phone}}",
                "description": "Arabic appointment confirmation WhatsApp template",
                "is_approved": 0,  # Needs Meta approval
            },
            {
                "template_name": "invoice_with_qr_ar",
                "language": "ar",
                "template_type": "invoice_with_qr",
                "template_content": "عزيزنا {{customer_name}}،\\nفاتورة رقم: {{invoice_number}}\\nتاريخ الفاتورة: {{invoice_date}}\\nرقم المركبة: {{vehicle_number}}\\nالخدمة: {{service_description}}\\nالمبلغ الصافي: {{net_amount}} {{currency}}\\nضريبة القيمة المضافة: {{vat_amount}} {{currency}}\\nالمجموع: {{total_amount}} {{currency}}\\nرمز QR: {{qr_code}}\\nورشة {{workshop_name}}\\nرقم الضريبة: {{workshop_vat_number}}",
                "description": "Arabic invoice with QR code WhatsApp template",
                "is_approved": 0,
            },
            # English WhatsApp Templates
            {
                "template_name": "appointment_confirmation_en",
                "language": "en",
                "template_type": "appointment_confirmation",
                "template_content": "Hello {{customer_name}}, your service appointment is confirmed:\\nDate: {{appointment_date}}\\nTime: {{appointment_time}}\\nService: {{service_type}}\\nVehicle: {{vehicle_number}}\\nWorkshop: {{workshop_name}}\\nAddress: {{workshop_address}}\\nContact: {{workshop_phone}}",
                "description": "English appointment confirmation WhatsApp template",
                "is_approved": 0,
            },
            {
                "template_name": "invoice_with_qr_en",
                "language": "en",
                "template_type": "invoice_with_qr",
                "template_content": "Dear {{customer_name}},\\nInvoice No: {{invoice_number}}\\nDate: {{invoice_date}}\\nVehicle: {{vehicle_number}}\\nService: {{service_description}}\\nNet Amount: {{net_amount}} {{currency}}\\nVAT: {{vat_amount}} {{currency}}\\nTotal: {{total_amount}} {{currency}}\\nQR Code: {{qr_code}}\\n{{workshop_name}}\\nVAT No: {{workshop_vat_number}}",
                "description": "English invoice with QR code WhatsApp template",
                "is_approved": 0,
            },
        ]

        for template_data in templates:
            if not frappe.db.exists("WhatsApp Template", template_data["template_name"]):
                template = frappe.new_doc("WhatsApp Template")
                template.update(template_data)
                template.insert()

        frappe.db.commit()
        frappe.logger().info("Default WhatsApp templates created successfully")

    except Exception as e:
        frappe.logger().error(f"Error creating default WhatsApp templates: {str(e)}")
        raise


def setup_communication_custom_fields():
    """Set up custom fields for communication tracking"""
    try:
        # Customer communication preferences
        customer_fields = [
            {
                "fieldname": "communication_section",
                "fieldtype": "Section Break",
                "label": "Communication Preferences",
                "insert_after": "mobile_no",
            },
            {
                "fieldname": "preferred_language",
                "fieldtype": "Select",
                "label": "Preferred Language",
                "options": "ar\\nen",
                "default": "ar",
                "insert_after": "communication_section",
            },
            {
                "fieldname": "sms_notifications",
                "fieldtype": "Check",
                "label": "SMS Notifications",
                "default": 1,
                "insert_after": "preferred_language",
            },
            {
                "fieldname": "whatsapp_notifications",
                "fieldtype": "Check",
                "label": "WhatsApp Notifications",
                "default": 1,
                "insert_after": "sms_notifications",
            },
            {
                "fieldname": "email_notifications",
                "fieldtype": "Check",
                "label": "Email Notifications",
                "default": 1,
                "insert_after": "whatsapp_notifications",
            },
        ]

        for field in customer_fields:
            if not frappe.db.exists(
                "Custom Field", {"dt": "Customer", "fieldname": field["fieldname"]}
            ):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = "Customer"
                custom_field.update(field)
                custom_field.insert()

        # Sales Invoice communication tracking
        invoice_fields = [
            {
                "fieldname": "communication_tracking_section",
                "fieldtype": "Section Break",
                "label": "Communication Tracking",
                "insert_after": "terms",
            },
            {
                "fieldname": "whatsapp_sent",
                "fieldtype": "Check",
                "label": "WhatsApp Sent",
                "default": 0,
                "read_only": 1,
                "insert_after": "communication_tracking_section",
            },
            {
                "fieldname": "whatsapp_sent_at",
                "fieldtype": "Datetime",
                "label": "WhatsApp Sent At",
                "read_only": 1,
                "insert_after": "whatsapp_sent",
            },
            {
                "fieldname": "sms_sent",
                "fieldtype": "Check",
                "label": "SMS Sent",
                "default": 0,
                "read_only": 1,
                "insert_after": "whatsapp_sent_at",
            },
            {
                "fieldname": "sms_sent_at",
                "fieldtype": "Datetime",
                "label": "SMS Sent At",
                "read_only": 1,
                "insert_after": "sms_sent",
            },
        ]

        for field in invoice_fields:
            if not frappe.db.exists(
                "Custom Field", {"dt": "Sales Invoice", "fieldname": field["fieldname"]}
            ):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = "Sales Invoice"
                custom_field.update(field)
                custom_field.insert()

        frappe.db.commit()
        frappe.logger().info("Communication custom fields created successfully")

    except Exception as e:
        frappe.logger().error(f"Error setting up communication custom fields: {str(e)}")
        raise
