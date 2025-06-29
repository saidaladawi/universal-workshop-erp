# -*- coding: utf-8 -*-
# Universal Workshop ERP - Performance Monitor Scheduler
# Copyright (c) 2024, Eng. Saeed Al-Adawi

import json
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import now, cint, flt


def collect_all_monitor_metrics():
    """Scheduled function to collect metrics from all active performance monitors"""
    try:
        # Get all active performance monitors
        monitors = frappe.get_list(
            'Performance Monitor',
            filters={'monitoring_enabled': 1, 'status': 'Active'},
            fields=['name', 'monitor_name', 'monitoring_interval_seconds']
        )
        
        results = []
        for monitor_data in monitors:
            try:
                monitor = frappe.get_doc('Performance Monitor', monitor_data['name'])
                result = monitor.collect_all_metrics()
                results.append({
                    'monitor': monitor_data['name'],
                    'status': 'success',
                    'result': result
                })
                
                # Log successful collection
                frappe.logger().info(f"Metrics collected for monitor: {monitor_data['monitor_name']}")
                
            except Exception as e:
                results.append({
                    'monitor': monitor_data['name'],
                    'status': 'error',
                    'error': str(e)
                })
                frappe.log_error(f"Failed to collect metrics for monitor {monitor_data['name']}: {str(e)}")
        
        return results
        
    except Exception as e:
        frappe.log_error(f"Performance monitor scheduler failed: {str(e)}")
        return []


def cleanup_old_performance_data():
    """Clean up old performance monitoring data based on retention settings"""
    try:
        # Get retention settings from Universal Workshop Settings
        retention_days = frappe.db.get_single_value(
            'Universal Workshop Settings', 
            'performance_data_retention_days'
        ) or 30
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Delete old performance monitor records
        old_monitors = frappe.get_list(
            'Performance Monitor',
            filters={'last_check_time': ['<', cutoff_date]},
            fields=['name']
        )
        
        deleted_count = 0
        for monitor in old_monitors:
            try:
                frappe.delete_doc('Performance Monitor', monitor['name'])
                deleted_count += 1
            except Exception as e:
                frappe.log_error(f"Failed to delete old monitor {monitor['name']}: {str(e)}")
        
        frappe.logger().info(f"Cleaned up {deleted_count} old performance monitor records")
        return deleted_count
        
    except Exception as e:
        frappe.log_error(f"Performance data cleanup failed: {str(e)}")
        return 0


def send_performance_alerts():
    """Send email alerts for critical performance issues"""
    try:
        # Get monitors with active alerts
        alert_monitors = frappe.get_list(
            'Performance Monitor',
            filters={
                'alert_enabled': 1,
                'alert_status': ['in', ['Warning', 'Critical']]
            },
            fields=['name', 'monitor_name', 'alert_severity', 'alert_message', 'alert_recipients', 'server_name']
        )
        
        alerts_sent = 0
        for monitor_data in alert_monitors:
            try:
                monitor = frappe.get_doc('Performance Monitor', monitor_data['name'])
                
                # Check cooldown period
                if monitor.alert_cooldown_minutes:
                    last_alert_time = getattr(monitor, 'last_alert_sent', None)
                    if last_alert_time:
                        cooldown_end = last_alert_time + timedelta(minutes=monitor.alert_cooldown_minutes)
                        if datetime.now() < cooldown_end:
                            continue  # Skip this alert due to cooldown
                
                # Send alert email
                if monitor.alert_recipients:
                    send_alert_email(monitor)
                    monitor.last_alert_sent = now()
                    monitor.save()
                    alerts_sent += 1
                    
            except Exception as e:
                frappe.log_error(f"Failed to send alert for monitor {monitor_data['name']}: {str(e)}")
        
        frappe.logger().info(f"Sent {alerts_sent} performance alerts")
        return alerts_sent
        
    except Exception as e:
        frappe.log_error(f"Performance alert sending failed: {str(e)}")
        return 0


