# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Appointment Booking Management
Handles real-time appointment booking with availability checking
"""

import frappe
from frappe import _
from frappe.utils import (
    get_datetime,
    add_to_date,
    get_weekday,
    getdate,
    time_diff_in_hours,
    now_datetime,
)
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional
from universal_workshop.customer_portal.auth import get_current_customer, require_customer_auth


@frappe.whitelist()
@require_customer_auth
def get_available_services() -> Dict:
    """
    Get list of available services for booking

    Returns:
        dict: Available services with pricing
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Get active workshop services
        services = frappe.get_list(
            "Workshop Service",
            filters={"is_active": 1, "is_bookable": 1},
            fields=[
                "name",
                "service_name",
                "service_name_ar",
                "service_type",
                "service_category",
                "estimated_duration",
                "base_price",
                "description",
                "description_ar",
                "requires_vehicle_inspection",
            ],
            order_by="service_category, service_name",
        )

        # Group services by category
        grouped_services = {}
        for service in services:
            category = service.get("service_category", "General")
            if category not in grouped_services:
                grouped_services[category] = []
            grouped_services[category].append(service)

        return {
            "success": True,
            "services": services,
            "grouped_services": grouped_services,
            "total_services": len(services),
        }

    except Exception as e:
        frappe.log_error(f"Error getting available services: {str(e)}", "Customer Portal Booking")
        return {"success": False, "message": _("Error retrieving available services")}


@frappe.whitelist()
@require_customer_auth
def get_available_time_slots(
    appointment_date: str, service_id: str, workshop_id: str = None
) -> Dict:
    """
    Get available time slots for a specific date and service

    Args:
        appointment_date: Date in YYYY-MM-DD format
        service_id: Workshop Service ID
        workshop_id: Optional workshop ID (defaults to customer's preferred workshop)

    Returns:
        dict: Available time slots
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Validate appointment date
        appointment_date_obj = getdate(appointment_date)
        today = getdate()

        if appointment_date_obj < today:
            return {"success": False, "message": _("Cannot book appointments for past dates")}

        # Check if date is too far in the future (e.g., 3 months)
        max_date = add_to_date(today, months=3)
        if appointment_date_obj > max_date:
            return {
                "success": False,
                "message": _("Cannot book appointments more than 3 months in advance"),
            }

        # Get service details
        service = frappe.get_doc("Workshop Service", service_id)
        service_duration = service.estimated_duration or 60  # minutes

        # Get workshop information
        if not workshop_id:
            workshop_id = _get_customer_preferred_workshop(customer["customer_id"])

        workshop = frappe.get_doc("Workshop Profile", workshop_id) if workshop_id else None

        # Get workshop working hours
        working_hours = _get_workshop_working_hours(workshop_id, appointment_date_obj)
        if not working_hours:
            return {"success": False, "message": _("Workshop is not available on this date")}

        # Get existing appointments for the date
        existing_appointments = _get_existing_appointments(workshop_id, appointment_date)

        # Get available technicians
        available_technicians = _get_available_technicians(
            workshop_id, appointment_date, service.service_type
        )

        # Generate time slots
        time_slots = _generate_time_slots(
            working_hours, service_duration, existing_appointments, available_technicians
        )

        return {
            "success": True,
            "time_slots": time_slots,
            "service_duration": service_duration,
            "workshop_name": workshop.workshop_name if workshop else "",
            "date": appointment_date,
        }

    except Exception as e:
        frappe.log_error(f"Error getting available time slots: {str(e)}", "Customer Portal Booking")
        return {"success": False, "message": _("Error retrieving available time slots")}


@frappe.whitelist()
@require_customer_auth
def create_appointment_booking(booking_data: Dict) -> Dict:
    """
    Create new appointment booking

    Args:
        booking_data: Booking information dictionary

    Returns:
        dict: Booking creation result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Validate required fields
        required_fields = ["appointment_date", "appointment_time", "service_id", "vehicle_id"]
        for field in required_fields:
            if not booking_data.get(field):
                return {
                    "success": False,
                    "message": _("Missing required field: {0}").format(
                        _(field.replace("_", " ").title())
                    ),
                }

        # Verify vehicle ownership
        vehicle_doc = frappe.get_doc("Vehicle Profile", booking_data["vehicle_id"])
        if vehicle_doc.customer != customer["customer_id"]:
            return {"success": False, "message": _("Access denied")}

        # Get service details
        service = frappe.get_doc("Workshop Service", booking_data["service_id"])

        # Check time slot availability
        slot_check = _check_time_slot_availability(
            booking_data["appointment_date"],
            booking_data["appointment_time"],
            service.estimated_duration or 60,
            booking_data.get("workshop_id"),
        )

        if not slot_check["available"]:
            return {"success": False, "message": _("Selected time slot is no longer available")}

        # Create service appointment
        appointment = frappe.new_doc("Service Appointment")
        appointment.customer = customer["customer_id"]
        appointment.vehicle = booking_data["vehicle_id"]
        appointment.service = booking_data["service_id"]
        appointment.service_type = service.service_type
        appointment.appointment_date = booking_data["appointment_date"]
        appointment.appointment_time = booking_data["appointment_time"]
        appointment.estimated_duration = service.estimated_duration or 60
        appointment.base_cost = service.base_price or 0
        appointment.workshop = booking_data.get("workshop_id") or _get_customer_preferred_workshop(
            customer["customer_id"]
        )
        appointment.status = "Scheduled"
        appointment.booking_source = "Customer Portal"

        # Set additional fields if provided
        if booking_data.get("special_instructions"):
            appointment.special_instructions = booking_data["special_instructions"]

        if booking_data.get("preferred_technician"):
            appointment.preferred_technician = booking_data["preferred_technician"]

        # Auto-assign technician if possible
        technician = _auto_assign_technician(
            appointment.workshop,
            appointment.appointment_date,
            appointment.appointment_time,
            service.service_type,
        )
        if technician:
            appointment.technician_assigned = technician

        appointment.insert(ignore_permissions=True)

        # Send confirmation notifications
        _send_booking_confirmation(appointment)

        # Log booking creation
        frappe.get_doc(
            {
                "doctype": "Communication History",
                "reference_doctype": "Service Appointment",
                "reference_name": appointment.name,
                "communication_type": "Booking Confirmation",
                "content": f"Appointment booked: {service.service_name} on {appointment.appointment_date} at {appointment.appointment_time}",
                "direction": "Outgoing",
                "sent_at": now_datetime(),
            }
        ).insert(ignore_permissions=True)

        return {
            "success": True,
            "message": _("Appointment booked successfully"),
            "appointment_id": appointment.name,
            "confirmation_details": {
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.appointment_time,
                "service_name": service.service_name,
                "estimated_duration": appointment.estimated_duration,
                "workshop_name": frappe.db.get_value(
                    "Workshop Profile", appointment.workshop, "workshop_name"
                ),
                "technician": appointment.technician_assigned or _("To be assigned"),
            },
        }

    except Exception as e:
        frappe.log_error(f"Error creating appointment booking: {str(e)}", "Customer Portal Booking")
        return {"success": False, "message": _("Error creating appointment booking")}


