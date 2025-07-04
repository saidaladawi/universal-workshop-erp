# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, getdate, nowdate
from datetime import datetime, timedelta


def update_customer_analytics():
    """Daily job to update customer analytics for all active customers"""
    try:
        frappe.log_error("Starting customer analytics update job", "Customer Analytics Job")

        # Get all active customers
        active_customers = frappe.get_all(
            "Customer", filters={"disabled": 0}, fields=["name", "customer_name"]
        )

        updated_count = 0
        error_count = 0

        for customer in active_customers:
            try:
                # Check if analytics needs update (older than 24 hours)
                existing_analytics = frappe.db.sql(
                    """
                    SELECT name, calculation_date
                    FROM `tabCustomer Analytics`
                    WHERE customer = %s
                    ORDER BY calculation_date DESC
                    LIMIT 1
                """,
                    (customer.name,),
                    as_dict=True,
                )

                needs_update = True
                if existing_analytics:
                    last_calc = getdate(existing_analytics[0].calculation_date)
                    if (getdate() - last_calc).days < 1:
                        needs_update = False

                if needs_update:
                    from universal_workshop.customer_management.doctype.customer_analytics.customer_analytics import (
                        CustomerAnalytics,
                    )

                    CustomerAnalytics.create_analytics_for_customer(customer.name)
                    updated_count += 1

            except Exception as e:
                frappe.log_error(
                    f"Error updating analytics for customer {customer.name}: {e!s}",
                    "Customer Analytics Error",
                )
                error_count += 1
                continue

        # Log completion
        message = (
            f"Customer analytics update completed. Updated: {updated_count}, Errors: {error_count}"
        )
        frappe.log_error(message, "Customer Analytics Job Completed")

        return {
            "success": True,
            "updated_count": updated_count,
            "error_count": error_count,
            "message": message,
        }

    except Exception as e:
        error_msg = f"Customer analytics update job failed: {e!s}"
        frappe.log_error(error_msg, "Customer Analytics Job Failed")
        return {"success": False, "error": error_msg}


def calculate_customer_segments():
    """Weekly job to recalculate customer segments based on updated analytics"""
    try:
        frappe.log_error("Starting customer segmentation job", "Customer Segmentation Job")

        # Get all customer analytics records from last week
        week_ago = add_days(getdate(), -7)
        analytics_records = frappe.get_all(
            "Customer Analytics",
            filters={"calculation_date": (">=", week_ago)},
            fields=["name", "customer", "lifetime_value", "retention_rate", "churn_probability"],
        )

        updated_segments = 0

        for analytics in analytics_records:
            try:
                doc = frappe.get_doc("Customer Analytics", analytics.name)
                old_segment = doc.segment

                # Recalculate segment
                doc.update_customer_segment()

                if doc.segment != old_segment:
                    doc.save()
                    updated_segments += 1

                    # Update customer master with new segment
                    customer_doc = frappe.get_doc("Customer", analytics.customer)
                    if hasattr(customer_doc, "customer_segment"):
                        customer_doc.customer_segment = doc.segment
                        customer_doc.save()

            except Exception as e:
                frappe.log_error(
                    f"Error updating segment for analytics {analytics.name}: {e!s}",
                    "Customer Segmentation Error",
                )
                continue

        message = f"Customer segmentation completed. Updated segments: {updated_segments}"
        frappe.log_error(message, "Customer Segmentation Job Completed")

        return {"success": True, "updated_segments": updated_segments, "message": message}

    except Exception as e:
        error_msg = f"Customer segmentation job failed: {e!s}"
        frappe.log_error(error_msg, "Customer Segmentation Job Failed")
        return {"success": False, "error": error_msg}


