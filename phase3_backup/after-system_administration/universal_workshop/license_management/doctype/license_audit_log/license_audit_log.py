# License Audit Log DocType Controller
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


class LicenseAuditLog(Document):
	"""License Audit Log DocType for security monitoring"""

	def validate(self):
		"""Validate audit log entry"""
		self.validate_event_data()
		self.validate_severity()

	def validate_event_data(self):
		"""Ensure event data is valid JSON if provided"""
		if self.event_data:
			try:
				json.loads(self.event_data)
			except json.JSONDecodeError:
				frappe.throw("Event data must be valid JSON format")

	def validate_severity(self):
		"""Validate severity level"""
		valid_severities = ["low", "medium", "high", "critical"]
		if self.severity not in valid_severities:
			frappe.throw(f"Severity must be one of: {', '.join(valid_severities)}")

	def before_insert(self):
		"""Set timestamp if not provided"""
		if not self.timestamp:
			self.timestamp = frappe.utils.now()

		# Capture request information if available
		if (
			hasattr(frappe.local, "request")
			and frappe.local.request
			and not self.ip_address
			and hasattr(frappe.local, "request_ip")
		):
			self.ip_address = frappe.local.request_ip

		if not self.user_agent:
			self.user_agent = frappe.get_request_header("User-Agent", "")

	def after_insert(self):
		"""Handle post-insert actions"""
		# Alert on high severity events
		if self.severity in ["high", "critical"]:
			self.send_security_alert()

	def send_security_alert(self):
		"""Send security alert for high-severity events"""
		try:
			# Get system administrators
			admins = frappe.get_all(
				"User",
				filters={"role_profile_name": "System Manager", "enabled": 1},
				fields=["email", "name"],
			)

			if admins:
				subject = f"Security Alert: {self.event_type}"
				message = f"""
                Security Event Detected:

                Event Type: {self.event_type}
                Severity: {self.severity}
                Timestamp: {self.timestamp}
                Workshop: {self.workshop_id or "Unknown"}
                IP Address: {self.ip_address or "Unknown"}

                Event Data: {self.event_data or "None"}
                Description: {self.description or "None"}

                Please investigate this security event immediately.
                """

				for admin in admins:
					frappe.sendmail(recipients=[admin.email], subject=subject, message=message, delayed=True)
		except Exception as e:
			frappe.log_error(f"Failed to send security alert: {e!s}")

	@staticmethod
	def log_event(event_type, event_data=None, workshop_id=None, severity="medium", description=None):
		"""Static method to easily log security events"""
		try:
			log_entry = frappe.new_doc("License Audit Log")
			log_entry.event_type = event_type
			log_entry.workshop_id = workshop_id
			log_entry.severity = severity
			log_entry.description = description

			if event_data:
				log_entry.event_data = (
					json.dumps(event_data) if isinstance(event_data, dict) else str(event_data)
				)

			log_entry.insert(ignore_permissions=True)
			frappe.db.commit()

		except Exception as e:
			frappe.log_error(f"Failed to create audit log entry: {e!s}")

	@staticmethod
	def cleanup_old_logs(days_to_keep=90):
		"""Clean up old audit logs to manage database size"""
		cutoff_date = frappe.utils.add_days(frappe.utils.today(), -days_to_keep)

		old_logs = frappe.get_all(
			"License Audit Log", filters={"timestamp": ["<", cutoff_date]}, pluck="name"
		)

		for log_name in old_logs:
			frappe.delete_doc("License Audit Log", log_name, ignore_permissions=True)

		if old_logs:
			frappe.db.commit()
			frappe.logger().info(f"Cleaned up {len(old_logs)} old audit log entries")

		return len(old_logs)