@frappe.whitelist()
@require_customer_auth
def cancel_appointment_booking(appointment_id: str, reason: str = "") -> Dict:
    """
    Cancel existing appointment booking

    Args:
        appointment_id: Service Appointment ID
        reason: Cancellation reason

    Returns:
        dict: Cancellation result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Verify appointment ownership
        appointment = frappe.get_doc("Service Appointment", appointment_id)
        if appointment.customer != customer["customer_id"]:
            return {"success": False, "message": _("Access denied")}

        # Check if appointment can be cancelled
        if appointment.status in ["Completed", "Cancelled"]:
            return {
                "success": False,
                "message": _("Cannot cancel appointment with status: {0}").format(
                    appointment.status
                ),
            }

        # Check cancellation policy (e.g., minimum 24 hours notice)
        appointment_datetime = get_datetime(
            f"{appointment.appointment_date} {appointment.appointment_time}"
        )
        hours_until_appointment = time_diff_in_hours(appointment_datetime, now_datetime())

        if hours_until_appointment < 24:
            return {
                "success": False,
                "message": _("Appointments must be cancelled at least 24 hours in advance"),
            }

        # Update appointment status
        appointment.status = "Cancelled"
        appointment.cancellation_reason = reason or "Cancelled by customer"
        appointment.cancelled_by = customer["customer_id"]
        appointment.cancellation_date = now_datetime()
        appointment.save(ignore_permissions=True)

        # Send cancellation notifications
        _send_cancellation_notification(appointment)

        # Log cancellation
        frappe.get_doc(
            {
                "doctype": "Communication History",
                "reference_doctype": "Service Appointment",
                "reference_name": appointment.name,
                "communication_type": "Booking Cancellation",
                "content": f"Appointment cancelled: {appointment.service_type} on {appointment.appointment_date}. Reason: {reason}",
                "direction": "Outgoing",
                "sent_at": now_datetime(),
            }
        ).insert(ignore_permissions=True)

        return {"success": True, "message": _("Appointment cancelled successfully")}

    except Exception as e:
        frappe.log_error(f"Error cancelling appointment: {str(e)}", "Customer Portal Booking")
        return {"success": False, "message": _("Error cancelling appointment")}


@frappe.whitelist()
@require_customer_auth
def reschedule_appointment_booking(appointment_id: str, new_date: str, new_time: str) -> Dict:
    """
    Reschedule existing appointment booking

    Args:
        appointment_id: Service Appointment ID
        new_date: New appointment date
        new_time: New appointment time

    Returns:
        dict: Reschedule result
    """
    try:
        customer = get_current_customer()
        if not customer:
            return {"success": False, "message": _("Authentication required")}

        # Verify appointment ownership
        appointment = frappe.get_doc("Service Appointment", appointment_id)
        if appointment.customer != customer["customer_id"]:
            return {"success": False, "message": _("Access denied")}

        # Check if appointment can be rescheduled
        if appointment.status in ["Completed", "Cancelled", "In Progress"]:
            return {
                "success": False,
                "message": _("Cannot reschedule appointment with status: {0}").format(
                    appointment.status
                ),
            }

        # Check new time slot availability
        slot_check = _check_time_slot_availability(
            new_date,
            new_time,
            appointment.estimated_duration or 60,
            appointment.workshop,
            exclude_appointment_id=appointment_id,
        )

        if not slot_check["available"]:
            return {"success": False, "message": _("Selected time slot is not available")}

        # Store old appointment details
        old_date = appointment.appointment_date
        old_time = appointment.appointment_time

        # Update appointment
        appointment.appointment_date = new_date
        appointment.appointment_time = new_time
        appointment.last_modified_by = customer["customer_id"]
        appointment.save(ignore_permissions=True)

        # Send reschedule notifications
        _send_reschedule_notification(appointment, old_date, old_time)

        # Log reschedule
        frappe.get_doc(
            {
                "doctype": "Communication History",
                "reference_doctype": "Service Appointment",
                "reference_name": appointment.name,
                "communication_type": "Booking Reschedule",
                "content": f"Appointment rescheduled from {old_date} {old_time} to {new_date} {new_time}",
                "direction": "Outgoing",
                "sent_at": now_datetime(),
            }
        ).insert(ignore_permissions=True)

        return {
            "success": True,
            "message": _("Appointment rescheduled successfully"),
            "new_appointment_details": {
                "appointment_date": new_date,
                "appointment_time": new_time,
                "service_name": frappe.db.get_value(
                    "Workshop Service", appointment.service, "service_name"
                ),
            },
        }

    except Exception as e:
        frappe.log_error(f"Error rescheduling appointment: {str(e)}", "Customer Portal Booking")
        return {"success": False, "message": _("Error rescheduling appointment")}


# Helper functions


def _get_customer_preferred_workshop(customer_id: str) -> Optional[str]:
    """Get customer's preferred workshop"""
    try:
        customer = frappe.get_doc("Customer", customer_id)
        return customer.get("preferred_workshop") or frappe.db.get_value(
            "Workshop Profile", {"is_default": 1}, "name"
        )
    except Exception:
        return frappe.db.get_value("Workshop Profile", {"is_default": 1}, "name")


