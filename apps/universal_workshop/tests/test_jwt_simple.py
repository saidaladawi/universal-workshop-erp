#!/usr/bin/env python3
"""
Simple integration test for JWT Authentication System
Tests basic functionality without requiring full test framework
"""

import os
import sys

# Add frappe to path
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench/apps/frappe")
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench/apps/erpnext")
sys.path.insert(0, "/home/said/frappe-dev/frappe-bench/apps/universal_workshop")

import frappe


def test_jwt_system():
	"""Test JWT system functionality"""
	print("🔐 Testing JWT Authentication System...")

	try:
		# Initialize frappe
		frappe.init(site="universal.local")
		frappe.connect()
		frappe.set_user("Administrator")

		# Test JWT Manager import
		print("📦 Importing JWT Manager...")
		from universal_workshop.license_management.jwt_manager import JWTManager

		jwt_manager = JWTManager()
		print("✅ JWT Manager imported successfully")

		# Test key pair generation
		print("🔑 Testing RSA key pair generation...")
		key_pair = jwt_manager.generate_key_pair()
		if key_pair and key_pair.public_key and key_pair.private_key:
			print("✅ RSA key pair generated successfully")
			print(f"   Algorithm: {key_pair.algorithm}")
			print(f"   Key Size: {key_pair.key_size}")
		else:
			print("❌ RSA key pair generation failed")
			return False

		# Test token generation
		print("🎫 Testing JWT token generation...")
		token_data = jwt_manager.generate_token(
			workshop_code="WS-TEST-001",
			hardware_fingerprint="test-hardware-123",
			business_name="Test Workshop",
			business_name_ar="ورشة اختبار",
		)

		if token_data and "access_token" in token_data:
			print("✅ JWT token generated successfully")
			print(f"   Token Type: {token_data.get('token_type')}")
			print(f"   Expires In: {token_data.get('expires_in')} seconds")
			print(f"   JTI: {token_data.get('jti')[:10]}...")
		else:
			print("❌ JWT token generation failed")
			return False

		# Test token validation
		print("🔍 Testing JWT token validation...")
		validation_result = jwt_manager.validate_token(token_data["access_token"], "test-hardware-123")

		if validation_result.get("valid"):
			print("✅ JWT token validation successful")
			print(f"   Workshop Code: {validation_result.get('workshop_code')}")
			print(f"   Hardware FP: {validation_result.get('hardware_fingerprint')[:10]}...")
		else:
			print(f"❌ JWT token validation failed: {validation_result.get('error')}")
			return False

		# Test Revoked Token DocType
		print("🚫 Testing Revoked Token functionality...")
		from universal_workshop.license_management.doctype.revoked_token.revoked_token import RevokedToken

		# Check if token is revoked (should be False initially)
		is_revoked = RevokedToken.is_token_revoked(token_data["jti"])
		if not is_revoked:
			print("✅ Token revocation check working (token not revoked)")
		else:
			print("❌ Token appears revoked when it shouldn't be")
			return False

		# Test token revocation
		revoked_token = RevokedToken.revoke_token(
			token_jti=token_data["jti"],
			reason="Integration test",
			reason_ar="اختبار التكامل",
			workshop_code="WS-TEST-001",
		)

		if revoked_token:
			print("✅ Token revocation successful")
			print(f"   Revoked Token ID: {revoked_token.name}")
		else:
			print("❌ Token revocation failed")
			return False

		# Verify token is now invalid
		validation_result_after_revoke = jwt_manager.validate_token(
			token_data["access_token"], "test-hardware-123"
		)

		if not validation_result_after_revoke.get("valid"):
			print("✅ Revoked token correctly rejected")
		else:
			print("❌ Revoked token still validates (should be rejected)")
			return False

		# Test Audit Log functionality
		print("📋 Testing License Audit Log...")
		from universal_workshop.license_management.doctype.license_audit_log.license_audit_log import (
			create_audit_log,
		)

		audit_log = create_audit_log(
			event_type="integration_test",
			severity="low",
			message="JWT integration test completed",
			event_data={"test_status": "success"},
			workshop_code="WS-TEST-001",
		)

		if audit_log:
			print("✅ Audit log creation successful")
			print(f"   Audit Log ID: {audit_log.name}")
		else:
			print("❌ Audit log creation failed")
			return False

		print("\n🎉 All JWT Authentication System tests passed!")
		return True

	except Exception as e:
		print(f"\n❌ Test failed with error: {e!s}")
		import traceback

		traceback.print_exc()
		return False

	finally:
		# Clean up
		frappe.db.rollback()
		frappe.destroy()


if __name__ == "__main__":
	success = test_jwt_system()
	sys.exit(0 if success else 1)
