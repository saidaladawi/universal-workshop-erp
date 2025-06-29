"""
Test Suite for Offline Grace Period Management System
Tests offline session creation, validation, and grace period handling
"""

import json
import time
import unittest
from datetime import datetime, timedelta

import frappe
from frappe.utils import add_hours, add_minutes, get_datetime, now_datetime
from universal_workshop.license_management.doctype.offline_session.offline_session import get_active_session
from universal_workshop.license_management.offline_manager import OfflineGracePeriodManager


class TestOfflineGracePeriodManager(unittest.TestCase):
	"""Test cases for offline grace period management"""

	def setUp(self):
		"""Set up test environment"""
		self.manager = OfflineGracePeriodManager()
		self.test_workshop_code = "WS-2024-0001"
		self.test_hardware_fingerprint = "test_hw_fingerprint_12345678901234567890"
		self.test_jwt_token = self._create_test_jwt_token()

		# Clean up any existing test data
		self._cleanup_test_data()

	def tearDown(self):
		"""Clean up after tests"""
		self._cleanup_test_data()

	def _cleanup_test_data(self):
		"""Remove test data"""
		try:
			# Delete test offline sessions
			test_sessions = frappe.get_all(
				"Offline Session", filters={"workshop_code": self.test_workshop_code}, pluck="name"
			)

			for session_name in test_sessions:
				frappe.delete_doc("Offline Session", session_name, force=True)

			frappe.db.commit()

		except Exception:
			pass  # Ignore cleanup errors

	def _create_test_jwt_token(self):
		"""Create a test JWT token for testing"""
		# This would normally come from the JWT manager
		return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.test_payload.test_signature"

	def test_start_offline_session_success(self):
		"""Test successful offline session creation"""
		# Mock JWT validation to return True
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			result = self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		self.assertTrue(result["success"])
		self.assertIn("offline_session_id", result)
		self.assertEqual(result["grace_period_remaining_hours"], 24)
		self.assertIn("expires_at", result)
		self.assertIn("secure_hash", result)

		# Verify session was created in database
		session = get_active_session(self.test_workshop_code)
		self.assertIsNotNone(session)
		self.assertEqual(session.workshop_code, self.test_workshop_code)
		self.assertEqual(session.status, "active")

	def test_start_offline_session_invalid_token(self):
		"""Test offline session creation with invalid token"""
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=False):
			result = self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, "invalid_token"
			)

		self.assertFalse(result["success"])
		self.assertIn("Cannot start offline session with invalid token", result["error"])
		self.assertTrue(result["requires_online_validation"])

	def test_validate_offline_session_success(self):
		"""Test successful offline session validation"""
		# First create an offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			start_result = self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		self.assertTrue(start_result["success"])

		# Now validate the session
		result = self.manager.validate_offline_session(
			self.test_workshop_code, self.test_hardware_fingerprint
		)

		self.assertTrue(result["valid"])
		self.assertLessEqual(result["grace_period_remaining_hours"], 24)
		self.assertIn("session_id", result)
		self.assertIn("last_online", result)
		self.assertIn("expires_at", result)

	def test_validate_offline_session_no_session(self):
		"""Test validation when no offline session exists"""
		result = self.manager.validate_offline_session(
			self.test_workshop_code, self.test_hardware_fingerprint
		)

		self.assertFalse(result["valid"])
		self.assertIn("No active offline session found", result["error"])
		self.assertTrue(result["requires_online_validation"])

	def test_validate_offline_session_hardware_mismatch(self):
		"""Test validation with hardware fingerprint mismatch"""
		# Create offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		# Validate with different hardware fingerprint
		result = self.manager.validate_offline_session(
			self.test_workshop_code, "different_hardware_fingerprint_123456"
		)

		self.assertFalse(result["valid"])
		self.assertIn("Hardware fingerprint mismatch", result["error"])
		self.assertTrue(result["security_violation"])

	def test_validate_offline_session_expired(self):
		"""Test validation of expired offline session"""
		# Create offline session with past expiration
		session_data = {
			"workshop_code": self.test_workshop_code,
			"hardware_fingerprint": self.test_hardware_fingerprint[:32],
			"started_at": add_hours(now_datetime(), -48).isoformat(),
			"expires_at": add_hours(now_datetime(), -24).isoformat(),
			"last_token_hash": "test_hash",
			"system_info": {"test": True},
			"secure_hash": "test_secure_hash",
		}

		# Create session directly in database
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": session_data["workshop_code"],
				"started_at": get_datetime(session_data["started_at"]),
				"expires_at": get_datetime(session_data["expires_at"]),
				"hardware_fingerprint_partial": session_data["hardware_fingerprint"],
				"secure_hash": session_data["secure_hash"],
				"status": "active",
				"session_data": json.dumps(session_data),
				"last_validation_at": now_datetime(),
				"activity_count": 1,
			}
		)
		session_doc.insert()
		frappe.db.commit()

		# Validate expired session
		result = self.manager.validate_offline_session(
			self.test_workshop_code, self.test_hardware_fingerprint
		)

		self.assertFalse(result["valid"])
		self.assertIn("Offline grace period expired", result["error"])
		self.assertTrue(result["grace_period_expired"])
		self.assertTrue(result["requires_online_validation"])

	def test_end_offline_session_success(self):
		"""Test successful offline session termination"""
		# Create offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			start_result = self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		# End session with successful online validation
		result = self.manager.end_offline_session(self.test_workshop_code, online_validation_success=True)

		self.assertTrue(result["success"])
		self.assertTrue(result["online_validation_success"])
		self.assertIn("session_duration_hours", result)
		self.assertIn("total_activities", result)

		# Verify session status updated
		session = frappe.get_doc("Offline Session", start_result["offline_session_id"])
		self.assertEqual(session.status, "completed")
		self.assertTrue(session.online_validation_success)
		self.assertIsNotNone(session.ended_at)

	def test_end_offline_session_no_session(self):
		"""Test ending offline session when none exists"""
		result = self.manager.end_offline_session(self.test_workshop_code, online_validation_success=False)

		self.assertTrue(result["success"])
		self.assertIn("No active offline session to end", result["message"])

	def test_clock_manipulation_detection(self):
		"""Test detection of system clock manipulation"""
		# Create offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		# Get session and manipulate last validation time to future
		session = get_active_session(self.test_workshop_code)
		session.last_validation_at = add_hours(now_datetime(), 1)  # 1 hour in future
		session.save()

		# Validate should detect clock manipulation
		result = self.manager.validate_offline_session(
			self.test_workshop_code, self.test_hardware_fingerprint
		)

		self.assertFalse(result["valid"])
		self.assertIn("Clock manipulation detected", result["error"])
		self.assertTrue(result["security_violation"])

	def test_grace_period_countdown(self):
		"""Test grace period countdown functionality"""
		# Create offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		# Simulate time passing by updating session start time
		session = get_active_session(self.test_workshop_code)
		session.started_at = add_hours(now_datetime(), -2)  # Started 2 hours ago
		session.expires_at = add_hours(now_datetime(), 22)  # Expires in 22 hours
		session.save()

		# Validate and check remaining time
		result = self.manager.validate_offline_session(
			self.test_workshop_code, self.test_hardware_fingerprint
		)

		self.assertTrue(result["valid"])
		self.assertLessEqual(result["grace_period_remaining_hours"], 22)
		self.assertGreaterEqual(result["grace_period_remaining_hours"], 21)

	def test_activity_tracking(self):
		"""Test offline session activity tracking"""
		# Create offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		# Validate multiple times to track activity
		for _i in range(3):
			result = self.manager.validate_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint
			)
			self.assertTrue(result["valid"])
			time.sleep(0.1)  # Small delay to ensure different timestamps

		# Check activity count
		session = get_active_session(self.test_workshop_code)
		self.assertGreaterEqual(session.activity_count, 3)

	def test_existing_session_handling(self):
		"""Test handling of existing offline sessions"""
		# Create first offline session
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			first_result = self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		# Try to create another session (should return existing)
		with unittest.mock.patch.object(self.manager, "_validate_token_for_offline", return_value=True):
			second_result = self.manager.start_offline_session(
				self.test_workshop_code, self.test_hardware_fingerprint, self.test_jwt_token
			)

		self.assertTrue(second_result["success"])
		self.assertIn("Resuming existing offline session", second_result["message"])
		self.assertEqual(first_result["offline_session_id"], second_result["offline_session_id"])

	def test_security_hash_validation(self):
		"""Test security hash validation for session integrity"""
		# Create session with tampered data
		session_data = {
			"workshop_code": self.test_workshop_code,
			"hardware_fingerprint": self.test_hardware_fingerprint[:32],
			"started_at": now_datetime().isoformat(),
			"expires_at": add_hours(now_datetime(), 24).isoformat(),
			"last_token_hash": "test_hash",
			"system_info": {"test": True},
			"secure_hash": "invalid_hash",  # Wrong hash
		}

		# Try to create session with invalid hash
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": session_data["workshop_code"],
				"started_at": get_datetime(session_data["started_at"]),
				"expires_at": get_datetime(session_data["expires_at"]),
				"hardware_fingerprint_partial": session_data["hardware_fingerprint"],
				"secure_hash": "different_hash",  # Mismatched hash
				"status": "active",
				"session_data": json.dumps(session_data),
				"last_validation_at": now_datetime(),
				"activity_count": 0,
			}
		)

		# This should trigger validation error on save
		with self.assertRaises(frappe.ValidationError):
			session_doc.insert()

	def test_session_cleanup(self):
		"""Test cleanup of old offline sessions"""
		# Create multiple completed sessions
		for i in range(3):
			session_doc = frappe.new_doc("Offline Session")
			session_doc.update(
				{
					"workshop_code": self.test_workshop_code,
					"started_at": add_hours(now_datetime(), -48),
					"expires_at": add_hours(now_datetime(), -24),
					"hardware_fingerprint_partial": self.test_hardware_fingerprint[:32],
					"secure_hash": f"test_hash_{i}",
					"status": "completed",
					"session_data": "{}",
					"last_validation_at": add_hours(now_datetime(), -24),
					"activity_count": i + 1,
					"ended_at": add_hours(now_datetime(), -23),
					"online_validation_success": True,
					"total_offline_hours": 1.0,
				}
			)
			session_doc.insert()

		frappe.db.commit()

		# Test cleanup
		self.manager._cleanup_old_offline_sessions(self.test_workshop_code)

		# Should still have sessions (within keep limit)
		remaining_sessions = frappe.get_all(
			"Offline Session", filters={"workshop_code": self.test_workshop_code}
		)
		self.assertLessEqual(len(remaining_sessions), 10)  # Keep last 10


