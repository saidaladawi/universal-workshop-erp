"""
Cost Analysis Dashboard Configuration for ERPNext v15 Analytics
Universal Workshop ERP - Procurement Analytics with Arabic Localization
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, today, add_months
import json


@frappe.whitelist()
def get_dashboard_config():
    """Get dashboard configuration for cost analysis"""

    return {
        "name": _("Procurement Cost Analysis"),
        "name_ar": "تحليل تكاليف المشتريات",
        "charts": [
            {
                "name": "supplier_spend_chart",
                "title": _("Supplier Spend Analysis"),
                "title_ar": "تحليل إنفاق الموردين",
                "chart_type": "donut",
                "data_source": "get_supplier_spend_chart_data",
                "height": 300,
                "color_scheme": ["#3498db", "#e74c3c", "#f39c12", "#2ecc71", "#9b59b6"],
            },
            {
                "name": "monthly_spend_trend",
                "title": _("Monthly Spend Trend"),
                "title_ar": "اتجاه الإنفاق الشهري",
                "chart_type": "line",
                "data_source": "get_monthly_spend_trend_data",
                "height": 350,
                "color_scheme": ["#3498db", "#e74c3c"],
            },
            {
                "name": "item_price_trends",
                "title": _("Item Price Trends"),
                "title_ar": "اتجاهات أسعار المواد",
                "chart_type": "line",
                "data_source": "get_item_price_trends_data",
                "height": 350,
                "color_scheme": ["#2ecc71", "#f39c12", "#9b59b6"],
            },
            {
                "name": "supplier_performance",
                "title": _("Supplier Performance"),
                "title_ar": "أداء الموردين",
                "chart_type": "bar",
                "data_source": "get_supplier_performance_data",
                "height": 300,
                "color_scheme": ["#2ecc71", "#e74c3c"],
            },
            {
                "name": "cost_breakdown",
                "title": _("Cost Breakdown by Category"),
                "title_ar": "تصنيف التكاليف حسب الفئة",
                "chart_type": "pie",
                "data_source": "get_cost_breakdown_data",
                "height": 300,
                "color_scheme": ["#3498db", "#e74c3c", "#f39c12", "#2ecc71", "#9b59b6", "#e67e22"],
            },
            {
                "name": "procurement_kpis",
                "title": _("Procurement KPIs"),
                "title_ar": "مؤشرات الأداء الرئيسية للمشتريات",
                "chart_type": "number",
                "data_source": "get_procurement_kpis_data",
                "height": 200,
            },
        ],
        "filters": [
            {
                "fieldname": "from_date",
                "label": _("From Date"),
                "label_ar": "من تاريخ",
                "fieldtype": "Date",
                "default": add_months(today(), -6),
                "reqd": 1,
            },
            {
                "fieldname": "to_date",
                "label": _("To Date"),
                "label_ar": "إلى تاريخ",
                "fieldtype": "Date",
                "default": today(),
                "reqd": 1,
            },
            {
                "fieldname": "supplier",
                "label": _("Supplier"),
                "label_ar": "المورد",
                "fieldtype": "Link",
                "options": "Supplier",
            },
            {
                "fieldname": "item_group",
                "label": _("Item Group"),
                "label_ar": "مجموعة المواد",
                "fieldtype": "Link",
                "options": "Item Group",
            },
            {
                "fieldname": "company",
                "label": _("Company"),
                "label_ar": "الشركة",
                "fieldtype": "Link",
                "options": "Company",
                "default": frappe.defaults.get_global_default("company"),
            },
        ],
        "number_cards": [
            {
                "name": "total_spend",
                "label": _("Total Spend"),
                "label_ar": "إجمالي الإنفاق",
                "data_source": "get_total_spend_card",
                "color": "#3498db",
                "icon": "fa fa-money",
            },
            {
                "name": "active_suppliers",
                "label": _("Active Suppliers"),
                "label_ar": "الموردون النشطون",
                "data_source": "get_active_suppliers_card",
                "color": "#2ecc71",
                "icon": "fa fa-users",
            },
            {
                "name": "avg_order_value",
                "label": _("Avg Order Value"),
                "label_ar": "متوسط قيمة الطلب",
                "data_source": "get_avg_order_value_card",
                "color": "#f39c12",
                "icon": "fa fa-shopping-cart",
            },
            {
                "name": "quality_pass_rate",
                "label": _("Quality Pass Rate"),
                "label_ar": "معدل نجاح الجودة",
                "data_source": "get_quality_pass_rate_card",
                "color": "#e74c3c",
                "icon": "fa fa-check-circle",
            },
        ],
    }


@frappe.whitelist()
def get_supplier_spend_chart_data(from_date=None, to_date=None, supplier=None):
    """Get data for supplier spend donut chart"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    spend_data = analyzer.get_supplier_spend_analysis(from_date, to_date, supplier)

    # Limit to top 10 suppliers for readability
    supplier_data = spend_data["supplier_spend_data"][:10]

    return {
        "labels": [item["supplier_name"] for item in supplier_data],
        "datasets": [
            {
                "values": [flt(item["total_spend"], 2) for item in supplier_data],
            }
        ],
    }


