"""
Universal Workshop ERP - Performance Monitoring Utilities
Real-time performance monitoring and alerting
"""

import frappe
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any

class PerformanceMonitor:
    """Performance monitoring and alerting system"""
    
    @staticmethod
    def check_system_health() -> Dict[str, Any]:
        """Check overall system health"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "metrics": {},
            "alerts": []
        }
        
        try:
            # System metrics
            health_status["metrics"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "active_connections": len(psutil.net_connections())
            }
            
            # Check for alerts
            if health_status["metrics"]["cpu_percent"] > 80:
                health_status["alerts"].append("High CPU usage detected")
                health_status["status"] = "warning"
            
            if health_status["metrics"]["memory_percent"] > 85:
                health_status["alerts"].append("High memory usage detected")
                health_status["status"] = "warning"
            
            if health_status["metrics"]["disk_usage"] > 90:
                health_status["alerts"].append("High disk usage detected")
                health_status["status"] = "critical"
            
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    @staticmethod
    def check_database_performance() -> Dict[str, Any]:
        """Check database performance metrics"""
        db_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "metrics": {},
            "slow_queries": []
        }
        
        try:
            # Check slow queries
            slow_queries = frappe.db.sql("""
                SELECT 
                    query_time,
                    lock_time,
                    rows_examined,
                    sql_text
                FROM mysql.slow_log 
                WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY query_time DESC 
                LIMIT 10
            """, as_dict=True)
            
            db_status["slow_queries"] = slow_queries
            
            if len(slow_queries) > 5:
                db_status["status"] = "warning"
            
        except Exception as e:
            db_status["error"] = str(e)
        
        return db_status
    
    @staticmethod
    def check_cache_performance() -> Dict[str, Any]:
        """Check Redis cache performance"""
        cache_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "metrics": {}
        }
        
        try:
            # Redis info (simplified)
            cache_status["metrics"] = {
                "cache_enabled": bool(frappe.cache()),
                "estimated_hit_ratio": 0.85  # Placeholder - would need Redis INFO
            }
            
        except Exception as e:
            cache_status["error"] = str(e)
        
        return cache_status
    
    @staticmethod
    def log_performance_metrics():
        """Log performance metrics for analysis"""
        try:
            metrics = {
                "system_health": PerformanceMonitor.check_system_health(),
                "database_performance": PerformanceMonitor.check_database_performance(),
                "cache_performance": PerformanceMonitor.check_cache_performance()
            }
            
            # Log to file for analysis
            frappe.log_error(json.dumps(metrics, indent=2), "Performance Metrics")
            
        except Exception as e:
            frappe.log_error(f"Performance monitoring error: {str(e)}", "Performance Monitor")
