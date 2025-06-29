"""
IP Security Manager for Universal Workshop ERP

Comprehensive IP security controls including whitelist/blacklist management,
geolocation restrictions, and VPN/proxy detection for enhanced security.
"""

import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, get_datetime


@dataclass
class IPSecurityRule:
    """IP security rule configuration"""

    ip_address: str
    rule_type: str  # 'whitelist', 'blacklist', 'geo_restrict'
    description: str = ""
    created_by: str = ""
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IPSecurityRule":
        return cls(**data)


@dataclass
class GeolocationPolicy:
    """Geolocation-based access policy"""

    allowed_countries: List[str]  # ISO country codes
    blocked_countries: List[str]
    allow_vpn: bool = False
    allow_proxy: bool = False
    allow_tor: bool = False
    require_geo_validation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeolocationPolicy":
        return cls(**data)


class IPSecurityManager:
    """
    Advanced IP Security Control System

    Features:
    - IP whitelist/blacklist management
    - Geolocation-based access control
    - VPN/Proxy/Tor detection
    - Country-based restrictions
    - Dynamic rule management
    """

    def __init__(self):
        self.cache_timeout = 3600  # 1 hour cache for geo data
        self.redis_client = frappe.cache()

        # Default geolocation policy (Oman-focused)
        self.default_geo_policy = GeolocationPolicy(
            allowed_countries=["OM", "AE", "SA", "QA", "KW", "BH"],  # GCC countries
            blocked_countries=["CN", "RU", "KP"],  # Known high-risk countries
            allow_vpn=False,
            allow_proxy=False,
            allow_tor=False,
            require_geo_validation=True,
        )

        # Initialize security rules storage
        self._ensure_security_tables()

    def _ensure_security_tables(self):
        """Ensure IP security tables exist"""
        try:
            if not frappe.db.exists("DocType", "IP Security Rule"):
                self._create_ip_security_doctype()
        except Exception as e:
            frappe.log_error(f"Error creating IP security tables: {e}")

    def _create_ip_security_doctype(self):
        """Create DocType for IP security rules"""
        doctype = frappe.new_doc("DocType")
        doctype.name = "IP Security Rule"
        doctype.module = "User Management"
        doctype.custom = 1
        doctype.is_submittable = 0
        doctype.track_changes = 1

        fields = [
            {"fieldname": "ip_address", "fieldtype": "Data", "label": "IP Address", "reqd": 1},
            {
                "fieldname": "rule_type",
                "fieldtype": "Select",
                "options": "Whitelist\nBlacklist\nGeo Restrict",
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
            {"fieldname": "expires_at", "fieldtype": "Datetime", "label": "Expires At"},
            {"fieldname": "is_active", "fieldtype": "Check", "label": "Is Active", "default": 1},
            {"fieldname": "country_code", "fieldtype": "Data", "label": "Country Code"},
            {"fieldname": "city", "fieldtype": "Data", "label": "City"},
            {"fieldname": "organization", "fieldtype": "Data", "label": "Organization"},
            {
                "fieldname": "threat_level",
                "fieldtype": "Select",
                "options": "Low\nMedium\nHigh\nCritical",
                "label": "Threat Level",
            },
        ]

        for field in fields:
            field["parent"] = "IP Security Rule"
            field["parenttype"] = "DocType"
            field["parentfield"] = "fields"
            doctype.append("fields", field)

        doctype.insert(ignore_permissions=True)
        frappe.db.commit()

    # =============================================================================
    # IP Security Validation
    # =============================================================================

    def validate_ip_access(self, ip_address: str, user_email: str = None) -> Dict[str, Any]:
        """
        Comprehensive IP access validation

        Args:
            ip_address: IP address to validate
            user_email: User email for role-based validation

        Returns:
            Validation result with access decision and details
        """
        result = {
            "allowed": True,
            "reason": "",
            "details": {},
            "threat_level": "low",
            "requires_mfa": False,
        }

        try:
            # Check whitelist first (highest priority)
            whitelist_check = self._check_whitelist(ip_address)
            if whitelist_check["is_whitelisted"]:
                result["details"]["whitelist"] = "IP is whitelisted"
                return result

            # Check blacklist (second priority)
            blacklist_check = self._check_blacklist(ip_address)
            if blacklist_check["is_blacklisted"]:
                result.update(
                    {
                        "allowed": False,
                        "reason": "IP_BLACKLISTED",
                        "details": blacklist_check,
                        "threat_level": "high",
                    }
                )
                return result

            # Get geolocation data
            geo_data = self._get_geolocation_data(ip_address)
            result["details"]["geolocation"] = geo_data

            # Apply geolocation policy
            geo_policy = self._get_geolocation_policy(user_email)
            geo_validation = self._validate_geolocation(geo_data, geo_policy)

            if not geo_validation["allowed"]:
                result.update(
                    {
                        "allowed": False,
                        "reason": "GEO_RESTRICTED",
                        "details": {**result["details"], **geo_validation},
                        "threat_level": "medium",
                    }
                )
                return result

            # Check for VPN/Proxy/Tor
            threat_analysis = self._analyze_ip_threats(ip_address, geo_data)
            result["details"]["threat_analysis"] = threat_analysis

            if threat_analysis["threat_level"] in ["high", "critical"]:
                if not geo_policy.allow_vpn and threat_analysis["is_vpn"]:
                    result.update(
                        {"allowed": False, "reason": "VPN_BLOCKED", "threat_level": "medium"}
                    )
                    return result

                if not geo_policy.allow_proxy and threat_analysis["is_proxy"]:
                    result.update(
                        {"allowed": False, "reason": "PROXY_BLOCKED", "threat_level": "medium"}
                    )
                    return result

                if not geo_policy.allow_tor and threat_analysis["is_tor"]:
                    result.update(
                        {"allowed": False, "reason": "TOR_BLOCKED", "threat_level": "high"}
                    )
                    return result

            # Require MFA for suspicious activities
            if threat_analysis["threat_level"] in ["medium", "high"]:
                result["requires_mfa"] = True

            result["threat_level"] = threat_analysis["threat_level"]

            # Log security check
            self._log_ip_security_check(ip_address, result)

            return result

        except Exception as e:
            frappe.log_error(f"Error validating IP access for {ip_address}: {e}")
            # Fail secure - deny access on error
            return {
                "allowed": False,
                "reason": "SECURITY_CHECK_ERROR",
                "details": {"error": str(e)},
                "threat_level": "high",
            }

    def _check_whitelist(self, ip_address: str) -> Dict[str, Any]:
        """Check if IP is whitelisted"""
        try:
            rules = frappe.get_list(
                "IP Security Rule",
                filters={"ip_address": ip_address, "rule_type": "Whitelist", "is_active": 1},
                fields=["name", "description", "expires_at"],
            )

            for rule in rules:
                if not rule.expires_at or get_datetime(rule.expires_at) > now_datetime():
                    return {
                        "is_whitelisted": True,
                        "rule_id": rule.name,
                        "description": rule.description,
                    }

            return {"is_whitelisted": False}

        except Exception as e:
            frappe.log_error(f"Error checking whitelist for {ip_address}: {e}")
            return {"is_whitelisted": False}

    def _check_blacklist(self, ip_address: str) -> Dict[str, Any]:
        """Check if IP is blacklisted"""
        try:
            rules = frappe.get_list(
                "IP Security Rule",
                filters={"ip_address": ip_address, "rule_type": "Blacklist", "is_active": 1},
                fields=["name", "description", "threat_level", "expires_at"],
            )

            for rule in rules:
                if not rule.expires_at or get_datetime(rule.expires_at) > now_datetime():
                    return {
                        "is_blacklisted": True,
                        "rule_id": rule.name,
                        "description": rule.description,
                        "threat_level": rule.threat_level or "medium",
                    }

            return {"is_blacklisted": False}

        except Exception as e:
            frappe.log_error(f"Error checking blacklist for {ip_address}: {e}")
            return {"is_blacklisted": False}

    def _get_geolocation_data(self, ip_address: str) -> Dict[str, Any]:
        """Get geolocation data for IP address"""
        cache_key = f"geo_data:{ip_address}"
        cached_data = self.redis_client.get(cache_key)

        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                pass

        # Get geolocation from multiple sources
        geo_data = self._fetch_geolocation_data(ip_address)

        # Cache the result
        self.redis_client.setex(cache_key, self.cache_timeout, json.dumps(geo_data))

        return geo_data

    def _fetch_geolocation_data(self, ip_address: str) -> Dict[str, Any]:
        """Fetch geolocation data from external APIs"""
        default_data = {
            "country": "unknown",
            "country_code": "xx",
            "city": "unknown",
            "region": "unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "organization": "unknown",
            "isp": "unknown",
            "timezone": "unknown",
        }

        # Skip private/local IP addresses
        if self._is_private_ip(ip_address):
            default_data.update(
                {
                    "country": "Local",
                    "country_code": "OM",  # Assume Oman for local IPs
                    "organization": "Local Network",
                }
            )
            return default_data

        try:
            # Try ip-api.com (free service)
            response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "country": data.get("country", "unknown"),
                        "country_code": data.get("countryCode", "xx").upper(),
                        "city": data.get("city", "unknown"),
                        "region": data.get("regionName", "unknown"),
                        "latitude": data.get("lat", 0.0),
                        "longitude": data.get("lon", 0.0),
                        "organization": data.get("org", "unknown"),
                        "isp": data.get("isp", "unknown"),
                        "timezone": data.get("timezone", "unknown"),
                    }

        except Exception as e:
            frappe.log_error(f"Error fetching geolocation for {ip_address}: {e}")

        return default_data

    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP is private/local"""
        import ipaddress

        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            return False

    def _get_geolocation_policy(self, user_email: str = None) -> GeolocationPolicy:
        """Get geolocation policy for user/system"""
        if user_email:
            try:
                user_doc = frappe.get_doc("User", user_email)
                custom_policy = getattr(user_doc, "geo_policy", None)
                if custom_policy:
                    policy_data = json.loads(custom_policy)
                    return GeolocationPolicy.from_dict(policy_data)
            except Exception:
                pass

        return self.default_geo_policy

    def _validate_geolocation(self, geo_data: Dict, policy: GeolocationPolicy) -> Dict[str, Any]:
        """Validate geolocation against policy"""
        country_code = geo_data.get("country_code", "").upper()

        # Check blocked countries first
        if country_code in policy.blocked_countries:
            return {
                "allowed": False,
                "reason": f"Country {country_code} is blocked",
                "country_code": country_code,
            }

        # Check allowed countries
        if policy.allowed_countries and country_code not in policy.allowed_countries:
            return {
                "allowed": False,
                "reason": f"Country {country_code} not in allowed list",
                "country_code": country_code,
                "allowed_countries": policy.allowed_countries,
            }

        return {"allowed": True, "country_code": country_code}

    def _analyze_ip_threats(self, ip_address: str, geo_data: Dict) -> Dict[str, Any]:
        """Analyze IP for threats (VPN, proxy, Tor, etc.)"""
        threat_analysis = {
            "is_vpn": False,
            "is_proxy": False,
            "is_tor": False,
            "is_suspicious": False,
            "threat_level": "low",
            "threat_indicators": [],
        }

        try:
            # Basic threat detection based on organization/ISP
            org = geo_data.get("organization", "").lower()
            isp = geo_data.get("isp", "").lower()

            # VPN indicators
            vpn_indicators = ["vpn", "virtual private", "proxy", "tunnel", "anonymous"]
            if any(indicator in org or indicator in isp for indicator in vpn_indicators):
                threat_analysis["is_vpn"] = True
                threat_analysis["threat_indicators"].append("VPN service detected")

            # Proxy indicators
            proxy_indicators = ["proxy", "datacenter", "hosting", "cloud", "server"]
            if any(indicator in org or indicator in isp for indicator in proxy_indicators):
                threat_analysis["is_proxy"] = True
                threat_analysis["threat_indicators"].append("Proxy/hosting service detected")

            # Tor indicators (basic detection)
            tor_indicators = ["tor", "onion", "relay"]
            if any(indicator in org or indicator in isp for indicator in tor_indicators):
                threat_analysis["is_tor"] = True
                threat_analysis["threat_indicators"].append("Tor network detected")

            # Calculate threat level
            threat_count = sum(
                [threat_analysis["is_vpn"], threat_analysis["is_proxy"], threat_analysis["is_tor"]]
            )

            if threat_count >= 2:
                threat_analysis["threat_level"] = "critical"
            elif threat_count == 1:
                threat_analysis["threat_level"] = "high"
            elif threat_analysis["threat_indicators"]:
                threat_analysis["threat_level"] = "medium"

            threat_analysis["is_suspicious"] = threat_count > 0

        except Exception as e:
            frappe.log_error(f"Error analyzing IP threats for {ip_address}: {e}")
            threat_analysis["threat_level"] = "unknown"

        return threat_analysis

    def _log_ip_security_check(self, ip_address: str, result: Dict):
        """Log IP security check for audit"""
        try:
            log_data = {
                "event_type": "ip_security_check",
                "ip_address": ip_address,
                "allowed": result["allowed"],
                "reason": result.get("reason", ""),
                "threat_level": result.get("threat_level", "low"),
                "details": result.get("details", {}),
                "timestamp": now_datetime(),
                "user": frappe.session.user,
            }

            # Log to security events
            from universal_workshop.user_management.security_alerts import log_security_event

            log_security_event("ip_security_check", log_data)

        except Exception as e:
            frappe.log_error(f"Error logging IP security check: {e}")

    # =============================================================================
    # Rule Management Methods
    # =============================================================================

    def add_ip_rule(
        self, ip_address: str, rule_type: str, description: str = "", expires_in_hours: int = None
    ) -> Dict[str, Any]:
        """Add new IP security rule"""
        try:
            expires_at = None
            if expires_in_hours:
                expires_at = now_datetime() + timedelta(hours=expires_in_hours)

            rule = frappe.new_doc("IP Security Rule")
            rule.update(
                {
                    "ip_address": ip_address,
                    "rule_type": rule_type.title(),
                    "description": description,
                    "created_by": frappe.session.user,
                    "expires_at": expires_at,
                    "is_active": 1,
                }
            )

            # Add geolocation data for context
            if rule_type.lower() in ["blacklist", "geo_restrict"]:
                geo_data = self._get_geolocation_data(ip_address)
                rule.country_code = geo_data.get("country_code")
                rule.city = geo_data.get("city")
                rule.organization = geo_data.get("organization")

            rule.insert()
            frappe.db.commit()

            return {
                "success": True,
                "rule_id": rule.name,
                "message": f"IP rule added successfully for {ip_address}",
            }

        except Exception as e:
            frappe.log_error(f"Error adding IP rule for {ip_address}: {e}")
            return {"success": False, "error": str(e)}

    def remove_ip_rule(self, rule_id: str) -> Dict[str, Any]:
        """Remove IP security rule"""
        try:
            rule = frappe.get_doc("IP Security Rule", rule_id)
            rule.is_active = 0
            rule.save()
            frappe.db.commit()

            return {"success": True, "message": f"IP rule {rule_id} deactivated successfully"}

        except Exception as e:
            frappe.log_error(f"Error removing IP rule {rule_id}: {e}")
            return {"success": False, "error": str(e)}


# =============================================================================
# Global Instance and API Methods
# =============================================================================

_ip_security_manager = None


def get_ip_security_manager() -> IPSecurityManager:
    """Get global IP security manager instance"""
    global _ip_security_manager
    if _ip_security_manager is None:
        _ip_security_manager = IPSecurityManager()
    return _ip_security_manager


@frappe.whitelist()
def validate_ip_access(ip_address: str, user_email: str = None) -> Dict[str, Any]:
    """Validate IP access (whitelisted API method)"""
    manager = get_ip_security_manager()
    return manager.validate_ip_access(ip_address, user_email)


@frappe.whitelist()
def add_ip_whitelist(
    ip_address: str, description: str = "", expires_in_hours: int = None
) -> Dict[str, Any]:
    """Add IP to whitelist"""
    manager = get_ip_security_manager()
    return manager.add_ip_rule(ip_address, "Whitelist", description, expires_in_hours)


@frappe.whitelist()
def add_ip_blacklist(
    ip_address: str, description: str = "", expires_in_hours: int = None
) -> Dict[str, Any]:
    """Add IP to blacklist"""
    manager = get_ip_security_manager()
    return manager.add_ip_rule(ip_address, "Blacklist", description, expires_in_hours)


@frappe.whitelist()
def remove_ip_rule(rule_id: str) -> Dict[str, Any]:
    """Remove IP security rule"""
    manager = get_ip_security_manager()
    return manager.remove_ip_rule(rule_id)


@frappe.whitelist()
def get_ip_geolocation(ip_address: str) -> Dict[str, Any]:
    """Get IP geolocation data"""
    manager = get_ip_security_manager()
    return manager._get_geolocation_data(ip_address)


def ip_security_hook(ip_address: str, user_email: str = None) -> bool:
    """Hook function for integration with other systems"""
    try:
        manager = get_ip_security_manager()
        result = manager.validate_ip_access(ip_address, user_email)
        return result["allowed"]
    except Exception as e:
        frappe.log_error(f"Error in IP security hook: {e}")
        return False  # Fail secure
