"""
Rate Limiting Manager for Universal Workshop ERP

Implements comprehensive rate limiting for login attempts, API endpoints,
and user actions with progressive penalties and IP-based controls.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt, get_datetime
from frappe.rate_limiter import rate_limit, RateLimiter


class WorkshopRateLimitManager:
    """
    Advanced rate limiting manager for Universal Workshop ERP

    Provides multi-layered rate limiting with:
    - Progressive penalties for repeated violations
    - IP-based tracking and controls
    - User-based rate limiting
    - Endpoint-specific limits
    - Integration with existing security systems
    """

    def __init__(self):
        """Initialize rate limiting manager"""
        self.config = self._load_rate_limit_config()
        self.violation_tracker = RateLimitViolationTracker()

    def _load_rate_limit_config(self) -> Dict[str, Any]:
        """Load rate limiting configuration"""
        default_config = {
            # Login rate limits
            "login_attempts": {
                "limit": 5,
                "window_minutes": 15,
                "lockout_minutes": 30,
                "progressive_lockout": True,
            },
            # API endpoint rate limits
            "api_endpoints": {
                "workshop_data": {"limit": 100, "window_minutes": 60},
                "customer_search": {"limit": 50, "window_minutes": 5},
                "vehicle_lookup": {"limit": 30, "window_minutes": 5},
                "service_creation": {"limit": 20, "window_minutes": 60},
                "payment_processing": {"limit": 10, "window_minutes": 60},
            },
            # User action rate limits
            "user_actions": {
                "file_upload": {"limit": 20, "window_minutes": 60},
                "report_generation": {"limit": 10, "window_minutes": 60},
                "export_data": {"limit": 5, "window_minutes": 60},
                "print_documents": {"limit": 50, "window_minutes": 60},
            },
            # IP-based controls
            "ip_controls": {
                "max_users_per_ip": 10,
                "suspicious_ip_threshold": 50,
                "block_duration_minutes": 60,
                "whitelist_ips": [],
                "blacklist_ips": [],
            },
            # Progressive penalties
            "progressive_penalties": {
                "enabled": True,
                "violation_levels": [
                    {"violations": 3, "lockout_minutes": 15},
                    {"violations": 5, "lockout_minutes": 60},
                    {"violations": 10, "lockout_minutes": 240},
                    {"violations": 20, "lockout_minutes": 1440},  # 24 hours
                ],
            },
        }

        # Merge with site config if available
        site_config = frappe.get_site_config()
        return site_config.get("workshop_rate_limits", default_config)

    def check_login_rate_limit(self, user_email: str, ip_address: str) -> Dict[str, Any]:
        """
        Check if login attempt is within rate limits

        Args:
            user_email: User attempting to log in
            ip_address: IP address of the request

        Returns:
            Dict with rate limit status and actions
        """
        try:
            # Check IP blacklist
            if self._is_ip_blacklisted(ip_address):
                return {
                    "allowed": False,
                    "reason": "IP_BLACKLISTED",
                    "message": _("Your IP address has been blocked"),
                    "retry_after": None,
                }

            # Check IP whitelist (if enabled)
            if self.config["ip_controls"]["whitelist_ips"] and not self._is_ip_whitelisted(
                ip_address
            ):
                return {
                    "allowed": False,
                    "reason": "IP_NOT_WHITELISTED",
                    "message": _("Access restricted to authorized IP addresses"),
                    "retry_after": None,
                }

            # Check user-specific login limits
            user_limit_result = self._check_user_login_limits(user_email)
            if not user_limit_result["allowed"]:
                return user_limit_result

            # Check IP-specific login limits
            ip_limit_result = self._check_ip_login_limits(ip_address)
            if not ip_limit_result["allowed"]:
                return ip_limit_result

            # Check progressive penalties
            penalty_result = self._check_progressive_penalties(user_email, ip_address)
            if not penalty_result["allowed"]:
                return penalty_result

            return {
                "allowed": True,
                "remaining_attempts": user_limit_result.get("remaining_attempts"),
                "reset_time": user_limit_result.get("reset_time"),
            }

        except Exception as e:
            frappe.log_error(f"Rate limit check error: {e}")
            return {"allowed": True, "error": str(e)}  # Fail open for availability

    def record_login_attempt(self, user_email: str, ip_address: str, success: bool) -> None:
        """Record login attempt for rate limiting"""
        try:
            timestamp = now_datetime()

            # Record user attempt
            self._record_user_attempt(user_email, timestamp, success)

            # Record IP attempt
            self._record_ip_attempt(ip_address, timestamp, success)

            # Track violations if failed
            if not success:
                self.violation_tracker.record_violation(user_email, ip_address, "LOGIN_FAILED")

            # Log for audit
            self._log_login_attempt(user_email, ip_address, success, timestamp)

        except Exception as e:
            frappe.log_error(f"Error recording login attempt: {e}")

    def check_api_rate_limit(self, endpoint: str, user: str, ip_address: str) -> Dict[str, Any]:
        """Check rate limits for API endpoints"""
        try:
            endpoint_config = self.config["api_endpoints"].get(endpoint)
            if not endpoint_config:
                return {"allowed": True}  # No specific limits for this endpoint

            # Generate cache keys
            user_key = f"api_rate_limit:user:{endpoint}:{user}"
            ip_key = f"api_rate_limit:ip:{endpoint}:{ip_address}"

            # Check user-based limits
            user_result = self._check_rate_limit(
                user_key, endpoint_config["limit"], endpoint_config["window_minutes"] * 60
            )

            # Check IP-based limits (higher threshold)
            ip_result = self._check_rate_limit(
                ip_key,
                endpoint_config["limit"] * 3,  # 3x limit for IP
                endpoint_config["window_minutes"] * 60,
            )

            if not user_result["allowed"] or not ip_result["allowed"]:
                return {
                    "allowed": False,
                    "reason": "API_RATE_LIMIT_EXCEEDED",
                    "message": _("API rate limit exceeded. Please try again later."),
                    "retry_after": max(
                        user_result.get("retry_after", 0), ip_result.get("retry_after", 0)
                    ),
                }

            return {"allowed": True}

        except Exception as e:
            frappe.log_error(f"API rate limit check error: {e}")
            return {"allowed": True}  # Fail open

    def _check_user_login_limits(self, user_email: str) -> Dict[str, Any]:
        """Check user-specific login rate limits"""
        config = self.config["login_attempts"]
        cache_key = f"login_attempts:user:{user_email}"

        return self._check_rate_limit(cache_key, config["limit"], config["window_minutes"] * 60)

    def _check_ip_login_limits(self, ip_address: str) -> Dict[str, Any]:
        """Check IP-specific login rate limits"""
        config = self.config["login_attempts"]
        cache_key = f"login_attempts:ip:{ip_address}"

        # Use higher threshold for IP-based limits
        return self._check_rate_limit(
            cache_key, config["limit"] * 2, config["window_minutes"] * 60  # 2x limit for IP
        )

    def _check_rate_limit(self, cache_key: str, limit: int, window_seconds: int) -> Dict[str, Any]:
        """Generic rate limit checker"""
        try:
            current_count = frappe.cache.get(cache_key) or 0

            if current_count >= limit:
                ttl = frappe.cache.ttl(cache_key) or window_seconds
                return {
                    "allowed": False,
                    "reason": "RATE_LIMIT_EXCEEDED",
                    "message": _("Rate limit exceeded. Please try again later."),
                    "retry_after": ttl,
                    "current_count": current_count,
                    "limit": limit,
                }

            return {
                "allowed": True,
                "remaining_attempts": limit - current_count,
                "reset_time": time.time() + window_seconds,
            }

        except Exception as e:
            frappe.log_error(f"Rate limit check error for {cache_key}: {e}")
            return {"allowed": True}

    def _record_user_attempt(self, user_email: str, timestamp: datetime, success: bool) -> None:
        """Record user login attempt"""
        cache_key = f"login_attempts:user:{user_email}"
        window_seconds = self.config["login_attempts"]["window_minutes"] * 60

        if not success:
            current_count = frappe.cache.get(cache_key) or 0
            frappe.cache.set(cache_key, current_count + 1, ex=window_seconds)

    def _record_ip_attempt(self, ip_address: str, timestamp: datetime, success: bool) -> None:
        """Record IP login attempt"""
        cache_key = f"login_attempts:ip:{ip_address}"
        window_seconds = self.config["login_attempts"]["window_minutes"] * 60

        if not success:
            current_count = frappe.cache.get(cache_key) or 0
            frappe.cache.set(cache_key, current_count + 1, ex=window_seconds)

    def _check_progressive_penalties(self, user_email: str, ip_address: str) -> Dict[str, Any]:
        """Check progressive penalty system"""
        if not self.config["progressive_penalties"]["enabled"]:
            return {"allowed": True}

        # Get violation counts
        user_violations = self.violation_tracker.get_violation_count(user_email, hours=24)
        ip_violations = self.violation_tracker.get_violation_count(ip_address, hours=24)

        # Check penalty levels
        max_violations = max(user_violations, ip_violations)
        penalty_config = self._get_penalty_level(max_violations)

        if penalty_config:
            # Check if user/IP is currently locked out
            lockout_key = f"progressive_lockout:{user_email}:{ip_address}"
            if frappe.cache.get(lockout_key):
                return {
                    "allowed": False,
                    "reason": "PROGRESSIVE_LOCKOUT",
                    "message": _("Account temporarily locked due to repeated violations"),
                    "retry_after": frappe.cache.ttl(lockout_key),
                }

        return {"allowed": True}

    def _get_penalty_level(self, violation_count: int) -> Optional[Dict[str, int]]:
        """Get penalty configuration for violation count"""
        penalty_levels = self.config["progressive_penalties"]["violation_levels"]

        for level in reversed(penalty_levels):
            if violation_count >= level["violations"]:
                return level

        return None

    def _is_ip_blacklisted(self, ip_address: str) -> bool:
        """Check if IP is blacklisted"""
        blacklist = self.config["ip_controls"]["blacklist_ips"]
        return ip_address in blacklist

    def _is_ip_whitelisted(self, ip_address: str) -> bool:
        """Check if IP is whitelisted"""
        whitelist = self.config["ip_controls"]["whitelist_ips"]
        return ip_address in whitelist if whitelist else True

    def _log_login_attempt(
        self, user_email: str, ip_address: str, success: bool, timestamp: datetime
    ) -> None:
        """Log login attempt for audit"""
        try:
            # Import security logging function
            from universal_workshop.user_management.security_alerts import log_security_event

            event_data = {
                "user_email": user_email,
                "ip_address": ip_address,
                "success": success,
                "timestamp": timestamp.isoformat(),
                "user_agent": frappe.local.request.headers.get("User-Agent", ""),
                "event_type": "LOGIN_ATTEMPT",
            }

            log_security_event("login_attempt_rate_tracked", event_data)

        except Exception as e:
            frappe.log_error(f"Error logging login attempt: {e}")

    def apply_progressive_lockout(self, user_email: str, ip_address: str) -> None:
        """Apply progressive lockout after violations"""
        try:
            violations = self.violation_tracker.get_violation_count(user_email, hours=24)
            penalty_config = self._get_penalty_level(violations)

            if penalty_config:
                lockout_key = f"progressive_lockout:{user_email}:{ip_address}"
                lockout_duration = penalty_config["lockout_minutes"] * 60

                frappe.cache.set(lockout_key, True, ex=lockout_duration)

                # Log security event
                self._log_security_event(
                    "PROGRESSIVE_LOCKOUT_APPLIED",
                    {
                        "user_email": user_email,
                        "ip_address": ip_address,
                        "violation_count": violations,
                        "lockout_duration_minutes": penalty_config["lockout_minutes"],
                    },
                )

        except Exception as e:
            frappe.log_error(f"Error applying progressive lockout: {e}")

    def get_rate_limit_status(self, user_email: str, ip_address: str) -> Dict[str, Any]:
        """Get current rate limiting status"""
        try:
            status = {
                "user_login_attempts": self._get_attempt_count(f"login_attempts:user:{user_email}"),
                "ip_login_attempts": self._get_attempt_count(f"login_attempts:ip:{ip_address}"),
                "violations_24h": self.violation_tracker.get_violation_count(user_email, hours=24),
                "ip_violations_24h": self.violation_tracker.get_violation_count(
                    ip_address, hours=24
                ),
                "progressive_lockout": bool(
                    frappe.cache.get(f"progressive_lockout:{user_email}:{ip_address}")
                ),
                "ip_blacklisted": self._is_ip_blacklisted(ip_address),
                "ip_whitelisted": self._is_ip_whitelisted(ip_address),
            }

            return status

        except Exception as e:
            frappe.log_error(f"Error getting rate limit status: {e}")
            return {}

    def _get_attempt_count(self, cache_key: str) -> int:
        """Get current attempt count from cache"""
        return frappe.cache.get(cache_key) or 0

    def _log_security_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log security event"""
        try:

            log_security_event(event_type, event_data)
        except Exception as e:
            frappe.log_error(f"Error logging security event: {e}")


