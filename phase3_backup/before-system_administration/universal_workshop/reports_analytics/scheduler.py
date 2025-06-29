# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, cint
import traceback


def execute_pending_reports():
    """
    Execute all pending scheduled reports
    This function is called by Frappe's scheduler (every 15 minutes)
    """
    try:
        frappe.log("Starting execution of pending scheduled reports")

        # Get all active schedules that are due for execution
        current_time = now_datetime()

        pending_schedules = frappe.get_list(
            "Report Schedule",
            filters={"status": "Active", "next_execution_time": ["<=", current_time]},
            fields=["name", "report_name", "schedule_name", "next_execution_time"],
        )

        executed_count = 0
        failed_count = 0

        for schedule_info in pending_schedules:
            try:
                frappe.log(f"Executing scheduled report: {schedule_info['name']}")

                # Get the full schedule document
                schedule = frappe.get_doc("Report Schedule", schedule_info["name"])

                # Execute the report
                result = schedule.execute_report()

                if result.get("success"):
                    executed_count += 1
                    frappe.log(f"Successfully executed report schedule: {schedule_info['name']}")
                else:
                    failed_count += 1
                    frappe.log_error(
                        f"Failed to execute report schedule: {schedule_info['name']} - {result.get('error', 'Unknown error')}",
                        "Report Scheduler",
                    )

            except Exception as e:
                failed_count += 1
                error_msg = f"Exception while executing schedule {schedule_info['name']}: {str(e)}"
                frappe.log_error(error_msg, "Report Scheduler")
                frappe.log(error_msg)

        # Log summary
        if executed_count > 0 or failed_count > 0:
            summary = f"Report execution summary: {executed_count} succeeded, {failed_count} failed"
            frappe.log(summary)

    except Exception as e:
        error_msg = f"Critical error in execute_pending_reports: {str(e)}\n{traceback.format_exc()}"
        frappe.log_error(error_msg, "Report Scheduler Critical")


def cleanup_expired_report_files():
    """
    Clean up expired report files
    This function is called by Frappe's scheduler (daily)
    """
    try:
        frappe.log("Starting cleanup of expired report files")

        # Get all executions with expired files
        expired_executions = frappe.get_list(
            "Report Schedule Execution",
            filters={"file_expiry_date": ["<", getdate()], "file_deleted": 0},
            fields=["name", "file_path", "file_expiry_date"],
        )

        cleaned_count = 0
        error_count = 0

        for execution_info in expired_executions:
            try:
                execution = frappe.get_doc("Report Schedule Execution", execution_info["name"])
                execution.delete_file()
                cleaned_count += 1

            except Exception as e:
                error_count += 1
                frappe.log_error(
                    f"Failed to delete expired file for execution {execution_info['name']}: {str(e)}",
                    "Report File Cleanup",
                )

        # Log summary
        summary = f"File cleanup summary: {cleaned_count} files deleted, {error_count} errors"
        frappe.log(summary)

        return {"cleaned": cleaned_count, "errors": error_count}

    except Exception as e:
        error_msg = (
            f"Critical error in cleanup_expired_report_files: {str(e)}\n{traceback.format_exc()}"
        )
        frappe.log_error(error_msg, "Report Cleanup Critical")
        return {"cleaned": 0, "errors": 1}


def update_schedule_statistics():
    """
    Update statistics for all report schedules
    This function is called by Frappe's scheduler (hourly)
    """
    try:
        frappe.log("Starting update of report schedule statistics")

        # Get all report schedules
        schedules = frappe.get_list(
            "Report Schedule", filters={"status": ["in", ["Active", "Paused"]]}, fields=["name"]
        )

        updated_count = 0

        for schedule_info in schedules:
            try:
                schedule = frappe.get_doc("Report Schedule", schedule_info["name"])

                # Calculate statistics from execution history
                executions = frappe.get_list(
                    "Report Schedule Execution",
                    filters={"parent": schedule.name},
                    fields=["execution_status", "execution_time"],
                    order_by="execution_time desc",
                    limit=100,
                )

                total_executions = len(executions)
                successful_executions = len(
                    [e for e in executions if e.execution_status == "Completed"]
                )

                # Calculate success rate
                if total_executions > 0:
                    success_rate = (successful_executions / total_executions) * 100
                else:
                    success_rate = 0

                # Update schedule statistics
                schedule.success_rate = success_rate
                schedule.error_count = total_executions - successful_executions

                # Get last execution log
                if executions:
                    last_execution = frappe.get_doc(
                        "Report Schedule Execution", executions[0]["name"]
                    )
                    schedule.last_execution_log = f"Status: {last_execution.execution_status}, Time: {last_execution.execution_time}"

                schedule.save()
                updated_count += 1

            except Exception as e:
                frappe.log_error(
                    f"Failed to update statistics for schedule {schedule_info['name']}: {str(e)}",
                    "Schedule Statistics Update",
                )

        frappe.log(f"Updated statistics for {updated_count} report schedules")

    except Exception as e:
        error_msg = (
            f"Critical error in update_schedule_statistics: {str(e)}\n{traceback.format_exc()}"
        )
        frappe.log_error(error_msg, "Schedule Statistics Critical")


