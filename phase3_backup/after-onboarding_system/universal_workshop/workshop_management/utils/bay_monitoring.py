# Copyright (c) 2025, Said Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, now_datetime, add_days, today
from datetime import datetime, timedelta


@frappe.whitelist()
def get_service_bay_dashboard():
    """Get comprehensive service bay monitoring dashboard data"""

    # Get all active bays
    bays = frappe.get_all(
        "Service Bay",
        filters={"is_active": 1},
        fields=[
            "name",
            "bay_code",
            "bay_name",
            "bay_name_ar",
            "bay_type",
            "workshop_profile",
            "current_occupancy",
            "max_vehicles",
            "utilization_rate",
            "average_service_time",
            "daily_capacity",
            "operating_hours_start",
            "operating_hours_end",
        ],
    )

    # Calculate overall metrics
    total_bays = len(bays)
    total_capacity = sum([bay.max_vehicles for bay in bays])
    total_occupied = sum([bay.current_occupancy for bay in bays])
    overall_utilization = (total_occupied / total_capacity * 100) if total_capacity > 0 else 0

    # Get today's orders
    today_orders = frappe.db.count(
        "Service Order", {"service_date": today(), "status": ["not in", ["Cancelled", "Draft"]]}
    )

    # Get completed orders today
    completed_today = frappe.db.count(
        "Service Order", {"service_date": today(), "status": "Completed"}
    )

    # Get pending quality checks
    pending_qc = frappe.db.count(
        "Quality Control Checkpoint", {"creation": [">=", today()], "status": "Pending"}
    )

    # Get weekly performance
    weekly_performance = get_weekly_performance()

    # Get capacity alerts
    capacity_alerts = get_capacity_alerts()

    return {
        "summary": {
            "total_bays": total_bays,
            "total_capacity": total_capacity,
            "current_occupied": total_occupied,
            "overall_utilization": flt(overall_utilization, 2),
            "today_orders": today_orders,
            "completed_today": completed_today,
            "pending_qc": pending_qc,
        },
        "bays": bays,
        "weekly_performance": weekly_performance,
        "capacity_alerts": capacity_alerts,
        "utilization_chart": get_utilization_chart_data(),
        "bay_status": get_real_time_bay_status(),
    }


@frappe.whitelist()
def get_real_time_bay_status():
    """Get real-time status of all service bays"""

    bays_status = frappe.db.sql(
        """
		SELECT 
			sb.name as bay_id,
			sb.bay_code,
			sb.bay_name,
			sb.bay_name_ar,
			sb.bay_type,
			sb.max_vehicles,
			sb.current_occupancy,
			sb.utilization_rate,
			COUNT(so.name) as current_orders,
			GROUP_CONCAT(
				CONCAT(so.name, ':', so.customer, ':', so.status)
				SEPARATOR '|'
			) as active_orders
		FROM `tabService Bay` sb
		LEFT JOIN `tabService Order` so ON sb.name = so.service_bay 
			AND so.status IN ('In Progress', 'Quality Check', 'Scheduled')
			AND so.service_date = CURDATE()
		WHERE sb.is_active = 1
		GROUP BY sb.name
		ORDER BY sb.bay_code
	""",
        as_dict=True,
    )

    # Process the results
    for bay in bays_status:
        bay.status = "Available"
        if bay.current_occupancy >= bay.max_vehicles:
            bay.status = "Full"
        elif bay.current_occupancy > 0:
            bay.status = "Occupied"

        # Parse active orders
        bay.orders = []
        if bay.active_orders:
            for order_info in bay.active_orders.split("|"):
                if order_info:
                    parts = order_info.split(":")
                    if len(parts) >= 3:
                        bay.orders.append(
                            {"order_id": parts[0], "customer": parts[1], "status": parts[2]}
                        )

        # Remove raw data
        del bay.active_orders

    return bays_status


@frappe.whitelist()
def get_weekly_performance():
    """Get weekly performance metrics"""

    performance = frappe.db.sql(
        """
		SELECT 
			DATE(so.service_date) as date,
			DAYNAME(so.service_date) as day_name,
			COUNT(so.name) as total_orders,
			SUM(CASE WHEN so.status = 'Completed' THEN 1 ELSE 0 END) as completed_orders,
			SUM(CASE WHEN so.status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
			AVG(TIMESTAMPDIFF(HOUR, so.service_start_time, so.service_end_time)) as avg_duration,
			COUNT(DISTINCT so.service_bay) as bays_used
		FROM `tabService Order` so
		WHERE so.service_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
		AND so.service_date <= CURDATE()
		GROUP BY DATE(so.service_date)
		ORDER BY so.service_date
	""",
        as_dict=True,
    )

    # Calculate completion rate
    for day in performance:
        if day.total_orders > 0:
            day.completion_rate = flt((day.completed_orders / day.total_orders) * 100, 2)
        else:
            day.completion_rate = 0
        day.avg_duration = flt(day.avg_duration or 0, 2)

    return performance