def send_alert_email(monitor):
    """Send email alert for performance monitor"""
    try:
        subject = f"Performance Alert - {monitor.monitor_name} ({monitor.alert_severity})"
        
        # Build email content
        content = f"""
        <h3>Performance Alert: {monitor.monitor_name}</h3>
        <p><strong>Server:</strong> {monitor.server_name}</p>
        <p><strong>Severity:</strong> {monitor.alert_severity}</p>
        <p><strong>Time:</strong> {monitor.last_check_time}</p>
        
        <h4>Alert Details:</h4>
        <p>{monitor.alert_message}</p>
        
        <h4>Current Metrics:</h4>
        <ul>
            <li><strong>CPU Usage:</strong> {monitor.cpu_usage_percent}%</li>
            <li><strong>Memory Usage:</strong> {monitor.memory_usage_percent}%</li>
            <li><strong>Disk Usage:</strong> {monitor.disk_usage_percent}%</li>
        </ul>
        
        <p>Please check the system and take appropriate action.</p>
        """
        
        # Add Arabic content if available
        if monitor.alert_message_ar:
            content += f"""
            <hr>
            <div dir="rtl">
                <h4>تفاصيل التنبيه:</h4>
                <p>{monitor.alert_message_ar}</p>
            </div>
            """
        
        # Send email to recipients
        recipients = [email.strip() for email in monitor.alert_recipients.split(',')]
        
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            content=content,
            header=['Performance Alert', 'red']
        )
        
        frappe.logger().info(f"Alert email sent for monitor: {monitor.monitor_name}")
        
    except Exception as e:
        frappe.log_error(f"Failed to send alert email for monitor {monitor.name}: {str(e)}")


@frappe.whitelist()
def get_performance_summary():
    """Get performance summary for all monitors"""
    try:
        monitors = frappe.get_list(
            'Performance Monitor',
            filters={'status': 'Active'},
            fields=[
                'name', 'monitor_name', 'server_name', 'monitor_type',
                'cpu_usage_percent', 'memory_usage_percent', 'disk_usage_percent',
                'alert_status', 'alert_severity', 'last_check_time'
            ]
        )
        
        summary = {
            'total_monitors': len(monitors),
            'critical_alerts': len([m for m in monitors if m.get('alert_severity') == 'Critical']),
            'warning_alerts': len([m for m in monitors if m.get('alert_severity') == 'Warning']),
            'healthy_monitors': len([m for m in monitors if m.get('alert_status') == 'No Alert']),
            'monitors': monitors
        }
        
        return summary
        
    except Exception as e:
        frappe.log_error(f"Failed to get performance summary: {str(e)}")
        return {'error': str(e)}


def setup_performance_monitoring_cron():
    """Setup cron jobs for performance monitoring"""
    try:
        instructions = """
        To enable automatic performance monitoring, add these cron jobs to your system:
        
        1. Edit crontab: crontab -e
        
        2. Add these lines:
        
        # Collect performance metrics every 5 minutes
        */5 * * * * cd /path/to/frappe-bench && bench --site universal.local execute universal_workshop.workshop_management.performance_monitor_scheduler.collect_all_monitor_metrics
        
        # Send performance alerts every 10 minutes
        */10 * * * * cd /path/to/frappe-bench && bench --site universal.local execute universal_workshop.workshop_management.performance_monitor_scheduler.send_performance_alerts
        
        # Clean up old performance data daily at 2 AM
        0 2 * * * cd /path/to/frappe-bench && bench --site universal.local execute universal_workshop.workshop_management.performance_monitor_scheduler.cleanup_old_performance_data
        
        3. Save and exit the crontab editor
        
        4. Verify cron jobs: crontab -l
        """
        
        return instructions
        
    except Exception as e:
        frappe.log_error(f"Failed to setup performance monitoring cron: {str(e)}")
        return f"Error: {str(e)}"
