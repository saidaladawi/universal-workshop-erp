"""
Offline Grace Period API Integration
Provides REST API endpoints for offline session management
"""

from typing import Dict, Optional

import frappe
from frappe import _
from frappe.utils import now_datetime
from universal_workshop.license_management.connectivity_monitor import get_connectivity_monitor
from universal_workshop.license_management.offline_manager import OfflineGracePeriodManager


@frappe.whitelist()
def get_offline_status(workshop_code: str) -> dict:
	"""
	Get comprehensive offline status for a workshop

	Args:
	    workshop_code (str): Workshop identifier

	Returns:
	    Dict: Complete offline status information
	"""
	try:
		from universal_workshop.license_management.doctype.offline_session.offline_session import (
			get_active_session,
		)

		# Get active offline session
		offline_session = get_active_session(workshop_code)

		# Get connectivity status
		connectivity_monitor = get_connectivity_monitor()
		connectivity_status = connectivity_monitor.get_connectivity_status(workshop_code)

		if offline_session:
			session_summary = offline_session.get_session_summary()

			return {
				"success": True,
				"has_offline_session": True,
				"offline_session": session_summary,
				"connectivity": connectivity_status,
				"can_operate_offline": not session_summary["is_expired"],
				"requires_online_validation": session_summary["is_expired"],
				"status_message": _("Operating in offline mode")
				if not session_summary["is_expired"]
				else _("Offline grace period expired - online validation required"),
			}
		else:
			return {
				"success": True,
				"has_offline_session": False,
				"offline_session": None,
				"connectivity": connectivity_status,
				"can_operate_offline": False,
				"requires_online_validation": True,
				"status_message": _("Online mode - no offline session active"),
			}

	except Exception as e:
		frappe.log_error(f"Failed to get offline status: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "status_message": _("Failed to retrieve offline status")}


@frappe.whitelist()
def initiate_offline_mode(workshop_code: str, hardware_fingerprint: str, current_jwt_token: str) -> dict:
	"""
	Initiate offline mode for a workshop

	Args:
	    workshop_code (str): Workshop identifier
	    hardware_fingerprint (str): Current hardware fingerprint
	    current_jwt_token (str): Current valid JWT token

	Returns:
	    Dict: Offline mode initiation result
	"""
	try:
		manager = OfflineGracePeriodManager()

		# Start offline session
		result = manager.start_offline_session(workshop_code, hardware_fingerprint, current_jwt_token)

		if result.get("success"):
			# Start connectivity monitoring
			connectivity_monitor = get_connectivity_monitor()
			monitoring_result = connectivity_monitor.start_monitoring(workshop_code)

			return {
				"success": True,
				"offline_session_id": result.get("offline_session_id"),
				"grace_period_hours": result.get("grace_period_remaining_hours"),
				"expires_at": result.get("expires_at"),
				"connectivity_monitoring": monitoring_result.get("success", False),
				"message": _("Offline mode activated successfully"),
			}
		else:
			return {
				"success": False,
				"error": result.get("error"),
				"requires_online_validation": result.get("requires_online_validation", False),
				"message": _("Failed to activate offline mode"),
			}

	except Exception as e:
		frappe.log_error(f"Failed to initiate offline mode: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "message": _("Error initiating offline mode")}


@frappe.whitelist()
def validate_offline_operation(workshop_code: str, hardware_fingerprint: str) -> dict:
	"""
	Validate current offline operation

	Args:
	    workshop_code (str): Workshop identifier
	    hardware_fingerprint (str): Current hardware fingerprint

	Returns:
	    Dict: Validation result
	"""
	try:
		manager = OfflineGracePeriodManager()

		# Validate offline session
		result = manager.validate_offline_session(workshop_code, hardware_fingerprint)

		if result.get("valid"):
			return {
				"success": True,
				"valid": True,
				"grace_period_remaining_hours": result.get("grace_period_remaining_hours"),
				"grace_period_remaining_minutes": result.get("grace_period_remaining_minutes"),
				"session_id": result.get("session_id"),
				"last_online": result.get("last_online"),
				"expires_at": result.get("expires_at"),
				"message": _("Offline operation validated successfully"),
			}
		else:
			return {
				"success": False,
				"valid": False,
				"error": result.get("error"),
				"requires_online_validation": result.get("requires_online_validation", False),
				"security_violation": result.get("security_violation", False),
				"grace_period_expired": result.get("grace_period_expired", False),
				"message": _("Offline operation validation failed"),
			}

	except Exception as e:
		frappe.log_error(f"Failed to validate offline operation: {e!s}", "Offline API")
		return {
			"success": False,
			"valid": False,
			"error": str(e),
			"message": _("Error validating offline operation"),
		}


@frappe.whitelist()
def terminate_offline_mode(workshop_code: str, online_validation_success: bool = False) -> dict:
	"""
	Terminate offline mode and return to online operation

	Args:
	    workshop_code (str): Workshop identifier
	    online_validation_success (bool): Whether online validation was successful

	Returns:
	    Dict: Termination result
	"""
	try:
		manager = OfflineGracePeriodManager()

		# End offline session
		result = manager.end_offline_session(workshop_code, online_validation_success)

		if result.get("success"):
			# Stop connectivity monitoring
			connectivity_monitor = get_connectivity_monitor()
			monitoring_result = connectivity_monitor.stop_monitoring(workshop_code)

			return {
				"success": True,
				"session_duration_hours": result.get("session_duration_hours"),
				"online_validation_success": result.get("online_validation_success"),
				"total_activities": result.get("total_activities"),
				"connectivity_monitoring_stopped": monitoring_result.get("success", False),
				"message": _("Offline mode terminated successfully"),
			}
		else:
			return {
				"success": False,
				"error": result.get("error"),
				"message": _("Failed to terminate offline mode"),
			}

	except Exception as e:
		frappe.log_error(f"Failed to terminate offline mode: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "message": _("Error terminating offline mode")}


@frappe.whitelist()
def get_connectivity_status(workshop_code: str) -> dict:
	"""
	Get current connectivity status

	Args:
	    workshop_code (str): Workshop identifier

	Returns:
	    Dict: Connectivity status
	"""
	try:
		connectivity_monitor = get_connectivity_monitor()
		status = connectivity_monitor.get_connectivity_status(workshop_code)

		# Perform immediate connectivity check
		connectivity_check = connectivity_monitor.check_connectivity(quick_check=True)

		return {
			"success": True,
			"monitoring_status": status,
			"current_connectivity": connectivity_check,
			"message": _("Connectivity status retrieved successfully"),
		}

	except Exception as e:
		frappe.log_error(f"Failed to get connectivity status: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "message": _("Error retrieving connectivity status")}


@frappe.whitelist()
def get_offline_session_history(workshop_code: str, limit: int = 10) -> dict:
	"""
	Get offline session history for a workshop

	Args:
	    workshop_code (str): Workshop identifier
	    limit (int): Maximum number of sessions to return

	Returns:
	    Dict: Session history
	"""
	try:
		sessions = frappe.get_all(
			"Offline Session",
			filters={"workshop_code": workshop_code},
			fields=[
				"name",
				"started_at",
				"expires_at",
				"ended_at",
				"status",
				"online_validation_success",
				"total_offline_hours",
				"activity_count",
			],
			order_by="creation desc",
			limit=limit,
		)

		# Calculate session statistics
		total_sessions = len(sessions)
		successful_validations = sum(1 for s in sessions if s.online_validation_success)
		total_offline_hours = sum(s.total_offline_hours or 0 for s in sessions)

		return {
			"success": True,
			"sessions": sessions,
			"statistics": {
				"total_sessions": total_sessions,
				"successful_validations": successful_validations,
				"success_rate": round((successful_validations / max(total_sessions, 1)) * 100, 2),
				"total_offline_hours": round(total_offline_hours, 2),
				"average_session_hours": round(total_offline_hours / max(total_sessions, 1), 2),
			},
			"message": _("Session history retrieved successfully"),
		}

	except Exception as e:
		frappe.log_error(f"Failed to get offline session history: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "message": _("Error retrieving session history")}


@frappe.whitelist()
def force_connectivity_check() -> dict:
	"""
	Force an immediate comprehensive connectivity check

	Returns:
	    Dict: Connectivity check result
	"""
	try:
		connectivity_monitor = get_connectivity_monitor()
		result = connectivity_monitor.check_connectivity(quick_check=False)

		return {
			"success": True,
			"connectivity_result": result,
			"connected": result.get("connected", False),
			"response_time": result.get("response_time"),
			"method": result.get("method"),
			"details": result.get("details", {}),
			"message": _("Connectivity check completed successfully"),
		}

	except Exception as e:
		frappe.log_error(f"Failed to perform connectivity check: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "message": _("Error performing connectivity check")}


# Dashboard data for offline management
@frappe.whitelist()
def get_offline_dashboard_data(workshop_code: str) -> dict:
	"""
	Get comprehensive dashboard data for offline management

	Args:
	    workshop_code (str): Workshop identifier

	Returns:
	    Dict: Dashboard data
	"""
	try:
		# Get current status
		offline_status = get_offline_status(workshop_code)

		# Get recent session history
		session_history = get_offline_session_history(workshop_code, limit=5)

		# Get connectivity status
		connectivity_status = get_connectivity_status(workshop_code)

		# Calculate grace period status
		grace_period_info = {}
		if offline_status.get("has_offline_session"):
			session = offline_status["offline_session"]
			remaining_time = session.get("remaining_time", {})

			if not remaining_time.get("expired", True):
				total_hours = 24  # Standard grace period
				remaining_hours = remaining_time.get("remaining_hours", 0)
				used_hours = total_hours - remaining_hours

				grace_period_info = {
					"total_hours": total_hours,
					"used_hours": used_hours,
					"remaining_hours": remaining_hours,
					"percentage_used": round((used_hours / total_hours) * 100, 1),
					"status": "active"
					if remaining_hours > 2
					else "warning"
					if remaining_hours > 0
					else "expired",
				}

		return {
			"success": True,
			"current_status": offline_status,
			"session_history": session_history,
			"connectivity_status": connectivity_status,
			"grace_period_info": grace_period_info,
			"timestamp": now_datetime().isoformat(),
			"message": _("Dashboard data retrieved successfully"),
		}

	except Exception as e:
		frappe.log_error(f"Failed to get offline dashboard data: {e!s}", "Offline API")
		return {"success": False, "error": str(e), "message": _("Error retrieving dashboard data")}
