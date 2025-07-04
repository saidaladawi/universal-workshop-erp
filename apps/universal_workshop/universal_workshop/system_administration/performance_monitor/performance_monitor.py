# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import json
import socket
import time
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, now, format_datetime

try:
    import psutil
except ImportError:
    psutil = None


class PerformanceMonitor(Document):
    # pylint: disable=no-member
    
    def validate(self):
        """Validate performance monitor configuration"""
        self.validate_thresholds()
        self.validate_monitor_name()
        
    def before_save(self):
        """Set default values and collect initial metrics"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_on:
            self.created_on = now()
        if not self.server_name:
            self.server_name = socket.gethostname()
            
    def validate_thresholds(self):
        """Validate warning and critical thresholds"""
        threshold_pairs = [
            (self.cpu_threshold_warning, self.cpu_threshold_critical, "CPU"),
            (self.memory_threshold_warning, self.memory_threshold_critical, "Memory"),
            (self.disk_threshold_warning, self.disk_threshold_critical, "Disk")
        ]
        
        for warning, critical, metric_type in threshold_pairs:
            if warning and critical and warning >= critical:
                frappe.throw(_("{0} warning threshold must be less than critical threshold").format(metric_type))
                
    def validate_monitor_name(self):
        """Validate monitor names"""
        if not self.monitor_name:
            frappe.throw(_("Monitor name is required"))
        if not self.monitor_name_ar:
            frappe.throw(_("Arabic monitor name is required"))
            
    @frappe.whitelist()
    def collect_all_metrics(self):
        """Collect all system metrics and update the document"""
        try:
            if not psutil:
                frappe.throw(_("psutil library is not installed. Cannot collect system metrics."))
                
            # Collect all metrics
            cpu_metrics = self.get_cpu_metrics()
            memory_metrics = self.get_memory_metrics()
            disk_metrics = self.get_disk_metrics()
            
            # Update document fields
            self.update_fields(cpu_metrics)
            self.update_fields(memory_metrics)
            self.update_fields(disk_metrics)
            
            # Update last check time
            self.last_check_time = now()
            
            # Check for alerts
            self.check_all_alerts()
            
            # Save the document
            self.save()
            
            return {
                'status': 'success',
                'message': _('System metrics collected successfully'),
                'timestamp': self.last_check_time
            }
            
        except Exception as e:
            frappe.log_error(f"Failed to collect metrics: {str(e)}")
            frappe.throw(_("Failed to collect system metrics: {0}").format(str(e)))
            
    def get_cpu_metrics(self):
        """Get CPU performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
                
            return {
                'cpu_usage_percent': flt(cpu_percent, 2),
                'cpu_core_count': cpu_count,
                'cpu_load_average_1min': flt(load_avg[0], 2)
            }
        except Exception as e:
            frappe.log_error(f"Failed to get CPU metrics: {str(e)}")
            return {}
            
    def get_memory_metrics(self):
        """Get memory performance metrics"""
        try:
            memory = psutil.virtual_memory()
            
            return {
                'memory_total_gb': flt(memory.total / (1024**3), 2),
                'memory_used_gb': flt(memory.used / (1024**3), 2),
                'memory_usage_percent': flt(memory.percent, 2)
            }
        except Exception as e:
            frappe.log_error(f"Failed to get memory metrics: {str(e)}")
            return {}
            
    def get_disk_metrics(self):
        """Get disk performance metrics"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            return {
                'disk_total_gb': flt(disk_usage.total / (1024**3), 2),
                'disk_used_gb': flt(disk_usage.used / (1024**3), 2),
                'disk_usage_percent': flt((disk_usage.used / disk_usage.total) * 100, 2)
            }
        except Exception as e:
            frappe.log_error(f"Failed to get disk metrics: {str(e)}")
            return {}
            
    def update_fields(self, metrics):
        """Update document fields with metrics"""
        for field, value in metrics.items():
            if hasattr(self, field):
                setattr(self, field, value)
                
    def check_all_alerts(self):
        """Check all metrics against thresholds"""
        alerts = []
        
        # Check CPU alerts
        if self.cpu_alert_enabled and self.cpu_usage_percent:
            if self.cpu_usage_percent >= self.cpu_threshold_critical:
                alerts.append({
                    'severity': 'Critical',
                    'message': f"CPU usage critically high: {self.cpu_usage_percent}%",
                    'message_ar': f"استخدام المعالج عالي جداً: {self.cpu_usage_percent}%"
                })
            elif self.cpu_usage_percent >= self.cpu_threshold_warning:
                alerts.append({
                    'severity': 'Warning',
                    'message': f"CPU usage above warning: {self.cpu_usage_percent}%",
                    'message_ar': f"استخدام المعالج تجاوز التحذير: {self.cpu_usage_percent}%"
                })
                
        # Check Memory alerts
        if self.memory_alert_enabled and self.memory_usage_percent:
            if self.memory_usage_percent >= self.memory_threshold_critical:
                alerts.append({
                    'severity': 'Critical',
                    'message': f"Memory usage critically high: {self.memory_usage_percent}%",
                    'message_ar': f"استخدام الذاكرة عالي جداً: {self.memory_usage_percent}%"
                })
            elif self.memory_usage_percent >= self.memory_threshold_warning:
                alerts.append({
                    'severity': 'Warning',
                    'message': f"Memory usage above warning: {self.memory_usage_percent}%",
                    'message_ar': f"استخدام الذاكرة تجاوز التحذير: {self.memory_usage_percent}%"
                })
                
        # Update alert status
        if alerts:
            self.set_alert_status(alerts)
        else:
            self.clear_alert_status()
            
    def set_alert_status(self, alerts):
        """Set alert status based on detected alerts"""
        highest_severity = 'Warning'
        
        for alert in alerts:
            if alert['severity'] == 'Critical':
                highest_severity = 'Critical'
                break
                
        self.alert_status = highest_severity
        self.alert_severity = highest_severity
        
        # Combine alert messages
        en_messages = [alert['message'] for alert in alerts]
        ar_messages = [alert['message_ar'] for alert in alerts]
        
        self.alert_message = "\n".join(en_messages)
        self.alert_message_ar = "\n".join(ar_messages)
        
    def clear_alert_status(self):
        """Clear alert status when no alerts are active"""
        self.alert_status = 'No Alert'
        self.alert_message = "All metrics are within normal thresholds"
        self.alert_message_ar = "جميع المقاييس ضمن الحدود الطبيعية"


@frappe.whitelist()
def get_system_metrics():
    """Get current system metrics without saving to database"""
    try:
        if not psutil:
            return {'error': 'psutil library not installed'}
            
        monitor = PerformanceMonitor({})
        
        return {
            'cpu': monitor.get_cpu_metrics(),
            'memory': monitor.get_memory_metrics(),
            'disk': monitor.get_disk_metrics(),
            'timestamp': now()
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to get system metrics: {str(e)}")
        return {'error': str(e)}
