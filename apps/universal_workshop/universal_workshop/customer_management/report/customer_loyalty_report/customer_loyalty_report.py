import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime, timedelta


def execute(filters=None):
    """Execute Customer Loyalty Report"""

    if not filters:
        filters = {}

    # Get customer loyalty data
    loyalty_data = get_customer_loyalty_data(filters)

    # Prepare columns
    columns = get_columns()

    # Prepare data
    data = prepare_data(loyalty_data, filters)

    # Get chart data
    chart = get_chart_data(data)

    return columns, data, None, chart


def get_columns():
    """Define report columns"""
    return [
        {
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 120,
        },
        {
            "fieldname": "customer_name",
            "label": _("Customer Name"),
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "customer_name_ar",
            "label": _("اسم العميل"),
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "fieldname": "loyalty_tier",
            "label": _("Loyalty Tier"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "total_points_earned",
            "label": _("Total Points Earned"),
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "total_points_redeemed",
            "label": _("Total Points Redeemed"),
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "current_points",
            "label": _("Current Points"),
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "fieldname": "points_value",
            "label": _("Points Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 150,
        },
        {
            "fieldname": "redemption_rate",
            "label": _("Redemption Rate (%)"),
            "fieldtype": "Percent",
            "width": 150,
        },
        {
            "fieldname": "last_activity_date",
            "label": _("Last Activity Date"),
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "fieldname": "days_since_activity",
            "label": _("Days Since Activity"),
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "total_transactions",
            "label": _("Total Transactions"),
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "avg_points_per_transaction",
            "label": _("Avg Points/Transaction"),
            "fieldtype": "Float",
            "width": 150,
        },
        {
            "fieldname": "loyalty_status",
            "label": _("Loyalty Status"),
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_customer_loyalty_data(filters):
    """Get customer loyalty data from database"""

    # Get filters
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    loyalty_tier = filters.get("loyalty_tier")
    loyalty_status = filters.get("loyalty_status")

    # Build conditions
    conditions = ["clp.docstatus = 1"]
    params = []

    if from_date:
        conditions.append("clp.posting_date >= %s")
        params.append(from_date)

    if to_date:
        conditions.append("clp.posting_date <= %s")
        params.append(to_date)

    if loyalty_tier:
        conditions.append("clp.loyalty_tier = %s")
        params.append(loyalty_tier)

    # Get loyalty points data
    loyalty_data = frappe.db.sql(
        """
        SELECT 
            clp.customer,
            c.customer_name,
            c.customer_name_ar,
            clp.loyalty_tier,
            SUM(CASE WHEN clp.points_type = 'Earned' THEN clp.points ELSE 0 END) as total_points_earned,
            SUM(CASE WHEN clp.points_type = 'Redeemed' THEN clp.points ELSE 0 END) as total_points_redeemed,
            MAX(clp.posting_date) as last_activity_date,
            COUNT(clp.name) as total_transactions
        FROM `tabCustomer Loyalty Points` clp
        LEFT JOIN `tabCustomer` c ON clp.customer = c.name
        WHERE """
        + " AND ".join(conditions)
        + """
        GROUP BY clp.customer
        ORDER BY total_points_earned DESC
    """,
        params,
        as_dict=1,
    )

    # Process data
    processed_data = []

    for loyalty in loyalty_data:
        # Calculate current points
        current_points = loyalty.total_points_earned - loyalty.total_points_redeemed

        # Calculate points value (assuming 1 point = 0.01 OMR)
        points_value = current_points * 0.01

        # Calculate redemption rate
        redemption_rate = (
            (loyalty.total_points_redeemed / loyalty.total_points_earned * 100)
            if loyalty.total_points_earned > 0
            else 0
        )

        # Calculate average points per transaction
        avg_points_per_transaction = (
            loyalty.total_points_earned / loyalty.total_transactions
            if loyalty.total_transactions > 0
            else 0
        )

        # Calculate days since last activity
        days_since_activity = 0
        if loyalty.last_activity_date:
            days_since_activity = (getdate() - loyalty.last_activity_date).days

        # Determine loyalty status
        loyalty_status = determine_loyalty_status(
            current_points, days_since_activity, loyalty.total_transactions
        )

        processed_data.append(
            {
                "customer": loyalty.customer,
                "customer_name": loyalty.customer_name or "",
                "customer_name_ar": loyalty.customer_name_ar or "",
                "loyalty_tier": loyalty.loyalty_tier,
                "total_points_earned": loyalty.total_points_earned or 0,
                "total_points_redeemed": loyalty.total_points_redeemed or 0,
                "current_points": current_points,
                "points_value": points_value,
                "redemption_rate": redemption_rate,
                "last_activity_date": loyalty.last_activity_date,
                "days_since_activity": days_since_activity,
                "total_transactions": loyalty.total_transactions or 0,
                "avg_points_per_transaction": avg_points_per_transaction,
                "loyalty_status": loyalty_status,
            }
        )

    return processed_data


def determine_loyalty_status(current_points, days_since_activity, total_transactions):
    """Determine loyalty status based on various metrics"""

    if current_points >= 1000 and days_since_activity <= 30:
        return "VIP"
    elif current_points >= 500 and days_since_activity <= 60:
        return "Gold"
    elif current_points >= 200 and days_since_activity <= 90:
        return "Silver"
    elif current_points >= 50 and days_since_activity <= 180:
        return "Bronze"
    elif days_since_activity <= 365:
        return "Active"
    else:
        return "Inactive"


def prepare_data(loyalty_data, filters):
    """Prepare data for report"""

    # Apply loyalty status filter if specified
    status_filter = filters.get("loyalty_status")
    if status_filter:
        loyalty_data = [item for item in loyalty_data if item["loyalty_status"] == status_filter]

    # Apply minimum points filter if specified
    min_points = filters.get("min_points")
    if min_points:
        loyalty_data = [item for item in loyalty_data if item["current_points"] >= min_points]

    # Sort by current points (descending)
    loyalty_data.sort(key=lambda x: x["current_points"], reverse=True)

    return loyalty_data


def get_chart_data(data):
    """Generate chart data"""

    # Group by loyalty tier
    tier_data = {}
    for item in data:
        tier = item["loyalty_tier"] or "No Tier"

        if tier not in tier_data:
            tier_data[tier] = {"count": 0, "total_points": 0, "avg_points": 0}

        tier_data[tier]["count"] += 1
        tier_data[tier]["total_points"] += item["current_points"]
        tier_data[tier]["avg_points"] += item["current_points"]

    # Calculate averages
    for tier in tier_data:
        if tier_data[tier]["count"] > 0:
            tier_data[tier]["avg_points"] /= tier_data[tier]["count"]

    # Prepare chart data
    chart_data = {
        "data": {
            "labels": list(tier_data.keys()),
            "datasets": [
                {
                    "name": "Customer Count",
                    "values": [tier_data[tier]["count"] for tier in tier_data.keys()],
                },
                {
                    "name": "Total Points",
                    "values": [tier_data[tier]["total_points"] for tier in tier_data.keys()],
                },
                {
                    "name": "Avg Points",
                    "values": [tier_data[tier]["avg_points"] for tier in tier_data.keys()],
                },
            ],
        },
        "type": "bar",
        "colors": ["#5e64ff", "#28a745", "#ffc107"],
        "height": 300,
    }

    return chart_data
