# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, time_diff, now, today, get_datetime, add_days
from datetime import datetime, timedelta
import json


class LaborTimeTracker:
    """Comprehensive labor time tracking system for Universal Workshop ERP"""

    def __init__(self, service_order_id=None):
        self.service_order_id = service_order_id
        self.service_order = None
        if service_order_id:
            self.service_order = frappe.get_doc("Service Order", service_order_id)

    def start_time_tracking(self, technician_id, activity_type="Service Work", notes=None):
        """Start time tracking for a technician on a service order"""
        try:
            # Check if technician already has active tracking
            active_log = frappe.db.exists(
                "Labor Time Log",
                {
                    "technician": technician_id,
                    "service_order": self.service_order_id,
                    "status": "Active",
                    "end_time": ["is", "not set"],
                },
            )

            if active_log:
                frappe.throw(
                    _(
                        "Technician {0} already has active time tracking on this service order"
                    ).format(technician_id)
                )

            # Create new labor time log
            time_log = frappe.new_doc("Labor Time Log")
            time_log.update(
                {
                    "technician": technician_id,
                    "service_order": self.service_order_id,
                    "activity_type": activity_type,
                    "start_time": now(),
                    "status": "Active",
                    "notes": notes or "",
                }
            )

            # Set default hourly rate from technician profile
            technician_doc = frappe.get_doc("Technician", technician_id)
            time_log.hourly_rate = technician_doc.hourly_rate or 10.0  # Default OMR 10/hour

            time_log.insert()

            # Update service order status if needed
            if self.service_order and self.service_order.status == "Pending":
                self.service_order.status = "In Progress"
                self.service_order.save()

            return {
                "success": True,
                "log_id": time_log.name,
                "message": _("Time tracking started for technician {0}").format(technician_id),
            }

        except Exception as e:
            frappe.log_error(f"Error starting time tracking: {str(e)}")
            return {
                "success": False,
                "message": _("Failed to start time tracking: {0}").format(str(e)),
            }

    def pause_time_tracking(self, log_id, pause_reason=None):
        """Pause active time tracking"""
        try:
            time_log = frappe.get_doc("Labor Time Log", log_id)

            if time_log.status != "Active":
                frappe.throw(_("Can only pause active time tracking"))

            # Calculate elapsed time
            if time_log.start_time:
                current_elapsed = time_diff(now(), time_log.start_time)
                time_log.total_hours = flt(time_log.total_hours) + flt(current_elapsed) / 3600

            time_log.status = "Paused"
            time_log.pause_time = now()
            time_log.pause_reason = pause_reason
            time_log.save()

            return {
                "success": True,
                "message": _("Time tracking paused"),
                "total_hours": time_log.total_hours,
            }

        except Exception as e:
            frappe.log_error(f"Error pausing time tracking: {str(e)}")
            return {
                "success": False,
                "message": _("Failed to pause time tracking: {0}").format(str(e)),
            }

    def resume_time_tracking(self, log_id):
        """Resume paused time tracking"""
        try:
            time_log = frappe.get_doc("Labor Time Log", log_id)

            if time_log.status != "Paused":
                frappe.throw(_("Can only resume paused time tracking"))

            time_log.status = "Active"
            time_log.resume_time = now()
            time_log.save()

            return {"success": True, "message": _("Time tracking resumed")}

        except Exception as e:
            frappe.log_error(f"Error resuming time tracking: {str(e)}")
            return {
                "success": False,
                "message": _("Failed to resume time tracking: {0}").format(str(e)),
            }

    def stop_time_tracking(self, log_id, completion_notes=None):
        """Stop time tracking and calculate final totals"""
        try:
            time_log = frappe.get_doc("Labor Time Log", log_id)

            if time_log.status not in ["Active", "Paused"]:
                frappe.throw(_("Can only stop active or paused time tracking"))

            # Calculate final total hours
            if time_log.status == "Active" and time_log.start_time:
                current_elapsed = time_diff(now(), time_log.start_time)
                time_log.total_hours = flt(time_log.total_hours) + flt(current_elapsed) / 3600

            time_log.end_time = now()
            time_log.status = "Completed"
            time_log.completion_notes = completion_notes

            # Calculate total cost
            time_log.total_cost = flt(time_log.total_hours) * flt(time_log.hourly_rate)

            time_log.save()

            # Create or update timesheet entry for payroll integration
            self.create_timesheet_entry(time_log)

            # Update service order labor costs
            self.update_service_order_labor_costs()

            return {
                "success": True,
                "message": _("Time tracking completed"),
                "total_hours": time_log.total_hours,
                "total_cost": time_log.total_cost,
            }

        except Exception as e:
            frappe.log_error(f"Error stopping time tracking: {str(e)}")
            return {
                "success": False,
                "message": _("Failed to stop time tracking: {0}").format(str(e)),
            }

    def create_timesheet_entry(self, time_log):
        """Create ERPNext timesheet entry for payroll integration"""
        try:
            # Check if timesheet already exists
            existing_timesheet = frappe.db.exists(
                "Timesheet",
                {
                    "employee": time_log.technician,
                    "start_date": get_datetime(time_log.start_time).date(),
                },
            )

            if existing_timesheet:
                timesheet = frappe.get_doc("Timesheet", existing_timesheet)
            else:
                timesheet = frappe.new_doc("Timesheet")
                timesheet.employee = time_log.technician
                timesheet.start_date = get_datetime(time_log.start_time).date()
                timesheet.end_date = get_datetime(time_log.end_time or now()).date()

            # Add time log entry
            timesheet.append(
                "time_logs",
                {
                    "activity_type": time_log.activity_type,
                    "from_time": time_log.start_time,
                    "to_time": time_log.end_time,
                    "hours": time_log.total_hours,
                    "project": self.service_order_id,  # Link to service order as project
                    "billable": 1,
                    "billing_hours": time_log.total_hours,
                    "billing_rate": time_log.hourly_rate,
                    "billing_amount": time_log.total_cost,
                },
            )

            timesheet.save()

            # Link back to labor time log
            time_log.timesheet = timesheet.name
            time_log.save()

        except Exception as e:
            frappe.log_error(f"Error creating timesheet entry: {str(e)}")

    def update_service_order_labor_costs(self):
        """Update service order with total labor costs"""
        if not self.service_order:
            return

        try:
            # Calculate total labor costs from all completed time logs
            total_labor_cost = frappe.db.sql(
                """
                SELECT SUM(total_cost) as total_cost,
                       SUM(total_hours) as total_hours
                FROM `tabLabor Time Log`
                WHERE service_order = %s AND status = 'Completed'
            """,
                [self.service_order_id],
                as_dict=True,
            )[0]

            if total_labor_cost:
                self.service_order.total_labor_hours = flt(total_labor_cost.total_hours or 0)
                self.service_order.total_labor_cost = flt(total_labor_cost.total_cost or 0)
                self.service_order.save()

        except Exception as e:
            frappe.log_error(f"Error updating service order labor costs: {str(e)}")

    def get_active_time_tracking(self, technician_id=None):
        """Get active time tracking sessions"""
        filters = {"service_order": self.service_order_id, "status": ["in", ["Active", "Paused"]]}

        if technician_id:
            filters["technician"] = technician_id

        return frappe.get_list(
            "Labor Time Log",
            filters=filters,
            fields=[
                "name",
                "technician",
                "activity_type",
                "start_time",
                "total_hours",
                "status",
                "hourly_rate",
                "notes",
            ],
        )

    def get_time_tracking_summary(self, date_range=None):
        """Get comprehensive time tracking summary"""
        filters = {"service_order": self.service_order_id}

        if date_range:
            filters["start_time"] = ["between", date_range]

        time_logs = frappe.get_list(
            "Labor Time Log",
            filters=filters,
            fields=[
                "name",
                "technician",
                "activity_type",
                "start_time",
                "end_time",
                "total_hours",
                "total_cost",
                "status",
                "notes",
            ],
        )

        # Calculate summary statistics
        total_hours = sum(flt(log.total_hours or 0) for log in time_logs)
        total_cost = sum(flt(log.total_cost or 0) for log in time_logs)

        # Group by technician
        technician_summary = {}
        for log in time_logs:
            tech = log.technician
            if tech not in technician_summary:
                technician_summary[tech] = {
                    "technician": tech,
                    "total_hours": 0,
                    "total_cost": 0,
                    "sessions": 0,
                }

            technician_summary[tech]["total_hours"] += flt(log.total_hours or 0)
            technician_summary[tech]["total_cost"] += flt(log.total_cost or 0)
            technician_summary[tech]["sessions"] += 1

        return {
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_sessions": len(time_logs),
            "time_logs": time_logs,
            "technician_summary": list(technician_summary.values()),
        }


