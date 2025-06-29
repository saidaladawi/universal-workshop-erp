# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import hashlib
import ipaddress
import json
from datetime import datetime, timedelta

import geoip2.database
import geoip2.errors
import requests

import frappe
from frappe import _
from frappe.utils import get_site_url, now


class SecurityAPIManager:
	"""Centralized security API management for external integrations"""

	def __init__(self):
		self.api_version = "1.0"
		self.rate_limits = {
			"create_monitor": 100,  # per hour
			"dashboard_data": 500,  # per hour
			"threat_report": 50,  # per hour
		}

	@frappe.whitelist()
	def create_threat_monitor(self, workshop_code, business_license, threat_data):
		"""Create security monitor from external threat detection systems"""
		try:
			# Validate rate limits
			if not self._check_rate_limit("create_monitor"):
				return {"success": False, "error": "Rate limit exceeded"}

			# Validate input data
			validated_data = self._validate_threat_data(threat_data)
			if not validated_data["valid"]:
				return {"success": False, "error": validated_data["message"]}

			# Enrich threat data with geolocation
			enriched_data = self._enrich_geolocation_data(validated_data["data"])

			# Create security monitor
			monitor = frappe.new_doc("Security Monitor")
			monitor.workshop_code = workshop_code
			monitor.business_license = business_license
			monitor.monitor_type = enriched_data.get("monitor_type", "Threat Detection")
			monitor.monitor_date = datetime.now()

			# Set location data
			monitor.ip_address = enriched_data.get("ip_address")
			monitor.geographic_location = enriched_data.get("geographic_location")
			monitor.country_code = enriched_data.get("country_code")
			monitor.city = enriched_data.get("city")

			# Set behavioral data
			monitor.activity_pattern = enriched_data.get("activity_pattern", "Normal")
			monitor.session_duration = enriched_data.get("session_duration", 0)
			monitor.concurrent_sessions = enriched_data.get("concurrent_sessions", 1)

			# Set system data
			monitor.hardware_fingerprint_hash = enriched_data.get("hardware_fingerprint_hash")
			monitor.os_version = enriched_data.get("os_version")
			monitor.browser_info = enriched_data.get("browser_info")

			# Add threat indicators
			if enriched_data.get("threat_indicators"):
				monitor.threat_indicators = enriched_data["threat_indicators"]

			# Insert and process
			monitor.insert()

			return {
				"success": True,
				"monitor_id": monitor.name,
				"risk_level": monitor.risk_level,
				"alert_generated": monitor.alert_status != "No Alert",
			}

		except Exception as e:
			frappe.log_error(f"Security API Error: {e!s}", "Security Monitor API")
			return {"success": False, "error": "Internal server error"}

	@frappe.whitelist()
	def get_real_time_threats(self, workshop_code=None, hours=24):
		"""Get real-time threat data for dashboards"""
		try:
			if not self._check_rate_limit("dashboard_data"):
				return {"success": False, "error": "Rate limit exceeded"}

			filters = {
				"monitor_date": [">=", datetime.now() - timedelta(hours=int(hours))],
				"risk_level": ["in", ["Medium", "High", "Critical"]],
			}

			if workshop_code:
				filters["workshop_code"] = workshop_code

			threats = frappe.get_list(
				"Security Monitor",
				filters=filters,
				fields=[
					"name",
					"workshop_code",
					"business_license",
					"monitor_type",
					"risk_level",
					"monitor_date",
					"alert_status",
					"ip_address",
					"geographic_location",
					"country_code",
					"location_risk_score",
					"behavioral_risk_score",
					"system_risk_score",
				],
				order_by="monitor_date desc",
				limit=100,
			)

			# Calculate threat metrics
			metrics = self._calculate_threat_metrics(threats)

			return {"success": True, "threats": threats, "metrics": metrics, "last_updated": now()}

		except Exception as e:
			frappe.log_error(f"Real-time Threats API Error: {e!s}", "Security Monitor API")
			return {"success": False, "error": "Internal server error"}

	@frappe.whitelist()
	def submit_threat_intelligence(self, threat_iocs, source="External"):
		"""Submit threat intelligence indicators for processing"""
		try:
			if not self._check_rate_limit("threat_report"):
				return {"success": False, "error": "Rate limit exceeded"}

			processed_indicators = []

			for ioc in threat_iocs:
				# Validate IOC format
				validated_ioc = self._validate_ioc(ioc)
				if validated_ioc["valid"]:
					# Create threat indicator entry
					indicator = {
						"indicator_type": validated_ioc["type"],
						"indicator_value": validated_ioc["value"],
						"risk_weight": validated_ioc.get("risk_weight", 5),
						"severity": validated_ioc.get("severity", "Medium"),
						"confidence_level": validated_ioc.get("confidence", "Medium"),
						"detected_at": datetime.now(),
						"description": validated_ioc.get("description", ""),
						"source": source,
					}
					processed_indicators.append(indicator)

			# Store threat intelligence
			if processed_indicators:
				self._store_threat_intelligence(processed_indicators)

			return {
				"success": True,
				"processed_count": len(processed_indicators),
				"total_submitted": len(threat_iocs),
			}

		except Exception as e:
			frappe.log_error(f"Threat Intelligence API Error: {e!s}", "Security Monitor API")
			return {"success": False, "error": "Internal server error"}

	@frappe.whitelist()
	def get_workshop_security_status(self, workshop_code):
		"""Get comprehensive security status for a workshop"""
		try:
			# Get recent security events
			recent_events = frappe.get_list(
				"Security Monitor",
				filters={
					"workshop_code": workshop_code,
					"monitor_date": [">=", datetime.now() - timedelta(days=7)],
				},
				fields=["risk_level", "monitor_type", "alert_status"],
				order_by="monitor_date desc",
			)

			# Calculate security score
			security_score = self._calculate_security_score(recent_events)

			# Get active alerts
			active_alerts = frappe.get_list(
				"Security Monitor",
				filters={
					"workshop_code": workshop_code,
					"alert_status": ["in", ["Alert Generated", "Under Investigation"]],
				},
				fields=["name", "risk_level", "monitor_type", "monitor_date"],
			)

			# Get license status
			license_status = self._get_license_security_status(workshop_code)

			return {
				"success": True,
				"workshop_code": workshop_code,
				"security_score": security_score,
				"threat_level": self._determine_threat_level(security_score),
				"active_alerts": len(active_alerts),
				"recent_events": len(recent_events),
				"license_status": license_status,
				"last_assessment": now(),
			}

		except Exception as e:
			frappe.log_error(f"Security Status API Error: {e!s}", "Security Monitor API")
			return {"success": False, "error": "Internal server error"}

	def _validate_threat_data(self, threat_data):
		"""Validate incoming threat data"""
		required_fields = ["monitor_type"]

		if isinstance(threat_data, str):
			try:
				threat_data = json.loads(threat_data)
			except json.JSONDecodeError:
				return {"valid": False, "message": "Invalid JSON format"}

		for field in required_fields:
			if field not in threat_data:
				return {"valid": False, "message": f"Missing required field: {field}"}

		# Validate IP address if provided
		if "ip_address" in threat_data:
			try:
				ipaddress.ip_address(threat_data["ip_address"])
			except ValueError:
				return {"valid": False, "message": "Invalid IP address format"}

		return {"valid": True, "data": threat_data, "message": "Valid"}

	def _enrich_geolocation_data(self, threat_data):
		"""Enrich threat data with geolocation information"""
		try:
			ip_address = threat_data.get("ip_address")
			if not ip_address:
				return threat_data

			# Attempt geolocation lookup (would require GeoIP database)
			# For now, implement basic logic
			if ip_address.startswith(("192.168.", "10.", "172.")):
				# Private IP - local network
				threat_data["geographic_location"] = "Local Network"
				threat_data["country_code"] = "OM"  # Assume Oman for local
				threat_data["city"] = "Unknown"
			else:
				# Public IP - attempt lookup (mock implementation)
				threat_data["geographic_location"] = "Unknown Location"
				threat_data["country_code"] = "XX"
				threat_data["city"] = "Unknown"

		except Exception as e:
			frappe.log_error(f"Geolocation enrichment error: {e!s}")

		return threat_data

	def _validate_ioc(self, ioc):
		"""Validate Indicator of Compromise (IOC)"""
		ioc_types = {
			"ip": self._validate_ip_ioc,
			"domain": self._validate_domain_ioc,
			"hash": self._validate_hash_ioc,
			"url": self._validate_url_ioc,
		}

		ioc_type = ioc.get("type", "").lower()
		if ioc_type not in ioc_types:
			return {"valid": False, "error": "Unknown IOC type"}

		return ioc_types[ioc_type](ioc)

	def _validate_ip_ioc(self, ioc):
		"""Validate IP address IOC"""
		try:
			ipaddress.ip_address(ioc["value"])
			return {
				"valid": True,
				"type": "Suspicious IP",
				"value": ioc["value"],
				"risk_weight": ioc.get("risk_weight", 6),
				"severity": ioc.get("severity", "Medium"),
				"confidence": ioc.get("confidence", "Medium"),
			}
		except ValueError:
			return {"valid": False, "error": "Invalid IP address"}

	def _validate_domain_ioc(self, ioc):
		"""Validate domain IOC"""
		domain = ioc["value"]
		if "." not in domain or len(domain) < 3:
			return {"valid": False, "error": "Invalid domain format"}

		return {
			"valid": True,
			"type": "Suspicious Domain",
			"value": domain,
			"risk_weight": ioc.get("risk_weight", 5),
			"severity": ioc.get("severity", "Medium"),
			"confidence": ioc.get("confidence", "Medium"),
		}

	def _validate_hash_ioc(self, ioc):
		"""Validate hash IOC"""
		hash_value = ioc["value"]
		if len(hash_value) not in [32, 40, 64]:  # MD5, SHA1, SHA256
			return {"valid": False, "error": "Invalid hash length"}

		return {
			"valid": True,
			"type": "Malicious Hash",
			"value": hash_value,
			"risk_weight": ioc.get("risk_weight", 8),
			"severity": ioc.get("severity", "High"),
			"confidence": ioc.get("confidence", "High"),
		}

	def _validate_url_ioc(self, ioc):
		"""Validate URL IOC"""
		url = ioc["value"]
		if not url.startswith(("http://", "https://")):
			return {"valid": False, "error": "Invalid URL format"}

		return {
			"valid": True,
			"type": "Malicious URL",
			"value": url,
			"risk_weight": ioc.get("risk_weight", 7),
			"severity": ioc.get("severity", "High"),
			"confidence": ioc.get("confidence", "Medium"),
		}

	def _store_threat_intelligence(self, indicators):
		"""Store threat intelligence indicators"""
		# Implementation would store in threat intelligence database
		# For now, log for audit purposes
		frappe.log_error(f"Threat Intelligence Stored: {len(indicators)} indicators", "Threat Intelligence")

	def _calculate_threat_metrics(self, threats):
		"""Calculate threat metrics from security monitor data"""
		if not threats:
			return {
				"total_threats": 0,
				"critical_threats": 0,
				"threat_trend": "stable",
				"average_risk_score": 0,
			}

		critical_count = sum(1 for t in threats if t.risk_level == "Critical")
		high_count = sum(1 for t in threats if t.risk_level == "High")

		# Calculate average risk score
		total_risk = 0
		risk_count = 0
		for threat in threats:
			if threat.location_risk_score:
				total_risk += threat.location_risk_score
				risk_count += 1
			if threat.behavioral_risk_score:
				total_risk += threat.behavioral_risk_score
				risk_count += 1
			if threat.system_risk_score:
				total_risk += threat.system_risk_score
				risk_count += 1

		avg_risk = total_risk / max(risk_count, 1)

		return {
			"total_threats": len(threats),
			"critical_threats": critical_count,
			"high_threats": high_count,
			"average_risk_score": round(avg_risk, 2),
			"threat_trend": "increasing" if critical_count > 2 else "stable",
		}

	def _calculate_security_score(self, events):
		"""Calculate overall security score for workshop"""
		if not events:
			return 85  # Default good score

		# Scoring algorithm
		base_score = 100

		for event in events:
			if event.risk_level == "Critical":
				base_score -= 20
			elif event.risk_level == "High":
				base_score -= 10
			elif event.risk_level == "Medium":
				base_score -= 5

		return max(0, base_score)

	def _determine_threat_level(self, security_score):
		"""Determine threat level from security score"""
		if security_score >= 80:
			return "Low"
		elif security_score >= 60:
			return "Medium"
		elif security_score >= 40:
			return "High"
		else:
			return "Critical"

	def _get_license_security_status(self, workshop_code):
		"""Get license-related security status"""
		try:
			# Check recent license validation events
			recent_validations = frappe.get_list(
				"License Audit Log",
				filters={
					"workshop_code": workshop_code,
					"event_type": "License Validation",
					"creation": [">=", datetime.now() - timedelta(hours=24)],
				},
				fields=["severity_level"],
			)

			failed_validations = [v for v in recent_validations if v.severity_level in ["High", "Critical"]]

			return {
				"license_valid": len(failed_validations) == 0,
				"validation_failures": len(failed_validations),
				"last_validation": now() if recent_validations else None,
			}

		except Exception as e:
			frappe.log_error(f"License status check error: {e!s}")
			return {"license_valid": True, "validation_failures": 0}

	def _check_rate_limit(self, endpoint):
		"""Check API rate limits"""
		# Simple rate limiting implementation
		# In production, would use Redis or similar
		cache_key = f"rate_limit_{endpoint}_{frappe.session.user}"

		try:
			current_count = frappe.cache().get(cache_key) or 0
			limit = self.rate_limits.get(endpoint, 100)

			if current_count >= limit:
				return False

			# Increment counter with 1-hour expiry
			frappe.cache().set(cache_key, current_count + 1, expires_in_sec=3600)
			return True

		except Exception:
			# If cache fails, allow the request
			return True


# Create global instance
security_api = SecurityAPIManager()


# Expose whitelisted methods
@frappe.whitelist()
def create_threat_monitor(workshop_code, business_license, threat_data):
	"""API endpoint for creating threat monitors"""
	return security_api.create_threat_monitor(workshop_code, business_license, threat_data)


@frappe.whitelist()
def get_real_time_threats(workshop_code=None, hours=24):
	"""API endpoint for real-time threat data"""
	return security_api.get_real_time_threats(workshop_code, hours)


@frappe.whitelist()
def submit_threat_intelligence(threat_iocs, source="External"):
	"""API endpoint for submitting threat intelligence"""
	return security_api.submit_threat_intelligence(threat_iocs, source)


@frappe.whitelist()
def get_workshop_security_status(workshop_code):
	"""API endpoint for workshop security status"""
	return security_api.get_workshop_security_status(workshop_code)