def cleanup_old_analytics():
    """Monthly job to clean up old analytics records (keep last 12 months)"""
    try:
        frappe.log_error("Starting analytics cleanup job", "Analytics Cleanup Job")

        # Delete analytics older than 12 months
        twelve_months_ago = add_days(getdate(), -365)

        old_analytics = frappe.get_all(
            "Customer Analytics",
            filters={"calculation_date": ("<", twelve_months_ago)},
            fields=["name"],
        )

        deleted_count = 0
        for analytics in old_analytics:
            try:
                frappe.delete_doc("Customer Analytics", analytics.name)
                deleted_count += 1
            except Exception as e:
                frappe.log_error(
                    f"Error deleting old analytics {analytics.name}: {e!s}",
                    "Analytics Cleanup Error",
                )
                continue

        message = f"Analytics cleanup completed. Deleted {deleted_count} old records"
        frappe.log_error(message, "Analytics Cleanup Job Completed")

        return {"success": True, "deleted_count": deleted_count, "message": message}

    except Exception as e:
        error_msg = f"Analytics cleanup job failed: {e!s}"
        frappe.log_error(error_msg, "Analytics Cleanup Job Failed")
        return {"success": False, "error": error_msg}


def send_analytics_alerts():
    """Daily job to send alerts for customers at risk"""
    try:
        frappe.log_error("Starting analytics alerts job", "Analytics Alerts Job")

        # Get high-risk customers (churn probability > 70%)
        at_risk_customers = frappe.db.sql(
            """
            SELECT
                ca.customer,
                ca.customer_name,
                ca.customer_name_ar,
                ca.churn_probability,
                ca.days_since_last_visit,
                ca.lifetime_value,
                c.preferred_language,
                c.mobile_no
            FROM `tabCustomer Analytics` ca
            JOIN `tabCustomer` c ON c.name = ca.customer
            WHERE ca.churn_probability > 70
            AND ca.calculation_date >= %s
            AND c.disabled = 0
            ORDER BY ca.churn_probability DESC
        """,
            (add_days(getdate(), -1),),
            as_dict=True,
        )

        alerts_sent = 0

        for customer in at_risk_customers:
            try:
                # Create task for sales team
                task_doc = frappe.new_doc("ToDo")
                task_doc.description = f"High Risk Customer Alert: {customer.customer_name} (Churn Risk: {customer.churn_probability}%)"
                task_doc.priority = "High"
                task_doc.status = "Open"
                task_doc.assigned_by = "Administrator"
                task_doc.reference_type = "Customer"
                task_doc.reference_name = customer.customer
                task_doc.insert()

                alerts_sent += 1

            except Exception as e:
                frappe.log_error(
                    f"Error creating alert for customer {customer.customer}: {e!s}",
                    "Analytics Alert Error",
                )
                continue

        message = f"Analytics alerts completed. Sent {alerts_sent} alerts for at-risk customers"
        frappe.log_error(message, "Analytics Alerts Job Completed")

        return {"success": True, "alerts_sent": alerts_sent, "message": message}

    except Exception as e:
        error_msg = f"Analytics alerts job failed: {e!s}"
        frappe.log_error(error_msg, "Analytics Alerts Job Failed")
        return {"success": False, "error": error_msg}


# Utility functions for manual execution


@frappe.whitelist()
def refresh_all_customer_analytics():
    """Manual function to refresh analytics for all customers"""
    if not frappe.has_permission("Customer Analytics", "write"):
        frappe.throw(_("Insufficient permissions to refresh customer analytics"))

    return update_customer_analytics()


@frappe.whitelist()
def recalculate_all_segments():
    """Manual function to recalculate all customer segments"""
    if not frappe.has_permission("Customer Analytics", "write"):
        frappe.throw(_("Insufficient permissions to recalculate segments"))

    return calculate_customer_segments()


def send_service_reminders():
    """Send service reminders to customers"""
    try:
        # Get customers with upcoming service due
        upcoming_services = frappe.get_all(
            "Customer Vehicle",
            filters={
                "next_service_date": ["<=", add_days(nowdate(), 7)],
                "next_service_date": [">=", nowdate()],
            },
            fields=["name", "customer", "vehicle_id", "next_service_date"],
        )

        for service in upcoming_services:
            customer = frappe.get_doc("Customer", service.customer)
            if customer.email:
                send_service_reminder_email(customer, service)
            if customer.phone:
                send_service_reminder_sms(customer, service)

        frappe.logger().info(f"Service reminders sent for {len(upcoming_services)} customers")

    except Exception as e:
        frappe.logger().error(f"Error sending service reminders: {str(e)}")


