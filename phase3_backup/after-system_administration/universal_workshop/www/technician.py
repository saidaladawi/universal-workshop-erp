import frappe
from frappe import _
from frappe.utils import cint, flt, get_url


def get_context(context):
    """Context for technician mobile interface"""

    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/technician"
        raise frappe.Redirect

    # Verify user has technician role
    if not has_technician_role():
        frappe.throw(_("Access denied. Technician role required."))

    # Get current user data
    context.user = get_current_user()

    # Get user's assigned jobs
    context.jobs = get_technician_jobs()

    # Get app configuration
    context.app_config = get_app_config()

    # Set page metadata
    context.title = _("Technician Portal - بوابة الفنيين")
    context.description = _("Mobile interface for technician workflow management")

    return context


def has_technician_role():
    """Check if current user has technician role"""
    user_roles = frappe.get_roles(frappe.session.user)
    return "Technician" in user_roles or "Workshop Manager" in user_roles


@frappe.whitelist()
def get_current_user():
    """Get current user details"""
    user = frappe.get_doc("User", frappe.session.user)

    # Get technician profile if exists
    technician = None
    if frappe.db.exists("Technician", {"user": frappe.session.user}):
        technician = frappe.get_doc("Technician", {"user": frappe.session.user})

    return {
        "name": user.name,
        "full_name": user.full_name,
        "email": user.email,
        "mobile": user.mobile_no,
        "language": user.language or "en",
        "technician": (
            {
                "name": technician.name if technician else None,
                "employee_id": technician.employee_id if technician else None,
                "department": technician.department if technician else None,
                "specialization": technician.specialization if technician else None,
                "skill_level": technician.skill_level if technician else None,
            }
            if technician
            else None
        ),
    }


@frappe.whitelist()
def get_technician_jobs():
    """Get jobs assigned to current technician"""

    # Get current technician
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")

    if not technician:
        return []

    # Get active service orders assigned to this technician
    jobs = frappe.db.sql(
        """
        SELECT 
            so.name,
            so.service_order_number,
            so.customer,
            so.customer_name,
            so.customer_name_ar,
            so.vehicle,
            so.vehicle_license_plate,
            so.priority,
            so.status,
            so.estimated_start_time,
            so.estimated_completion_time,
            so.actual_start_time,
            so.actual_completion_time,
            so.service_type,
            so.description,
            so.description_ar,
            so.total_estimated_cost,
            so.creation,
            so.modified
        FROM `tabService Order` so
        WHERE so.assigned_technician = %s
        AND so.status IN ('Assigned', 'In Progress', 'On Hold')
        AND so.docstatus = 1
        ORDER BY 
            CASE so.priority 
                WHEN 'High' THEN 1 
                WHEN 'Medium' THEN 2 
                ELSE 3 
            END,
            so.estimated_start_time ASC
    """,
        [technician],
        as_dict=True,
    )

    # Add additional details for each job
    for job in jobs:
        # Get vehicle details
        if job.vehicle:
            vehicle_details = (
                frappe.db.get_value(
                    "Vehicle Profile",
                    job.vehicle,
                    ["make", "model", "year", "color", "vin"],
                    as_dict=True,
                )
                or {}
            )
            job.update(vehicle_details)

        # Get service items
        job.service_items = frappe.db.sql(
            """
            SELECT 
                item_code,
                item_name,
                item_name_ar,
                qty,
                estimated_time_hours,
                rate,
                amount
            FROM `tabService Order Item`
            WHERE parent = %s
            ORDER BY idx
        """,
            [job.name],
            as_dict=True,
        )

        # Get current time logs for this job
        job.current_time_log = get_active_time_log(job.name)

        # Calculate estimated duration
        total_hours = sum([item.estimated_time_hours or 0 for item in job.service_items])
        job.estimated_duration_hours = total_hours

    return jobs


@frappe.whitelist()
def get_active_time_log(service_order):
    """Get active time log for a service order"""

    return frappe.db.sql(
        """
        SELECT 
            name,
            start_time,
            end_time,
            total_hours,
            status,
            break_duration_minutes
        FROM `tabTime Log`
        WHERE service_order = %s
        AND status = 'Running'
        ORDER BY start_time DESC
        LIMIT 1
    """,
        [service_order],
        as_dict=True,
    )