class RateLimitViolationTracker:
    """Track rate limiting violations for progressive penalties"""

    def __init__(self):
        self.violation_cache_prefix = "rate_limit_violations"

    def record_violation(self, identifier: str, ip_address: str, violation_type: str) -> None:
        """Record a rate limiting violation"""
        try:
            timestamp = now_datetime()

            # Record for user
            user_key = f"{self.violation_cache_prefix}:user:{identifier}"
            self._add_violation(user_key, timestamp, violation_type)

            # Record for IP
            ip_key = f"{self.violation_cache_prefix}:ip:{ip_address}"
            self._add_violation(ip_key, timestamp, violation_type)

        except Exception as e:
            frappe.log_error(f"Error recording violation: {e}")

    def _add_violation(self, cache_key: str, timestamp: datetime, violation_type: str) -> None:
        """Add violation to cache"""
        violations = frappe.cache.get(cache_key) or []

        # Add new violation
        violations.append({"timestamp": timestamp.isoformat(), "type": violation_type})

        # Keep only last 24 hours of violations
        cutoff_time = timestamp - timedelta(hours=24)
        violations = [v for v in violations if get_datetime(v["timestamp"]) > cutoff_time]

        # Store back in cache (expire after 25 hours to be safe)
        frappe.cache.set(cache_key, violations, ex=25 * 60 * 60)

    def get_violation_count(self, identifier: str, hours: int = 24) -> int:
        """Get violation count for identifier in specified time window"""
        try:
            cache_key = f"{self.violation_cache_prefix}:user:{identifier}"
            if "." in identifier:  # Assume IP address if contains dots
                cache_key = f"{self.violation_cache_prefix}:ip:{identifier}"

            violations = frappe.cache.get(cache_key) or []

            # Filter violations within time window
            cutoff_time = now_datetime() - timedelta(hours=hours)
            recent_violations = [
                v for v in violations if get_datetime(v["timestamp"]) > cutoff_time
            ]

            return len(recent_violations)

        except Exception as e:
            frappe.log_error(f"Error getting violation count: {e}")
            return 0


