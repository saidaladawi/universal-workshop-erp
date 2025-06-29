"""
Universal Workshop ERP - Dashboard Workspace Configuration
ERPNext v15 Desk API integration with Arabic localization
"""

import frappe
from frappe import _


def get_workspace_data():
    """Get workspace configuration for Universal Workshop Dashboard"""

    return {
        "name": "Universal Workshop Dashboard",
        "title": _("Workshop Dashboard") if frappe.local.lang == "en" else "لوحة تحكم الورشة",
        "icon": "fa fa-tachometer-alt",
        "category": "Places",
        "public": 1,
        "is_hidden": 0,
        "is_default": 1,
        "parent_page": "",
        "restrict_to_domain": "Manufacturing",
        "sequence_id": 1,
        "shortcuts": get_dashboard_shortcuts(),
        "charts": get_dashboard_charts(),
        "number_cards": get_dashboard_cards(),
        "quick_lists": get_quick_lists(),
        "links": get_dashboard_links(),
    }


def get_dashboard_shortcuts():
    """Get dashboard shortcuts for quick actions"""
    return [
        {
            "type": "DocType",
            "label": _("Service Order") if frappe.local.lang == "en" else "أمر خدمة",
            "doc_type": "Service Order",
            "icon": "fa fa-wrench",
            "color": "#1976d2",
            "stats_filter": {"status": "Open"},
            "description": (
                _("Create new service order")
                if frappe.local.lang == "en"
                else "إنشاء أمر خدمة جديد"
            ),
        },
        {
            "type": "DocType",
            "label": _("Customer") if frappe.local.lang == "en" else "عميل",
            "doc_type": "Customer",
            "icon": "fa fa-user",
            "color": "#4caf50",
            "stats_filter": {"disabled": 0},
            "description": (
                _("Register new customer") if frappe.local.lang == "en" else "تسجيل عميل جديد"
            ),
        },
        {
            "type": "DocType",
            "label": _("Vehicle") if frappe.local.lang == "en" else "مركبة",
            "doc_type": "Vehicle",
            "icon": "fa fa-car",
            "color": "#ff9800",
            "stats_filter": {"status": "Active"},
            "description": (
                _("Register new vehicle") if frappe.local.lang == "en" else "تسجيل مركبة جديدة"
            ),
        },
        {
            "type": "DocType",
            "label": _("Item") if frappe.local.lang == "en" else "صنف",
            "doc_type": "Item",
            "icon": "fa fa-cog",
            "color": "#9c27b0",
            "stats_filter": {"disabled": 0, "is_stock_item": 1},
            "description": (
                _("Add inventory item") if frappe.local.lang == "en" else "إضافة صنف للمخزون"
            ),
        },
        {
            "type": "DocType",
            "label": _("Sales Invoice") if frappe.local.lang == "en" else "فاتورة مبيعات",
            "doc_type": "Sales Invoice",
            "icon": "fa fa-file-invoice",
            "color": "#f44336",
            "stats_filter": {"status": "Draft"},
            "description": (
                _("Create sales invoice") if frappe.local.lang == "en" else "إنشاء فاتورة مبيعات"
            ),
        },
        {
            "type": "Page",
            "label": _("Workshop Reports") if frappe.local.lang == "en" else "تقارير الورشة",
            "url": "/app/query-report",
            "icon": "fa fa-chart-bar",
            "color": "#607d8b",
            "description": (
                _("View workshop analytics") if frappe.local.lang == "en" else "عرض تحليلات الورشة"
            ),
        },
    ]


def get_dashboard_charts():
    """Get dashboard charts configuration"""
    return [
        {
            "chart_name": (
                _("Monthly Revenue Trend")
                if frappe.local.lang == "en"
                else "اتجاه الإيرادات الشهرية"
            ),
            "chart_type": "Line",
            "document_type": "Sales Invoice",
            "based_on": "posting_date",
            "time_interval": "Monthly",
            "timespan": "Last Year",
            "value_based_on": "base_grand_total",
            "filters_json": '{"status": "Paid", "is_return": 0}',
            "timeseries": 1,
            "color": "#1976d2",
            "width": "Half",
        },
        {
            "chart_name": (
                _("Service Status Distribution")
                if frappe.local.lang == "en"
                else "توزيع حالة الخدمات"
            ),
            "chart_type": "Donut",
            "document_type": "Service Order",
            "group_by_type": "Select",
            "group_by_based_on": "status",
            "aggregate_function_based_on": "Count",
            "filters_json": "{}",
            "color": "#4caf50",
            "width": "Half",
        },
        {
            "chart_name": (
                _("Daily Service Orders") if frappe.local.lang == "en" else "أوامر الخدمة اليومية"
            ),
            "chart_type": "Bar",
            "document_type": "Service Order",
            "based_on": "creation",
            "time_interval": "Daily",
            "timespan": "Last Month",
            "aggregate_function_based_on": "Count",
            "filters_json": "{}",
            "color": "#ff9800",
            "width": "Full",
        },
    ]