@frappe.whitelist()
def start_time_tracking(service_order, notes=None):
    """Start time tracking for a service order"""

    # Check if there's already an active time log
    active_log = get_active_time_log(service_order)
    if active_log:
        frappe.throw(_("Time tracking is already active for this job"))

    # Get technician
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    if not technician:
        frappe.throw(_("Technician profile not found"))

    # Create new time log
    time_log = frappe.new_doc("Time Log")
    time_log.technician = technician
    time_log.service_order = service_order
    time_log.start_time = frappe.utils.now()
    time_log.status = "Running"
    time_log.notes = notes or ""
    time_log.created_via_mobile = 1
    time_log.save()

    # Update service order status
    frappe.db.set_value("Service Order", service_order, "status", "In Progress")

    return {"success": True, "time_log": time_log.name, "message": _("Time tracking started")}


@frappe.whitelist()
def stop_time_tracking(service_order, notes=None):
    """Stop time tracking for a service order"""

    # Get active time log
    active_log = get_active_time_log(service_order)
    if not active_log:
        frappe.throw(_("No active time tracking found"))

    # Update time log
    time_log = frappe.get_doc("Time Log", active_log[0].name)
    time_log.end_time = frappe.utils.now()
    time_log.status = "Completed"
    if notes:
        time_log.notes += f"\n{notes}"

    # Calculate total hours
    if time_log.start_time and time_log.end_time:
        duration = frappe.utils.time_diff(time_log.end_time, time_log.start_time)
        time_log.total_hours = flt(duration.total_seconds() / 3600, 2)

    time_log.save()

    return {
        "success": True,
        "total_hours": time_log.total_hours,
        "message": _("Time tracking stopped"),
    }


@frappe.whitelist()
def pause_time_tracking(service_order, break_reason=None):
    """Pause time tracking for a break"""

    # Get active time log
    active_log = get_active_time_log(service_order)
    if not active_log:
        frappe.throw(_("No active time tracking found"))

    # Update time log to paused
    time_log = frappe.get_doc("Time Log", active_log[0].name)
    time_log.status = "Paused"
    time_log.pause_time = frappe.utils.now()
    time_log.break_reason = break_reason or ""
    time_log.save()

    return {"success": True, "message": _("Time tracking paused")}


@frappe.whitelist()
def resume_time_tracking(service_order):
    """Resume time tracking after a break"""

    # Get paused time log
    paused_log = frappe.db.get_value(
        "Time Log", {"service_order": service_order, "status": "Paused"}, "name"
    )

    if not paused_log:
        frappe.throw(_("No paused time tracking found"))

    # Update time log to running
    time_log = frappe.get_doc("Time Log", paused_log)

    # Calculate break duration
    if time_log.pause_time:
        break_duration = frappe.utils.time_diff(frappe.utils.now(), time_log.pause_time)
        current_break = time_log.break_duration_minutes or 0
        time_log.break_duration_minutes = current_break + (break_duration.total_seconds() / 60)

    time_log.status = "Running"
    time_log.pause_time = None
    time_log.save()

    return {"success": True, "message": _("Time tracking resumed")}


@frappe.whitelist()
def update_job_status(service_order, status, notes=None):
    """Update job status from mobile app"""

    allowed_statuses = ["In Progress", "On Hold", "Completed", "Quality Check"]

    if status not in allowed_statuses:
        frappe.throw(_("Invalid status"))

    # Get service order
    service_order_doc = frappe.get_doc("Service Order", service_order)

    # Verify technician assignment
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    if service_order_doc.assigned_technician != technician:
        frappe.throw(_("You are not assigned to this job"))

    # Update status
    service_order_doc.status = status
    if notes:
        service_order_doc.add_comment("Comment", notes)

    # Set completion time if completed
    if status == "Completed":
        service_order_doc.actual_completion_time = frappe.utils.now()

        # Stop any active time tracking
        active_log = get_active_time_log(service_order)
        if active_log:
            stop_time_tracking(service_order, "Job completed via mobile")

    service_order_doc.save()

    return {"success": True, "message": _("Job status updated to {0}").format(_(status))}


@frappe.whitelist()
def save_media_file(service_order, file_data, file_name, file_type="image"):
    """Save media file from mobile app"""

    # Verify technician assignment
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    service_order_doc = frappe.get_doc("Service Order", service_order)

    if service_order_doc.assigned_technician != technician:
        frappe.throw(_("You are not assigned to this job"))

    # Create file record
    file_doc = frappe.new_doc("File")
    file_doc.file_name = file_name
    file_doc.attached_to_doctype = "Service Order"
    file_doc.attached_to_name = service_order
    file_doc.folder = "Home/Attachments"
    file_doc.is_private = 0
    file_doc.save()

    return {
        "success": True,
        "file_url": file_doc.file_url,
        "message": _("Media file saved successfully"),
    }


