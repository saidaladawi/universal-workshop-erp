"""
Unit Tests for JWT Authentication System
Tests token generation, validation, revocation, and Arabic support
"""

import json
import unittest
from datetime import datetime, timedelta

import frappe
from universal_workshop.license_management.doctype.revoked_token.revoked_token import RevokedToken
from universal_workshop.license_management.jwt_manager import JWTManager


class TestJWTAuthentication(unittest.TestCase):
	"""Test suite for JWT Authentication System"""

	@classmethod
	def setUpClass(cls):
		"""Set up test environment"""
		# Ensure test site is set up
		frappe.set_user("Administrator")

		# Create test workshop and user data
		cls.test_workshop_code = "WS-TEST-001"
		cls.test_business_name = "Test Auto Workshop"
		cls.test_business_name_ar = "ورشة اختبار السيارات"
		cls.test_hardware_fp = "test-hardware-123"
		cls.test_owner_name = "Ahmed Al-Rashid"
		cls.test_owner_name_ar = "أحمد الراشد"

		# Initialize JWT Manager
		cls.jwt_manager = JWTManager()

	def setUp(self):
		"""Set up each test"""
		frappe.db.rollback()

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	def test_rsa_key_generation(self):
		"""Test RSA key pair generation and storage"""
		# Generate key pair
		key_pair_doc = self.jwt_manager.generate_key_pair()

		# Verify key pair exists
		self.assertIsNotNone(key_pair_doc)
		self.assertEqual(key_pair_doc.algorithm, "RS256")
		self.assertEqual(key_pair_doc.key_size, 2048)
		self.assertTrue(key_pair_doc.public_key.startswith("-----BEGIN PUBLIC KEY-----"))
		self.assertTrue(key_pair_doc.private_key.startswith("-----BEGIN PRIVATE KEY-----"))

		# Verify key validation
		self.assertTrue(key_pair_doc.is_valid)

	def test_jwt_token_generation(self):
		"""Test JWT token generation with Arabic business data"""
		# Generate token with Arabic business information
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
			business_name_ar=self.test_business_name_ar,
			owner_name=self.test_owner_name,
			owner_name_ar=self.test_owner_name_ar,
		)

		# Verify token structure
		self.assertIsInstance(token_data, dict)
		self.assertIn("access_token", token_data)
		self.assertIn("token_type", token_data)
		self.assertIn("expires_in", token_data)
		self.assertIn("jti", token_data)

		# Verify token format (JWT has 3 parts separated by dots)
		token_parts = token_data["access_token"].split(".")
		self.assertEqual(len(token_parts), 3)

		# Verify expiration is 24 hours
		self.assertEqual(token_data["expires_in"], 86400)  # 24 hours in seconds

	def test_jwt_token_validation_success(self):
		"""Test successful JWT token validation"""
		# Generate token
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
		)

		# Validate token
		validation_result = self.jwt_manager.validate_token(token_data["access_token"], self.test_hardware_fp)

		# Verify validation success
		self.assertTrue(validation_result["valid"])
		self.assertEqual(validation_result["workshop_code"], self.test_workshop_code)
		self.assertEqual(validation_result["hardware_fingerprint"], self.test_hardware_fp)
		self.assertIn("user_id", validation_result)

	def test_jwt_token_validation_hardware_mismatch(self):
		"""Test JWT token validation with mismatched hardware fingerprint"""
		# Generate token
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
		)

		# Validate with different hardware fingerprint
		validation_result = self.jwt_manager.validate_token(
			token_data["access_token"], "different-hardware-123"
		)

		# Verify validation failure
		self.assertFalse(validation_result["valid"])
		self.assertEqual(validation_result["error"], "Hardware fingerprint mismatch")

	def test_jwt_token_validation_expired(self):
		"""Test JWT token validation with expired token"""
		# Create expired token by mocking time
		import jwt

		# Generate key pair
		key_pair = self.jwt_manager.get_or_create_key_pair()

		# Create expired token payload
		expired_time = datetime.utcnow() - timedelta(hours=25)  # 25 hours ago
		payload = {
			"iss": "universal_workshop",
			"sub": frappe.session.user,
			"aud": "workshop_client",
			"exp": int(expired_time.timestamp()),
			"iat": int((expired_time - timedelta(hours=1)).timestamp()),
			"nbf": int((expired_time - timedelta(hours=1)).timestamp()),
			"jti": "expired-test-token",
			"workshop_code": self.test_workshop_code,
			"hardware_fingerprint": self.test_hardware_fp,
		}

		# Generate expired token
		expired_token = jwt.encode(payload, key_pair.private_key, algorithm="RS256")

		# Validate expired token
		validation_result = self.jwt_manager.validate_token(expired_token, self.test_hardware_fp)

		# Verify validation failure
		self.assertFalse(validation_result["valid"])
		self.assertIn("expired", validation_result["error"].lower())

	def test_jwt_token_refresh(self):
		"""Test JWT token refresh functionality"""
		# Generate initial token
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
		)

		# Refresh token (should work within 6-hour window)
		refresh_result = self.jwt_manager.refresh_token(token_data["access_token"], self.test_hardware_fp)

		# Verify refresh success
		self.assertTrue(refresh_result["success"])
		self.assertIn("access_token", refresh_result)
		self.assertNotEqual(refresh_result["access_token"], token_data["access_token"])

	def test_token_revocation(self):
		"""Test token revocation functionality"""
		# Generate token
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
		)

		# Revoke token
		revoked_token = RevokedToken.revoke_token(
			token_jti=token_data["jti"],
			reason="Testing token revocation",
			reason_ar="اختبار إلغاء الرمز المميز",
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
		)

		# Verify revocation record
		self.assertIsNotNone(revoked_token)
		self.assertEqual(revoked_token.token_jti, token_data["jti"])
		self.assertEqual(revoked_token.reason, "Testing token revocation")
		self.assertEqual(revoked_token.reason_ar, "اختبار إلغاء الرمز المميز")

		# Verify token is now invalid
		validation_result = self.jwt_manager.validate_token(token_data["access_token"], self.test_hardware_fp)

		self.assertFalse(validation_result["valid"])
		self.assertIn("revoked", validation_result["error"].lower())

	def test_arabic_business_name_encoding(self):
		"""Test proper handling of Arabic business names in JWT"""
		# Generate token with Arabic business name
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name_ar=self.test_business_name_ar,
			owner_name_ar=self.test_owner_name_ar,
		)

		# Validate and decode token
		validation_result = self.jwt_manager.validate_token(token_data["access_token"], self.test_hardware_fp)

		# Verify Arabic text is preserved
		self.assertTrue(validation_result["valid"])

		# Decode token manually to check Arabic content
		import jwt

		key_pair = self.jwt_manager.get_or_create_key_pair()
		decoded = jwt.decode(
			token_data["access_token"],
			key_pair.public_key,
			algorithms=["RS256"],
			options={"verify_exp": False},
		)

		self.assertEqual(decoded.get("business_name_ar"), self.test_business_name_ar)
		self.assertEqual(decoded.get("owner_name_ar"), self.test_owner_name_ar)

	def test_revoked_token_cleanup(self):
		"""Test automatic cleanup of expired revoked tokens"""
		# Create expired revoked token
		from frappe.utils import add_days, now_datetime

		expired_token = frappe.new_doc("Revoked Token")
		expired_token.update(
			{
				"token_jti": "expired-test-token-cleanup",
				"reason": "Test cleanup",
				"original_exp": add_days(now_datetime(), -10),  # Expired 10 days ago
				"revoked_by": frappe.session.user,
				"revoked_at": add_days(now_datetime(), -10),
			}
		)
		expired_token.insert()
		frappe.db.commit()

		# Run cleanup
		deleted_count = RevokedToken.cleanup_expired_tokens()

		# Verify token was cleaned up
		self.assertGreaterEqual(deleted_count, 1)
		self.assertFalse(frappe.db.exists("Revoked Token", "expired-test-token-cleanup"))

	def test_security_audit_logging(self):
		"""Test that JWT operations create appropriate audit logs"""
		# Generate token (should create audit log)
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
		)

		# Revoke token (should create audit log)
		RevokedToken.revoke_token(
			token_jti=token_data["jti"], reason="Security test", workshop_code=self.test_workshop_code
		)

		# Check audit logs exist
		audit_logs = frappe.get_all(
			"License Audit Log",
			filters={
				"workshop_code": self.test_workshop_code,
				"event_type": ["in", ["token_generated", "token_revoked"]],
			},
		)

		self.assertGreaterEqual(len(audit_logs), 1)

	def test_token_validation_performance(self):
		"""Test JWT validation performance"""
		import time

		# Generate token
		token_data = self.jwt_manager.generate_token(
			workshop_code=self.test_workshop_code,
			hardware_fingerprint=self.test_hardware_fp,
			business_name=self.test_business_name,
		)

		# Measure validation time
		start_time = time.time()
		validation_result = self.jwt_manager.validate_token(token_data["access_token"], self.test_hardware_fp)
		end_time = time.time()

		# Validation should be fast (under 100ms)
		validation_time = end_time - start_time
		self.assertLess(validation_time, 0.1, "Token validation too slow")
		self.assertTrue(validation_result["valid"])

	def test_concurrent_token_generation(self):
		"""Test that concurrent token generation works correctly"""
		import threading
		import time

		tokens = []
		errors = []

		def generate_token_thread():
			try:
				token_data = self.jwt_manager.generate_token(
					workshop_code=f"{self.test_workshop_code}-{threading.current_thread().ident}",
					hardware_fingerprint=f"{self.test_hardware_fp}-{threading.current_thread().ident}",
					business_name=self.test_business_name,
				)
				tokens.append(token_data)
			except Exception as e:
				errors.append(str(e))

		# Create and start multiple threads
		threads = []
		for _i in range(5):
			thread = threading.Thread(target=generate_token_thread)
			threads.append(thread)
			thread.start()

		# Wait for all threads to complete
		for thread in threads:
			thread.join()

		# Verify results
		self.assertEqual(len(errors), 0, f"Errors in concurrent generation: {errors}")
		self.assertEqual(len(tokens), 5)

		# Verify all tokens are unique
		jtis = [token["jti"] for token in tokens]
		self.assertEqual(len(jtis), len(set(jtis)), "Duplicate JTIs generated")


if __name__ == "__main__":
	unittest.main()