@frappe.whitelist()
def get_monthly_spend_trend_data(from_date=None, to_date=None, supplier=None):
    """Get monthly spend trend data"""

    if not from_date:
        from_date = add_months(today(), -12)
    if not to_date:
        to_date = today()

    monthly_data = frappe.db.sql(
        """
        SELECT 
            DATE_FORMAT(posting_date, '%Y-%m') as month,
            SUM(grand_total) as total_spend,
            COUNT(*) as order_count
        FROM `tabPurchase Order`
        WHERE docstatus = 1 
            AND posting_date BETWEEN %(from_date)s AND %(to_date)s
            {supplier_condition}
        GROUP BY DATE_FORMAT(posting_date, '%Y-%m')
        ORDER BY month
        """.format(
            supplier_condition="AND supplier = %(supplier)s" if supplier else ""
        ),
        {"from_date": from_date, "to_date": to_date, "supplier": supplier},
        as_dict=True,
    )

    return {
        "labels": [item["month"] for item in monthly_data],
        "datasets": [
            {
                "name": _("Spend Amount"),
                "values": [flt(item["total_spend"], 2) for item in monthly_data],
            },
            {
                "name": _("Order Count"),
                "values": [item["order_count"] for item in monthly_data],
            },
        ],
    }


@frappe.whitelist()
def get_item_price_trends_data(from_date=None, to_date=None, item_group=None):
    """Get item price trends data for top items"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    price_data = analyzer.get_price_trend_analysis(
        item_group=item_group, from_date=from_date, to_date=to_date
    )

    # Get top 5 items by total spend
    top_items = sorted(
        price_data.items(),
        key=lambda x: sum([item["amount"] for item in x[1]["price_history"]]),
        reverse=True,
    )[:5]

    datasets = []
    for item_code, item_data in top_items:
        price_history = sorted(item_data["price_history"], key=lambda x: x["date"])
        datasets.append(
            {
                "name": item_data["item_name"][:30],  # Truncate for display
                "values": [flt(item["rate"], 3) for item in price_history],
            }
        )

    # Use dates from first item as labels
    labels = []
    if top_items:
        first_item = top_items[0][1]
        labels = [
            item["date"].strftime("%Y-%m")
            for item in sorted(first_item["price_history"], key=lambda x: x["date"])
        ]

    return {
        "labels": labels,
        "datasets": datasets,
    }


@frappe.whitelist()
def get_supplier_performance_data(from_date=None, to_date=None):
    """Get supplier performance bar chart data"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    performance_data = analyzer.get_supplier_performance_scorecard(
        from_date=from_date, to_date=to_date
    )

    # Get top 10 suppliers by performance score
    top_suppliers = sorted(
        performance_data["supplier_scorecards"],
        key=lambda x: x.get("overall_score", 0),
        reverse=True,
    )[:10]

    return {
        "labels": [item["supplier_name"] for item in top_suppliers],
        "datasets": [
            {
                "name": _("Quality Score"),
                "values": [flt(item.get("quality_score", 0), 1) for item in top_suppliers],
            },
            {
                "name": _("Delivery Score"),
                "values": [flt(item.get("delivery_score", 0), 1) for item in top_suppliers],
            },
        ],
    }


@frappe.whitelist()
def get_cost_breakdown_data(from_date=None, to_date=None):
    """Get cost breakdown by item group"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    breakdown_data = analyzer.get_cost_breakdown_analysis(from_date, to_date)

    return {
        "labels": [item["item_group"] for item in breakdown_data["item_group_breakdown"]],
        "datasets": [
            {
                "values": [
                    flt(item["total_amount"], 2) for item in breakdown_data["item_group_breakdown"]
                ],
            }
        ],
    }


@frappe.whitelist()
def get_procurement_kpis_data(from_date=None, to_date=None):
    """Get procurement KPIs for number cards"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    kpis = analyzer.get_procurement_kpis(from_date, to_date)

    return kpis["current_period"]


@frappe.whitelist()
def get_total_spend_card(from_date=None, to_date=None):
    """Get total spend card data"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    spend_data = analyzer.get_supplier_spend_analysis(from_date, to_date)

    currency = frappe.defaults.get_global_default("currency") or "OMR"

    return {
        "value": flt(spend_data["summary"]["total_spend"], 2),
        "formatted_value": f"{currency} {spend_data['summary']['total_spend']:,.2f}",
        "currency": currency,
    }


@frappe.whitelist()
def get_active_suppliers_card(from_date=None, to_date=None):
    """Get active suppliers card data"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    spend_data = analyzer.get_supplier_spend_analysis(from_date, to_date)

    return {
        "value": spend_data["summary"]["total_suppliers"],
        "formatted_value": str(spend_data["summary"]["total_suppliers"]),
    }