@frappe.whitelist()
def sync_time_logs(time_logs_data):
    """Sync time logs from mobile app to server"""

    try:
        time_logs = frappe.parse_json(time_logs_data)
        synced_logs = []

        for log_data in time_logs:
            # Check if log already exists
            existing_log = frappe.db.exists("Time Log Mobile", {"mobile_id": log_data.get("id")})

            if not existing_log:
                # Create new time log
                time_log = frappe.new_doc("Time Log Mobile")
                time_log.mobile_id = log_data.get("id")
                time_log.service_order = log_data.get("job")
                time_log.action = log_data.get("action")
                time_log.timestamp = log_data.get("timestamp")
                time_log.elapsed_time = log_data.get("elapsed_time", 0)
                time_log.work_time = log_data.get("work_time", 0)
                time_log.breaks_data = frappe.as_json(log_data.get("breaks", []))
                time_log.current_break_data = frappe.as_json(log_data.get("current_break"))
                time_log.additional_data = frappe.as_json(log_data.get("additional_data", {}))
                time_log.technician = frappe.db.get_value(
                    "Technician", {"user": frappe.session.user}, "name"
                )
                time_log.save()

                synced_logs.append(log_data.get("id"))

        return {
            "success": True,
            "synced_count": len(synced_logs),
            "synced_logs": synced_logs,
            "message": _("Time logs synced successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Time log sync failed: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Failed to sync time logs")}


@frappe.whitelist()
def start_break(service_order, break_type="rest", reason=""):
    """Start a break for active time tracking"""

    # Get active time log
    active_log = get_active_time_log(service_order)
    if not active_log:
        frappe.throw(_("No active time tracking found"))

    # Create break record
    break_log = frappe.new_doc("Break Log")
    break_log.time_log = active_log[0].name
    break_log.service_order = service_order
    break_log.break_type = break_type
    break_log.reason = reason
    break_log.start_time = frappe.utils.now()
    break_log.technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    break_log.save()

    # Update time log status
    frappe.db.set_value("Time Log", active_log[0].name, "status", "On Break")

    return {
        "success": True,
        "break_id": break_log.name,
        "message": _("Break started: {0}").format(_(break_type)),
    }


@frappe.whitelist()
def end_break(service_order, break_id=None):
    """End the current break and resume work"""

    # Get active break
    if break_id:
        active_break = frappe.get_doc("Break Log", break_id)
    else:
        active_break = frappe.db.get_value(
            "Break Log", {"service_order": service_order, "end_time": ["is", "not set"]}, "name"
        )

        if active_break:
            active_break = frappe.get_doc("Break Log", active_break)

    if not active_break:
        frappe.throw(_("No active break found"))

    # End break
    active_break.end_time = frappe.utils.now()

    # Calculate duration
    if active_break.start_time:
        duration = frappe.utils.time_diff(active_break.end_time, active_break.start_time)
        active_break.duration_minutes = duration.total_seconds() / 60

    active_break.save()

    # Resume time tracking
    active_log = get_active_time_log(service_order)
    if active_log:
        frappe.db.set_value("Time Log", active_log[0].name, "status", "Running")

    return {
        "success": True,
        "break_duration": active_break.duration_minutes,
        "message": _("Break ended, work resumed"),
    }


@frappe.whitelist()
def add_manual_time(service_order, minutes, reason):
    """Add manual time entry to current job"""

    if not service_order or not minutes or not reason:
        frappe.throw(_("Service order, minutes, and reason are required"))

    # Get technician
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    if not technician:
        frappe.throw(_("Technician profile not found"))

    # Create manual time entry
    manual_entry = frappe.new_doc("Manual Time Entry")
    manual_entry.service_order = service_order
    manual_entry.technician = technician
    manual_entry.minutes = flt(minutes)
    manual_entry.reason = reason
    manual_entry.entry_time = frappe.utils.now()
    manual_entry.approved = 0  # Requires approval
    manual_entry.save()

    return {
        "success": True,
        "entry_id": manual_entry.name,
        "message": _("Manual time entry added: {0} minutes").format(minutes),
    }


@frappe.whitelist()
def get_break_types():
    """Get available break types with translations"""

    lang = frappe.local.lang or "en"

    break_types = {
        "ar": {
            "prayer": "صلاة",
            "lunch": "غداء",
            "rest": "استراحة",
            "technical": "مشكلة تقنية",
            "material": "انتظار قطع",
            "emergency": "طارئ",
            "other": "أخرى",
        },
        "en": {
            "prayer": "Prayer",
            "lunch": "Lunch",
            "rest": "Rest Break",
            "technical": "Technical Issue",
            "material": "Waiting for Parts",
            "emergency": "Emergency",
            "other": "Other",
        },
    }

    return {
        "success": True,
        "break_types": break_types.get(lang, break_types["en"]),
        "all_languages": break_types,
    }


