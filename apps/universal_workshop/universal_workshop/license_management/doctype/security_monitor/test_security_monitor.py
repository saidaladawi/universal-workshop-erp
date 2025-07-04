# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import unittest
from datetime import datetime, timedelta

import frappe
from universal_workshop.license_management.doctype.security_monitor.security_monitor import (
	create_security_monitor,
	get_security_dashboard_data,
	resolve_security_alert,
)


class TestSecurityMonitor(unittest.TestCase):
	def setUp(self):
		"""Setup test data"""
		self.test_workshop_code = "WS-2024-TEST"
		self.test_business_license = "1234567"
		self.test_monitor_data = {
			"workshop_code": self.test_workshop_code,
			"business_license": self.test_business_license,
			"monitor_type": "Login Activity",
			"ip_address": "192.168.1.100",
			"geographic_location": "Muscat, Oman",
			"country_code": "OM",
			"hardware_fingerprint_hash": "test_fingerprint_hash",
		}

		# Clean up any existing test data
		frappe.db.delete("Security Monitor", {"workshop_code": self.test_workshop_code})
		frappe.db.delete("License Audit Log", {"workshop_code": self.test_workshop_code})

	def tearDown(self):
		"""Clean up test data"""
		frappe.db.delete("Security Monitor", {"workshop_code": self.test_workshop_code})
		frappe.db.delete("License Audit Log", {"workshop_code": self.test_workshop_code})

	def test_basic_security_monitor_creation(self):
		"""Test basic security monitor creation"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)
		monitor.insert()

		# Verify creation
		self.assertTrue(monitor.name)
		self.assertEqual(monitor.workshop_code, self.test_workshop_code)
		self.assertEqual(monitor.risk_level, "Low")  # Default for normal activity
		self.assertTrue(monitor.audit_hash)

	def test_risk_score_calculation(self):
		"""Test risk score calculation algorithms"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Test location risk
		monitor.vpn_detected = 1
		monitor.location_change_detected = 1
		monitor.distance_from_usual = 50
		monitor.country_code = "US"  # Non-Oman country

		# Test behavioral risk
		monitor.unusual_activity_detected = 1
		monitor.concurrent_sessions = 3
		monitor.activity_pattern = "Suspicious"
		monitor.session_duration = 600  # 10 hours

		# Test system risk
		monitor.system_changes_detected = 1
		monitor.failed_validation_count = 2
		monitor.license_validation_attempts = 15

		monitor.insert()

		# Verify risk calculations
		self.assertGreater(monitor.location_risk_score, 0)
		self.assertGreater(monitor.behavioral_risk_score, 0)
		self.assertGreater(monitor.system_risk_score, 0)
		self.assertEqual(monitor.risk_level, "Critical")  # Should escalate to critical

	def test_threat_indicator_validation(self):
		"""Test threat indicator processing"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Add threat indicators
		monitor.threat_indicators = [
			{
				"indicator_type": "Suspicious IP",
				"indicator_value": "192.168.1.100",
				"risk_weight": 8,
				"severity": "High",
				"confidence_level": "High",
				"detected_at": datetime.now(),
				"description": "IP address from suspicious range",
				"source": "Automated System",
			},
			{
				"indicator_type": "Multiple Failed Attempts",
				"indicator_value": "5 attempts",
				"risk_weight": 6,
				"severity": "Medium",
				"confidence_level": "Certain",
				"detected_at": datetime.now(),
				"description": "Multiple authentication failures",
				"source": "Behavioral Analysis",
			},
		]

		monitor.insert()

		# Verify threat processing
		self.assertEqual(len(monitor.threat_indicators), 2)
		self.assertIn(monitor.risk_level, ["Medium", "High", "Critical"])

	def test_critical_threat_auto_escalation(self):
		"""Test automatic escalation for critical threats"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Add multiple critical indicators
		monitor.threat_indicators = [
			{
				"indicator_type": "System Tampering",
				"indicator_value": "Hardware modification detected",
				"risk_weight": 10,
				"severity": "Critical",
				"confidence_level": "Certain",
				"detected_at": datetime.now(),
				"source": "Automated System",
			},
			{
				"indicator_type": "Geographic Velocity",
				"indicator_value": "Impossible travel detected",
				"risk_weight": 9,
				"severity": "Critical",
				"confidence_level": "High",
				"detected_at": datetime.now(),
				"source": "Geographic Analysis",
			},
			{
				"indicator_type": "License Violation",
				"indicator_value": "Concurrent license usage",
				"risk_weight": 10,
				"severity": "Critical",
				"confidence_level": "Certain",
				"detected_at": datetime.now(),
				"source": "Automated System",
			},
		]

		monitor.insert()

		# Verify auto-escalation
		self.assertEqual(monitor.risk_level, "Critical")
		self.assertEqual(monitor.auto_response_triggered, 1)
		self.assertEqual(monitor.alert_status, "Alert Generated")
		self.assertTrue(len(monitor.recommended_actions) > 0)

	def test_automated_action_generation(self):
		"""Test automated security action generation"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)
		monitor.risk_level = "Critical"
		monitor.location_change_detected = 1
		monitor.distance_from_usual = 150
		monitor.insert()

		# Verify automated actions
		actions = monitor.recommended_actions
		self.assertTrue(len(actions) >= 1)

		# Check for immediate block action
		block_action = next((a for a in actions if a.action_type == "Immediate Block"), None)
		self.assertIsNotNone(block_action)
		self.assertEqual(block_action.priority, "Urgent")

		# Check for investigation action
		investigate_action = next((a for a in actions if a.action_type == "Manual Investigation"), None)
		self.assertIsNotNone(investigate_action)

	def test_audit_hash_generation(self):
		"""Test audit hash generation and integrity"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)
		monitor.insert()

		# Verify hash generation
		self.assertTrue(monitor.audit_hash)
		self.assertTrue(monitor.verification_signature)
		self.assertEqual(monitor.integrity_verified, 1)
		self.assertEqual(monitor.tamper_evident, 0)

		# Verify hash consistency
		original_hash = monitor.audit_hash
		monitor.reload()
		self.assertEqual(monitor.audit_hash, original_hash)

	def test_security_alert_generation(self):
		"""Test security alert creation and processing"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)
		monitor.risk_level = "High"
		monitor.insert()

		# Verify alert generation
		self.assertEqual(monitor.alert_status, "Alert Generated")

		# Verify audit log creation
		audit_logs = frappe.get_list(
			"License Audit Log",
			filters={"workshop_code": self.test_workshop_code, "event_type": "Security Monitor"},
		)
		self.assertTrue(len(audit_logs) > 0)

	def test_api_create_security_monitor(self):
		"""Test API function for creating security monitors"""
		monitor_id = create_security_monitor(
			workshop_code=self.test_workshop_code,
			business_license=self.test_business_license,
			monitor_type="Behavioral Analysis",
			risk_level="Medium",
			unusual_activity_detected=1,
		)

		self.assertIsNotNone(monitor_id)

		# Verify creation
		monitor = frappe.get_doc("Security Monitor", monitor_id)
		self.assertEqual(monitor.workshop_code, self.test_workshop_code)
		self.assertEqual(monitor.monitor_type, "Behavioral Analysis")
		self.assertEqual(monitor.unusual_activity_detected, 1)

	def test_dashboard_data_retrieval(self):
		"""Test security dashboard data API"""
		# Create test monitors
		for i in range(3):
			monitor = frappe.new_doc("Security Monitor")
			monitor.update(self.test_monitor_data)
			monitor.monitor_type = f"Test Type {i}"
			monitor.risk_level = ["Low", "Medium", "High"][i]
			monitor.insert()

		# Test dashboard data
		dashboard_data = get_security_dashboard_data(workshop_code=self.test_workshop_code)

		self.assertIn("monitors", dashboard_data)
		self.assertIn("summary", dashboard_data)
		self.assertEqual(dashboard_data["summary"]["total_monitors"], 3)
		self.assertEqual(dashboard_data["summary"]["risk_distribution"]["High"], 1)

	def test_alert_resolution(self):
		"""Test security alert resolution"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)
		monitor.risk_level = "High"
		monitor.alert_status = "Alert Generated"
		monitor.insert()

		# Resolve alert
		result = resolve_security_alert(monitor.name, "Investigated and resolved - false positive")

		self.assertTrue(result["success"])

		# Verify resolution
		monitor.reload()
		self.assertEqual(monitor.alert_status, "Resolved")
		self.assertEqual(monitor.resolved_by, frappe.session.user)
		self.assertIsNotNone(monitor.resolution_date)
		self.assertIn("false positive", monitor.investigation_notes)

	def test_geographic_analysis(self):
		"""Test geographic-based threat detection"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Test foreign country access
		monitor.country_code = "RU"  # Russia
		monitor.vpn_detected = 1
		monitor.geographic_location = "Moscow, Russia"
		monitor.distance_from_usual = 500

		monitor.insert()

		# Verify geographic risk assessment
		self.assertGreater(monitor.location_risk_score, 30)  # Should have significant location risk
		self.assertIn(monitor.risk_level, ["Medium", "High", "Critical"])

	def test_behavioral_pattern_analysis(self):
		"""Test behavioral pattern detection"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Test unusual behavioral patterns
		monitor.activity_pattern = "Unusual Hours"
		monitor.session_duration = 720  # 12 hours
		monitor.concurrent_sessions = 4
		monitor.unusual_activity_detected = 1

		monitor.insert()

		# Verify behavioral analysis
		self.assertGreater(monitor.behavioral_risk_score, 40)
		self.assertIn(monitor.risk_level, ["Medium", "High", "Critical"])

	def test_system_integrity_monitoring(self):
		"""Test system integrity and tampering detection"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Test system tampering indicators
		monitor.system_changes_detected = 1
		monitor.failed_validation_count = 5
		monitor.license_validation_attempts = 25
		monitor.hardware_fingerprint_hash = "modified_fingerprint_hash"

		monitor.insert()

		# Verify system risk assessment
		self.assertGreater(monitor.system_risk_score, 50)
		self.assertIn(monitor.risk_level, ["High", "Critical"])

	def test_concurrent_threat_handling(self):
		"""Test handling of multiple concurrent threats"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)

		# Multiple threat vectors
		monitor.vpn_detected = 1
		monitor.location_change_detected = 1
		monitor.unusual_activity_detected = 1
		monitor.system_changes_detected = 1
		monitor.concurrent_sessions = 5
		monitor.failed_validation_count = 3

		monitor.insert()

		# Verify comprehensive threat assessment
		self.assertEqual(monitor.risk_level, "Critical")
		self.assertEqual(monitor.auto_response_triggered, 1)
		self.assertTrue(len(monitor.recommended_actions) >= 2)

	def test_arabic_location_support(self):
		"""Test Arabic location name handling"""
		monitor = frappe.new_doc("Security Monitor")
		monitor.update(self.test_monitor_data)
		monitor.geographic_location = "مسقط، عمان"  # Arabic location
		monitor.city = "مسقط"

		monitor.insert()

		# Verify Arabic location handling
		self.assertEqual(monitor.geographic_location, "مسقط، عمان")
		self.assertEqual(monitor.city, "مسقط")
		self.assertTrue(monitor.audit_hash)  # Should handle Unicode in hash generation

	def test_performance_monitoring(self):
		"""Test system performance under load"""
		import time

		start_time = time.time()

		# Create multiple monitors rapidly
		monitor_ids = []
		for i in range(10):
			monitor = frappe.new_doc("Security Monitor")
			monitor.update(self.test_monitor_data)
			monitor.workshop_code = f"WS-PERF-{i}"
			monitor.insert()
			monitor_ids.append(monitor.name)

		end_time = time.time()

		# Verify performance (should complete within reasonable time)
		self.assertLess(end_time - start_time, 10)  # Should complete within 10 seconds

		# Clean up performance test data
		for monitor_id in monitor_ids:
			frappe.delete_doc("Security Monitor", monitor_id)


if __name__ == "__main__":
	unittest.main()