# Rate limiting decorators for workshop endpoints
def workshop_rate_limit(endpoint: str, limit: int = None, window_minutes: int = None):
    """
    Rate limiting decorator for workshop endpoints

    Args:
        endpoint: Endpoint identifier
        limit: Request limit (optional, uses config if not provided)
        window_minutes: Time window in minutes (optional, uses config if not provided)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Get user and IP
                user = frappe.session.user
                ip_address = frappe.local.request.environ.get("REMOTE_ADDR", "unknown")

                # Check rate limits
                rate_manager = WorkshopRateLimitManager()
                result = rate_manager.check_api_rate_limit(endpoint, user, ip_address)

                if not result["allowed"]:
                    frappe.throw(
                        result["message"],
                        frappe.TooManyRequestsError,
                        title=_("Rate Limit Exceeded"),
                    )

                return func(*args, **kwargs)

            except Exception as e:
                if isinstance(e, frappe.TooManyRequestsError):
                    raise
                frappe.log_error(f"Rate limit decorator error: {e}")
                return func(*args, **kwargs)  # Continue on error

        return wrapper

    return decorator


# Whitelisted methods for rate limiting management
@frappe.whitelist()
def get_rate_limit_status():
    """Get current user's rate limiting status"""
    try:
        user_email = frappe.session.user
        ip_address = frappe.local.request.environ.get("REMOTE_ADDR", "unknown")

        rate_manager = WorkshopRateLimitManager()
        return rate_manager.get_rate_limit_status(user_email, ip_address)

    except Exception as e:
        frappe.log_error(f"Error getting rate limit status: {e}")
        return {"error": str(e)}


