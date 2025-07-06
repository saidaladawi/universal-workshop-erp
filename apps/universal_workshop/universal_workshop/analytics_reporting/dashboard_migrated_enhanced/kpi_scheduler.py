"""
Universal Workshop ERP - KPI Background Job Scheduler
Automatic KPI calculation and cache refresh with configurable intervals
"""

import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now
from frappe.utils.background_jobs import enqueue
from universal_workshop.dashboard.realtime_kpi_engine import RealtimeKPIEngine


class KPIScheduler:
    """Background job scheduler for KPI calculations"""

    def __init__(self):
        self.engine = RealtimeKPIEngine()
        self.job_queue = "short"  # Use short queue for frequent updates

    def schedule_all_kpi_updates(self):
        """Schedule all KPI update jobs based on their refresh intervals"""

        # High-frequency KPIs (every 1 minute)
        high_frequency_kpis = ["today_revenue", "active_service_orders", "technician_utilization"]

        # Medium-frequency KPIs (every 5 minutes)
        medium_frequency_kpis = ["completion_rate", "average_service_time", "inventory_health"]

        # Low-frequency KPIs (every 15 minutes)
        low_frequency_kpis = [
            "monthly_revenue",
            "average_order_value",
            "customer_satisfaction",
            "return_customer_rate",
            "equipment_utilization",
        ]

        # Schedule high-frequency updates
        enqueue(
            method=self.update_kpi_category,
            queue=self.job_queue,
            timeout=300,
            job_name="high_frequency_kpi_update",
            kpi_ids=high_frequency_kpis,
            interval=60,  # 1 minute
        )

        # Schedule medium-frequency updates
        enqueue(
            method=self.update_kpi_category,
            queue=self.job_queue,
            timeout=300,
            job_name="medium_frequency_kpi_update",
            kpi_ids=medium_frequency_kpis,
            interval=300,  # 5 minutes
        )

        # Schedule low-frequency updates
        enqueue(
            method=self.update_kpi_category,
            queue=self.job_queue,
            timeout=600,
            job_name="low_frequency_kpi_update",
            kpi_ids=low_frequency_kpis,
            interval=900,  # 15 minutes
        )

    def update_kpi_category(self, kpi_ids: list[str], interval: int):
        """Update specific KPIs and reschedule for next interval"""
        try:
            # Force refresh the specified KPIs
            all_kpis = self.engine.get_all_kpis(force_refresh=True)
            updated_kpis = [kpi for kpi in all_kpis if kpi["id"] in kpi_ids]

            # Log the update
            frappe.logger().info(f"Updated {len(updated_kpis)} KPIs: {', '.join(kpi_ids)}")

            # Reschedule for next interval
            enqueue(
                method=self.update_kpi_category,
                queue=self.job_queue,
                timeout=300,
                job_name=f"kpi_update_{interval}s",
                kpi_ids=kpi_ids,
                interval=interval,
                eta=interval,  # Schedule for next interval
            )

        except Exception as e:
            frappe.log_error(f"KPI update failed for {kpi_ids}: {e!s}", "KPI Scheduler Error")


# Scheduled functions for Frappe scheduler
def update_high_frequency_kpis():
    """Update high-frequency KPIs (called every minute via hooks)"""
    try:
        high_frequency_kpis = ["today_revenue", "active_service_orders", "technician_utilization"]

        engine = RealtimeKPIEngine()
        all_kpis = engine.get_all_kpis(force_refresh=True)
        updated = [kpi for kpi in all_kpis if kpi["id"] in high_frequency_kpis]

        frappe.logger().info(f"High-frequency KPI update: {len(updated)} metrics refreshed")

    except Exception as e:
        frappe.log_error(f"High-frequency KPI update failed: {e!s}", "KPI Scheduler")


def update_medium_frequency_kpis():
    """Update medium-frequency KPIs (called every 5 minutes via hooks)"""
    try:
        medium_frequency_kpis = ["completion_rate", "average_service_time", "inventory_health"]

        engine = RealtimeKPIEngine()
        all_kpis = engine.get_all_kpis(force_refresh=True)
        updated = [kpi for kpi in all_kpis if kpi["id"] in medium_frequency_kpis]

        frappe.logger().info(f"Medium-frequency KPI update: {len(updated)} metrics refreshed")

    except Exception as e:
        frappe.log_error(f"Medium-frequency KPI update failed: {e!s}", "KPI Scheduler")


def update_low_frequency_kpis():
    """Update low-frequency KPIs (called every 15 minutes via hooks)"""
    try:
        low_frequency_kpis = [
            "monthly_revenue",
            "average_order_value",
            "customer_satisfaction",
            "return_customer_rate",
            "equipment_utilization",
        ]

        engine = RealtimeKPIEngine()
        all_kpis = engine.get_all_kpis(force_refresh=True)
        updated = [kpi for kpi in all_kpis if kpi["id"] in low_frequency_kpis]

        frappe.logger().info(f"Low-frequency KPI update: {len(updated)} metrics refreshed")

    except Exception as e:
        frappe.log_error(f"Low-frequency KPI update failed: {e!s}", "KPI Scheduler")


def daily_kpi_cleanup():
    """Daily cleanup and optimization (called daily via hooks)"""
    try:
        engine = RealtimeKPIEngine()

        # Clear old cache entries
        cleared = engine.clear_cache()

        # Warm up cache with fresh data
        engine.get_all_kpis(force_refresh=True)

        frappe.logger().info(f"Daily KPI cleanup: {cleared} cache entries cleared, cache warmed up")

    except Exception as e:
        frappe.log_error(f"Daily KPI cleanup failed: {e!s}", "KPI Scheduler")


