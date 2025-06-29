# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import hashlib
import json
from datetime import datetime, timedelta

import requests

import frappe
from frappe import _
from frappe.model.document import Document


class SecurityMonitor(Document):
	def before_save(self):
		"""Generate audit hash and validate threat indicators"""
		self.validate_threat_indicators()
		self.calculate_risk_scores()
		self.generate_audit_hash()
		self.update_alert_status()

	def validate_threat_indicators(self):
		"""Validate and process threat indicators"""
		if not self.threat_indicators:
			return

		total_risk = 0
		critical_indicators = 0

		for indicator in self.threat_indicators:
			# Validate risk weight
			if indicator.risk_weight < 1 or indicator.risk_weight > 10:
				frappe.throw(_("Risk weight must be between 1 and 10"))

			# Count critical indicators
			if indicator.severity == "Critical":
				critical_indicators += 1

			total_risk += indicator.risk_weight

		# Auto-escalate if too many critical indicators
		if critical_indicators >= 3:
			self.risk_level = "Critical"
			self.auto_response_triggered = 1

	def calculate_risk_scores(self):
		"""Calculate composite risk scores from various factors"""
		# Location risk calculation
		location_risk = 0
		if self.vpn_detected:
			location_risk += 20
		if self.location_change_detected:
			location_risk += (self.distance_from_usual or 0) * 0.1
		if self.country_code and self.country_code != "OM":
			location_risk += 15

		self.location_risk_score = min(100, int(location_risk))

		# Behavioral risk calculation
		behavioral_risk = 0
		if self.unusual_activity_detected:
			behavioral_risk += 25
		if self.concurrent_sessions > 1:
			behavioral_risk += (self.concurrent_sessions - 1) * 10
		if self.activity_pattern in ["Unusual Hours", "Suspicious"]:
			behavioral_risk += 20
		if self.session_duration and self.session_duration > 480:  # > 8 hours
			behavioral_risk += 15

		self.behavioral_risk_score = min(100, int(behavioral_risk))

		# System risk calculation
		system_risk = 0
		if self.system_changes_detected:
			system_risk += 30
		if self.failed_validation_count > 0:
			system_risk += self.failed_validation_count * 5
		if self.license_validation_attempts > 10:
			system_risk += 20

		self.system_risk_score = min(100, int(system_risk))

		# Overall risk level determination
		max_risk = max(self.location_risk_score, self.behavioral_risk_score, self.system_risk_score)
		if max_risk >= 80:
			self.risk_level = "Critical"
		elif max_risk >= 60:
			self.risk_level = "High"
		elif max_risk >= 30:
			self.risk_level = "Medium"
		else:
			self.risk_level = "Low"

	def generate_audit_hash(self):
		"""Generate audit hash for integrity verification"""
		# Create hash data
		hash_data = {
			"workshop_code": self.workshop_code,
			"business_license": self.business_license,
			"monitor_date": str(self.monitor_date),
			"monitor_type": self.monitor_type,
			"risk_level": self.risk_level,
			"hardware_fingerprint_hash": self.hardware_fingerprint_hash or "",
			"ip_address": self.ip_address or "",
			"threat_count": len(self.threat_indicators) if self.threat_indicators else 0,
		}

		# Generate hash
		hash_string = json.dumps(hash_data, sort_keys=True)
		self.audit_hash = hashlib.sha256(hash_string.encode()).hexdigest()

		# Verification signature (simplified for demo)
		self.verification_signature = hashlib.sha256(
			f"{self.audit_hash}{frappe.session.user}".encode()
		).hexdigest()[:16]

	def update_alert_status(self):
		"""Update alert status based on risk level and triggers"""
		if self.risk_level in ["High", "Critical"] and self.alert_status == "No Alert":
			self.alert_status = "Alert Generated"

		if self.auto_response_triggered:
			self.add_automated_actions()

	def add_automated_actions(self):
		"""Add automated security actions based on threat level"""
		if not self.recommended_actions:
			self.recommended_actions = []

		# Critical risk actions
		if self.risk_level == "Critical":
			self.recommended_actions.append(
				{
					"action_type": "Immediate Block",
					"action_description": "Block access immediately due to critical security risk",
					"priority": "Urgent",
					"estimated_effort": "5 Minutes",
					"responsible_party": "System Administrator",
				}
			)

		# High risk actions
		elif self.risk_level == "High":
			self.recommended_actions.append(
				{
					"action_type": "Additional Verification",
					"action_description": "Require additional authentication steps",
					"priority": "High",
					"estimated_effort": "15 Minutes",
					"responsible_party": "Security Team",
				}
			)

		# Location-based actions
		if self.location_change_detected and self.distance_from_usual > 100:
			self.recommended_actions.append(
				{
					"action_type": "Manual Investigation",
					"action_description": f"Investigate location change of {self.distance_from_usual:.1f}km",
					"priority": "Medium",
					"estimated_effort": "30 Minutes",
					"responsible_party": "Security Team",
				}
			)

	def after_insert(self):
		"""Post-creation actions"""
		self.send_security_alerts()
		self.log_to_audit_system()

	def send_security_alerts(self):
		"""Send alerts for high-risk events"""
		if self.risk_level in ["High", "Critical"]:
			try:
				# Send email alert
				frappe.sendmail(
					recipients=["security@universal-workshop.om"],
					subject=f"Security Alert: {self.risk_level} Risk Detected",
					message=self.get_alert_message(),
					header=["Security Alert", "red"],
				)

				# Log SMS alert (implementation would depend on SMS provider)
				self.send_sms_alert()

			except Exception as e:
				frappe.log_error(f"Failed to send security alert: {e!s}")

	def get_alert_message(self):
		"""Generate alert message content"""
		message = f"""
        Security Alert Details:

        Workshop: {self.workshop_code}
        Business License: {self.business_license}
        Risk Level: {self.risk_level}
        Monitor Type: {self.monitor_type}
        Detected At: {self.monitor_date}

        Location Information:
        - IP Address: {self.ip_address or "Unknown"}
        - Geographic Location: {self.geographic_location or "Unknown"}
        - VPN Detected: {"Yes" if self.vpn_detected else "No"}

        Risk Scores:
        - Location Risk: {self.location_risk_score}/100
        - Behavioral Risk: {self.behavioral_risk_score}/100
        - System Risk: {self.system_risk_score}/100

        Threat Indicators: {len(self.threat_indicators) if self.threat_indicators else 0}

        Immediate action may be required.
        """
		return message

	def send_sms_alert(self):
		"""Send SMS alert for critical threats"""
		if self.risk_level == "Critical":
			# This would integrate with SMS provider
			# For now, just log the attempt
			frappe.log_error(
				f"SMS Alert triggered for {self.workshop_code} - {self.risk_level} risk", "SMS Security Alert"
			)

	def log_to_audit_system(self):
		"""Log security event to audit system"""
		try:
			# Create audit log entry
			audit_log = frappe.new_doc("License Audit Log")
			audit_log.workshop_code = self.workshop_code
			audit_log.business_license = self.business_license
			audit_log.event_type = "Security Monitor"
			audit_log.event_description = f"{self.monitor_type} - {self.risk_level} Risk"
			audit_log.severity_level = self.risk_level
			audit_log.system_component = "Security Monitor"
			audit_log.event_data = json.dumps(
				{
					"monitor_id": self.name,
					"threat_count": len(self.threat_indicators) if self.threat_indicators else 0,
					"location_risk": self.location_risk_score,
					"behavioral_risk": self.behavioral_risk_score,
					"system_risk": self.system_risk_score,
				}
			)
			audit_log.insert()

		except Exception as e:
			frappe.log_error(f"Failed to create audit log: {e!s}")


