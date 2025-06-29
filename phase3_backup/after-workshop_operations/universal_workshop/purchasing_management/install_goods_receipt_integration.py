"""
Installation Script for Purchase Receipt Quality Inspection Integration
Universal Workshop ERP - Purchasing Management
"""

import frappe
from frappe import _
from universal_workshop.purchasing_management.purchase_receipt_extensions import (
    setup_purchase_receipt_custom_fields,
)


def install_goods_receipt_quality_inspection_integration():
    """Install Purchase Receipt Quality Inspection integration"""

    try:
        frappe.msgprint(_("Installing Purchase Receipt Quality Inspection integration..."))

        # Step 1: Create custom fields
        create_purchase_receipt_custom_fields()

        # Step 2: Setup client scripts
        setup_purchase_receipt_client_scripts()

        # Step 3: Create web forms for mobile interface
        create_mobile_inspection_web_form()

        # Step 4: Setup custom print formats
        setup_custom_print_formats()

        # Step 5: Create dashboard cards
        create_quality_inspection_dashboard()

        # Step 6: Setup notifications
        setup_quality_inspection_notifications()

        frappe.db.commit()

        frappe.msgprint(
            _("Purchase Receipt Quality Inspection integration installed successfully!"),
            title=_("Installation Complete"),
            indicator="green",
        )

    except Exception as e:
        frappe.log_error(f"Error installing Purchase Receipt QI integration: {str(e)}")
        frappe.throw(_("Installation failed: {0}").format(str(e)))


def create_purchase_receipt_custom_fields():
    """Create custom fields for Purchase Receipt and Purchase Receipt Item"""

    frappe.msgprint(_("Creating custom fields..."))

    # Custom fields for Purchase Receipt DocType
    purchase_receipt_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_section",
            "fieldtype": "Section Break",
            "label": "Quality Inspection",
            "insert_after": "status",
            "collapsible": 1,
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_required",
            "fieldtype": "Check",
            "label": "Quality Inspection Required",
            "insert_after": "quality_inspection_section",
            "default": 0,
            "read_only": 1,
            "description": "Automatically set if any items require quality inspection",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_status",
            "fieldtype": "Select",
            "label": "Quality Inspection Status",
            "options": "\nPending\nIn Progress\nCompleted\nFailed\nNot Required",
            "insert_after": "quality_inspection_required",
            "default": "Not Required",
            "read_only": 1,
            "in_list_view": 1,
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_status_ar",
            "fieldtype": "Data",
            "label": "حالة فحص الجودة",
            "insert_after": "quality_inspection_status",
            "read_only": 1,
            "translatable": 1,
            "depends_on": "eval:frappe.boot.lang === 'ar'",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "column_break_qi_1",
            "fieldtype": "Column Break",
            "insert_after": "quality_inspection_status_ar",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "total_inspections_pending",
            "fieldtype": "Int",
            "label": "Total Inspections Pending",
            "insert_after": "column_break_qi_1",
            "default": 0,
            "read_only": 1,
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_summary",
            "fieldtype": "Text Editor",
            "label": "Quality Inspection Summary",
            "insert_after": "total_inspections_pending",
            "read_only": 1,
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_notes",
            "fieldtype": "Text Editor",
            "label": "Quality Inspection Notes",
            "insert_after": "quality_inspection_summary",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt",
            "fieldname": "quality_inspection_notes_ar",
            "fieldtype": "Text Editor",
            "label": "ملاحظات فحص الجودة",
            "insert_after": "quality_inspection_notes",
            "translatable": 1,
            "depends_on": "eval:frappe.boot.lang === 'ar'",
        },
    ]

    # Custom fields for Purchase Receipt Item child table
    purchase_receipt_item_fields = [
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt Item",
            "fieldname": "quality_inspection_required",
            "fieldtype": "Check",
            "label": "QI Required",
            "insert_after": "quality_inspection",
            "default": 0,
            "in_list_view": 1,
            "read_only": 1,
            "width": "80px",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt Item",
            "fieldname": "inspection_status",
            "fieldtype": "Select",
            "label": "Inspection Status",
            "options": "\nNot Required\nPending\nIn Progress\nPassed\nFailed",
            "insert_after": "quality_inspection_required",
            "default": "Not Required",
            "in_list_view": 1,
            "read_only": 1,
            "width": "120px",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt Item",
            "fieldname": "inspections_completed",
            "fieldtype": "Int",
            "label": "Inspections Completed",
            "insert_after": "inspection_status",
            "default": 0,
            "read_only": 1,
            "width": "100px",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt Item",
            "fieldname": "quality_score",
            "fieldtype": "Float",
            "label": "Quality Score (%)",
            "insert_after": "inspections_completed",
            "precision": 2,
            "read_only": 1,
            "width": "100px",
        },
        {
            "doctype": "Custom Field",
            "dt": "Purchase Receipt Item",
            "fieldname": "batch_inspections_required",
            "fieldtype": "Int",
            "label": "Batch Inspections Required",
            "insert_after": "quality_score",
            "default": 1,
            "description": "Number of batch/serial inspections required for this item",
            "width": "120px",
        },
    ]

    # Create all custom fields
    all_fields = purchase_receipt_fields + purchase_receipt_item_fields

    for field_config in all_fields:
        # Check if field already exists
        existing_field = frappe.db.get_value(
            "Custom Field",
            {"dt": field_config["dt"], "fieldname": field_config["fieldname"]},
            "name",
        )

        if not existing_field:
            # Create custom field
            try:
                custom_field = frappe.new_doc("Custom Field")
                custom_field.update(field_config)
                custom_field.insert()
                frappe.msgprint(_("Created custom field: {0}").format(field_config["fieldname"]))
            except Exception as e:
                frappe.log_error(f"Error creating field {field_config['fieldname']}: {str(e)}")


