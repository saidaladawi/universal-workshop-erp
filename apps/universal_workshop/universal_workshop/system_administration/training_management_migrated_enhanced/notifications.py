import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_days, add_months
from datetime import datetime, timedelta
import json


def send_overdue_training_reminders():
    """Daily task to send overdue training reminders"""
    try:
        # Get all overdue training records
        overdue_records = frappe.get_all(
            'Training Progress',
            filters={
                'next_review_date': ['<', nowdate()],
                'status': 'Completed'
            },
            fields=[
                'name', 'user', 'training_module', 'module_title',
                'next_review_date', 'competency_level'
            ]
        )

        # Group by user to send consolidated emails
        user_overdue = {}
        for record in overdue_records:
            if record.user not in user_overdue:
                user_overdue[record.user] = []
            user_overdue[record.user].append(record)

        # Send reminders
        for user, records in user_overdue.items():
            send_consolidated_overdue_reminder(user, records)

        frappe.logger().info(f"Sent overdue training reminders to {len(user_overdue)} users")

    except Exception as e:
        frappe.log_error(f"Failed to send overdue training reminders: {str(e)}")


def send_certificate_expiry_reminders():
    """Daily task to send certificate expiry reminders"""
    try:
        # Get certificates expiring in 30, 60, 90 days
        reminder_periods = [30, 60, 90]

        for days in reminder_periods:
            expiry_date = add_days(nowdate(), days)

            expiring_certs = frappe.get_all(
                'Training Certification',
                filters={
                    'valid_until': expiry_date,
                    'is_expired': 0
                },
                fields=[
                    'name', 'user', 'certificate_number', 'module_title',
                    'valid_until', 'competency_level'
                ]
            )

            for cert in expiring_certs:
                send_certificate_expiry_reminder(cert, days)

        frappe.logger().info(f"Processed certificate expiry reminders")

    except Exception as e:
        frappe.log_error(f"Failed to send certificate expiry reminders: {str(e)}")


def send_progress_summaries():
    """Weekly task to send progress summaries to users"""
    try:
        # Get all users with active training progress
        active_users = frappe.get_all(
            'Training Progress',
            filters={'status': ['in', ['In Progress', 'Not Started']]},
            fields=['user'],
            group_by='user'
        )

        for user_record in active_users:
            user = user_record.user
            send_weekly_progress_summary(user)

        frappe.logger().info(f"Sent weekly progress summaries to {len(active_users)} users")

    except Exception as e:
        frappe.log_error(f"Failed to send weekly progress summaries: {str(e)}")


def generate_training_reports():
    """Monthly task to generate training analytics reports"""
    try:
        # Generate system-wide training statistics
        stats = get_monthly_training_statistics()

        # Save monthly report
        save_monthly_training_report(stats)

        # Send management summary
        send_management_training_summary(stats)

        frappe.logger().info("Generated monthly training reports")

    except Exception as e:
        frappe.log_error(f"Failed to generate monthly training reports: {str(e)}")


def send_consolidated_overdue_reminder(user, overdue_records):
    """Send consolidated overdue reminder to user"""
    try:
        user_email = frappe.db.get_value("User", user, "email")
        if not user_email:
            return

        # Calculate days overdue for each record
        for record in overdue_records:
            record.days_overdue = (getdate() - getdate(record.next_review_date)).days

        # Create email content
        subject = _("Training Review Required - {0} Overdue Modules").format(len(overdue_records))

        modules_html = ""
        for record in overdue_records:
            urgency_class = "danger" if record.days_overdue > 30 else "warning"
            modules_html += f"""
                <tr>
                    <td>{record.module_title}</td>
                    <td><span class="badge badge-{urgency_class}">{record.days_overdue} days</span></td>
                    <td>{_(record.competency_level or 'Not Assessed')}</td>
                    <td>{record.next_review_date}</td>
                </tr>
            """

        email_content = f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">Training Reviews Required</h2>
            <p>You have {len(overdue_records)} training modules that require review:</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead style="background: #f8f9fa;">
                    <tr>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Module</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Days Overdue</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Current Level</th>
                        <th style="padding: 10px; border: 1px solid #dee2e6;">Review Due</th>
                    </tr>
                </thead>
                <tbody>
                    {modules_html}
                </tbody>
            </table>

            <p>Please complete these reviews to maintain your certification status.</p>
            <p><a href="/training-dashboard" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                Access Training Dashboard
            </a></p>
        </div>
        """

        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message=email_content,
            header=_("Training Review Required")
        )

    except Exception as e:
        frappe.log_error(f"Failed to send overdue reminder to {user}: {str(e)}")


def send_certificate_expiry_reminder(cert, days_until_expiry):
    """Send certificate expiry reminder"""
    try:
        user_email = frappe.db.get_value("User", cert.user, "email")
        if not user_email:
            return

        subject = _("Certificate Expiring Soon - {0}").format(cert.module_title)

        urgency_color = "#dc3545" if days_until_expiry <= 30 else "#ffc107"

        email_content = f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: {urgency_color};">Certificate Expiry Notice</h2>

            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <strong>⚠️ Your certificate expires in {days_until_expiry} days</strong>
            </div>

            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <strong>Certificate Details:</strong><br>
                <strong>Module:</strong> {cert.module_title}<br>
                <strong>Certificate Number:</strong> {cert.certificate_number}<br>
                <strong>Competency Level:</strong> {_(cert.competency_level)}<br>
                <strong>Expiry Date:</strong> {cert.valid_until}<br>
            </div>

            <p>To maintain your certification, please complete the required review training before the expiry date.</p>
            <p><a href="/training-dashboard" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                View Training Dashboard
            </a></p>
        </div>
        """

        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message=email_content,
            header=_("Certificate Expiry Notice")
        )

    except Exception as e:
        frappe.log_error(f"Failed to send expiry reminder for cert {cert.name}: {str(e)}")