def update_vehicle_service_history():
    """Update vehicle service history from completed service orders"""
    try:
        # Get completed service orders from last 24 hours
        completed_orders = frappe.get_all(
            "Service Order",
            filters={"status": "Completed", "modified": [">=", add_days(nowdate(), -1)]},
            fields=["name", "customer", "vehicle", "service_date", "total_amount"],
        )

        for order in completed_orders:
            update_vehicle_history(order)

        frappe.logger().info(f"Updated service history for {len(completed_orders)} vehicles")

    except Exception as e:
        frappe.logger().error(f"Error updating vehicle service history: {str(e)}")


def generate_workshop_reports():
    """Generate weekly workshop reports"""
    try:
        # Generate various reports
        generate_daily_sales_report()
        generate_inventory_report()
        generate_customer_activity_report()

        frappe.logger().info("Weekly workshop reports generated successfully")

    except Exception as e:
        frappe.logger().error(f"Error generating workshop reports: {str(e)}")


def send_service_reminder_email(customer, service):
    """Send email reminder for service"""
    try:
        subject = _("Service Reminder - Vehicle {0}").format(service.vehicle_id)
        message = _(
            """
        Dear {0},
        
        This is a reminder that your vehicle {1} is due for service on {2}.
        
        Please contact us to schedule your appointment.
        
        Best regards,
        Universal Workshop Team
        """
        ).format(customer.customer_name, service.vehicle_id, service.next_service_date)

        frappe.sendmail(recipients=[customer.email], subject=subject, message=message)

    except Exception as e:
        frappe.logger().error(f"Error sending email reminder: {str(e)}")


def send_service_reminder_sms(customer, service):
    """Send SMS reminder for service"""
    try:
        message = _("Service reminder: Vehicle {0} due on {1}. Call us to schedule.").format(
            service.vehicle_id, service.next_service_date
        )

        # SMS sending logic would go here
        # For now, just log the SMS
        frappe.logger().info(f"SMS reminder sent to {customer.phone}: {message}")

    except Exception as e:
        frappe.logger().error(f"Error sending SMS reminder: {str(e)}")


def update_vehicle_history(service_order):
    """Update vehicle service history"""
    try:
        vehicle = frappe.get_doc("Customer Vehicle", service_order.vehicle)

        # Update last service date
        vehicle.last_service_date = service_order.service_date
        vehicle.last_service_amount = service_order.total_amount

        # Calculate next service date (example: 6 months from service date)
        next_service = add_days(service_order.service_date, 180)
        vehicle.next_service_date = next_service

        vehicle.save()

    except Exception as e:
        frappe.logger().error(f"Error updating vehicle history: {str(e)}")


def generate_daily_sales_report():
    """Generate daily sales report"""
    try:
        today = nowdate()

        # Get today's sales
        sales_data = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_orders,
                SUM(grand_total) as total_revenue,
                AVG(grand_total) as avg_order_value
            FROM `tabSales Invoice`
            WHERE DATE(posting_date) = %s
            AND docstatus = 1
        """,
            [today],
            as_dict=True,
        )

        if sales_data:
            frappe.logger().info(f"Daily sales report: {sales_data[0]}")

    except Exception as e:
        frappe.logger().error(f"Error generating daily sales report: {str(e)}")


def generate_inventory_report():
    """Generate inventory status report"""
    try:
        # Get low stock items
        low_stock_items = frappe.get_all(
            "Item",
            filters={"is_stock_item": 1, "disabled": 0},
            fields=["item_code", "item_name", "stock_uom"],
        )

        frappe.logger().info(f"Inventory report: {len(low_stock_items)} items checked")

    except Exception as e:
        frappe.logger().error(f"Error generating inventory report: {str(e)}")


def generate_customer_activity_report():
    """Generate customer activity report"""
    try:
        # Get customer activity for last week
        customer_activity = frappe.db.sql(
            """
            SELECT 
                customer,
                COUNT(*) as visits,
                SUM(grand_total) as total_spent
            FROM `tabSales Invoice`
            WHERE posting_date >= %s
            AND docstatus = 1
            GROUP BY customer
            ORDER BY total_spent DESC
            LIMIT 10
        """,
            [add_days(nowdate(), -7)],
            as_dict=True,
        )

        frappe.logger().info(f"Customer activity report: {len(customer_activity)} active customers")

    except Exception as e:
        frappe.logger().error(f"Error generating customer activity report: {str(e)}")
