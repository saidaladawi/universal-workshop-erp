# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import json
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate, now, today


class MobileDeviceManagement(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate mobile device data before saving"""
        self.validate_device_identifiers()
        self.validate_user_assignment()
        self.validate_policy_settings()
        self.validate_arabic_fields()
        self.update_compliance_status()

    def before_save(self):
        """Set default values and generate identifiers before saving"""
        if not self.device_uuid:
            self.device_uuid = str(uuid.uuid4())

        if not self.enrollment_date:
            self.enrollment_date = now()

        # Update last sync time
        self.last_sync_time = now()

        # Generate enrollment token if needed
        if not self.device_enrollment_token:
            self.device_enrollment_token = self.generate_enrollment_token()

    def validate_device_identifiers(self):
        """Validate device identifiers and prevent duplicates"""
        # Validate IMEI format (15 digits)
        if self.imei and not re.match(r"^\d{15}$", self.imei):
            frappe.throw(_("IMEI must be exactly 15 digits"))

        # Validate MAC address format
        if self.mac_address and not re.match(
            r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$", self.mac_address
        ):
            frappe.throw(_("Invalid MAC address format"))

        # Check for duplicate device IDs
        existing_device = frappe.db.get_value(
            "Mobile Device Management",
            {"device_id": self.device_id, "name": ["!=", self.name or ""]},
            "name",
        )
        if existing_device:
            frappe.throw(_("Device ID {0} already exists").format(self.device_id))

    def validate_user_assignment(self):
        """Validate user assignment and permissions"""
        if not self.assigned_user:
            frappe.throw(_("Assigned user is required"))

        # Check if user exists and is active
        user_enabled = frappe.db.get_value("User", self.assigned_user, "enabled")
        if not user_enabled:
            frappe.throw(_("Cannot assign device to disabled user"))

        # Validate contact information
        if self.contact_number and not re.match(r"^\+968\s?\d{8}$", self.contact_number):
            frappe.throw(_("Contact number must be in Oman format: +968 XXXXXXXX"))

    def validate_policy_settings(self):
        """Validate policy configuration settings"""
        # Screen lock timeout validation
        if self.screen_lock_timeout and (
            self.screen_lock_timeout < 1 or self.screen_lock_timeout > 60
        ):
            frappe.throw(_("Screen lock timeout must be between 1 and 60 minutes"))

        # Max failed attempts validation
        if self.max_failed_attempts and (
            self.max_failed_attempts < 3 or self.max_failed_attempts > 10
        ):
            frappe.throw(_("Max failed attempts must be between 3 and 10"))

        # Data usage limit validation
        if self.data_usage_limit and self.data_usage_limit < 0:
            frappe.throw(_("Data usage limit cannot be negative"))

    def validate_arabic_fields(self):
        """Ensure Arabic fields are properly filled"""
        if not self.device_name_ar and self.device_name:
            # Auto-suggest Arabic name if not provided
            self.device_name_ar = f"جهاز {self.device_name}"

        if not self.device_owner_ar and self.device_owner:
            # Auto-suggest Arabic owner name if not provided
            self.device_owner_ar = f"مالك الجهاز: {self.device_owner}"

    def update_compliance_status(self):
        """Calculate and update compliance status and score"""
        compliance_score = self.calculate_compliance_score()
        self.compliance_score = compliance_score

        # Determine compliance status
        if compliance_score >= 90:
            self.compliance_status = "Compliant / ممتثل"
        elif compliance_score >= 70:
            self.compliance_status = "Partial / جزئي"
        else:
            self.compliance_status = "Non-Compliant / غير ممتثل"

        self.last_compliance_check = now()

    def calculate_compliance_score(self) -> float:
        """Calculate device compliance score based on policies and security"""
        total_checks = 0
        passed_checks = 0

        # Policy compliance checks
        policy_checks = [
            ("password_policy_enabled", self.password_policy_enabled and not self.weak_password),
            ("encryption_enabled", self.encryption_enabled and not self.missing_encryption),
            ("auto_lock_enabled", self.auto_lock_enabled),
            ("remote_wipe_enabled", self.remote_wipe_enabled),
            ("app_restrictions_enabled", self.app_restrictions_enabled),
        ]

        for check_name, check_result in policy_checks:
            total_checks += 1
            if check_result:
                passed_checks += 1

        # Security compliance checks
        security_checks = [
            ("no_jailbreak", not self.jailbreak_detected),
            ("no_malware", not self.malware_detected),
            ("no_unauthorized_apps", not self.unauthorized_apps),
            ("updated_os", not self.outdated_os),
            ("certificate_valid", self.certificate_status == "Valid / صالح"),
        ]

        for check_name, check_result in security_checks:
            total_checks += 1
            if check_result:
                passed_checks += 1

        # Calculate score
        if total_checks == 0:
            return 0.0

        return round((passed_checks / total_checks) * 100, 1)

    def generate_enrollment_token(self) -> str:
        """Generate unique enrollment token for device registration"""
        token = str(uuid.uuid4()).replace("-", "")[:16].upper()
        return f"UW-{token}"

    @frappe.whitelist()
    def sync_device_info(self):
        """Sync device information from MDM provider"""
        try:
            # This would integrate with actual MDM service (e.g., Microsoft Intune, VMware Workspace ONE)
            # For now, simulate data collection

            # Update device metrics
            self.collect_device_metrics()

            # Check installed apps
            self.scan_installed_apps()

            # Update compliance status
            self.update_compliance_status()

            # Log activity
            self.log_activity("Device information synchronized successfully")

            # Save changes
            self.save()

            frappe.msgprint(_("Device information synchronized successfully"))

        except Exception as e:
            error_msg = f"Device sync failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.log_error(error_msg, "MDM Device Sync")
            frappe.throw(_("Device synchronization failed: {0}").format(str(e)))

    def collect_device_metrics(self):
        """Collect device performance and security metrics"""
        # Simulate collecting real device data
        # In production, this would connect to MDM APIs

        import random

        # Update battery level (simulation)
        self.battery_level = random.randint(20, 100)

        # Update signal strength (simulation)
        self.signal_strength = random.randint(-100, -50)

        # Update storage usage (simulation)
        if self.device_storage_total:
            self.device_storage_used = random.uniform(
                self.device_storage_total * 0.3, self.device_storage_total * 0.9
            )

        # Update security status (simulation)
        self.jailbreak_detected = random.choice([True, False]) if random.random() < 0.1 else False
        self.malware_detected = random.choice([True, False]) if random.random() < 0.05 else False

        # Update network quality
        signal_quality = abs(self.signal_strength or -70)
        if signal_quality <= 50:
            self.network_quality = "Excellent / ممتاز"
        elif signal_quality <= 70:
            self.network_quality = "Good / جيد"
        elif signal_quality <= 85:
            self.network_quality = "Fair / مقبول"
        else:
            self.network_quality = "Poor / ضعيف"

    def scan_installed_apps(self):
        """Scan and categorize installed applications"""
        # Simulate app scanning
        # In production, this would query MDM provider's API

        # Example app data structure
        installed_apps = [
            {
                "name": "Universal Workshop",
                "package": "com.universal.workshop",
                "type": "corporate",
            },
            {"name": "WhatsApp", "package": "com.whatsapp", "type": "personal"},
            {"name": "Chrome", "package": "com.android.chrome", "type": "browser"},
            {
                "name": "Microsoft Outlook",
                "package": "com.microsoft.office.outlook",
                "type": "corporate",
            },
        ]

        self.installed_apps = json.dumps(installed_apps)

        # Count apps by type
        corporate_count = len([app for app in installed_apps if app.get("type") == "corporate"])
        personal_count = len([app for app in installed_apps if app.get("type") == "personal"])

        self.corporate_apps_count = corporate_count
        self.personal_apps_count = personal_count

        # Check for restricted apps
        restricted_apps = ["com.example.restricted", "com.gambling.app"]
        restricted_found = len(
            [app for app in installed_apps if app.get("package") in restricted_apps]
        )
        self.restricted_apps_detected = restricted_found

        # Update app compliance score
        total_apps = len(installed_apps)
        if total_apps > 0:
            self.app_compliance_score = round(
                ((total_apps - restricted_found) / total_apps) * 100, 1
            )

        self.last_app_sync = now()

    @frappe.whitelist()
    def lock_device(self):
        """Lock the device remotely"""
        try:
            # In production, this would send lock command to MDM provider
            self.device_locked = True
            self.log_activity(f"Device locked remotely by {frappe.session.user}", "Security")
            self.save()

            # Send notification
            self.send_notification(
                "Device Locked",
                f"Device {self.device_name} has been locked remotely for security reasons.",
                "Security Alert",
            )

            frappe.msgprint(_("Device has been locked successfully"))

        except Exception as e:
            error_msg = f"Device lock failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.throw(_("Failed to lock device: {0}").format(str(e)))

    @frappe.whitelist()
    def unlock_device(self):
        """Unlock the device remotely"""
        try:
            # In production, this would send unlock command to MDM provider
            self.device_locked = False
            self.log_activity(f"Device unlocked remotely by {frappe.session.user}", "Security")
            self.save()

            frappe.msgprint(_("Device has been unlocked successfully"))

        except Exception as e:
            error_msg = f"Device unlock failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.throw(_("Failed to unlock device: {0}").format(str(e)))

    @frappe.whitelist()
    def initiate_remote_wipe(self, reason: str = ""):
        """Initiate remote wipe of the device"""
        try:
            # Validate reason
            if not reason:
                frappe.throw(_("Reason for remote wipe is required"))

            # Set wipe pending status
            self.remote_wipe_pending = True
            self.wipe_reason = reason
            self.wipe_initiated_by = frappe.session.user
            self.wipe_date = now()

            # Log security action
            self.log_activity(
                f"Remote wipe initiated by {frappe.session.user}. Reason: {reason}", "Security"
            )

            # Save changes
            self.save()

            # Send critical notification
            self.send_notification(
                "Critical: Remote Wipe Initiated",
                f"Remote wipe has been initiated for device {self.device_name}. Reason: {reason}",
                "Critical Security Alert",
            )

            frappe.msgprint(_("Remote wipe has been initiated successfully"))

        except Exception as e:
            error_msg = f"Remote wipe initiation failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.throw(_("Failed to initiate remote wipe: {0}").format(str(e)))

    @frappe.whitelist()
    def install_app(self, app_package: str, app_name: str = ""):
        """Install application on device"""
        try:
            # Validate app package
            if not app_package:
                frappe.throw(_("App package name is required"))

            # Add to pending installs
            pending_installs = json.loads(self.pending_app_installs or "[]")
            pending_installs.append(
                {
                    "package": app_package,
                    "name": app_name or app_package,
                    "initiated_at": now(),
                    "status": "pending",
                }
            )

            self.pending_app_installs = json.dumps(pending_installs)
            self.app_update_pending = True

            self.log_activity(f"App installation requested: {app_name or app_package}")
            self.save()

            frappe.msgprint(_("App installation has been queued"))

        except Exception as e:
            error_msg = f"App installation failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.throw(_("Failed to install app: {0}").format(str(e)))

    @frappe.whitelist()
    def uninstall_app(self, app_package: str):
        """Uninstall application from device"""
        try:
            # Validate app package
            if not app_package:
                frappe.throw(_("App package name is required"))

            # Log action
            self.log_activity(f"App uninstallation requested: {app_package}")

            # In production, send uninstall command to MDM provider
            frappe.msgprint(_("App uninstallation has been queued"))

        except Exception as e:
            error_msg = f"App uninstallation failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.throw(_("Failed to uninstall app: {0}").format(str(e)))

    def send_notification(self, title: str, message: str, priority: str = "Normal"):
        """Send notification to device and admin contacts"""
        try:
            # Log notification
            notification_data = {
                "title": title,
                "message": message,
                "priority": priority,
                "timestamp": now(),
                "language": self.notification_language or "Both / كلاهما",
            }

            # Update communication log
            comm_log = self.communication_log or ""
            comm_log += f"\n[{now()}] {priority}: {title} - {message}"
            self.communication_log = comm_log
            self.last_communication = now()

            # Send email notification if enabled
            if self.email_notifications and self.email_address:
                self.send_email_notification(title, message)

            # Send SMS notification if enabled
            if self.sms_notifications and self.contact_number:
                self.send_sms_notification(title, message)

            # In production, send push notification to device
            if self.push_notifications:
                # This would integrate with FCM, APNS, or MDM provider
                pass

        except Exception as e:
            frappe.log_error(f"Notification sending failed: {str(e)}", "MDM Notification")

    def send_email_notification(self, title: str, message: str):
        """Send email notification"""
        try:
            # Prepare email content in both languages if needed
            if self.notification_language == "Both / كلاهما":
                subject = f"{title} / تنبيه أمني"
                content = f"{message}\n\n---\n\nهذا تنبيه أمني من نظام إدارة الأجهزة المحمولة"
            elif self.notification_language == "Arabic / العربية":
                subject = f"تنبيه أمني: {title}"
                content = f"تنبيه أمني من نظام إدارة الأجهزة المحمولة\n\n{message}"
            else:
                subject = f"Security Alert: {title}"
                content = f"Security alert from Mobile Device Management system\n\n{message}"

            # Send email (this would use Frappe's email system)
            frappe.sendmail(
                recipients=[self.email_address],
                subject=subject,
                message=content,
                header=["Mobile Device Management Alert", "تنبيه إدارة الأجهزة المحمولة"],
            )

        except Exception as e:
            frappe.log_error(f"Email notification failed: {str(e)}", "MDM Email")

    def send_sms_notification(self, title: str, message: str):
        """Send SMS notification"""
        try:
            # Prepare SMS content (keep it short)
            if self.notification_language == "Arabic / العربية":
                sms_content = f"تنبيه أمني: {title[:50]}..."
            else:
                sms_content = f"Security Alert: {title[:50]}..."

            # In production, this would integrate with SMS provider
            # For now, just log the action
            self.log_activity(f"SMS notification sent: {sms_content}")

        except Exception as e:
            frappe.log_error(f"SMS notification failed: {str(e)}", "MDM SMS")

    def log_activity(self, activity: str, activity_type: str = "Info"):
        """Log device activity with timestamp"""
        timestamp = now()
        log_entry = f"[{timestamp}] {activity_type}: {activity}"

        # Update activity log
        current_log = self.activity_log or ""
        self.activity_log = f"{log_entry}\n{current_log}"

        # Update security log for security-related activities
        if activity_type in ["Security", "Error", "Critical"]:
            security_log = self.security_log or ""
            self.security_log = f"{log_entry}\n{security_log}"

    @frappe.whitelist()
    def run_compliance_check(self):
        """Run comprehensive compliance check"""
        try:
            # Sync latest device info
            self.collect_device_metrics()
            self.scan_installed_apps()

            # Check policy compliance
            violations = []

            # Check password policy
            if self.password_policy_enabled and self.weak_password:
                violations.append("Weak password detected")

            # Check encryption
            if self.encryption_enabled and self.missing_encryption:
                violations.append("Device encryption not enabled")

            # Check for jailbreak/root
            if self.jailbreak_detected:
                violations.append("Device jailbreak/root detected")

            # Check for malware
            if self.malware_detected:
                violations.append("Malware detected on device")

            # Check for unauthorized apps
            if self.unauthorized_apps:
                violations.append("Unauthorized applications installed")

            # Check OS version
            if self.outdated_os:
                violations.append("Operating system is outdated")

            # Update violation counts
            self.security_violations = len(
                [v for v in violations if "jailbreak" in v.lower() or "malware" in v.lower()]
            )
            self.policy_violations = len(violations) - self.security_violations

            # Update compliance status
            self.update_compliance_status()

            # Add compliance notes
            if violations:
                self.compliance_notes = "Violations found:\n" + "\n".join(violations)
            else:
                self.compliance_notes = "No compliance violations detected"

            # Log compliance check
            self.log_activity(f"Compliance check completed. Score: {self.compliance_score}%")

            # Save changes
            self.save()

            # Send notification if non-compliant
            if self.compliance_status == "Non-Compliant / غير ممتثل":
                self.send_notification(
                    "Compliance Alert",
                    f"Device {self.device_name} is non-compliant. Violations: {len(violations)}",
                    "High",
                )

            frappe.msgprint(
                _("Compliance check completed. Score: {0}%").format(self.compliance_score)
            )

        except Exception as e:
            error_msg = f"Compliance check failed: {str(e)}"
            self.log_activity(error_msg, "Error")
            frappe.throw(_("Compliance check failed: {0}").format(str(e)))

    @frappe.whitelist()
    def get_device_dashboard_data(self) -> Dict:
        """Get device dashboard data for UI display"""
        try:
            # Calculate uptime (approximate)
            enrollment_date = getdate(self.enrollment_date)
            days_active = (getdate(today()) - enrollment_date).days

            # Parse installed apps
            installed_apps = json.loads(self.installed_apps or "[]")

            # Calculate storage percentage
            storage_percentage = 0
            if self.device_storage_total and self.device_storage_used:
                storage_percentage = round(
                    (self.device_storage_used / self.device_storage_total) * 100, 1
                )

            dashboard_data = {
                "device_info": {
                    "name": self.device_name,
                    "name_ar": self.device_name_ar,
                    "type": self.device_type,
                    "status": self.device_status,
                    "manufacturer": self.manufacturer,
                    "model": self.device_model,
                    "os": f"{self.operating_system} {self.os_version}",
                },
                "compliance": {
                    "status": self.compliance_status,
                    "score": self.compliance_score,
                    "last_check": self.last_compliance_check,
                    "violations": self.security_violations + self.policy_violations,
                },
                "performance": {
                    "battery_level": self.battery_level,
                    "battery_health": self.battery_health,
                    "signal_strength": self.signal_strength,
                    "network_quality": self.network_quality,
                    "storage_used": storage_percentage,
                    "performance_score": self.performance_score,
                },
                "security": {
                    "device_locked": self.device_locked,
                    "encryption_enabled": self.encryption_enabled,
                    "jailbreak_detected": self.jailbreak_detected,
                    "malware_detected": self.malware_detected,
                    "last_security_scan": self.last_security_scan,
                    "certificate_status": self.certificate_status,
                },
                "apps": {
                    "total_installed": len(installed_apps),
                    "corporate_apps": self.corporate_apps_count,
                    "personal_apps": self.personal_apps_count,
                    "restricted_detected": self.restricted_apps_detected,
                    "app_compliance_score": self.app_compliance_score,
                },
                "usage": {
                    "days_active": days_active,
                    "last_sync": self.last_sync_time,
                    "data_usage": self.total_data_usage,
                    "daily_average": self.daily_usage_average,
                },
            }

            return dashboard_data

        except Exception as e:
            frappe.log_error(f"Dashboard data retrieval failed: {str(e)}", "MDM Dashboard")
            return {}

    @frappe.whitelist()
    def export_device_report(self) -> Dict:
        """Export comprehensive device report"""
        try:
            report_data = {
                "device_information": {
                    "device_name": self.device_name,
                    "device_name_ar": self.device_name_ar,
                    "device_id": self.device_id,
                    "device_type": self.device_type,
                    "manufacturer": self.manufacturer,
                    "model": self.device_model,
                    "serial_number": self.serial_number,
                    "imei": self.imei,
                    "operating_system": self.operating_system,
                    "os_version": self.os_version,
                    "enrollment_date": self.enrollment_date,
                    "assigned_user": self.assigned_user,
                    "department": self.department,
                },
                "compliance_report": {
                    "compliance_status": self.compliance_status,
                    "compliance_score": self.compliance_score,
                    "last_compliance_check": self.last_compliance_check,
                    "security_violations": self.security_violations,
                    "policy_violations": self.policy_violations,
                    "compliance_notes": self.compliance_notes,
                },
                "security_status": {
                    "encryption_enabled": self.encryption_enabled,
                    "password_policy_enabled": self.password_policy_enabled,
                    "remote_wipe_enabled": self.remote_wipe_enabled,
                    "device_locked": self.device_locked,
                    "jailbreak_detected": self.jailbreak_detected,
                    "malware_detected": self.malware_detected,
                    "certificate_status": self.certificate_status,
                    "last_security_scan": self.last_security_scan,
                },
                "activity_summary": {
                    "last_sync_time": self.last_sync_time,
                    "battery_level": self.battery_level,
                    "signal_strength": self.signal_strength,
                    "network_quality": self.network_quality,
                    "total_data_usage": self.total_data_usage,
                    "corporate_apps_count": self.corporate_apps_count,
                    "personal_apps_count": self.personal_apps_count,
                },
                "logs": {
                    "activity_log": self.activity_log,
                    "security_log": self.security_log,
                    "communication_log": self.communication_log,
                },
                "generated_at": now(),
                "generated_by": frappe.session.user,
            }

            return report_data

        except Exception as e:
            frappe.log_error(f"Device report export failed: {str(e)}", "MDM Report")
            return {}


# WhiteListed methods for API access
@frappe.whitelist()
def get_device_list(filters: Optional[Dict] = None) -> List[Dict]:
    """Get list of managed devices with optional filters"""
    try:
        # Default filters
        if not filters:
            filters = {"device_status": ["!=", "Retired / متقاعد"]}

        devices = frappe.get_list(
            "Mobile Device Management",
            filters=filters,
            fields=[
                "name",
                "device_name",
                "device_name_ar",
                "device_type",
                "device_status",
                "compliance_status",
                "assigned_user",
                "last_sync_time",
                "battery_level",
                "compliance_score",
            ],
            order_by="device_name asc",
        )

        return devices

    except Exception as e:
        frappe.log_error(f"Device list retrieval failed: {str(e)}", "MDM API")
        return []


@frappe.whitelist()
def get_compliance_summary() -> Dict:
    """Get compliance summary across all devices"""
    try:
        # Get device counts by compliance status
        compliance_data = frappe.db.sql(
            """
            SELECT 
                compliance_status,
                COUNT(*) as count,
                AVG(compliance_score) as avg_score
            FROM `tabMobile Device Management`
            WHERE device_status != 'Retired / متقاعد'
            GROUP BY compliance_status
        """,
            as_dict=True,
        )

        # Get total counts
        total_devices = frappe.db.count(
            "Mobile Device Management", {"device_status": ["!=", "Retired / متقاعد"]}
        )

        # Get devices with violations
        devices_with_violations = frappe.db.sql(
            """
            SELECT COUNT(*) as count
            FROM `tabMobile Device Management`
            WHERE (security_violations > 0 OR policy_violations > 0)
            AND device_status != 'Retired / متقاعد'
        """,
            as_dict=True,
        )[0].count

        summary = {
            "total_devices": total_devices,
            "compliance_breakdown": compliance_data,
            "devices_with_violations": devices_with_violations,
            "compliance_rate": 0,
        }

        # Calculate overall compliance rate
        if total_devices > 0:
            compliant_devices = sum(
                [
                    item["count"]
                    for item in compliance_data
                    if "Compliant" in item["compliance_status"]
                ]
            )
            summary["compliance_rate"] = round((compliant_devices / total_devices) * 100, 1)

        return summary

    except Exception as e:
        frappe.log_error(f"Compliance summary retrieval failed: {str(e)}", "MDM API")
        return {}


@frappe.whitelist()
def bulk_device_action(device_names: List[str], action: str, **kwargs) -> Dict:
    """Perform bulk action on multiple devices"""
    try:
        results = {"success": [], "failed": []}

        for device_name in device_names:
            try:
                device = frappe.get_doc("Mobile Device Management", device_name)

                if action == "sync":
                    device.sync_device_info()
                elif action == "lock":
                    device.lock_device()
                elif action == "unlock":
                    device.unlock_device()
                elif action == "compliance_check":
                    device.run_compliance_check()
                elif action == "remote_wipe":
                    reason = kwargs.get("reason", "Bulk security action")
                    device.initiate_remote_wipe(reason)
                else:
                    raise ValueError(f"Unknown action: {action}")

                results["success"].append(device_name)

            except Exception as e:
                results["failed"].append({"device": device_name, "error": str(e)})

        return results

    except Exception as e:
        frappe.log_error(f"Bulk device action failed: {str(e)}", "MDM Bulk Action")
        return {"success": [], "failed": [{"error": str(e)}]}


@frappe.whitelist()
def enroll_new_device(device_data: Dict) -> Dict:
    """Enroll a new device in the MDM system"""
    try:
        # Validate required fields
        required_fields = ["device_name", "device_id", "device_type", "assigned_user"]
        for field in required_fields:
            if not device_data.get(field):
                frappe.throw(_("Missing required field: {0}").format(field))

        # Create new device record
        device = frappe.new_doc("Mobile Device Management")
        device.update(device_data)

        # Set default values
        device.enrollment_method = device_data.get("enrollment_method", "Manual / يدوي")
        device.policy_profile = device_data.get("policy_profile", "Technician / فني")
        device.device_status = "Active / نشط"

        # Save device
        device.insert()

        # Run initial compliance check
        device.run_compliance_check()

        return {
            "success": True,
            "device_name": device.name,
            "enrollment_token": device.device_enrollment_token,
            "message": _("Device enrolled successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Device enrollment failed: {str(e)}", "MDM Enrollment")
        return {"success": False, "error": str(e), "message": _("Device enrollment failed")}