# Manual refresh triggers
@frappe.whitelist()
def force_refresh_all_kpis():
    """Manually force refresh all KPIs"""
    try:
        engine = RealtimeKPIEngine()
        kpis = engine.get_all_kpis(force_refresh=True)

        return {
            "success": True,
            "message": _("All KPIs refreshed successfully"),
            "kpi_count": len(kpis),
            "last_updated": get_datetime(),
        }

    except Exception as e:
        frappe.log_error(f"Manual KPI refresh failed: {e!s}", "KPI Manual Refresh")
        return {"success": False, "message": _("KPI refresh failed: {0}").format(str(e))}


@frappe.whitelist()
def get_kpi_update_status():
    """Get status of KPI update jobs"""
    try:
        # Check last update times from cache
        engine = RealtimeKPIEngine()

        status = {
            "last_high_frequency_update": None,
            "last_medium_frequency_update": None,
            "last_low_frequency_update": None,
            "cache_entries": 0,
            "system_status": "online",
        }

        # Try to get cache statistics
        try:
            # This would check Redis/cache status
            cache_info = engine.redis_client.info()
            status["cache_entries"] = cache_info.get("db0", {}).get("keys", 0)
        except Exception:
            status["cache_entries"] = "Unknown"

        return status

    except Exception as e:
        frappe.log_error(f"KPI status check failed: {e!s}", "KPI Status")
        return {"system_status": "error", "error": str(e)}


@frappe.whitelist()
def configure_kpi_intervals(high_freq: int = 60, medium_freq: int = 300, low_freq: int = 900):
    """Configure KPI update intervals"""
    try:
        # Validate intervals
        high_freq = max(30, cint(high_freq))  # Minimum 30 seconds
        medium_freq = max(180, cint(medium_freq))  # Minimum 3 minutes
        low_freq = max(600, cint(low_freq))  # Minimum 10 minutes

        # Store in Site Config or Custom Settings
        frappe.db.set_single_value(
            "Universal Workshop Settings",
            {
                "kpi_high_frequency_interval": high_freq,
                "kpi_medium_frequency_interval": medium_freq,
                "kpi_low_frequency_interval": low_freq,
            },
        )

        return {
            "success": True,
            "message": _("KPI intervals updated successfully"),
            "intervals": {
                "high_frequency": f"{high_freq}s",
                "medium_frequency": f"{medium_freq}s",
                "low_frequency": f"{low_freq}s",
            },
        }

    except Exception as e:
        frappe.log_error(f"KPI interval configuration failed: {e!s}", "KPI Configuration")
        return {"success": False, "message": _("Configuration failed: {0}").format(str(e))}


class KPIHealthMonitor:
    """Monitor KPI system health and performance"""

    def __init__(self):
        self.engine = RealtimeKPIEngine()

    def check_system_health(self) -> dict[str, Any]:
        """Check overall KPI system health"""
        health_report = {
            "overall_status": "healthy",
            "redis_status": "unknown",
            "cache_hit_rate": 0,
            "average_response_time": 0,
            "failed_calculations": 0,
            "recommendations": [],
        }

        try:
            # Check Redis connectivity
            self.engine.redis_client.ping()
            health_report["redis_status"] = "healthy"
        except Exception:
            health_report["redis_status"] = "error"
            health_report["overall_status"] = "warning"
            health_report["recommendations"].append("Check Redis connection")

        # Check cache performance
        try:
            import time

            start_time = time.time()

            # Test cache performance
            self.engine.get_all_kpis()
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            health_report["average_response_time"] = round(response_time, 2)

            if response_time > 1000:  # > 1 second
                health_report["overall_status"] = "warning"
                health_report["recommendations"].append("High response time detected")

        except Exception as e:
            health_report["failed_calculations"] += 1
            health_report["overall_status"] = "error"
            health_report["recommendations"].append(f"KPI calculation failed: {e!s}")

        return health_report

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get detailed performance metrics"""
        metrics = {
            "total_kpis": 0,
            "cached_kpis": 0,
            "cache_efficiency": 0,
            "update_frequency": {},
            "error_rate": 0,
        }

        try:
            # Get all KPIs
            all_kpis = self.engine.get_all_kpis()
            metrics["total_kpis"] = len(all_kpis)

            # Check cache efficiency
            cached_count = 0
            for kpi in all_kpis:
                cache_key = f"kpi_{kpi['id']}"
                if self.engine._get_cached_data(cache_key):
                    cached_count += 1

            metrics["cached_kpis"] = cached_count
            metrics["cache_efficiency"] = (cached_count / len(all_kpis) * 100) if all_kpis else 0

        except Exception as e:
            frappe.log_error(f"Performance metrics calculation failed: {e!s}", "KPI Performance")
            metrics["error_rate"] = 100

        return metrics


@frappe.whitelist()
def get_kpi_health_report():
    """Get comprehensive KPI system health report"""
    try:
        monitor = KPIHealthMonitor()

        health = monitor.check_system_health()
        performance = monitor.get_performance_metrics()

        return {
            "success": True,
            "health": health,
            "performance": performance,
            "timestamp": get_datetime(),
        }

    except Exception as e:
        frappe.log_error(f"Health report generation failed: {e!s}", "KPI Health Report")
        return {"success": False, "error": str(e)}
