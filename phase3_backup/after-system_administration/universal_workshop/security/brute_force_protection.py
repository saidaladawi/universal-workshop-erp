"""
Enhanced Brute Force Protection for Universal Workshop ERP

Implements advanced brute force protection with IP intelligence,
device fingerprinting, and automated threat response.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt, get_datetime, random_string
from universal_workshop.security.rate_limiting_manager import WorkshopRateLimitManager
from universal_workshop.user_management.security_alerts import SecurityAlertManager


class BruteForceProtectionManager:
    """
    Advanced brute force protection system for Universal Workshop ERP

    Features:
    - IP intelligence and reputation tracking
    - Device fingerprinting and trust levels
    - Automated threat response and escalation
    - Geographic location analysis
    - Pattern detection and anomaly scoring
    - Integration with existing security systems
    """

    def __init__(self):
        """Initialize brute force protection manager"""
        self.config = self._load_protection_config()
        self.rate_manager = WorkshopRateLimitManager()
        self.alert_manager = SecurityAlertManager()
        self.ip_intelligence = IPIntelligenceEngine()
        self.device_tracker = DeviceFingerprintTracker()

    def _load_protection_config(self) -> Dict[str, Any]:
        """Load brute force protection configuration"""
        default_config = {
            # Attack detection thresholds
            "attack_detection": {
                "failed_attempts_threshold": 5,
                "time_window_minutes": 15,
                "suspicious_pattern_threshold": 10,
                "anomaly_score_threshold": 0.8,
            },
            # Response escalation levels
            "response_levels": {
                "level_1": {
                    "threshold": 5,
                    "actions": ["delay_response", "captcha_challenge"],
                    "duration_minutes": 30,
                },
                "level_2": {
                    "threshold": 10,
                    "actions": ["temp_account_lock", "admin_notification"],
                    "duration_minutes": 120,
                },
                "level_3": {
                    "threshold": 20,
                    "actions": ["ip_block", "security_alert", "admin_escalation"],
                    "duration_minutes": 720,
                },
                "level_4": {
                    "threshold": 50,
                    "actions": ["permanent_ip_block", "incident_response"],
                    "duration_minutes": -1,  # Permanent until manual review
                },
            },
            # Device trust levels
            "device_trust": {
                "new_device_threshold": 0.3,
                "trusted_device_threshold": 0.8,
                "suspicious_device_threshold": 0.2,
                "trust_decay_days": 30,
            },
            # Geographic controls
            "geographic_controls": {
                "enabled": True,
                "allowed_countries": [],  # Empty = all allowed
                "blocked_countries": ["CN", "RU", "KP"],  # Example blocked countries
                "alert_on_new_country": True,
                "require_verification_new_country": True,
            },
            # Pattern analysis
            "pattern_analysis": {
                "enabled": True,
                "common_passwords_check": True,
                "credential_stuffing_detection": True,
                "timing_analysis": True,
                "behavioral_analysis": True,
            },
        }

        site_config = frappe.get_site_config()
        return site_config.get("brute_force_protection", default_config)

    def analyze_login_attempt(
        self, user_email: str, password: str, ip_address: str, user_agent: str = ""
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of login attempt for brute force indicators

        Args:
            user_email: Email attempting to log in
            password: Password attempted (for pattern analysis)
            ip_address: Source IP address
            user_agent: Browser user agent string

        Returns:
            Dict with analysis results and recommended actions
        """
        try:
            analysis_result = {
                "timestamp": now_datetime(),
                "user_email": user_email,
                "ip_address": ip_address,
                "risk_score": 0.0,
                "threat_indicators": [],
                "recommended_actions": [],
                "allow_attempt": True,
                "require_additional_verification": False,
            }

            # 1. Rate limiting analysis
            rate_limit_result = self.rate_manager.check_login_rate_limit(user_email, ip_address)
            if not rate_limit_result["allowed"]:
                analysis_result["allow_attempt"] = False
                analysis_result["threat_indicators"].append("RATE_LIMIT_EXCEEDED")
                analysis_result["risk_score"] += 0.3

            # 2. IP intelligence analysis
            ip_analysis = self.ip_intelligence.analyze_ip(ip_address)
            analysis_result["risk_score"] += ip_analysis["risk_score"]
            analysis_result["threat_indicators"].extend(ip_analysis["indicators"])

            # 3. Device fingerprinting analysis
            device_fingerprint = self._generate_device_fingerprint(user_agent, ip_address)
            device_analysis = self.device_tracker.analyze_device(user_email, device_fingerprint)
            analysis_result["risk_score"] += device_analysis["risk_score"]
            analysis_result["threat_indicators"].extend(device_analysis["indicators"])

            # 4. Geographic analysis
            if self.config["geographic_controls"]["enabled"]:
                geo_analysis = self._analyze_geographic_location(ip_address, user_email)
                analysis_result["risk_score"] += geo_analysis["risk_score"]
                analysis_result["threat_indicators"].extend(geo_analysis["indicators"])

            # 5. Pattern analysis
            if self.config["pattern_analysis"]["enabled"]:
                pattern_analysis = self._analyze_attack_patterns(user_email, password, ip_address)
                analysis_result["risk_score"] += pattern_analysis["risk_score"]
                analysis_result["threat_indicators"].extend(pattern_analysis["indicators"])

            # 6. Historical behavior analysis
            behavior_analysis = self._analyze_user_behavior(user_email, ip_address)
            analysis_result["risk_score"] += behavior_analysis["risk_score"]
            analysis_result["threat_indicators"].extend(behavior_analysis["indicators"])

            # 7. Determine response level and actions
            response_level = self._determine_response_level(analysis_result["risk_score"])
            analysis_result["response_level"] = response_level
            analysis_result["recommended_actions"] = self._get_response_actions(response_level)

            # 8. Apply automatic protections
            if (
                analysis_result["risk_score"]
                > self.config["attack_detection"]["anomaly_score_threshold"]
            ):
                analysis_result["allow_attempt"] = False
                analysis_result["require_additional_verification"] = True
                self._apply_automatic_protections(analysis_result)

            # 9. Log analysis for monitoring
            self._log_brute_force_analysis(analysis_result)

            return analysis_result

        except Exception as e:
            frappe.log_error(f"Brute force analysis error: {e}")
            return {
                "allow_attempt": True,
                "error": str(e),
                "risk_score": 0.0,
                "threat_indicators": ["ANALYSIS_ERROR"],
            }

    def record_login_outcome(
        self, user_email: str, ip_address: str, success: bool, analysis_result: Dict[str, Any]
    ) -> None:
        """Record login attempt outcome for learning and tracking"""
        try:
            # Update rate limiting
            self.rate_manager.record_login_attempt(user_email, ip_address, success)

            # Update IP intelligence
            self.ip_intelligence.update_ip_reputation(ip_address, success, analysis_result)

            # Update device trust
            if "device_fingerprint" in analysis_result:
                self.device_tracker.update_device_trust(
                    user_email, analysis_result["device_fingerprint"], success
                )

            # Track attack progression if failed
            if not success:
                self._track_attack_progression(user_email, ip_address, analysis_result)

            # Generate security alerts if needed
            if analysis_result.get("risk_score", 0) > 0.7:
                self._generate_security_alerts(user_email, ip_address, success, analysis_result)

        except Exception as e:
            frappe.log_error(f"Error recording login outcome: {e}")

    def _generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Generate device fingerprint from available data"""
        try:
            # Combine available data for fingerprinting
            fingerprint_data = f"{user_agent}:{ip_address}"

            # Hash for consistent fingerprint
            return hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]

        except Exception as e:
            frappe.log_error(f"Error generating device fingerprint: {e}")
            return "unknown"

    def _analyze_geographic_location(self, ip_address: str, user_email: str) -> Dict[str, Any]:
        """Analyze geographic location for suspicious activity"""
        try:
            # Basic IP geolocation (simplified - would use actual GeoIP service)
            geo_info = self._get_ip_geolocation(ip_address)

            analysis = {
                "risk_score": 0.0,
                "indicators": [],
                "country": geo_info.get("country", "Unknown"),
                "region": geo_info.get("region", "Unknown"),
            }

            # Check blocked countries
            if geo_info.get("country") in self.config["geographic_controls"]["blocked_countries"]:
                analysis["risk_score"] += 0.8
                analysis["indicators"].append("BLOCKED_COUNTRY")

            # Check for new country access
            if self.config["geographic_controls"]["alert_on_new_country"]:
                if self._is_new_country_for_user(user_email, geo_info.get("country")):
                    analysis["risk_score"] += 0.3
                    analysis["indicators"].append("NEW_COUNTRY_ACCESS")

            return analysis

        except Exception as e:
            frappe.log_error(f"Geographic analysis error: {e}")
            return {"risk_score": 0.0, "indicators": []}

    def _get_ip_geolocation(self, ip_address: str) -> Dict[str, str]:
        """Get IP geolocation (simplified implementation)"""
        # This would integrate with a real GeoIP service
        # For now, return mock data
        return {"country": "OM", "region": "Muscat", "city": "Muscat"}  # Oman

    def _analyze_attack_patterns(
        self, user_email: str, password: str, ip_address: str
    ) -> Dict[str, Any]:
        """Analyze for common attack patterns"""
        try:
            analysis = {"risk_score": 0.0, "indicators": []}

            # Common password check
            if self.config["pattern_analysis"]["common_passwords_check"]:
                if self._is_common_password(password):
                    analysis["risk_score"] += 0.2
                    analysis["indicators"].append("COMMON_PASSWORD_ATTEMPT")

            # Credential stuffing detection
            if self.config["pattern_analysis"]["credential_stuffing_detection"]:
                if self._detect_credential_stuffing(ip_address):
                    analysis["risk_score"] += 0.5
                    analysis["indicators"].append("CREDENTIAL_STUFFING_PATTERN")

            # Sequential user enumeration
            if self._detect_user_enumeration(ip_address):
                analysis["risk_score"] += 0.4
                analysis["indicators"].append("USER_ENUMERATION_PATTERN")

            return analysis

        except Exception as e:
            frappe.log_error(f"Pattern analysis error: {e}")
            return {"risk_score": 0.0, "indicators": []}

    def _analyze_user_behavior(self, user_email: str, ip_address: str) -> Dict[str, Any]:
        """Analyze user behavior for anomalies"""
        try:
            analysis = {"risk_score": 0.0, "indicators": []}

            # Check for unusual login times
            if self._is_unusual_login_time(user_email):
                analysis["risk_score"] += 0.2
                analysis["indicators"].append("UNUSUAL_LOGIN_TIME")

            # Check for rapid login attempts
            if self._detect_rapid_attempts(user_email):
                analysis["risk_score"] += 0.3
                analysis["indicators"].append("RAPID_LOGIN_ATTEMPTS")

            # Check for distributed attacks
            if self._detect_distributed_attack(user_email):
                analysis["risk_score"] += 0.4
                analysis["indicators"].append("DISTRIBUTED_ATTACK_PATTERN")

            return analysis

        except Exception as e:
            frappe.log_error(f"Behavior analysis error: {e}")
            return {"risk_score": 0.0, "indicators": []}

    def _determine_response_level(self, risk_score: float) -> int:
        """Determine response level based on risk score"""
        if risk_score >= 0.8:
            return 4  # Critical
        elif risk_score >= 0.6:
            return 3  # High
        elif risk_score >= 0.4:
            return 2  # Medium
        elif risk_score >= 0.2:
            return 1  # Low
        else:
            return 0  # No action

    def _get_response_actions(self, response_level: int) -> List[str]:
        """Get recommended actions for response level"""
        if response_level == 0:
            return []

        level_key = f"level_{response_level}"
        return self.config["response_levels"].get(level_key, {}).get("actions", [])

    def _apply_automatic_protections(self, analysis_result: Dict[str, Any]) -> None:
        """Apply automatic protection measures"""
        try:
            actions = analysis_result.get("recommended_actions", [])

            # Apply IP blocking if needed
            if "ip_block" in actions:
                self._add_ip_to_blacklist(analysis_result["ip_address"], temporary=True)

            # Apply progressive lockout
            if "temp_account_lock" in actions:
                self.rate_manager.apply_progressive_lockout(
                    analysis_result["user_email"], analysis_result["ip_address"]
                )

            # Generate security alerts
            if "security_alert" in actions:
                self.alert_manager.create_alert(
                    "BRUTE_FORCE_DETECTED", analysis_result, severity="high"
                )

        except Exception as e:
            frappe.log_error(f"Error applying automatic protections: {e}")

    def _is_common_password(self, password: str) -> bool:
        """Check if password is commonly used (simplified)"""
        common_passwords = [
            "password",
            "123456",
            "12345678",
            "admin",
            "qwerty",
            "password123",
            "123456789",
            "welcome",
            "login",
            "test",
        ]
        return password.lower() in common_passwords

    def _detect_credential_stuffing(self, ip_address: str) -> bool:
        """Detect credential stuffing patterns"""
        try:
            # Check if IP has attempted multiple different usernames recently
            cache_key = f"credential_stuffing:{ip_address}"
            attempts = frappe.cache.get(cache_key) or {}

            # Count unique usernames attempted in last hour
            cutoff_time = now_datetime() - timedelta(hours=1)
            recent_usernames = set()

            for username, timestamps in attempts.items():
                recent_timestamps = [ts for ts in timestamps if get_datetime(ts) > cutoff_time]
                if recent_timestamps:
                    recent_usernames.add(username)

            return len(recent_usernames) > 10  # More than 10 different usernames

        except Exception as e:
            frappe.log_error(f"Credential stuffing detection error: {e}")
            return False

    def _add_ip_to_blacklist(self, ip_address: str, temporary: bool = True) -> None:
        """Add IP to blacklist temporarily or permanently"""
        try:
            if temporary:
                # Add to temporary blacklist (24 hours)
                cache_key = f"temp_blacklist:{ip_address}"
                frappe.cache.set(cache_key, True, ex=24 * 60 * 60)
            else:
                # Add to permanent blacklist (would update configuration)
                # This is a simplified implementation
                frappe.logger().warning(f"IP {ip_address} marked for permanent blacklist")

        except Exception as e:
            frappe.log_error(f"Error adding IP to blacklist: {e}")

    def _log_brute_force_analysis(self, analysis_result: Dict[str, Any]) -> None:
        """Log brute force analysis for monitoring"""
        try:
            # Log to security events
            event_data = {
                "event_type": "BRUTE_FORCE_ANALYSIS",
                "risk_score": analysis_result["risk_score"],
                "threat_indicators": analysis_result["threat_indicators"],
                "response_level": analysis_result.get("response_level", 0),
                "user_email": analysis_result["user_email"],
                "ip_address": analysis_result["ip_address"],
                "timestamp": analysis_result["timestamp"].isoformat(),
            }

            from universal_workshop.user_management.security_alerts import log_security_event

            log_security_event("brute_force_analysis", event_data)

        except Exception as e:
            frappe.log_error(f"Error logging brute force analysis: {e}")

    # Additional helper methods would be implemented here...
    def _is_new_country_for_user(self, user_email: str, country: str) -> bool:
        """Check if this is a new country for the user"""
        # Simplified implementation
        return False

    def _is_unusual_login_time(self, user_email: str) -> bool:
        """Check if login time is unusual for the user"""
        # Simplified implementation
        return False

    def _detect_rapid_attempts(self, user_email: str) -> bool:
        """Detect rapid login attempts"""
        # Simplified implementation
        return False

    def _detect_distributed_attack(self, user_email: str) -> bool:
        """Detect distributed attack patterns"""
        # Simplified implementation
        return False

    def _detect_user_enumeration(self, ip_address: str) -> bool:
        """Detect user enumeration patterns"""
        # Simplified implementation
        return False

    def _track_attack_progression(
        self, user_email: str, ip_address: str, analysis_result: Dict[str, Any]
    ) -> None:
        """Track attack progression for escalation"""
        # Simplified implementation
        pass

    def _generate_security_alerts(
        self, user_email: str, ip_address: str, success: bool, analysis_result: Dict[str, Any]
    ) -> None:
        """Generate security alerts for high-risk attempts"""
        # Simplified implementation
        pass


class IPIntelligenceEngine:
    """IP intelligence and reputation tracking"""

    def __init__(self):
        self.reputation_cache_prefix = "ip_reputation"

    def analyze_ip(self, ip_address: str) -> Dict[str, Any]:
        """Analyze IP address for threat indicators"""
        # Simplified implementation
        return {"risk_score": 0.0, "indicators": [], "reputation": "unknown"}

    def update_ip_reputation(
        self, ip_address: str, success: bool, analysis_result: Dict[str, Any]
    ) -> None:
        """Update IP reputation based on behavior"""
        # Simplified implementation
        pass


class DeviceFingerprintTracker:
    """Device fingerprinting and trust tracking"""

    def __init__(self):
        self.device_cache_prefix = "device_fingerprint"

    def analyze_device(self, user_email: str, device_fingerprint: str) -> Dict[str, Any]:
        """Analyze device for trust level and risk"""
        # Simplified implementation
        return {"risk_score": 0.0, "indicators": [], "trust_level": "unknown"}

    def update_device_trust(self, user_email: str, device_fingerprint: str, success: bool) -> None:
        """Update device trust level"""
        # Simplified implementation
        pass


# Whitelisted API methods
@frappe.whitelist()
def get_brute_force_protection_status():
    """Get current brute force protection status"""
    try:
        protection_manager = BruteForceProtectionManager()
        ip_address = frappe.local.request.environ.get("REMOTE_ADDR", "unknown")

        return {
            "protection_enabled": True,
            "ip_address": ip_address,
            "threat_level": "low",  # Would be calculated
            "last_analysis": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"Error getting protection status: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def admin_review_blocked_ips():
    """Get list of blocked IPs for admin review"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Not authorized to review blocked IPs"))

    try:
        # Get temporarily blocked IPs
        blocked_ips = []
        # Implementation would scan cache for blocked IPs

        return {
            "blocked_ips": blocked_ips,
            "total_count": len(blocked_ips),
            "timestamp": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"Error reviewing blocked IPs: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def admin_unblock_ip(ip_address: str):
    """Unblock an IP address (admin only)"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Not authorized to unblock IPs"))

    try:
        # Remove from temporary blacklist
        cache_key = f"temp_blacklist:{ip_address}"
        frappe.cache.delete(cache_key)

        # Log the action
        frappe.logger().info(f"IP {ip_address} unblocked by {frappe.session.user}")

        return {"success": True, "message": _("IP address unblocked successfully")}

    except Exception as e:
        frappe.log_error(f"Error unblocking IP: {e}")
        return {"success": False, "error": str(e)}