def check_and_expire_schedules():
    """
    Check for schedules that have reached their end date and mark them as expired
    This function is called by Frappe's scheduler (daily)
    """
    try:
        frappe.log("Checking for expired report schedules")

        current_date = getdate()

        # Get active schedules that have passed their end date
        expired_schedules = frappe.get_list(
            "Report Schedule",
            filters={"status": "Active", "schedule_end_date": ["<", current_date]},
            fields=["name", "schedule_name", "schedule_end_date"],
        )

        expired_count = 0

        for schedule_info in expired_schedules:
            try:
                schedule = frappe.get_doc("Report Schedule", schedule_info["name"])
                schedule.status = "Expired"
                schedule.next_execution_time = None
                schedule.save()

                expired_count += 1
                frappe.log(f"Marked schedule as expired: {schedule_info['name']}")

            except Exception as e:
                frappe.log_error(
                    f"Failed to expire schedule {schedule_info['name']}: {str(e)}",
                    "Schedule Expiration",
                )

        if expired_count > 0:
            frappe.log(f"Marked {expired_count} schedules as expired")

    except Exception as e:
        error_msg = (
            f"Critical error in check_and_expire_schedules: {str(e)}\n{traceback.format_exc()}"
        )
        frappe.log_error(error_msg, "Schedule Expiration Critical")


def retry_failed_executions():
    """
    Retry failed executions that are within retry limits
    This function is called by Frappe's scheduler (every 30 minutes)
    """
    try:
        frappe.log("Checking for failed executions to retry")

        # Get failed executions that can be retried
        failed_executions = frappe.db.sql(
            """
            SELECT name, retry_count, max_retries, parent
            FROM `tabReport Schedule Execution`
            WHERE execution_status = 'Failed'
            AND retry_count < max_retries
            AND TIMESTAMPDIFF(MINUTE, modified, NOW()) >= 30
            LIMIT 50
        """,
            as_dict=True,
        )

        retried_count = 0

        for execution_info in failed_executions:
            try:
                execution = frappe.get_doc("Report Schedule Execution", execution_info["name"])
                schedule = frappe.get_doc("Report Schedule", execution_info["parent"])

                # Retry the execution
                execution.retry_execution()
                result = schedule.execute_report()

                if result.get("success"):
                    retried_count += 1
                    frappe.log(f"Successfully retried execution: {execution_info['name']}")
                else:
                    frappe.log(f"Retry failed for execution: {execution_info['name']}")

            except Exception as e:
                frappe.log_error(
                    f"Failed to retry execution {execution_info['name']}: {str(e)}",
                    "Execution Retry",
                )

        if retried_count > 0:
            frappe.log(f"Successfully retried {retried_count} failed executions")

    except Exception as e:
        error_msg = f"Critical error in retry_failed_executions: {str(e)}\n{traceback.format_exc()}"
        frappe.log_error(error_msg, "Execution Retry Critical")