def _get_workshop_working_hours(workshop_id: str, date_obj: datetime) -> Optional[Dict]:
    """Get workshop working hours for a specific date"""
    try:
        if not workshop_id:
            return None

        workshop = frappe.get_doc("Workshop Profile", workshop_id)
        weekday = get_weekday(date_obj)

        # Check if workshop is open on this weekday
        weekday_map = {
            "Monday": "monday",
            "Tuesday": "tuesday",
            "Wednesday": "wednesday",
            "Thursday": "thursday",
            "Friday": "friday",
            "Saturday": "saturday",
            "Sunday": "sunday",
        }

        weekday_field = weekday_map.get(weekday)
        if not weekday_field or not workshop.get(f"open_{weekday_field}"):
            return None

        # Get working hours
        start_time = workshop.get(f"{weekday_field}_start_time") or time(8, 0)  # Default 8:00 AM
        end_time = workshop.get(f"{weekday_field}_end_time") or time(17, 0)  # Default 5:00 PM

        return {
            "start_time": start_time,
            "end_time": end_time,
            "lunch_break_start": workshop.get("lunch_break_start") or time(12, 0),
            "lunch_break_end": workshop.get("lunch_break_end") or time(13, 0),
        }

    except Exception:
        # Default working hours if workshop not found
        return {
            "start_time": time(8, 0),
            "end_time": time(17, 0),
            "lunch_break_start": time(12, 0),
            "lunch_break_end": time(13, 0),
        }


