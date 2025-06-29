"""
Business Binding Utility Module
Handles workshop-business license binding operations and validation
for Universal Workshop ERP license management system.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from universal_workshop.license_management.utils.hardware_fingerprint import HardwareFingerprintValidator
from universal_workshop.license_management.utils.jwt_manager import JWTManager


class BusinessBindingManager:
	"""Manager for workshop-business license binding operations"""

	def __init__(self):
		"""Initialize business binding manager"""
		self.jwt_manager = JWTManager()
		self.hardware_validator = HardwareFingerprintValidator()

	def bind_workshop_to_business(
		self,
		workshop_code: str,
		business_license_number: str,
		hardware_fingerprint: str,
		license_key_hash: str,
	) -> dict[str, Any]:
		"""Bind workshop to business registration with full validation"""
		try:
			# Step 1: Validate business registration exists and is verified
			business = self._get_verified_business(business_license_number)
			if not business:
				return {"success": False, "error": _("Business license not found or not verified")}

			# Step 2: Validate hardware fingerprint
			if not self._validate_hardware_fingerprint(hardware_fingerprint):
				return {"success": False, "error": _("Invalid hardware fingerprint")}

			# Step 3: Check for existing binding conflicts
			binding_check = self._check_binding_conflicts(workshop_code, business_license_number)
			if not binding_check["allowed"]:
				return {"success": False, "error": binding_check["reason"]}

			# Step 4: Create workshop binding record
			binding_result = self._create_workshop_binding(
				workshop_code, business, hardware_fingerprint, license_key_hash
			)

			if binding_result["success"]:
				# Step 5: Generate JWT token for the binding
				token_result = self._generate_binding_token(
					workshop_code, business_license_number, hardware_fingerprint
				)

				if token_result["success"]:
					# Step 6: Log successful binding
					self._log_binding_event(
						workshop_code,
						business_license_number,
						"Bound",
						{"hardware_hash": hashlib.sha256(hardware_fingerprint.encode()).hexdigest()},
					)

					return {
						"success": True,
						"message": _("Workshop successfully bound to business"),
						"workshop_code": workshop_code,
						"business_name": business.business_name_en,
						"business_name_ar": business.business_name_ar,
						"binding_date": datetime.now().isoformat(),
						"token": token_result["token"],
						"expires_at": token_result["expires_at"],
					}
				else:
					# Rollback binding if token generation failed
					self._rollback_binding(workshop_code, business_license_number)
					return {
						"success": False,
						"error": _("Failed to generate license token: {0}").format(token_result["error"]),
					}
			else:
				return {"success": False, "error": binding_result["error"]}

		except Exception as e:
			frappe.log_error(f"Workshop binding failed: {e}")
			return {"success": False, "error": str(e)}

	def unbind_workshop_from_business(
		self, workshop_code: str, business_license_number: str
	) -> dict[str, Any]:
		"""Unbind workshop from business registration"""
		try:
			# Step 1: Get business registration
			business = frappe.get_doc(
				"Business Registration", {"business_license_number": business_license_number}
			)

			if not business:
				return {"success": False, "error": _("Business license not found")}

			# Step 2: Remove workshop binding
			unbind_result = business.unbind_from_workshop(workshop_code)

			if unbind_result["success"]:
				# Step 3: Revoke all tokens for this workshop-business combination
				self._revoke_binding_tokens(workshop_code, business_license_number)

				# Step 4: Log unbinding event
				self._log_binding_event(workshop_code, business_license_number, "Unbound", {})

				return {
					"success": True,
					"message": _("Workshop successfully unbound from business"),
					"workshop_code": workshop_code,
					"business_name": business.business_name_en,
				}
			else:
				return unbind_result

		except Exception as e:
			frappe.log_error(f"Workshop unbinding failed: {e}")
			return {"success": False, "error": str(e)}

	def validate_workshop_binding(
		self, workshop_code: str, business_license_number: str, hardware_fingerprint: str
	) -> dict[str, Any]:
		"""Validate workshop binding with business and hardware"""
		try:
			# Step 1: Get business registration
			business = self._get_verified_business(business_license_number)
			if not business:
				return {"valid": False, "error": _("Business license not found or not verified")}

			# Step 2: Check workshop binding exists
			workshop_binding = self._get_workshop_binding(business, workshop_code)
			if not workshop_binding:
				return {"valid": False, "error": _("Workshop not bound to this business")}

			# Step 3: Validate hardware fingerprint
			hardware_match = self._validate_binding_hardware(workshop_binding, hardware_fingerprint)

			if not hardware_match["valid"]:
				return {"valid": False, "error": hardware_match["error"]}

			# Step 4: Check binding status and expiry
			binding_status = self._check_binding_status(workshop_binding)
			if not binding_status["active"]:
				return {"valid": False, "error": binding_status["reason"]}

			# Step 5: Update last validation timestamp
			self._update_binding_validation(workshop_binding)

			return {
				"valid": True,
				"business_name": business.business_name_en,
				"business_name_ar": business.business_name_ar,
				"workshop_code": workshop_code,
				"binding_date": workshop_binding.binding_date,
				"last_validation": datetime.now().isoformat(),
				"verification_status": business.verification_status,
			}

		except Exception as e:
			frappe.log_error(f"Binding validation failed: {e}")
			return {"valid": False, "error": str(e)}

	def get_workshop_bindings(self, workshop_code: str) -> dict[str, Any]:
		"""Get all business bindings for a workshop"""
		try:
			bindings = frappe.db.sql(
				"""
                SELECT br.business_name_en, br.business_name_ar, br.business_license_number,
                       br.verification_status, br.binding_status, br.binding_date,
                       bwb.binding_status as workshop_binding_status, bwb.last_validation,
                       bwb.validation_failures
                FROM `tabBusiness Registration` br
                JOIN `tabBusiness Workshop Binding` bwb ON bwb.parent = br.name
                WHERE bwb.workshop_code = %s
                ORDER BY bwb.binding_date DESC
            """,
				(workshop_code,),
				as_dict=True,
			)

			return {
				"success": True,
				"workshop_code": workshop_code,
				"bindings": bindings,
				"total_bindings": len(bindings),
				"active_bindings": len([b for b in bindings if b.workshop_binding_status == "Active"]),
			}

		except Exception as e:
			return {"success": False, "error": str(e)}

	def get_business_bindings(self, business_license_number: str) -> dict[str, Any]:
		"""Get all workshop bindings for a business"""
		try:
			business = frappe.get_doc(
				"Business Registration", {"business_license_number": business_license_number}
			)

			if not business:
				return {"success": False, "error": _("Business license not found")}

			bindings = []
			for workshop_binding in business.workshop_codes:
				bindings.append(
					{
						"workshop_code": workshop_binding.workshop_code,
						"workshop_name": workshop_binding.workshop_name,
						"workshop_name_ar": workshop_binding.workshop_name_ar,
						"binding_date": workshop_binding.binding_date,
						"binding_status": workshop_binding.binding_status,
						"last_validation": workshop_binding.last_validation,
						"validation_failures": workshop_binding.validation_failures,
					}
				)

			return {
				"success": True,
				"business_name": business.business_name_en,
				"business_name_ar": business.business_name_ar,
				"business_license_number": business_license_number,
				"verification_status": business.verification_status,
				"bindings": bindings,
				"total_bindings": len(bindings),
				"active_bindings": len([b for b in bindings if b["binding_status"] == "Active"]),
			}

		except Exception as e:
			return {"success": False, "error": str(e)}

	def _get_verified_business(self, business_license_number: str) -> Any | None:
		"""Get verified business registration"""
		try:
			business = frappe.get_doc(
				"Business Registration", {"business_license_number": business_license_number}
			)

			if business and business.verification_status == "Verified":
				return business
			return None

		except Exception:
			return None

	def _validate_hardware_fingerprint(self, hardware_fingerprint: str) -> bool:
		"""Validate hardware fingerprint format and content"""
		try:
			if not hardware_fingerprint or len(hardware_fingerprint) < 64:
				return False

			# Validate fingerprint structure (should be JSON with specific fields)
			fingerprint_data = json.loads(hardware_fingerprint)
			required_fields = ["primary_hash", "secondary_hash", "components"]

			return all(field in fingerprint_data for field in required_fields)

		except Exception:
			return False

	def _check_binding_conflicts(self, workshop_code: str, business_license_number: str) -> dict[str, Any]:
		"""Check for binding conflicts"""
		try:
			# Check if workshop is already bound to a different business
			existing_binding = frappe.db.sql(
				"""
                SELECT br.business_license_number, br.business_name_en
                FROM `tabBusiness Registration` br
                JOIN `tabBusiness Workshop Binding` bwb ON bwb.parent = br.name
                WHERE bwb.workshop_code = %s
                  AND br.business_license_number != %s
                  AND bwb.binding_status = 'Active'
            """,
				(workshop_code, business_license_number),
				as_dict=True,
			)

			if existing_binding:
				return {
					"allowed": False,
					"reason": _("Workshop already bound to business: {0}").format(
						existing_binding[0]["business_name_en"]
					),
				}

			# Check business binding limits (if any)
			business_bindings = frappe.db.count(
				"Business Workshop Binding",
				{
					"parent": frappe.db.get_value(
						"Business Registration", {"business_license_number": business_license_number}, "name"
					),
					"binding_status": "Active",
				},
			)

			max_workshops = frappe.conf.get("max_workshops_per_business", 10)
			if business_bindings >= max_workshops:
				return {
					"allowed": False,
					"reason": _("Business has reached maximum workshop limit: {0}").format(max_workshops),
				}

			return {"allowed": True, "reason": None}

		except Exception as e:
			return {"allowed": False, "reason": str(e)}

	def _create_workshop_binding(
		self, workshop_code: str, business: Any, hardware_fingerprint: str, license_key_hash: str
	) -> dict[str, Any]:
		"""Create workshop binding record"""
		try:
			# Get workshop details (assuming Workshop DocType exists)
			workshop_name = workshop_code  # Fallback to code if name not available
			workshop_name_ar = workshop_code

			try:
				workshop_doc = frappe.get_doc("Workshop Profile", {"workshop_code": workshop_code})
				workshop_name = workshop_doc.workshop_name or workshop_code
				workshop_name_ar = workshop_doc.workshop_name_ar or workshop_code
			except Exception:
				pass  # Use fallback values

			# Create binding record
			binding_result = business.bind_to_workshop(
				workshop_code, license_key_hash, hashlib.sha256(hardware_fingerprint.encode()).hexdigest()
			)

			if binding_result["success"]:
				# Update binding with workshop details
				for binding in business.workshop_codes:
					if binding.workshop_code == workshop_code:
						binding.workshop_name = workshop_name
						binding.workshop_name_ar = workshop_name_ar
						break

				business.save(ignore_permissions=True)

				return {"success": True, "binding_id": f"{business.name}-{workshop_code}"}
			else:
				return binding_result

		except Exception as e:
			return {"success": False, "error": str(e)}

	def _generate_binding_token(
		self, workshop_code: str, business_license_number: str, hardware_fingerprint: str
	) -> dict[str, Any]:
		"""Generate JWT token for workshop-business binding"""
		try:
			claims = {
				"workshop_code": workshop_code,
				"business_license": business_license_number,
				"hardware_hash": hashlib.sha256(hardware_fingerprint.encode()).hexdigest(),
				"binding_type": "workshop_business",
				"issued_at": datetime.now().isoformat(),
			}

			token_result = self.jwt_manager.generate_token(claims)
			return token_result

		except Exception as e:
			return {"success": False, "error": str(e)}

	def _rollback_binding(self, workshop_code: str, business_license_number: str):
		"""Rollback binding in case of failure"""
		try:
			business = frappe.get_doc(
				"Business Registration", {"business_license_number": business_license_number}
			)

			if business:
				business.unbind_from_workshop(workshop_code)

		except Exception as e:
			frappe.log_error(f"Binding rollback failed: {e}")

	def _get_workshop_binding(self, business: Any, workshop_code: str) -> Any | None:
		"""Get specific workshop binding from business"""
		for binding in business.workshop_codes:
			if binding.workshop_code == workshop_code:
				return binding
		return None

	def _validate_binding_hardware(self, workshop_binding: Any, hardware_fingerprint: str) -> dict[str, Any]:
		"""Validate hardware fingerprint against binding"""
		try:
			stored_hash = workshop_binding.hardware_fingerprint_hash
			current_hash = hashlib.sha256(hardware_fingerprint.encode()).hexdigest()

			if stored_hash == current_hash:
				return {"valid": True}

			# Try hardware fingerprint validation with tolerance
			validation_result = self.hardware_validator.validate_fingerprint(
				hardware_fingerprint, stored_hash
			)

			if validation_result["valid"]:
				return {"valid": True}
			else:
				# Increment validation failures
				workshop_binding.validation_failures = (workshop_binding.validation_failures or 0) + 1

				return {"valid": False, "error": _("Hardware fingerprint mismatch")}

		except Exception as e:
			return {"valid": False, "error": str(e)}

	def _check_binding_status(self, workshop_binding: Any) -> dict[str, Any]:
		"""Check if binding is active and valid"""
		if workshop_binding.binding_status != "Active":
			return {
				"active": False,
				"reason": _("Workshop binding is {0}").format(workshop_binding.binding_status),
			}

		# Check for excessive validation failures
		max_failures = frappe.conf.get("max_binding_validation_failures", 10)
		if (workshop_binding.validation_failures or 0) >= max_failures:
			return {"active": False, "reason": _("Workshop binding suspended due to validation failures")}

		return {"active": True}

	def _update_binding_validation(self, workshop_binding: Any):
		"""Update binding last validation timestamp"""
		try:
			workshop_binding.last_validation = datetime.now()
			workshop_binding.save(ignore_permissions=True)
		except Exception:
			pass  # Non-critical failure

	def _revoke_binding_tokens(self, workshop_code: str, business_license_number: str):
		"""Revoke all tokens for workshop-business binding"""
		try:
			# Find tokens with matching claims
			tokens_to_revoke = frappe.db.sql(
				"""
                SELECT token_hash FROM `tabRevoked Token`
                WHERE details LIKE %s AND details LIKE %s
            """,
				(
					f'%"workshop_code": "{workshop_code}"%',
					f'%"business_license": "{business_license_number}"%',
				),
			)

			for token_hash_row in tokens_to_revoke:
				self.jwt_manager.revoke_token(token_hash_row[0])

		except Exception as e:
			frappe.log_error(f"Token revocation failed: {e}")

	def _log_binding_event(
		self, workshop_code: str, business_license_number: str, action: str, details: dict[str, Any]
	):
		"""Log binding events for audit trail"""
		try:
			frappe.get_doc(
				{
					"doctype": "License Audit Log",
					"event_type": "Workshop Business Binding",
					"event_description": f"Workshop {workshop_code} {action.lower()} to/from business {business_license_number}",
					"severity": "Info",
					"workshop_code": workshop_code,
					"business_license": business_license_number,
					"details": json.dumps(
						{
							"action": action,
							"workshop_code": workshop_code,
							"business_license": business_license_number,
							"timestamp": datetime.now().isoformat(),
							**details,
						},
						ensure_ascii=False,
					),
				}
			).insert(ignore_permissions=True)

		except Exception as e:
			frappe.log_error(f"Failed to log binding event: {e}")


# API endpoints for business binding management


@frappe.whitelist()
def bind_workshop_to_business(workshop_code, business_license_number, hardware_fingerprint, license_key_hash):
	"""API endpoint for workshop-business binding"""
	try:
		manager = BusinessBindingManager()
		result = manager.bind_workshop_to_business(
			workshop_code, business_license_number, hardware_fingerprint, license_key_hash
		)
		return result

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def unbind_workshop_from_business(workshop_code, business_license_number):
	"""API endpoint for workshop-business unbinding"""
	try:
		manager = BusinessBindingManager()
		result = manager.unbind_workshop_from_business(workshop_code, business_license_number)
		return result

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def validate_workshop_binding(workshop_code, business_license_number, hardware_fingerprint):
	"""API endpoint for workshop binding validation"""
	try:
		manager = BusinessBindingManager()
		result = manager.validate_workshop_binding(
			workshop_code, business_license_number, hardware_fingerprint
		)
		return result

	except Exception as e:
		return {"valid": False, "error": str(e)}


@frappe.whitelist()
def get_workshop_bindings(workshop_code):
	"""API endpoint for getting workshop bindings"""
	try:
		manager = BusinessBindingManager()
		result = manager.get_workshop_bindings(workshop_code)
		return result

	except Exception as e:
		return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_business_bindings(business_license_number):
	"""API endpoint for getting business bindings"""
	try:
		manager = BusinessBindingManager()
		result = manager.get_business_bindings(business_license_number)
		return result

	except Exception as e:
		return {"success": False, "error": str(e)}
