"""
Offline Session DocType Controller
Manages offline license validation sessions with security features
"""

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime, now_datetime


class OfflineSession(Document):
	"""
	Controller for Offline Session DocType
	Handles offline session validation and security
	"""

	def validate(self):
		"""Validate offline session data"""
		self.validate_workshop_code()
		self.validate_session_timing()
		self.validate_security_hash()

	def before_save(self):
		"""Pre-save validations and data preparation"""
		if not self.last_validation_at:
			self.last_validation_at = now_datetime()

		if not self.activity_count:
			self.activity_count = 0

	def on_update(self):
		"""Post-update operations"""
		# Log session updates for audit
		if self.has_value_changed("status"):
			self._log_status_change()

	def validate_workshop_code(self):
		"""Validate workshop code format and existence"""
		if not self.workshop_code:
			frappe.throw(_("Workshop Code is required"))

		# Check workshop code format (WS-YYYY-NNNN)
		import re

		if not re.match(r"^WS-\d{4}-\d{4}$", self.workshop_code):
			frappe.throw(_("Invalid Workshop Code format. Expected: WS-YYYY-NNNN"))

	def validate_session_timing(self):
		"""Validate session start/end timing logic"""
		if not self.started_at:
			frappe.throw(_("Session start time is required"))

		if not self.expires_at:
			frappe.throw(_("Session expiration time is required"))

		# Validate expiration is after start
		if get_datetime(self.expires_at) <= get_datetime(self.started_at):
			frappe.throw(_("Session expiration must be after start time"))

		# Validate ended_at if provided
		if self.ended_at and get_datetime(self.ended_at) < get_datetime(self.started_at):
			frappe.throw(_("Session end time cannot be before start time"))

		# Check for reasonable grace period (not more than 48 hours)
		duration_hours = (
			get_datetime(self.expires_at) - get_datetime(self.started_at)
		).total_seconds() / 3600
		if duration_hours > 48:
			frappe.throw(_("Offline grace period cannot exceed 48 hours"))

	def validate_security_hash(self):
		"""Validate session security hash integrity"""
		if self.secure_hash and self.session_data:
			try:
				# Verify hash matches session data
				session_data = json.loads(self.session_data)
				expected_hash = session_data.get("secure_hash")

				if expected_hash and expected_hash != self.secure_hash:
					frappe.throw(_("Session security hash mismatch detected"))

			except json.JSONDecodeError:
				frappe.throw(_("Invalid session data format"))

	def is_expired(self) -> bool:
		"""Check if offline session has expired"""
		current_time = now_datetime()
		return current_time >= get_datetime(self.expires_at)

	def get_remaining_time(self) -> dict:
		"""Get remaining time in the grace period"""
		if self.is_expired():
			return {"expired": True, "remaining_hours": 0, "remaining_minutes": 0}

		current_time = now_datetime()
		time_remaining = get_datetime(self.expires_at) - current_time

		remaining_hours = int(time_remaining.total_seconds() / 3600)
		remaining_minutes = int((time_remaining.total_seconds() % 3600) / 60)

		return {
			"expired": False,
			"remaining_hours": remaining_hours,
			"remaining_minutes": remaining_minutes,
			"total_remaining_seconds": int(time_remaining.total_seconds()),
		}

	def update_activity(self):
		"""Update session activity timestamp and count"""
		self.last_validation_at = now_datetime()
		self.activity_count = (self.activity_count or 0) + 1
		self.save(ignore_permissions=True)

	def verify_hardware_fingerprint(self, current_fingerprint: str) -> bool:
		"""Verify hardware fingerprint consistency"""
		if not self.hardware_fingerprint_partial:
			return False

		# Compare partial fingerprints (first 32 characters)
		current_partial = current_fingerprint[:32] if current_fingerprint else ""
		return current_partial == self.hardware_fingerprint_partial

	def get_session_summary(self) -> dict:
		"""Get comprehensive session summary"""
		duration_data = self._calculate_session_duration()
		remaining_time = self.get_remaining_time()

		return {
			"session_id": self.name,
			"workshop_code": self.workshop_code,
			"status": self.status,
			"started_at": self.started_at,
			"expires_at": self.expires_at,
			"ended_at": self.ended_at,
			"duration": duration_data,
			"remaining_time": remaining_time,
			"activity_count": self.activity_count or 0,
			"last_validation": self.last_validation_at,
			"online_validation_success": self.online_validation_success,
			"is_expired": self.is_expired(),
		}

	def _calculate_session_duration(self) -> dict:
		"""Calculate session duration metrics"""
		start_time = get_datetime(self.started_at)
		end_time = get_datetime(self.ended_at) if self.ended_at else now_datetime()

		duration = end_time - start_time
		hours = duration.total_seconds() / 3600

		return {
			"total_hours": round(hours, 2),
			"total_days": round(hours / 24, 2),
			"total_seconds": int(duration.total_seconds()),
			"is_completed": bool(self.ended_at),
		}

	def _log_status_change(self):
		"""Log status changes for audit"""
		try:
			from universal_workshop.license_management.doctype.license_audit_log.license_audit_log import (
				create_audit_log,
			)

			create_audit_log(
				event_type="offline_session_status_change",
				severity="medium",
				message=f"Offline session status changed to: {self.status}",
				event_data={
					"session_id": self.name,
					"workshop_code": self.workshop_code,
					"old_status": self.get_db_value("status"),
					"new_status": self.status,
					"timestamp": now_datetime().isoformat(),
				},
				workshop_code=self.workshop_code,
			)

		except Exception as e:
			frappe.log_error(f"Failed to log offline session status change: {e!s}", "Offline Session Audit")


# Utility functions for offline session management
def get_active_session(workshop_code: str):
	"""Get active offline session for workshop"""
	filters = {"workshop_code": workshop_code, "status": "active"}

	if frappe.db.exists("Offline Session", filters):
		return frappe.get_doc("Offline Session", filters)
	return None


def cleanup_expired_sessions():
	"""Clean up expired offline sessions (scheduled job)"""
	try:
		# Mark expired sessions
		expired_sessions = frappe.get_all(
			"Offline Session",
			filters={"status": "active", "expires_at": ["<", now_datetime()]},
			fields=["name", "workshop_code"],
		)

		for session in expired_sessions:
			doc = frappe.get_doc("Offline Session", session.name)
			doc.status = "expired"
			doc.ended_at = now_datetime()
			doc.save(ignore_permissions=True)

		# Delete old completed/expired sessions (keep last 50 per workshop)
		workshops = frappe.get_all(
			"Offline Session", filters={"status": ["!=", "active"]}, fields=["workshop_code"], distinct=True
		)

		for workshop in workshops:
			old_sessions = frappe.get_all(
				"Offline Session",
				filters={"workshop_code": workshop.workshop_code, "status": ["!=", "active"]},
				order_by="creation desc",
				start=50,  # Keep latest 50
			)

			for session in old_sessions:
				frappe.delete_doc("Offline Session", session.name, force=True)

		frappe.db.commit()

	except Exception as e:
		frappe.log_error(f"Offline session cleanup failed: {e!s}", "Offline Session Cleanup")


# Scheduled function for cleanup (add to hooks.py)
def scheduled_offline_session_cleanup():
	"""Scheduled cleanup function"""
	cleanup_expired_sessions()
