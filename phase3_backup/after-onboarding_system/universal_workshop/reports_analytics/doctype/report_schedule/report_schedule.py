# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import (
    now_datetime,
    add_days,
    add_months,
    get_datetime,
    getdate,
    format_datetime,
    cint,
    flt,
    get_files_path,
)
from datetime import datetime, timedelta
import json
import os
import traceback
from typing import Dict, List, Optional, Any


class ReportSchedule(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def autoname(self):
        """Generate schedule name based on naming series"""
        if not self.schedule_name:
            self.schedule_name = f"Schedule for {self.report_name or 'Report'}"

        # Generate unique ID following naming convention
        from frappe.model.naming import make_autoname

        self.name = make_autoname("SCH-.YYYY.-.#####")

    def validate(self):
        """Validate report schedule configuration"""
        self.validate_report_reference()
        self.validate_schedule_configuration()
        self.validate_delivery_configuration()
        self.validate_date_ranges()
        self.set_next_execution_time()

    def validate_report_reference(self):
        """Validate that the linked report exists and is accessible"""
        if not self.report_name:
            frappe.throw(_("Report name is required"))

        # Check if report exists in Report DocType
        if not frappe.db.exists("Report", self.report_name):
            frappe.throw(_("Report '{0}' does not exist").format(self.report_name))

    def validate_schedule_configuration(self):
        """Validate schedule frequency and timing"""
        if not self.frequency:
            frappe.throw(_("Schedule frequency is required"))

        valid_frequencies = ["Daily", "Weekly", "Monthly", "Yearly", "Custom Cron"]
        if self.frequency not in valid_frequencies:
            frappe.throw(_("Invalid frequency: {0}").format(self.frequency))

        if self.frequency == "Weekly" and not self.day_of_week:
            frappe.throw(_("Day of week is required for weekly schedules"))

        if self.frequency == "Monthly" and not self.day_of_month:
            frappe.throw(_("Day of month is required for monthly schedules"))

        if self.frequency == "Custom Cron" and not self.cron_expression:
            frappe.throw(_("Cron expression is required for custom schedules"))

    def validate_delivery_configuration(self):
        """Validate delivery methods and recipients"""
        if not self.delivery_method:
            frappe.throw(_("Delivery method is required"))

        if self.delivery_method == "Email":
            if not self.email_recipients:
                frappe.throw(_("Email recipients are required for email delivery"))

            # Validate email addresses
            import re

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            emails = [email.strip() for email in self.email_recipients.split(",")]

            for email in emails:
                if not re.match(email_pattern, email):
                    frappe.throw(_("Invalid email address: {0}").format(email))

    def validate_date_ranges(self):
        """Validate start and end dates"""
        if self.schedule_start_date and self.schedule_end_date:
            if getdate(self.schedule_start_date) > getdate(self.schedule_end_date):
                frappe.throw(_("Start date cannot be after end date"))

        if self.schedule_start_date and getdate(self.schedule_start_date) < getdate():
            if self.status == "Active":
                frappe.msgprint(
                    _("Start date is in the past. Schedule will begin from next occurrence.")
                )

    def set_next_execution_time(self):
        """Calculate next execution time based on frequency"""
        if self.status != "Active":
            self.next_execution_time = None
            return

        now = now_datetime()
        start_date = get_datetime(self.schedule_start_date) if self.schedule_start_date else now

        # Use start date if in future, otherwise use current time
        base_time = max(start_date, now)

        # Set time of day
        if self.execution_time:
            time_parts = self.execution_time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

            base_time = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

        next_execution = self.calculate_next_execution(base_time)

        # Ensure next execution is not in the past
        if next_execution <= now:
            next_execution = self.calculate_next_execution(next_execution)

        self.next_execution_time = next_execution

    def calculate_next_execution(self, from_time: datetime) -> datetime:
        """Calculate next execution time based on frequency"""
        if self.frequency == "Daily":
            return from_time + timedelta(days=1)

        elif self.frequency == "Weekly":
            # Calculate next occurrence of specified day of week
            days_ahead = self.get_days_until_weekday(from_time, self.day_of_week)
            if days_ahead == 0:  # Today is the day, schedule for next week
                days_ahead = 7
            return from_time + timedelta(days=days_ahead)

        elif self.frequency == "Monthly":
            # Calculate next month with same day
            next_month = add_months(from_time, 1)
            try:
                return next_month.replace(day=cint(self.day_of_month))
            except ValueError:
                # Handle case where day doesn't exist in next month (e.g., Feb 30)
                return next_month.replace(day=28)

        elif self.frequency == "Yearly":
            return from_time.replace(year=from_time.year + 1)

        elif self.frequency == "Custom Cron":
            # Use croniter library if available
            try:
                from croniter import croniter

                cron = croniter(self.cron_expression, from_time)
                return cron.get_next(datetime)
            except ImportError:
                frappe.throw(_("croniter library is required for custom cron expressions"))

        return from_time + timedelta(days=1)  # Default fallback

    def get_days_until_weekday(self, from_date: datetime, target_weekday: str) -> int:
        """Calculate days until target weekday"""
        weekdays = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

        current_weekday = from_date.weekday()
        target_weekday_num = weekdays.get(target_weekday, 0)

        days_ahead = target_weekday_num - current_weekday
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        return days_ahead

    def before_save(self):
        """Actions before saving document"""
        if self.has_value_changed("status"):
            if self.status == "Active":
                self.setup_background_job()
            elif self.status in ["Inactive", "Paused"]:
                self.remove_background_job()

    def setup_background_job(self):
        """Setup background job for this schedule"""
        job_name = f"report_schedule_{self.name}"

        # Remove existing job if any
        self.remove_background_job()

        # Create new scheduler event
        if not frappe.db.exists("Scheduled Job Type", job_name):
            job_doc = frappe.new_doc("Scheduled Job Type")
            job_doc.method = "universal_workshop.reports_analytics.doctype.report_schedule.report_schedule.execute_scheduled_report"
            job_doc.frequency = "Cron"
            job_doc.cron_format = self.get_cron_expression()
            job_doc.insert()

    def remove_background_job(self):
        """Remove background job for this schedule"""
        job_name = f"report_schedule_{self.name}"
        if frappe.db.exists("Scheduled Job Type", job_name):
            frappe.delete_doc("Scheduled Job Type", job_name)

    def get_cron_expression(self) -> str:
        """Convert frequency to cron expression"""
        if self.frequency == "Custom Cron":
            return self.cron_expression

        # Parse execution time
        hour = 9  # Default hour
        minute = 0  # Default minute

        if self.execution_time:
            time_parts = self.execution_time.split(":")
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0

        if self.frequency == "Daily":
            return f"{minute} {hour} * * *"
        elif self.frequency == "Weekly":
            weekday_num = {
                "Monday": 1,
                "Tuesday": 2,
                "Wednesday": 3,
                "Thursday": 4,
                "Friday": 5,
                "Saturday": 6,
                "Sunday": 0,
            }.get(self.day_of_week, 1)
            return f"{minute} {hour} * * {weekday_num}"
        elif self.frequency == "Monthly":
            return f"{minute} {hour} {self.day_of_month or 1} * *"
        elif self.frequency == "Yearly":
            return f"{minute} {hour} 1 1 *"

        return f"{minute} {hour} * * *"  # Default daily

    def execute_report(self, manual=False) -> Dict[str, Any]:
        """Execute the scheduled report"""
        execution_record = None

        try:
            # Create execution record
            execution_record = self.create_execution_record(manual)
            execution_record.mark_as_running()

            # Check if schedule is still active and within date range
            if not manual and not self.is_execution_allowed():
                execution_record.mark_as_cancelled()
                return {"success": False, "message": "Execution not allowed at this time"}

            # Get report data
            report_data = self.generate_report_data()

            # Generate report file
            file_path, file_url, file_size = self.generate_report_file(report_data)

            # Mark execution as completed
            rows_generated = (
                len(report_data.get("data", [])) if isinstance(report_data, dict) else 0
            )
            execution_record.mark_as_completed(file_path, file_url, rows_generated, file_size)

            # Deliver report
            delivery_result = self.deliver_report(file_path, execution_record)

            # Update next execution time
            if not manual:
                self.update_next_execution_time()

            return {
                "success": True,
                "execution_id": execution_record.execution_id,
                "file_path": file_path,
                "delivery_result": delivery_result,
            }

        except Exception as e:
            error_message = str(e)
            error_traceback = traceback.format_exc()

            if execution_record:
                execution_record.mark_as_failed(error_message, error_traceback)

                # Retry logic
                if execution_record.retry_count < execution_record.max_retries:
                    frappe.enqueue(
                        "universal_workshop.reports_analytics.doctype.report_schedule.report_schedule.retry_execution",
                        queue="long",
                        timeout=300,
                        execution_name=execution_record.name,
                        delay=300,  # 5 minute delay before retry
                    )

            frappe.log_error(
                f"Report execution failed: {error_message}", "Report Schedule Execution"
            )

            return {
                "success": False,
                "error": error_message,
                "execution_id": execution_record.execution_id if execution_record else None,
            }

    def create_execution_record(self, manual=False) -> "ReportScheduleExecution":
        """Create execution record in child table"""
        # Import here to avoid circular imports
        from universal_workshop.reports_analytics.doctype.report_schedule_execution.report_schedule_execution import (
            ReportScheduleExecution,
        )

        execution = frappe.new_doc("Report Schedule Execution")
        execution.execution_time = now_datetime()
        execution.scheduled_time = self.next_execution_time if not manual else now_datetime()
        execution.report_name = self.report_name
        execution.report_format = self.report_format
        execution.delivery_method = self.delivery_method
        execution.recipients = self.email_recipients if self.delivery_method == "Email" else ""
        execution.max_retries = self.max_retry_attempts or 3

        # Apply filters
        if self.report_filters:
            execution.filters_applied = self.report_filters

        execution.insert()
        return execution

    def is_execution_allowed(self) -> bool:
        """Check if execution is allowed at current time"""
        if self.status != "Active":
            return False

        current_date = getdate()

        # Check date range
        if self.schedule_start_date and current_date < getdate(self.schedule_start_date):
            return False

        if self.schedule_end_date and current_date > getdate(self.schedule_end_date):
            self.status = "Expired"
            self.save()
            return False

        # Check execution conditions
        if self.execution_condition_script:
            try:
                # Execute condition script
                result = frappe.safe_eval(self.execution_condition_script, {"frappe": frappe})
                return bool(result)
            except Exception as e:
                frappe.log_error(f"Execution condition script failed: {e}", "Report Schedule")
                return True  # Default to allow execution if script fails

        return True

    def generate_report_data(self) -> Dict[str, Any]:
        """Generate report data using Frappe's report engine"""
        # Get report document
        report_doc = frappe.get_doc("Report", self.report_name)

        # Parse filters
        filters = {}
        if self.report_filters:
            try:
                filters = json.loads(self.report_filters)
            except json.JSONDecodeError:
                frappe.log_error(
                    f"Invalid report filters JSON: {self.report_filters}", "Report Schedule"
                )

        # Add dynamic filter processing
        if self.dynamic_filter_script:
            try:
                dynamic_filters = frappe.safe_eval(
                    self.dynamic_filter_script, {"frappe": frappe, "filters": filters}
                )
                filters.update(dynamic_filters or {})
            except Exception as e:
                frappe.log_error(f"Dynamic filter script failed: {e}", "Report Schedule")

        # Execute report
        if report_doc.report_type == "Report Builder":
            data = self.execute_report_builder(report_doc, filters)
        elif report_doc.report_type == "Query Report":
            data = self.execute_query_report(report_doc, filters)
        elif report_doc.report_type == "Script Report":
            data = self.execute_script_report(report_doc, filters)
        else:
            frappe.throw(_("Unsupported report type: {0}").format(report_doc.report_type))

        return data

    def execute_report_builder(self, report_doc, filters) -> Dict[str, Any]:
        """Execute Report Builder type report"""
        from frappe.desk.query_report import run_report_builder

        return run_report_builder(report_doc.name, filters)

    def execute_query_report(self, report_doc, filters) -> Dict[str, Any]:
        """Execute Query Report type report"""
        from frappe.desk.query_report import run

        return run(report_doc.name, filters)

    def execute_script_report(self, report_doc, filters) -> Dict[str, Any]:
        """Execute Script Report type report"""
        from frappe.desk.query_report import run

        return run(report_doc.name, filters)

    def generate_report_file(self, report_data) -> tuple:
        """Generate report file in specified format"""
        # Create reports directory if not exists
        reports_dir = os.path.join(get_files_path(), "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        # Generate filename
        timestamp = now_datetime().strftime("%Y%m%d_%H%M%S")
        if self.custom_filename_template:
            filename = self.process_filename_template(timestamp)
        else:
            filename = f"{self.report_name}_{timestamp}.{self.report_format.lower()}"

        file_path = os.path.join(reports_dir, filename)

        # Generate file based on format
        if self.report_format == "PDF":
            file_path = self.generate_pdf_report(report_data, file_path)
        elif self.report_format == "XLSX":
            file_path = self.generate_excel_report(report_data, file_path)
        elif self.report_format == "CSV":
            file_path = self.generate_csv_report(report_data, file_path)
        elif self.report_format == "HTML":
            file_path = self.generate_html_report(report_data, file_path)
        else:
            frappe.throw(_("Unsupported report format: {0}").format(self.report_format))

        # Get file size
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        file_size_str = f"{file_size_mb:.2f} MB"

        # Generate download URL
        file_url = f"/api/method/universal_workshop.reports_analytics.doctype.report_schedule_execution.report_schedule_execution.download_report_file?execution_name="

        return file_path, file_url, file_size_str

    def process_filename_template(self, timestamp) -> str:
        """Process custom filename template with placeholders"""
        template = self.custom_filename_template

        # Replace placeholders
        replacements = {
            "{report_name}": self.report_name,
            "{timestamp}": timestamp,
            "{date}": getdate().strftime("%Y%m%d"),
            "{time}": now_datetime().strftime("%H%M%S"),
            "{format}": self.report_format.lower(),
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))

        # Ensure file extension
        if not template.endswith(f".{self.report_format.lower()}"):
            template += f".{self.report_format.lower()}"

        return template

    def generate_pdf_report(self, report_data, file_path) -> str:
        """Generate PDF report"""
        from frappe.utils.pdf import get_pdf

        # Generate HTML content
        html_content = self.generate_html_content(report_data)

        # Convert to PDF
        pdf_content = get_pdf(html_content)

        with open(file_path, "wb") as f:
            f.write(pdf_content)

        return file_path

    def generate_excel_report(self, report_data, file_path) -> str:
        """Generate Excel report"""
        import openpyxl
        from openpyxl.styles import Font, Alignment

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.report_name[:31]  # Excel sheet name limit

        # Add header
        if report_data.get("columns"):
            headers = [col.get("label", col.get("fieldname", "")) for col in report_data["columns"]]
            ws.append(headers)

            # Style header row
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")

        # Add data
        if report_data.get("data"):
            for row in report_data["data"]:
                if isinstance(row, dict):
                    # Convert dict to list based on column order
                    row_data = [
                        row.get(col.get("fieldname"), "") for col in report_data.get("columns", [])
                    ]
                else:
                    row_data = row
                ws.append(row_data)

        wb.save(file_path)
        return file_path

    def generate_csv_report(self, report_data, file_path) -> str:
        """Generate CSV report"""
        import csv

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            if report_data.get("columns"):
                headers = [
                    col.get("label", col.get("fieldname", "")) for col in report_data["columns"]
                ]
                writer.writerow(headers)

            # Write data
            if report_data.get("data"):
                for row in report_data["data"]:
                    if isinstance(row, dict):
                        # Convert dict to list based on column order
                        row_data = [
                            row.get(col.get("fieldname"), "")
                            for col in report_data.get("columns", [])
                        ]
                    else:
                        row_data = row
                    writer.writerow(row_data)

        return file_path

    def generate_html_report(self, report_data, file_path) -> str:
        """Generate HTML report"""
        html_content = self.generate_html_content(report_data)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return file_path

    def generate_html_content(self, report_data) -> str:
        """Generate HTML content for report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{self.report_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.report_name}</h1>
                <p>Generated on: {format_datetime(now_datetime())}</p>
            </div>
            <table>
        """

        # Add headers
        if report_data.get("columns"):
            html += "<thead><tr>"
            for col in report_data["columns"]:
                html += f"<th>{col.get('label', col.get('fieldname', ''))}</th>"
            html += "</tr></thead>"

        # Add data
        if report_data.get("data"):
            html += "<tbody>"
            for row in report_data["data"]:
                html += "<tr>"
                if isinstance(row, dict):
                    for col in report_data.get("columns", []):
                        value = row.get(col.get("fieldname"), "")
                        html += f"<td>{frappe.utils.escape_html(str(value))}</td>"
                else:
                    for value in row:
                        html += f"<td>{frappe.utils.escape_html(str(value))}</td>"
                html += "</tr>"
            html += "</tbody>"

        html += """
            </table>
        </body>
        </html>
        """

        return html

    def deliver_report(self, file_path, execution_record) -> Dict[str, Any]:
        """Deliver report via configured method"""
        if self.delivery_method == "Email":
            return self.deliver_via_email(file_path, execution_record)
        elif self.delivery_method == "Notification":
            return self.deliver_via_notification(file_path, execution_record)
        elif self.delivery_method == "Download":
            return {"success": True, "message": "Report available for download"}
        # Add other delivery methods as needed

        return {"success": False, "message": "Unsupported delivery method"}

    def deliver_via_email(self, file_path, execution_record) -> Dict[str, Any]:
        """Deliver report via email"""
        try:
            # Prepare email content
            subject = self.email_subject or f"Scheduled Report: {self.report_name}"
            message = (
                self.email_body or f"Please find attached the scheduled report: {self.report_name}"
            )

            # Process subject and message templates
            subject = self.process_email_template(subject)
            message = self.process_email_template(message)

            # Send email
            frappe.sendmail(
                recipients=self.email_recipients.split(","),
                subject=subject,
                message=message,
                attachments=[
                    {"fname": os.path.basename(file_path), "fcontent": open(file_path, "rb").read()}
                ],
                sender=self.sender_email_account,
                now=True,
            )

            # Update execution record
            email_count = len(self.email_recipients.split(","))
            execution_record.update_delivery_status("Sent", email_count)

            return {"success": True, "message": f"Email sent to {email_count} recipients"}

        except Exception as e:
            execution_record.update_delivery_status("Failed")
            frappe.log_error(f"Email delivery failed: {e}", "Report Schedule Email")
            return {"success": False, "message": str(e)}

    def deliver_via_notification(self, file_path, execution_record) -> Dict[str, Any]:
        """Deliver report via system notification"""
        try:
            # Create notification for each recipient
            recipients = self.email_recipients.split(",") if self.email_recipients else [self.owner]

            for recipient in recipients:
                frappe.get_doc(
                    {
                        "doctype": "Notification Log",
                        "for_user": recipient.strip(),
                        "type": "Alert",
                        "document_type": "Report Schedule",
                        "document_name": self.name,
                        "subject": f"Scheduled Report Ready: {self.report_name}",
                        "email_content": f"Your scheduled report '{self.report_name}' has been generated and is ready for download.",
                    }
                ).insert(ignore_permissions=True)

            execution_record.update_delivery_status("Delivered", notification_sent=True)
            return {"success": True, "message": "Notifications sent"}

        except Exception as e:
            execution_record.update_delivery_status("Failed")
            frappe.log_error(f"Notification delivery failed: {e}", "Report Schedule Notification")
            return {"success": False, "message": str(e)}

    def process_email_template(self, template: str) -> str:
        """Process email template with placeholders"""
        replacements = {
            "{report_name}": self.report_name,
            "{schedule_name}": self.schedule_name,
            "{date}": format_datetime(now_datetime(), "dd-MM-yyyy"),
            "{time}": format_datetime(now_datetime(), "HH:mm"),
            "{workshop_name}": frappe.defaults.get_user_default("Company") or "Workshop",
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, str(value))

        return template

    def update_next_execution_time(self):
        """Update next execution time after successful execution"""
        if self.frequency != "One Time":
            next_time = self.calculate_next_execution(get_datetime(self.next_execution_time))

            # Check if next execution is within end date
            if self.schedule_end_date and getdate(next_time) > getdate(self.schedule_end_date):
                self.status = "Expired"
                self.next_execution_time = None
            else:
                self.next_execution_time = next_time

            self.save()


# Background job functions
@frappe.whitelist()
def execute_scheduled_report(report_schedule_name):
    """Execute a specific scheduled report (called by background job)"""
    try:
        schedule = frappe.get_doc("Report Schedule", report_schedule_name)
        return schedule.execute_report()
    except Exception as e:
        frappe.log_error(
            f"Scheduled report execution failed: {e}", "Report Schedule Background Job"
        )
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def retry_execution(execution_name):
    """Retry a failed execution"""
    try:
        execution = frappe.get_doc("Report Schedule Execution", execution_name)
        schedule = frappe.get_doc("Report Schedule", execution.parent)

        execution.retry_execution()
        return schedule.execute_report()

    except Exception as e:
        frappe.log_error(f"Retry execution failed: {e}", "Report Schedule Retry")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def execute_all_pending_schedules():
    """Execute all pending scheduled reports (to be run via scheduler)"""
    current_time = now_datetime()

    # Get all active schedules that are due for execution
    pending_schedules = frappe.get_list(
        "Report Schedule",
        filters={"status": "Active", "next_execution_time": ["<=", current_time]},
        fields=["name", "report_name"],
    )

    results = []
    for schedule_info in pending_schedules:
        try:
            result = execute_scheduled_report(schedule_info["name"])
            results.append(
                {
                    "schedule": schedule_info["name"],
                    "report": schedule_info["report_name"],
                    "result": result,
                }
            )
        except Exception as e:
            frappe.log_error(
                f"Failed to execute schedule {schedule_info['name']}: {e}", "Report Scheduler"
            )
            results.append(
                {
                    "schedule": schedule_info["name"],
                    "report": schedule_info["report_name"],
                    "result": {"success": False, "error": str(e)},
                }
            )

    return results


@frappe.whitelist()
def test_report_execution(report_schedule_name):
    """Test report execution manually"""
    schedule = frappe.get_doc("Report Schedule", report_schedule_name)
    return schedule.execute_report(manual=True)
