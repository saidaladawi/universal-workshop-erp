# pylint: disable=no-member
"""Service Bay Utilization Report

This report provides comprehensive analytics on service bay utilization including
capacity planning insights, efficiency metrics, and revenue analysis.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate, add_days, time_diff_in_hours
from datetime import datetime, timedelta


def execute(filters=None):
    """Execute Service Bay Utilization report"""

    if not filters:
        filters = {}

    # Validate required filters
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw(_("From Date and To Date are required"))

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data


def get_columns(filters):
    """Get report columns based on filters"""

    columns = [
        {
            "fieldname": "service_bay",
            "label": _("Service Bay"),
            "fieldtype": "Link",
            "options": "Service Bay",
            "width": 150,
        },
        {"fieldname": "bay_name_ar", "label": _("اسم الحوض"), "fieldtype": "Data", "width": 120},
    ]

    # Add date column if grouping by date
    if filters.get("group_by") in ["Daily", "Weekly", "Monthly"]:
        columns.append({"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100})

    columns.extend(
        [
            {
                "fieldname": "total_hours",
                "label": _("Total Available Hours"),
                "fieldtype": "Float",
                "precision": 2,
                "width": 140,
            },
            {
                "fieldname": "utilized_hours",
                "label": _("Utilized Hours"),
                "fieldtype": "Float",
                "precision": 2,
                "width": 120,
            },
            {
                "fieldname": "utilization_percentage",
                "label": _("Utilization %"),
                "fieldtype": "Percent",
                "width": 100,
            },
            {
                "fieldname": "service_orders_count",
                "label": _("Service Orders"),
                "fieldtype": "Int",
                "width": 100,
            },
            {
                "fieldname": "avg_service_time",
                "label": _("Avg Service Time (hrs)"),
                "fieldtype": "Float",
                "precision": 2,
                "width": 140,
            },
            {
                "fieldname": "downtime_hours",
                "label": _("Downtime Hours"),
                "fieldtype": "Float",
                "precision": 2,
                "width": 120,
            },
            {
                "fieldname": "revenue_generated",
                "label": _("Revenue Generated"),
                "fieldtype": "Currency",
                "width": 130,
            },
            {
                "fieldname": "efficiency_score",
                "label": _("Efficiency Score"),
                "fieldtype": "Float",
                "precision": 1,
                "width": 120,
            },
        ]
    )

    return columns


def get_data(filters):
    """Get report data"""

    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    # Get service bays
    bay_filters = {"is_active": 1}
    if filters.get("service_bay"):
        bay_filters["name"] = filters.get("service_bay")
    if filters.get("workshop"):
        bay_filters["workshop"] = filters.get("workshop")

    service_bays = frappe.get_list(
        "Service Bay",
        filters=bay_filters,
        fields=["name", "bay_name", "bay_name_ar", "working_hours_per_day"],
    )

    if not service_bays:
        return []

    data = []
    group_by = filters.get("group_by", "Daily")

    if group_by == "Daily":
        data = get_daily_utilization(service_bays, from_date, to_date, filters)
    elif group_by == "Weekly":
        data = get_weekly_utilization(service_bays, from_date, to_date, filters)
    elif group_by == "Monthly":
        data = get_monthly_utilization(service_bays, from_date, to_date, filters)
    else:
        data = get_summary_utilization(service_bays, from_date, to_date, filters)

    return data


def get_daily_utilization(service_bays, from_date, to_date, filters):
    """Get daily utilization data"""

    data = []
    current_date = from_date

    while current_date <= to_date:
        for bay in service_bays:
            utilization_data = calculate_bay_utilization(bay, current_date, current_date, filters)
            utilization_data["date"] = current_date
            data.append(utilization_data)

        current_date = add_days(current_date, 1)

    return data


def get_weekly_utilization(service_bays, from_date, to_date, filters):
    """Get weekly utilization data"""

    data = []
    current_date = from_date

    while current_date <= to_date:
        week_end = min(add_days(current_date, 6), to_date)

        for bay in service_bays:
            utilization_data = calculate_bay_utilization(bay, current_date, week_end, filters)
            utilization_data["date"] = current_date
            data.append(utilization_data)

        current_date = add_days(week_end, 1)

    return data


def get_monthly_utilization(service_bays, from_date, to_date, filters):
    """Get monthly utilization data"""

    data = []
    current_date = from_date.replace(day=1)

    while current_date <= to_date:
        # Get last day of month
        if current_date.month == 12:
            next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            next_month = current_date.replace(month=current_date.month + 1, day=1)

        month_end = min((next_month - timedelta(days=1)).date(), to_date)
        month_start = max(current_date, from_date)

        for bay in service_bays:
            utilization_data = calculate_bay_utilization(bay, month_start, month_end, filters)
            utilization_data["date"] = month_start
            data.append(utilization_data)

        current_date = next_month.date()

    return data


def get_summary_utilization(service_bays, from_date, to_date, filters):
    """Get summary utilization data for the entire period"""

    data = []

    for bay in service_bays:
        utilization_data = calculate_bay_utilization(bay, from_date, to_date, filters)
        data.append(utilization_data)

    return data


def calculate_bay_utilization(bay, from_date, to_date, filters):
    """Calculate utilization metrics for a service bay in a date range"""

    # Calculate total available hours
    days_count = (getdate(to_date) - getdate(from_date)).days + 1
    working_hours_per_day = flt(bay.get("working_hours_per_day", 8))
    total_hours = days_count * working_hours_per_day

    # Get service orders for this bay in the date range
    service_orders = frappe.db.sql(
        """
        SELECT 
            name,
            start_time,
            end_time,
            status,
            grand_total
        FROM `tabService Order`
        WHERE service_bay = %s
        AND DATE(start_time) BETWEEN %s AND %s
        AND docstatus = 1
    """,
        [bay.name, from_date, to_date],
        as_dict=True,
    )

    # Calculate metrics
    utilized_hours = 0
    service_orders_count = len(service_orders)
    total_revenue = 0
    completed_orders = 0

    for order in service_orders:
        if order.start_time and order.end_time:
            order_duration = time_diff_in_hours(order.end_time, order.start_time)
            utilized_hours += order_duration

        if order.status == "Completed":
            completed_orders += 1

        if order.grand_total:
            total_revenue += flt(order.grand_total)

    # Calculate derived metrics
    utilization_percentage = (utilized_hours / total_hours * 100) if total_hours > 0 else 0
    avg_service_time = (utilized_hours / service_orders_count) if service_orders_count > 0 else 0
    downtime_hours = total_hours - utilized_hours

    # Calculate efficiency score (composite metric)
    efficiency_score = calculate_efficiency_score(
        utilization_percentage, service_orders_count, completed_orders, total_revenue
    )

    return {
        "service_bay": bay.name,
        "bay_name_ar": bay.get("bay_name_ar", ""),
        "total_hours": flt(total_hours, 2),
        "utilized_hours": flt(utilized_hours, 2),
        "utilization_percentage": flt(utilization_percentage, 1),
        "service_orders_count": service_orders_count,
        "avg_service_time": flt(avg_service_time, 2),
        "downtime_hours": flt(downtime_hours, 2),
        "revenue_generated": flt(total_revenue, 2),
        "efficiency_score": flt(efficiency_score, 1),
    }


def calculate_efficiency_score(utilization_pct, total_orders, completed_orders, revenue):
    """Calculate composite efficiency score (0-100)"""

    # Utilization component (40% weight)
    utilization_score = min(utilization_pct, 100) * 0.4

    # Completion rate component (30% weight)
    completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    completion_score = completion_rate * 0.3

    # Revenue productivity component (30% weight)
    # Normalize revenue to a 0-100 scale (assume 1000 OMR as good daily revenue)
    revenue_score = min(revenue / 1000 * 100, 100) * 0.3

    return utilization_score + completion_score + revenue_score


def get_chart_data(filters, data):
    """Generate chart data for the report"""

    if not data:
        return None

    # Group data for chart
    chart_data = {
        "data": {
            "labels": [],
            "datasets": [
                {"name": "Utilization %", "values": []},
                {"name": "Efficiency Score", "values": []},
            ],
        },
        "type": "line",
        "height": 300,
    }

    for row in data:
        if filters.get("group_by") in ["Daily", "Weekly", "Monthly"]:
            label = row.get("date", "").strftime("%Y-%m-%d") if row.get("date") else ""
        else:
            label = row.get("service_bay", "")

        chart_data["data"]["labels"].append(label)
        chart_data["data"]["datasets"][0]["values"].append(row.get("utilization_percentage", 0))
        chart_data["data"]["datasets"][1]["values"].append(row.get("efficiency_score", 0))

    return chart_data


@frappe.whitelist()
def get_bay_capacity_insights(service_bay, from_date, to_date):
    """Get capacity planning insights for a service bay"""

    bay_data = frappe.get_doc("Service Bay", service_bay)

    # Get historical utilization
    utilization_data = calculate_bay_utilization(
        bay_data.as_dict(), getdate(from_date), getdate(to_date), {}
    )

    # Calculate capacity insights
    current_utilization = utilization_data["utilization_percentage"]
    current_orders = utilization_data["service_orders_count"]

    # Capacity recommendations
    insights = {
        "current_utilization": current_utilization,
        "capacity_status": get_capacity_status(current_utilization),
        "recommended_actions": get_capacity_recommendations(current_utilization, current_orders),
        "potential_additional_orders": calculate_additional_capacity(
            utilization_data["total_hours"], utilization_data["avg_service_time"]
        ),
        "peak_hours_analysis": get_peak_hours_analysis(service_bay, from_date, to_date),
    }

    return insights


def get_capacity_status(utilization_pct):
    """Get capacity status based on utilization percentage"""

    if utilization_pct < 50:
        return "Under-utilized"
    elif utilization_pct < 75:
        return "Optimal"
    elif utilization_pct < 90:
        return "High Utilization"
    else:
        return "Over-utilized"


def get_capacity_recommendations(utilization_pct, orders_count):
    """Get capacity planning recommendations"""

    recommendations = []

    if utilization_pct < 50:
        recommendations.append("Consider marketing initiatives to increase bookings")
        recommendations.append("Evaluate staffing levels for cost optimization")
    elif utilization_pct > 85:
        recommendations.append("Consider extending working hours or adding shifts")
        recommendations.append("Implement appointment scheduling optimization")
        recommendations.append("Evaluate adding additional service bays")

    if orders_count > 0:
        recommendations.append(f"Current processing {orders_count} orders in the period")

    return recommendations


def calculate_additional_capacity(total_hours, avg_service_time):
    """Calculate how many additional orders could be accommodated"""

    if avg_service_time > 0:
        return int(total_hours / avg_service_time)

    return 0


def get_peak_hours_analysis(service_bay, from_date, to_date):
    """Analyze peak usage hours for better scheduling"""

    hourly_data = frappe.db.sql(
        """
        SELECT 
            HOUR(start_time) as hour,
            COUNT(*) as order_count,
            AVG(TIME_TO_SEC(TIMEDIFF(end_time, start_time))/3600) as avg_duration
        FROM `tabService Order`
        WHERE service_bay = %s
        AND DATE(start_time) BETWEEN %s AND %s
        AND start_time IS NOT NULL
        AND end_time IS NOT NULL
        GROUP BY HOUR(start_time)
        ORDER BY order_count DESC
    """,
        [service_bay, from_date, to_date],
        as_dict=True,
    )

    return hourly_data[:5]  # Top 5 peak hours
