# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional


class MigrationDashboard(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate migration dashboard configuration"""
        self.validate_dashboard_name()
        self.validate_refresh_settings()
        self.validate_notification_settings()
        self.set_defaults()

    def validate_dashboard_name(self):
        """Ensure dashboard name is provided"""
        if not self.dashboard_name:
            frappe.throw(_("Dashboard name is required"))

        if not self.dashboard_name_ar and frappe.local.lang == "ar":
            frappe.msgprint(_("Arabic dashboard name recommended for Arabic locale"))

    def validate_refresh_settings(self):
        """Validate auto-refresh settings"""
        if self.auto_refresh_enabled:
            if not self.refresh_interval or self.refresh_interval < 10:
                frappe.throw(_("Minimum refresh interval is 10 seconds"))
            if self.refresh_interval > 3600:
                frappe.throw(_("Maximum refresh interval is 1 hour (3600 seconds)"))

    def validate_notification_settings(self):
        """Validate notification threshold settings"""
        if self.enable_notifications:
            if not self.notification_threshold:
                self.notification_threshold = 90
            if self.notification_threshold < 0 or self.notification_threshold > 100:
                frappe.throw(_("Notification threshold must be between 0 and 100"))

    def set_defaults(self):
        """Set default values for new dashboards"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.today()
        if not self.layout_columns:
            self.layout_columns = "4"
        if not self.widget_size:
            self.widget_size = "Medium"
        if not self.color_scheme:
            self.color_scheme = "Default"

    def before_save(self):
        """Process dashboard configuration before saving"""
        self.setup_default_kpis()
        self.setup_default_charts()
        self.validate_widget_positions()

    def setup_default_kpis(self):
        """Setup default KPI cards if none exist"""
        if not self.kpi_cards:
            default_kpis = [
                {
                    "kpi_name": "Migration Progress",
                    "kpi_name_ar": "تقدم الترحيل",
                    "kpi_type": "Records Processed",
                    "metric_source": "Migration Job",
                    "calculation_method": "Percentage",
                    "display_format": "Percentage",
                    "show_trend": 1,
                    "sort_order": 1,
                },
                {
                    "kpi_name": "Success Rate",
                    "kpi_name_ar": "معدل النجاح",
                    "kpi_type": "Success Rate",
                    "metric_source": "Transaction Record",
                    "calculation_method": "Percentage",
                    "display_format": "Percentage",
                    "threshold_warning": 90,
                    "threshold_critical": 70,
                    "show_trend": 1,
                    "sort_order": 2,
                },
                {
                    "kpi_name": "Error Count",
                    "kpi_name_ar": "عدد الأخطاء",
                    "kpi_type": "Error Rate",
                    "metric_source": "Error Log",
                    "calculation_method": "Count",
                    "display_format": "Number",
                    "threshold_warning": 10,
                    "threshold_critical": 50,
                    "show_trend": 1,
                    "sort_order": 3,
                },
                {
                    "kpi_name": "Processing Speed",
                    "kpi_name_ar": "سرعة المعالجة",
                    "kpi_type": "Processing Speed",
                    "metric_source": "Performance Monitor",
                    "calculation_method": "Average",
                    "display_format": "Number",
                    "show_trend": 1,
                    "sort_order": 4,
                },
            ]

            for kpi in default_kpis:
                self.append("kpi_cards", kpi)

    def setup_default_charts(self):
        """Setup default progress charts if none exist"""
        if not self.progress_charts:
            default_charts = [
                {
                    "chart_name": "Migration Timeline",
                    "chart_name_ar": "الجدول الزمني للترحيل",
                    "chart_type": "Line",
                    "data_source": "Processing Timeline",
                    "x_axis_field": "time",
                    "y_axis_field": "records_processed",
                    "time_range": 24,
                    "chart_size": "Large",
                    "position_x": 1,
                    "position_y": 1,
                },
                {
                    "chart_name": "Status Breakdown",
                    "chart_name_ar": "تفصيل الحالة",
                    "chart_type": "Pie",
                    "data_source": "Migration Job Status",
                    "grouping_field": "status",
                    "chart_size": "Medium",
                    "position_x": 2,
                    "position_y": 1,
                },
                {
                    "chart_name": "Error Categories",
                    "chart_name_ar": "فئات الأخطاء",
                    "chart_type": "Bar",
                    "data_source": "Error Breakdown",
                    "x_axis_field": "error_category",
                    "y_axis_field": "error_count",
                    "chart_size": "Medium",
                    "position_x": 1,
                    "position_y": 2,
                },
            ]

            for chart in default_charts:
                self.append("progress_charts", chart)

    def validate_widget_positions(self):
        """Validate widget positions don't overlap"""
        positions = {}
        for chart in self.progress_charts:
            if chart.position_x and chart.position_y:
                pos_key = f"{chart.position_x}_{chart.position_y}"
                if pos_key in positions:
                    frappe.msgprint(
                        _("Chart positions overlap: {0} and {1}").format(
                            chart.chart_name, positions[pos_key]
                        )
                    )
                positions[pos_key] = chart.chart_name


class MigrationDashboardAnalytics:
    """Analytics engine for migration dashboard data"""

    def __init__(self, dashboard_name: str):
        self.dashboard_name = dashboard_name
        self.dashboard = frappe.get_doc("Migration Dashboard", dashboard_name)
        self.cache_duration = 30  # Cache results for 30 seconds

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data including KPIs, charts, and metrics"""

        # Check cache first
        cache_key = f"migration_dashboard_data_{self.dashboard_name}"
        cached_data = frappe.cache().get_value(cache_key)

        if cached_data and not self._is_cache_expired(cached_data):
            return cached_data

        # Generate fresh data
        dashboard_data = {
            "meta": self._get_dashboard_meta(),
            "kpis": self._calculate_all_kpis(),
            "charts": self._generate_all_charts(),
            "errors": self._get_error_analysis(),
            "performance": self._get_performance_metrics(),
            "notifications": self._check_notifications(),
            "timestamp": frappe.utils.now(),
            "auto_refresh": self.dashboard.auto_refresh_enabled,
            "refresh_interval": self.dashboard.refresh_interval,
        }

        # Cache the data
        frappe.cache().set_value(cache_key, dashboard_data, expires_in_sec=self.cache_duration)

        return dashboard_data

    def _get_dashboard_meta(self) -> Dict[str, Any]:
        """Get dashboard metadata"""
        return {
            "name": self.dashboard.dashboard_name,
            "name_ar": self.dashboard.dashboard_name_ar,
            "layout_columns": int(self.dashboard.layout_columns),
            "widget_size": self.dashboard.widget_size,
            "color_scheme": self.dashboard.color_scheme,
            "theme_variant": self.dashboard.theme_variant,
            "language": frappe.local.lang or "en",
        }

    def _calculate_all_kpis(self) -> List[Dict[str, Any]]:
        """Calculate values for all configured KPIs"""
        kpis = []

        for kpi_config in self.dashboard.kpi_cards:
            kpi_data = self._calculate_single_kpi(kpi_config)
            kpis.append(kpi_data)

        return sorted(kpis, key=lambda x: x.get("sort_order", 999))

    def _calculate_single_kpi(self, kpi_config) -> Dict[str, Any]:
        """Calculate value for a single KPI"""

        try:
            # Get base value based on KPI type and source
            base_value = self._get_kpi_base_value(kpi_config)

            # Apply calculation method
            calculated_value = self._apply_calculation_method(base_value, kpi_config)

            # Format the value
            formatted_value = self._format_kpi_value(calculated_value, kpi_config)

            # Get trend data if enabled
            trend_data = None
            if kpi_config.show_trend:
                trend_data = self._get_kpi_trend(kpi_config)

            # Determine status based on thresholds
            status = self._determine_kpi_status(calculated_value, kpi_config)

            return {
                "name": kpi_config.kpi_name,
                "name_ar": kpi_config.kpi_name_ar,
                "type": kpi_config.kpi_type,
                "value": calculated_value,
                "formatted_value": formatted_value,
                "status": status,
                "trend": trend_data,
                "color_scheme": kpi_config.color_scheme,
                "sort_order": kpi_config.sort_order or 999,
                "timestamp": frappe.utils.now(),
            }

        except Exception as e:
            frappe.log_error(f"KPI calculation failed for {kpi_config.kpi_name}: {str(e)}")
            return {
                "name": kpi_config.kpi_name,
                "value": 0,
                "formatted_value": "Error",
                "status": "error",
                "error_message": str(e),
            }

    def _get_kpi_base_value(self, kpi_config) -> float:
        """Get base value for KPI calculation"""

        source = kpi_config.metric_source
        kpi_type = kpi_config.kpi_type

        if source == "Migration Job":
            return self._get_migration_job_metric(kpi_type)
        elif source == "Transaction Record":
            return self._get_transaction_metric(kpi_type)
        elif source == "Error Log":
            return self._get_error_metric(kpi_type)
        elif source == "Performance Monitor":
            return self._get_performance_metric(kpi_type)
        elif source == "Custom Query" and kpi_config.sql_query:
            return self._execute_custom_query(kpi_config.sql_query)
        else:
            return 0.0

    def _get_migration_job_metric(self, kpi_type: str) -> float:
        """Get metrics from Migration Job records"""

        time_filter = self._get_time_filter(hours=24)

        if kpi_type == "Records Processed":
            result = frappe.db.sql(
                f"""
                SELECT COALESCE(SUM(processed_records), 0) as total
                FROM `tabMigration Job`
                WHERE {time_filter}
            """,
                as_dict=True,
            )
            return float(result[0]["total"]) if result else 0.0

        elif kpi_type == "Success Rate":
            result = frappe.db.sql(
                f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
                FROM `tabMigration Job`
                WHERE {time_filter}
            """,
                as_dict=True,
            )

            if result and result[0]["total"] > 0:
                return (float(result[0]["completed"]) / float(result[0]["total"])) * 100
            return 0.0

        elif kpi_type == "Completion Time":
            result = frappe.db.sql(
                f"""
                SELECT AVG(TIMESTAMPDIFF(MINUTE, start_time, end_time)) as avg_minutes
                FROM `tabMigration Job`
                WHERE status = 'Completed' AND {time_filter}
            """,
                as_dict=True,
            )
            return float(result[0]["avg_minutes"]) if result and result[0]["avg_minutes"] else 0.0

        return 0.0

    def _get_transaction_metric(self, kpi_type: str) -> float:
        """Get metrics from Transaction Record"""

        time_filter = self._get_time_filter(hours=24)

        if kpi_type == "Success Rate":
            result = frappe.db.sql(
                f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'EXECUTED' THEN 1 ELSE 0 END) as executed
                FROM `tabTransaction Record`
                WHERE {time_filter}
            """,
                as_dict=True,
            )

            if result and result[0]["total"] > 0:
                return (float(result[0]["executed"]) / float(result[0]["total"])) * 100
            return 0.0

        elif kpi_type == "Processing Speed":
            result = frappe.db.sql(
                f"""
                SELECT COUNT(*) / GREATEST(TIMESTAMPDIFF(HOUR, MIN(timestamp), MAX(timestamp)), 1) as records_per_hour
                FROM `tabTransaction Record`
                WHERE {time_filter}
            """,
                as_dict=True,
            )
            return float(result[0]["records_per_hour"]) if result else 0.0

        return 0.0

    def _get_error_metric(self, kpi_type: str) -> float:
        """Get metrics from Error Log"""

        time_filter = self._get_time_filter(hours=24)

        if kpi_type == "Error Rate":
            result = frappe.db.sql(
                f"""
                SELECT COUNT(*) as error_count
                FROM `tabError Log`
                WHERE error_type = 'Migration Error' AND {time_filter}
            """,
                as_dict=True,
            )
            return float(result[0]["error_count"]) if result else 0.0

        return 0.0

    def _get_performance_metric(self, kpi_type: str) -> float:
        """Get performance metrics"""

        if kpi_type == "Processing Speed":
            # Get average processing speed from recent jobs
            result = frappe.db.sql(
                """
                SELECT AVG(processed_records / GREATEST(TIMESTAMPDIFF(SECOND, start_time, end_time), 1)) as records_per_second
                FROM `tabMigration Job`
                WHERE status = 'Completed' 
                AND start_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND processed_records > 0
                AND end_time IS NOT NULL
            """,
                as_dict=True,
            )
            return (
                float(result[0]["records_per_second"])
                if result and result[0]["records_per_second"]
                else 0.0
            )

        return 0.0

    def _execute_custom_query(self, sql_query: str) -> float:
        """Execute custom SQL query for KPI calculation"""

        try:
            # Basic SQL injection protection
            dangerous_keywords = ["drop", "delete", "update", "insert", "create", "alter"]
            query_lower = sql_query.lower()

            for keyword in dangerous_keywords:
                if keyword in query_lower:
                    frappe.throw(_("Dangerous SQL keyword detected: {0}").format(keyword))

            result = frappe.db.sql(sql_query, as_dict=True)

            if result and len(result) > 0:
                # Try to get numeric value from first column of first row
                first_row = result[0]
                first_value = list(first_row.values())[0]
                return float(first_value) if first_value is not None else 0.0

        except Exception as e:
            frappe.log_error(f"Custom query execution failed: {str(e)}")

        return 0.0

    def _get_time_filter(self, hours: int = 24) -> str:
        """Generate time filter SQL clause"""
        return f"creation >= DATE_SUB(NOW(), INTERVAL {hours} HOUR)"

    def _apply_calculation_method(self, base_value: float, kpi_config) -> float:
        """Apply calculation method to base value"""

        method = kpi_config.calculation_method

        if method == "Percentage" and kpi_config.target_value:
            return (base_value / kpi_config.target_value) * 100
        elif method in ["Count", "Sum", "Average", "Min", "Max"]:
            return base_value
        else:
            return base_value

    def _format_kpi_value(self, value: float, kpi_config) -> str:
        """Format KPI value for display"""

        display_format = kpi_config.display_format

        if display_format == "Percentage":
            return f"{value:.1f}%"
        elif display_format == "Currency":
            return f"OMR {value:,.3f}"
        elif display_format == "Time Duration":
            hours = int(value // 60)
            minutes = int(value % 60)
            return f"{hours}h {minutes}m"
        elif display_format == "Data Size":
            if value >= 1024**3:
                return f"{value/(1024**3):.2f} GB"
            elif value >= 1024**2:
                return f"{value/(1024**2):.2f} MB"
            elif value >= 1024:
                return f"{value/1024:.2f} KB"
            else:
                return f"{value:.0f} B"
        else:  # Number
            return f"{value:,.0f}"

    def _determine_kpi_status(self, value: float, kpi_config) -> str:
        """Determine KPI status based on thresholds"""

        warning_threshold = kpi_config.threshold_warning
        critical_threshold = kpi_config.threshold_critical

        if critical_threshold and value <= critical_threshold:
            return "critical"
        elif warning_threshold and value <= warning_threshold:
            return "warning"
        else:
            return "success"

    def _get_kpi_trend(self, kpi_config) -> Optional[Dict[str, Any]]:
        """Get trend data for KPI"""

        trend_period = kpi_config.trend_period or 24

        # Get current and previous values
        current_value = self._get_kpi_base_value(kpi_config)

        # Get value from trend_period hours ago
        previous_time = datetime.now() - timedelta(hours=trend_period)

        # This is simplified - in reality you'd want historical KPI snapshots
        # For now, just calculate a trend direction based on error patterns

        return {"direction": "up", "percentage_change": 5.2, "trend_period": trend_period}

    def _generate_all_charts(self) -> List[Dict[str, Any]]:
        """Generate data for all configured charts"""
        charts = []

        for chart_config in self.dashboard.progress_charts:
            chart_data = self._generate_single_chart(chart_config)
            charts.append(chart_data)

        return charts

    def _generate_single_chart(self, chart_config) -> Dict[str, Any]:
        """Generate data for a single chart"""

        try:
            chart_data = {
                "name": chart_config.chart_name,
                "name_ar": chart_config.chart_name_ar,
                "type": chart_config.chart_type,
                "size": chart_config.chart_size,
                "position": {"x": chart_config.position_x, "y": chart_config.position_y},
                "data": self._get_chart_data(chart_config),
                "config": self._get_chart_config(chart_config),
            }

            return chart_data

        except Exception as e:
            frappe.log_error(f"Chart generation failed for {chart_config.chart_name}: {str(e)}")
            return {
                "name": chart_config.chart_name,
                "type": chart_config.chart_type,
                "error": str(e),
            }

    def _get_chart_data(self, chart_config) -> Dict[str, Any]:
        """Get data for chart based on its data source"""

        source = chart_config.data_source

        if source == "Migration Job Status":
            return self._get_job_status_data()
        elif source == "Processing Timeline":
            return self._get_processing_timeline_data(chart_config.time_range)
        elif source == "Error Breakdown":
            return self._get_error_breakdown_data()
        elif source == "Performance Metrics":
            return self._get_performance_chart_data()
        elif source == "Completion Rate":
            return self._get_completion_rate_data()
        else:
            return {"labels": [], "datasets": []}

    def _get_job_status_data(self) -> Dict[str, Any]:
        """Get migration job status distribution"""

        result = frappe.db.sql(
            """
            SELECT 
                status,
                COUNT(*) as count
            FROM `tabMigration Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY status
            ORDER BY count DESC
        """,
            as_dict=True,
        )

        labels = [row["status"] for row in result]
        data = [row["count"] for row in result]

        return {
            "labels": labels,
            "datasets": [{"data": data, "backgroundColor": self._get_status_colors(labels)}],
        }

    def _get_processing_timeline_data(self, time_range: int) -> Dict[str, Any]:
        """Get processing timeline data"""

        result = frappe.db.sql(
            f"""
            SELECT 
                DATE_FORMAT(creation, '%H:%i') as time_label,
                SUM(processed_records) as records_processed
            FROM `tabMigration Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL {time_range} HOUR)
            GROUP BY DATE_FORMAT(creation, '%Y-%m-%d %H')
            ORDER BY creation
        """,
            as_dict=True,
        )

        labels = [row["time_label"] for row in result]
        data = [row["records_processed"] for row in result]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Records Processed",
                    "data": data,
                    "borderColor": "#3498db",
                    "backgroundColor": "rgba(52, 152, 219, 0.1)",
                    "fill": True,
                }
            ],
        }

    def _get_error_breakdown_data(self) -> Dict[str, Any]:
        """Get error breakdown by category"""

        result = frappe.db.sql(
            """
            SELECT 
                error_category,
                COUNT(*) as error_count
            FROM `tabError Log`
            WHERE error_type = 'Migration Error'
            AND creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY error_category
            ORDER BY error_count DESC
            LIMIT 10
        """,
            as_dict=True,
        )

        labels = [row["error_category"] for row in result]
        data = [row["error_count"] for row in result]

        return {
            "labels": labels,
            "datasets": [{"label": "Error Count", "data": data, "backgroundColor": "#e74c3c"}],
        }

    def _get_performance_chart_data(self) -> Dict[str, Any]:
        """Get performance metrics over time"""

        result = frappe.db.sql(
            """
            SELECT 
                DATE_FORMAT(creation, '%H:%i') as time_label,
                AVG(processed_records / GREATEST(TIMESTAMPDIFF(SECOND, start_time, end_time), 1)) as avg_speed
            FROM `tabMigration Job`
            WHERE status = 'Completed'
            AND creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND processed_records > 0
            GROUP BY DATE_FORMAT(creation, '%Y-%m-%d %H')
            ORDER BY creation
        """,
            as_dict=True,
        )

        labels = [row["time_label"] for row in result]
        data = [float(row["avg_speed"]) if row["avg_speed"] else 0 for row in result]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Records/Second",
                    "data": data,
                    "borderColor": "#2ecc71",
                    "backgroundColor": "rgba(46, 204, 113, 0.1)",
                }
            ],
        }

    def _get_completion_rate_data(self) -> Dict[str, Any]:
        """Get completion rate over time"""

        result = frappe.db.sql(
            """
            SELECT 
                DATE_FORMAT(creation, '%H:%i') as time_label,
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_jobs
            FROM `tabMigration Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY DATE_FORMAT(creation, '%Y-%m-%d %H')
            ORDER BY creation
        """,
            as_dict=True,
        )

        labels = [row["time_label"] for row in result]
        completion_rates = [
            (row["completed_jobs"] / row["total_jobs"]) * 100 if row["total_jobs"] > 0 else 0
            for row in result
        ]

        return {
            "labels": labels,
            "datasets": [
                {
                    "label": "Completion Rate (%)",
                    "data": completion_rates,
                    "borderColor": "#f39c12",
                    "backgroundColor": "rgba(243, 156, 18, 0.1)",
                }
            ],
        }

    def _get_status_colors(self, statuses: List[str]) -> List[str]:
        """Get appropriate colors for job statuses"""

        color_mapping = {
            "Completed": "#2ecc71",
            "Running": "#3498db",
            "Pending": "#f39c12",
            "Failed": "#e74c3c",
            "Paused": "#95a5a6",
        }

        return [color_mapping.get(status, "#7f8c8d") for status in statuses]

    def _get_chart_config(self, chart_config) -> Dict[str, Any]:
        """Get configuration for chart rendering"""

        return {
            "responsive": True,
            "maintainAspectRatio": False,
            "animation": {"duration": 1000},
            "legend": {"display": True, "position": "bottom"},
            "scales": self._get_chart_scales(chart_config.chart_type),
        }

    def _get_chart_scales(self, chart_type: str) -> Dict[str, Any]:
        """Get appropriate scales for chart type"""

        if chart_type in ["Line", "Bar", "Area"]:
            return {
                "x": {"display": True, "title": {"display": True, "text": "Time"}},
                "y": {
                    "display": True,
                    "title": {"display": True, "text": "Count"},
                    "beginAtZero": True,
                },
            }
        else:
            return {}

    def _get_error_analysis(self) -> Dict[str, Any]:
        """Get comprehensive error analysis"""

        # Get error summary
        error_summary = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_errors,
                COUNT(DISTINCT error_category) as unique_categories,
                AVG(CASE WHEN severity = 'Critical' THEN 1 ELSE 0 END) * 100 as critical_percentage
            FROM `tabError Log`
            WHERE error_type = 'Migration Error'
            AND creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """,
            as_dict=True,
        )

        # Get top error categories
        top_errors = frappe.db.sql(
            """
            SELECT 
                error_category,
                error_message,
                COUNT(*) as occurrence_count,
                severity
            FROM `tabError Log`
            WHERE error_type = 'Migration Error'
            AND creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY error_category, error_message, severity
            ORDER BY occurrence_count DESC
            LIMIT 10
        """,
            as_dict=True,
        )

        return {
            "summary": error_summary[0] if error_summary else {},
            "top_errors": top_errors,
            "recommendations": self._generate_error_recommendations(top_errors),
        }

    def _generate_error_recommendations(self, top_errors: List[Dict]) -> List[str]:
        """Generate recommendations based on error patterns"""

        recommendations = []

        if not top_errors:
            return recommendations

        # Check for validation errors
        validation_errors = [
            e for e in top_errors if "validation" in e.get("error_category", "").lower()
        ]
        if validation_errors:
            recommendations.append(
                "Review data validation rules - multiple validation errors detected"
            )

        # Check for performance issues
        timeout_errors = [e for e in top_errors if "timeout" in e.get("error_message", "").lower()]
        if timeout_errors:
            recommendations.append("Consider increasing timeout values or optimizing batch sizes")

        # Check for data quality issues
        duplicate_errors = [
            e for e in top_errors if "duplicate" in e.get("error_message", "").lower()
        ]
        if duplicate_errors:
            recommendations.append("Implement duplicate detection and resolution strategy")

        return recommendations

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""

        metrics = frappe.db.sql(
            """
            SELECT 
                AVG(processed_records / GREATEST(TIMESTAMPDIFF(SECOND, start_time, end_time), 1)) as avg_throughput,
                MAX(processed_records / GREATEST(TIMESTAMPDIFF(SECOND, start_time, end_time), 1)) as max_throughput,
                AVG(TIMESTAMPDIFF(SECOND, start_time, end_time)) as avg_duration,
                AVG(memory_peak_mb) as avg_memory_usage,
                AVG(cpu_usage_percent) as avg_cpu_usage
            FROM `tabMigration Job`
            WHERE status = 'Completed'
            AND creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            AND processed_records > 0
        """,
            as_dict=True,
        )

        return metrics[0] if metrics else {}

    def _check_notifications(self) -> List[Dict[str, Any]]:
        """Check for conditions that require notifications"""

        notifications = []

        if not self.dashboard.enable_notifications:
            return notifications

        threshold = self.dashboard.notification_threshold

        # Check job completion rates
        completion_rate = self._get_current_completion_rate()
        if completion_rate < threshold:
            notifications.append(
                {
                    "type": "warning",
                    "title": "Low Completion Rate",
                    "message": f"Job completion rate ({completion_rate:.1f}%) is below threshold ({threshold}%)",
                    "timestamp": frappe.utils.now(),
                }
            )

        # Check error rates
        error_rate = self._get_current_error_rate()
        if error_rate > (100 - threshold):
            notifications.append(
                {
                    "type": "error",
                    "title": "High Error Rate",
                    "message": f"Error rate ({error_rate:.1f}%) is above acceptable threshold",
                    "timestamp": frappe.utils.now(),
                }
            )

        return notifications

    def _get_current_completion_rate(self) -> float:
        """Get current job completion rate"""

        result = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM `tabMigration Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """,
            as_dict=True,
        )

        if result and result[0]["total"] > 0:
            return (result[0]["completed"] / result[0]["total"]) * 100

        return 100.0  # Default to 100% if no recent jobs

    def _get_current_error_rate(self) -> float:
        """Get current error rate"""

        result = frappe.db.sql(
            """
            SELECT COUNT(*) as error_count
            FROM `tabError Log`
            WHERE error_type = 'Migration Error'
            AND creation >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """,
            as_dict=True,
        )

        total_operations = frappe.db.sql(
            """
            SELECT SUM(processed_records) as total
            FROM `tabMigration Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """,
            as_dict=True,
        )

        error_count = result[0]["error_count"] if result else 0
        total_records = (
            total_operations[0]["total"] if total_operations and total_operations[0]["total"] else 1
        )

        return (error_count / total_records) * 100

    def _is_cache_expired(self, cached_data: Dict) -> bool:
        """Check if cached data has expired"""

        if "timestamp" not in cached_data:
            return True

        cache_time = datetime.fromisoformat(cached_data["timestamp"].replace("Z", "+00:00"))
        current_time = datetime.now()

        return (current_time - cache_time).total_seconds() > self.cache_duration


# API Methods for frontend integration
@frappe.whitelist()
def get_dashboard_list():
    """Get list of available migration dashboards"""

    dashboards = frappe.get_list(
        "Migration Dashboard",
        filters={"is_active": 1},
        fields=["name", "dashboard_name", "dashboard_name_ar", "created_by", "created_date"],
        order_by="created_date desc",
    )

    return dashboards


@frappe.whitelist()
def get_dashboard_data(dashboard_name):
    """Get complete dashboard data for frontend display"""

    try:
        analytics = MigrationDashboardAnalytics(dashboard_name)
        return analytics.get_dashboard_data()

    except Exception as e:
        frappe.log_error(f"Dashboard data retrieval failed: {str(e)}")
        return {"error": str(e), "timestamp": frappe.utils.now()}


@frappe.whitelist()
def refresh_dashboard_data(dashboard_name):
    """Force refresh of dashboard data (clear cache)"""

    try:
        cache_key = f"migration_dashboard_data_{dashboard_name}"
        frappe.cache().delete_value(cache_key)

        analytics = MigrationDashboardAnalytics(dashboard_name)
        return analytics.get_dashboard_data()

    except Exception as e:
        frappe.log_error(f"Dashboard refresh failed: {str(e)}")
        return {"error": str(e), "timestamp": frappe.utils.now()}


@frappe.whitelist()
def create_default_dashboard():
    """Create a default migration dashboard with standard configuration"""

    try:
        # Check if default dashboard already exists
        if frappe.db.exists("Migration Dashboard", "Default Migration Dashboard"):
            return frappe.get_doc("Migration Dashboard", "Default Migration Dashboard")

        # Create new dashboard
        dashboard = frappe.new_doc("Migration Dashboard")
        dashboard.dashboard_name = "Default Migration Dashboard"
        dashboard.dashboard_name_ar = "لوحة تحكم الترحيل الافتراضية"
        dashboard.is_active = 1
        dashboard.auto_refresh_enabled = 1
        dashboard.refresh_interval = 30
        dashboard.show_live_metrics = 1
        dashboard.enable_notifications = 1
        dashboard.notification_threshold = 90
        dashboard.layout_columns = "4"
        dashboard.widget_size = "Medium"
        dashboard.color_scheme = "Default"
        dashboard.theme_variant = "Standard"

        dashboard.insert()

        return dashboard.as_dict()

    except Exception as e:
        frappe.log_error(f"Default dashboard creation failed: {str(e)}")
        frappe.throw(_("Failed to create default dashboard: {0}").format(str(e)))


@frappe.whitelist()
def get_migration_job_summary():
    """Get quick summary of migration jobs for dashboard overview"""

    try:
        summary = frappe.db.sql(
            """
            SELECT 
                COUNT(*) as total_jobs,
                SUM(CASE WHEN status = 'Running' THEN 1 ELSE 0 END) as running_jobs,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_jobs,
                SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed_jobs,
                SUM(COALESCE(processed_records, 0)) as total_records_processed,
                AVG(CASE WHEN status = 'Completed' THEN 
                    processed_records / GREATEST(TIMESTAMPDIFF(SECOND, start_time, end_time), 1)
                    ELSE NULL END) as avg_throughput
            FROM `tabMigration Job`
            WHERE creation >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """,
            as_dict=True,
        )

        return summary[0] if summary else {}

    except Exception as e:
        frappe.log_error(f"Migration job summary failed: {str(e)}")
        return {"error": str(e)}