@frappe.whitelist()
def get_time_summary(service_order):
    """Get comprehensive time summary for a job"""

    # Get all time logs for the job
    time_logs = frappe.db.sql(
        """
        SELECT 
            name,
            start_time,
            end_time,
            total_hours,
            status,
            break_duration_minutes
        FROM `tabTime Log`
        WHERE service_order = %s
        ORDER BY start_time
    """,
        [service_order],
        as_dict=True,
    )

    # Get all breaks for the job
    breaks = frappe.db.sql(
        """
        SELECT 
            break_type,
            reason,
            start_time,
            end_time,
            duration_minutes
        FROM `tabBreak Log`
        WHERE service_order = %s
        ORDER BY start_time
    """,
        [service_order],
        as_dict=True,
    )

    # Get manual time entries
    manual_entries = frappe.db.sql(
        """
        SELECT 
            minutes,
            reason,
            entry_time,
            approved
        FROM `tabManual Time Entry`
        WHERE service_order = %s
        ORDER BY entry_time
    """,
        [service_order],
        as_dict=True,
    )

    # Calculate totals
    total_work_hours = sum([log.total_hours or 0 for log in time_logs])
    total_break_minutes = sum([log.break_duration_minutes or 0 for log in time_logs])
    total_manual_minutes = sum([entry.minutes or 0 for entry in manual_entries if entry.approved])

    return {
        "success": True,
        "time_logs": time_logs,
        "breaks": breaks,
        "manual_entries": manual_entries,
        "summary": {
            "total_work_hours": total_work_hours,
            "total_break_minutes": total_break_minutes,
            "total_manual_minutes": total_manual_minutes,
            "total_billable_hours": total_work_hours + (total_manual_minutes / 60),
        },
    }


@frappe.whitelist()
def get_technician_performance():
    """Get technician performance metrics"""

    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    if not technician:
        frappe.throw(_("Technician profile not found"))

    # Get performance data for last 30 days
    from datetime import datetime, timedelta

    thirty_days_ago = datetime.now() - timedelta(days=30)

    # Jobs completed
    completed_jobs = frappe.db.count(
        "Service Order",
        {
            "assigned_technician": technician,
            "status": "Completed",
            "actual_completion_time": [">=", thirty_days_ago.strftime("%Y-%m-%d")],
        },
    )

    # Average job time
    avg_time = frappe.db.sql(
        """
        SELECT AVG(total_hours) as avg_hours
        FROM `tabTime Log`
        WHERE technician = %s
        AND creation >= %s
        AND status = 'Completed'
    """,
        [technician, thirty_days_ago.strftime("%Y-%m-%d")],
        as_dict=True,
    )

    # Break patterns
    break_patterns = frappe.db.sql(
        """
        SELECT 
            break_type,
            AVG(duration_minutes) as avg_duration,
            COUNT(*) as frequency
        FROM `tabBreak Log`
        WHERE technician = %s
        AND creation >= %s
        GROUP BY break_type
    """,
        [technician, thirty_days_ago.strftime("%Y-%m-%d")],
        as_dict=True,
    )

    return {
        "success": True,
        "performance": {
            "completed_jobs_30d": completed_jobs,
            "average_job_hours": avg_time[0].avg_hours if avg_time else 0,
            "break_patterns": break_patterns,
        },
    }


def get_app_config():
    """Get app configuration for mobile interface"""

    return {
        "company": frappe.db.get_single_value("Global Defaults", "default_company"),
        "currency": frappe.db.get_single_value("Global Defaults", "default_currency"),
        "language": frappe.db.get_single_value("System Settings", "language"),
        "time_zone": frappe.db.get_single_value("System Settings", "time_zone"),
        "date_format": frappe.db.get_single_value("System Settings", "date_format"),
        "time_format": frappe.db.get_single_value("System Settings", "time_format"),
        "app_version": frappe.get_attr("universal_workshop.__version__") or "1.0.0",
        "offline_sync_interval": 300000,  # 5 minutes
        "max_offline_hours": 2,
        "break_types_enabled": True,
        "manual_time_entry_enabled": True,
        "require_break_approval": False,
        "require_manual_time_approval": True,
    }


