# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Service Request Tracking
Handles real-time service tracking and progress monitoring
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime, time_diff_in_hours, add_to_date, getdate, flt
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from universal_workshop.customer_portal.auth import get_current_customer, require_customer_auth


@frappe.whitelist()
@require_customer_auth
def get_active_service_requests() -> Dict:
    """
    Get customer's active service requests with real-time status

    Returns:
        dict: Active service requests with tracking information
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Get active service appointments and work orders
        active_requests = []

        # Get scheduled and in-progress appointments
        appointments = frappe.get_list(
            "Service Appointment",
            filters={
                "customer": customer["customer_id"],
                "status": [
                    "in",
                    ["Scheduled", "In Progress", "Waiting for Parts", "Waiting for Approval"],
                ],
            },
            fields=[
                "name",
                "appointment_date",
                "appointment_time",
                "status",
                "service",
                "service_type",
                "vehicle",
                "workshop",
                "technician_assigned",
                "estimated_duration",
                "base_cost",
                "progress_percentage",
                "estimated_completion_time",
                "special_instructions",
                "creation",
                "modified",
            ],
            order_by="appointment_date asc",
        )

        for appointment in appointments:
            # Get detailed tracking information
            tracking_info = _get_appointment_tracking_details(appointment["name"])

            # Get vehicle information
            vehicle_info = _get_vehicle_basic_info(appointment["vehicle"])

            # Get service information
            service_info = _get_service_basic_info(appointment["service"])

            active_requests.append(
                {
                    "id": appointment["name"],
                    "type": "appointment",
                    "status": appointment["status"],
                    "service_name": service_info.get("service_name", ""),
                    "service_name_ar": service_info.get("service_name_ar", ""),
                    "service_type": appointment["service_type"],
                    "vehicle": vehicle_info,
                    "appointment_date": appointment["appointment_date"],
                    "appointment_time": appointment["appointment_time"],
                    "technician": appointment.get("technician_assigned", ""),
                    "workshop": appointment["workshop"],
                    "estimated_duration": appointment.get("estimated_duration", 0),
                    "progress_percentage": appointment.get("progress_percentage", 0),
                    "estimated_completion": appointment.get("estimated_completion_time"),
                    "tracking": tracking_info,
                    "created": appointment["creation"],
                    "last_updated": appointment["modified"],
                }
            )

        # Get active work orders (if any)
        work_orders = frappe.get_list(
            "Work Order",
            filters={
                "customer": customer["customer_id"],
                "status": ["in", ["Open", "In Process", "Completed"]],
            },
            fields=[
                "name",
                "transaction_date",
                "status",
                "item_name",
                "qty",
                "produced_qty",
                "planned_start_date",
                "planned_end_date",
                "actual_start_date",
                "actual_end_date",
            ],
            order_by="planned_start_date asc",
        )

        for work_order in work_orders:
            active_requests.append(
                {
                    "id": work_order["name"],
                    "type": "work_order",
                    "status": work_order["status"],
                    "item_name": work_order["item_name"],
                    "quantity": work_order["qty"],
                    "produced_quantity": work_order.get("produced_qty", 0),
                    "planned_start": work_order.get("planned_start_date"),
                    "planned_end": work_order.get("planned_end_date"),
                    "actual_start": work_order.get("actual_start_date"),
                    "actual_end": work_order.get("actual_end_date"),
                    "progress_percentage": _calculate_work_order_progress(work_order),
                    "created": work_order["transaction_date"],
                }
            )

        return {
            "success": True,
            "active_requests": active_requests,
            "total_active": len(active_requests),
        }

    except Exception as e:
        frappe.log_error(
            f"Error getting active service requests: {str(e)}", "Customer Portal Tracking"
        )
        return {"success": False, "message": _("Error retrieving active service requests")}


@frappe.whitelist()
@require_customer_auth
def get_service_request_details(request_id: str, request_type: str = "appointment") -> Dict:
    """
    Get detailed information about a specific service request

    Args:
        request_id: Service request ID
        request_type: Type of request ('appointment' or 'work_order')

    Returns:
        dict: Detailed service request information
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        if request_type == "appointment":
            return _get_appointment_details(request_id, customer["customer_id"])
        elif request_type == "work_order":
            return _get_work_order_details(request_id, customer["customer_id"])
        else:
            return {"success": False, "message": _("Invalid request type")}

    except Exception as e:
        frappe.log_error(
            f"Error getting service request details: {str(e)}", "Customer Portal Tracking"
        )
        return {"success": False, "message": _("Error retrieving service request details")}