@frappe.whitelist()
def get_avg_order_value_card(from_date=None, to_date=None):
    """Get average order value card data"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    spend_data = analyzer.get_supplier_spend_analysis(from_date, to_date)

    currency = frappe.defaults.get_global_default("currency") or "OMR"
    avg_value = flt(spend_data["summary"]["avg_spend_per_supplier"], 2)

    return {
        "value": avg_value,
        "formatted_value": f"{currency} {avg_value:,.2f}",
        "currency": currency,
    }


@frappe.whitelist()
def get_quality_pass_rate_card(from_date=None, to_date=None):
    """Get quality pass rate card data"""

    from .cost_analysis import ProcurementCostAnalyzer

    analyzer = ProcurementCostAnalyzer()
    performance_data = analyzer.get_supplier_performance_scorecard(
        from_date=from_date, to_date=to_date
    )

    # Calculate overall quality pass rate
    total_inspections = 0
    passed_inspections = 0

    for supplier in performance_data["supplier_scorecards"]:
        supplier_inspections = supplier.get("total_inspections", 0)
        supplier_pass_rate = supplier.get("quality_score", 0) / 100

        total_inspections += supplier_inspections
        passed_inspections += supplier_inspections * supplier_pass_rate

    overall_pass_rate = (
        (passed_inspections / total_inspections * 100) if total_inspections > 0 else 0
    )

    return {
        "value": flt(overall_pass_rate, 1),
        "formatted_value": f"{overall_pass_rate:.1f}%",
    }


@frappe.whitelist()
def export_dashboard_data(from_date=None, to_date=None, format_type="excel"):
    """Export dashboard data in various formats"""

    from .cost_analysis import export_procurement_analytics

    return export_procurement_analytics(format_type, from_date, to_date)


def create_cost_analysis_dashboard():
    """Create the Cost Analysis Dashboard DocType and Page"""

    # Create Dashboard Page
    dashboard_page = {
        "doctype": "Page",
        "name": "cost-analysis-dashboard",
        "title": _("Cost Analysis Dashboard"),
        "page_name": "cost-analysis-dashboard",
        "module": "Universal Workshop",
        "standard": "Yes",
        "system_page": 1,
        "roles": [
            {"role": "Purchase Manager"},
            {"role": "Purchase User"},
            {"role": "Accounts Manager"},
            {"role": "Workshop Manager"},
        ],
    }

    if not frappe.db.exists("Page", "cost-analysis-dashboard"):
        page_doc = frappe.get_doc(dashboard_page)
        page_doc.insert(ignore_permissions=True)

    # Create Workspace if it doesn't exist
    workspace = {
        "doctype": "Workspace",
        "name": "Procurement Analytics",
        "title": _("Procurement Analytics"),
        "icon": "fa fa-chart-line",
        "module": "Universal Workshop",
        "parent_page": "",
        "public": 1,
        "charts": [
            {
                "chart_name": "Supplier Spend Analysis",
                "label": _("Supplier Spend Analysis"),
            },
            {
                "chart_name": "Monthly Spend Trend",
                "label": _("Monthly Spend Trend"),
            },
        ],
        "shortcuts": [
            {
                "type": "DocType",
                "doctype": "Purchase Order",
                "label": _("Purchase Orders"),
            },
            {
                "type": "DocType",
                "doctype": "Purchase Receipt",
                "label": _("Purchase Receipts"),
            },
            {
                "type": "DocType",
                "doctype": "Supplier",
                "label": _("Suppliers"),
            },
            {
                "type": "Page",
                "page": "cost-analysis-dashboard",
                "label": _("Cost Analysis Dashboard"),
            },
        ],
    }

    if not frappe.db.exists("Workspace", "Procurement Analytics"):
        workspace_doc = frappe.get_doc(workspace)
        workspace_doc.insert(ignore_permissions=True)


def install_cost_analysis_dashboard():
    """Install cost analysis dashboard and related components"""

    try:
        # Create dashboard page and workspace
        create_cost_analysis_dashboard()

        # Create custom role if needed
        if not frappe.db.exists("Role", "Procurement Analyst"):
            role_doc = frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": "Procurement Analyst",
                    "description": _("Can view and analyze procurement data"),
                    "is_custom": 1,
                }
            )
            role_doc.insert(ignore_permissions=True)

        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Cost Analysis Dashboard installed successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Dashboard installation error: {str(e)}")
        return {
            "status": "error",
            "message": f"Installation failed: {str(e)}",
        }
