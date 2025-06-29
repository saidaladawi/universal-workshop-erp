import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, today, now_datetime
import json
from datetime import datetime, timedelta


def get_context(context):
    """Get context for Universal Workshop Dashboard"""

    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    # Check user permissions
    if not has_dashboard_access():
        frappe.throw(_("You don't have permission to access the dashboard"))

    # Get workshop configuration
    workshop_config = get_workshop_config()

    # Get dashboard data
    dashboard_data = get_dashboard_data()

    # Get KPI data
    kpi_data = get_kpi_data()

    # Get recent activities
    recent_activities = get_recent_activities()

    # Get alerts and notifications
    alerts = get_dashboard_alerts()

    # Update context
    context.update(
        {
            "title": _("Universal Workshop Dashboard"),
            "workshop_config": workshop_config,
            "dashboard_data": dashboard_data,
            "kpi_data": kpi_data,
            "recent_activities": recent_activities,
            "alerts": alerts,
            "user_name": frappe.get_user().full_name,
            "user_roles": frappe.get_roles(),
            "current_date": today(),
            "current_time": now_datetime().strftime("%H:%M"),
            "language": frappe.local.lang or "en",
            "is_rtl": frappe.local.lang == "ar",
        }
    )

    return context


def has_dashboard_access():
    """Check if current user has access to dashboard"""
    allowed_roles = ["Workshop Owner", "Workshop Manager", "System Manager", "Administrator"]

    user_roles = frappe.get_roles()
    return any(role in allowed_roles for role in user_roles)


def get_workshop_config():
    """Get workshop configuration and branding"""
    try:
        workshop = frappe.get_list(
            "Workshop Profile",
            filters={"status": "Active"},
            fields=[
                "workshop_name",
                "workshop_name_ar",
                "logo",
                "primary_color",
                "secondary_color",
                "business_license",
                "vat_number",
                "phone",
                "email",
                "address",
                "address_ar",
            ],
            limit=1,
        )

        if workshop:
            return workshop[0]
        else:
            return {
                "workshop_name": "Universal Workshop",
                "workshop_name_ar": "الورشة الشاملة",
                "logo": None,
                "primary_color": "#667eea",
                "secondary_color": "#764ba2",
            }

    except Exception as e:
        frappe.log_error(f"Error getting workshop config: {e}")
        return {}


def get_dashboard_data():
    """Get main dashboard statistics"""
    try:
        today_date = today()

        # Service Orders Statistics
        total_service_orders = frappe.db.count("Service Order")
        pending_service_orders = frappe.db.count("Service Order", {"status": "Pending"})
        in_progress_service_orders = frappe.db.count("Service Order", {"status": "In Progress"})
        completed_today = frappe.db.count(
            "Service Order", {"status": "Completed", "completion_date": today_date}
        )

        # Customer Statistics
        total_customers = frappe.db.count("Customer")
        new_customers_today = frappe.db.count("Customer", {"creation": [">=", today_date]})

        # Vehicle Statistics
        total_vehicles = frappe.db.count("Vehicle")
        vehicles_in_service = frappe.db.count("Vehicle", {"status": "In Service"})

        # Financial Statistics
        today_revenue = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND posting_date = %s
        """,
                [today_date],
            )[0][0]
            or 0
        )

        monthly_revenue = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND MONTH(posting_date) = MONTH(%s)
            AND YEAR(posting_date) = YEAR(%s)
        """,
                [today_date, today_date],
            )[0][0]
            or 0
        )

        # Inventory Statistics
        low_stock_items = frappe.db.count(
            "Item", {"is_stock_item": 1, "actual_qty": ["<=", "reorder_level"]}
        )

        return {
            "service_orders": {
                "total": total_service_orders,
                "pending": pending_service_orders,
                "in_progress": in_progress_service_orders,
                "completed_today": completed_today,
            },
            "customers": {"total": total_customers, "new_today": new_customers_today},
            "vehicles": {"total": total_vehicles, "in_service": vehicles_in_service},
            "financial": {
                "today_revenue": flt(today_revenue, 3),
                "monthly_revenue": flt(monthly_revenue, 3),
            },
            "inventory": {"low_stock_items": low_stock_items},
        }

    except Exception as e:
        frappe.log_error(f"Error getting dashboard data: {e}")
        return {}


