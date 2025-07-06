# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
import os
from datetime import datetime, timedelta


class ReportScheduleExecution(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def before_insert(self):
        """Set default values before inserting execution record"""
        if not self.execution_id:
            self.execution_id = frappe.generate_hash(length=10)

        if not self.execution_time:
            self.execution_time = frappe.utils.now_datetime()

        if not self.execution_status:
            self.execution_status = "Queued"

    def validate(self):
        """Validate execution record data"""
        self.validate_execution_status()
        self.calculate_execution_duration()

    def validate_execution_status(self):
        """Validate execution status transitions"""
        valid_statuses = ["Queued", "Running", "Completed", "Failed", "Cancelled", "Retrying"]
        if self.execution_status not in valid_statuses:
            frappe.throw(_("Invalid execution status: {0}").format(self.execution_status))

    def calculate_execution_duration(self):
        """Calculate execution duration if start and end times are available"""
        if self.execution_time and self.execution_status in ["Completed", "Failed", "Cancelled"]:
            if not self.execution_duration:
                # Calculate duration based on creation time vs current time
                start_time = frappe.utils.get_datetime(self.execution_time)
                end_time = frappe.utils.now_datetime()
                duration = (end_time - start_time).total_seconds()
                self.execution_duration = int(duration)

    def mark_as_running(self):
        """Mark execution as running"""
        self.execution_status = "Running"
        self.execution_time = frappe.utils.now_datetime()
        self.save()

    def mark_as_completed(self, file_path=None, file_url=None, rows_generated=0, file_size=None):
        """Mark execution as completed with results"""
        self.execution_status = "Completed"
        self.rows_generated = rows_generated

        if file_path:
            self.file_path = file_path
        if file_url:
            self.file_url = file_url
        if file_size:
            self.file_size = file_size

        # Set file expiry date (30 days by default)
        self.file_expiry_date = frappe.utils.add_days(frappe.utils.today(), 30)

        self.calculate_execution_duration()
        self.save()

    def mark_as_failed(self, error_message, error_traceback=None):
        """Mark execution as failed with error details"""
        self.execution_status = "Failed"
        self.error_message = error_message
        if error_traceback:
            self.error_traceback = error_traceback

        self.calculate_execution_duration()
        self.save()

    def mark_as_cancelled(self):
        """Mark execution as cancelled"""
        self.execution_status = "Cancelled"
        self.calculate_execution_duration()
        self.save()

    def retry_execution(self):
        """Retry failed execution if within retry limits"""
        if self.retry_count >= self.max_retries:
            frappe.throw(
                _("Maximum retry limit ({0}) reached for this execution").format(self.max_retries)
            )

        self.retry_count += 1
        self.execution_status = "Retrying"
        self.error_message = None
        self.error_traceback = None
        self.save()

    def update_delivery_status(self, status, email_count=0, notification_sent=False):
        """Update delivery status and counts"""
        valid_delivery_statuses = ["Pending", "Sent", "Delivered", "Failed", "Bounced"]
        if status not in valid_delivery_statuses:
            frappe.throw(_("Invalid delivery status: {0}").format(status))

        self.delivery_status = status
        if email_count > 0:
            self.email_sent_count = email_count
        if notification_sent:
            self.notification_sent = 1

        self.save()

    def increment_download_count(self):
        """Increment file download count"""
        if not self.download_count:
            self.download_count = 0
        self.download_count += 1
        self.save()

    def check_file_expiry(self):
        """Check if the file has expired and mark for deletion"""
        if (
            self.file_expiry_date
            and frappe.utils.getdate(self.file_expiry_date) < frappe.utils.today()
        ):
            self.delete_file()

    def delete_file(self):
        """Delete the generated file and mark as deleted"""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                self.file_deleted = 1
                self.file_path = None
                self.file_url = None
                self.save()
                frappe.log("Report file deleted: {0}".format(self.file_path))
            except Exception as e:
                frappe.log_error(f"Failed to delete report file: {e}", "Report Schedule Execution")

    def get_execution_summary(self):
        """Get execution summary for reporting"""
        return {
            "execution_id": self.execution_id,
            "status": self.execution_status,
            "duration": self.execution_duration or 0,
            "rows_generated": self.rows_generated or 0,
            "delivery_status": self.delivery_status,
            "error_message": self.error_message,
            "file_size": self.file_size,
            "download_count": self.download_count or 0,
        }


@frappe.whitelist()
def get_execution_history(report_schedule, limit=10):
    """Get execution history for a report schedule"""
    executions = frappe.get_list(
        "Report Schedule Execution",
        filters={"parent": report_schedule},
        fields=[
            "name",
            "execution_id",
            "execution_time",
            "execution_status",
            "execution_duration",
            "rows_generated",
            "delivery_status",
            "error_message",
            "file_size",
            "download_count",
        ],
        order_by="execution_time desc",
        limit=limit,
    )

    return executions


@frappe.whitelist()
def download_report_file(execution_name):
    """Download report file from execution record"""
    execution = frappe.get_doc("Report Schedule Execution", execution_name)

    if not execution.file_path or execution.file_deleted:
        frappe.throw(_("Report file is not available or has been deleted"))

    if not os.path.exists(execution.file_path):
        frappe.throw(_("Report file not found on server"))

    # Check file expiry
    execution.check_file_expiry()
    if execution.file_deleted:
        frappe.throw(_("Report file has expired and been deleted"))

    # Increment download count
    execution.increment_download_count()

    # Return file for download
    with open(execution.file_path, "rb") as f:
        file_content = f.read()

    filename = os.path.basename(execution.file_path)
    frappe.local.response.filename = filename
    frappe.local.response.filecontent = file_content
    frappe.local.response.type = "download"


@frappe.whitelist()
def cleanup_expired_files():
    """Clean up expired report files (to be run via scheduler)"""
    executions = frappe.get_list(
        "Report Schedule Execution",
        filters={"file_expiry_date": ["<", frappe.utils.today()], "file_deleted": 0},
        fields=["name"],
    )

    deleted_count = 0
    for execution_name in executions:
        try:
            execution = frappe.get_doc("Report Schedule Execution", execution_name["name"])
            execution.delete_file()
            deleted_count += 1
        except Exception as e:
            frappe.log_error(
                f"Failed to cleanup file for {execution_name}: {e}", "Report Schedule Cleanup"
            )

    frappe.log(f"Cleaned up {deleted_count} expired report files")
    return deleted_count


@frappe.whitelist()
def get_execution_statistics(report_schedule=None, days=30):
    """Get execution statistics for reports"""
    filters = {}
    if report_schedule:
        filters["parent"] = report_schedule

    # Get executions from last N days
    from_date = frappe.utils.add_days(frappe.utils.today(), -days)
    filters["execution_time"] = [">=", from_date]

    executions = frappe.get_list(
        "Report Schedule Execution",
        filters=filters,
        fields=["execution_status", "execution_duration", "rows_generated", "delivery_status"],
    )

    stats = {
        "total_executions": len(executions),
        "successful_executions": len([e for e in executions if e.execution_status == "Completed"]),
        "failed_executions": len([e for e in executions if e.execution_status == "Failed"]),
        "average_duration": 0,
        "total_rows_generated": sum([e.rows_generated or 0 for e in executions]),
        "successful_deliveries": len([e for e in executions if e.delivery_status == "Delivered"]),
    }

    # Calculate average duration
    durations = [e.execution_duration for e in executions if e.execution_duration]
    if durations:
        stats["average_duration"] = sum(durations) / len(durations)

    # Calculate success rates
    if stats["total_executions"] > 0:
        stats["success_rate"] = (stats["successful_executions"] / stats["total_executions"]) * 100
        stats["delivery_success_rate"] = (
            stats["successful_deliveries"] / stats["total_executions"]
        ) * 100
    else:
        stats["success_rate"] = 0
        stats["delivery_success_rate"] = 0

    return stats
