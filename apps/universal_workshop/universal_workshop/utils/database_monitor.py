"""
Database Performance Monitoring System
Advanced database monitoring for Universal Workshop ERP with real-time metrics
"""

import time
import psutil
import frappe
from frappe import _
from frappe.utils import now_datetime, flt, cint
from typing import Dict, List, Any, Optional, Tuple
import threading
import re

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class DatabaseMonitor:
    """Comprehensive Database Performance Monitoring for Universal Workshop"""

    def __init__(self):
        self.redis_client = frappe.cache() if REDIS_AVAILABLE else None
        self.slow_query_threshold = 2.0  # seconds
        self.connection_timeout_threshold = 5.0  # seconds

        # Performance thresholds
        self.thresholds = {
            "slow_query": 2.0,
            "connection_timeout": 5.0,
            "high_connections": 80,  # percentage of max_connections
            "lock_timeout": 10.0,
            "temp_table_size": 100,  # MB
            "query_cache_hit_rate": 95,  # percentage
        }

        # Arabic metric names
        self.arabic_metrics = {
            "slow_queries": "الاستعلامات البطيئة",
            "active_connections": "الاتصالات النشطة",
            "query_cache_hit_rate": "معدل إصابة ذاكرة التخزين المؤقت",
            "table_locks": "أقفال الجداول",
            "innodb_buffer_pool": "مجموعة المخزن المؤقت InnoDB",
            "temp_tables": "الجداول المؤقتة",
            "database_size": "حجم قاعدة البيانات",
        }

    def monitor_database_performance(self) -> Dict[str, Any]:
        """Comprehensive database performance monitoring"""
        try:
            performance_data = {
                "timestamp": now_datetime().isoformat(),
                "connection_stats": self._get_connection_statistics(),
                "query_performance": self._analyze_query_performance(),
                "innodb_metrics": self._get_innodb_metrics(),
                "database_size": self._get_database_size_info(),
                "replication_status": self._get_replication_status(),
                "slow_queries": self._get_slow_query_analysis(),
                "table_locks": self._get_table_lock_analysis(),
                "cache_performance": self._get_cache_performance(),
                "system_status": self._get_system_status(),
            }

            # Store in Redis for real-time access
            if self.redis_client:
                self._store_realtime_metrics(performance_data)

            # Check for alerts
            self._check_database_alerts(performance_data)

            return performance_data

        except Exception as e:
            frappe.log_error(f"Database monitoring error: {str(e)}", "Database Monitor Error")
            return {"error": str(e), "timestamp": now_datetime().isoformat()}

    def _get_connection_statistics(self) -> Dict[str, Any]:
        """Get database connection statistics"""
        try:
            # MySQL connection stats
            connection_stats = frappe.db.sql(
                """
                SHOW STATUS LIKE 'Threads_%'
            """,
                as_dict=True,
            )

            # Convert to dictionary
            stats_dict = {stat["Variable_name"]: flt(stat["Value"]) for stat in connection_stats}

            # Get max connections
            max_connections = frappe.db.sql(
                """
                SHOW VARIABLES LIKE 'max_connections'
            """,
                as_dict=True,
            )

            max_conn_value = flt(max_connections[0]["Value"]) if max_connections else 0

            # Calculate connection utilization
            current_connections = stats_dict.get("Threads_connected", 0)
            connection_utilization = (
                (current_connections / max_conn_value * 100) if max_conn_value > 0 else 0
            )

            return {
                "current_connections": current_connections,
                "max_connections": max_conn_value,
                "connection_utilization_percent": round(connection_utilization, 2),
                "threads_running": stats_dict.get("Threads_running", 0),
                "threads_cached": stats_dict.get("Threads_cached", 0),
                "threads_created": stats_dict.get("Threads_created", 0),
                "status": (
                    "healthy"
                    if connection_utilization < 80
                    else "warning" if connection_utilization < 95 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(f"Connection statistics error: {str(e)}", "Database Monitor Error")
            return {"error": str(e)}

    def _analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance and identify slow queries"""
        try:
            # Get query statistics
            query_stats = frappe.db.sql(
                """
                SHOW STATUS WHERE Variable_name LIKE 'Com_%' 
                OR Variable_name LIKE 'Slow_queries'
                OR Variable_name LIKE 'Questions'
                OR Variable_name LIKE 'Queries'
            """,
                as_dict=True,
            )

            stats_dict = {stat["Variable_name"]: flt(stat["Value"]) for stat in query_stats}

            # Calculate query rates
            total_queries = stats_dict.get("Questions", 0)
            slow_queries = stats_dict.get("Slow_queries", 0)
            slow_query_rate = (slow_queries / total_queries * 100) if total_queries > 0 else 0

            # Get current processlist for analysis
            processlist = frappe.db.sql(
                """
                SELECT 
                    ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO
                FROM information_schema.PROCESSLIST 
                WHERE COMMAND != 'Sleep' 
                AND TIME > %s
                ORDER BY TIME DESC
                LIMIT 10
            """,
                [self.slow_query_threshold],
                as_dict=True,
            )

            # Analyze slow queries from performance schema (if available)
            slow_query_analysis = self._get_performance_schema_analysis()

            return {
                "total_queries": total_queries,
                "slow_queries": slow_queries,
                "slow_query_rate_percent": round(slow_query_rate, 4),
                "current_long_running": len(processlist),
                "long_running_queries": processlist,
                "slow_query_details": slow_query_analysis,
                "com_select": stats_dict.get("Com_select", 0),
                "com_insert": stats_dict.get("Com_insert", 0),
                "com_update": stats_dict.get("Com_update", 0),
                "com_delete": stats_dict.get("Com_delete", 0),
                "status": (
                    "healthy"
                    if slow_query_rate < 1
                    else "warning" if slow_query_rate < 5 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(
                f"Query performance analysis error: {str(e)}", "Database Monitor Error"
            )
            return {"error": str(e)}

    def _get_performance_schema_analysis(self) -> List[Dict]:
        """Get detailed slow query analysis from performance schema"""
        try:
            # Check if performance schema is enabled
            ps_enabled = frappe.db.sql(
                """
                SELECT COUNT(*) as count 
                FROM information_schema.SCHEMATA 
                WHERE SCHEMA_NAME = 'performance_schema'
            """,
                as_dict=True,
            )

            if not ps_enabled or ps_enabled[0]["count"] == 0:
                return []

            # Get top slow queries from performance schema
            slow_queries = frappe.db.sql(
                """
                SELECT 
                    DIGEST_TEXT as query_pattern,
                    COUNT_STAR as execution_count,
                    AVG_TIMER_WAIT/1000000000 as avg_execution_time_seconds,
                    MAX_TIMER_WAIT/1000000000 as max_execution_time_seconds,
                    SUM_ROWS_EXAMINED as total_rows_examined,
                    SUM_ROWS_SENT as total_rows_sent,
                    SUM_CREATED_TMP_TABLES as temp_tables_created,
                    FIRST_SEEN,
                    LAST_SEEN
                FROM performance_schema.events_statements_summary_by_digest 
                WHERE AVG_TIMER_WAIT/1000000000 > %s
                ORDER BY AVG_TIMER_WAIT DESC 
                LIMIT 10
            """,
                [self.slow_query_threshold],
                as_dict=True,
            )

            return slow_queries

        except Exception as e:
            # Performance schema might not be available
            return []

    def _get_innodb_metrics(self) -> Dict[str, Any]:
        """Get InnoDB performance metrics"""
        try:
            # InnoDB status variables
            innodb_stats = frappe.db.sql(
                """
                SHOW STATUS WHERE Variable_name LIKE 'Innodb_%'
            """,
                as_dict=True,
            )

            stats_dict = {stat["Variable_name"]: stat["Value"] for stat in innodb_stats}

            # Buffer pool statistics
            buffer_pool_size = flt(stats_dict.get("Innodb_buffer_pool_bytes_data", 0)) / (
                1024 * 1024
            )  # MB
            buffer_pool_total = (
                flt(stats_dict.get("Innodb_buffer_pool_pages_total", 0)) * 16 / 1024
            )  # MB (16KB pages)
            buffer_pool_free = (
                flt(stats_dict.get("Innodb_buffer_pool_pages_free", 0)) * 16 / 1024
            )  # MB

            buffer_pool_utilization = (
                ((buffer_pool_total - buffer_pool_free) / buffer_pool_total * 100)
                if buffer_pool_total > 0
                else 0
            )

            # Hit rate calculation
            buffer_pool_reads = flt(stats_dict.get("Innodb_buffer_pool_reads", 0))
            buffer_pool_read_requests = flt(stats_dict.get("Innodb_buffer_pool_read_requests", 0))
            hit_rate = (
                ((buffer_pool_read_requests - buffer_pool_reads) / buffer_pool_read_requests * 100)
                if buffer_pool_read_requests > 0
                else 0
            )

            return {
                "buffer_pool_size_mb": round(buffer_pool_size, 2),
                "buffer_pool_total_mb": round(buffer_pool_total, 2),
                "buffer_pool_utilization_percent": round(buffer_pool_utilization, 2),
                "buffer_pool_hit_rate_percent": round(hit_rate, 2),
                "rows_read": flt(stats_dict.get("Innodb_rows_read", 0)),
                "rows_inserted": flt(stats_dict.get("Innodb_rows_inserted", 0)),
                "rows_updated": flt(stats_dict.get("Innodb_rows_updated", 0)),
                "rows_deleted": flt(stats_dict.get("Innodb_rows_deleted", 0)),
                "log_writes": flt(stats_dict.get("Innodb_log_writes", 0)),
                "pages_created": flt(stats_dict.get("Innodb_pages_created", 0)),
                "pages_read": flt(stats_dict.get("Innodb_pages_read", 0)),
                "pages_written": flt(stats_dict.get("Innodb_pages_written", 0)),
                "status": (
                    "healthy" if hit_rate > 95 else "warning" if hit_rate > 85 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(f"InnoDB metrics error: {str(e)}", "Database Monitor Error")
            return {"error": str(e)}

    def _get_database_size_info(self) -> Dict[str, Any]:
        """Get database size and growth information"""
        try:
            # Current database size
            size_query = frappe.db.sql(
                """
                SELECT 
                    table_schema,
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                    ROUND(SUM(data_length) / 1024 / 1024, 2) AS data_size_mb,
                    ROUND(SUM(index_length) / 1024 / 1024, 2) AS index_size_mb,
                    COUNT(*) as table_count
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                GROUP BY table_schema
            """,
                as_dict=True,
            )

            # Largest tables
            largest_tables = frappe.db.sql(
                """
                SELECT 
                    table_name,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                    ROUND(data_length / 1024 / 1024, 2) AS data_size_mb,
                    ROUND(index_length / 1024 / 1024, 2) AS index_size_mb,
                    table_rows
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY (data_length + index_length) DESC 
                LIMIT 10
            """,
                as_dict=True,
            )

            # Table with most rows
            largest_row_count = frappe.db.sql(
                """
                SELECT 
                    table_name,
                    table_rows,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY table_rows DESC 
                LIMIT 10
            """,
                as_dict=True,
            )

            db_info = size_query[0] if size_query else {}

            return {
                "database_name": db_info.get("table_schema", "unknown"),
                "total_size_mb": db_info.get("size_mb", 0),
                "data_size_mb": db_info.get("data_size_mb", 0),
                "index_size_mb": db_info.get("index_size_mb", 0),
                "table_count": db_info.get("table_count", 0),
                "largest_tables": largest_tables,
                "tables_by_row_count": largest_row_count,
                "status": (
                    "healthy"
                    if db_info.get("size_mb", 0) < 5000
                    else "warning" if db_info.get("size_mb", 0) < 10000 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(f"Database size info error: {str(e)}", "Database Monitor Error")
            return {"error": str(e)}

    def _get_replication_status(self) -> Dict[str, Any]:
        """Get MySQL replication status if configured"""
        try:
            # Check if this is a slave
            slave_status = frappe.db.sql("SHOW SLAVE STATUS", as_dict=True)

            if slave_status:
                status = slave_status[0]
                return {
                    "is_slave": True,
                    "slave_io_running": status.get("Slave_IO_Running"),
                    "slave_sql_running": status.get("Slave_SQL_Running"),
                    "seconds_behind_master": status.get("Seconds_Behind_Master"),
                    "master_host": status.get("Master_Host"),
                    "master_port": status.get("Master_Port"),
                    "last_error": status.get("Last_Error"),
                    "status": (
                        "healthy"
                        if status.get("Slave_IO_Running") == "Yes"
                        and status.get("Slave_SQL_Running") == "Yes"
                        else "critical"
                    ),
                }
            else:
                # Check if this is a master
                master_status = frappe.db.sql("SHOW MASTER STATUS", as_dict=True)
                return {
                    "is_slave": False,
                    "is_master": bool(master_status),
                    "master_status": master_status[0] if master_status else None,
                    "status": "healthy",
                }

        except Exception as e:
            # Replication might not be configured
            return {"is_slave": False, "is_master": False, "status": "not_configured"}

    def _get_slow_query_analysis(self) -> Dict[str, Any]:
        """Detailed analysis of slow queries"""
        try:
            # Check if slow query log is enabled
            slow_query_status = frappe.db.sql(
                """
                SHOW VARIABLES WHERE Variable_name IN ('slow_query_log', 'long_query_time', 'slow_query_log_file')
            """,
                as_dict=True,
            )

            status_dict = {var["Variable_name"]: var["Value"] for var in slow_query_status}

            # Get slow query count
            slow_query_count = frappe.db.sql(
                """
                SHOW STATUS LIKE 'Slow_queries'
            """,
                as_dict=True,
            )

            count_value = flt(slow_query_count[0]["Value"]) if slow_query_count else 0

            return {
                "slow_query_log_enabled": status_dict.get("slow_query_log") == "ON",
                "long_query_time": flt(status_dict.get("long_query_time", 0)),
                "slow_query_log_file": status_dict.get("slow_query_log_file"),
                "total_slow_queries": count_value,
                "status": (
                    "healthy"
                    if count_value < 100
                    else "warning" if count_value < 1000 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(f"Slow query analysis error: {str(e)}", "Database Monitor Error")
            return {"error": str(e)}

    def _get_table_lock_analysis(self) -> Dict[str, Any]:
        """Analyze table locks and blocking queries"""
        try:
            # Get table lock stats
            lock_stats = frappe.db.sql(
                """
                SHOW STATUS WHERE Variable_name LIKE '%lock%' OR Variable_name LIKE '%Lock%'
            """,
                as_dict=True,
            )

            stats_dict = {stat["Variable_name"]: flt(stat["Value"]) for stat in lock_stats}

            # Get current lock waits
            lock_waits = frappe.db.sql(
                """
                SELECT 
                    r.trx_id waiting_trx_id,
                    r.trx_mysql_thread_id waiting_thread,
                    r.trx_query waiting_query,
                    b.trx_id blocking_trx_id,
                    b.trx_mysql_thread_id blocking_thread,
                    b.trx_query blocking_query
                FROM information_schema.innodb_lock_waits w
                INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
                INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id
            """,
                as_dict=True,
            )

            return {
                "table_locks_immediate": stats_dict.get("Table_locks_immediate", 0),
                "table_locks_waited": stats_dict.get("Table_locks_waited", 0),
                "innodb_row_lock_waits": stats_dict.get("Innodb_row_lock_waits", 0),
                "innodb_row_lock_time": stats_dict.get("Innodb_row_lock_time", 0),
                "current_lock_waits": len(lock_waits),
                "lock_wait_details": lock_waits,
                "status": (
                    "healthy"
                    if len(lock_waits) == 0
                    else "warning" if len(lock_waits) < 5 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(f"Table lock analysis error: {str(e)}", "Database Monitor Error")
            return {"error": str(e)}

    def _get_cache_performance(self) -> Dict[str, Any]:
        """Analyze query cache and other cache performance"""
        try:
            # Query cache stats
            cache_stats = frappe.db.sql(
                """
                SHOW STATUS WHERE Variable_name LIKE 'Qcache_%'
            """,
                as_dict=True,
            )

            stats_dict = {stat["Variable_name"]: flt(stat["Value"]) for stat in cache_stats}

            # Calculate hit rate
            hits = stats_dict.get("Qcache_hits", 0)
            selects = stats_dict.get("Com_select", 0)
            hit_rate = (hits / (hits + selects) * 100) if (hits + selects) > 0 else 0

            # Key cache stats
            key_cache_stats = frappe.db.sql(
                """
                SHOW STATUS WHERE Variable_name LIKE 'Key_%'
            """,
                as_dict=True,
            )

            key_stats_dict = {stat["Variable_name"]: flt(stat["Value"]) for stat in key_cache_stats}

            return {
                "query_cache_hit_rate_percent": round(hit_rate, 2),
                "query_cache_hits": hits,
                "query_cache_inserts": stats_dict.get("Qcache_inserts", 0),
                "query_cache_size": stats_dict.get("Qcache_total_blocks", 0),
                "key_reads": key_stats_dict.get("Key_reads", 0),
                "key_read_requests": key_stats_dict.get("Key_read_requests", 0),
                "key_writes": key_stats_dict.get("Key_writes", 0),
                "key_write_requests": key_stats_dict.get("Key_write_requests", 0),
                "status": (
                    "healthy" if hit_rate > 80 else "warning" if hit_rate > 60 else "critical"
                ),
            }

        except Exception as e:
            frappe.log_error(
                f"Cache performance analysis error: {str(e)}", "Database Monitor Error"
            )
            return {"error": str(e)}

    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall database system status"""
        try:
            # Uptime and basic stats
            system_vars = frappe.db.sql(
                """
                SHOW STATUS WHERE Variable_name IN ('Uptime', 'Threads_connected', 'Questions', 'Slow_queries', 'Opens', 'Flush_commands', 'Open_tables')
            """,
                as_dict=True,
            )

            stats_dict = {stat["Variable_name"]: flt(stat["Value"]) for stat in system_vars}

            uptime_hours = stats_dict.get("Uptime", 0) / 3600

            return {
                "uptime_hours": round(uptime_hours, 2),
                "questions_per_second": round(
                    stats_dict.get("Questions", 0) / max(stats_dict.get("Uptime", 1), 1), 2
                ),
                "slow_queries_per_hour": round(
                    stats_dict.get("Slow_queries", 0) / max(uptime_hours, 1), 2
                ),
                "open_tables": stats_dict.get("Open_tables", 0),
                "table_opens": stats_dict.get("Opens", 0),
                "flush_commands": stats_dict.get("Flush_commands", 0),
                "status": "healthy",  # Overall status determined by other metrics
            }

        except Exception as e:
            frappe.log_error(f"System status error: {str(e)}", "Database Monitor Error")
            return {"error": str(e)}

    def _store_realtime_metrics(self, performance_data: Dict):
        """Store metrics in Redis for real-time access"""
        if not self.redis_client:
            return

        try:
            # Store current metrics
            self.redis_client.setex("db_monitor:current", 300, frappe.as_json(performance_data))

            # Store historical data (last 24 hours)
            timestamp = now_datetime().strftime("%Y%m%d%H%M")
            history_key = f"db_monitor:history:{timestamp}"

            # Simplified metrics for historical storage
            simplified_metrics = {
                "timestamp": performance_data["timestamp"],
                "connections": performance_data.get("connection_stats", {}).get(
                    "current_connections", 0
                ),
                "slow_queries": performance_data.get("query_performance", {}).get(
                    "slow_queries", 0
                ),
                "buffer_pool_hit_rate": performance_data.get("innodb_metrics", {}).get(
                    "buffer_pool_hit_rate_percent", 0
                ),
                "database_size_mb": performance_data.get("database_size", {}).get(
                    "total_size_mb", 0
                ),
            }

            self.redis_client.setex(history_key, 86400, frappe.as_json(simplified_metrics))

        except Exception as e:
            frappe.log_error(f"Redis storage error: {str(e)}", "Database Monitor Error")

    def _check_database_alerts(self, performance_data: Dict):
        """Check performance data against thresholds and create alerts"""
        try:
            # Import here to avoid circular imports
            from universal_workshop.analytics_reporting.doctype.performance_alert.performance_alert import (
                PerformanceAlert,
            )

            # Check connection utilization
            conn_stats = performance_data.get("connection_stats", {})
            conn_utilization = conn_stats.get("connection_utilization_percent", 0)

            if conn_utilization > 95:
                PerformanceAlert.create_alert(
                    "high_connections",
                    "database_connection_utilization",
                    conn_utilization,
                    95,
                    "Critical",
                    alert_data=conn_stats,
                )
            elif conn_utilization > 80:
                PerformanceAlert.create_alert(
                    "high_connections",
                    "database_connection_utilization",
                    conn_utilization,
                    80,
                    "High",
                    alert_data=conn_stats,
                )

            # Check slow query rate
            query_stats = performance_data.get("query_performance", {})
            slow_query_rate = query_stats.get("slow_query_rate_percent", 0)

            if slow_query_rate > 5:
                PerformanceAlert.create_alert(
                    "high_slow_query_rate",
                    "slow_query_rate_percent",
                    slow_query_rate,
                    5,
                    "Critical",
                    alert_data=query_stats,
                )
            elif slow_query_rate > 1:
                PerformanceAlert.create_alert(
                    "high_slow_query_rate",
                    "slow_query_rate_percent",
                    slow_query_rate,
                    1,
                    "High",
                    alert_data=query_stats,
                )

            # Check InnoDB buffer pool hit rate
            innodb_stats = performance_data.get("innodb_metrics", {})
            hit_rate = innodb_stats.get("buffer_pool_hit_rate_percent", 100)

            if hit_rate < 85:
                PerformanceAlert.create_alert(
                    "low_buffer_pool_hit_rate",
                    "innodb_buffer_pool_hit_rate",
                    hit_rate,
                    85,
                    "Critical",
                    alert_data=innodb_stats,
                )
            elif hit_rate < 95:
                PerformanceAlert.create_alert(
                    "low_buffer_pool_hit_rate",
                    "innodb_buffer_pool_hit_rate",
                    hit_rate,
                    95,
                    "High",
                    alert_data=innodb_stats,
                )

            # Check for lock waits
            lock_stats = performance_data.get("table_locks", {})
            lock_waits = lock_stats.get("current_lock_waits", 0)

            if lock_waits > 10:
                PerformanceAlert.create_alert(
                    "high_lock_waits",
                    "current_lock_waits",
                    lock_waits,
                    10,
                    "Critical",
                    alert_data=lock_stats,
                )
            elif lock_waits > 5:
                PerformanceAlert.create_alert(
                    "high_lock_waits",
                    "current_lock_waits",
                    lock_waits,
                    5,
                    "High",
                    alert_data=lock_stats,
                )

        except Exception as e:
            frappe.log_error(f"Database alert checking error: {str(e)}", "Database Monitor Error")


# Whitelisted API methods
@frappe.whitelist()
def get_database_performance():
    """API endpoint for database performance monitoring"""
    monitor = DatabaseMonitor()
    return monitor.monitor_database_performance()


@frappe.whitelist()
def get_realtime_database_metrics():
    """API endpoint for real-time database metrics"""
    monitor = DatabaseMonitor()

    if not monitor.redis_client:
        return {"error": "Redis not available for real-time metrics"}

    try:
        current_metrics = monitor.redis_client.get("db_monitor:current")
        if current_metrics:
            return frappe.parse_json(current_metrics)
        else:
            # Generate fresh metrics if none cached
            return monitor.monitor_database_performance()

    except Exception as e:
        frappe.log_error(f"Real-time database metrics error: {str(e)}", "Database Monitor Error")
        return {"error": str(e)}


@frappe.whitelist()
def get_database_history(hours=24):
    """API endpoint for historical database metrics"""
    monitor = DatabaseMonitor()

    if not monitor.redis_client:
        return {"error": "Redis not available for historical metrics"}

    try:
        history = []
        current_time = now_datetime()

        for i in range(int(hours) * 6):  # Every 10 minutes
            timestamp = frappe.utils.add_to_date(current_time, minutes=-i * 10)
            history_key = f"db_monitor:history:{timestamp.strftime('%Y%m%d%H%M')}"

            metrics = monitor.redis_client.get(history_key)
            if metrics:
                history.append(frappe.parse_json(metrics))

        return {
            "period_hours": hours,
            "data_points": len(history),
            "metrics": sorted(history, key=lambda x: x["timestamp"]),
        }

    except Exception as e:
        frappe.log_error(f"Database history error: {str(e)}", "Database Monitor Error")
        return {"error": str(e)}


# Background job function
def monitor_database_performance_job():
    """Background job for continuous database monitoring"""
    try:
        monitor = DatabaseMonitor()
        performance_data = monitor.monitor_database_performance()

        frappe.logger().info(f"Database monitoring completed: {performance_data.get('timestamp')}")

        return {"status": "success", "data": performance_data}

    except Exception as e:
        frappe.log_error(f"Database monitoring job error: {str(e)}", "Database Monitor Job Error")
        return {"status": "error", "error": str(e)}


# ✅ ADD: Real-time metrics collection for scheduler
def collect_realtime_metrics():
    """Collect real-time database metrics every 10 minutes"""
    try:
        monitor = DatabaseMonitor()

        # Collect lightweight metrics for real-time monitoring
        realtime_data = {
            "timestamp": now_datetime().isoformat(),
            "connections": monitor._get_connection_statistics(),
            "slow_queries": frappe.db.sql("SHOW STATUS LIKE 'Slow_queries'", as_dict=True),
            "questions": frappe.db.sql("SHOW STATUS LIKE 'Questions'", as_dict=True),
            "threads_running": frappe.db.sql("SHOW STATUS LIKE 'Threads_running'", as_dict=True),
        }

        # Store in Redis for dashboard access
        if monitor.redis_client:
            try:
                # Store current status
                metric_key = f"db:realtime:{now_datetime().strftime('%Y%m%d%H%M')}"
                monitor.redis_client.setex(
                    metric_key, 3600, frappe.as_json(realtime_data)
                )  # 1 hour expiry

                # Update current database status
                monitor.redis_client.setex(
                    "db:current_status", 300, frappe.as_json(realtime_data)
                )  # 5 min expiry

            except Exception as e:
                frappe.log_error(
                    f"Database Redis storage error: {str(e)}", "Database Monitor Redis Error"
                )

        frappe.logger().info(f"Real-time database metrics collected: {realtime_data['timestamp']}")

        return {"status": "success", "metrics": realtime_data}

    except Exception as e:
        frappe.log_error(
            f"Database real-time metrics error: {str(e)}", "Database Monitor Metrics Error"
        )
        return {"status": "error", "error": str(e)}
