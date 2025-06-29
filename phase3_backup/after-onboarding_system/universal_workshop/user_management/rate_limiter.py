"""
Rate Limiting Manager for Universal Workshop ERP

Provides comprehensive rate limiting for workshop endpoints with
IP-based controls, brute force protection, and progressive penalties.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime, get_datetime


class RateLimiter:
    """
    Advanced rate limiting system with IP-based controls and progressive penalties
    """

    def __init__(self):
        """Initialize rate limiter with configuration"""
        self.redis_client = frappe.cache()

        # Rate limit configurations per endpoint type
        self.endpoint_limits = {
            # Authentication endpoints - strict limits
            "login": {"requests": 5, "window": 300, "burst": 2},  # 5 requests per 5 minutes
            "password_reset": {
                "requests": 3,
                "window": 600,
                "burst": 1,
            },  # 3 requests per 10 minutes
            # API endpoints - moderate limits
            "workshop_api": {"requests": 100, "window": 60, "burst": 20},  # 100 requests per minute
            "customer_api": {"requests": 50, "window": 60, "burst": 10},
            "vehicle_api": {"requests": 30, "window": 60, "burst": 8},
            # Search endpoints - higher limits
            "search": {"requests": 200, "window": 60, "burst": 50},
            # Dashboard endpoints - moderate limits
            "dashboard": {"requests": 60, "window": 60, "burst": 15},
            # Print/export endpoints - lower limits due to resource usage
            "export": {"requests": 10, "window": 300, "burst": 3},  # 10 requests per 5 minutes
            "print": {"requests": 20, "window": 60, "burst": 5},
        }

        # Progressive penalty system
        self.penalty_multipliers = {
            1: 1.0,  # First violation - normal rate
            2: 2.0,  # Second violation - 2x slower
            3: 4.0,  # Third violation - 4x slower
            4: 8.0,  # Fourth violation - 8x slower
            5: 16.0,  # Fifth+ violation - 16x slower
        }

        # IP-based blocking thresholds
        self.ip_blocking = {
            "suspicious_threshold": 10,  # Block after 10 violations in hour
            "malicious_threshold": 20,  # Extended block after 20 violations
            "block_duration": 3600,  # 1 hour standard block
            "extended_block_duration": 86400,  # 24 hour extended block
        }

    def check_rate_limit(
        self, endpoint_type: str, identifier: str, ip_address: str = None
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limits

        Args:
            endpoint_type: Type of endpoint (login, api, search, etc.)
            identifier: User identifier (user_id, session_id, etc.)
            ip_address: Client IP address

        Returns:
            Dict with rate limit status and remaining quota
        """
        current_time = time.time()

        # Check IP-based blocking first
        if ip_address:
            ip_block_result = self._check_ip_blocking(ip_address, current_time)
            if ip_block_result["blocked"]:
                return {
                    "allowed": False,
                    "reason": "IP_BLOCKED",
                    "message": _("IP address temporarily blocked due to suspicious activity"),
                    "retry_after": ip_block_result["retry_after"],
                    "block_expires": ip_block_result["expires_at"],
                }

        # Get rate limit configuration
        if endpoint_type not in self.endpoint_limits:
            endpoint_type = "workshop_api"  # Default fallback

        limits = self.endpoint_limits[endpoint_type]

        # Create rate limit keys
        base_key = f"rate_limit:{endpoint_type}:{identifier}"
        window_key = f"{base_key}:{int(current_time // limits['window'])}"
        violation_key = f"violations:{identifier}"

        # Get current request count and violations
        current_count = cint(self.redis_client.get(window_key) or 0)
        violation_count = cint(self.redis_client.get(violation_key) or 0)

        # Apply progressive penalties
        effective_limit = self._calculate_effective_limit(limits["requests"], violation_count)

        # Check if within limits
        if current_count >= effective_limit:
            # Rate limit exceeded - record violation
            self._record_violation(identifier, ip_address, endpoint_type, current_time)

            remaining_time = limits["window"] - (current_time % limits["window"])

            return {
                "allowed": False,
                "reason": "RATE_LIMIT_EXCEEDED",
                "message": _("Rate limit exceeded. Please wait before making more requests."),
                "limit": effective_limit,
                "current": current_count,
                "retry_after": int(remaining_time),
                "violation_count": violation_count + 1,
            }

        # Check burst limit
        burst_key = f"burst:{base_key}:{int(current_time // 10)}"  # 10-second burst window
        burst_count = cint(self.redis_client.get(burst_key) or 0)

        if burst_count >= limits["burst"]:
            return {
                "allowed": False,
                "reason": "BURST_LIMIT_EXCEEDED",
                "message": _("Too many requests in short time. Please slow down."),
                "retry_after": 10,
            }

        # Allow request - increment counters
        self.redis_client.setex(window_key, limits["window"], current_count + 1)
        self.redis_client.setex(burst_key, 10, burst_count + 1)

        return {
            "allowed": True,
            "limit": effective_limit,
            "current": current_count + 1,
            "remaining": effective_limit - current_count - 1,
            "reset_time": int(
                current_time + (limits["window"] - (current_time % limits["window"]))
            ),
        }

    def _check_ip_blocking(self, ip_address: str, current_time: float) -> Dict[str, Any]:
        """Check if IP address is blocked"""
        ip_key = f"ip_block:{ip_address}"
        ip_violations_key = (
            f"ip_violations:{ip_address}:{int(current_time // 3600)}"  # Hourly window
        )

        # Check if IP is currently blocked
        block_data = self.redis_client.get(ip_key)
        if block_data:
            try:
                block_info = json.loads(block_data)
                if current_time < block_info["expires_at"]:
                    return {
                        "blocked": True,
                        "reason": block_info["reason"],
                        "expires_at": block_info["expires_at"],
                        "retry_after": int(block_info["expires_at"] - current_time),
                    }
            except (json.JSONDecodeError, KeyError):
                # Clean up corrupted data
                self.redis_client.delete(ip_key)

        return {"blocked": False}

    def _calculate_effective_limit(self, base_limit: int, violation_count: int) -> int:
        """Calculate effective rate limit with progressive penalties"""
        penalty_level = min(violation_count, 5)  # Cap at level 5
        multiplier = self.penalty_multipliers.get(penalty_level, 1.0)

        # Reduce limit based on violations
        effective_limit = max(1, int(base_limit / multiplier))
        return effective_limit

    def _record_violation(
        self, identifier: str, ip_address: str, endpoint_type: str, current_time: float
    ):
        """Record rate limit violation for progressive penalties"""
        violation_key = f"violations:{identifier}"
        ip_violations_key = f"ip_violations:{ip_address}:{int(current_time // 3600)}"

        # Increment user violations (24 hour expiry)
        current_violations = cint(self.redis_client.get(violation_key) or 0)
        self.redis_client.setex(violation_key, 86400, current_violations + 1)

        # Increment IP violations (1 hour window)
        ip_violations = cint(self.redis_client.get(ip_violations_key) or 0)
        self.redis_client.setex(ip_violations_key, 3600, ip_violations + 1)

        # Check if IP should be blocked
        if ip_violations >= self.ip_blocking["suspicious_threshold"]:
            self._block_ip_address(ip_address, ip_violations, current_time)

        # Log security event
        self._log_rate_limit_violation(
            identifier, ip_address, endpoint_type, current_violations + 1
        )

    def _block_ip_address(self, ip_address: str, violation_count: int, current_time: float):
        """Block IP address based on violation severity"""
        ip_key = f"ip_block:{ip_address}"

        # Determine block duration and reason
        if violation_count >= self.ip_blocking["malicious_threshold"]:
            block_duration = self.ip_blocking["extended_block_duration"]
            reason = "MALICIOUS_ACTIVITY"
        else:
            block_duration = self.ip_blocking["block_duration"]
            reason = "SUSPICIOUS_ACTIVITY"

        expires_at = current_time + block_duration

        block_data = {
            "reason": reason,
            "blocked_at": current_time,
            "expires_at": expires_at,
            "violation_count": violation_count,
        }

        self.redis_client.setex(ip_key, block_duration, json.dumps(block_data))

        # Log IP blocking event
        frappe.log_error(
            f"IP {ip_address} blocked for {reason}. Duration: {block_duration}s, Violations: {violation_count}",
            "IP Security",
        )

    def _log_rate_limit_violation(
        self, identifier: str, ip_address: str, endpoint_type: str, violation_count: int
    ):
        """Log rate limit violation for security monitoring"""
        try:
            from universal_workshop.user_management.security_logger import log_security_event

            event_data = {
                "identifier": identifier,
                "ip_address": ip_address,
                "endpoint_type": endpoint_type,
                "violation_count": violation_count,
                "timestamp": now_datetime().isoformat(),
            }

            log_security_event("rate_limit_violation", event_data)

        except ImportError:
            # Fallback logging
            frappe.log_error(
                f"Rate limit violation: {identifier} from {ip_address} on {endpoint_type} (violation #{violation_count})",
                "Rate Limiter",
            )

    def get_rate_limit_status(self, endpoint_type: str, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for identifier"""
        if endpoint_type not in self.endpoint_limits:
            endpoint_type = "workshop_api"

        limits = self.endpoint_limits[endpoint_type]
        current_time = time.time()

        window_key = (
            f"rate_limit:{endpoint_type}:{identifier}:{int(current_time // limits['window'])}"
        )
        violation_key = f"violations:{identifier}"

        current_count = cint(self.redis_client.get(window_key) or 0)
        violation_count = cint(self.redis_client.get(violation_key) or 0)

        effective_limit = self._calculate_effective_limit(limits["requests"], violation_count)

        return {
            "endpoint_type": endpoint_type,
            "limit": effective_limit,
            "current": current_count,
            "remaining": max(0, effective_limit - current_count),
            "violation_count": violation_count,
            "reset_time": int(
                current_time + (limits["window"] - (current_time % limits["window"]))
            ),
        }

    def reset_rate_limit(self, endpoint_type: str, identifier: str) -> bool:
        """Reset rate limit for identifier (admin function)"""
        try:
            current_time = time.time()
            window_key = f"rate_limit:{endpoint_type}:{identifier}:{int(current_time // self.endpoint_limits[endpoint_type]['window'])}"
            violation_key = f"violations:{identifier}"

            self.redis_client.delete(window_key)
            self.redis_client.delete(violation_key)

            return True
        except Exception as e:
            frappe.log_error(f"Error resetting rate limit: {e}", "Rate Limiter")
            return False

    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock IP address (admin function)"""
        try:
            ip_key = f"ip_block:{ip_address}"
            self.redis_client.delete(ip_key)

            # Clean up violation keys for this hour
            current_time = time.time()
            ip_violations_key = f"ip_violations:{ip_address}:{int(current_time // 3600)}"
            self.redis_client.delete(ip_violations_key)

            frappe.log_error(f"IP {ip_address} unblocked by admin", "IP Security")
            return True
        except Exception as e:
            frappe.log_error(f"Error unblocking IP {ip_address}: {e}", "Rate Limiter")
            return False


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit_decorator(endpoint_type: str):
    """Decorator to apply rate limiting to API functions"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get request context
            identifier = frappe.session.user or "anonymous"
            ip_address = frappe.local.request_ip or "unknown"

            # Check rate limit
            limiter = get_rate_limiter()
            result = limiter.check_rate_limit(endpoint_type, identifier, ip_address)

            if not result["allowed"]:
                frappe.local.response["http_status_code"] = 429
                frappe.local.response.update(
                    {"rate_limit_exceeded": True, "retry_after": result.get("retry_after", 60)}
                )
                frappe.throw(
                    result["message"], frappe.RateLimitExceededError, title=_("Rate Limit Exceeded")
                )

            # Add rate limit headers to response
            frappe.local.response.update(
                {
                    "X-RateLimit-Limit": result["limit"],
                    "X-RateLimit-Remaining": result.get("remaining", 0),
                    "X-RateLimit-Reset": result.get("reset_time", 0),
                }
            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


@frappe.whitelist()
def get_rate_limit_status(endpoint_type: str = "workshop_api") -> Dict[str, Any]:
    """API endpoint to get current rate limit status"""
    identifier = frappe.session.user or "anonymous"
    limiter = get_rate_limiter()
    return limiter.get_rate_limit_status(endpoint_type, identifier)


@frappe.whitelist()
def reset_user_rate_limit(user_id: str, endpoint_type: str = "workshop_api") -> Dict[str, bool]:
    """API endpoint to reset rate limit for user (admin only)"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Insufficient permissions to reset rate limits"))

    limiter = get_rate_limiter()
    success = limiter.reset_rate_limit(endpoint_type, user_id)

    return {"success": success}


@frappe.whitelist()
def unblock_ip_address(ip_address: str) -> Dict[str, bool]:
    """API endpoint to unblock IP address (admin only)"""
    if not frappe.has_permission("System Manager"):
        frappe.throw(_("Insufficient permissions to unblock IP addresses"))

    limiter = get_rate_limiter()
    success = limiter.unblock_ip(ip_address)

    return {"success": success}