@frappe.whitelist()
def get_utilization_chart_data():
    """Get utilization chart data for the last 30 days"""

    chart_data = frappe.db.sql(
        """
		SELECT 
			DATE(creation) as date,
			AVG(utilization_rate) as avg_utilization,
			MAX(utilization_rate) as max_utilization,
			MIN(utilization_rate) as min_utilization
		FROM `tabService Bay`
		WHERE creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
		AND is_active = 1
		GROUP BY DATE(creation)
		ORDER BY date
	""",
        as_dict=True,
    )

    return chart_data


@frappe.whitelist()
def get_capacity_alerts():
    """Get capacity planning alerts and recommendations"""

    alerts = []

    # Get bays with high utilization (>90%)
    high_utilization_bays = frappe.get_all(
        "Service Bay",
        filters={"is_active": 1, "utilization_rate": [">", 90]},
        fields=["bay_code", "bay_name", "utilization_rate", "current_occupancy", "max_vehicles"],
    )

    for bay in high_utilization_bays:
        alerts.append(
            {
                "type": "high_utilization",
                "severity": "warning",
                "title": _("High Utilization Alert"),
                "message": _("Bay {0} is running at {1}% capacity").format(
                    bay.bay_code, bay.utilization_rate
                ),
                "bay_code": bay.bay_code,
                "recommendation": _("Consider redirecting some orders to other available bays"),
            }
        )

    # Get bays with no activity today
    inactive_bays = frappe.db.sql(
        """
		SELECT sb.bay_code, sb.bay_name
		FROM `tabService Bay` sb
		LEFT JOIN `tabService Order` so ON sb.name = so.service_bay 
			AND so.service_date = CURDATE()
		WHERE sb.is_active = 1 
		AND so.name IS NULL
		GROUP BY sb.name
	""",
        as_dict=True,
    )

    for bay in inactive_bays:
        alerts.append(
            {
                "type": "no_activity",
                "severity": "info",
                "title": _("Underutilized Bay"),
                "message": _("Bay {0} has no scheduled orders today").format(bay.bay_code),
                "bay_code": bay.bay_code,
                "recommendation": _(
                    "Consider scheduling routine maintenance or promotional services"
                ),
            }
        )

    # Check for maintenance overdue
    overdue_maintenance = frappe.db.sql(
        """
		SELECT bay_code, bay_name, last_maintenance_date, maintenance_schedule
		FROM `tabService Bay`
		WHERE is_active = 1
		AND last_maintenance_date IS NOT NULL
		AND (
			(maintenance_schedule = 'Weekly' AND last_maintenance_date < DATE_SUB(CURDATE(), INTERVAL 7 DAY))
			OR (maintenance_schedule = 'Bi-weekly' AND last_maintenance_date < DATE_SUB(CURDATE(), INTERVAL 14 DAY))
			OR (maintenance_schedule = 'Monthly' AND last_maintenance_date < DATE_SUB(CURDATE(), INTERVAL 30 DAY))
			OR (maintenance_schedule = 'Quarterly' AND last_maintenance_date < DATE_SUB(CURDATE(), INTERVAL 90 DAY))
		)
	""",
        as_dict=True,
    )

    for bay in overdue_maintenance:
        alerts.append(
            {
                "type": "maintenance_overdue",
                "severity": "error",
                "title": _("Maintenance Overdue"),
                "message": _("Bay {0} maintenance is overdue").format(bay.bay_code),
                "bay_code": bay.bay_code,
                "recommendation": _("Schedule maintenance immediately to prevent equipment issues"),
            }
        )

    return alerts


@frappe.whitelist()
def get_capacity_planning_report(days_ahead=30):
    """Generate capacity planning report for upcoming days"""

    # Get scheduled orders for the next N days
    future_orders = frappe.db.sql(
        """
		SELECT 
			service_date,
			service_bay,
			COUNT(*) as orders_count,
			SUM(estimated_duration) as total_duration
		FROM `tabService Order`
		WHERE service_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
		AND status NOT IN ('Cancelled', 'Completed')
		GROUP BY service_date, service_bay
		ORDER BY service_date, service_bay
	""",
        [days_ahead],
        as_dict=True,
    )

    # Get bay capacities
    bay_capacities = frappe.get_all(
        "Service Bay",
        filters={"is_active": 1},
        fields=["name", "bay_code", "daily_capacity", "max_vehicles"],
    )

    capacity_map = {bay.name: bay for bay in bay_capacities}

    # Analyze capacity by date
    capacity_analysis = {}
    for order in future_orders:
        date = str(order.service_date)
        if date not in capacity_analysis:
            capacity_analysis[date] = {
                "date": date,
                "total_orders": 0,
                "total_capacity": sum([bay.daily_capacity for bay in bay_capacities]),
                "bays": {},
            }

        bay_info = capacity_map.get(order.service_bay, {})
        capacity_analysis[date]["total_orders"] += order.orders_count
        capacity_analysis[date]["bays"][order.service_bay] = {
            "bay_code": bay_info.get("bay_code", "Unknown"),
            "scheduled_orders": order.orders_count,
            "daily_capacity": bay_info.get("daily_capacity", 0),
            "utilization": (
                (order.orders_count / bay_info.get("daily_capacity", 1)) * 100
                if bay_info.get("daily_capacity")
                else 0
            ),
        }

    # Convert to list and sort
    planning_data = list(capacity_analysis.values())
    planning_data.sort(key=lambda x: x["date"])

    # Add utilization percentage
    for day in planning_data:
        if day["total_capacity"] > 0:
            day["overall_utilization"] = (day["total_orders"] / day["total_capacity"]) * 100
        else:
            day["overall_utilization"] = 0

    return planning_data