# API Methods for time tracking operations
@frappe.whitelist()
def start_labor_tracking(service_order_id, technician_id, activity_type="Service Work", notes=None):
    """Start labor time tracking for a service order"""
    tracker = LaborTimeTracker(service_order_id)
    return tracker.start_time_tracking(technician_id, activity_type, notes)


@frappe.whitelist()
def pause_labor_tracking(log_id, pause_reason=None):
    """Pause active labor time tracking"""
    time_log = frappe.get_doc("Labor Time Log", log_id)
    tracker = LaborTimeTracker(time_log.service_order)
    return tracker.pause_time_tracking(log_id, pause_reason)


@frappe.whitelist()
def resume_labor_tracking(log_id):
    """Resume paused labor time tracking"""
    time_log = frappe.get_doc("Labor Time Log", log_id)
    tracker = LaborTimeTracker(time_log.service_order)
    return tracker.resume_time_tracking(log_id)


@frappe.whitelist()
def stop_labor_tracking(log_id, completion_notes=None):
    """Stop labor time tracking and calculate totals"""
    time_log = frappe.get_doc("Labor Time Log", log_id)
    tracker = LaborTimeTracker(time_log.service_order)
    return tracker.stop_time_tracking(log_id, completion_notes)


@frappe.whitelist()
def get_active_labor_tracking(service_order_id, technician_id=None):
    """Get active time tracking sessions for a service order"""
    tracker = LaborTimeTracker(service_order_id)
    return tracker.get_active_time_tracking(technician_id)


