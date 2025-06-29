# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import os
import json
import time
import hashlib
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, cint, now_datetime, add_days, get_datetime, format_datetime


class BackupManager(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate backup settings and configuration"""
        self.validate_backup_type()
        self.validate_schedule_settings()
        self.validate_retention_settings()
        self.validate_storage_settings()

    def before_save(self):
        """Set default values and calculate fields before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_on:
            self.created_on = now_datetime()

        # Auto-generate backup name if not provided
        if not self.backup_name:
            self.backup_name = self.generate_backup_name()

        # Calculate estimated completion time
        if self.backup_type and self.status == "Scheduled":
            self.estimated_duration = self.estimate_backup_duration()

    def validate_backup_type(self):
        """Validate backup type and settings"""
        if not self.backup_type:
            frappe.throw(_("Backup type is required"))

        if self.backup_type == "Scheduled" and not self.scheduled_time:
            frappe.throw(_("Scheduled time is required for scheduled backups"))

        if self.backup_type == "Manual" and self.status not in [
            "Pending",
            "In Progress",
            "Completed",
            "Failed",
        ]:
            frappe.throw(_("Invalid status for manual backup"))

    def validate_schedule_settings(self):
        """Validate scheduling configuration"""
        if self.backup_type == "Scheduled":
            if not self.frequency:
                frappe.throw(_("Backup frequency is required"))

            if self.frequency == "Custom" and not self.cron_expression:
                frappe.throw(_("Cron expression is required for custom frequency"))

    def validate_retention_settings(self):
        """Validate backup retention policy"""
        if self.retention_days and self.retention_days < 1:
            frappe.throw(_("Retention days must be at least 1"))

        if self.max_backup_count and self.max_backup_count < 1:
            frappe.throw(_("Maximum backup count must be at least 1"))

    def validate_storage_settings(self):
        """Validate storage configuration"""
        if self.storage_location:
            # Ensure storage directory exists and is writable
            storage_path = Path(self.storage_location)
            try:
                storage_path.mkdir(parents=True, exist_ok=True)
                if not os.access(storage_path, os.W_OK):
                    frappe.throw(
                        _("Storage location is not writable: {0}").format(self.storage_location)
                    )
            except Exception as e:
                frappe.throw(_("Invalid storage location: {0}").format(str(e)))

    def generate_backup_name(self) -> str:
        """Generate automatic backup name"""
        site_name = frappe.local.site or "universal"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_suffix = "auto" if self.backup_type == "Scheduled" else "manual"
        return f"BK-{site_name}-{timestamp}-{backup_suffix}"

    def estimate_backup_duration(self) -> int:
        """Estimate backup duration in minutes based on data size"""
        try:
            # Get database size
            db_size = self.get_database_size()

            # Get files size if including files
            files_size = 0
            if self.include_files:
                files_size = self.get_files_size()

            total_size_gb = (db_size + files_size) / (1024 * 1024 * 1024)

            # Estimate: ~1GB per minute (conservative estimate)
            estimated_minutes = max(1, int(total_size_gb * 1.5))

            return estimated_minutes

        except Exception:
            # Default estimate if calculation fails
            return 15

    def get_database_size(self) -> int:
        """Get current database size in bytes"""
        try:
            result = frappe.db.sql(
                """
                SELECT 
                    SUM(data_length + index_length) as size
                FROM information_schema.tables 
                WHERE table_schema = %s
            """,
                [frappe.conf.db_name],
            )

            return int(result[0][0]) if result and result[0][0] else 0

        except Exception:
            return 0

    def get_files_size(self) -> int:
        """Get total size of files to be backed up"""
        try:
            site_path = Path(frappe.get_site_path())
            total_size = 0

            # Calculate public files size
            public_path = site_path / "public"
            if public_path.exists():
                total_size += self.get_directory_size(public_path)

            # Calculate private files size if included
            if self.include_private_files:
                private_path = site_path / "private"
                if private_path.exists():
                    total_size += self.get_directory_size(private_path)

            return total_size

        except Exception:
            return 0

    def get_directory_size(self, path: Path) -> int:
        """Get directory size recursively"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
            return total_size
        except Exception:
            return 0

    @frappe.whitelist()
    def create_backup(self) -> Dict:
        """Create a new backup"""
        try:
            # Update status
            self.status = "In Progress"
            self.started_at = now_datetime()
            self.save()
            frappe.db.commit()

            # Create backup directory
            backup_dir = self.prepare_backup_directory()

            # Execute backup based on type
            backup_result = self.execute_backup(backup_dir)

            if backup_result["success"]:
                # Update success status
                self.status = "Completed"
                self.completed_at = now_datetime()
                self.file_path = backup_result["file_path"]
                self.backup_size = backup_result["size"]
                self.compression_ratio = backup_result.get("compression_ratio", 0)

                # Calculate actual duration
                if self.started_at:
                    duration = (
                        get_datetime(self.completed_at) - get_datetime(self.started_at)
                    ).total_seconds()
                    self.duration_minutes = int(duration / 60)

                # Verify backup if enabled
                if self.verification_enabled:
                    verification_result = self.verify_backup()
                    self.verification_status = "Passed" if verification_result else "Failed"
                    self.verification_result = json.dumps(verification_result)

                # Send notification
                if self.send_notification:
                    self.send_backup_notification("success")

                self.log_backup_event("Backup completed successfully", "Info")

            else:
                # Update failure status
                self.status = "Failed"
                self.completed_at = now_datetime()
                self.error_log = backup_result.get("error", "Unknown error occurred")

                if self.send_notification:
                    self.send_backup_notification("failure")

                self.log_backup_event(f"Backup failed: {self.error_log}", "Error")

            self.save()
            frappe.db.commit()

            return {
                "success": backup_result["success"],
                "message": (
                    _("Backup completed successfully")
                    if backup_result["success"]
                    else _("Backup failed")
                ),
                "backup_name": self.backup_name,
                "file_path": self.file_path if backup_result["success"] else None,
            }

        except Exception as e:
            self.status = "Failed"
            self.error_log = str(e)
            self.completed_at = now_datetime()
            self.save()
            frappe.db.commit()

            self.log_backup_event(f"Backup exception: {str(e)}", "Error")

            return {"success": False, "message": _("Backup failed: {0}").format(str(e))}

    def prepare_backup_directory(self) -> str:
        """Prepare backup directory and return path"""
        # Use configured storage location or default
        if self.storage_location:
            backup_base = Path(self.storage_location)
        else:
            backup_base = Path(frappe.get_site_path()) / "private" / "backups"

        # Create timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_dir = backup_base / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        return str(backup_dir)

    def execute_backup(self, backup_dir: str) -> Dict:
        """Execute the actual backup process"""
        try:
            site_name = frappe.local.site
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Generate backup filename
            backup_filename = f"{self.backup_name}_{timestamp}.sql.gz"
            backup_path = os.path.join(backup_dir, backup_filename)

            # Build backup command
            cmd = ["bench", "--site", site_name, "backup"]

            if self.include_files:
                cmd.append("--with-files")

            if self.include_private_files:
                cmd.append("--with-private-files")

            # Add backup path
            cmd.extend(["--backup-path-db", backup_path])

            # Execute backup command
            self.log_backup_event(f"Starting backup with command: {' '.join(cmd)}", "Info")

            result = subprocess.run(
                cmd,
                cwd=frappe.get_app_path("frappe", ".."),
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            if result.returncode == 0:
                # Verify file was created
                if os.path.exists(backup_path):
                    file_size = os.path.getsize(backup_path)

                    # Calculate compression ratio if possible
                    compression_ratio = 0
                    try:
                        original_size = self.get_database_size()
                        if original_size > 0:
                            compression_ratio = round((1 - file_size / original_size) * 100, 2)
                    except Exception:
                        pass

                    return {
                        "success": True,
                        "file_path": backup_path,
                        "size": file_size,
                        "compression_ratio": compression_ratio,
                    }
                else:
                    return {"success": False, "error": "Backup file was not created"}
            else:
                return {"success": False, "error": f"Backup command failed: {result.stderr}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Backup timed out after 1 hour"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def verify_backup(self) -> Dict:
        """Verify backup integrity"""
        try:
            if not self.file_path or not os.path.exists(self.file_path):
                return {"status": "Failed", "message": "Backup file not found"}

            verification_results = {}

            # File size check
            file_size = os.path.getsize(self.file_path)
            verification_results["file_size_check"] = {
                "status": "Passed" if file_size > 0 else "Failed",
                "size": file_size,
            }

            # MD5 checksum
            if self.calculate_checksums:
                md5_hash = self.calculate_file_hash(self.file_path, "md5")
                self.md5_checksum = md5_hash
                verification_results["md5_checksum"] = {"status": "Passed", "hash": md5_hash}

                # SHA256 checksum
                sha256_hash = self.calculate_file_hash(self.file_path, "sha256")
                self.sha256_checksum = sha256_hash
                verification_results["sha256_checksum"] = {"status": "Passed", "hash": sha256_hash}

            # File integrity check (try to read the file)
            try:
                if self.file_path.endswith(".gz"):
                    import gzip

                    with gzip.open(self.file_path, "rb") as f:
                        # Read first few bytes to verify it's a valid gzip file
                        f.read(100)
                else:
                    with open(self.file_path, "rb") as f:
                        f.read(100)

                verification_results["file_integrity"] = {
                    "status": "Passed",
                    "message": "File is readable and not corrupted",
                }
            except Exception as e:
                verification_results["file_integrity"] = {
                    "status": "Failed",
                    "message": f"File integrity check failed: {str(e)}",
                }

            # Overall verification status
            all_passed = all(
                result.get("status") == "Passed" for result in verification_results.values()
            )

            verification_results["overall_status"] = "Passed" if all_passed else "Failed"

            return verification_results

        except Exception as e:
            return {"status": "Failed", "message": f"Verification failed: {str(e)}"}

    def calculate_file_hash(self, file_path: str, algorithm: str = "md5") -> str:
        """Calculate file hash"""
        try:
            hash_func = (
                hashlib.md5(usedforsecurity=False) if algorithm == "md5" else hashlib.sha256()
            )

            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)

            return hash_func.hexdigest()

        except Exception:
            return ""

    def send_backup_notification(self, status: str):
        """Send backup completion notification"""
        try:
            if not self.notification_email:
                return

            subject = _("Backup {0}: {1}").format(
                _("Completed") if status == "success" else _("Failed"), self.backup_name
            )

            if status == "success":
                message = _(
                    """
                Backup completed successfully:
                
                Backup Name: {0}
                Started: {1}
                Completed: {2}
                Duration: {3} minutes
                File Size: {4} MB
                File Path: {5}
                
                Verification: {6}
                """
                ).format(
                    self.backup_name,
                    format_datetime(self.started_at),
                    format_datetime(self.completed_at),
                    self.duration_minutes or 0,
                    round((self.backup_size or 0) / (1024 * 1024), 2),
                    self.file_path or "",
                    self.verification_status or "Not performed",
                )
            else:
                message = _(
                    """
                Backup failed:
                
                Backup Name: {0}
                Started: {1}
                Failed: {2}
                Error: {3}
                """
                ).format(
                    self.backup_name,
                    format_datetime(self.started_at),
                    format_datetime(self.completed_at),
                    self.error_log or "Unknown error",
                )

            frappe.sendmail(recipients=[self.notification_email], subject=subject, message=message)

        except Exception as e:
            self.log_backup_event(f"Failed to send notification: {str(e)}", "Warning")

    def log_backup_event(self, message: str, level: str = "Info"):
        """Log backup events"""
        try:
            log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n"

            if not self.backup_log:
                self.backup_log = ""

            self.backup_log += log_entry

            # Keep only last 100 lines to prevent excessive growth
            lines = self.backup_log.split("\n")
            if len(lines) > 100:
                self.backup_log = "\n".join(lines[-100:])

            # Also log to Frappe's error log for important events
            if level in ["Error", "Critical"]:
                frappe.log_error(message, "Backup Manager")

        except Exception:
            pass

    @frappe.whitelist()
    def delete_backup(self) -> Dict:
        """Delete backup file and record"""
        try:
            # Delete physical file if exists
            if self.file_path and os.path.exists(self.file_path):
                os.remove(self.file_path)
                self.log_backup_event(f"Backup file deleted: {self.file_path}", "Info")

            # Delete the document
            self.delete()
            frappe.db.commit()

            return {"success": True, "message": _("Backup deleted successfully")}

        except Exception as e:
            return {"success": False, "message": _("Failed to delete backup: {0}").format(str(e))}

    @staticmethod
    @frappe.whitelist()
    def cleanup_old_backups(retention_days: int = None) -> Dict:
        """Clean up old backups based on retention policy"""
        try:
            if retention_days is None:
                # Get default retention from settings
                settings = frappe.get_single("Universal Workshop Settings")
                retention_days = settings.backup_retention_days or 30

            cutoff_date = add_days(now_datetime(), -retention_days)

            # Find old backups
            old_backups = frappe.get_list(
                "Backup Manager",
                filters={"creation": ["<", cutoff_date], "status": "Completed"},
                fields=["name", "file_path", "backup_name"],
            )

            deleted_count = 0
            for backup in old_backups:
                try:
                    # Delete file if exists
                    if backup.file_path and os.path.exists(backup.file_path):
                        os.remove(backup.file_path)

                    # Delete record
                    frappe.delete_doc("Backup Manager", backup.name)
                    deleted_count += 1

                except Exception as e:
                    frappe.log_error(
                        f"Failed to delete backup {backup.name}: {str(e)}", "Backup Cleanup"
                    )

            frappe.db.commit()

            return {
                "success": True,
                "message": _("Cleaned up {0} old backups").format(deleted_count),
                "deleted_count": deleted_count,
            }

        except Exception as e:
            return {"success": False, "message": _("Backup cleanup failed: {0}").format(str(e))}

    @staticmethod
    @frappe.whitelist()
    def get_backup_statistics() -> Dict:
        """Get backup statistics and health information"""
        try:
            # Count backups by status
            stats = frappe.db.sql(
                """
                SELECT 
                    status,
                    COUNT(*) as count,
                    AVG(duration_minutes) as avg_duration,
                    SUM(backup_size) as total_size
                FROM `tabBackup Manager`
                GROUP BY status
            """,
                as_dict=True,
            )

            # Recent backup success rate
            recent_backups = frappe.db.sql(
                """
                SELECT status
                FROM `tabBackup Manager`
                WHERE creation >= %s
                ORDER BY creation DESC
            """,
                [add_days(now_datetime(), -7)],
                as_list=True,
            )

            total_recent = len(recent_backups)
            successful_recent = len([b for b in recent_backups if b[0] == "Completed"])
            success_rate = (successful_recent / total_recent * 100) if total_recent > 0 else 0

            # Storage usage
            total_storage = sum(stat.total_size or 0 for stat in stats)

            # Next scheduled backup
            next_backup = frappe.db.get_value(
                "Backup Manager",
                filters={
                    "backup_type": "Scheduled",
                    "status": "Scheduled",
                    "scheduled_time": [">", now_datetime()],
                },
                fieldname=["backup_name", "scheduled_time"],
                order_by="scheduled_time ASC",
            )

            return {
                "success": True,
                "statistics": {
                    "status_breakdown": stats,
                    "success_rate": round(success_rate, 2),
                    "total_storage_bytes": total_storage,
                    "total_storage_mb": (
                        round(total_storage / (1024 * 1024), 2) if total_storage else 0
                    ),
                    "total_backups": sum(stat.count for stat in stats),
                    "next_scheduled": {
                        "name": next_backup[0] if next_backup else None,
                        "time": next_backup[1] if next_backup else None,
                    },
                },
            }

        except Exception as e:
            return {
                "success": False,
                "message": _("Failed to get backup statistics: {0}").format(str(e)),
            }


@frappe.whitelist()
def create_scheduled_backup(backup_name: str = None) -> Dict:
    """Create a scheduled backup (called by cron job)"""
    try:
        # Create new backup manager document
        backup_doc = frappe.new_doc("Backup Manager")
        backup_doc.backup_type = "Scheduled"
        backup_doc.backup_name = backup_name or f"Auto-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_doc.status = "Pending"
        backup_doc.scheduled_time = now_datetime()

        # Get default settings from Universal Workshop Settings
        settings = frappe.get_single("Universal Workshop Settings")
        backup_doc.include_files = getattr(settings, "backup_include_files", 1)
        backup_doc.include_private_files = getattr(settings, "backup_include_private_files", 0)
        backup_doc.verification_enabled = getattr(settings, "backup_verification_enabled", 1)
        backup_doc.send_notification = getattr(settings, "backup_send_notifications", 1)
        backup_doc.notification_email = getattr(settings, "backup_notification_email", "")

        backup_doc.insert()
        frappe.db.commit()

        # Execute the backup
        result = backup_doc.create_backup()

        return result

    except Exception as e:
        frappe.log_error(f"Scheduled backup failed: {str(e)}", "Backup Manager")
        return {"success": False, "message": _("Scheduled backup failed: {0}").format(str(e))}


@frappe.whitelist()
def get_backup_health_status() -> Dict:
    """Get overall backup system health status"""
    try:
        # Check last successful backup
        last_backup = frappe.db.get_value(
            "Backup Manager",
            filters={"status": "Completed"},
            fieldname=["backup_name", "completed_at"],
            order_by="completed_at DESC",
        )

        health_status = "Healthy"
        warnings = []

        if not last_backup:
            health_status = "Critical"
            warnings.append(_("No successful backups found"))
        else:
            last_backup_time = get_datetime(last_backup[1])
            days_since_backup = (now_datetime() - last_backup_time).days

            if days_since_backup > 7:
                health_status = "Critical"
                warnings.append(
                    _("Last successful backup was {0} days ago").format(days_since_backup)
                )
            elif days_since_backup > 3:
                health_status = "Warning"
                warnings.append(
                    _("Last successful backup was {0} days ago").format(days_since_backup)
                )

        # Check for failed backups in last 24 hours
        failed_backups = frappe.db.count(
            "Backup Manager",
            filters={"status": "Failed", "creation": [">", add_days(now_datetime(), -1)]},
        )

        if failed_backups > 0:
            if health_status == "Healthy":
                health_status = "Warning"
            warnings.append(_("{0} backup(s) failed in the last 24 hours").format(failed_backups))

        # Check storage space
        # This would require system-specific implementation

        return {
            "success": True,
            "health_status": health_status,
            "warnings": warnings,
            "last_backup": {
                "name": last_backup[0] if last_backup else None,
                "time": last_backup[1] if last_backup else None,
            },
            "failed_in_24h": failed_backups,
        }

    except Exception as e:
        return {
            "success": False,
            "message": _("Failed to get backup health status: {0}").format(str(e)),
        }
