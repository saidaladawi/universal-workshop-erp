import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime, timedelta


def execute(filters=None):
    """Execute Customer Analytics Report"""

    if not filters:
        filters = {}

    # Get customer analytics data
    customer_data = get_customer_analytics_data(filters)

    # Prepare columns
    columns = get_columns()

    # Prepare data
    data = prepare_data(customer_data, filters)

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
            "fieldname": "customer_group",
            "label": _("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group",
            "width": 120,
        },
        {
            "fieldname": "customer_type",
            "label": _("Customer Type"),
            "fieldtype": "Data",
            "width": 120,
        },
        {"fieldname": "total_orders", "label": _("Total Orders"), "fieldtype": "Int", "width": 100},
        {
            "fieldname": "total_revenue",
            "label": _("Total Revenue (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 150,
        },
        {
            "fieldname": "avg_order_value",
            "label": _("Avg Order Value (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 150,
        },
        {
            "fieldname": "last_order_date",
            "label": _("Last Order Date"),
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "fieldname": "days_since_last_order",
            "label": _("Days Since Last Order"),
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "fieldname": "loyalty_points",
            "label": _("Loyalty Points"),
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "fieldname": "customer_status",
            "label": _("Customer Status"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "outstanding_amount",
            "label": _("Outstanding Amount (OMR)"),
            "fieldtype": "Currency",
            "options": "Company:company:default_currency",
            "width": 150,
        },
        {
            "fieldname": "payment_terms",
            "label": _("Payment Terms"),
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_customer_analytics_data(filters):
    """Get customer analytics data from database"""

    # Get filters
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    customer_group = filters.get("customer_group")
    customer_type = filters.get("customer_type")

    # Build conditions
    conditions = ["c.disabled = 0"]
    params = []

    if customer_group:
        conditions.append("c.customer_group = %s")
        params.append(customer_group)

    if customer_type:
        conditions.append("c.customer_type = %s")
        params.append(customer_type)

    # Get customer data with order statistics
    customer_data = frappe.db.sql(
        """
        SELECT 
            c.name as customer,
            c.customer_name,
            c.customer_name_ar,
            c.customer_group,
            c.customer_type,
            c.payment_terms,
            COUNT(DISTINCT si.name) as total_orders,
            SUM(si.grand_total) as total_revenue,
            MAX(si.posting_date) as last_order_date,
            SUM(si.outstanding_amount) as outstanding_amount
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Invoice` si ON c.name = si.customer AND si.docstatus = 1
        WHERE """
        + " AND ".join(conditions)
        + """
        GROUP BY c.name
        ORDER BY total_revenue DESC
    """,
        params,
        as_dict=1,
    )

    # Get loyalty points data
    loyalty_data = get_loyalty_points_data()

    # Process data
    processed_data = []

    for customer in customer_data:
        # Calculate average order value
        avg_order_value = (
            customer.total_revenue / customer.total_orders if customer.total_orders > 0 else 0
        )

        # Calculate days since last order
        days_since_last_order = 0
        if customer.last_order_date:
            days_since_last_order = (getdate() - customer.last_order_date).days

        # Get loyalty points
        loyalty_points = loyalty_data.get(customer.customer, 0)

        # Determine customer status
        customer_status = determine_customer_status(
            customer.total_orders,
            customer.total_revenue,
            days_since_last_order,
            customer.outstanding_amount,
        )

        processed_data.append(
            {
                "customer": customer.customer,
                "customer_name": customer.customer_name or "",
                "customer_name_ar": customer.customer_name_ar or "",
                "customer_group": customer.customer_group,
                "customer_type": customer.customer_type,
                "total_orders": customer.total_orders or 0,
                "total_revenue": customer.total_revenue or 0,
                "avg_order_value": avg_order_value,
                "last_order_date": customer.last_order_date,
                "days_since_last_order": days_since_last_order,
                "loyalty_points": loyalty_points,
                "customer_status": customer_status,
                "outstanding_amount": customer.outstanding_amount or 0,
                "payment_terms": customer.payment_terms,
            }
        )

    return processed_data


def get_loyalty_points_data():
    """Get loyalty points data for customers"""

    loyalty_data = frappe.db.sql(
        """
        SELECT 
            customer,
            SUM(points_earned - points_redeemed) as net_points
        FROM `tabCustomer Loyalty Points`
        WHERE docstatus = 1
        GROUP BY customer
    """,
        as_dict=1,
    )

    return {item.customer: item.net_points for item in loyalty_data}


def determine_customer_status(
    total_orders, total_revenue, days_since_last_order, outstanding_amount
):
    """Determine customer status based on various metrics"""

    if total_orders == 0:
        return "New"
    elif days_since_last_order <= 30:
        return "Active"
    elif days_since_last_order <= 90:
        return "At Risk"
    elif days_since_last_order <= 365:
        return "Inactive"
    else:
        return "Lost"

    # Additional logic for VIP customers
    if total_revenue > 10000:  # High value customers
        return "VIP"

    # Check for payment issues
    if outstanding_amount > 1000:
        return "Payment Issue"


def prepare_data(customer_data, filters):
    """Prepare data for report"""

    # Apply customer status filter if specified
    status_filter = filters.get("customer_status")
    if status_filter:
        customer_data = [item for item in customer_data if item["customer_status"] == status_filter]

    # Apply revenue filter if specified
    min_revenue = filters.get("min_revenue")
    if min_revenue:
        customer_data = [item for item in customer_data if item["total_revenue"] >= min_revenue]

    # Sort by total revenue (descending)
    customer_data.sort(key=lambda x: x["total_revenue"], reverse=True)

    return customer_data


def get_chart_data(data):
    """Generate chart data"""

    # Group by customer status
    status_data = {}
    for item in data:
        status = item["customer_status"]
        if status not in status_data:
            status_data[status] = {"count": 0, "total_revenue": 0, "avg_order_value": 0}

        status_data[status]["count"] += 1
        status_data[status]["total_revenue"] += item["total_revenue"]
        status_data[status]["avg_order_value"] += item["avg_order_value"]

    # Calculate averages
    for status in status_data:
        if status_data[status]["count"] > 0:
            status_data[status]["avg_order_value"] /= status_data[status]["count"]

    # Prepare chart data
    chart_data = {
        "data": {
            "labels": list(status_data.keys()),
            "datasets": [
                {
                    "name": "Customer Count",
                    "values": [status_data[status]["count"] for status in status_data.keys()],
                },
                {
                    "name": "Total Revenue (OMR)",
                    "values": [
                        status_data[status]["total_revenue"] for status in status_data.keys()
                    ],
                },
                {
                    "name": "Avg Order Value (OMR)",
                    "values": [
                        status_data[status]["avg_order_value"] for status in status_data.keys()
                    ],
                },
            ],
        },
        "type": "bar",
        "colors": ["#5e64ff", "#28a745", "#ffc107"],
        "height": 300,
    }

    return chart_data