@frappe.whitelist()
def get_part_by_barcode(barcode):
    """Get part information by barcode"""

    if not barcode:
        frappe.throw(_("Barcode is required"))

    # Search for item by barcode
    part = frappe.db.get_value(
        "Item",
        {"barcode": barcode, "disabled": 0},
        [
            "name",
            "item_code",
            "item_name",
            "item_name_ar",
            "standard_rate",
            "stock_uom",
            "description",
            "description_ar",
        ],
        as_dict=True,
    )

    if not part:
        # Try searching by item_code as fallback
        part = frappe.db.get_value(
            "Item",
            {"item_code": barcode, "disabled": 0},
            [
                "name",
                "item_code",
                "item_name",
                "item_name_ar",
                "standard_rate",
                "stock_uom",
                "description",
                "description_ar",
            ],
            as_dict=True,
        )

    if not part:
        return {"success": False, "message": _("Part not found with barcode: {0}").format(barcode)}

    # Get current stock quantity
    try:
        stock_qty = (
            frappe.db.get_value("Bin", {"item_code": part.item_code}, "sum(actual_qty)") or 0
        )
    except:
        stock_qty = 0

    part.stock_qty = stock_qty

    return {
        "success": True,
        "part": part,
        "message": _("Part found: {0}").format(part.item_name or part.item_code),
    }


@frappe.whitelist()
def add_part_usage(service_order, barcode, quantity=1, notes=""):
    """Add part usage to service order"""

    if not service_order or not barcode:
        frappe.throw(_("Service order and barcode are required"))

    # Verify technician assignment
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    service_order_doc = frappe.get_doc("Service Order", service_order)

    if service_order_doc.assigned_technician != technician:
        frappe.throw(_("You are not assigned to this job"))

    # Get part information
    part_response = get_part_by_barcode(barcode)
    if not part_response.get("success"):
        frappe.throw(part_response.get("message"))

    part = part_response.get("part")

    # Create parts usage record
    part_usage = frappe.new_doc("Part Usage")
    part_usage.service_order = service_order
    part_usage.item_code = part.item_code
    part_usage.item_name = part.item_name
    part_usage.item_name_ar = part.item_name_ar
    part_usage.quantity = flt(quantity)
    part_usage.rate = flt(part.standard_rate or 0)
    part_usage.amount = flt(quantity) * flt(part.standard_rate or 0)
    part_usage.uom = part.stock_uom
    part_usage.barcode = barcode
    part_usage.technician = technician
    part_usage.usage_time = frappe.utils.now()
    part_usage.notes = notes
    part_usage.synced = 1  # Mark as synced since created on server
    part_usage.save()

    return {
        "success": True,
        "part_usage": part_usage.name,
        "part_info": part,
        "message": _("Part usage recorded: {0} x {1}").format(quantity, part.item_name),
    }


@frappe.whitelist()
def sync_parts_usage(parts_data):
    """Sync parts usage from mobile app to server"""

    try:
        parts_list = frappe.parse_json(parts_data)
        synced_parts = []

        for part_data in parts_list:
            # Check if part usage already exists
            existing_usage = frappe.db.exists("Part Usage", {"mobile_id": part_data.get("id")})

            if not existing_usage:
                # Get part information
                part_response = get_part_by_barcode(part_data.get("barcode"))
                if not part_response.get("success"):
                    continue  # Skip if part not found

                part = part_response.get("part")

                # Create new part usage
                part_usage = frappe.new_doc("Part Usage")
                part_usage.mobile_id = part_data.get("id")
                part_usage.service_order = part_data.get("job")
                part_usage.item_code = part.item_code
                part_usage.item_name = part.item_name
                part_usage.item_name_ar = part.item_name_ar
                part_usage.quantity = flt(part_data.get("quantity", 1))
                part_usage.rate = flt(part.standard_rate or 0)
                part_usage.amount = part_usage.quantity * part_usage.rate
                part_usage.uom = part.stock_uom
                part_usage.barcode = part_data.get("barcode")
                part_usage.technician = part_data.get("technician")
                part_usage.usage_time = part_data.get("timestamp")
                part_usage.notes = part_data.get("notes", "")
                part_usage.synced = 1
                part_usage.save()

                synced_parts.append(part_data.get("id"))

        return {
            "success": True,
            "synced_count": len(synced_parts),
            "synced_parts": synced_parts,
            "message": _("Parts usage synced successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Parts sync failed: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Failed to sync parts usage")}