@frappe.whitelist()
def admin_reset_rate_limits(user_email: str = None, ip_address: str = None):
    """Reset rate limits for user or IP (admin only)"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Not authorized to reset rate limits"))

    try:
        # Reset user limits
        if user_email:
            cache_keys = [
                f"login_attempts:user:{user_email}",
                f"progressive_lockout:{user_email}:*",
                f"rate_limit_violations:user:{user_email}",
            ]
            for key in cache_keys:
                frappe.cache.delete(key)

        # Reset IP limits
        if ip_address:
            cache_keys = [
                f"login_attempts:ip:{ip_address}",
                f"progressive_lockout:*:{ip_address}",
                f"rate_limit_violations:ip:{ip_address}",
            ]
            for key in cache_keys:
                frappe.cache.delete(key)

        return {"success": True, "message": _("Rate limits reset successfully")}

    except Exception as e:
        frappe.log_error(f"Error resetting rate limits: {e}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def admin_configure_rate_limits(config_data: str):
    """Configure rate limiting settings (admin only)"""
    if not frappe.has_permission("System Settings", "write"):
        frappe.throw(_("Not authorized to configure rate limits"))

    try:
        config = json.loads(config_data)

        # Update site config
        site_config = frappe.get_site_config()
        site_config["workshop_rate_limits"] = config

        # Save configuration (this would need to be implemented based on Frappe's config management)
        # For now, we'll use a custom setting
        frappe.db.set_value(
            "System Settings", "System Settings", "workshop_rate_limits", json.dumps(config)
        )

        return {"success": True, "message": _("Rate limit configuration updated")}

    except Exception as e:
        frappe.log_error(f"Error configuring rate limits: {e}")
        return {"success": False, "error": str(e)}