@frappe.whitelist()
@require_customer_auth
def get_service_tracking_timeline(request_id: str) -> Dict:
    """
    Get service tracking timeline with status updates

    Args:
        request_id: Service request ID

    Returns:
        dict: Service tracking timeline
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Verify request ownership
        if not _verify_request_ownership(request_id, customer["customer_id"]):
            return {"success": False, "message": _("Access denied")}

        # Get timeline events from various sources
        timeline_events = []

        # Get appointment status updates
        status_updates = frappe.get_list(
            "Service Status Update",
            filters={"service_appointment": request_id},
            fields=[
                "status",
                "update_message",
                "update_message_ar",
                "estimated_completion",
                "progress_percentage",
                "technician",
                "creation",
                "owner",
            ],
            order_by="creation desc",
        )

        for update in status_updates:
            timeline_events.append(
                {
                    "type": "status_update",
                    "timestamp": update["creation"],
                    "status": update["status"],
                    "message": update.get("update_message", ""),
                    "message_ar": update.get("update_message_ar", ""),
                    "progress": update.get("progress_percentage", 0),
                    "estimated_completion": update.get("estimated_completion"),
                    "technician": update.get("technician", ""),
                    "updated_by": update["owner"],
                }
            )

        # Get communication history
        communications = frappe.get_list(
            "Communication History",
            filters={"reference_doctype": "Service Appointment", "reference_name": request_id},
            fields=[
                "communication_type",
                "content",
                "direction",
                "sent_at",
                "delivery_status",
                "creation",
            ],
            order_by="creation desc",
        )

        for comm in communications:
            timeline_events.append(
                {
                    "type": "communication",
                    "timestamp": comm["sent_at"] or comm["creation"],
                    "communication_type": comm["communication_type"],
                    "content": comm["content"],
                    "direction": comm["direction"],
                    "delivery_status": comm.get("delivery_status", ""),
                }
            )

        # Get parts usage updates
        parts_updates = frappe.get_list(
            "Parts Usage",
            filters={"service_appointment": request_id},
            fields=[
                "part_name",
                "quantity_used",
                "unit_cost",
                "total_cost",
                "approval_required",
                "approved_by_customer",
                "creation",
                "modified",
            ],
            order_by="creation desc",
        )

        for part in parts_updates:
            timeline_events.append(
                {
                    "type": "parts_update",
                    "timestamp": part["creation"],
                    "part_name": part["part_name"],
                    "quantity": part["quantity_used"],
                    "unit_cost": part["unit_cost"],
                    "total_cost": part["total_cost"],
                    "approval_required": part.get("approval_required", False),
                    "approved": part.get("approved_by_customer", False),
                }
            )

        # Sort timeline by timestamp (newest first)
        timeline_events.sort(key=lambda x: x["timestamp"], reverse=True)

        return {"success": True, "timeline": timeline_events, "total_events": len(timeline_events)}

    except Exception as e:
        frappe.log_error(
            f"Error getting service tracking timeline: {str(e)}", "Customer Portal Tracking"
        )
        return {"success": False, "message": _("Error retrieving service timeline")}


@frappe.whitelist()
@require_customer_auth
def approve_parts_usage(request_id: str, parts_usage_ids: List[str]) -> Dict:
    """
    Approve parts usage for service request

    Args:
        request_id: Service request ID
        parts_usage_ids: List of parts usage IDs to approve

    Returns:
        dict: Approval result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Verify request ownership
        if not _verify_request_ownership(request_id, customer["customer_id"]):
            return {"success": False, "message": _("Access denied")}

        approved_parts = []
        total_cost = 0

        for parts_id in parts_usage_ids:
            parts_usage = frappe.get_doc("Parts Usage", parts_id)

            # Verify parts belong to this request
            if parts_usage.service_appointment != request_id:
                continue

            # Approve parts usage
            parts_usage.approved_by_customer = True
            parts_usage.customer_approval_date = now_datetime()
            parts_usage.approved_by = customer["customer_id"]
            parts_usage.save(ignore_permissions=True)

            approved_parts.append(
                {
                    "part_name": parts_usage.part_name,
                    "quantity": parts_usage.quantity_used,
                    "total_cost": parts_usage.total_cost,
                }
            )
            total_cost += parts_usage.total_cost

        # Update service appointment status if needed
        appointment = frappe.get_doc("Service Appointment", request_id)
        if appointment.status == "Waiting for Approval":
            appointment.status = "In Progress"
            appointment.save(ignore_permissions=True)

            # Send notification about approval
            _send_parts_approval_notification(appointment, approved_parts, total_cost)

        # Log approval
        frappe.get_doc(
            {
                "doctype": "Communication History",
                "reference_doctype": "Service Appointment",
                "reference_name": request_id,
                "communication_type": "Parts Approval",
                "content": f"Customer approved {len(approved_parts)} parts with total cost {total_cost} OMR",
                "direction": "Incoming",
                "sent_at": now_datetime(),
            }
        ).insert(ignore_permissions=True)

        return {
            "success": True,
            "message": _("Parts usage approved successfully"),
            "approved_parts": approved_parts,
            "total_cost": total_cost,
        }

    except Exception as e:
        frappe.log_error(f"Error approving parts usage: {str(e)}", "Customer Portal Tracking")
        return {"success": False, "message": _("Error approving parts usage")}