@frappe.whitelist()
def get_parts_list(service_order):
    """Get list of parts used in service order"""

    if not service_order:
        frappe.throw(_("Service order is required"))

    # Verify technician assignment
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    service_order_doc = frappe.get_doc("Service Order", service_order)

    if service_order_doc.assigned_technician != technician:
        frappe.throw(_("You are not assigned to this job"))

    # Get parts usage for this service order
    parts_usage = frappe.get_all(
        "Part Usage",
        filters={"service_order": service_order},
        fields=[
            "name",
            "item_code",
            "item_name",
            "item_name_ar",
            "quantity",
            "rate",
            "amount",
            "uom",
            "barcode",
            "usage_time",
            "notes",
            "synced",
        ],
        order_by="usage_time desc",
    )

    # Calculate totals
    total_amount = sum(part.amount for part in parts_usage)
    total_parts = len(parts_usage)

    return {
        "success": True,
        "parts_usage": parts_usage,
        "totals": {"total_parts": total_parts, "total_amount": total_amount},
        "message": _("Parts list retrieved successfully"),
    }


@frappe.whitelist()
def remove_part_usage(part_usage_id):
    """Remove part usage record"""

    if not part_usage_id:
        frappe.throw(_("Part usage ID is required"))

    # Get part usage
    part_usage = frappe.get_doc("Part Usage", part_usage_id)

    # Verify technician can modify this record
    technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
    if part_usage.technician != technician:
        frappe.throw(_("You can only modify your own part usage records"))

    # Delete the record
    frappe.delete_doc("Part Usage", part_usage_id)

    return {"success": True, "message": _("Part usage removed successfully")}


@frappe.whitelist()
def search_parts(search_term, limit=20):
    """Search parts across multiple fields"""
    if not search_term or len(search_term.strip()) < 2:
        return {"success": False, "message": _("Search term must be at least 2 characters")}

    # Search across multiple fields
    conditions = []
    search_fields = [
        "item_code",
        "item_name",
        "item_name_ar",
        "item_group",
        "description",
        "description_ar",
    ]

    for field in search_fields:
        conditions.append(f"`{field}` LIKE %(search_term)s")

    sql = f"""
        SELECT 
            name,
            item_code,
            item_name,
            item_name_ar,
            standard_rate,
            stock_uom,
            image,
            description
        FROM `tabItem`
        WHERE ({' OR '.join(conditions)})
        AND disabled = 0
        AND is_stock_item = 1
        ORDER BY 
            CASE WHEN item_code LIKE %(search_term)s THEN 0 ELSE 1 END,
            item_name
        LIMIT %(limit)s
    """

    try:
        parts = frappe.db.sql(
            sql, {"search_term": f"%{search_term}%", "limit": limit}, as_dict=True
        )

        return {"success": True, "parts": parts, "count": len(parts)}

    except Exception as e:
        frappe.log_error(f"Parts search error: {str(e)}")
        return {"success": False, "message": _("Search failed")}


# ============================================================================
# PUSH NOTIFICATION SYSTEM
# ============================================================================


@frappe.whitelist()
def subscribe_to_notifications(subscription_data):
    """Subscribe technician to push notifications"""
    try:
        # Get technician
        technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
        if not technician:
            frappe.throw(_("Technician profile not found"))

        # Parse subscription data
        import json

        if isinstance(subscription_data, str):
            subscription_data = json.loads(subscription_data)

        # Store subscription in custom doctype or user data
        user = frappe.get_doc("User", frappe.session.user)

        # Store subscription details in custom fields or separate doctype
        subscription_doc = frappe.new_doc("Push Notification Subscription")
        subscription_doc.user = frappe.session.user
        subscription_doc.technician = technician
        subscription_doc.endpoint = subscription_data.get("endpoint")
        subscription_doc.auth_key = subscription_data.get("keys", {}).get("auth")
        subscription_doc.p256dh_key = subscription_data.get("keys", {}).get("p256dh")
        subscription_doc.is_active = 1
        subscription_doc.insert()

        return {
            "success": True,
            "message": _("Successfully subscribed to notifications"),
            "subscription_id": subscription_doc.name,
        }

    except Exception as e:
        frappe.log_error(f"Push notification subscription error: {str(e)}")
        return {"success": False, "message": _("Failed to subscribe to notifications")}


@frappe.whitelist()
def unsubscribe_from_notifications():
    """Unsubscribe technician from push notifications"""
    try:
        # Deactivate all subscriptions for this user
        subscriptions = frappe.get_all(
            "Push Notification Subscription",
            filters={"user": frappe.session.user, "is_active": 1},
            fields=["name"],
        )

        for sub in subscriptions:
            frappe.db.set_value("Push Notification Subscription", sub.name, "is_active", 0)

        return {"success": True, "message": _("Successfully unsubscribed from notifications")}

    except Exception as e:
        frappe.log_error(f"Push notification unsubscribe error: {str(e)}")
        return {"success": False, "message": _("Failed to unsubscribe from notifications")}


