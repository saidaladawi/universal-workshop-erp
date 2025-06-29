# pylint: disable=no-member
"""Data Aggregation Utilities for Analytics Reporting

This module provides data aggregation procedures and scheduled jobs to populate
analytics tables from operational data for the Universal Workshop ERP.
"""

import json
import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, now_datetime, add_days
from datetime import datetime, timedelta


def setup_default_workshop_kpis():
    """Setup default KPIs for workshop operations"""

    default_kpis = [
        {
            "kpi_code": "MONTHLY_REVENUE",
            "kpi_name": "Monthly Revenue",
            "kpi_name_ar": "الإيرادات الشهرية",
            "kpi_category": "Financial",
            "calculation_type": "Simple Aggregation",
            "frequency": "Daily",
            "source_doctype": "Sales Invoice",
            "source_field": "grand_total",
            "aggregation_function": "SUM",
            "filters_json": json.dumps(
                {"docstatus": 1, "posting_date": [">=", add_days(getdate(), -30)]}
            ),
            "target_value": 50000.0,  # OMR 50,000 monthly target
        },
        {
            "kpi_code": "CUSTOMER_SATISFACTION",
            "kpi_name": "Customer Satisfaction Score",
            "kpi_name_ar": "درجة رضا العملاء",
            "kpi_category": "Customer",
            "calculation_type": "Simple Aggregation",
            "frequency": "Daily",
            "source_doctype": "Customer Feedback",
            "source_field": "satisfaction_score",
            "aggregation_function": "AVG",
            "filters_json": json.dumps({"feedback_date": [">=", add_days(getdate(), -30)]}),
            "target_value": 4.5,  # Out of 5
        },
        {
            "kpi_code": "SERVICE_ORDERS_COMPLETED",
            "kpi_name": "Completed Service Orders",
            "kpi_name_ar": "أوامر الخدمة المكتملة",
            "kpi_category": "Operational",
            "calculation_type": "Simple Aggregation",
            "frequency": "Daily",
            "source_doctype": "Service Order",
            "source_field": "name",
            "aggregation_function": "COUNT",
            "filters_json": json.dumps(
                {"status": "Completed", "completion_date": [">=", add_days(getdate(), -30)]}
            ),
            "target_value": 150.0,  # 150 orders per month
        },
        {
            "kpi_code": "TECHNICIAN_PRODUCTIVITY",
            "kpi_name": "Average Technician Productivity",
            "kpi_name_ar": "متوسط إنتاجية الفنيين",
            "kpi_category": "Technician",
            "calculation_type": "Custom Formula",
            "frequency": "Daily",
            "calculation_script": """
# Calculate technician productivity (orders per technician per day)
from frappe.utils import add_days, getdate

completed_orders = frappe.db.count('Service Order', {
    'status': 'Completed',
    'completion_date': ['>=', add_days(getdate(), -30)]
})

active_technicians = frappe.db.count('Technician', {
    'employment_status': 'Active'
})

if active_technicians > 0:
    result = completed_orders / active_technicians / 30  # per day
else:
    result = 0
""",
            "target_value": 1.5,  # 1.5 orders per technician per day
        },
        {
            "kpi_code": "PARTS_INVENTORY_TURNOVER",
            "kpi_name": "Parts Inventory Turnover",
            "kpi_name_ar": "معدل دوران مخزون القطع",
            "kpi_category": "Inventory",
            "calculation_type": "Custom Formula",
            "frequency": "Weekly",
            "calculation_script": """
# Calculate inventory turnover rate
from frappe.utils import add_days, getdate

# Get total cost of goods sold (parts used)
parts_used = frappe.db.sql('''
    SELECT SUM(amount) 
    FROM `tabStock Ledger Entry` 
    WHERE voucher_type = 'Service Order' 
    AND posting_date >= %s
''', [add_days(getdate(), -30)])[0][0] or 0

# Get average inventory value
avg_inventory = frappe.db.sql('''
    SELECT AVG(valuation_rate * actual_qty) 
    FROM `tabStock Ledger Entry` 
    WHERE posting_date >= %s
''', [add_days(getdate(), -30)])[0][0] or 1

result = parts_used / avg_inventory if avg_inventory > 0 else 0
""",
            "target_value": 4.0,  # 4 times per month
        },
        {
            "kpi_code": "SERVICE_BAY_UTILIZATION",
            "kpi_name": "Service Bay Utilization Rate",
            "kpi_name_ar": "معدل استخدام أحواض الخدمة",
            "kpi_category": "Operational",
            "calculation_type": "Custom Formula",
            "frequency": "Daily",
            "calculation_script": """
# Calculate service bay utilization
from frappe.utils import add_days, getdate, time_diff_in_hours

# Get total available hours (assume 8 hours per day, 30 days)
total_bays = frappe.db.count('Service Bay', {'is_active': 1})
total_available_hours = total_bays * 8 * 30

# Get total utilized hours
utilized_hours = frappe.db.sql('''
    SELECT SUM(TIME_TO_SEC(TIMEDIFF(end_time, start_time))/3600) 
    FROM `tabService Order` 
    WHERE status IN ('In Progress', 'Completed')
    AND start_time >= %s
''', [add_days(getdate(), -30)])[0][0] or 0

result = (utilized_hours / total_available_hours * 100) if total_available_hours > 0 else 0
""",
            "target_value": 75.0,  # 75% utilization
        },
    ]

    created_kpis = []
    for kpi_data in default_kpis:
        # Check if KPI already exists
        if not frappe.db.exists("Analytics KPI", kpi_data["kpi_code"]):
            kpi = frappe.new_doc("Analytics KPI")
            kpi.update(kpi_data)
            kpi.insert()
            created_kpis.append(kpi.kpi_code)

    return created_kpis