@frappe.whitelist()
@require_customer_auth
def submit_service_feedback(request_id: str, feedback_data: Dict) -> Dict:
    """
    Submit feedback for completed service

    Args:
        request_id: Service request ID
        feedback_data: Feedback information

    Returns:
        dict: Feedback submission result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Verify request ownership and completion
        appointment = frappe.get_doc("Service Appointment", request_id)
        if appointment.customer != customer["customer_id"]:
            return {"success": False, "message": _("Access denied")}

        if appointment.status != "Completed":
            return {
                "success": False,
                "message": _("Feedback can only be submitted for completed services"),
            }

        # Check if feedback already exists
        existing_feedback = frappe.db.exists(
            "Service Feedback",
            {"service_appointment": request_id, "customer": customer["customer_id"]},
        )

        if existing_feedback:
            return {
                "success": False,
                "message": _("Feedback has already been submitted for this service"),
            }

        # Create service feedback
        feedback = frappe.new_doc("Service Feedback")
        feedback.service_appointment = request_id
        feedback.customer = customer["customer_id"]
        feedback.vehicle = appointment.vehicle
        feedback.workshop = appointment.workshop
        feedback.technician = appointment.technician_assigned

        # Set feedback fields
        feedback.overall_rating = feedback_data.get("overall_rating", 5)
        feedback.service_quality_rating = feedback_data.get("service_quality_rating", 5)
        feedback.technician_rating = feedback_data.get("technician_rating", 5)
        feedback.timeliness_rating = feedback_data.get("timeliness_rating", 5)
        feedback.value_for_money_rating = feedback_data.get("value_for_money_rating", 5)

        feedback.feedback_comments = feedback_data.get("comments", "")
        feedback.feedback_comments_ar = feedback_data.get("comments_ar", "")

        feedback.would_recommend = feedback_data.get("would_recommend", True)
        feedback.would_return = feedback_data.get("would_return", True)

        feedback.feedback_date = now_datetime()
        feedback.insert(ignore_permissions=True)

        # Update appointment with feedback reference
        appointment.feedback_submitted = True
        appointment.feedback_id = feedback.name
        appointment.save(ignore_permissions=True)

        # Log feedback submission
        frappe.get_doc(
            {
                "doctype": "Communication History",
                "reference_doctype": "Service Appointment",
                "reference_name": request_id,
                "communication_type": "Feedback Submission",
                "content": f"Customer submitted feedback with overall rating: {feedback.overall_rating}/5",
                "direction": "Incoming",
                "sent_at": now_datetime(),
            }
        ).insert(ignore_permissions=True)

        # Send thank you notification
        _send_feedback_thank_you(appointment, feedback)

        return {
            "success": True,
            "message": _("Feedback submitted successfully"),
            "feedback_id": feedback.name,
        }

    except Exception as e:
        frappe.log_error(f"Error submitting service feedback: {str(e)}", "Customer Portal Tracking")
        return {"success": False, "message": _("Error submitting feedback")}


@frappe.whitelist()
@require_customer_auth
def get_service_history_with_feedback() -> Dict:
    """
    Get customer's service history with feedback status

    Returns:
        dict: Service history with feedback information
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Get completed services
        completed_services = frappe.get_list(
            "Service Appointment",
            filters={"customer": customer["customer_id"], "status": "Completed"},
            fields=[
                "name",
                "appointment_date",
                "completion_date",
                "service",
                "service_type",
                "vehicle",
                "workshop",
                "technician_assigned",
                "total_cost",
                "feedback_submitted",
                "feedback_id",
                "creation",
            ],
            order_by="completion_date desc",
        )

        service_history = []
        for service in completed_services:
            # Get vehicle info
            vehicle_info = _get_vehicle_basic_info(service["vehicle"])

            # Get service info
            service_info = _get_service_basic_info(service["service"])

            # Get feedback info if exists
            feedback_info = None
            if service["feedback_submitted"] and service["feedback_id"]:
                feedback_info = _get_feedback_summary(service["feedback_id"])

            service_history.append(
                {
                    "appointment_id": service["name"],
                    "service_date": service["appointment_date"],
                    "completion_date": service["completion_date"],
                    "service_name": service_info.get("service_name", ""),
                    "service_name_ar": service_info.get("service_name_ar", ""),
                    "service_type": service["service_type"],
                    "vehicle": vehicle_info,
                    "workshop": service["workshop"],
                    "technician": service.get("technician_assigned", ""),
                    "total_cost": service.get("total_cost", 0),
                    "feedback_submitted": service.get("feedback_submitted", False),
                    "feedback": feedback_info,
                    "can_submit_feedback": not service.get("feedback_submitted", False),
                }
            )

        return {
            "success": True,
            "service_history": service_history,
            "total_services": len(service_history),
        }

    except Exception as e:
        frappe.log_error(f"Error getting service history: {str(e)}", "Customer Portal Tracking")
        return {"success": False, "message": _("Error retrieving service history")}


