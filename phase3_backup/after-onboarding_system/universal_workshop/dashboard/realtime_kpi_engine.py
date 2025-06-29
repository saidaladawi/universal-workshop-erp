"""
Universal Workshop ERP - Real-time KPI Metrics Engine
Advanced metrics calculation with Redis caching and background job processing
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, add_days, flt, cint, time_diff_in_seconds
from frappe.utils.redis_wrapper import RedisWrapper
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime, timedelta
import time
import redis


class RealtimeKPIEngine:
    """Real-time KPI calculation engine with Redis caching and background processing"""

    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.cache_ttl = 300  # 5 minutes default TTL
        self.language = frappe.local.lang or "en"
        self.user = frappe.session.user
        self.user_roles = frappe.get_roles()

    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for caching"""
        try:
            return frappe.cache()
        except Exception:
            # Fallback to local Redis if Frappe cache fails
            return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

    def get_all_kpis(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get all KPI metrics with caching support"""
        cache_key = f"workshop_kpis_{self.user}_{self.language}"

        if not force_refresh:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

        kpis = []

        # Financial KPIs
        kpis.extend(self._get_financial_kpis())

        # Operational KPIs
        kpis.extend(self._get_operational_kpis())

        # Resource KPIs
        kpis.extend(self._get_resource_kpis())

        # Customer KPIs
        kpis.extend(self._get_customer_kpis())

        # Cache the results
        self._set_cached_data(cache_key, kpis, self.cache_ttl)

        return kpis

    def _get_financial_kpis(self) -> List[Dict[str, Any]]:
        """Get financial performance KPIs"""
        kpis = []

        # Today's Revenue with real-time calculation
        revenue_data = self._calculate_revenue_metrics()
        kpis.append(
            {
                "id": "today_revenue",
                "title": _("Today's Revenue") if self.language == "en" else "إيرادات اليوم",
                "value": revenue_data["today"],
                "previous_value": revenue_data["yesterday"],
                "format": "currency",
                "currency": "OMR",
                "trend": self._calculate_trend(revenue_data["today"], revenue_data["yesterday"]),
                "icon": "fa-money-bill-wave",
                "color": self._get_trend_color(revenue_data["today"], revenue_data["yesterday"]),
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": revenue_data.get("daily_target", 0),
                "achievement_percentage": self._calculate_achievement_percentage(
                    revenue_data["today"], revenue_data.get("daily_target", 0)
                ),
            }
        )

        # Monthly Revenue Progress
        monthly_data = self._calculate_monthly_revenue_progress()
        kpis.append(
            {
                "id": "monthly_revenue",
                "title": _("Monthly Progress") if self.language == "en" else "التقدم الشهري",
                "value": monthly_data["current_month"],
                "format": "currency",
                "currency": "OMR",
                "trend": self._calculate_trend(
                    monthly_data["current_month"], monthly_data["last_month"]
                ),
                "icon": "fa-chart-line",
                "color": "primary",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": monthly_data.get("monthly_target", 0),
                "achievement_percentage": self._calculate_achievement_percentage(
                    monthly_data["current_month"], monthly_data.get("monthly_target", 0)
                ),
                "subtitle": f"{monthly_data['days_completed']}/{monthly_data['total_days']} "
                + (_("days") if self.language == "en" else "أيام"),
            }
        )

        # Average Order Value
        aov_data = self._calculate_average_order_value()
        kpis.append(
            {
                "id": "average_order_value",
                "title": _("Avg Order Value") if self.language == "en" else "متوسط قيمة الطلب",
                "value": aov_data["current"],
                "format": "currency",
                "currency": "OMR",
                "trend": self._calculate_trend(aov_data["current"], aov_data["previous"]),
                "icon": "fa-receipt",
                "color": "info",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "subtitle": f"{aov_data['order_count']} "
                + (_("orders today") if self.language == "en" else "طلبات اليوم"),
            }
        )

        return kpis

    def _get_operational_kpis(self) -> List[Dict[str, Any]]:
        """Get operational performance KPIs"""
        kpis = []

        # Active Service Orders with priority breakdown
        orders_data = self._calculate_service_orders_metrics()
        kpis.append(
            {
                "id": "active_service_orders",
                "title": (
                    _("Active Service Orders") if self.language == "en" else "أوامر الخدمة النشطة"
                ),
                "value": orders_data["total"],
                "format": "number",
                "trend": self._calculate_trend(
                    orders_data["total"], orders_data["yesterday_total"]
                ),
                "icon": "fa-tools",
                "color": "primary",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "breakdown": {
                    "urgent": orders_data["urgent"],
                    "normal": orders_data["normal"],
                    "low": orders_data["low"],
                },
                "subtitle": f"{orders_data['urgent']} "
                + (_("urgent") if self.language == "en" else "عاجل"),
            }
        )

        # Service Completion Rate
        completion_data = self._calculate_completion_rate()
        kpis.append(
            {
                "id": "completion_rate",
                "title": _("Completion Rate") if self.language == "en" else "معدل الإنجاز",
                "value": completion_data["rate"],
                "format": "percentage",
                "trend": self._calculate_trend(
                    completion_data["rate"], completion_data["previous_rate"]
                ),
                "icon": "fa-check-circle",
                "color": "success",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": 90,  # Target 90% completion rate
                "achievement_percentage": completion_data["rate"],
                "subtitle": f"{completion_data['completed_today']}/{completion_data['total_today']} "
                + (_("completed") if self.language == "en" else "مكتمل"),
            }
        )

        # Average Service Time
        service_time_data = self._calculate_average_service_time()
        kpis.append(
            {
                "id": "average_service_time",
                "title": _("Avg Service Time") if self.language == "en" else "متوسط وقت الخدمة",
                "value": service_time_data["hours"],
                "format": "decimal",
                "unit": _("hours") if self.language == "en" else "ساعات",
                "trend": self._calculate_trend(
                    service_time_data["hours"], service_time_data["previous_hours"], reverse=True
                ),
                "icon": "fa-clock",
                "color": "warning",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": service_time_data.get("target_hours", 8),
                "subtitle": f"{service_time_data['completed_count']} "
                + (_("services") if self.language == "en" else "خدمات"),
            }
        )

        return kpis

    def _get_resource_kpis(self) -> List[Dict[str, Any]]:
        """Get resource utilization KPIs"""
        kpis = []

        # Technician Utilization with detailed breakdown
        tech_data = self._calculate_technician_utilization()
        kpis.append(
            {
                "id": "technician_utilization",
                "title": (
                    _("Technician Utilization") if self.language == "en" else "استخدام الفنيين"
                ),
                "value": tech_data["utilization_percentage"],
                "format": "percentage",
                "trend": self._calculate_trend(
                    tech_data["utilization_percentage"], tech_data["previous_utilization"]
                ),
                "icon": "fa-users",
                "color": "info",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": 85,  # Target 85% utilization
                "breakdown": {
                    "total_technicians": tech_data["total"],
                    "active_technicians": tech_data["active"],
                    "idle_technicians": tech_data["idle"],
                    "on_break": tech_data.get("on_break", 0),
                },
                "subtitle": f"{tech_data['active']}/{tech_data['total']} "
                + (_("active") if self.language == "en" else "نشط"),
            }
        )

        # Equipment Utilization
        equipment_data = self._calculate_equipment_utilization()
        kpis.append(
            {
                "id": "equipment_utilization",
                "title": _("Equipment Usage") if self.language == "en" else "استخدام المعدات",
                "value": equipment_data["utilization_percentage"],
                "format": "percentage",
                "trend": self._calculate_trend(
                    equipment_data["utilization_percentage"], equipment_data["previous_utilization"]
                ),
                "icon": "fa-wrench",
                "color": "secondary",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "breakdown": {
                    "total_equipment": equipment_data["total"],
                    "in_use": equipment_data["in_use"],
                    "maintenance": equipment_data.get("maintenance", 0),
                    "available": equipment_data["available"],
                },
            }
        )

        # Inventory Health
        inventory_data = self._calculate_inventory_health()
        kpis.append(
            {
                "id": "inventory_health",
                "title": _("Inventory Health") if self.language == "en" else "صحة المخزون",
                "value": inventory_data["health_score"],
                "format": "percentage",
                "trend": self._calculate_trend(
                    inventory_data["health_score"], inventory_data["previous_score"]
                ),
                "icon": "fa-boxes",
                "color": self._get_inventory_health_color(inventory_data["health_score"]),
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "breakdown": {
                    "total_items": inventory_data["total_items"],
                    "in_stock": inventory_data["in_stock"],
                    "low_stock": inventory_data["low_stock"],
                    "out_of_stock": inventory_data["out_of_stock"],
                },
                "subtitle": f"{inventory_data['low_stock']} "
                + (_("low stock") if self.language == "en" else "مخزون منخفض"),
            }
        )

        return kpis

    def _get_customer_kpis(self) -> List[Dict[str, Any]]:
        """Get customer satisfaction and service KPIs"""
        kpis = []

        # Customer Satisfaction Score
        satisfaction_data = self._calculate_customer_satisfaction()
        kpis.append(
            {
                "id": "customer_satisfaction",
                "title": _("Customer Satisfaction") if self.language == "en" else "رضا العملاء",
                "value": satisfaction_data["average_rating"],
                "format": "decimal",
                "unit": "/5",
                "trend": self._calculate_trend(
                    satisfaction_data["average_rating"], satisfaction_data["previous_rating"]
                ),
                "icon": "fa-smile",
                "color": self._get_satisfaction_color(satisfaction_data["average_rating"]),
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": 4.5,
                "breakdown": {
                    "total_reviews": satisfaction_data["total_reviews"],
                    "five_star": satisfaction_data.get("five_star", 0),
                    "four_star": satisfaction_data.get("four_star", 0),
                    "three_star": satisfaction_data.get("three_star", 0),
                    "two_star": satisfaction_data.get("two_star", 0),
                    "one_star": satisfaction_data.get("one_star", 0),
                },
                "subtitle": f"{satisfaction_data['total_reviews']} "
                + (_("reviews") if self.language == "en" else "مراجعة"),
            }
        )

        # Return Customer Rate
        return_customer_data = self._calculate_return_customer_rate()
        kpis.append(
            {
                "id": "return_customer_rate",
                "title": (
                    _("Return Customer Rate") if self.language == "en" else "معدل العملاء العائدين"
                ),
                "value": return_customer_data["rate"],
                "format": "percentage",
                "trend": self._calculate_trend(
                    return_customer_data["rate"], return_customer_data["previous_rate"]
                ),
                "icon": "fa-redo",
                "color": "success",
                "grid_size": "col-lg-3 col-md-6 col-sm-12",
                "last_updated": get_datetime(),
                "target": 70,  # Target 70% return rate
                "subtitle": f"{return_customer_data['return_customers']}/{return_customer_data['total_customers']} "
                + (_("customers") if self.language == "en" else "عملاء"),
            }
        )

        return kpis

    # Real-time calculation methods
    def _calculate_revenue_metrics(self) -> Dict[str, float]:
        """Calculate real-time revenue metrics"""
        cache_key = "revenue_metrics"
        cached = self._get_cached_data(cache_key, ttl=60)  # 1-minute cache

        if cached:
            return cached

        today = nowdate()
        yesterday = add_days(today, -1)

        # Today's revenue
        today_revenue = frappe.db.sql(
            """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE posting_date = %s 
            AND docstatus = 1
            AND is_return = 0
        """,
            (today,),
        )[0][0]

        # Yesterday's revenue
        yesterday_revenue = frappe.db.sql(
            """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE posting_date = %s 
            AND docstatus = 1
            AND is_return = 0
        """,
            (yesterday,),
        )[0][0]

        # Daily target (from settings or calculated)
        daily_target = self._get_daily_revenue_target()

        result = {
            "today": flt(today_revenue, 3),
            "yesterday": flt(yesterday_revenue, 3),
            "daily_target": flt(daily_target, 3),
        }

        self._set_cached_data(cache_key, result, 60)
        return result

    def _calculate_monthly_revenue_progress(self) -> Dict[str, Any]:
        """Calculate monthly revenue progress"""
        cache_key = "monthly_revenue_progress"
        cached = self._get_cached_data(cache_key, ttl=300)  # 5-minute cache

        if cached:
            return cached

        today = datetime.now()
        current_month_start = today.replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)

        # Current month revenue
        current_month_revenue = frappe.db.sql(
            """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE posting_date >= %s AND posting_date <= %s
            AND docstatus = 1
            AND is_return = 0
        """,
            (current_month_start.date(), today.date()),
        )[0][0]

        # Last month revenue
        last_month_revenue = frappe.db.sql(
            """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE posting_date >= %s AND posting_date <= %s
            AND docstatus = 1
            AND is_return = 0
        """,
            (last_month_start.date(), last_month_end.date()),
        )[0][0]

        # Calculate month metrics
        import calendar

        total_days = calendar.monthrange(today.year, today.month)[1]
        days_completed = today.day

        result = {
            "current_month": flt(current_month_revenue, 3),
            "last_month": flt(last_month_revenue, 3),
            "monthly_target": self._get_monthly_revenue_target(),
            "days_completed": days_completed,
            "total_days": total_days,
        }

        self._set_cached_data(cache_key, result, 300)
        return result

    def _calculate_average_order_value(self) -> Dict[str, float]:
        """Calculate average order value"""
        cache_key = "average_order_value"
        cached = self._get_cached_data(cache_key, ttl=300)

        if cached:
            return cached

        today = nowdate()
        yesterday = add_days(today, -1)

        # Today's AOV
        today_stats = frappe.db.sql(
            """
            SELECT 
                COALESCE(AVG(grand_total), 0) as avg_value,
                COUNT(*) as order_count
            FROM `tabSales Invoice`
            WHERE posting_date = %s 
            AND docstatus = 1
            AND is_return = 0
        """,
            (today,),
            as_dict=True,
        )[0]

        # Yesterday's AOV
        yesterday_aov = frappe.db.sql(
            """
            SELECT COALESCE(AVG(grand_total), 0) as avg_value
            FROM `tabSales Invoice`
            WHERE posting_date = %s 
            AND docstatus = 1
            AND is_return = 0
        """,
            (yesterday,),
        )[0][0]

        result = {
            "current": flt(today_stats.avg_value, 3),
            "previous": flt(yesterday_aov, 3),
            "order_count": cint(today_stats.order_count),
        }

        self._set_cached_data(cache_key, result, 300)
        return result

    def _calculate_service_orders_metrics(self) -> Dict[str, int]:
        """Calculate service orders metrics"""
        cache_key = "service_orders_metrics"
        cached = self._get_cached_data(cache_key, ttl=60)

        if cached:
            return cached

        # Current active orders
        active_orders = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as urgent,
                SUM(CASE WHEN priority = 'Medium' THEN 1 ELSE 0 END) as normal,
                SUM(CASE WHEN priority = 'Low' THEN 1 ELSE 0 END) as low
            FROM `tabWork Order`
            WHERE status IN ('Open', 'In Progress', 'Material Transferred')
            AND docstatus = 1
        """,
            as_dict=True,
        )[0]

        # Yesterday's count for trend
        yesterday = add_days(nowdate(), -1)
        yesterday_count = frappe.db.sql(
            """
            SELECT COUNT(*) as count
            FROM `tabWork Order`
            WHERE DATE(creation) = %s
            AND docstatus = 1
        """,
            (yesterday,),
        )[0][0]

        result = {
            "total": cint(active_orders.total),
            "urgent": cint(active_orders.urgent),
            "normal": cint(active_orders.normal),
            "low": cint(active_orders.low),
            "yesterday_total": cint(yesterday_count),
        }

        self._set_cached_data(cache_key, result, 60)
        return result

    def _calculate_completion_rate(self) -> Dict[str, float]:
        """Calculate service completion rate"""
        cache_key = "completion_rate"
        cached = self._get_cached_data(cache_key, ttl=300)

        if cached:
            return cached

        today = nowdate()
        yesterday = add_days(today, -1)

        # Today's completion stats
        today_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_today,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_today
            FROM `tabWork Order`
            WHERE DATE(creation) = %s
            AND docstatus = 1
        """,
            (today,),
            as_dict=True,
        )[0]

        # Yesterday's completion rate
        yesterday_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM `tabWork Order`
            WHERE DATE(creation) = %s
            AND docstatus = 1
        """,
            (yesterday,),
            as_dict=True,
        )[0]

        # Calculate rates
        today_rate = (
            (today_stats.completed_today / today_stats.total_today * 100)
            if today_stats.total_today > 0
            else 0
        )
        yesterday_rate = (
            (yesterday_stats.completed / yesterday_stats.total * 100)
            if yesterday_stats.total > 0
            else 0
        )

        result = {
            "rate": flt(today_rate, 1),
            "previous_rate": flt(yesterday_rate, 1),
            "completed_today": cint(today_stats.completed_today),
            "total_today": cint(today_stats.total_today),
        }

        self._set_cached_data(cache_key, result, 300)
        return result

    def _calculate_average_service_time(self) -> Dict[str, float]:
        """Calculate average service completion time"""
        cache_key = "average_service_time"
        cached = self._get_cached_data(cache_key, ttl=300)

        if cached:
            return cached

        # Last 7 days average service time
        week_ago = add_days(nowdate(), -7)

        service_times = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as count,
                AVG(TIMESTAMPDIFF(HOUR, creation, modified)) as avg_hours
            FROM `tabWork Order`
            WHERE status = 'Completed'
            AND creation >= %s
            AND docstatus = 1
        """,
            (week_ago,),
            as_dict=True,
        )[0]

        # Previous week for comparison
        two_weeks_ago = add_days(nowdate(), -14)
        previous_avg = frappe.db.sql(
            """
            SELECT AVG(TIMESTAMPDIFF(HOUR, creation, modified)) as avg_hours
            FROM `tabWork Order`
            WHERE status = 'Completed'
            AND creation >= %s AND creation < %s
            AND docstatus = 1
        """,
            (two_weeks_ago, week_ago),
        )[0][0]

        result = {
            "hours": flt(service_times.avg_hours or 0, 1),
            "previous_hours": flt(previous_avg or 0, 1),
            "completed_count": cint(service_times.count),
            "target_hours": 8.0,  # Target 8 hours average
        }

        self._set_cached_data(cache_key, result, 300)
        return result

    def _calculate_technician_utilization(self) -> Dict[str, Any]:
        """Calculate real-time technician utilization"""
        cache_key = "technician_utilization"
        cached = self._get_cached_data(cache_key, ttl=120)

        if cached:
            return cached

        # Get total active technicians
        total_technicians = frappe.db.count(
            "Employee", {"designation": "Technician", "status": "Active"}
        )

        # Get currently working technicians
        active_technicians = frappe.db.sql(
            """
            SELECT COUNT(DISTINCT employee) as active
            FROM `tabWork Order`
            WHERE status IN ('Open', 'In Progress', 'Material Transferred')
            AND employee IS NOT NULL
            AND docstatus = 1
        """
        )[0][0]

        # Calculate utilization
        utilization = (active_technicians / total_technicians * 100) if total_technicians > 0 else 0

        # Previous period utilization for trend
        yesterday = add_days(nowdate(), -1)
        previous_utilization = (
            frappe.db.sql(
                """
            SELECT COUNT(DISTINCT employee) / %s * 100 as util
            FROM `tabWork Order`
            WHERE DATE(creation) = %s
            AND employee IS NOT NULL
            AND docstatus = 1
        """,
                (total_technicians, yesterday),
            )[0][0]
            or 0
        )

        result = {
            "total": total_technicians,
            "active": cint(active_technicians),
            "idle": total_technicians - cint(active_technicians),
            "utilization_percentage": flt(utilization, 1),
            "previous_utilization": flt(previous_utilization, 1),
        }

        self._set_cached_data(cache_key, result, 120)
        return result

    def _calculate_equipment_utilization(self) -> Dict[str, Any]:
        """Calculate equipment utilization"""
        cache_key = "equipment_utilization"
        cached = self._get_cached_data(cache_key, ttl=300)

        if cached:
            return cached

        # Placeholder for equipment tracking
        # This would integrate with equipment management system
        result = {
            "total": 15,
            "in_use": 12,
            "available": 3,
            "maintenance": 0,
            "utilization_percentage": 80.0,
            "previous_utilization": 75.0,
        }

        self._set_cached_data(cache_key, result, 300)
        return result

    def _calculate_inventory_health(self) -> Dict[str, Any]:
        """Calculate inventory health metrics"""
        cache_key = "inventory_health"
        cached = self._get_cached_data(cache_key, ttl=600)  # 10-minute cache

        if cached:
            return cached

        # Inventory statistics
        inventory_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_items,
                SUM(CASE WHEN 
                    (SELECT COALESCE(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = i.item_code) > i.reorder_level 
                    THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN 
                    (SELECT COALESCE(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = i.item_code) <= i.reorder_level
                    AND (SELECT COALESCE(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = i.item_code) > 0
                    THEN 1 ELSE 0 END) as low_stock,
                SUM(CASE WHEN 
                    (SELECT COALESCE(SUM(actual_qty), 0) FROM `tabBin` WHERE item_code = i.item_code) <= 0
                    THEN 1 ELSE 0 END) as out_of_stock
            FROM `tabItem` i
            WHERE is_stock_item = 1
            AND disabled = 0
        """,
            as_dict=True,
        )[0]

        # Calculate health score
        total = inventory_stats.total_items or 1
        health_score = (inventory_stats.in_stock / total * 100) if total > 0 else 0

        result = {
            "total_items": cint(inventory_stats.total_items),
            "in_stock": cint(inventory_stats.in_stock),
            "low_stock": cint(inventory_stats.low_stock),
            "out_of_stock": cint(inventory_stats.out_of_stock),
            "health_score": flt(health_score, 1),
            "previous_score": 75.0,  # Would be calculated from historical data
        }

        self._set_cached_data(cache_key, result, 600)
        return result

    def _calculate_customer_satisfaction(self) -> Dict[str, Any]:
        """Calculate customer satisfaction metrics"""
        cache_key = "customer_satisfaction"
        cached = self._get_cached_data(cache_key, ttl=900)  # 15-minute cache

        if cached:
            return cached

        # Get satisfaction data from feedback
        satisfaction_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_reviews,
                AVG(rating) as average_rating,
                SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as five_star,
                SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as four_star,
                SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as three_star,
                SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as two_star,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as one_star
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
            AND docstatus = 1
        """,
            (add_days(nowdate(), -30),),
            as_dict=True,
        )[0]

        # Previous month for comparison
        previous_rating = frappe.db.sql(
            """
            SELECT AVG(rating) as avg_rating
            FROM `tabCustomer Feedback`
            WHERE creation >= %s AND creation < %s
            AND docstatus = 1
        """,
            (add_days(nowdate(), -60), add_days(nowdate(), -30)),
        )[0][0]

        result = {
            "total_reviews": cint(satisfaction_stats.total_reviews),
            "average_rating": flt(satisfaction_stats.average_rating or 0, 1),
            "previous_rating": flt(previous_rating or 0, 1),
            "five_star": cint(satisfaction_stats.five_star),
            "four_star": cint(satisfaction_stats.four_star),
            "three_star": cint(satisfaction_stats.three_star),
            "two_star": cint(satisfaction_stats.two_star),
            "one_star": cint(satisfaction_stats.one_star),
        }

        self._set_cached_data(cache_key, result, 900)
        return result

    def _calculate_return_customer_rate(self) -> Dict[str, Any]:
        """Calculate return customer rate"""
        cache_key = "return_customer_rate"
        cached = self._get_cached_data(cache_key, ttl=3600)  # 1-hour cache

        if cached:
            return cached

        # Last 30 days
        month_ago = add_days(nowdate(), -30)

        # Customers with multiple orders
        customer_stats = frappe.db.sql(
            """
            SELECT 
                COUNT(DISTINCT customer) as total_customers,
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer END) as return_customers
            FROM (
                SELECT customer, COUNT(*) as order_count
                FROM `tabSales Invoice`
                WHERE posting_date >= %s
                AND docstatus = 1
                GROUP BY customer
            ) customer_orders
        """,
            (month_ago,),
            as_dict=True,
        )[0]

        # Calculate return rate
        return_rate = (
            (customer_stats.return_customers / customer_stats.total_customers * 100)
            if customer_stats.total_customers > 0
            else 0
        )

        result = {
            "total_customers": cint(customer_stats.total_customers),
            "return_customers": cint(customer_stats.return_customers),
            "rate": flt(return_rate, 1),
            "previous_rate": 65.0,  # Would be calculated from historical data
        }

        self._set_cached_data(cache_key, result, 3600)
        return result

    # Utility methods
    def _calculate_trend(
        self, current: float, previous: float, reverse: bool = False
    ) -> Dict[str, Any]:
        """Calculate trend direction and percentage"""
        if previous == 0:
            change = 100 if current > 0 else 0
        else:
            change = ((current - previous) / previous) * 100

        if reverse:  # For metrics where lower is better (like service time)
            direction = "down" if change <= 0 else "up"
            color = "success" if change <= 0 else "danger"
        else:
            direction = "up" if change >= 0 else "down"
            color = "success" if change >= 0 else "danger"

        return {"direction": direction, "percentage": flt(abs(change), 1), "color": color}

    def _calculate_achievement_percentage(self, current: float, target: float) -> float:
        """Calculate achievement percentage against target"""
        if target == 0:
            return 0
        return flt((current / target) * 100, 1)

    def _get_trend_color(self, current: float, previous: float) -> str:
        """Get color based on trend"""
        if current >= previous:
            return "success"
        elif current >= previous * 0.9:  # Within 10% of previous
            return "warning"
        else:
            return "danger"

    def _get_inventory_health_color(self, health_score: float) -> str:
        """Get color based on inventory health score"""
        if health_score >= 80:
            return "success"
        elif health_score >= 60:
            return "warning"
        else:
            return "danger"

    def _get_satisfaction_color(self, rating: float) -> str:
        """Get color based on satisfaction rating"""
        if rating >= 4.0:
            return "success"
        elif rating >= 3.0:
            return "warning"
        else:
            return "danger"

    def _get_daily_revenue_target(self) -> float:
        """Get daily revenue target"""
        # This would come from settings
        return 2000.0  # OMR 2000 daily target

    def _get_monthly_revenue_target(self) -> float:
        """Get monthly revenue target"""
        # This would come from settings
        return 60000.0  # OMR 60000 monthly target

    # Cache management
    def _get_cached_data(self, key: str, ttl: int = None) -> Optional[Any]:
        """Get data from Redis cache"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            frappe.log_error(f"Cache get error: {e}", "KPI Cache Error")
        return None

    def _set_cached_data(self, key: str, data: Any, ttl: int = None) -> bool:
        """Set data in Redis cache"""
        try:
            ttl = ttl or self.cache_ttl
            self.redis_client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            frappe.log_error(f"Cache set error: {e}", "KPI Cache Error")
            return False

    def clear_cache(self, pattern: str = "workshop_*") -> int:
        """Clear cache entries matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            frappe.log_error(f"Cache clear error: {e}", "KPI Cache Error")
        return 0


# API Methods for dashboard integration
@frappe.whitelist()
def get_realtime_kpis(force_refresh: bool = False):
    """Get all real-time KPI metrics"""
    engine = RealtimeKPIEngine()
    return engine.get_all_kpis(force_refresh=cint(force_refresh))


@frappe.whitelist()
def get_kpi_by_category(category: str, force_refresh: bool = False):
    """Get KPIs by category (financial, operational, resource, customer)"""
    engine = RealtimeKPIEngine()
    all_kpis = engine.get_all_kpis(force_refresh=cint(force_refresh))

    category_mapping = {
        "financial": ["today_revenue", "monthly_revenue", "average_order_value"],
        "operational": ["active_service_orders", "completion_rate", "average_service_time"],
        "resource": ["technician_utilization", "equipment_utilization", "inventory_health"],
        "customer": ["customer_satisfaction", "return_customer_rate"],
    }

    if category not in category_mapping:
        return all_kpis

    return [kpi for kpi in all_kpis if kpi["id"] in category_mapping[category]]


@frappe.whitelist()
def clear_kpi_cache():
    """Clear all KPI cache entries"""
    engine = RealtimeKPIEngine()
    cleared_count = engine.clear_cache()
    return {"success": True, "cleared_entries": cleared_count}


@frappe.whitelist()
def get_kpi_trends(kpi_id: str, days: int = 7):
    """Get historical trend data for a specific KPI"""
    # This would implement historical trend calculation
    # For now, return sample data
    return {"kpi_id": kpi_id, "trend_data": [], "period": f"Last {days} days"}
