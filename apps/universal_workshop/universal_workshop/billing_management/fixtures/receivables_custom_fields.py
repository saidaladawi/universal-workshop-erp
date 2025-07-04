"""
Custom fields for receivables management and financial reporting in Universal Workshop ERP
Supports Oman accounting standards and automated dunning processes
"""

import frappe


def create_receivables_custom_fields():
    """Create custom fields for receivables management and financial reporting"""

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
        {
            "fieldname": "custom_payment_history_section",
            "fieldtype": "Section Break",
            "label": "Payment History / تاريخ الدفع",
            "insert_after": "custom_credit_limit_omr",
        },
        {
            "fieldname": "custom_last_payment_date",
            "fieldtype": "Date",
            "label": "Last Payment Date / تاريخ آخر دفعة",
            "read_only": 1,
            "insert_after": "custom_payment_history_section",
        },
        {
            "fieldname": "custom_total_outstanding",
            "fieldtype": "Currency",
            "label": "Total Outstanding / إجمالي المبلغ المستحق",
            "options": "OMR",
            "precision": 3,
            "read_only": 1,
            "insert_after": "custom_last_payment_date",
        },
        {
            "fieldname": "custom_payment_behavior_score",
            "fieldtype": "Int",
            "label": "Payment Behavior Score / نقاط سلوك الدفع",
            "description": "Score from 1-10 based on payment history",
            "read_only": 1,
            "insert_after": "custom_total_outstanding",
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
            "options": "No Action Required\nReminder Sent\nPhone Call Required\nLegal Notice Sent\nDebt Collection\nمطلوب عدم اتخاذ إجراء\nتم إرسال تذكير\nمطلوب اتصال هاتفي\nتم إرسال إشعار قانوني\nتحصيل الديون",
            "default": "No Action Required",
            "insert_after": "custom_last_reminder_date",
        },
        {
            "fieldname": "custom_expected_payment_date",
            "fieldtype": "Date",
            "label": "Expected Payment Date / تاريخ الدفع المتوقع",
            "insert_after": "custom_payment_follow_up_status",
        },
        {
            "fieldname": "custom_aging_category",
            "fieldtype": "Select",
            "label": "Aging Category / فئة التقادم",
            "options": "Current\n1-30 Days\n31-60 Days\n61-90 Days\n90+ Days\nحالي\n١-٣٠ يوم\n٣١-٦٠ يوم\n٦١-٩٠ يوم\n٩٠+ يوم",
            "read_only": 1,
            "insert_after": "custom_expected_payment_date",
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
            if not frappe.db.exists("Custom Field", f'{doctype}-{field["fieldname"]}'):
                custom_field = frappe.new_doc("Custom Field")
                custom_field.dt = doctype
                custom_field.update(field)
                custom_field.insert()
                print(f"✅ Created custom field: {doctype}.{field['fieldname']}")


def create_dunning_communication_doctype():
    """Create DocType for tracking dunning communications"""

    if frappe.db.exists("DocType", "Dunning Communication"):
        return

    doctype_dict = {
        "doctype": "DocType",
        "name": "Dunning Communication",
        "module": "Universal Workshop",
        "custom": 1,
        "is_submittable": 0,
        "track_changes": 1,
        "autoname": "naming_series:",
        "naming_series": "DCOMM-.YYYY.-.#####",
        "fields": [
            {
                "fieldname": "naming_series",
                "fieldtype": "Select",
                "label": "Series",
                "options": "DCOMM-.YYYY.-.#####",
                "reqd": 1,
            },
            {
                "fieldname": "customer",
                "fieldtype": "Link",
                "label": "Customer / العميل",
                "options": "Customer",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "reference_invoice",
                "fieldtype": "Link",
                "label": "Reference Invoice / الفاتورة المرجعية",
                "options": "Sales Invoice",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "communication_method",
                "fieldtype": "Select",
                "label": "Communication Method / طريقة التواصل",
                "options": "SMS\nWhatsApp\nEmail\nPhone\nLegal Notice\nرسالة نصية\nواتساب\nبريد إلكتروني\nهاتف\nإشعار قانوني",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "contact_info",
                "fieldtype": "Data",
                "label": "Contact Information / معلومات الاتصال",
                "reqd": 1,
            },
            {
                "fieldname": "communication_date",
                "fieldtype": "Date",
                "label": "Communication Date / تاريخ التواصل",
                "default": "Today",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "days_overdue",
                "fieldtype": "Int",
                "label": "Days Overdue / الأيام المتأخرة",
                "reqd": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "outstanding_amount",
                "fieldtype": "Currency",
                "label": "Outstanding Amount / المبلغ المستحق",
                "options": "OMR",
                "precision": 3,
                "reqd": 1,
            },
            {
                "fieldname": "currency",
                "fieldtype": "Link",
                "label": "Currency / العملة",
                "options": "Currency",
                "default": "OMR",
            },
            {
                "fieldname": "template_used",
                "fieldtype": "Data",
                "label": "Template Used / القالب المستخدم",
            },
            {
                "fieldname": "language",
                "fieldtype": "Select",
                "label": "Language / اللغة",
                "options": "en\nar\nEnglish\nArabic",
                "default": "en",
            },
            {
                "fieldname": "message_content",
                "fieldtype": "Text Editor",
                "label": "Message Content / محتوى الرسالة",
            },
            {
                "fieldname": "status",
                "fieldtype": "Select",
                "label": "Status / الحالة",
                "options": "Sent\nDelivered\nFailed\nResponse Received\nمرسل\nتم التسليم\nفشل\nتم استلام الرد",
                "default": "Sent",
                "in_list_view": 1,
            },
            {
                "fieldname": "response_received",
                "fieldtype": "Text",
                "label": "Customer Response / رد العميل",
            },
            {
                "fieldname": "follow_up_required",
                "fieldtype": "Check",
                "label": "Follow-up Required / مطلوب متابعة",
            },
            {
                "fieldname": "next_action_date",
                "fieldtype": "Date",
                "label": "Next Action Date / تاريخ الإجراء التالي",
            },
        ],
        "permissions": [
            {"role": "Accounts Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "Accounts User", "read": 1, "write": 1, "create": 1},
            {"role": "Workshop Manager", "read": 1, "write": 1},
        ],
    }

    doc = frappe.get_doc(doctype_dict)
    doc.insert()
    print("✅ Created Dunning Communication DocType")


def setup_receivables_management():
    """Main setup function for receivables management"""
    print("🚀 Setting up receivables management system...")

    try:
        create_receivables_custom_fields()
        create_dunning_communication_doctype()

        print("✅ Receivables management setup completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Receivables management setup failed: {e}")
        frappe.log_error(f"Receivables management setup error: {e}")
        return False


if __name__ == "__main__":
    setup_receivables_management()