@frappe.whitelist()
def get_labor_tracking_summary(service_order_id, from_date=None, to_date=None):
    """Get comprehensive labor time tracking summary"""
    tracker = LaborTimeTracker(service_order_id)
    date_range = None
    if from_date and to_date:
        date_range = [from_date, to_date]
    return tracker.get_time_tracking_summary(date_range)


@frappe.whitelist()
def get_technician_productivity(technician_id, from_date=None, to_date=None):
    """Get technician productivity metrics"""
    filters = {"technician": technician_id, "status": "Completed"}

    if from_date and to_date:
        filters["start_time"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["start_time"] = [">=", from_date]
    elif to_date:
        filters["start_time"] = ["<=", to_date]

    time_logs = frappe.get_list(
        "Labor Time Log",
        filters=filters,
        fields=[
            "service_order",
            "total_hours",
            "total_cost",
            "start_time",
            "end_time",
            "activity_type",
        ],
    )

    # Calculate productivity metrics
    total_hours = sum(flt(log.total_hours or 0) for log in time_logs)
    total_revenue = sum(flt(log.total_cost or 0) for log in time_logs)
    total_jobs = len(set(log.service_order for log in time_logs))

    # Calculate average time per job
    avg_time_per_job = total_hours / total_jobs if total_jobs > 0 else 0
    avg_revenue_per_hour = total_revenue / total_hours if total_hours > 0 else 0

    return {
        "technician": technician_id,
        "period": {"from_date": from_date, "to_date": to_date},
        "metrics": {
            "total_hours": total_hours,
            "total_revenue": total_revenue,
            "total_jobs": total_jobs,
            "avg_time_per_job": avg_time_per_job,
            "avg_revenue_per_hour": avg_revenue_per_hour,
        },
        "time_logs": time_logs,
    }


@frappe.whitelist()
def auto_complete_daily_tracking():
    """Auto-complete any active tracking sessions at end of day"""
    active_logs = frappe.get_list(
        "Labor Time Log", filters={"status": "Active"}, fields=["name", "service_order"]
    )

    completed_count = 0
    for log in active_logs:
        try:
            tracker = LaborTimeTracker(log.service_order)
            result = tracker.stop_time_tracking(
                log.name, completion_notes="Auto-completed at end of day"
            )
            if result["success"]:
                completed_count += 1
        except Exception as e:
            frappe.log_error(f"Error auto-completing time log {log.name}: {str(e)}")

    return {
        "success": True,
        "message": _("Auto-completed {0} active time tracking sessions").format(completed_count),
        "completed_count": completed_count,
    }