def _get_existing_appointments(workshop_id: str, appointment_date: str) -> List[Dict]:
    """Get existing appointments for a workshop on a specific date"""
    try:
        appointments = frappe.get_list(
            "Service Appointment",
            filters={
                "workshop": workshop_id,
                "appointment_date": appointment_date,
                "status": ["not in", ["Cancelled", "Completed"]],
            },
            fields=["appointment_time", "estimated_duration", "technician_assigned"],
            order_by="appointment_time",
        )

        return appointments

    except Exception:
        return []


def _get_available_technicians(
    workshop_id: str, appointment_date: str, service_type: str
) -> List[str]:
    """Get available technicians for a specific date and service type"""
    try:
        # Get technicians qualified for this service type
        technicians = frappe.get_list(
            "Technician",
            filters={
                "workshop": workshop_id,
                "employment_status": "Active",
                "specialization": ["like", f"%{service_type}%"],
            },
            fields=["name", "employee_id", "technician_name"],
        )

        # Check technician availability (simple check - can be enhanced)
        available_technicians = []
        for tech in technicians:
            # Check if technician has conflicting appointments
            conflicts = frappe.db.count(
                "Service Appointment",
                {
                    "technician_assigned": tech.name,
                    "appointment_date": appointment_date,
                    "status": ["not in", ["Cancelled", "Completed"]],
                },
            )

            if conflicts < 8:  # Assuming max 8 appointments per day
                available_technicians.append(tech.name)

        return available_technicians

    except Exception:
        return []


def _generate_time_slots(
    working_hours: Dict,
    service_duration: int,
    existing_appointments: List,
    available_technicians: List,
) -> List[Dict]:
    """Generate available time slots"""
    slots = []

    start_time = working_hours["start_time"]
    end_time = working_hours["end_time"]
    lunch_start = working_hours["lunch_break_start"]
    lunch_end = working_hours["lunch_break_end"]

    # Convert to minutes for easier calculation
    current_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    lunch_start_minutes = lunch_start.hour * 60 + lunch_start.minute
    lunch_end_minutes = lunch_end.hour * 60 + lunch_end.minute

    slot_duration = 30  # 30-minute slots

    while current_minutes + service_duration <= end_minutes:
        # Skip lunch break
        if current_minutes >= lunch_start_minutes and current_minutes < lunch_end_minutes:
            current_minutes = lunch_end_minutes
            continue

        # Check if slot conflicts with existing appointments
        slot_time = f"{current_minutes // 60:02d}:{current_minutes % 60:02d}"

        if not _has_appointment_conflict(slot_time, service_duration, existing_appointments):
            # Calculate available technicians for this slot
            slot_technicians = _get_slot_available_technicians(
                slot_time, service_duration, existing_appointments, available_technicians
            )

            if slot_technicians:
                slots.append(
                    {
                        "time": slot_time,
                        "display_time": _format_time_display(slot_time),
                        "available_technicians": len(slot_technicians),
                        "is_available": True,
                    }
                )

        current_minutes += slot_duration

    return slots


def _check_time_slot_availability(
    appointment_date: str,
    appointment_time: str,
    duration: int,
    workshop_id: str = None,
    exclude_appointment_id: str = None,
) -> Dict:
    """Check if a specific time slot is available"""
    try:
        # Get existing appointments
        filters = {
            "workshop": workshop_id,
            "appointment_date": appointment_date,
            "status": ["not in", ["Cancelled", "Completed"]],
        }

        if exclude_appointment_id:
            filters["name"] = ["!=", exclude_appointment_id]

        existing_appointments = frappe.get_list(
            "Service Appointment",
            filters=filters,
            fields=["appointment_time", "estimated_duration"],
        )

        # Check for conflicts
        conflicts = _has_appointment_conflict(appointment_time, duration, existing_appointments)

        return {"available": not conflicts, "conflicts": conflicts}

    except Exception:
        return {"available": False, "conflicts": True}


