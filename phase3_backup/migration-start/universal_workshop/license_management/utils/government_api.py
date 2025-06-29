"""
Government API Integration Module
Provides integration with Oman government verification services
for business license and civil ID verification.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import requests

import frappe
from frappe import _


class GovernmentVerificationService:
	"""Service for integrating with Oman government verification APIs"""

	def __init__(self):
		"""Initialize government verification service"""
		self.config = self._load_config()
		self.session = requests.Session()
		self.timeout = 30

	def _load_config(self) -> dict[str, Any]:
		"""Load configuration from site config"""
		site_config = frappe.get_site_config()

		return {
			"api_key": site_config.get("oman_gov_api_key", ""),
			"api_secret": site_config.get("oman_gov_api_secret", ""),
			"base_url": site_config.get("oman_gov_api_url", "https://api.rop.gov.om"),
			"sandbox_mode": site_config.get("oman_gov_sandbox", True),
			"sandbox_url": "https://sandbox-api.rop.gov.om",
			"rate_limit": site_config.get("oman_gov_rate_limit", 100),  # per hour
			"cache_ttl": site_config.get("oman_gov_cache_ttl", 3600),  # 1 hour
		}

	def verify_business_license(self, license_number: str, business_name: str) -> dict[str, Any]:
		"""
		Verify business license with Oman Ministry of Commerce

		Args:
		    license_number: Business license number
		    business_name: Registered business name

		Returns:
		    Dict containing verification result
		"""
		if not license_number or not business_name:
			return {"valid": False, "error": "License number and business name are required"}

		try:
			# Check cache first
			cache_key = f"business_license_{license_number}"
			cached_result = self._get_cached_result(cache_key)
			if cached_result:
				return cached_result

			# Prepare request data
			request_data = {
				"license_number": license_number,
				"business_name": business_name,
				"verification_type": "business_license",
			}

			# Make API request
			response = self._make_request("/verify/business-license", request_data)

			if response.get("success"):
				result = {
					"valid": True,
					"license_number": response.get("license_number"),
					"business_name": response.get("business_name"),
					"issue_date": response.get("issue_date"),
					"expiry_date": response.get("expiry_date"),
					"status": response.get("status"),
					"activities": response.get("permitted_activities", []),
					"verification_timestamp": datetime.now().isoformat(),
				}
			else:
				result = {"valid": False, "error": response.get("message", "Verification failed")}

			# Cache the result
			self._cache_result(cache_key, result)
			return result

		except Exception as e:
			frappe.log_error(f"Business license verification failed: {e!s}")
			return {"valid": False, "error": f"Verification service error: {e!s}"}

	def verify_civil_id(self, civil_id: str, name: str) -> dict[str, Any]:
		"""
		Verify civil ID with Oman Royal Police

		Args:
		    civil_id: Civil ID number
		    name: Person's name

		Returns:
		    Dict containing verification result
		"""
		if not civil_id or not name:
			return {"valid": False, "error": "Civil ID and name are required"}

		try:
			# Check cache first
			cache_key = f"civil_id_{civil_id}"
			cached_result = self._get_cached_result(cache_key)
			if cached_result:
				return cached_result

			# Prepare request data
			request_data = {"civil_id": civil_id, "name": name, "verification_type": "civil_id"}

			# Make API request
			response = self._make_request("/verify/civil-id", request_data)

			if response.get("success"):
				result = {
					"valid": True,
					"civil_id": response.get("civil_id"),
					"name": response.get("name"),
					"nationality": response.get("nationality"),
					"gender": response.get("gender"),
					"date_of_birth": response.get("date_of_birth"),
					"verification_timestamp": datetime.now().isoformat(),
				}
			else:
				result = {"valid": False, "error": response.get("message", "Verification failed")}

			# Cache the result (shorter TTL for personal data)
			self._cache_result(cache_key, result, ttl=1800)  # 30 minutes
			return result

		except Exception as e:
			frappe.log_error(f"Civil ID verification failed: {e!s}")
			return {"valid": False, "error": f"Verification service error: {e!s}"}

	def verify_vat_registration(self, vat_number: str, business_name: str) -> dict[str, Any]:
		"""
		Verify VAT registration with Oman Tax Authority

		Args:
		    vat_number: VAT registration number
		    business_name: Registered business name

		Returns:
		    Dict containing verification result
		"""
		if not vat_number or not business_name:
			return {"valid": False, "error": "VAT number and business name are required"}

		try:
			# Check cache first
			cache_key = f"vat_number_{vat_number}"
			cached_result = self._get_cached_result(cache_key)
			if cached_result:
				return cached_result

			# Prepare request data
			request_data = {
				"vat_number": vat_number,
				"business_name": business_name,
				"verification_type": "vat_registration",
			}

			# Make API request
			response = self._make_request("/verify/vat-registration", request_data)

			if response.get("success"):
				result = {
					"valid": True,
					"vat_number": response.get("vat_number"),
					"business_name": response.get("business_name"),
					"registration_date": response.get("registration_date"),
					"status": response.get("status"),
					"verification_timestamp": datetime.now().isoformat(),
				}
			else:
				result = {"valid": False, "error": response.get("message", "Verification failed")}

			# Cache the result
			self._cache_result(cache_key, result)
			return result

		except Exception as e:
			frappe.log_error(f"VAT registration verification failed: {e!s}")
			return {"valid": False, "error": f"Verification service error: {e!s}"}

	def _make_request(self, endpoint: str, data: dict[str, Any], method: str = "POST") -> dict[str, Any]:
		"""Make authenticated request to government API"""
		try:
			timestamp = str(int(datetime.now().timestamp()))
			payload = json.dumps(data, ensure_ascii=False)
			signature = self._generate_signature(payload, timestamp)

			headers = {
				"Content-Type": "application/json",
				"Authorization": f"Bearer {self.config['api_key']}",
				"X-Timestamp": timestamp,
				"X-Signature": signature,
				"User-Agent": "Universal-Workshop-ERP/2.0",
			}

			# Use sandbox URL if in sandbox mode
			base_url = self.config["sandbox_url"] if self.config["sandbox_mode"] else self.config["base_url"]
			url = f"{base_url}{endpoint}"

			# Make request with proper timeout
			if method.upper() == "POST":
				response = self.session.post(url, data=payload, headers=headers, timeout=self.timeout)
			else:
				response = self.session.get(url, headers=headers, timeout=self.timeout)

			response.raise_for_status()
			return response.json()

		except requests.exceptions.Timeout:
			return {"success": False, "message": "Request timeout"}
		except requests.exceptions.ConnectionError:
			return {"success": False, "message": "Connection error"}
		except requests.exceptions.HTTPError as e:
			return {"success": False, "message": f"HTTP error: {e.response.status_code}"}
		except Exception as e:
			return {"success": False, "message": f"Request failed: {e!s}"}

	def _generate_signature(self, payload: str, timestamp: str) -> str:
		"""Generate HMAC signature for request authentication"""
		try:
			message = f"{timestamp}{payload}"
			signature = hmac.new(
				self.config["api_secret"].encode("utf-8"), message.encode("utf-8"), hashlib.sha256
			).hexdigest()
			return signature
		except Exception as e:
			frappe.log_error(f"Signature generation failed: {e!s}")
			return ""

	def _get_cached_result(self, cache_key: str) -> dict[str, Any] | None:
		"""Get cached verification result"""
		try:
			cached = frappe.cache().get_value(cache_key)
			if cached:
				cached_data = json.loads(cached)

				# Check if cache is still valid
				cache_time = datetime.fromisoformat(cached_data.get("cached_at", ""))
				if datetime.now() - cache_time < timedelta(seconds=self.config["cache_ttl"]):
					return cached_data.get("result")
				else:
					# Cache expired, remove it
					frappe.cache().delete_value(cache_key)

			return None

		except Exception as e:
			frappe.log_error(f"Cache retrieval failed for {cache_key}: {e!s}")
			return None

	def _cache_result(self, cache_key: str, result: dict[str, Any], ttl: int | None = None) -> None:
		"""Cache verification result"""
		try:
			cache_ttl = ttl or self.config["cache_ttl"]

			cache_data = {"result": result, "cached_at": datetime.now().isoformat()}

			frappe.cache().set_value(
				cache_key, json.dumps(cache_data, ensure_ascii=False), expires_in_sec=cache_ttl
			)

		except Exception as e:
			frappe.log_error(f"Cache storage failed for {cache_key}: {e!s}")

	def get_rate_limit_status(self) -> dict[str, Any]:
		"""Get current rate limit status"""
		try:
			# Check rate limit from cache
			rate_limit_key = "gov_api_rate_limit"
			current_count = frappe.cache().get_value(rate_limit_key) or 0

			return {
				"requests_made": int(current_count),
				"requests_limit": self.config["rate_limit"],
				"requests_remaining": max(0, self.config["rate_limit"] - int(current_count)),
				"reset_time": (datetime.now() + timedelta(hours=1)).isoformat(),
			}

		except Exception as e:
			frappe.log_error(f"Rate limit check failed: {e!s}")
			return {"error": str(e)}

	def test_connection(self) -> dict[str, Any]:
		"""Test connection to government API"""
		try:
			# Simple ping endpoint
			response = self._make_request("/ping", {}, method="GET")

			if response.get("success"):
				return {
					"connected": True,
					"message": "Connection successful",
					"api_version": response.get("version", "Unknown"),
					"server_time": response.get("timestamp"),
				}
			else:
				return {"connected": False, "message": response.get("message", "Connection failed")}

		except Exception as e:
			return {"connected": False, "message": f"Connection test failed: {e!s}"}


# API endpoints for external access
@frappe.whitelist()
def verify_business_license_api(license_number: str, business_name: str):
	"""API endpoint for business license verification"""
	service = GovernmentVerificationService()
	return service.verify_business_license(license_number, business_name)


@frappe.whitelist()
def verify_civil_id_api(civil_id: str, name: str):
	"""API endpoint for civil ID verification"""
	service = GovernmentVerificationService()
	return service.verify_civil_id(civil_id, name)


@frappe.whitelist()
def verify_vat_registration_api(vat_number: str, business_name: str):
	"""API endpoint for VAT registration verification"""
	service = GovernmentVerificationService()
	return service.verify_vat_registration(vat_number, business_name)


@frappe.whitelist()
def test_government_api_connection():
	"""API endpoint to test government API connection"""
	service = GovernmentVerificationService()
	return service.test_connection()


@frappe.whitelist()
def get_verification_rate_limit():
	"""API endpoint to get current rate limit status"""
	service = GovernmentVerificationService()
	return service.get_rate_limit_status()