@frappe.whitelist()
def update_workshop_kpis():
    """Update all workshop KPIs - to be called by scheduler"""

    from universal_workshop.analytics_reporting.doctype.analytics_kpi.analytics_kpi import (
        update_all_kpis,
    )

    try:
        results = update_all_kpis()

        # Log results
        frappe.logger().info(f"KPI Update Results: {results}")

        return {"status": "success", "message": f"Updated {len(results)} KPIs", "results": results}

    except Exception as e:
        frappe.log_error(f"Error updating workshop KPIs: {str(e)}", "KPI Update Error")
        return {"status": "error", "message": str(e)}


def get_revenue_analytics():
    """Get comprehensive revenue analytics"""

    # Current month revenue
    current_month_revenue = frappe.db.sql(
        """
        SELECT 
            SUM(grand_total) as total_revenue,
            COUNT(*) as invoice_count,
            AVG(grand_total) as avg_invoice_value
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        AND MONTH(posting_date) = MONTH(CURDATE())
        AND YEAR(posting_date) = YEAR(CURDATE())
    """,
        as_dict=True,
    )[0]

    # Previous month for comparison
    previous_month_revenue = frappe.db.sql(
        """
        SELECT 
            SUM(grand_total) as total_revenue,
            COUNT(*) as invoice_count
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        AND posting_date >= DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE())-1 DAY), INTERVAL 1 MONTH)
        AND posting_date < DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE())-1 DAY)
    """,
        as_dict=True,
    )[0]

    # Calculate growth
    current_revenue = current_month_revenue.get("total_revenue", 0) or 0
    previous_revenue = previous_month_revenue.get("total_revenue", 0) or 0

    revenue_growth = 0
    if previous_revenue > 0:
        revenue_growth = ((current_revenue - previous_revenue) / previous_revenue) * 100

    return {
        "current_month": current_month_revenue,
        "previous_month": previous_month_revenue,
        "revenue_growth_percentage": flt(revenue_growth, 2),
    }