class TestOfflineSessionDocType(unittest.TestCase):
	"""Test cases for Offline Session DocType"""

	def setUp(self):
		"""Set up test environment"""
		self.test_workshop_code = "WS-2024-0002"
		self._cleanup_test_data()

	def tearDown(self):
		"""Clean up after tests"""
		self._cleanup_test_data()

	def _cleanup_test_data(self):
		"""Remove test data"""
		try:
			test_sessions = frappe.get_all(
				"Offline Session", filters={"workshop_code": self.test_workshop_code}, pluck="name"
			)

			for session_name in test_sessions:
				frappe.delete_doc("Offline Session", session_name, force=True)

			frappe.db.commit()

		except Exception:
			pass

	def test_doctype_validation_success(self):
		"""Test successful DocType validation"""
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": self.test_workshop_code,
				"started_at": now_datetime(),
				"expires_at": add_hours(now_datetime(), 24),
				"hardware_fingerprint_partial": "test_fingerprint_partial",
				"secure_hash": "test_secure_hash",
				"status": "active",
				"session_data": '{"test": true}',
				"activity_count": 0,
			}
		)

		# Should not raise any errors
		session_doc.insert()
		self.assertIsNotNone(session_doc.name)

	def test_doctype_validation_invalid_workshop_code(self):
		"""Test validation with invalid workshop code"""
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": "INVALID-CODE",  # Invalid format
				"started_at": now_datetime(),
				"expires_at": add_hours(now_datetime(), 24),
				"status": "active",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			session_doc.insert()

	def test_doctype_validation_invalid_timing(self):
		"""Test validation with invalid timing"""
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": self.test_workshop_code,
				"started_at": now_datetime(),
				"expires_at": add_hours(now_datetime(), -1),  # Expires before start
				"status": "active",
			}
		)

		with self.assertRaises(frappe.ValidationError):
			session_doc.insert()

	def test_session_expiry_check(self):
		"""Test session expiry checking"""
		# Create expired session
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": self.test_workshop_code,
				"started_at": add_hours(now_datetime(), -25),
				"expires_at": add_hours(now_datetime(), -1),  # Expired 1 hour ago
				"status": "active",
			}
		)
		session_doc.insert()

		# Test expiry check
		self.assertTrue(session_doc.is_expired())

		# Test remaining time for expired session
		remaining = session_doc.get_remaining_time()
		self.assertTrue(remaining["expired"])
		self.assertEqual(remaining["remaining_hours"], 0)

	def test_session_remaining_time(self):
		"""Test remaining time calculation"""
		# Create active session with 12 hours remaining
		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": self.test_workshop_code,
				"started_at": add_hours(now_datetime(), -12),
				"expires_at": add_hours(now_datetime(), 12),
				"status": "active",
			}
		)
		session_doc.insert()

		remaining = session_doc.get_remaining_time()
		self.assertFalse(remaining["expired"])
		self.assertAlmostEqual(remaining["remaining_hours"], 12, delta=1)

	def test_hardware_fingerprint_verification(self):
		"""Test hardware fingerprint verification"""
		test_fingerprint = "test_hardware_fingerprint_12345678"

		session_doc = frappe.new_doc("Offline Session")
		session_doc.update(
			{
				"workshop_code": self.test_workshop_code,
				"started_at": now_datetime(),
				"expires_at": add_hours(now_datetime(), 24),
				"hardware_fingerprint_partial": test_fingerprint[:32],
				"status": "active",
			}
		)
		session_doc.insert()

		# Test matching fingerprint
		self.assertTrue(session_doc.verify_hardware_fingerprint(test_fingerprint))

		# Test non-matching fingerprint
		self.assertFalse(session_doc.verify_hardware_fingerprint("different_fingerprint"))


if __name__ == "__main__":
	# Run tests
	unittest.main()