def setup_purchase_receipt_client_scripts():
    """Setup client scripts for Purchase Receipt"""

    frappe.msgprint(_("Setting up client scripts..."))

    # Check if client script already exists
    existing_script = frappe.db.get_value(
        "Client Script",
        {"dt": "Purchase Receipt", "name": "Purchase Receipt Quality Inspection"},
        "name",
    )

    if not existing_script:
        client_script = frappe.new_doc("Client Script")
        client_script.dt = "Purchase Receipt"
        client_script.name = "Purchase Receipt Quality Inspection"
        client_script.enabled = 1
        client_script.script = """
        frappe.require([
            "/assets/universal_workshop/js/purchase_receipt_qi.js"
        ]);
        """
        client_script.insert()


def create_mobile_inspection_web_form():
    """Create mobile-friendly web form for quality inspection"""

    frappe.msgprint(_("Creating mobile inspection web form..."))

    # Check if web form already exists
    existing_form = frappe.db.get_value("Web Form", "mobile-quality-inspection")

    if not existing_form:
        web_form = frappe.new_doc("Web Form")
        web_form.title = "Mobile Quality Inspection"
        web_form.route = "mobile-quality-inspection"
        web_form.doc_type = "Quality Inspection"
        web_form.is_standard = 1
        web_form.published = 1
        web_form.allow_edit = 1
        web_form.allow_multiple = 1
        web_form.show_sidebar = 0
        web_form.allow_print = 1
        web_form.allow_delete = 0
        web_form.login_required = 1

        # Add web form fields
        web_form_fields = [
            {
                "fieldname": "purchase_receipt",
                "fieldtype": "Link",
                "label": "Purchase Receipt",
                "reqd": 1,
                "read_only": 1,
            },
            {
                "fieldname": "item_code",
                "fieldtype": "Link",
                "label": "Item Code",
                "reqd": 1,
                "read_only": 1,
            },
            {"fieldname": "item_name", "fieldtype": "Data", "label": "Item Name", "read_only": 1},
            {
                "fieldname": "supplier",
                "fieldtype": "Link",
                "label": "Supplier",
                "reqd": 1,
                "read_only": 1,
            },
            {"fieldname": "batch_no", "fieldtype": "Link", "label": "Batch No"},
            {"fieldname": "serial_no", "fieldtype": "Small Text", "label": "Serial Numbers"},
            {
                "fieldname": "inspection_date",
                "fieldtype": "Date",
                "label": "Inspection Date",
                "reqd": 1,
                "default": "Today",
            },
            {"fieldname": "inspected_by", "fieldtype": "Link", "label": "Inspected By", "reqd": 1},
            {
                "fieldname": "overall_result",
                "fieldtype": "Select",
                "label": "Overall Result",
                "options": "Pass\nFail\nPartial Pass",
                "reqd": 1,
            },
            {
                "fieldname": "quality_score",
                "fieldtype": "Float",
                "label": "Quality Score (%)",
                "precision": 2,
            },
            {
                "fieldname": "inspection_remarks",
                "fieldtype": "Text Editor",
                "label": "Inspection Remarks",
            },
            {
                "fieldname": "inspection_remarks_ar",
                "fieldtype": "Text Editor",
                "label": "ملاحظات الفحص",
            },
        ]

        for field in web_form_fields:
            web_form.append("web_form_fields", field)

        web_form.insert()