def get_customer_analytics():
    """Get customer-related analytics"""

    # Customer satisfaction metrics
    satisfaction_data = frappe.db.sql(
        """
        SELECT 
            AVG(satisfaction_score) as avg_satisfaction,
            COUNT(*) as feedback_count,
            SUM(CASE WHEN satisfaction_score >= 4 THEN 1 ELSE 0 END) as positive_feedback
        FROM `tabCustomer Feedback`
        WHERE feedback_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    """,
        as_dict=True,
    )[0]

    # Customer retention
    retention_data = frappe.db.sql(
        """
        SELECT 
            COUNT(DISTINCT customer) as total_customers,
            COUNT(DISTINCT CASE WHEN last_service_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY) 
                                THEN customer END) as active_customers
        FROM `tabCustomer`
        WHERE creation <= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
    """,
        as_dict=True,
    )[0]

    total_customers = retention_data.get("total_customers", 0) or 0
    active_customers = retention_data.get("active_customers", 0) or 0
    retention_rate = (active_customers / total_customers * 100) if total_customers > 0 else 0

    return {
        "satisfaction": satisfaction_data,
        "retention_rate": flt(retention_rate, 2),
        "customer_counts": retention_data,
    }


def get_operational_analytics():
    """Get operational efficiency analytics"""

    # Service completion metrics
    service_metrics = frappe.db.sql(
        """
        SELECT 
            COUNT(*) as total_orders,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_orders,
            AVG(CASE WHEN status = 'Completed' AND start_time IS NOT NULL AND end_time IS NOT NULL
                     THEN TIME_TO_SEC(TIMEDIFF(end_time, start_time))/3600 END) as avg_completion_time
        FROM `tabService Order`
        WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    """,
        as_dict=True,
    )[0]

    # Technician productivity
    technician_metrics = frappe.db.sql(
        """
        SELECT 
            COUNT(DISTINCT t.name) as total_technicians,
            COUNT(DISTINCT so.assigned_technician) as active_technicians,
            COUNT(so.name) / COUNT(DISTINCT so.assigned_technician) as avg_orders_per_technician
        FROM `tabTechnician` t
        LEFT JOIN `tabService Order` so ON so.assigned_technician = t.name 
            AND so.creation >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        WHERE t.employment_status = 'Active'
    """,
        as_dict=True,
    )[0]

    return {"service_metrics": service_metrics, "technician_metrics": technician_metrics}


def get_inventory_analytics():
    """Get inventory-related analytics"""

    # Inventory turnover
    inventory_data = frappe.db.sql(
        """
        SELECT 
            SUM(CASE WHEN actual_qty < 0 THEN ABS(actual_qty * valuation_rate) ELSE 0 END) as parts_consumed,
            AVG(CASE WHEN actual_qty > 0 THEN actual_qty * valuation_rate ELSE 0 END) as avg_inventory_value
        FROM `tabStock Ledger Entry`
        WHERE posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    """,
        as_dict=True,
    )[0]

    # Low stock items
    low_stock_items = frappe.db.sql(
        """
        SELECT COUNT(*) as low_stock_count
        FROM `tabItem`
        WHERE is_stock_item = 1
        AND EXISTS (
            SELECT 1 FROM `tabBin` 
            WHERE item_code = `tabItem`.item_code 
            AND actual_qty <= reorder_level
        )
    """,
        as_dict=True,
    )[0]

    return {
        "inventory_metrics": inventory_data,
        "low_stock_count": low_stock_items.get("low_stock_count", 0),
    }


@frappe.whitelist()
def get_dashboard_summary():
    """Get comprehensive dashboard summary for executive view"""

    try:
        summary = {
            "revenue": get_revenue_analytics(),
            "customers": get_customer_analytics(),
            "operations": get_operational_analytics(),
            "inventory": get_inventory_analytics(),
            "last_updated": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        }

        return summary

    except Exception as e:
        frappe.log_error(f"Error generating dashboard summary: {str(e)}", "Dashboard Summary Error")
        raise


def setup_kpi_scheduler_jobs():
    """Setup scheduled jobs for KPI updates"""

    scheduler_jobs = [
        {
            "job_name": "update_workshop_kpis",
            "cron_format": "0 */6 * * *",  # Every 6 hours
            "python_path": "universal_workshop.analytics_reporting.data_aggregation.update_workshop_kpis",
        },
        {
            "job_name": "cleanup_old_kpi_history",
            "cron_format": "0 2 * * 0",  # Weekly on Sunday at 2 AM
            "python_path": "universal_workshop.analytics_reporting.doctype.analytics_kpi_history.analytics_kpi_history.cleanup_old_history",
        },
    ]

    return scheduler_jobs
