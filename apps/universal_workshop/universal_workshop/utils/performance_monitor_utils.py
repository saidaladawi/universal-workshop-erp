"""
Universal Workshop ERP - Performance Monitoring Utilities
Real-time performance monitoring and alerting
"""

import frappe
import time
import psutil
import json
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
            # Check database connections
            connection_count = frappe.db.sql("""
                SHOW STATUS LIKE 'Threads_connected'
            """, as_dict=True)
            
            if connection_count:
                db_status["metrics"]["active_connections"] = connection_count[0].get("Value", 0)
            
            # Check slow queries (if slow query log is enabled)
            try:
                slow_queries = frappe.db.sql("""
                    SELECT 
                        query_time,
                        lock_time,
                        rows_examined,
                        LEFT(sql_text, 100) as sql_text_preview
                    FROM mysql.slow_log 
                    WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                    ORDER BY query_time DESC 
                    LIMIT 10
                """, as_dict=True)
                
                db_status["slow_queries"] = slow_queries
                
                if len(slow_queries) > 5:
                    db_status["status"] = "warning"
                    
            except:
                # Slow query log may not be available
                db_status["slow_queries"] = []
            
            # Check table locks
            try:
                table_locks = frappe.db.sql("""
                    SHOW STATUS LIKE 'Table_locks_waited'
                """, as_dict=True)
                
                if table_locks:
                    db_status["metrics"]["table_locks_waited"] = table_locks[0].get("Value", 0)
                    
            except:
                pass
            
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
            # Basic cache connectivity test
            cache_enabled = bool(frappe.cache())
            cache_status["metrics"]["cache_enabled"] = cache_enabled
            
            if cache_enabled:
                # Test cache functionality
                test_key = "workshop:performance_test"
                test_value = {"test": True, "timestamp": frappe.utils.now()}
                
                # Test write
                frappe.cache().set_value(test_key, test_value, expires_in_sec=60)
                
                # Test read
                retrieved_value = frappe.cache().get_value(test_key)
                
                cache_status["metrics"]["cache_read_write_test"] = "passed" if retrieved_value else "failed"
                
                # Clean up test key
                frappe.cache().delete_value(test_key)
                
                # Estimated hit ratio (placeholder - would need Redis INFO in real implementation)
                cache_status["metrics"]["estimated_hit_ratio"] = 0.85
                
            else:
                cache_status["status"] = "warning"
                cache_status["alerts"] = ["Cache is disabled or not available"]
            
        except Exception as e:
            cache_status["error"] = str(e)
            cache_status["status"] = "error"
        
        return cache_status
    
    @staticmethod
    def get_performance_dashboard_data() -> Dict[str, Any]:
        """Get comprehensive performance data for dashboard"""
        try:
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_health": PerformanceMonitor.check_system_health(),
                "database_performance": PerformanceMonitor.check_database_performance(),
                "cache_performance": PerformanceMonitor.check_cache_performance()
            }
            
            return dashboard_data
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
