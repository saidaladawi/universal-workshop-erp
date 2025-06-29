"""
Custom fields for Receivables Management and Financial Reporting
Universal Workshop ERP - Billing Management Module
"""

import frappe


def create_receivables_custom_fields():
    """Create custom fields for receivables management"""

    # Customer fields for dunning and communication
    customer_fields = [
        {
            "fieldname": "custom_communication_section",
            "fieldtype": "Section Break",
            "label": "Communication Preferences / تفضيلات التواصل",
            "insert_after": "website",
        },
        {
            "fieldname": "custom_whatsapp_number",
            "fieldtype": "Data",
            "label": "WhatsApp Number / رقم الواتساب",
            "options": "Phone",
            "insert_after": "custom_communication_section",
        },
        {
            "fieldname": "custom_preferred_communication_language",
            "fieldtype": "Select",
            "label": "Preferred Language / اللغة المفضلة",
            "options": "English\nArabic\nعربي",
            "default": "English",
            "insert_after": "custom_whatsapp_number",
        },
        {
            "fieldname": "custom_communication_opt_in",
            "fieldtype": "Check",
            "label": "Consent for Payment Reminders / موافقة على تذكير الدفع",
            "default": 1,
            "insert_after": "custom_preferred_communication_language",
        },
        {
            "fieldname": "custom_payment_terms_agreed",
            "fieldtype": "Check",
            "label": "Payment Terms Agreed / شروط الدفع متفق عليها",
            "insert_after": "custom_communication_opt_in",
        },
        {
            "fieldname": "custom_credit_limit_omr",
            "fieldtype": "Currency",
            "label": "Credit Limit (OMR) / حد الائتمان",
            "options": "OMR",
            "precision": 3,
            "insert_after": "custom_payment_terms_agreed",
        },
    ]

    # Company fields for VAT reporting
    company_fields = [
        {
            "fieldname": "custom_vat_reporting_section",
            "fieldtype": "Section Break",
            "label": "VAT Reporting Configuration / إعدادات تقارير ضريبة القيمة المضافة",
            "insert_after": "default_currency",
        },
        {
            "fieldname": "custom_vat_registered",
            "fieldtype": "Check",
            "label": "VAT Registered / مسجل في ضريبة القيمة المضافة",
            "insert_after": "custom_vat_reporting_section",
        },
        {
            "fieldname": "custom_vat_registration_date",
            "fieldtype": "Date",
            "label": "VAT Registration Date / تاريخ التسجيل في الضريبة",
            "insert_after": "custom_vat_registered",
        },
        {
            "fieldname": "custom_business_activity",
            "fieldtype": "Data",
            "label": "Business Activity / النشاط التجاري",
            "default": "Automotive Workshop Services",
            "insert_after": "custom_vat_registration_date",
        },
        {
            "fieldname": "custom_ota_portal_username",
            "fieldtype": "Data",
            "label": "OTA Portal Username / اسم المستخدم في بوابة هيئة الضرائب",
            "insert_after": "custom_business_activity",
        },
        {
            "fieldname": "custom_quarterly_filing_day",
            "fieldtype": "Select",
            "label": "Quarterly Filing Day / يوم التقديم الفصلي",
            "options": "15\n28\n30",
            "default": "28",
            "description": "Day of month for quarterly VAT filing",
            "insert_after": "custom_ota_portal_username",
        },
    ]

    # Sales Invoice fields for payment tracking
    sales_invoice_fields = [
        {
            "fieldname": "custom_payment_tracking_section",
            "fieldtype": "Section Break",
            "label": "Payment Tracking / تتبع الدفع",
            "insert_after": "terms",
        },
        {
            "fieldname": "custom_payment_reminder_count",
            "fieldtype": "Int",
            "label": "Payment Reminders Sent / عدد التذكيرات المرسلة",
            "default": 0,
            "read_only": 1,
            "insert_after": "custom_payment_tracking_section",
        },
        {
            "fieldname": "custom_last_reminder_date",
            "fieldtype": "Date",
            "label": "Last Reminder Date / تاريخ آخر تذكير",
            "read_only": 1,
            "insert_after": "custom_payment_reminder_count",
        },
        {
            "fieldname": "custom_payment_follow_up_status",
            "fieldtype": "Select",
            "label": "Follow-up Status / حالة المتابعة",
            "options": "No Action Required\nReminder Sent\nPhone Call Required\nLegal Notice Sent\nDebt Collection",
            "default": "No Action Required",
            "insert_after": "custom_last_reminder_date",
        },
        {
            "fieldname": "custom_expected_payment_date",
            "fieldtype": "Date",
            "label": "Expected Payment Date / تاريخ الدفع المتوقع",
            "insert_after": "custom_payment_follow_up_status",
        },
    ]

    # Apply custom fields
    field_groups = [
        ("Customer", customer_fields),
        ("Company", company_fields),
        ("Sales Invoice", sales_invoice_fields),
    ]

    for doctype, fields in field_groups:
        for field in fields:
            custom_field_name = f'{doctype}-{field["fieldname"]}'
            if not frappe.db.exists("Custom Field", custom_field_name):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = doctype
                custom_field.update(field)
                custom_field.insert()
                print(f"✅ Created custom field: {custom_field_name}")


if __name__ == "__main__":
    create_receivables_custom_fields()
