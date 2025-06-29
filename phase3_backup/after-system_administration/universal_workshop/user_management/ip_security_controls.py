"""
IP Security Controls for Universal Workshop ERP
Implements whitelist/blacklist and geolocation-based access control
"""

import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime


class IPSecurityControls:
    """IP-based security controls with whitelist/blacklist and geo-restrictions"""

    def __init__(self):
        self.redis_client = frappe.cache()
        self.cache_timeout = 3600  # 1 hour

        # Default Oman-centric policy
        self.default_allowed_countries = ["OM", "AE", "SA", "QA", "KW", "BH"]
        self.default_blocked_countries = ["CN", "RU", "KP", "IR"]

    def validate_ip_access(self, ip_address: str, user_email: str = None) -> Dict[str, Any]:
        """Main IP validation method"""
        result = {"allowed": True, "reason": "", "details": {}}

        try:
            # Check whitelist first (highest priority)
            if self._is_whitelisted(ip_address):
                result["details"]["whitelist"] = True
                return result

            # Check blacklist
            if self._is_blacklisted(ip_address):
                result.update(
                    {"allowed": False, "reason": "IP_BLACKLISTED", "details": {"blacklisted": True}}
                )
                return result

            # Geolocation validation
            geo_result = self._validate_geolocation(ip_address)
            result["details"]["geolocation"] = geo_result

            if not geo_result["allowed"]:
                result.update({"allowed": False, "reason": "GEO_RESTRICTED", "details": geo_result})
                return result

            # VPN/Proxy detection
            threat_result = self._detect_threats(ip_address)
            result["details"]["threats"] = threat_result

            if threat_result["high_risk"]:
                result.update(
                    {"allowed": False, "reason": "HIGH_RISK_IP", "details": threat_result}
                )
                return result

            self._log_ip_check(ip_address, result)
            return result

        except Exception as e:
            frappe.log_error(f"IP validation error for {ip_address}: {e}")
            return {"allowed": False, "reason": "VALIDATION_ERROR"}

    def _is_whitelisted(self, ip_address: str) -> bool:
        """Check if IP is whitelisted"""
        try:
            cache_key = f"ip_whitelist:{ip_address}"
            cached = self.redis_client.get(cache_key)
            if cached is not None:
                return json.loads(cached)

            # Check database
            result = frappe.db.exists(
                "IP Security Rule",
                {"ip_address": ip_address, "rule_type": "Whitelist", "is_active": 1},
            )

            is_whitelisted = bool(result)
            self.redis_client.setex(cache_key, 300, json.dumps(is_whitelisted))
            return is_whitelisted

        except Exception as e:
            frappe.log_error(f"Whitelist check error for {ip_address}: {e}")
            return False

    def _is_blacklisted(self, ip_address: str) -> bool:
        """Check if IP is blacklisted"""
        try:
            cache_key = f"ip_blacklist:{ip_address}"
            cached = self.redis_client.get(cache_key)
            if cached is not None:
                return json.loads(cached)

            result = frappe.db.exists(
                "IP Security Rule",
                {"ip_address": ip_address, "rule_type": "Blacklist", "is_active": 1},
            )

            is_blacklisted = bool(result)
            self.redis_client.setex(cache_key, 300, json.dumps(is_blacklisted))
            return is_blacklisted

        except Exception as e:
            frappe.log_error(f"Blacklist check error for {ip_address}: {e}")
            return False

    def _validate_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Validate IP geolocation"""
        geo_data = self._get_geolocation(ip_address)
        country_code = geo_data.get("country_code", "").upper()

        # Check blocked countries
        if country_code in self.default_blocked_countries:
            return {
                "allowed": False,
                "reason": f"Blocked country: {country_code}",
                "country": geo_data.get("country"),
                "country_code": country_code,
            }

        # For workshop system, we're more lenient than default policy
        # but log suspicious countries
        if country_code and country_code not in self.default_allowed_countries:
            # Log but allow (with elevated monitoring)
            frappe.log_error(f"Access from non-GCC country: {country_code} - {ip_address}")

        return {
            "allowed": True,
            "country": geo_data.get("country"),
            "country_code": country_code,
            "city": geo_data.get("city"),
        }

    def _get_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get IP geolocation data"""
        cache_key = f"geo_data:{ip_address}"
        cached = self.redis_client.get(cache_key)

        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass

        # Skip local/private IPs
        if self._is_private_ip(ip_address):
            geo_data = {
                "country": "Oman",
                "country_code": "OM",
                "city": "Local",
                "organization": "Local Network",
            }
        else:
            geo_data = self._fetch_geolocation(ip_address)

        self.redis_client.setex(cache_key, self.cache_timeout, json.dumps(geo_data))
        return geo_data

    def _fetch_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Fetch geolocation from external API"""
        default = {
            "country": "Unknown",
            "country_code": "XX",
            "city": "Unknown",
            "organization": "Unknown",
        }

        try:
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                timeout=5,
                params={"fields": "status,country,countryCode,city,org"},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "Unknown"),
                        "country_code": data.get("countryCode", "XX"),
                        "city": data.get("city", "Unknown"),
                        "organization": data.get("org", "Unknown"),
                    }
        except Exception as e:
            frappe.log_error(f"Geolocation fetch error for {ip_address}: {e}")

        return default

    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP is private/local"""
        import ipaddress

        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private or ip.is_loopback
        except ValueError:
            return False

    def _detect_threats(self, ip_address: str) -> Dict[str, Any]:
        """Basic threat detection for VPN/Proxy"""
        geo_data = self._get_geolocation(ip_address)
        org = geo_data.get("organization", "").lower()

        threat_indicators = ["vpn", "proxy", "hosting", "datacenter", "cloud"]
        is_suspicious = any(indicator in org for indicator in threat_indicators)

        return {
            "high_risk": False,  # Conservative for workshop system
            "suspicious": is_suspicious,
            "organization": geo_data.get("organization"),
            "threat_level": "medium" if is_suspicious else "low",
        }

    def _log_ip_check(self, ip_address: str, result: Dict):
        """Log IP security check"""
        try:
            from universal_workshop.user_management.security_alerts import log_security_event

            log_security_event(
                "ip_security_check",
                {
                    "ip_address": ip_address,
                    "allowed": result["allowed"],
                    "reason": result.get("reason", ""),
                    "details": result.get("details", {}),
                    "timestamp": now_datetime(),
                    "user": frappe.session.user,
                },
            )
        except Exception as e:
            frappe.log_error(f"Error logging IP check: {e}")

    def add_ip_rule(self, ip_address: str, rule_type: str, description: str = "") -> Dict[str, Any]:
        """Add IP whitelist/blacklist rule"""
        try:
            # Create security rule record
            if not frappe.db.exists("DocType", "IP Security Rule"):
                self._create_ip_security_doctype()

            rule = frappe.new_doc("IP Security Rule")
            rule.update(
                {
                    "ip_address": ip_address,
                    "rule_type": rule_type.title(),
                    "description": description,
                    "created_by": frappe.session.user,
                    "is_active": 1,
                }
            )
            rule.insert()

            # Clear cache
            cache_key = f"ip_{rule_type.lower()}:{ip_address}"
            self.redis_client.delete(cache_key)

            return {"success": True, "rule_id": rule.name}

        except Exception as e:
            frappe.log_error(f"Error adding IP rule: {e}")
            return {"success": False, "error": str(e)}

    def _create_ip_security_doctype(self):
        """Create IP Security Rule DocType if it doesn't exist"""
        doctype = frappe.new_doc("DocType")
        doctype.name = "IP Security Rule"
        doctype.module = "User Management"
        doctype.custom = 1

        fields = [
            {"fieldname": "ip_address", "fieldtype": "Data", "label": "IP Address", "reqd": 1},
            {
                "fieldname": "rule_type",
                "fieldtype": "Select",
                "options": "Whitelist\nBlacklist",
                "label": "Rule Type",
                "reqd": 1,
            },
            {"fieldname": "description", "fieldtype": "Text", "label": "Description"},
            {
                "fieldname": "created_by",
                "fieldtype": "Link",
                "options": "User",
                "label": "Created By",
            },
            {"fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "default": 1},
        ]

        for field in fields:
            field["parent"] = "IP Security Rule"
            field["parenttype"] = "DocType"
            field["parentfield"] = "fields"
            doctype.append("fields", field)

        doctype.insert(ignore_permissions=True)
        frappe.db.commit()


# Global instance
_ip_security = None


def get_ip_security_controls():
    """Get global IP security controls instance"""
    global _ip_security
    if _ip_security is None:
        _ip_security = IPSecurityControls()
    return _ip_security


@frappe.whitelist()
def validate_ip_access(ip_address: str, user_email: str = None):
    """API method to validate IP access"""
    controls = get_ip_security_controls()
    return controls.validate_ip_access(ip_address, user_email)


@frappe.whitelist()
def add_ip_whitelist(ip_address: str, description: str = ""):
    """Add IP to whitelist"""
    controls = get_ip_security_controls()
    return controls.add_ip_rule(ip_address, "Whitelist", description)


@frappe.whitelist()
def add_ip_blacklist(ip_address: str, description: str = ""):
    """Add IP to blacklist"""
    controls = get_ip_security_controls()
    return controls.add_ip_rule(ip_address, "Blacklist", description)