def setup_custom_print_formats():
    """Setup custom print formats for Purchase Receipt with QI info"""

    frappe.msgprint(_("Setting up custom print formats..."))

    # Check if print format already exists
    existing_format = frappe.db.get_value("Print Format", "Purchase Receipt with QI")

    if not existing_format:
        print_format = frappe.new_doc("Print Format")
        print_format.name = "Purchase Receipt with QI"
        print_format.doc_type = "Purchase Receipt"
        print_format.print_format_type = "Jinja"
        print_format.disabled = 0
        print_format.standard = "Yes"

        # Simple HTML template with QI information
        print_format.html = """
        <div class="print-format">
            <h3>Purchase Receipt - {{ doc.name }}</h3>
            
            <div class="row">
                <div class="col-xs-6">
                    <p><strong>Supplier:</strong> {{ doc.supplier_name }}</p>
                    <p><strong>Date:</strong> {{ doc.posting_date }}</p>
                </div>
                <div class="col-xs-6">
                    <p><strong>Quality Inspection Status:</strong> {{ doc.quality_inspection_status }}</p>
                    <p><strong>Pending Inspections:</strong> {{ doc.total_inspections_pending }}</p>
                </div>
            </div>
            
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>Item Code</th>
                        <th>Item Name</th>
                        <th>Qty</th>
                        <th>QI Required</th>
                        <th>Inspection Status</th>
                        <th>Quality Score</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in doc.items %}
                    <tr>
                        <td>{{ item.item_code }}</td>
                        <td>{{ item.item_name }}</td>
                        <td>{{ item.qty }}</td>
                        <td>{{ "Yes" if item.quality_inspection_required else "No" }}</td>
                        <td>{{ item.inspection_status or "Not Required" }}</td>
                        <td>{{ item.quality_score or "-" }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            {% if doc.quality_inspection_notes %}
            <div class="section">
                <h4>Quality Inspection Notes</h4>
                <p>{{ doc.quality_inspection_notes }}</p>
            </div>
            {% endif %}
        </div>
        """

        print_format.insert()


def create_quality_inspection_dashboard():
    """Create dashboard cards for quality inspection tracking"""

    frappe.msgprint(_("Creating quality inspection dashboard..."))

    # Dashboard for Purchase Receipt QI status
    dashboard_config = {
        "module_name": "Purchasing Management",
        "is_standard": 1,
        "charts": [
            {
                "chart_name": "Purchase Receipt QI Status",
                "chart_type": "Donut",
                "document_type": "Purchase Receipt",
                "filters_json": '{"quality_inspection_required": 1}',
                "based_on": "quality_inspection_status",
                "timeseries": 0,
            },
            {
                "chart_name": "Monthly QI Inspections",
                "chart_type": "Line",
                "document_type": "Quality Inspection",
                "filters_json": '{"purchase_receipt": ["!=", ""]}',
                "based_on": "creation",
                "timeseries": 1,
                "timespan": "Last Year",
                "time_interval": "Monthly",
            },
        ],
        "cards": [
            {
                "card_name": "Pending Quality Inspections",
                "document_type": "Purchase Receipt",
                "filters_json": '{"quality_inspection_status": "Pending", "docstatus": 1}',
                "function": "Count",
            },
            {
                "card_name": "Failed Quality Inspections",
                "document_type": "Purchase Receipt",
                "filters_json": '{"quality_inspection_status": "Failed", "docstatus": 1}',
                "function": "Count",
            },
        ],
    }

    # Create dashboard if it doesn't exist
    existing_dashboard = frappe.db.get_value("Dashboard", "Purchase Receipt Quality Inspection")

    if not existing_dashboard:
        dashboard = frappe.new_doc("Dashboard")
        dashboard.dashboard_name = "Purchase Receipt Quality Inspection"
        dashboard.module = "Purchasing Management"
        dashboard.is_standard = 1

        # Add charts
        for chart_config in dashboard_config["charts"]:
            dashboard.append("charts", chart_config)

        # Add cards
        for card_config in dashboard_config["cards"]:
            dashboard.append("cards", card_config)

        dashboard.insert()