# Helper functions


def _get_appointment_tracking_details(appointment_id: str) -> Dict:
    """Get detailed tracking information for appointment"""
    try:
        # Get latest status update
        latest_update = frappe.get_list(
            "Service Status Update",
            filters={"service_appointment": appointment_id},
            fields=[
                "status",
                "update_message",
                "progress_percentage",
                "estimated_completion",
                "creation",
            ],
            order_by="creation desc",
            limit=1,
        )

        if latest_update:
            update = latest_update[0]
            return {
                "last_update": update["creation"],
                "current_status": update["status"],
                "progress_message": update.get("update_message", ""),
                "progress_percentage": update.get("progress_percentage", 0),
                "estimated_completion": update.get("estimated_completion"),
            }

        return {}

    except Exception:
        return {}


def _get_vehicle_basic_info(vehicle_id: str) -> Dict:
    """Get basic vehicle information"""
    try:
        vehicle = frappe.get_doc("Vehicle Profile", vehicle_id)
        return {
            "id": vehicle.name,
            "license_plate": vehicle.license_plate,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
        }
    except Exception:
        return {}


def _get_service_basic_info(service_id: str) -> Dict:
    """Get basic service information"""
    try:
        service = frappe.get_doc("Workshop Service", service_id)
        return {
            "id": service.name,
            "service_name": service.service_name,
            "service_name_ar": service.get("service_name_ar", ""),
            "service_type": service.service_type,
            "estimated_duration": service.estimated_duration,
        }
    except Exception:
        return {}


def _calculate_work_order_progress(work_order: Dict) -> float:
    """Calculate work order progress percentage"""
    try:
        qty = flt(work_order.get("qty", 0))
        produced_qty = flt(work_order.get("produced_qty", 0))

        if qty > 0:
            return (produced_qty / qty) * 100
        return 0
    except Exception:
        return 0


def _get_appointment_details(appointment_id: str, customer_id: str) -> Dict:
    """Get detailed appointment information"""
    try:
        appointment = frappe.get_doc("Service Appointment", appointment_id)

        # Verify ownership
        if appointment.customer != customer_id:
            return {"success": False, "message": _("Access denied")}

        # Get comprehensive details
        vehicle_info = _get_vehicle_basic_info(appointment.vehicle)
        service_info = _get_service_basic_info(appointment.service)
        tracking_info = _get_appointment_tracking_details(appointment_id)

        # Get parts information
        parts_usage = frappe.get_list(
            "Parts Usage",
            filters={"service_appointment": appointment_id},
            fields=[
                "part_name",
                "quantity_used",
                "unit_cost",
                "total_cost",
                "approval_required",
                "approved_by_customer",
            ],
        )

        return {
            "success": True,
            "appointment": {
                "id": appointment.name,
                "status": appointment.status,
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.appointment_time,
                "completion_date": appointment.get("completion_date"),
                "service": service_info,
                "vehicle": vehicle_info,
                "workshop": appointment.workshop,
                "technician": appointment.get("technician_assigned", ""),
                "estimated_duration": appointment.get("estimated_duration", 0),
                "base_cost": appointment.get("base_cost", 0),
                "total_cost": appointment.get("total_cost", 0),
                "special_instructions": appointment.get("special_instructions", ""),
                "tracking": tracking_info,
                "parts_usage": parts_usage,
                "created": appointment.creation,
                "last_updated": appointment.modified,
            },
        }

    except Exception as e:
        frappe.log_error(f"Error getting appointment details: {str(e)}", "Customer Portal Tracking")
        return {"success": False, "message": _("Error retrieving appointment details")}