@frappe.whitelist()
def send_job_assignment_notification(service_order, technician, priority="normal"):
    """Send push notification for new job assignment"""
    try:
        # Get service order details
        so_doc = frappe.get_doc("Service Order", service_order)
        customer_name = so_doc.customer_name or so_doc.customer
        vehicle_info = (
            f"{so_doc.vehicle_make} {so_doc.vehicle_model}"
            if hasattr(so_doc, "vehicle_make")
            else "Vehicle"
        )

        # Get technician subscriptions
        subscriptions = get_technician_subscriptions(technician)

        if not subscriptions:
            return {"success": False, "message": _("No active subscriptions found")}

        # Prepare notification payload
        lang = (
            frappe.db.get_value(
                "User", frappe.db.get_value("Technician", technician, "user"), "language"
            )
            or "en"
        )

        title = _("New Job Assignment") if lang == "en" else "تعيين مهمة جديدة"
        body = (
            f"{_('Customer')}: {customer_name}\n{_('Vehicle')}: {vehicle_info}"
            if lang == "en"
            else f"العميل: {customer_name}\nالمركبة: {vehicle_info}"
        )

        notification_payload = {
            "title": title,
            "body": body,
            "icon": "/assets/universal_workshop/images/icons/icon-192x192.png",
            "badge": "/assets/universal_workshop/images/icons/badge-72x72.png",
            "tag": f"job-{service_order}",
            "data": {
                "type": "job_assignment",
                "service_order": service_order,
                "priority": priority,
                "url": f"/technician?job={service_order}",
            },
            "actions": [
                {"action": "view_job", "title": _("View Job") if lang == "en" else "عرض المهمة"},
                {"action": "dismiss", "title": _("Dismiss") if lang == "en" else "إغلاق"},
            ],
        }

        # Send notifications to all active subscriptions
        sent_count = 0
        for subscription in subscriptions:
            if send_push_notification(subscription, notification_payload):
                sent_count += 1

        return {
            "success": True,
            "message": _("Notification sent to {0} devices").format(sent_count),
            "sent_count": sent_count,
        }

    except Exception as e:
        frappe.log_error(f"Job assignment notification error: {str(e)}")
        return {"success": False, "message": _("Failed to send notification")}


@frappe.whitelist()
def send_priority_update_notification(service_order, new_priority, reason=""):
    """Send push notification for priority changes"""
    try:
        # Get service order and technician
        so_doc = frappe.get_doc("Service Order", service_order)
        technician = so_doc.assigned_technician

        if not technician:
            return {"success": False, "message": _("No technician assigned")}

        # Get technician subscriptions
        subscriptions = get_technician_subscriptions(technician)

        if not subscriptions:
            return {"success": False, "message": _("No active subscriptions found")}

        # Prepare notification payload
        lang = (
            frappe.db.get_value(
                "User", frappe.db.get_value("Technician", technician, "user"), "language"
            )
            or "en"
        )

        title = _("Priority Update") if lang == "en" else "تحديث الأولوية"
        priority_text = (
            _("High Priority")
            if new_priority == "high"
            else (_("Medium Priority") if new_priority == "medium" else _("Low Priority"))
        )
        if lang == "ar":
            priority_text = (
                "أولوية عالية"
                if new_priority == "high"
                else ("أولوية متوسطة" if new_priority == "medium" else "أولوية منخفضة")
            )

        body = f"{_('Job')}: {service_order}\n{_('Priority')}: {priority_text}"
        if lang == "ar":
            body = f"المهمة: {service_order}\nالأولوية: {priority_text}"

        if reason:
            body += f"\n{_('Reason')}: {reason}" if lang == "en" else f"\nالسبب: {reason}"

        notification_payload = {
            "title": title,
            "body": body,
            "icon": "/assets/universal_workshop/images/icons/icon-192x192.png",
            "badge": "/assets/universal_workshop/images/icons/badge-72x72.png",
            "tag": f"priority-{service_order}",
            "urgency": "high" if new_priority == "high" else "normal",
            "data": {
                "type": "priority_update",
                "service_order": service_order,
                "new_priority": new_priority,
                "url": f"/technician?job={service_order}",
            },
            "actions": [
                {"action": "view_job", "title": _("View Job") if lang == "en" else "عرض المهمة"}
            ],
        }

        # Send notifications
        sent_count = 0
        for subscription in subscriptions:
            if send_push_notification(subscription, notification_payload):
                sent_count += 1

        return {
            "success": True,
            "message": _("Priority update notification sent to {0} devices").format(sent_count),
            "sent_count": sent_count,
        }

    except Exception as e:
        frappe.log_error(f"Priority update notification error: {str(e)}")
        return {"success": False, "message": _("Failed to send priority notification")}