def generate_scheduler_summary():
    """
    Generate daily summary of scheduler activities
    This function is called by Frappe's scheduler (daily at 23:00)
    """
    try:
        frappe.log("Generating daily scheduler summary")

        current_date = getdate()

        # Get execution statistics for today
        today_executions = frappe.db.sql(
            """
            SELECT 
                execution_status,
                COUNT(*) as count,
                AVG(CASE WHEN execution_duration IS NOT NULL THEN execution_duration ELSE 0 END) as avg_duration
            FROM `tabReport Schedule Execution`
            WHERE DATE(execution_time) = %s
            GROUP BY execution_status
        """,
            [current_date],
            as_dict=True,
        )

        # Get active schedules count
        active_schedules = frappe.db.count("Report Schedule", {"status": "Active"})

        # Get error log count for today
        error_count = frappe.db.sql(
            """
            SELECT COUNT(*) as count
            FROM `tabError Log`
            WHERE DATE(creation) = %s
            AND method_name LIKE '%report%schedule%'
        """,
            [current_date],
            as_dict=True,
        )[0]["count"]

        # Create summary
        summary = {
            "date": current_date,
            "active_schedules": active_schedules,
            "executions": today_executions,
            "error_count": error_count,
        }

        # Log summary
        summary_text = f"""
        Daily Report Scheduler Summary for {current_date}:
        - Active Schedules: {active_schedules}
        - Executions: {len(today_executions)} different statuses
        - Errors: {error_count}
        """

        for exec_stat in today_executions:
            summary_text += f"\n  - {exec_stat['execution_status']}: {exec_stat['count']} (avg duration: {exec_stat['avg_duration']:.2f}s)"

        frappe.log(summary_text)

        # Send summary email to administrators if there are significant errors
        if error_count > 10:  # Threshold for notification
            send_error_notification(summary_text, error_count)

        return summary

    except Exception as e:
        error_msg = (
            f"Critical error in generate_scheduler_summary: {str(e)}\n{traceback.format_exc()}"
        )
        frappe.log_error(error_msg, "Scheduler Summary Critical")


def send_error_notification(summary_text, error_count):
    """Send email notification for high error count"""
    try:
        # Get system managers
        system_managers = frappe.get_list(
            "Has Role", filters={"role": "System Manager"}, fields=["parent"], distinct=True
        )

        if not system_managers:
            return

        recipients = [manager["parent"] for manager in system_managers]

        frappe.sendmail(
            recipients=recipients,
            subject=f"Report Scheduler Alert: {error_count} errors detected",
            message=f"""
            <h3>Report Scheduler Alert</h3>
            <p>The report scheduler has detected {error_count} errors today.</p>
            <pre>{summary_text}</pre>
            <p>Please check the Error Log for more details.</p>
            """,
            now=True,
        )

    except Exception as e:
        frappe.log_error(f"Failed to send error notification: {str(e)}", "Scheduler Notification")


# Maintenance functions
def archive_old_execution_records():
    """
    Archive execution records older than 6 months
    This function is called by Frappe's scheduler (weekly)
    """
    try:
        frappe.log("Starting archival of old execution records")

        # Get executions older than 6 months
        cutoff_date = add_days(getdate(), -180)  # 6 months

        old_executions = frappe.get_list(
            "Report Schedule Execution",
            filters={"execution_time": ["<", cutoff_date]},
            fields=["name"],
        )

        archived_count = 0

        # Instead of deleting, we could move to an archive table
        # For now, we'll just delete very old records
        for execution_info in old_executions:
            try:
                execution = frappe.get_doc("Report Schedule Execution", execution_info["name"])

                # Delete the file if it exists
                if execution.file_path and not execution.file_deleted:
                    execution.delete_file()

                # Delete the execution record
                frappe.delete_doc("Report Schedule Execution", execution_info["name"])
                archived_count += 1

            except Exception as e:
                frappe.log_error(
                    f"Failed to archive execution {execution_info['name']}: {str(e)}",
                    "Execution Archive",
                )

        frappe.log(f"Archived {archived_count} old execution records")

    except Exception as e:
        error_msg = (
            f"Critical error in archive_old_execution_records: {str(e)}\n{traceback.format_exc()}"
        )
        frappe.log_error(error_msg, "Execution Archive Critical")


def optimize_report_performance():
    """
    Analyze and optimize report performance
    This function is called by Frappe's scheduler (weekly)
    """
    try:
        frappe.log("Starting report performance optimization analysis")

        # Get reports with long execution times
        slow_reports = frappe.db.sql(
            """
            SELECT 
                parent,
                report_name,
                AVG(execution_duration) as avg_duration,
                COUNT(*) as execution_count
            FROM `tabReport Schedule Execution`
            WHERE execution_status = 'Completed'
            AND execution_duration > 300  -- 5 minutes
            AND execution_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY parent, report_name
            HAVING execution_count >= 5
            ORDER BY avg_duration DESC
            LIMIT 10
        """,
            as_dict=True,
        )

        if slow_reports:
            # Log performance issues
            performance_report = "Slow Report Performance Analysis:\n"
            for report in slow_reports:
                performance_report += f"- {report['report_name']}: avg {report['avg_duration']:.2f}s ({report['execution_count']} executions)\n"

            frappe.log(performance_report)

            # You could implement additional optimization logic here
            # such as suggesting index creation, query optimization, etc.

    except Exception as e:
        error_msg = f"Error in optimize_report_performance: {str(e)}\n{traceback.format_exc()}"
        frappe.log_error(error_msg, "Performance Optimization")
