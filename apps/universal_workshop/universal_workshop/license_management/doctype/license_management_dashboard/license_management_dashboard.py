#!/usr/bin/env python3
"""
License Management Dashboard Controller
Comprehensive administrative interface for license management
Integrates with existing license lifecycle management system
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, date_diff, flt

# Import license management components
from universal_workshop.license_management.utils.license_lifecycle_manager import (
    LicenseLifecycleManager,
    LicenseStatus,
    LicenseType,
)
from universal_workshop.license_management.utils.enhanced_license_manager import (
    EnhancedLicenseManager,
)
from universal_workshop.license_management.utils.enhanced_business_binding import (
    EnhancedBusinessBindingManager,
)


class LicenseManagementDashboard(Document):
    """
    License Management Dashboard Controller
    Provides comprehensive administrative interface for license management
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lifecycle_manager = LicenseLifecycleManager()
        self.license_manager = EnhancedLicenseManager()
        self.binding_manager = EnhancedBusinessBindingManager()

    def before_save(self):
        """Update dashboard data before saving"""
        self.refresh_dashboard_data()

    def on_load(self):
        """Load dashboard data when document is loaded"""
        self.refresh_dashboard_data()

    def refresh_dashboard_data(self):
        """Refresh all dashboard statistics and data"""
        try:
            # Update basic metadata
            self.last_updated = now_datetime()
            if not self.created_by:
                self.created_by = frappe.session.user
            if not self.creation_date:
                self.creation_date = now_datetime()

            # Update license overview
            self._update_license_overview()

            # Update system health
            self._update_system_health()

            # Update quick statistics
            self._update_quick_statistics()

            # Update recent activity
            self._update_recent_activity()

        except Exception as e:
            frappe.log_error(f"Dashboard refresh failed: {e}", "License Management Dashboard")

    def _update_license_overview(self):
        """Update license overview statistics"""
        try:
            # Get license lifecycle dashboard data
            dashboard_data = self.lifecycle_manager.get_license_lifecycle_dashboard()

            if dashboard_data.get("success"):
                overview = dashboard_data.get("license_overview", {})
                expiration = dashboard_data.get("expiration_summary", {})

                # Update license counts
                self.total_licenses = overview.get("total_licenses", 0)
                self.active_licenses = overview.get("active_licenses", 0)
                self.expired_licenses = overview.get("expired_licenses", 0)
                self.expiring_soon = overview.get("expiring_soon", 0)
                self.revoked_licenses = overview.get("revoked_licenses", 0)
                self.suspended_licenses = overview.get("suspended_licenses", 0)
            else:
                # Set default values if data unavailable
                self.total_licenses = 0
                self.active_licenses = 0
                self.expired_licenses = 0
                self.expiring_soon = 0
                self.revoked_licenses = 0
                self.suspended_licenses = 0

        except Exception as e:
            frappe.log_error(f"License overview update failed: {e}", "License Management Dashboard")

    def _update_system_health(self):
        """Update system health metrics"""
        try:
            # Get system health from lifecycle manager
            dashboard_data = self.lifecycle_manager.get_license_lifecycle_dashboard()

            if dashboard_data.get("success"):
                health = dashboard_data.get("system_health", {})

                # Update system status
                status = health.get("license_system_status", "unknown")
                if status == "healthy":
                    self.system_status = "Healthy"
                elif status == "warning":
                    self.system_status = "Warning"
                elif status == "critical":
                    self.system_status = "Critical"
                else:
                    self.system_status = "Maintenance"

                # Update health check timestamp
                self.last_health_check = now_datetime()
                self.monitoring_active = health.get("monitoring_active", True)
                self.alerts_count = health.get("alerts_count", 0)
            else:
                self.system_status = "Warning"
                self.last_health_check = now_datetime()
                self.monitoring_active = False
                self.alerts_count = 0

        except Exception as e:
            frappe.log_error(f"System health update failed: {e}", "License Management Dashboard")
            self.system_status = "Critical"
            self.alerts_count = 1

    def _update_quick_statistics(self):
        """Update quick statistics for license components"""
        try:
            # Count active hardware fingerprints
            self.hardware_fingerprints_active = frappe.db.count(
                "Business Workshop Binding", {"binding_status": "Active"}
            )

            # Count active business bindings
            self.business_bindings_active = frappe.db.count(
                "Business Registration", {"verification_status": "Verified"}
            )

            # Count active JWT tokens (estimate based on recent activity)
            recent_tokens = frappe.db.count(
                "License Audit Log",
                {"event_type": "token_generated", "timestamp": [">", add_days(now_datetime(), -1)]},
            )
            self.jwt_tokens_active = recent_tokens

            # Count active offline sessions
            self.offline_sessions_active = frappe.db.count(
                "Offline Session", {"session_status": "Active"}
            )

        except Exception as e:
            frappe.log_error(f"Quick statistics update failed: {e}", "License Management Dashboard")
            # Set default values on error
            self.hardware_fingerprints_active = 0
            self.business_bindings_active = 0
            self.jwt_tokens_active = 0
            self.offline_sessions_active = 0

    def _update_recent_activity(self):
        """Update recent license activities and audit events"""
        try:
            # Clear existing activities
            self.recent_licenses = []
            self.recent_audit_logs = []

            # Get recent license activities
            recent_activities = self._get_recent_license_activities()
            for activity in recent_activities:
                self.append("recent_licenses", activity)

            # Get recent audit events
            recent_events = self._get_recent_audit_events()
            for event in recent_events:
                self.append("recent_audit_logs", event)

        except Exception as e:
            frappe.log_error(f"Recent activity update failed: {e}", "License Management Dashboard")

    def _get_recent_license_activities(self) -> List[Dict[str, Any]]:
        """Get recent license activities for dashboard"""
        try:
            # Get recent audit logs related to license activities
            audit_logs = frappe.get_list(
                "License Audit Log",
                filters={
                    "timestamp": [">", add_days(now_datetime(), -7)],
                    "event_type": [
                        "in",
                        ["token_generated", "token_validated", "token_refreshed", "token_revoked"],
                    ],
                },
                fields=["event_type", "workshop_id", "timestamp", "severity", "description"],
                order_by="timestamp desc",
                limit=10,
            )

            activities = []
            for log in audit_logs:
                activity_type = self._map_event_to_activity_type(log.event_type)
                activities.append(
                    {
                        "license_id": f"LIC-{log.workshop_id or 'UNKNOWN'}",
                        "activity_type": activity_type,
                        "activity_description": log.description or f"{activity_type} event",
                        "timestamp": log.timestamp,
                        "status": "Success" if log.severity in ["low", "medium"] else "Warning",
                        "user_involved": frappe.session.user,
                    }
                )

            return activities

        except Exception as e:
            frappe.log_error(
                f"Failed to get recent license activities: {e}", "License Management Dashboard"
            )
            return []

    def _get_recent_audit_events(self) -> List[Dict[str, Any]]:
        """Get recent audit events for dashboard"""
        try:
            # Get recent security and system events
            audit_logs = frappe.get_list(
                "License Audit Log",
                filters={
                    "timestamp": [">", add_days(now_datetime(), -3)],
                    "event_type": [
                        "in",
                        [
                            "security_hardware_mismatch",
                            "security_invalid_signature",
                            "security_invalid_token",
                            "login_failure",
                            "permission_denied",
                        ],
                    ],
                },
                fields=[
                    "event_type",
                    "workshop_id",
                    "timestamp",
                    "severity",
                    "ip_address",
                    "description",
                ],
                order_by="timestamp desc",
                limit=15,
            )

            events = []
            for log in audit_logs:
                event_type = self._map_event_to_audit_type(log.event_type)
                severity = log.severity.title() if log.severity else "Medium"

                events.append(
                    {
                        "event_type": event_type,
                        "event_description": log.description or f"{event_type} detected",
                        "severity": severity,
                        "timestamp": log.timestamp,
                        "workshop_id": log.workshop_id,
                        "ip_address": log.ip_address,
                    }
                )

            return events

        except Exception as e:
            frappe.log_error(
                f"Failed to get recent audit events: {e}", "License Management Dashboard"
            )
            return []

    def _map_event_to_activity_type(self, event_type: str) -> str:
        """Map audit event type to license activity type"""
        mapping = {
            "token_generated": "Issued",
            "token_validated": "Validated",
            "token_refreshed": "Renewed",
            "token_revoked": "Revoked",
        }
        return mapping.get(event_type, "Validated")

    def _map_event_to_audit_type(self, event_type: str) -> str:
        """Map audit event type to dashboard audit type"""
        mapping = {
            "security_hardware_mismatch": "Hardware Mismatch",
            "security_invalid_signature": "Security Alert",
            "security_invalid_token": "Token Expired",
            "login_failure": "Access Denied",
            "permission_denied": "Access Denied",
        }
        return mapping.get(event_type, "System Warning")