def get_technician_subscriptions(technician):
    """Get all active push notification subscriptions for a technician"""
    try:
        user = frappe.db.get_value("Technician", technician, "user")
        if not user:
            return []

        subscriptions = frappe.get_all(
            "Push Notification Subscription",
            filters={"user": user, "is_active": 1},
            fields=["name", "endpoint", "auth_key", "p256dh_key"],
        )

        return subscriptions

    except Exception as e:
        frappe.log_error(f"Error getting technician subscriptions: {str(e)}")
        return []


def send_push_notification(subscription, payload):
    """Send push notification using Web Push Protocol"""
    try:
        from pywebpush import webpush, WebPushException
        import json

        # VAPID keys should be configured in site_config.json
        vapid_private_key = frappe.conf.get("vapid_private_key")
        vapid_public_key = frappe.conf.get("vapid_public_key")
        vapid_claims = {
            "sub": f"mailto:{frappe.conf.get('admin_email', 'admin@universal-workshop.om')}"
        }

        if not vapid_private_key or not vapid_public_key:
            frappe.log_error("VAPID keys not configured for push notifications")
            return False

        # Prepare subscription info
        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {"auth": subscription.auth_key, "p256dh": subscription.p256dh_key},
        }

        # Send notification
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims,
        )

        return True

    except WebPushException as e:
        if e.response and e.response.status_code == 410:
            # Subscription is no longer valid, deactivate it
            frappe.db.set_value("Push Notification Subscription", subscription.name, "is_active", 0)
            frappe.log_error(f"Deactivated invalid push subscription: {subscription.name}")
        else:
            frappe.log_error(f"WebPush error: {str(e)}")
        return False
    except Exception as e:
        frappe.log_error(f"Push notification send error: {str(e)}")
        return False


@frappe.whitelist()
def get_notification_settings():
    """Get current notification preferences for technician"""
    try:
        technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
        if not technician:
            frappe.throw(_("Technician profile not found"))

        # Get active subscriptions count
        active_subscriptions = frappe.db.count(
            "Push Notification Subscription", {"user": frappe.session.user, "is_active": 1}
        )

        # Get notification preferences (if we have a custom doctype for this)
        settings = {
            "job_assignments": True,
            "priority_updates": True,
            "deadline_reminders": True,
            "break_reminders": True,
            "active_subscriptions": active_subscriptions,
        }

        return {"success": True, "settings": settings}

    except Exception as e:
        frappe.log_error(f"Get notification settings error: {str(e)}")
        return {"success": False, "message": _("Failed to get notification settings")}


@frappe.whitelist()
def update_notification_settings(settings_data):
    """Update notification preferences for technician"""
    try:
        technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
        if not technician:
            frappe.throw(_("Technician profile not found"))

        import json

        if isinstance(settings_data, str):
            settings_data = json.loads(settings_data)

        # Store settings in user preferences or custom doctype
        # For now, we'll use frappe.defaults
        for key, value in settings_data.items():
            frappe.defaults.set_user_default(f"notification_{key}", value)

        return {"success": True, "message": _("Notification settings updated successfully")}

    except Exception as e:
        frappe.log_error(f"Update notification settings error: {str(e)}")
        return {"success": False, "message": _("Failed to update settings")}


# Test notification for development
@frappe.whitelist()
def send_test_notification():
    """Send test notification to current technician"""
    try:
        technician = frappe.db.get_value("Technician", {"user": frappe.session.user}, "name")
        if not technician:
            frappe.throw(_("Technician profile not found"))

        subscriptions = get_technician_subscriptions(technician)

        if not subscriptions:
            return {"success": False, "message": _("No active subscriptions found")}

        lang = frappe.db.get_value("User", frappe.session.user, "language") or "en"

        notification_payload = {
            "title": _("Test Notification") if lang == "en" else "إشعار تجريبي",
            "body": (
                _("This is a test notification from Universal Workshop")
                if lang == "en"
                else "هذا إشعار تجريبي من الورشة الشاملة"
            ),
            "icon": "/assets/universal_workshop/images/icons/icon-192x192.png",
            "badge": "/assets/universal_workshop/images/icons/badge-72x72.png",
            "tag": "test-notification",
            "data": {"type": "test", "url": "/technician"},
        }

        sent_count = 0
        for subscription in subscriptions:
            if send_push_notification(subscription, notification_payload):
                sent_count += 1

        return {
            "success": True,
            "message": _("Test notification sent to {0} devices").format(sent_count),
            "sent_count": sent_count,
        }

    except Exception as e:
        frappe.log_error(f"Test notification error: {str(e)}")
        return {"success": False, "message": _("Failed to send test notification")}