def get_dashboard_cards():
    """Get dashboard number cards configuration"""
    return [
        {
            "label": _("Today's Revenue") if frappe.local.lang == "en" else "إيرادات اليوم",
            "function": "universal_workshop.dashboard.workshop_dashboard.get_today_revenue_card",
            "document_type": "Sales Invoice",
            "color": "#1976d2",
            "width": "Third",
        },
        {
            "label": (
                _("Active Service Orders") if frappe.local.lang == "en" else "أوامر الخدمة النشطة"
            ),
            "function": "universal_workshop.dashboard.workshop_dashboard.get_active_orders_card",
            "document_type": "Service Order",
            "color": "#4caf50",
            "width": "Third",
        },
        {
            "label": (
                _("Available Technicians") if frappe.local.lang == "en" else "الفنيين المتاحين"
            ),
            "function": "universal_workshop.dashboard.workshop_dashboard.get_technicians_card",
            "document_type": "Technician",
            "color": "#ff9800",
            "width": "Third",
        },
        {
            "label": _("Low Stock Items") if frappe.local.lang == "en" else "أصناف منخفضة المخزون",
            "function": "universal_workshop.dashboard.workshop_dashboard.get_low_stock_card",
            "document_type": "Item",
            "color": "#f44336",
            "width": "Third",
        },
        {
            "label": _("Customer Satisfaction") if frappe.local.lang == "en" else "رضا العملاء",
            "function": "universal_workshop.dashboard.workshop_dashboard.get_satisfaction_card",
            "document_type": "Customer Feedback",
            "color": "#9c27b0",
            "width": "Third",
        },
        {
            "label": _("Monthly Target") if frappe.local.lang == "en" else "الهدف الشهري",
            "function": "universal_workshop.dashboard.workshop_dashboard.get_monthly_target_card",
            "document_type": "Budget",
            "color": "#607d8b",
            "width": "Third",
        },
    ]


def get_quick_lists():
    """Get quick lists for dashboard"""
    return [
        {
            "label": (
                _("Recent Service Orders") if frappe.local.lang == "en" else "أوامر الخدمة الحديثة"
            ),
            "document_type": "Service Order",
            "view": "List",
            "filters": [["creation", ">=", "Today"]],
            "fields": ["name", "customer", "status", "creation"],
            "limit": 10,
        },
        {
            "label": _("Pending Invoices") if frappe.local.lang == "en" else "الفواتير المعلقة",
            "document_type": "Sales Invoice",
            "view": "List",
            "filters": [["status", "=", "Draft"]],
            "fields": ["name", "customer", "grand_total", "posting_date"],
            "limit": 5,
        },
        {
            "label": _("Overdue Tasks") if frappe.local.lang == "en" else "المهام المتأخرة",
            "document_type": "Task",
            "view": "List",
            "filters": [["status", "=", "Open"], ["exp_end_date", "<", "Today"]],
            "fields": ["name", "subject", "status", "exp_end_date"],
            "limit": 8,
        },
    ]