@frappe.whitelist()
def optimize_bay_assignments(date=None):
    """Suggest optimal bay assignments for a given date"""

    if not date:
        date = today()

    # Get pending orders for the date
    pending_orders = frappe.get_all(
        "Service Order",
        filters={
            "service_date": date,
            "status": ["in", ["Draft", "Scheduled"]],
            "service_bay": ["is", "not set"],
        },
        fields=["name", "service_type", "estimated_duration", "priority", "customer"],
    )

    # Get available bays
    available_bays = frappe.db.sql(
        """
		SELECT 
			sb.name,
			sb.bay_code,
			sb.bay_type,
			sb.max_vehicles,
			sb.daily_capacity,
			COUNT(so.name) as current_bookings
		FROM `tabService Bay` sb
		LEFT JOIN `tabService Order` so ON sb.name = so.service_bay 
			AND so.service_date = %s
			AND so.status NOT IN ('Cancelled', 'Completed')
		WHERE sb.is_active = 1
		GROUP BY sb.name
		HAVING current_bookings < sb.max_vehicles
		ORDER BY current_bookings, sb.bay_type
	""",
        [date],
        as_dict=True,
    )

    # Simple assignment algorithm
    assignments = []
    for order in pending_orders:
        best_bay = None
        best_score = 0

        for bay in available_bays:
            score = 0

            # Bay type matching
            if bay.bay_type == "General Service":
                score += 1
            elif order.service_type and bay.bay_type in order.service_type:
                score += 3

            # Capacity consideration
            if bay.current_bookings < bay.max_vehicles:
                score += (bay.max_vehicles - bay.current_bookings) * 2

            # Priority consideration
            if order.priority == "High":
                score += 2

            if score > best_score:
                best_score = score
                best_bay = bay

        if best_bay:
            assignments.append(
                {
                    "order_id": order.name,
                    "customer": order.customer,
                    "recommended_bay": best_bay.bay_code,
                    "bay_id": best_bay.name,
                    "score": best_score,
                    "reason": f"Best match based on bay type and availability",
                }
            )

            # Update bay booking count for next iteration
            best_bay.current_bookings += 1

    return assignments


@frappe.whitelist()
def update_bay_utilization():
    """Update utilization metrics for all bays (scheduled function)"""

    bays = frappe.get_all("Service Bay", filters={"is_active": 1})

    for bay in bays:
        bay_doc = frappe.get_doc("Service Bay", bay.name)
        bay_doc.update_utilization_metrics()
        bay_doc.save()

    frappe.db.commit()
    return f"Updated utilization for {len(bays)} bays"


@frappe.whitelist()
def get_quality_control_metrics():
    """Get quality control metrics for the dashboard"""

    # QC checkpoints today
    today_checkpoints = frappe.db.count("Quality Control Checkpoint", {"creation": [">=", today()]})

    # Passed vs Failed checkpoints
    qc_results = frappe.db.sql(
        """
		SELECT 
			status,
			COUNT(*) as count
		FROM `tabQuality Control Checkpoint`
		WHERE DATE(creation) = CURDATE()
		GROUP BY status
	""",
        as_dict=True,
    )

    # Average inspection time
    avg_inspection_time = (
        frappe.db.sql(
            """
		SELECT AVG(TIMESTAMPDIFF(MINUTE, creation, modified)) as avg_minutes
		FROM `tabQuality Control Checkpoint`
		WHERE status = 'Passed'
		AND DATE(creation) = CURDATE()
	"""
        )[0][0]
        or 0
    )

    # Photos and documents uploaded today
    photos_uploaded = frappe.db.count("Quality Control Photo", {"creation": [">=", today()]})

    documents_uploaded = frappe.db.count("Quality Control Document", {"creation": [">=", today()]})

    return {
        "today_checkpoints": today_checkpoints,
        "qc_results": qc_results,
        "avg_inspection_time": flt(avg_inspection_time, 2),
        "photos_uploaded": photos_uploaded,
        "documents_uploaded": documents_uploaded,
    }
