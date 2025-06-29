# -*- coding: utf-8 -*-
# Universal Workshop ERP - Performance Monitoring API
# Copyright (c) 2024, Eng. Saeed Al-Adawi

import json
import socket
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import flt, cint, now

try:
    import psutil
except ImportError:
    psutil = None


@frappe.whitelist()
def get_system_metrics():
    """Get current system metrics"""
    try:
        if not psutil:
            return {"error": "psutil library not installed"}

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)

        # Memory metrics
        memory = psutil.virtual_memory()

        # Disk metrics
        disk_usage = psutil.disk_usage("/")

        # Network metrics
        network = psutil.net_io_counters()

        return {
            "cpu": {
                "usage_percent": flt(cpu_percent, 2),
                "core_count": cpu_count,
                "load_average_1min": flt(load_avg[0], 2),
                "load_average_5min": flt(load_avg[1], 2),
                "load_average_15min": flt(load_avg[2], 2),
            },
            "memory": {
                "total_gb": flt(memory.total / (1024**3), 2),
                "used_gb": flt(memory.used / (1024**3), 2),
                "free_gb": flt(memory.free / (1024**3), 2),
                "usage_percent": flt(memory.percent, 2),
                "available_gb": flt(memory.available / (1024**3), 2),
            },
            "disk": {
                "total_gb": flt(disk_usage.total / (1024**3), 2),
                "used_gb": flt(disk_usage.used / (1024**3), 2),
                "free_gb": flt(disk_usage.free / (1024**3), 2),
                "usage_percent": flt((disk_usage.used / disk_usage.total) * 100, 2),
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
            "timestamp": now(),
            "server_name": socket.gethostname(),
        }

    except Exception as e:
        frappe.log_error(f"Failed to get system metrics: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_database_metrics():
    """Get database performance metrics"""
    try:
        # Database size
        db_size_query = """
            SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
        """
        db_size = frappe.db.sql(db_size_query, as_list=True)[0][0] or 0

        # Connection count
        connection_query = "SHOW STATUS LIKE 'Threads_connected'"
        connections = frappe.db.sql(connection_query, as_list=True)
        connection_count = int(connections[0][1]) if connections else 0

        # Query statistics
        queries_query = "SHOW STATUS LIKE 'Questions'"
        queries = frappe.db.sql(queries_query, as_list=True)
        total_queries = int(queries[0][1]) if queries else 0

        # Slow queries
        slow_queries_query = "SHOW STATUS LIKE 'Slow_queries'"
        slow_queries = frappe.db.sql(slow_queries_query, as_list=True)
        slow_query_count = int(slow_queries[0][1]) if slow_queries else 0

        return {
            "database_size_mb": flt(db_size, 2),
            "active_connections": connection_count,
            "total_queries": total_queries,
            "slow_queries": slow_query_count,
            "timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Failed to get database metrics: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_application_metrics():
    """Get application performance metrics"""
    try:
        # Get active user count
        active_users = frappe.db.count("User", {"enabled": 1})

        # Get background job count (handle missing DocType)
        bg_jobs = 0
        try:
            if frappe.db.exists("DocType", "RQ Job"):
                bg_jobs = frappe.db.count("RQ Job", {"status": ["in", ["queued", "started"]]})
        except:
            pass

        # Get error count (last 24 hours)
        error_count = 0
        try:
            yesterday = datetime.now() - timedelta(days=1)
            if frappe.db.exists("DocType", "Error Log"):
                error_count = frappe.db.count(
                    "Error Log", {"creation": [">", yesterday.strftime("%Y-%m-%d %H:%M:%S")]}
                )
        except:
            pass

        # Get cache hit ratio (if Redis is available)
        cache_hit_ratio = 0
        try:
            import redis

            redis_client = redis.Redis.from_url(frappe.conf.redis_cache)
            info = redis_client.info()
            if "keyspace_hits" in info and "keyspace_misses" in info:
                hits = info["keyspace_hits"]
                misses = info["keyspace_misses"]
                if hits + misses > 0:
                    cache_hit_ratio = flt((hits / (hits + misses)) * 100, 2)
        except:
            pass

        return {
            "active_users": active_users,
            "background_jobs": bg_jobs,
            "error_count_24h": error_count,
            "cache_hit_ratio": cache_hit_ratio,
            "timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Failed to get application metrics: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_comprehensive_metrics():
    """Get all metrics in one call"""
    try:
        return {
            "system": get_system_metrics(),
            "database": get_database_metrics(),
            "application": get_application_metrics(),
            "timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Failed to get comprehensive metrics: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def create_performance_alert(monitor_name, severity, message, message_ar=None):
    """Create a performance alert"""
    try:
        alert = frappe.new_doc("Performance Alert")
        alert.monitor_name = monitor_name
        alert.severity = severity
        alert.message = message
        alert.message_ar = message_ar or message
        alert.created_on = now()
        alert.status = "Active"
        alert.insert()

        return {"success": True, "alert_id": alert.name}

    except Exception as e:
        frappe.log_error(f"Failed to create performance alert: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_performance_history(monitor_name=None, hours=24):
    """Get performance monitoring history"""
    try:
        filters = {}
        if monitor_name:
            filters["monitor_name"] = monitor_name

        # Get data from the last N hours
        since_time = datetime.now() - timedelta(hours=cint(hours))
        filters["last_check_time"] = [">", since_time.strftime("%Y-%m-%d %H:%M:%S")]

        monitors = frappe.get_list(
            "Performance Monitor",
            filters=filters,
            fields=[
                "name",
                "monitor_name",
                "last_check_time",
                "cpu_usage_percent",
                "memory_usage_percent",
                "disk_usage_percent",
                "alert_status",
                "alert_severity",
            ],
            order_by="last_check_time desc",
        )

        return {"history": monitors, "total_records": len(monitors), "time_range_hours": hours}

    except Exception as e:
        frappe.log_error(f"Failed to get performance history: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def test_performance_monitoring():
    """Test performance monitoring functionality"""
    try:
        # Test system metrics collection
        system_metrics = get_system_metrics()
        if "error" in system_metrics:
            return {"success": False, "error": "System metrics failed", "details": system_metrics}

        # Test database metrics collection
        db_metrics = get_database_metrics()
        if "error" in db_metrics:
            return {"success": False, "error": "Database metrics failed", "details": db_metrics}

        # Test application metrics collection
        app_metrics = get_application_metrics()
        if "error" in app_metrics:
            return {"success": False, "error": "Application metrics failed", "details": app_metrics}

        return {
            "success": True,
            "message": "Performance monitoring test completed successfully",
            "test_results": {
                "system_metrics": system_metrics,
                "database_metrics": db_metrics,
                "application_metrics": app_metrics,
            },
        }

    except Exception as e:
        frappe.log_error(f"Performance monitoring test failed: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_test_performance_monitor():
    """Create a test Performance Monitor document"""
    try:
        monitor = frappe.new_doc("Performance Monitor")
        monitor.monitor_name = "System Performance Test"
        monitor.monitor_name_ar = "اختبار أداء النظام"
        monitor.monitor_type = "Real-time"
        monitor.monitoring_enabled = 1
        monitor.alert_enabled = 1
        monitor.cpu_threshold_warning = 70
        monitor.cpu_threshold_critical = 90
        monitor.memory_threshold_warning = 75
        monitor.memory_threshold_critical = 90
        monitor.disk_threshold_warning = 80
        monitor.disk_threshold_critical = 95
        monitor.insert()

        # Collect metrics
        result = monitor.collect_all_metrics()

        return {
            "success": True,
            "monitor_id": monitor.name,
            "monitor_name": monitor.monitor_name,
            "metrics_result": result,
        }

    except Exception as e:
        frappe.log_error(f"Failed to create test monitor: {str(e)}")
        return {"success": False, "error": str(e)}