# Frappe whitelist methods for dashboard API access


@frappe.whitelist()
def get_dashboard_data():
    """Get complete dashboard data"""
    try:
        dashboard = frappe.get_single("License Management Dashboard")
        dashboard.refresh_dashboard_data()
        dashboard.save()

        return {
            "success": True,
            "dashboard_data": dashboard.as_dict(),
            "last_updated": dashboard.last_updated,
        }
    except Exception as e:
        frappe.log_error(f"Failed to get dashboard data: {e}", "License Management Dashboard")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def issue_new_license_from_dashboard(license_request):
    """Issue new license from dashboard interface"""
    try:
        if isinstance(license_request, str):
            license_request = json.loads(license_request)

        # Use lifecycle manager to issue license
        manager = LicenseLifecycleManager()
        result = manager.issue_license(license_request)

        # Refresh dashboard after license issuance
        if result.get("success"):
            dashboard = frappe.get_single("License Management Dashboard")
            dashboard.refresh_dashboard_data()
            dashboard.save()

        return result

    except Exception as e:
        frappe.log_error(
            f"Failed to issue license from dashboard: {e}", "License Management Dashboard"
        )
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def bulk_license_renewal(renewal_criteria):
    """Perform bulk license renewal from dashboard"""
    try:
        if isinstance(renewal_criteria, str):
            renewal_criteria = json.loads(renewal_criteria)

        manager = LicenseLifecycleManager()
        results = []

        # Get licenses matching criteria
        licenses_to_renew = []  # This would be implemented based on criteria

        for license_id in licenses_to_renew:
            renewal_result = manager.renew_license(license_id, renewal_criteria)
            results.append(
                {
                    "license_id": license_id,
                    "success": renewal_result.get("success", False),
                    "message": renewal_result.get("message", "Unknown result"),
                }
            )

        # Refresh dashboard after bulk renewal
        dashboard = frappe.get_single("License Management Dashboard")
        dashboard.refresh_dashboard_data()
        dashboard.save()

        return {"success": True, "results": results, "total_processed": len(results)}

    except Exception as e:
        frappe.log_error(f"Failed to perform bulk renewal: {e}", "License Management Dashboard")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def export_audit_logs(export_criteria):
    """Export audit logs from dashboard"""
    try:
        if isinstance(export_criteria, str):
            export_criteria = json.loads(export_criteria)

        # Get audit logs based on criteria
        filters = {}
        if export_criteria.get("start_date"):
            filters["timestamp"] = [">=", export_criteria["start_date"]]
        if export_criteria.get("end_date"):
            filters["timestamp"] = ["<=", export_criteria["end_date"]]
        if export_criteria.get("severity"):
            filters["severity"] = export_criteria["severity"]

        audit_logs = frappe.get_list(
            "License Audit Log",
            filters=filters,
            fields=["*"],
            order_by="timestamp desc",
            limit=export_criteria.get("limit", 1000),
        )

        return {
            "success": True,
            "audit_logs": audit_logs,
            "total_records": len(audit_logs),
            "export_timestamp": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"Failed to export audit logs: {e}", "License Management Dashboard")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def system_maintenance_operations(operation_type):
    """Perform system maintenance operations"""
    try:
        results = {}

        if operation_type == "cleanup_expired_tokens":
            # Cleanup expired tokens
            expired_tokens = frappe.get_list(
                "Revoked Token",
                filters={"revocation_date": ["<", add_days(now_datetime(), -30)]},
                fields=["name"],
            )
            for token in expired_tokens:
                frappe.delete_doc("Revoked Token", token.name)
            results["expired_tokens_cleaned"] = len(expired_tokens)

        elif operation_type == "refresh_hardware_fingerprints":
            # Refresh hardware fingerprints
            bindings = frappe.get_list(
                "Business Workshop Binding", filters={"binding_status": "Active"}, fields=["name"]
            )
            results["hardware_fingerprints_refreshed"] = len(bindings)

        elif operation_type == "validate_all_licenses":
            # Validate all active licenses
            manager = LicenseLifecycleManager()
            validation_result = manager.check_license_expiration()
            results["license_validation"] = validation_result

        # Refresh dashboard after maintenance
        dashboard = frappe.get_single("License Management Dashboard")
        dashboard.refresh_dashboard_data()
        dashboard.save()

        return {
            "success": True,
            "operation_type": operation_type,
            "results": results,
            "timestamp": now_datetime().isoformat(),
        }

    except Exception as e:
        frappe.log_error(f"System maintenance failed: {e}", "License Management Dashboard")
        return {"success": False, "error": str(e)}