def get_kpi_data():
    """Get Key Performance Indicators"""
    try:
        # Calculate date ranges
        today_date = today()
        week_start = getdate(today_date) - timedelta(days=6)
        month_start = getdate(today_date).replace(day=1)

        # Service Efficiency KPIs
        avg_service_time = (
            frappe.db.sql(
                """
            SELECT AVG(DATEDIFF(completion_date, service_date)) as avg_days
            FROM `tabService Order`
            WHERE status = 'Completed'
            AND completion_date >= %s
        """,
                [week_start],
            )[0][0]
            or 0
        )

        # Customer Satisfaction
        avg_satisfaction = (
            frappe.db.sql(
                """
            SELECT AVG(satisfaction_rating) as avg_rating
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
        """,
                [month_start],
            )[0][0]
            or 0
        )

        # Revenue Growth
        last_month_revenue = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND MONTH(posting_date) = MONTH(DATE_SUB(%s, INTERVAL 1 MONTH))
            AND YEAR(posting_date) = YEAR(DATE_SUB(%s, INTERVAL 1 MONTH))
        """,
                [today_date, today_date],
            )[0][0]
            or 0
        )

        current_month_revenue = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND MONTH(posting_date) = MONTH(%s)
            AND YEAR(posting_date) = YEAR(%s)
        """,
                [today_date, today_date],
            )[0][0]
            or 0
        )

        revenue_growth = 0
        if last_month_revenue > 0:
            revenue_growth = (
                (current_month_revenue - last_month_revenue) / last_month_revenue
            ) * 100

        # Technician Utilization
        total_technicians = frappe.db.count("Workshop Technician", {"status": "Active"})
        busy_technicians = frappe.db.count(
            "Workshop Technician", {"status": "Active", "current_availability": "Busy"}
        )

        technician_utilization = 0
        if total_technicians > 0:
            technician_utilization = (busy_technicians / total_technicians) * 100

        return {
            "service_efficiency": {"avg_service_time": flt(avg_service_time, 1), "unit": _("days")},
            "customer_satisfaction": {"avg_rating": flt(avg_satisfaction, 1), "max_rating": 5},
            "revenue_growth": {
                "percentage": flt(revenue_growth, 1),
                "trend": "up" if revenue_growth > 0 else "down" if revenue_growth < 0 else "stable",
            },
            "technician_utilization": {
                "percentage": flt(technician_utilization, 1),
                "busy_count": busy_technicians,
                "total_count": total_technicians,
            },
        }

    except Exception as e:
        frappe.log_error(f"Error getting KPI data: {e}")
        return {}


def get_recent_activities():
    """Get recent activities for dashboard"""
    try:
        activities = []

        # Recent Service Orders
        recent_services = frappe.get_list(
            "Service Order",
            fields=["name", "customer", "vehicle", "status", "creation", "modified"],
            order_by="creation desc",
            limit=10,
        )

        for service in recent_services:
            activities.append(
                {
                    "type": "service_order",
                    "title": f"Service Order {service.name}",
                    "description": f"Customer: {service.customer}",
                    "timestamp": service.creation,
                    "status": service.status,
                    "icon": "tool",
                }
            )

        # Recent Customer Registrations
        recent_customers = frappe.get_list(
            "Customer",
            fields=["customer_name", "customer_name_ar", "creation"],
            order_by="creation desc",
            limit=5,
        )

        for customer in recent_customers:
            name = (
                customer.customer_name_ar if frappe.local.lang == "ar" else customer.customer_name
            )
            activities.append(
                {
                    "type": "customer",
                    "title": _("New Customer Registered"),
                    "description": name,
                    "timestamp": customer.creation,
                    "icon": "user",
                }
            )

        # Sort activities by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return activities[:15]  # Return top 15 activities

    except Exception as e:
        frappe.log_error(f"Error getting recent activities: {e}")
        return []


def get_dashboard_alerts():
    """Get alerts and notifications for dashboard"""
    try:
        alerts = []

        # Low Stock Alerts
        low_stock_items = frappe.get_list(
            "Item",
            filters={"is_stock_item": 1, "actual_qty": ["<=", "reorder_level"]},
            fields=["item_name", "actual_qty", "reorder_level"],
            limit=5,
        )

        for item in low_stock_items:
            alerts.append(
                {
                    "type": "warning",
                    "title": _("Low Stock Alert"),
                    "message": f"{item.item_name}: {item.actual_qty} remaining",
                    "priority": "medium",
                    "action": "reorder",
                }
            )

        # Overdue Service Orders
        overdue_services = frappe.get_list(
            "Service Order",
            filters={
                "status": ["in", ["Pending", "In Progress"]],
                "expected_completion_date": ["<", today()],
            },
            fields=["name", "customer", "expected_completion_date"],
            limit=5,
        )

        for service in overdue_services:
            alerts.append(
                {
                    "type": "danger",
                    "title": _("Overdue Service"),
                    "message": f"Service Order {service.name} for {service.customer}",
                    "priority": "high",
                    "action": "follow_up",
                }
            )

        # License Expiry Check
        try:
            from universal_workshop.license_management.license_validator import (
                validate_current_license,
            )

            license_status = validate_current_license()

            if license_status.get("days_remaining", 0) <= 30:
                alerts.append(
                    {
                        "type": "warning",
                        "title": _("License Expiry Warning"),
                        "message": f"License expires in {license_status.get('days_remaining', 0)} days",
                        "priority": "high",
                        "action": "renew_license",
                    }
                )
        except:
            pass

        return alerts

    except Exception as e:
        frappe.log_error(f"Error getting dashboard alerts: {e}")
        return []


