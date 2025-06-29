"""
Secure Redirect Management for Universal Workshop ERP

Provides secure redirect functionality to prevent open redirect attacks
and ensure users are only redirected to authorized URLs within the application.
"""

import re
from urllib.parse import urlparse, urljoin
from typing import Optional, List, Dict, Any

import frappe
from frappe import _
from frappe.utils import get_url


class SecureRedirectManager:
    """
    Secure redirect management system that validates and sanitizes redirect URLs
    to prevent open redirect attacks and unauthorized external redirects.
    """

    def __init__(self):
        """Initialize secure redirect manager with configuration"""
        self.allowed_schemes = ["http", "https"]
        self.allowed_hosts = self._get_allowed_hosts()
        self.default_redirect = "/app"

        # Workshop-specific safe paths
        self.safe_paths = [
            "/app",
            "/app/",
            "/app/workspace/Workshop%20Management",
            "/app/workspace/workshop-management",
            "/app/service-order",
            "/app/customer",
            "/app/vehicle",
            "/app/item",
            "/app/workshop-profile",
            "/app/user",
            "/technician",
            "/customer-portal",
            "/workshop-onboarding",
            "/login",
            "/logout",
            "/universal-workshop-dashboard",
            "/app/universal-workshop-dashboard",
        ]

        # Dangerous patterns to block
        self.blocked_patterns = [
            r"javascript:",
            r"data:",
            r"vbscript:",
            r"file:",
            r"ftp:",
            r"\\/\\/",  # Protocol-relative URLs
            r"@",  # Potential for host confusion
            r"%2f%2f",  # URL-encoded //
            r"%5c%5c",  # URL-encoded \\
        ]

    def _get_allowed_hosts(self) -> List[str]:
        """Get list of allowed hosts for redirects"""
        allowed_hosts = []

        # Add current site host
        site_config = frappe.get_site_config()
        current_host = site_config.get("host_name")
        if current_host:
            allowed_hosts.append(current_host)

        # Add localhost variations for development
        allowed_hosts.extend(
            [
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "universal.local",
            ]
        )

        # Add any custom allowed hosts from site config
        custom_hosts = site_config.get("allowed_redirect_hosts", [])
        if isinstance(custom_hosts, list):
            allowed_hosts.extend(custom_hosts)

        return list(set(allowed_hosts))  # Remove duplicates

    def validate_redirect_url(self, redirect_url: str) -> Dict[str, Any]:
        """
        Validate a redirect URL for security issues

        Args:
            redirect_url: The URL to validate

        Returns:
            Dict with validation result and sanitized URL
        """
        if not redirect_url:
            return {
                "is_valid": False,
                "error": "Empty redirect URL",
                "safe_url": self.default_redirect,
            }

        # Remove whitespace and decode common encodings
        redirect_url = redirect_url.strip()

        # Check for dangerous patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, redirect_url.lower()):
                return {
                    "is_valid": False,
                    "error": f"Blocked pattern detected: {pattern}",
                    "safe_url": self.default_redirect,
                }

        # Parse the URL
        try:
            parsed = urlparse(redirect_url)
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Invalid URL format: {e}",
                "safe_url": self.default_redirect,
            }

        # Handle relative URLs (these are generally safe)
        if not parsed.scheme and not parsed.netloc:
            # Relative path - validate against safe paths
            if self._is_safe_path(redirect_url):
                return {"is_valid": True, "safe_url": redirect_url, "type": "relative"}
            else:
                return {
                    "is_valid": False,
                    "error": "Path not in allowed list",
                    "safe_url": self.default_redirect,
                }

        # Handle absolute URLs
        if parsed.scheme not in self.allowed_schemes:
            return {
                "is_valid": False,
                "error": f"Scheme '{parsed.scheme}' not allowed",
                "safe_url": self.default_redirect,
            }

        # Check if host is allowed
        if parsed.netloc and not self._is_allowed_host(parsed.netloc):
            return {
                "is_valid": False,
                "error": f"Host '{parsed.netloc}' not allowed",
                "safe_url": self.default_redirect,
            }

        # Check if path is safe
        if not self._is_safe_path(parsed.path):
            return {
                "is_valid": False,
                "error": "Path not in allowed list",
                "safe_url": self.default_redirect,
            }

        return {"is_valid": True, "safe_url": redirect_url, "type": "absolute"}

    def _is_safe_path(self, path: str) -> bool:
        """Check if a path is in the safe paths list"""
        if not path:
            return False

        # Normalize path
        path = path.rstrip("/")
        if not path:
            path = "/"

        # Check exact matches first
        if path in self.safe_paths:
            return True

        # Check if path starts with any safe path
        for safe_path in self.safe_paths:
            if path.startswith(safe_path.rstrip("/")):
                return True

        return False

    def _is_allowed_host(self, host: str) -> bool:
        """Check if a host is in the allowed hosts list"""
        if not host:
            return False

        # Remove port if present
        host_without_port = host.split(":")[0].lower()

        return host_without_port in [h.lower() for h in self.allowed_hosts]

    def get_safe_redirect_url(
        self, requested_url: str, user_roles: Optional[List[str]] = None
    ) -> str:
        """
        Get a safe redirect URL, falling back to role-based defaults if invalid

        Args:
            requested_url: The requested redirect URL
            user_roles: User's roles for role-based fallback

        Returns:
            A safe redirect URL
        """
        # Validate the requested URL
        validation_result = self.validate_redirect_url(requested_url)

        if validation_result["is_valid"]:
            return validation_result["safe_url"]

        # Log the security issue
        frappe.log_error(
            f"Redirect security issue: {validation_result['error']} for URL: {requested_url}",
            "Secure Redirect",
        )

        # Fall back to role-based redirect
        if user_roles:
            return self._get_role_based_redirect(user_roles)

        return self.default_redirect

    def _get_role_based_redirect(self, user_roles: List[str]) -> str:
        """Get redirect URL based on user roles"""
        # Workshop Owner gets dedicated dashboard
        if "Workshop Owner" in user_roles:
            return "/universal-workshop-dashboard"

        # High-privilege system roles
        elif any(role in user_roles for role in ["System Manager", "Administrator"]):
            return "/app/workspace/Workshop%20Management"

        # Management roles
        elif "Workshop Manager" in user_roles:
            return "/app/workspace/Workshop%20Management"

        # Technician role
        elif "Workshop Technician" in user_roles:
            return "/technician"

        # Customer role
        elif "Customer" in user_roles:
            return "/customer-portal"

        # Default fallback
        else:
            return self.default_redirect

    def add_safe_path(self, path: str) -> bool:
        """
        Add a new safe path to the allowed list

        Args:
            path: The path to add

        Returns:
            True if added successfully
        """
        if path and path not in self.safe_paths:
            self.safe_paths.append(path)
            return True
        return False

    def remove_safe_path(self, path: str) -> bool:
        """
        Remove a path from the safe list

        Args:
            path: The path to remove

        Returns:
            True if removed successfully
        """
        if path in self.safe_paths:
            self.safe_paths.remove(path)
            return True
        return False

    def get_configuration(self) -> Dict[str, Any]:
        """Get current redirect security configuration"""
        return {
            "allowed_schemes": self.allowed_schemes,
            "allowed_hosts": self.allowed_hosts,
            "safe_paths": self.safe_paths,
            "default_redirect": self.default_redirect,
            "blocked_patterns": self.blocked_patterns,
        }