def _has_appointment_conflict(slot_time: str, duration: int, existing_appointments: List) -> bool:
    """Check if a time slot conflicts with existing appointments"""
    try:
        slot_start = datetime.strptime(slot_time, "%H:%M").time()
        slot_start_minutes = slot_start.hour * 60 + slot_start.minute
        slot_end_minutes = slot_start_minutes + duration

        for appointment in existing_appointments:
            app_time = datetime.strptime(str(appointment.appointment_time), "%H:%M:%S").time()
            app_start_minutes = app_time.hour * 60 + app_time.minute
            app_end_minutes = app_start_minutes + (appointment.estimated_duration or 60)

            # Check for overlap
            if slot_start_minutes < app_end_minutes and slot_end_minutes > app_start_minutes:
                return True

        return False

    except Exception:
        return True


def _get_slot_available_technicians(
    slot_time: str, duration: int, existing_appointments: List, all_technicians: List
) -> List[str]:
    """Get technicians available for a specific time slot"""
    available = []

    for tech in all_technicians:
        # Check if technician is busy during this slot
        tech_busy = False
        for appointment in existing_appointments:
            if appointment.get("technician_assigned") == tech:
                if _has_appointment_conflict(slot_time, duration, [appointment]):
                    tech_busy = True
                    break

        if not tech_busy:
            available.append(tech)

    return available


def _auto_assign_technician(
    workshop_id: str, appointment_date: str, appointment_time: str, service_type: str
) -> Optional[str]:
    """Auto-assign best available technician"""
    try:
        available_technicians = _get_available_technicians(
            workshop_id, appointment_date, service_type
        )
        if available_technicians:
            # Simple assignment: first available technician
            # Can be enhanced with workload balancing, skill matching, etc.
            return available_technicians[0]
    except Exception:
        pass
    return None


def _format_time_display(time_str: str) -> str:
    """Format time for display"""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return time_obj.strftime("%I:%M %p")
    except Exception:
        return time_str


def _send_booking_confirmation(appointment):
    """Send booking confirmation notifications"""
    try:
        # Use customer portal communication integration
        from universal_workshop.customer_portal.communication_integration import (
            send_booking_confirmation,
        )

        result = send_booking_confirmation(appointment.name)
        if result.get("error"):
            frappe.log_error(
                f"Booking confirmation failed: {result['error']}", "Customer Portal Booking"
            )
        else:
            frappe.logger().info(
                f"Booking confirmation sent for {appointment.name}: {len(result.get('notifications_sent', []))} notifications"
            )

    except Exception as e:
        frappe.log_error(f"Error sending booking confirmation: {str(e)}", "Customer Portal Booking")


def _send_cancellation_notification(appointment, reason=""):
    """Send cancellation notification"""
    try:
        # Use customer portal communication integration
        from universal_workshop.customer_portal.communication_integration import (
            send_cancellation_notice,
        )

        result = send_cancellation_notice(appointment.name, reason)
        if result.get("error"):
            frappe.log_error(
                f"Cancellation notice failed: {result['error']}", "Customer Portal Booking"
            )
        else:
            frappe.logger().info(
                f"Cancellation notice sent for {appointment.name}: {len(result.get('notifications_sent', []))} notifications"
            )

    except Exception as e:
        frappe.log_error(
            f"Error sending cancellation notification: {str(e)}", "Customer Portal Booking"
        )


def _send_reschedule_notification(appointment, old_date, old_time):
    """Send reschedule notification"""
    try:
        # Use customer portal communication integration
        from universal_workshop.customer_portal.communication_integration import (
            send_reschedule_notice,
        )

        result = send_reschedule_notice(appointment.name, old_date, old_time)
        if result.get("error"):
            frappe.log_error(
                f"Reschedule notice failed: {result['error']}", "Customer Portal Booking"
            )
        else:
            frappe.logger().info(
                f"Reschedule notice sent for {appointment.name}: {len(result.get('notifications_sent', []))} notifications"
            )

    except Exception as e:
        frappe.log_error(
            f"Error sending reschedule notification: {str(e)}", "Customer Portal Booking"
        )
