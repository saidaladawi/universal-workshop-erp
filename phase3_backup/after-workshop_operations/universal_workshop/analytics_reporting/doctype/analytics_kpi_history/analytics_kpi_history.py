# pylint: disable=no-member
"""Analytics KPI History DocType Controller

This module provides historical KPI data storage and retrieval functionality
for trend analysis and reporting in the analytics dashboard.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class AnalyticsKPIHistory(Document):
    """Controller for Analytics KPI History DocType"""

    def validate(self):
        """Validate KPI history record before saving"""
        self.validate_kpi_reference()
        self.set_kpi_name()
        self.calculate_variance_from_target()

    def before_save(self):
        """Set calculated fields before saving"""
        self.set_aggregation_period()

    def validate_kpi_reference(self):
        """Validate that KPI reference exists and is active"""
        if not self.kpi_code:
            frappe.throw(_("KPI Code is required"))

        # Verify KPI exists
        if not frappe.db.exists("Analytics KPI", self.kpi_code):
            frappe.throw(_("KPI {0} does not exist").format(self.kpi_code))

    def set_kpi_name(self):
        """Set KPI name from referenced Analytics KPI"""
        if self.kpi_code:
            kpi_name = frappe.db.get_value("Analytics KPI", self.kpi_code, "kpi_name")
            if kpi_name:
                self.kpi_name = kpi_name

    def calculate_variance_from_target(self):
        """Calculate variance from target value"""
        if self.target_value and self.recorded_value is not None:
            self.variance_from_target = flt(self.recorded_value - self.target_value, 3)
        else:
            self.variance_from_target = 0.0

    def set_aggregation_period(self):
        """Set human-readable aggregation period"""
        if not self.aggregation_period and self.recorded_date:
            from datetime import datetime

            date_obj = self.recorded_date
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d %H:%M:%S")

            period_formats = {
                "Hourly": date_obj.strftime("%Y-%m-%d %H:00"),
                "Daily": date_obj.strftime("%Y-%m-%d"),
                "Weekly": f"Week {date_obj.isocalendar().week} {date_obj.year}",
                "Monthly": date_obj.strftime("%B %Y"),
                "Quarterly": f"Q{((date_obj.month-1)//3)+1} {date_obj.year}",
                "Yearly": str(date_obj.year),
            }

            self.aggregation_period = period_formats.get(
                self.period_type, date_obj.strftime("%Y-%m-%d")
            )


@frappe.whitelist()
def get_kpi_trend_analysis(kpi_code, period_type="Daily", limit=30):
    """Get KPI trend analysis data for charts and reporting"""

    if not frappe.db.exists("Analytics KPI", kpi_code):
        frappe.throw(_("KPI {0} does not exist").format(kpi_code))

    # Get historical data
    historical_data = frappe.get_list(
        "Analytics KPI History",
        filters={"kpi_code": kpi_code, "period_type": period_type},
        fields=[
            "recorded_date",
            "recorded_value",
            "target_value",
            "percentage_change",
            "trend_direction",
            "status",
            "variance_from_target",
            "aggregation_period",
        ],
        order_by="recorded_date desc",
        limit=limit,
    )

    if not historical_data:
        return {"kpi_code": kpi_code, "message": "No historical data available", "data": []}

    # Reverse to get chronological order for charts
    historical_data.reverse()

    # Calculate additional metrics
    values = [d["recorded_value"] for d in historical_data if d["recorded_value"] is not None]

    analysis = {
        "kpi_code": kpi_code,
        "period_type": period_type,
        "data_points": len(historical_data),
        "data": historical_data,
        "statistics": {
            "min_value": min(values) if values else 0,
            "max_value": max(values) if values else 0,
            "avg_value": flt(sum(values) / len(values), 3) if values else 0,
            "latest_value": values[-1] if values else 0,
            "trend": _calculate_overall_trend(values),
        },
    }

    return analysis


def _calculate_overall_trend(values):
    """Calculate overall trend from a series of values"""
    if len(values) < 2:
        return "Insufficient Data"

    # Simple linear trend calculation
    first_half_avg = sum(values[: len(values) // 2]) / (len(values) // 2)
    second_half_avg = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)

    if second_half_avg > first_half_avg * 1.05:  # 5% threshold
        return "Improving"
    elif second_half_avg < first_half_avg * 0.95:  # 5% threshold
        return "Declining"
    else:
        return "Stable"


@frappe.whitelist()
def get_kpi_performance_summary(kpi_codes=None, date_range=None):
    """Get performance summary for multiple KPIs"""

    filters = {}

    if kpi_codes:
        if isinstance(kpi_codes, str):
            kpi_codes = [code.strip() for code in kpi_codes.split(",")]
        filters["kpi_code"] = ["in", kpi_codes]

    if date_range:
        filters["recorded_date"] = date_range

    # Get latest record for each KPI
    latest_records = frappe.db.sql(
        """
        SELECT 
            kpi_code,
            kpi_name,
            recorded_value,
            target_value,
            percentage_change,
            trend_direction,
            status,
            recorded_date
        FROM `tabAnalytics KPI History` h1
        WHERE recorded_date = (
            SELECT MAX(recorded_date) 
            FROM `tabAnalytics KPI History` h2 
            WHERE h2.kpi_code = h1.kpi_code
            {date_filter}
        )
        {kpi_filter}
        ORDER BY kpi_code
    """.format(
            date_filter=(
                f"AND recorded_date {date_range[0]} '{date_range[1]}'" if date_range else ""
            ),
            kpi_filter=(
                f"AND kpi_code IN ({','.join(['%s'] * len(kpi_codes))})" if kpi_codes else ""
            ),
        ),
        kpi_codes if kpi_codes else [],
        as_dict=True,
    )

    return {
        "summary": latest_records,
        "total_kpis": len(latest_records),
        "on_target": len([r for r in latest_records if r.status == "On Target"]),
        "above_target": len([r for r in latest_records if r.status == "Above Target"]),
        "below_target": len([r for r in latest_records if r.status == "Below Target"]),
    }


@frappe.whitelist()
def cleanup_old_history(retention_days=365):
    """Clean up old KPI history records beyond retention period"""

    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=retention_days)

    # Count records to be deleted
    old_records_count = frappe.db.count(
        "Analytics KPI History", {"recorded_date": ["<", cutoff_date]}
    )

    if old_records_count == 0:
        return {"message": "No old records to clean up", "deleted_count": 0}

    # Delete old records
    frappe.db.delete("Analytics KPI History", {"recorded_date": ["<", cutoff_date]})

    frappe.db.commit()

    return {
        "message": f"Successfully cleaned up {old_records_count} old KPI history records",
        "deleted_count": old_records_count,
        "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
    }
