import frappe
from frappe import _

def get_data():
    """Dashboard للورشة الشاملة مع تصميم احترافي"""

    return {
        "heatmap": True,
        "heatmap_message": _("This is based on the Service Orders created for the Workshop in the past year"),
        "fieldname": "creation",
        "transactions": [
            {
                "label": _("Vehicle Management"),
                "icon": "fa fa-car",
                "color": "#1976d2",
                "items": ["Vehicle", "Vehicle Make", "Vehicle Model", "Vehicle Inspection"]
            },
            {
                "label": _("Service Operations"),
                "icon": "fa fa-wrench",
                "color": "#f44336",
                "items": ["Service Order", "Service Bay", "Technician", "Quality Control Checkpoint"]
            },
            {
                "label": _("Customer Management"),
                "icon": "fa fa-users",
                "color": "#4caf50",
                "items": ["Customer Analytics", "Customer Loyalty Points"]
            },
            {
                "label": _("Reports & Analytics"),
                "icon": "fa fa-chart-bar",
                "color": "#ff9800",
                "items": ["Service Order Report", "Vehicle Performance Report", "Technician Performance"]
            }
        ],

        "charts": [
            {
                "chart_name": _("Service Orders This Month"),
                "chart_type": "line",
                "custom_options": {
                    "type": "line",
                    "colors": ["#1976d2"],
                    "axisOptions": {
                        "xIsSeries": 1
                    }
                },
                "source": "Service Order"
            },
            {
                "chart_name": _("Vehicle Status Distribution"),
                "chart_type": "donut",
                "custom_options": {
                    "type": "donut",
                    "colors": ["#4caf50", "#ff9800", "#f44336"],
                    "height": 300
                },
                "source": "Vehicle"
            }
        ],

        "cards": [
            {
                "card_name": _("Total Vehicles"),
                "function": "get_vehicle_count",
                "color": "#1976d2",
                "icon": "fa fa-car"
            },
            {
                "card_name": _("Active Service Orders"),
                "function": "get_active_service_orders",
                "color": "#f44336",
                "icon": "fa fa-wrench"
            },
            {
                "card_name": _("Available Technicians"),
                "function": "get_available_technicians",
                "color": "#4caf50",
                "icon": "fa fa-user-cog"
            },
            {
                "card_name": _("This Month Revenue"),
                "function": "get_month_revenue",
                "color": "#ff9800",
                "icon": "fa fa-money-bill-wave"
            }
        ]
    }

@frappe.whitelist()
def get_vehicle_count():
    """عدد المركبات الإجمالي"""
    count = frappe.db.count("Vehicle")
    return {
        "value": count,
        "indicator": "Green" if count > 0 else "Red"
    }

@frappe.whitelist()
def get_active_service_orders():
    """أوامر الخدمة النشطة"""
    count = frappe.db.count("Service Order", {"status": ["in", ["Open", "In Progress"]]})
    return {
        "value": count,
        "indicator": "Orange" if count > 0 else "Green"
    }

@frappe.whitelist()
def get_available_technicians():
    """الفنيين المتاحين"""
    count = frappe.db.count("Technician", {"status": "Active"})
    return {
        "value": count,
        "indicator": "Green" if count > 0 else "Red"
    }

@frappe.whitelist()
def get_month_revenue():
    """إيرادات الشهر الحالي"""
    from frappe.utils import getdate, get_first_day, get_last_day

    first_day = get_first_day(getdate())
    last_day = get_last_day(getdate())

    revenue = frappe.db.sql("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue
        FROM `tabService Order`
        WHERE creation BETWEEN %s AND %s
        AND status = 'Completed'
    """, (first_day, last_day))[0][0]

    return {
        "value": f"{revenue:,.2f}",
        "indicator": "Green" if revenue > 0 else "Red"
    }