@frappe.whitelist()
def get_dashboard_chart_data(chart_type="revenue", period="week"):
    """Get data for dashboard charts"""
    try:
        if chart_type == "revenue":
            return get_revenue_chart_data(period)
        elif chart_type == "service_orders":
            return get_service_orders_chart_data(period)
        elif chart_type == "customer_satisfaction":
            return get_satisfaction_chart_data(period)
        else:
            return {}

    except Exception as e:
        frappe.log_error(f"Error getting chart data: {e}")
        return {}


def get_revenue_chart_data(period="week"):
    """Get revenue chart data"""
    try:
        if period == "week":
            # Last 7 days
            data = frappe.db.sql(
                """
                SELECT 
                    DATE(posting_date) as date,
                    SUM(grand_total) as revenue
                FROM `tabSales Invoice`
                WHERE docstatus = 1 
                AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(posting_date)
                ORDER BY date
            """,
                as_dict=True,
            )
        elif period == "month":
            # Last 30 days
            data = frappe.db.sql(
                """
                SELECT 
                    DATE(posting_date) as date,
                    SUM(grand_total) as revenue
                FROM `tabSales Invoice`
                WHERE docstatus = 1 
                AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY DATE(posting_date)
                ORDER BY date
            """,
                as_dict=True,
            )

        return {
            "labels": [str(d.date) for d in data],
            "datasets": [
                {
                    "label": _("Revenue (OMR)"),
                    "data": [flt(d.revenue, 3) for d in data],
                    "backgroundColor": "rgba(102, 126, 234, 0.1)",
                    "borderColor": "rgba(102, 126, 234, 1)",
                    "borderWidth": 2,
                    "fill": True,
                }
            ],
        }

    except Exception as e:
        frappe.log_error(f"Error getting revenue chart data: {e}")
        return {}


def get_service_orders_chart_data(period="week"):
    """Get service orders chart data"""
    try:
        if period == "week":
            data = frappe.db.sql(
                """
                SELECT 
                    DATE(creation) as date,
                    COUNT(*) as count
                FROM `tabService Order`
                WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(creation)
                ORDER BY date
            """,
                as_dict=True,
            )

        return {
            "labels": [str(d.date) for d in data],
            "datasets": [
                {
                    "label": _("Service Orders"),
                    "data": [d.count for d in data],
                    "backgroundColor": "rgba(118, 75, 162, 0.1)",
                    "borderColor": "rgba(118, 75, 162, 1)",
                    "borderWidth": 2,
                    "fill": True,
                }
            ],
        }

    except Exception as e:
        frappe.log_error(f"Error getting service orders chart data: {e}")
        return {}


def get_satisfaction_chart_data(period="week"):
    """Get customer satisfaction chart data"""
    try:
        if period == "week":
            data = frappe.db.sql(
                """
                SELECT 
                    DATE(creation) as date,
                    AVG(satisfaction_rating) as avg_rating
                FROM `tabCustomer Feedback`
                WHERE creation >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(creation)
                ORDER BY date
            """,
                as_dict=True,
            )

        return {
            "labels": [str(d.date) for d in data],
            "datasets": [
                {
                    "label": _("Customer Satisfaction"),
                    "data": [flt(d.avg_rating, 1) for d in data],
                    "backgroundColor": "rgba(40, 167, 69, 0.1)",
                    "borderColor": "rgba(40, 167, 69, 1)",
                    "borderWidth": 2,
                    "fill": True,
                }
            ],
        }

    except Exception as e:
        frappe.log_error(f"Error getting satisfaction chart data: {e}")
        return {}


@frappe.whitelist()
def mark_alert_read(alert_id):
    """Mark alert as read"""
    try:
        # Implementation for marking alerts as read
        # This would depend on how alerts are stored
        return {"status": "success"}
    except Exception as e:
        frappe.log_error(f"Error marking alert as read: {e}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def refresh_dashboard_data():
    """Refresh dashboard data"""
    try:
        return {
            "dashboard_data": get_dashboard_data(),
            "kpi_data": get_kpi_data(),
            "alerts": get_dashboard_alerts(),
            "timestamp": now_datetime().isoformat(),
        }
    except Exception as e:
        frappe.log_error(f"Error refreshing dashboard data: {e}")
        return {"status": "error", "message": str(e)}