def setup_quality_inspection_notifications():
    """Setup notifications for quality inspection events"""

    frappe.msgprint(_("Setting up quality inspection notifications..."))

    notifications = [
        {
            "name": "Purchase Receipt QI Required",
            "document_type": "Purchase Receipt",
            "event": "Submit",
            "send_alert_on": "Submit",
            "condition": "doc.quality_inspection_required and doc.total_inspections_pending > 0",
            "message": "Quality inspection required for Purchase Receipt {{ doc.name }}. {{ doc.total_inspections_pending }} inspections pending.",
            "subject": "Quality Inspection Required - {{ doc.name }}",
            "recipients": [{"receiver_by": "Role", "receiver": "Quality Inspector"}],
        },
        {
            "name": "Quality Inspection Failed",
            "document_type": "Purchase Receipt",
            "event": "Change",
            "send_alert_on": "Value Change",
            "value_changed": "quality_inspection_status",
            "condition": "doc.quality_inspection_status == 'Failed'",
            "message": "Quality inspection failed for Purchase Receipt {{ doc.name }}. Please review and take corrective action.",
            "subject": "Quality Inspection Failed - {{ doc.name }}",
            "recipients": [
                {"receiver_by": "Role", "receiver": "Purchase Manager"},
                {"receiver_by": "Role", "receiver": "Quality Inspector"},
            ],
        },
    ]

    for notif_config in notifications:
        existing_notif = frappe.db.get_value("Notification", notif_config["name"])

        if not existing_notif:
            notification = frappe.new_doc("Notification")
            notification.update(notif_config)
            notification.insert()


# API Functions for Mobile Interface
@frappe.whitelist()
def get_purchase_receipt_items_for_inspection(purchase_receipt):
    """Get items requiring inspection for mobile interface"""

    pr_doc = frappe.get_doc("Purchase Receipt", purchase_receipt)
    items_for_inspection = []

    for item in pr_doc.items:
        if (
            getattr(item, "quality_inspection_required", 0)
            and getattr(item, "inspection_status", "") == "Pending"
        ):
            items_for_inspection.append(
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "item_name_ar": getattr(item, "item_name_ar", ""),
                    "qty": item.qty,
                    "batch_no": getattr(item, "batch_no", ""),
                    "purchase_receipt_item": item.name,
                    "batch_inspections_required": getattr(item, "batch_inspections_required", 1),
                }
            )

    return {
        "purchase_receipt": {
            "name": pr_doc.name,
            "supplier": pr_doc.supplier,
            "supplier_name": pr_doc.supplier_name,
            "posting_date": pr_doc.posting_date,
        },
        "items": items_for_inspection,
    }


@frappe.whitelist()
def submit_mobile_quality_inspection(data):
    """Submit quality inspection from mobile interface"""

    import json

    if isinstance(data, str):
        data = json.loads(data)

    try:
        # Create Quality Inspection record
        qi_doc = frappe.new_doc("Quality Inspection")
        qi_doc.update(data)
        qi_doc.insert()
        qi_doc.submit()

        # Update Purchase Receipt status
        frappe.call(
            "universal_workshop.purchasing_management.purchase_receipt_extensions.update_purchase_receipt_inspection_status",
            purchase_receipt=data.get("purchase_receipt"),
        )

        return {
            "status": "success",
            "quality_inspection": qi_doc.name,
            "message": _("Quality inspection submitted successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error submitting mobile QI: {str(e)}")
        return {"status": "error", "message": str(e)}


def update_purchase_receipt_integration():
    """Update Purchase Receipt integration after installation"""

    try:
        # Update Purchase Receipt controller integration
        update_purchase_receipt_hooks()

        # Clear cache to ensure new fields are recognized
        frappe.clear_cache()

        frappe.msgprint(_("Purchase Receipt integration updated successfully"))

    except Exception as e:
        frappe.log_error(f"Error updating Purchase Receipt integration: {str(e)}")


def update_purchase_receipt_hooks():
    """Update hooks.py to include Purchase Receipt integration"""

    # This would typically be done manually or through installation patches
    # For now, we'll just log that this step needs to be completed
    frappe.msgprint(
        _(
            "Please add the following to your hooks.py file:\n\n"
            "doc_events = {\n"
            "    'Purchase Receipt': {\n"
            "        'validate': 'universal_workshop.purchasing_management.purchase_receipt_extensions.PurchaseReceiptQualityInspectionController.validate',\n"
            "        'on_submit': 'universal_workshop.purchasing_management.purchase_receipt_extensions.PurchaseReceiptQualityInspectionController.on_submit'\n"
            "    }\n"
            "}"
        ),
        title=_("Manual Configuration Required"),
        indicator="orange",
    )