# Static methods for external monitoring integration
@frappe.whitelist()
def create_security_monitor(workshop_code, business_license, monitor_type, **kwargs):
	"""Create security monitor entry from external systems"""
	try:
		monitor = frappe.new_doc("Security Monitor")
		monitor.workshop_code = workshop_code
		monitor.business_license = business_license
		monitor.monitor_type = monitor_type
		monitor.monitor_date = datetime.now()

		# Set optional fields
		for key, value in kwargs.items():
			if hasattr(monitor, key):
				setattr(monitor, key, value)

		monitor.insert()
		return monitor.name

	except Exception as e:
		frappe.log_error(f"Failed to create security monitor: {e!s}")
		return None


@frappe.whitelist()
def get_security_dashboard_data(workshop_code=None, days=7):
	"""Get security dashboard data for monitoring interface"""
	try:
		filters = {"monitor_date": [">=", datetime.now() - timedelta(days=days)]}
		if workshop_code:
			filters["workshop_code"] = workshop_code

		monitors = frappe.get_list(
			"Security Monitor",
			filters=filters,
			fields=[
				"name",
				"workshop_code",
				"monitor_type",
				"risk_level",
				"monitor_date",
				"alert_status",
				"location_risk_score",
				"behavioral_risk_score",
				"system_risk_score",
			],
			order_by="monitor_date desc",
		)

		# Calculate summary statistics
		risk_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
		total_monitors = len(monitors)

		for monitor in monitors:
			risk_counts[monitor.risk_level] += 1

		return {
			"monitors": monitors,
			"summary": {
				"total_monitors": total_monitors,
				"risk_distribution": risk_counts,
				"critical_alerts": risk_counts["Critical"],
				"high_risk_percentage": (risk_counts["High"] + risk_counts["Critical"])
				/ max(total_monitors, 1)
				* 100,
			},
		}

	except Exception as e:
		frappe.log_error(f"Failed to get security dashboard data: {e!s}")
		return {"monitors": [], "summary": {}}


@frappe.whitelist()
def resolve_security_alert(monitor_id, resolution_notes):
	"""Resolve a security alert with investigation notes"""
	try:
		monitor = frappe.get_doc("Security Monitor", monitor_id)
		monitor.alert_status = "Resolved"
		monitor.investigation_notes = resolution_notes
		monitor.resolved_by = frappe.session.user
		monitor.resolution_date = datetime.now()
		monitor.save()

		return {"success": True, "message": "Security alert resolved successfully"}

	except Exception as e:
		frappe.log_error(f"Failed to resolve security alert: {e!s}")
		return {"success": False, "message": str(e)}