def get_dashboard_links():
    """Get dashboard navigation links organized by modules"""
    return [
        {
            "label": _("Service Management") if frappe.local.lang == "en" else "إدارة الخدمات",
            "icon": "fa fa-wrench",
            "color": "#1976d2",
            "type": "Card Break",
        },
        {
            "label": _("Service Order") if frappe.local.lang == "en" else "أمر خدمة",
            "type": "DocType",
            "name": "Service Order",
            "description": (
                _("Manage workshop service orders")
                if frappe.local.lang == "en"
                else "إدارة أوامر خدمة الورشة"
            ),
        },
        {
            "label": _("Service Bay") if frappe.local.lang == "en" else "خليج الخدمة",
            "type": "DocType",
            "name": "Service Bay",
            "description": (
                _("Manage service bays and assignments")
                if frappe.local.lang == "en"
                else "إدارة أخلجة الخدمة والمهام"
            ),
        },
        {
            "label": _("Technician") if frappe.local.lang == "en" else "فني",
            "type": "DocType",
            "name": "Technician",
            "description": (
                _("Manage workshop technicians")
                if frappe.local.lang == "en"
                else "إدارة فنيي الورشة"
            ),
        },
        {
            "label": (
                _("Customer & Vehicle Management")
                if frappe.local.lang == "en"
                else "إدارة العملاء والمركبات"
            ),
            "icon": "fa fa-users",
            "color": "#4caf50",
            "type": "Card Break",
        },
        {
            "label": _("Customer") if frappe.local.lang == "en" else "عميل",
            "type": "DocType",
            "name": "Customer",
            "description": (
                _("Manage customer database")
                if frappe.local.lang == "en"
                else "إدارة قاعدة بيانات العملاء"
            ),
        },
        {
            "label": _("Vehicle") if frappe.local.lang == "en" else "مركبة",
            "type": "DocType",
            "name": "Vehicle",
            "description": (
                _("Vehicle registration and history")
                if frappe.local.lang == "en"
                else "تسجيل المركبات وتاريخها"
            ),
        },
        {
            "label": _("Vehicle Inspection") if frappe.local.lang == "en" else "فحص المركبة",
            "type": "DocType",
            "name": "Vehicle Inspection",
            "description": (
                _("Vehicle inspection records")
                if frappe.local.lang == "en"
                else "سجلات فحص المركبات"
            ),
        },
        {
            "label": _("Inventory & Parts") if frappe.local.lang == "en" else "المخزون والقطع",
            "icon": "fa fa-boxes",
            "color": "#ff9800",
            "type": "Card Break",
        },
        {
            "label": _("Item") if frappe.local.lang == "en" else "صنف",
            "type": "DocType",
            "name": "Item",
            "description": (
                _("Manage inventory items") if frappe.local.lang == "en" else "إدارة أصناف المخزون"
            ),
        },
        {
            "label": _("Stock Entry") if frappe.local.lang == "en" else "قيد مخزون",
            "type": "DocType",
            "name": "Stock Entry",
            "description": (
                _("Stock movements and adjustments")
                if frappe.local.lang == "en"
                else "حركات وتعديلات المخزون"
            ),
        },
        {
            "label": _("Purchase Order") if frappe.local.lang == "en" else "أمر شراء",
            "type": "DocType",
            "name": "Purchase Order",
            "description": (
                _("Parts procurement orders") if frappe.local.lang == "en" else "أوامر شراء القطع"
            ),
        },
        {
            "label": _("Financial Management") if frappe.local.lang == "en" else "الإدارة المالية",
            "icon": "fa fa-money-bill-wave",
            "color": "#f44336",
            "type": "Card Break",
        },
        {
            "label": _("Sales Invoice") if frappe.local.lang == "en" else "فاتورة مبيعات",
            "type": "DocType",
            "name": "Sales Invoice",
            "description": (
                _("Customer invoicing") if frappe.local.lang == "en" else "فوترة العملاء"
            ),
        },
        {
            "label": _("Payment Entry") if frappe.local.lang == "en" else "قيد دفع",
            "type": "DocType",
            "name": "Payment Entry",
            "description": (
                _("Payment processing") if frappe.local.lang == "en" else "معالجة المدفوعات"
            ),
        },
        {
            "label": _("Quotation") if frappe.local.lang == "en" else "عرض أسعار",
            "type": "DocType",
            "name": "Quotation",
            "description": (
                _("Customer quotations") if frappe.local.lang == "en" else "عروض أسعار العملاء"
            ),
        },
    ]


@frappe.whitelist()
def get_today_revenue_card():
    """Get today's revenue for number card"""
    from frappe.utils import nowdate, flt

    revenue = (
        frappe.db.sql(
            """
        SELECT COALESCE(SUM(base_grand_total), 0)
        FROM `tabSales Invoice`
        WHERE posting_date = %s
        AND docstatus = 1
        AND is_return = 0
    """,
            [nowdate()],
        )[0][0]
        or 0
    )

    return {"value": flt(revenue, 3), "fieldtype": "Currency", "currency": "OMR"}


@frappe.whitelist()
def get_active_orders_card():
    """Get active service orders count"""
    count = frappe.db.count("Service Order", {"status": ["in", ["Open", "In Progress", "On Hold"]]})

    return {"value": count, "fieldtype": "Int"}


@frappe.whitelist()
def get_technicians_card():
    """Get available technicians count"""
    count = frappe.db.count(
        "Technician",
        {"status": "Active", "availability_status": ["in", ["Available", "Partially Available"]]},
    )

    return {"value": count, "fieldtype": "Int"}


@frappe.whitelist()
def get_low_stock_card():
    """Get low stock items count"""
    count = (
        frappe.db.sql(
            """
        SELECT COUNT(*)
        FROM `tabBin` bin
        INNER JOIN `tabItem` item ON bin.item_code = item.name
        WHERE bin.actual_qty <= item.min_order_qty
        AND item.disabled = 0
        AND item.is_stock_item = 1
    """
        )[0][0]
        or 0
    )

    return {"value": count, "fieldtype": "Int"}


@frappe.whitelist()
def get_satisfaction_card():
    """Get customer satisfaction percentage"""
    # Implementation depends on Customer Feedback DocType
    # For now, return a placeholder
    return {"value": 85.5, "fieldtype": "Percent"}


@frappe.whitelist()
def get_monthly_target_card():
    """Get monthly target achievement percentage"""
    from frappe.utils import get_first_day, get_last_day, nowdate, flt

    # Get current month revenue
    first_day = get_first_day(nowdate())
    last_day = get_last_day(nowdate())

    actual_revenue = (
        frappe.db.sql(
            """
        SELECT COALESCE(SUM(base_grand_total), 0)
        FROM `tabSales Invoice`
        WHERE posting_date BETWEEN %s AND %s
        AND docstatus = 1
        AND is_return = 0
    """,
            [first_day, last_day],
        )[0][0]
        or 0
    )

    # Get monthly target (placeholder - would come from Budget or Settings)
    monthly_target = 50000  # OMR 50,000 target

    achievement = (actual_revenue / monthly_target * 100) if monthly_target > 0 else 0

    return {"value": flt(achievement, 1), "fieldtype": "Percent"}