# Global instance
_redirect_manager = None


def get_redirect_manager() -> SecureRedirectManager:
    """Get global redirect manager instance"""
    global _redirect_manager
    if _redirect_manager is None:
        _redirect_manager = SecureRedirectManager()
    return _redirect_manager


@frappe.whitelist()
def validate_redirect_url(url: str) -> Dict[str, Any]:
    """
    API endpoint to validate redirect URLs

    Args:
        url: URL to validate

    Returns:
        Validation result
    """
    manager = get_redirect_manager()
    return manager.validate_redirect_url(url)


@frappe.whitelist()
def get_safe_redirect(url: str, fallback: Optional[str] = None) -> str:
    """
    API endpoint to get safe redirect URL

    Args:
        url: Requested URL
        fallback: Fallback URL if validation fails

    Returns:
        Safe redirect URL
    """
    manager = get_redirect_manager()
    user_roles = frappe.get_roles(frappe.session.user)

    # Use provided fallback or role-based fallback
    if fallback:
        # Validate the fallback URL too
        fallback_validation = manager.validate_redirect_url(fallback)
        if not fallback_validation["is_valid"]:
            fallback = None

    if fallback:
        # Temporarily add fallback to safe paths for this validation
        original_safe_paths = manager.safe_paths.copy()
        manager.safe_paths.append(fallback)

        result = manager.get_safe_redirect_url(url, user_roles)

        # Restore original safe paths
        manager.safe_paths = original_safe_paths

        return result
    else:
        return manager.get_safe_redirect_url(url, user_roles)


@frappe.whitelist()
def get_redirect_configuration() -> Dict[str, Any]:
    """
    Get current redirect security configuration

    Returns:
        Configuration dictionary
    """
    manager = get_redirect_manager()
    return manager.get_configuration()