def _get_work_order_details(work_order_id: str, customer_id: str) -> Dict:
    """Get detailed work order information"""
    try:
        work_order = frappe.get_doc("Work Order", work_order_id)

        # Verify ownership
        if work_order.customer != customer_id:
            return {"success": False, "message": _("Access denied")}

        return {
            "success": True,
            "work_order": {
                "id": work_order.name,
                "status": work_order.status,
                "item_name": work_order.item_name,
                "quantity": work_order.qty,
                "produced_quantity": work_order.get("produced_qty", 0),
                "planned_start": work_order.get("planned_start_date"),
                "planned_end": work_order.get("planned_end_date"),
                "actual_start": work_order.get("actual_start_date"),
                "actual_end": work_order.get("actual_end_date"),
                "progress_percentage": _calculate_work_order_progress(work_order),
                "created": work_order.transaction_date,
            },
        }

    except Exception as e:
        frappe.log_error(f"Error getting work order details: {str(e)}", "Customer Portal Tracking")
        return {"success": False, "message": _("Error retrieving work order details")}


def _verify_request_ownership(request_id: str, customer_id: str) -> bool:
    """Verify that the service request belongs to the customer"""
    try:
        # Check in Service Appointment
        appointment = frappe.db.get_value("Service Appointment", request_id, "customer")
        if appointment == customer_id:
            return True

        # Check in Work Order
        work_order = frappe.db.get_value("Work Order", request_id, "customer")
        if work_order == customer_id:
            return True

        return False

    except Exception:
        return False


def _get_feedback_summary(feedback_id: str) -> Dict:
    """Get feedback summary information"""
    try:
        feedback = frappe.get_doc("Service Feedback", feedback_id)
        return {
            "overall_rating": feedback.overall_rating,
            "service_quality_rating": feedback.service_quality_rating,
            "technician_rating": feedback.technician_rating,
            "timeliness_rating": feedback.timeliness_rating,
            "value_rating": feedback.value_for_money_rating,
            "comments": feedback.get("feedback_comments", ""),
            "would_recommend": feedback.get("would_recommend", False),
            "feedback_date": feedback.feedback_date,
        }
    except Exception:
        return {}


def _send_parts_approval_notification(appointment, approved_parts, total_cost):
    """Send parts approval notification"""
    try:
        # Send parts approval confirmation via customer portal communication integration
        from universal_workshop.customer_portal.communication_integration import (
            send_parts_approval_request,
        )

        # Create parts usage record for notification
        parts_usage = frappe.new_doc("Parts Usage")
        parts_usage.service_appointment = appointment.name
        parts_usage.customer = appointment.customer
        parts_usage.total_cost = total_cost
        parts_usage.items = approved_parts
        parts_usage.save()

        result = send_parts_approval_request(parts_usage.name)
        if result.get("error"):
            frappe.log_error(f"Parts approval notification failed: {result['error']}", "Customer Portal Tracking")
        else:
            frappe.logger().info(f"Parts approval notification sent for {appointment.name}: {len(result.get('notifications_sent', []))} notifications")
            
    except Exception as e:
        frappe.log_error(
            f"Error sending parts approval notification: {str(e)}", "Customer Portal Tracking"
        )


def _send_feedback_thank_you(appointment, feedback):
    """Send feedback thank you notification"""
    try:
        # Send feedback completion notification via customer portal communication integration
            send_feedback_request,
        )

        # Send feedback request notification (which includes thank you for completed feedback)
        result = send_feedback_request(appointment.name)
        if result.get("error"):
            frappe.log_error(f"Feedback thank you notification failed: {result['error']}", "Customer Portal Tracking")
        else:
            frappe.logger().info(f"Feedback thank you sent for {appointment.name}: {len(result.get('notifications_sent', []))} notifications")
            
    except Exception as e:
        frappe.log_error(f"Error sending feedback thank you: {str(e)}", "Customer Portal Tracking")


def _send_service_status_update_notification(appointment_id: str, new_status: str):
    """Send service status update notification to customer"""
    try:
        # Find related work order
        work_orders = frappe.get_list("Work Order", 
                                    filters={"service_appointment": appointment_id},
                                    limit=1)
        
        if work_orders:
                send_service_status_update,
            )
            
            result = send_service_status_update(work_orders[0].name, new_status)
            if result.get("error"):
                frappe.log_error(f"Status update notification failed: {result['error']}", "Customer Portal Tracking")
            else:
                frappe.logger().info(f"Status update notification sent for {appointment_id}: {len(result.get('notifications_sent', []))} notifications")
                
    except Exception as e:
        frappe.log_error(f"Error sending status update notification: {str(e)}", "Customer Portal Tracking")