def send_weekly_progress_summary(user):
    """Send weekly progress summary to user"""
    try:
        user_email = frappe.db.get_value("User", user, "email")
        if not user_email:
            return

        # Get user's progress data
        progress_records = frappe.get_all(
            'Training Progress',
            filters={'user': user},
            fields=[
                'name', 'training_module', 'module_title', 'status',
                'progress_percentage', 'competency_level', 'time_spent_minutes'
            ]
        )

        # Calculate weekly statistics
        total_modules = len(progress_records)
        completed_modules = len([r for r in progress_records if r.status == 'Completed'])
        in_progress_modules = len([r for r in progress_records if r.status == 'In Progress'])
        total_time = sum([r.time_spent_minutes or 0 for r in progress_records])

        subject = _("Weekly Training Progress Summary")

        # Create progress summary HTML
        progress_html = ""
        for record in progress_records[:5]:  # Show top 5
            status_color = "#28a745" if record.status == "Completed" else "#ffc107" if record.status == "In Progress" else "#6c757d"
            progress_html += f"""
                <tr>
                    <td>{record.module_title}</td>
                    <td><span style="color: {status_color};">{_(record.status)}</span></td>
                    <td>{record.progress_percentage or 0}%</td>
                    <td>{_(record.competency_level or 'Not Assessed')}</td>
                </tr>
            """

        email_content = f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #667eea;">Weekly Training Summary</h2>

            <div style="display: flex; gap: 15px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                    <h3 style="color: #667eea; margin: 0;">{total_modules}</h3>
                    <small>Total Modules</small>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                    <h3 style="color: #28a745; margin: 0;">{completed_modules}</h3>
                    <small>Completed</small>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                    <h3 style="color: #ffc107; margin: 0;">{in_progress_modules}</h3>
                    <small>In Progress</small>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                    <h3 style="color: #17a2b8; margin: 0;">{round(total_time/60, 1)}h</h3>
                    <small>Training Time</small>
                </div>
            </div>

            <h4>Recent Activity:</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <thead style="background: #f8f9fa;">
                    <tr>
                        <th style="padding: 8px; border: 1px solid #dee2e6;">Module</th>
                        <th style="padding: 8px; border: 1px solid #dee2e6;">Status</th>
                        <th style="padding: 8px; border: 1px solid #dee2e6;">Progress</th>
                        <th style="padding: 8px; border: 1px solid #dee2e6;">Level</th>
                    </tr>
                </thead>
                <tbody>
                    {progress_html}
                </tbody>
            </table>

            <p style="margin-top: 20px;">
                <a href="/training-dashboard" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Full Dashboard
                </a>
            </p>
        </div>
        """

        frappe.sendmail(
            recipients=[user_email],
            subject=subject,
            message=email_content,
            header=_("Training Progress Summary")
        )

    except Exception as e:
        frappe.log_error(f"Failed to send progress summary to {user}: {str(e)}")


def get_monthly_training_statistics():
    """Get comprehensive monthly training statistics"""
    try:
        # Get all training progress records
        all_progress = frappe.get_all(
            'Training Progress',
            fields=[
                'user', 'training_module', 'status', 'progress_percentage',
                'competency_level', 'time_spent_minutes', 'completed_on'
            ]
        )

        # Get all certifications
        all_certifications = frappe.get_all(
            'Training Certification',
            fields=['user', 'training_module', 'competency_level', 'issued_on']
        )

        # Calculate statistics
        stats = {
            'total_users': len(set([r.user for r in all_progress])),
            'total_modules': len(set([r.training_module for r in all_progress])),
            'total_progress_records': len(all_progress),
            'completed_modules': len([r for r in all_progress if r.status == 'Completed']),
            'in_progress_modules': len([r for r in all_progress if r.status == 'In Progress']),
            'total_certifications': len(all_certifications),
            'total_training_hours': sum([r.time_spent_minutes or 0 for r in all_progress]) / 60,
            'competency_distribution': {},
            'monthly_completions': len([r for r in all_progress if r.completed_on and getdate(r.completed_on).month == getdate().month]),
            'average_completion_rate': 0
        }

        # Calculate competency distribution
        for record in all_progress:
            level = record.competency_level or 'Not Assessed'
            stats['competency_distribution'][level] = stats['competency_distribution'].get(level, 0) + 1

        # Calculate average completion rate
        if stats['total_progress_records'] > 0:
            total_progress = sum([r.progress_percentage or 0 for r in all_progress])
            stats['average_completion_rate'] = round(total_progress / stats['total_progress_records'], 2)

        return stats

    except Exception as e:
        frappe.log_error(f"Failed to calculate training statistics: {str(e)}")
        return {}


def save_monthly_training_report(stats):
    """Save monthly training report"""
    try:
        report = frappe.new_doc("Training Report")
        report.report_type = "Monthly Summary"
        report.report_date = nowdate()
        report.statistics = json.dumps(stats)
        report.insert()

    except Exception as e:
        frappe.log_error(f"Failed to save monthly training report: {str(e)}")


def send_management_training_summary(stats):
    """Send training summary to management"""
    try:
        # Get users with Training Manager role
        managers = frappe.get_all(
            'Has Role',
            filters={'role': 'Training Manager'},
            fields=['parent']
        )

        if not managers:
            return

        manager_emails = []
        for manager in managers:
            email = frappe.db.get_value("User", manager.parent, "email")
            if email:
                manager_emails.append(email)

        if not manager_emails:
            return

        subject = _("Monthly Training Analytics Report")

        # Create statistics HTML
        competency_html = ""
        for level, count in stats.get('competency_distribution', {}).items():
            competency_html += f"<li>{_(level)}: {count} users</li>"

        email_content = f"""
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2 style="color: #667eea;">Monthly Training Analytics</h2>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="color: #667eea; margin: 0;">{stats.get('total_users', 0)}</h3>
                    <small>Active Users</small>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="color: #28a745; margin: 0;">{stats.get('completed_modules', 0)}</h3>
                    <small>Completed Modules</small>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="color: #17a2b8; margin: 0;">{stats.get('total_certifications', 0)}</h3>
                    <small>Certifications Issued</small>
                </div>
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center;">
                    <h3 style="color: #ffc107; margin: 0;">{round(stats.get('total_training_hours', 0), 1)}h</h3>
                    <small>Total Training Hours</small>
                </div>
            </div>

            <h4>Key Metrics:</h4>
            <ul>
                <li><strong>Average Completion Rate:</strong> {stats.get('average_completion_rate', 0)}%</li>
                <li><strong>Monthly Completions:</strong> {stats.get('monthly_completions', 0)} modules</li>
                <li><strong>Total Training Modules:</strong> {stats.get('total_modules', 0)}</li>
            </ul>

            <h4>Competency Distribution:</h4>
            <ul>{competency_html}</ul>

            <p style="margin-top: 20px;">
                <a href="/app/training-progress" style="background: #667eea; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    View Detailed Reports
                </a>
            </p>
        </div>
        """

        frappe.sendmail(
            recipients=manager_emails,
            subject=subject,
            message=email_content,
            header=_("Training Analytics Report")
        )

    except Exception as e:
        frappe.log_error(f"Failed to send management training summary: {str(e)}")


# Utility functions for milestone notifications
@frappe.whitelist()
def trigger_milestone_notification(training_progress_name, milestone):
    """Manually trigger milestone notification for testing"""
    try:
        doc = frappe.get_doc("Training Progress", training_progress_name)
        doc.send_milestone_notification(milestone)
        return {"status": "success", "message": _("Milestone notification sent")}
    except Exception as e:
        frappe.log_error(f"Failed to trigger milestone notification: {str(e)}")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def send_immediate_progress_update(user):
    """Send immediate progress update to user"""
    try:
        send_weekly_progress_summary(user)
        return {"status": "success", "message": _("Progress update sent")}
    except Exception as e:
        frappe.log_error(f"Failed to send progress update: {str(e)}")
        return {"status": "error", "message": str(e)}
