# Week 16: Health Monitoring System with Prometheus/Grafana Integration
# Universal Workshop ERP - Real-time Health Monitoring

import time
import json
import psutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
import frappe
from frappe import _
from frappe.utils import now, flt
import redis
import requests

class HealthMonitoringSystem:
    """
    Comprehensive health monitoring system with Prometheus/Grafana integration
    Monitors system health, application performance, and Arabic-specific metrics
    """
    
    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.health_history = []
        self.alert_thresholds = self._load_alert_thresholds()
        self.prometheus_metrics = {}
        
    def _get_redis_client(self):
        """Get Redis client for health data storage"""
        try:
            return redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
        except Exception as e:
            frappe.log_error(f"Redis connection failed: {e}")
            return None
    
    def _load_alert_thresholds(self) -> Dict:
        """Load alert thresholds configuration"""
        return {
            'cpu_critical': 90,
            'cpu_warning': 80,
            'memory_critical': 95,
            'memory_warning': 85,
            'disk_critical': 95,
            'disk_warning': 90,
            'response_time_critical': 10000,  # 10 seconds
            'response_time_warning': 5000,   # 5 seconds
            'error_rate_critical': 10,       # 10%
            'error_rate_warning': 5,         # 5%
            'database_connections_critical': 95,
            'database_connections_warning': 80
        }
    
    def collect_comprehensive_health_metrics(self) -> Dict:
        """Collect comprehensive health metrics for monitoring"""
        timestamp = datetime.now()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'system': self._collect_system_metrics(),
            'database': self._collect_database_metrics(),
            'redis': self._collect_redis_metrics(),
            'application': self._collect_application_metrics(),
            'arabic_specific': self._collect_arabic_metrics(),
            'network': self._collect_network_metrics(),
            'security': self._collect_security_metrics(),
            'performance': self._collect_performance_metrics()
        }
        
        # Calculate overall health score
        metrics['overall_health'] = self._calculate_overall_health_score(metrics)
        
        # Store metrics in Redis for real-time access
        if self.redis_client:
            self.redis_client.setex(
                f"health:metrics:{int(timestamp.timestamp())}", 
                3600, 
                json.dumps(metrics)
            )
        
        # Store in health history
        self.health_history.append(metrics)
        if len(self.health_history) > 1000:  # Keep last 1000 entries
            self.health_history = self.health_history[-1000:]
        
        # Generate alerts if needed
        alerts = self._check_alert_conditions(metrics)
        if alerts:
            self._send_health_alerts(alerts)
        
        return metrics
    
    def _collect_system_metrics(self) -> Dict:
        """Collect system-level metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': memory.total / (1024**3),
                'memory_used_gb': memory.used / (1024**3),
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
                'disk_used_gb': disk.used / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3),
                'load_average_1m': load_avg[0],
                'load_average_5m': load_avg[1],
                'load_average_15m': load_avg[2],
                'uptime_seconds': time.time() - psutil.boot_time()
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting system metrics: {e}")
            return {'error': str(e)}
    
    def _collect_database_metrics(self) -> Dict:
        """Collect database performance metrics"""
        try:
            # Database connection and performance
            connection_start = time.time()
            frappe.db.sql("SELECT 1")
            connection_time = (time.time() - connection_start) * 1000
            
            # Get database statistics
            db_stats = frappe.db.sql("""
                SELECT 
                    (SELECT COUNT(*) FROM information_schema.processlist WHERE Command != 'Sleep') as active_connections,
                    (SELECT COUNT(*) FROM information_schema.processlist) as total_connections,
                    (SELECT COUNT(*) FROM information_schema.processlist WHERE Time > 5) as slow_queries,
                    (SELECT VARIABLE_VALUE FROM information_schema.global_status WHERE VARIABLE_NAME = 'Threads_connected') as threads_connected,
                    (SELECT VARIABLE_VALUE FROM information_schema.global_status WHERE VARIABLE_NAME = 'Questions') as total_queries,
                    (SELECT VARIABLE_VALUE FROM information_schema.global_status WHERE VARIABLE_NAME = 'Uptime') as db_uptime
            """, as_dict=True)[0]
            
            # Calculate database size
            db_size = frappe.db.sql("""
                SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)[0][0] or 0
            
            return {
                'connection_time_ms': connection_time,
                'active_connections': int(db_stats.get('active_connections', 0)),
                'total_connections': int(db_stats.get('total_connections', 0)),
                'slow_queries': int(db_stats.get('slow_queries', 0)),
                'threads_connected': int(db_stats.get('threads_connected', 0)),
                'total_queries': int(db_stats.get('total_queries', 0)),
                'database_size_mb': db_size,
                'uptime_seconds': int(db_stats.get('db_uptime', 0))
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting database metrics: {e}")
            return {'error': str(e)}
    
    def _collect_redis_metrics(self) -> Dict:
        """Collect Redis performance metrics"""
        try:
            if not self.redis_client:
                return {'error': 'Redis not available'}
            
            info = self.redis_client.info()
            
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_mb': info.get('used_memory', 0) / (1024**2),
                'used_memory_peak_mb': info.get('used_memory_peak', 0) / (1024**2),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting Redis metrics: {e}")
            return {'error': str(e)}
    
    def _collect_application_metrics(self) -> Dict:
        """Collect application-specific metrics"""
        try:
            # Get active user sessions
            active_sessions = frappe.db.count('Sessions', 
                                            filters={'lastupdate': ['>', datetime.now() - timedelta(minutes=30)]})
            
            # Get recent error count
            recent_errors = frappe.db.count('Error Log',
                                          filters={'creation': ['>', datetime.now() - timedelta(hours=1)]})
            
            # Get job queue status
            queued_jobs = frappe.db.count('RQ Job', filters={'status': 'queued'})
            failed_jobs = frappe.db.count('RQ Job', filters={'status': 'failed'})
            
            # Get email queue status
            email_queue = frappe.db.count('Email Queue', filters={'status': 'Not Sent'})
            
            return {
                'active_user_sessions': active_sessions,
                'recent_errors_1h': recent_errors,
                'queued_background_jobs': queued_jobs,
                'failed_background_jobs': failed_jobs,
                'pending_emails': email_queue,
                'frappe_version': frappe.__version__
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting application metrics: {e}")
            return {'error': str(e)}
    
    def _collect_arabic_metrics(self) -> Dict:
        """Collect Arabic language and RTL specific metrics"""
        try:
            # Count Arabic content in key DocTypes
            arabic_customers = frappe.db.count('Customer', 
                                             filters={'customer_name_ar': ['!=', '']})
            
            arabic_workshops = frappe.db.count('Workshop Profile',
                                             filters={'workshop_name_ar': ['!=', '']})
            
            # Check Arabic language usage
            arabic_sessions = frappe.db.count('Sessions',
                                            filters={'data': ['like', '%"lang": "ar"%']})
            
            # Test Arabic text rendering capability
            arabic_render_test = self._test_arabic_rendering()
            
            return {
                'arabic_customers_count': arabic_customers,
                'arabic_workshops_count': arabic_workshops,
                'arabic_user_sessions': arabic_sessions,
                'arabic_rendering_working': arabic_render_test,
                'rtl_support_enabled': True,  # Assuming RTL is always enabled
                'arabic_fonts_available': self._check_arabic_fonts()
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting Arabic metrics: {e}")
            return {'error': str(e)}
    
    def _collect_network_metrics(self) -> Dict:
        """Collect network performance metrics"""
        try:
            network_io = psutil.net_io_counters()
            connections = psutil.net_connections()
            
            # Count connection states
            connection_states = {}
            for conn in connections:
                state = conn.status
                connection_states[state] = connection_states.get(state, 0) + 1
            
            return {
                'bytes_sent': network_io.bytes_sent,
                'bytes_received': network_io.bytes_recv,
                'packets_sent': network_io.packets_sent,
                'packets_received': network_io.packets_recv,
                'total_connections': len(connections),
                'established_connections': connection_states.get('ESTABLISHED', 0),
                'listening_connections': connection_states.get('LISTEN', 0)
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting network metrics: {e}")
            return {'error': str(e)}
    
    def _collect_security_metrics(self) -> Dict:
        """Collect security-related metrics"""
        try:
            # Failed login attempts in last hour
            failed_logins = frappe.db.count('Activity Log',
                                          filters={
                                              'subject': 'Login Failed',
                                              'creation': ['>', datetime.now() - timedelta(hours=1)]
                                          })
            
            # Recent security alerts
            security_alerts = frappe.db.count('Security Monitor',
                                            filters={
                                                'risk_level': ['in', ['High', 'Critical']],
                                                'creation': ['>', datetime.now() - timedelta(hours=24)]
                                            })
            
            return {
                'failed_logins_1h': failed_logins,
                'security_alerts_24h': security_alerts,
                'ssl_certificate_valid': self._check_ssl_certificate(),
                'firewall_active': self._check_firewall_status()
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting security metrics: {e}")
            return {'error': str(e)}
    
    def _collect_performance_metrics(self) -> Dict:
        """Collect performance-related metrics"""
        try:
            # Recent load test results
            recent_load_tests = frappe.get_list('Load Test Result',
                                              filters={'test_timestamp': ['>', datetime.now() - timedelta(days=7)]},
                                              fields=['overall_grade', 'pass_percentage', 'avg_response_time'],
                                              limit=10)
            
            if recent_load_tests:
                avg_pass_rate = sum(t.get('pass_percentage', 0) for t in recent_load_tests) / len(recent_load_tests)
                avg_response_time = sum(t.get('avg_response_time', 0) for t in recent_load_tests) / len(recent_load_tests)
            else:
                avg_pass_rate = 0
                avg_response_time = 0
            
            return {
                'recent_load_tests_count': len(recent_load_tests),
                'avg_load_test_pass_rate': avg_pass_rate,
                'avg_load_test_response_time': avg_response_time,
                'cache_hit_ratio': self._calculate_cache_hit_ratio()
            }
            
        except Exception as e:
            frappe.log_error(f"Error collecting performance metrics: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_health_score(self, metrics: Dict) -> Dict:
        """Calculate overall system health score (0-100)"""
        score = 100
        issues = []
        
        # System health impact
        system = metrics.get('system', {})
        if system.get('cpu_percent', 0) > self.alert_thresholds['cpu_critical']:
            score -= 20
            issues.append('Critical CPU usage')
        elif system.get('cpu_percent', 0) > self.alert_thresholds['cpu_warning']:
            score -= 10
            issues.append('High CPU usage')
        
        if system.get('memory_percent', 0) > self.alert_thresholds['memory_critical']:
            score -= 25
            issues.append('Critical memory usage')
        elif system.get('memory_percent', 0) > self.alert_thresholds['memory_warning']:
            score -= 15
            issues.append('High memory usage')
        
        if system.get('disk_percent', 0) > self.alert_thresholds['disk_critical']:
            score -= 20
            issues.append('Critical disk usage')
        elif system.get('disk_percent', 0) > self.alert_thresholds['disk_warning']:
            score -= 10
            issues.append('High disk usage')
        
        # Database health impact
        database = metrics.get('database', {})
        if database.get('slow_queries', 0) > 10:
            score -= 15
            issues.append('High number of slow queries')
        
        # Application health impact
        application = metrics.get('application', {})
        if application.get('recent_errors_1h', 0) > 50:
            score -= 20
            issues.append('High error rate')
        elif application.get('recent_errors_1h', 0) > 20:
            score -= 10
            issues.append('Moderate error rate')
        
        # Security health impact
        security = metrics.get('security', {})
        if security.get('failed_logins_1h', 0) > 20:
            score -= 15
            issues.append('High failed login attempts')
        
        if security.get('security_alerts_24h', 0) > 5:
            score -= 10
            issues.append('Multiple security alerts')
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Determine health status
        if score >= 90:
            status = 'excellent'
        elif score >= 75:
            status = 'good'
        elif score >= 60:
            status = 'fair'
        elif score >= 40:
            status = 'poor'
        else:
            status = 'critical'
        
        return {
            'score': score,
            'status': status,
            'issues': issues,
            'last_updated': datetime.now().isoformat()
        }
    
    def _check_alert_conditions(self, metrics: Dict) -> List[Dict]:
        """Check for alert conditions based on metrics"""
        alerts = []
        
        system = metrics.get('system', {})
        database = metrics.get('database', {})
        application = metrics.get('application', {})
        
        # CPU alerts
        if system.get('cpu_percent', 0) > self.alert_thresholds['cpu_critical']:
            alerts.append({
                'severity': 'critical',
                'type': 'system',
                'message': f"Critical CPU usage: {system.get('cpu_percent', 0):.1f}%",
                'metric': 'cpu_percent',
                'value': system.get('cpu_percent', 0),
                'threshold': self.alert_thresholds['cpu_critical']
            })
        elif system.get('cpu_percent', 0) > self.alert_thresholds['cpu_warning']:
            alerts.append({
                'severity': 'warning',
                'type': 'system',
                'message': f"High CPU usage: {system.get('cpu_percent', 0):.1f}%",
                'metric': 'cpu_percent',
                'value': system.get('cpu_percent', 0),
                'threshold': self.alert_thresholds['cpu_warning']
            })
        
        # Memory alerts
        if system.get('memory_percent', 0) > self.alert_thresholds['memory_critical']:
            alerts.append({
                'severity': 'critical',
                'type': 'system',
                'message': f"Critical memory usage: {system.get('memory_percent', 0):.1f}%",
                'metric': 'memory_percent',
                'value': system.get('memory_percent', 0),
                'threshold': self.alert_thresholds['memory_critical']
            })
        
        # Database alerts
        if database.get('slow_queries', 0) > 10:
            alerts.append({
                'severity': 'warning',
                'type': 'database',
                'message': f"High number of slow queries: {database.get('slow_queries', 0)}",
                'metric': 'slow_queries',
                'value': database.get('slow_queries', 0),
                'threshold': 10
            })
        
        # Application alerts
        if application.get('recent_errors_1h', 0) > 50:
            alerts.append({
                'severity': 'critical',
                'type': 'application',
                'message': f"High error rate: {application.get('recent_errors_1h', 0)} errors in last hour",
                'metric': 'recent_errors_1h',
                'value': application.get('recent_errors_1h', 0),
                'threshold': 50
            })
        
        return alerts
    
    def generate_prometheus_metrics(self) -> str:
        """Generate Prometheus-compatible metrics output"""
        metrics = self.collect_comprehensive_health_metrics()
        prometheus_output = []
        
        # System metrics
        system = metrics.get('system', {})
        prometheus_output.extend([
            f"# HELP universal_workshop_cpu_percent CPU usage percentage",
            f"# TYPE universal_workshop_cpu_percent gauge",
            f"universal_workshop_cpu_percent {system.get('cpu_percent', 0)}",
            "",
            f"# HELP universal_workshop_memory_percent Memory usage percentage", 
            f"# TYPE universal_workshop_memory_percent gauge",
            f"universal_workshop_memory_percent {system.get('memory_percent', 0)}",
            "",
            f"# HELP universal_workshop_disk_percent Disk usage percentage",
            f"# TYPE universal_workshop_disk_percent gauge", 
            f"universal_workshop_disk_percent {system.get('disk_percent', 0)}",
            ""
        ])
        
        # Database metrics
        database = metrics.get('database', {})
        prometheus_output.extend([
            f"# HELP universal_workshop_db_connections Active database connections",
            f"# TYPE universal_workshop_db_connections gauge",
            f"universal_workshop_db_connections {database.get('active_connections', 0)}",
            "",
            f"# HELP universal_workshop_db_slow_queries Slow database queries",
            f"# TYPE universal_workshop_db_slow_queries gauge",
            f"universal_workshop_db_slow_queries {database.get('slow_queries', 0)}",
            ""
        ])
        
        # Overall health score
        health = metrics.get('overall_health', {})
        prometheus_output.extend([
            f"# HELP universal_workshop_health_score Overall system health score (0-100)",
            f"# TYPE universal_workshop_health_score gauge",
            f"universal_workshop_health_score {health.get('score', 0)}",
            ""
        ])
        
        return "\n".join(prometheus_output)

# WhiteListed API methods for health monitoring

@frappe.whitelist()
def get_health_metrics():
    """Get current health metrics"""
    monitor = HealthMonitoringSystem()
    return monitor.collect_comprehensive_health_metrics()

@frappe.whitelist()
def get_prometheus_metrics():
    """Get Prometheus-compatible metrics"""
    monitor = HealthMonitoringSystem()
    return monitor.generate_prometheus_metrics()

@frappe.whitelist()
def get_health_alerts():
    """Get current health alerts"""
    monitor = HealthMonitoringSystem()
    metrics = monitor.collect_comprehensive_health_metrics()
    return monitor._check_alert_conditions(metrics)

@frappe.whitelist()
def get_health_history(hours=24):
    """Get health metrics history"""
    monitor = HealthMonitoringSystem()
    
    # Filter history by time range
    cutoff_time = datetime.now() - timedelta(hours=hours)
    filtered_history = [
        m for m in monitor.health_history 
        if datetime.fromisoformat(m['timestamp']) > cutoff_time
    ]
    
    return filtered_history[-100:]  # Return last 100 entries 