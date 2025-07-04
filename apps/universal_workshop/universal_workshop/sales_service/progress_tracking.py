"""
Progress Tracking System for Universal Workshop ERP
Provides real-time tracking of service orders from estimate to completion
Supports Arabic localization and ERPNext v15 best practices
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, get_datetime, time_diff_in_hours
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Tuple

# pylint: disable=no-member


class ServiceOrderProgressTracker:
    """
    Manages progress tracking for service orders with real-time updates
    """

    def __init__(self, service_order_name: str):
        self.service_order = frappe.get_doc("Sales Order", service_order_name)
        self.progress_log = []
        self.status_history = []

    @frappe.whitelist()
    def update_progress(
        self,
        operation_id: str,
        status: str,
        progress_percentage: float = 0,
        technician: str = None,
        notes: str = "",
        time_spent: float = 0,
    ) -> Dict:
        """
        Update progress for specific operation

        Args:
            operation_id: ID of the operation being updated
            status: New status (not_started, in_progress, completed, on_hold)
            progress_percentage: Completion percentage (0-100)
            technician: Assigned technician
            notes: Progress notes
            time_spent: Time spent in hours

        Returns:
            Updated progress information
        """
        try:
            # Create progress log entry
            progress_entry = frappe.new_doc("Service Progress Log")
            progress_entry.service_order = self.service_order.name
            progress_entry.operation_id = operation_id
            progress_entry.status = status
            progress_entry.progress_percentage = flt(progress_percentage, 2)
            progress_entry.technician = technician or frappe.session.user
            progress_entry.notes = notes
            progress_entry.notes_ar = self._translate_to_arabic(notes) if notes else ""
            progress_entry.time_spent = flt(time_spent, 2)
            progress_entry.timestamp = get_datetime()
            progress_entry.insert()

            # Update overall service order progress
            self._update_overall_progress()

            # Send real-time notifications
            self._send_progress_notification(operation_id, status, progress_percentage)

            # Update timeline
            self._add_timeline_entry(operation_id, status, progress_percentage, notes)

            return {
                "status": "success",
                "message": _("Progress updated successfully"),
                "message_ar": "تم تحديث التقدم بنجاح",
                "progress_log_id": progress_entry.name,
                "overall_progress": self._calculate_overall_progress(),
            }

        except Exception as e:
            frappe.log_error(f"Progress update error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to update progress: {0}").format(str(e)),
                "message_ar": "فشل في تحديث التقدم: {0}".format(str(e)),
            }

    @frappe.whitelist()
    def get_progress_dashboard(self) -> Dict:
        """
        Get comprehensive progress dashboard data

        Returns:
            Dashboard data with progress information
        """
        try:
            # Get operations and their status
            operations = self._get_service_operations()

            # Calculate progress metrics
            overall_progress = self._calculate_overall_progress()

            # Get timeline data
            timeline = self._get_progress_timeline()

            # Get technician assignments
            technician_assignments = self._get_technician_assignments()

            # Get current status
            current_status = self._get_current_status()

            return {
                "status": "success",
                "data": {
                    "service_order": self.service_order.name,
                    "customer": self.service_order.customer,
                    "vehicle": getattr(self.service_order, "vehicle_registration", "N/A"),
                    "overall_progress": overall_progress,
                    "current_status": current_status,
                    "operations": operations,
                    "timeline": timeline,
                    "technician_assignments": technician_assignments,
                    "estimated_completion": self._calculate_estimated_completion(),
                    "quality_checkpoints": self._get_quality_checkpoints(),
                },
            }

        except Exception as e:
            frappe.log_error(f"Dashboard error: {str(e)}")
            return {"status": "error", "message": _("Failed to load dashboard: {0}").format(str(e))}

    @frappe.whitelist()
    def start_operation(self, operation_id: str, technician: str = None) -> Dict:
        """
        Start a specific operation

        Args:
            operation_id: Operation to start
            technician: Assigned technician

        Returns:
            Operation start result
        """
        return self.update_progress(
            operation_id=operation_id,
            status="in_progress",
            progress_percentage=5,
            technician=technician,
            notes=_("Operation started"),
            time_spent=0,
        )

    @frappe.whitelist()
    def complete_operation(self, operation_id: str, notes: str = "", time_spent: float = 0) -> Dict:
        """
        Complete a specific operation

        Args:
            operation_id: Operation to complete
            notes: Completion notes
            time_spent: Total time spent

        Returns:
            Operation completion result
        """
        return self.update_progress(
            operation_id=operation_id,
            status="completed",
            progress_percentage=100,
            notes=notes or _("Operation completed successfully"),
            time_spent=time_spent,
        )

    @frappe.whitelist()
    def hold_operation(self, operation_id: str, reason: str = "") -> Dict:
        """
        Put operation on hold

        Args:
            operation_id: Operation to hold
            reason: Hold reason

        Returns:
            Hold operation result
        """
        return self.update_progress(
            operation_id=operation_id,
            status="on_hold",
            notes=reason or _("Operation on hold"),
            time_spent=0,
        )

    def _get_service_operations(self) -> List[Dict]:
        """Get list of service operations with their progress"""
        operations = []

        # Get operations from service order items
        for item in self.service_order.items:
            if item.item_group == "Services":
                # Get latest progress for this operation
                latest_progress = frappe.db.sql(
                    """
                    SELECT status, progress_percentage, technician, notes, timestamp
                    FROM `tabService Progress Log`
                    WHERE service_order = %s AND operation_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """,
                    [self.service_order.name, item.name],
                    as_dict=True,
                )

                operation_data = {
                    "operation_id": item.name,
                    "operation_name": item.item_name,
                    "operation_name_ar": getattr(item, "item_name_ar", ""),
                    "description": item.description,
                    "estimated_hours": item.qty,
                    "status": latest_progress[0].status if latest_progress else "not_started",
                    "progress_percentage": (
                        latest_progress[0].progress_percentage if latest_progress else 0
                    ),
                    "technician": latest_progress[0].technician if latest_progress else "",
                    "last_updated": latest_progress[0].timestamp if latest_progress else "",
                    "notes": latest_progress[0].notes if latest_progress else "",
                }
                operations.append(operation_data)

        return operations

    def _calculate_overall_progress(self) -> Dict:
        """Calculate overall service order progress"""
        operations = self._get_service_operations()

        if not operations:
            return {"percentage": 0, "status": "not_started"}

        total_operations = len(operations)
        completed_operations = sum(1 for op in operations if op["status"] == "completed")
        in_progress_operations = sum(1 for op in operations if op["status"] == "in_progress")
        on_hold_operations = sum(1 for op in operations if op["status"] == "on_hold")

        # Calculate weighted progress
        total_progress = sum(op["progress_percentage"] for op in operations)
        overall_percentage = total_progress / total_operations if total_operations > 0 else 0

        # Determine overall status
        if completed_operations == total_operations:
            overall_status = "completed"
        elif on_hold_operations > 0:
            overall_status = "on_hold"
        elif in_progress_operations > 0:
            overall_status = "in_progress"
        else:
            overall_status = "not_started"

        return {
            "percentage": round(overall_percentage, 1),
            "status": overall_status,
            "completed_operations": completed_operations,
            "total_operations": total_operations,
            "in_progress_operations": in_progress_operations,
            "on_hold_operations": on_hold_operations,
        }

    def _get_progress_timeline(self) -> List[Dict]:
        """Get progress timeline for display"""
        timeline = frappe.db.sql(
            """
            SELECT 
                operation_id,
                status,
                progress_percentage,
                technician,
                notes,
                notes_ar,
                time_spent,
                timestamp,
                creation
            FROM `tabService Progress Log`
            WHERE service_order = %s
            ORDER BY timestamp DESC
            LIMIT 50
        """,
            [self.service_order.name],
            as_dict=True,
        )

        # Format timeline entries
        formatted_timeline = []
        for entry in timeline:
            formatted_entry = {
                "timestamp": entry.timestamp,
                "operation_id": entry.operation_id,
                "status": entry.status,
                "status_display": self._get_status_display(entry.status),
                "progress_percentage": entry.progress_percentage,
                "technician": entry.technician,
                "technician_name": frappe.db.get_value("User", entry.technician, "full_name")
                or entry.technician,
                "notes": entry.notes,
                "notes_ar": entry.notes_ar,
                "time_spent": entry.time_spent,
                "icon": self._get_status_icon(entry.status),
                "color": self._get_status_color(entry.status),
            }
            formatted_timeline.append(formatted_entry)

        return formatted_timeline

    def _get_technician_assignments(self) -> List[Dict]:
        """Get current technician assignments"""
        assignments = frappe.db.sql(
            """
            SELECT DISTINCT
                spl.technician,
                u.full_name as technician_name,
                spl.operation_id,
                COUNT(*) as active_operations,
                AVG(spl.progress_percentage) as avg_progress
            FROM `tabService Progress Log` spl
            LEFT JOIN `tabUser` u ON spl.technician = u.name
            WHERE spl.service_order = %s 
            AND spl.status IN ('in_progress', 'on_hold')
            GROUP BY spl.technician, spl.operation_id
            ORDER BY spl.timestamp DESC
        """,
            [self.service_order.name],
            as_dict=True,
        )

        return assignments

    def _get_current_status(self) -> Dict:
        """Get current service order status"""
        progress = self._calculate_overall_progress()

        status_mapping = {
            "not_started": {
                "label": _("Not Started"),
                "label_ar": "لم يبدأ",
                "color": "gray",
                "icon": "fa-clock-o",
            },
            "in_progress": {
                "label": _("In Progress"),
                "label_ar": "قيد التنفيذ",
                "color": "blue",
                "icon": "fa-cog fa-spin",
            },
            "on_hold": {
                "label": _("On Hold"),
                "label_ar": "متوقف",
                "color": "orange",
                "icon": "fa-pause",
            },
            "completed": {
                "label": _("Completed"),
                "label_ar": "مكتمل",
                "color": "green",
                "icon": "fa-check",
            },
        }

        current_status = status_mapping.get(progress["status"], status_mapping["not_started"])
        current_status["progress_percentage"] = progress["percentage"]

        return current_status

    def _calculate_estimated_completion(self) -> Dict:
        """Calculate estimated completion time"""
        operations = self._get_service_operations()

        total_estimated_hours = sum(op.get("estimated_hours", 0) for op in operations)
        completed_hours = sum(
            op.get("estimated_hours", 0) for op in operations if op["status"] == "completed"
        )

        remaining_hours = total_estimated_hours - completed_hours

        # Estimate completion based on current progress rate
        if remaining_hours > 0:
            estimated_completion = nowdate()
            if remaining_hours <= 8:  # Same day
                estimated_completion = nowdate()
            elif remaining_hours <= 16:  # Next day
                estimated_completion = frappe.utils.add_days(nowdate(), 1)
            else:  # Multiple days
                estimated_completion = frappe.utils.add_days(nowdate(), int(remaining_hours / 8))
        else:
            estimated_completion = nowdate()

        return {
            "date": estimated_completion,
            "remaining_hours": remaining_hours,
            "total_hours": total_estimated_hours,
            "completion_percentage": (
                (completed_hours / total_estimated_hours * 100) if total_estimated_hours > 0 else 0
            ),
        }

    def _get_quality_checkpoints(self) -> List[Dict]:
        """Get quality control checkpoints"""
        # This would integrate with quality control system
        checkpoints = [
            {
                "checkpoint": "Initial Inspection",
                "checkpoint_ar": "الفحص الأولي",
                "status": "completed",
                "technician": "QC Inspector",
                "timestamp": nowdate(),
            },
            {
                "checkpoint": "Final Quality Check",
                "checkpoint_ar": "فحص الجودة النهائي",
                "status": "pending",
                "technician": "",
                "timestamp": "",
            },
        ]
        return checkpoints

    def _get_status_display(self, status: str) -> Dict:
        """Get display information for status"""
        status_map = {
            "not_started": {"en": "Not Started", "ar": "لم يبدأ"},
            "in_progress": {"en": "In Progress", "ar": "قيد التنفيذ"},
            "on_hold": {"en": "On Hold", "ar": "متوقف"},
            "completed": {"en": "Completed", "ar": "مكتمل"},
        }
        return status_map.get(status, {"en": status, "ar": status})

    def _get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {
            "not_started": "fa-clock-o",
            "in_progress": "fa-cog fa-spin",
            "on_hold": "fa-pause",
            "completed": "fa-check",
        }
        return icons.get(status, "fa-question")

    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors = {
            "not_started": "gray",
            "in_progress": "blue",
            "on_hold": "orange",
            "completed": "green",
        }
        return colors.get(status, "gray")

    def _update_overall_progress(self):
        """Update overall service order progress"""
        progress = self._calculate_overall_progress()

        # Update service order fields
        self.service_order.db_set("progress_percentage", progress["percentage"])
        self.service_order.db_set("progress_status", progress["status"])

        # Update delivery status if completed
        if progress["status"] == "completed":
            self.service_order.db_set("status", "To Deliver and Bill")

    def _send_progress_notification(self, operation_id: str, status: str, progress: float):
        """Send real-time progress notifications"""
        # This would integrate with notification system
        notification_data = {
            "service_order": self.service_order.name,
            "operation_id": operation_id,
            "status": status,
            "progress": progress,
            "customer": self.service_order.customer,
            "timestamp": get_datetime(),
        }

        # Publish real-time update
        frappe.publish_realtime("progress_update", notification_data, user=frappe.session.user)

    def _add_timeline_entry(self, operation_id: str, status: str, progress: float, notes: str):
        """Add entry to service order timeline"""
        timeline_entry = {
            "subject": _("Progress Update: {0}").format(operation_id),
            "content": notes,
            "communication_type": "Comment",
            "reference_doctype": "Sales Order",
            "reference_name": self.service_order.name,
        }

        frappe.get_doc(timeline_entry).insert(ignore_permissions=True)

    def _translate_to_arabic(self, text: str) -> str:
        """Simple Arabic translation helper"""
        # This would integrate with translation service
        translation_map = {
            "Operation started": "بدأت العملية",
            "Operation completed successfully": "تمت العملية بنجاح",
            "Operation on hold": "العملية متوقفة",
            "Progress updated": "تم تحديث التقدم",
        }
        return translation_map.get(text, text)


# WhiteListed API Methods
@frappe.whitelist()
def update_operation_progress(
    service_order,
    operation_id,
    status,
    progress_percentage=0,
    technician=None,
    notes="",
    time_spent=0,
):
    """Update progress for specific operation"""
    tracker = ServiceOrderProgressTracker(service_order)
    return tracker.update_progress(
        operation_id=operation_id,
        status=status,
        progress_percentage=progress_percentage,
        technician=technician,
        notes=notes,
        time_spent=time_spent,
    )


@frappe.whitelist()
def get_progress_dashboard(service_order):
    """Get progress dashboard for service order"""
    tracker = ServiceOrderProgressTracker(service_order)
    return tracker.get_progress_dashboard()


@frappe.whitelist()
def start_operation(service_order, operation_id, technician=None):
    """Start specific operation"""
    tracker = ServiceOrderProgressTracker(service_order)
    return tracker.start_operation(operation_id, technician)


@frappe.whitelist()
def complete_operation(service_order, operation_id, notes="", time_spent=0):
    """Complete specific operation"""
    tracker = ServiceOrderProgressTracker(service_order)
    return tracker.complete_operation(operation_id, notes, time_spent)


@frappe.whitelist()
def hold_operation(service_order, operation_id, reason=""):
    """Put operation on hold"""
    tracker = ServiceOrderProgressTracker(service_order)
    return tracker.hold_operation(operation_id, reason)


@frappe.whitelist()
def get_workshop_floor_status():
    """Get real-time workshop floor status for all active service orders"""
    try:
        active_orders = frappe.db.sql(
            """
            SELECT name, customer, creation, status
            FROM `tabSales Order`
            WHERE docstatus = 1
            AND status NOT IN ('Completed', 'Cancelled')
            AND service_estimate_reference IS NOT NULL
            ORDER BY creation DESC
        """,
            as_dict=True,
        )

        floor_status = []
        for order in active_orders:
            tracker = ServiceOrderProgressTracker(order.name)
            progress = tracker._calculate_overall_progress()

            floor_status.append(
                {
                    "service_order": order.name,
                    "customer": order.customer,
                    "status": progress["status"],
                    "progress_percentage": progress["percentage"],
                    "creation": order.creation,
                    "estimated_completion": tracker._calculate_estimated_completion(),
                }
            )

        return {"status": "success", "data": floor_status, "total_active_orders": len(floor_status)}

    except Exception as e:
        frappe.log_error(f"Workshop floor status error: {str(e)}")
        return {
            "status": "error",
            "message": _("Failed to get workshop floor status: {0}").format(str(e)),
        }
