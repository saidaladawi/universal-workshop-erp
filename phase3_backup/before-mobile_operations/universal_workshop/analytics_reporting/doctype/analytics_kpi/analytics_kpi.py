# pylint: disable=no-member
"""Analytics KPI DocType Controller

This module provides KPI calculation, validation, and trend analysis functionality
for the Universal Workshop ERP analytics dashboard.
"""

import json
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, now_datetime
from datetime import datetime, timedelta


class AnalyticsKPI(Document):
    """Controller for Analytics KPI DocType"""

    def validate(self):
        """Validate KPI configuration before saving"""
        self.validate_kpi_code()
        self.validate_data_source()
        self.calculate_percentage_change()
        self.determine_trend_direction()
        self.determine_status()

    def before_save(self):
        """Set metadata before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        self.last_updated_by = frappe.session.user

    def validate_kpi_code(self):
        """Validate KPI code format and uniqueness"""
        if not self.kpi_code:
            frappe.throw(_("KPI Code is required"))

        # Ensure uppercase and underscore format
        if not self.kpi_code.replace("_", "").replace("-", "").isalnum():
            frappe.throw(
                _("KPI Code must contain only alphanumeric characters, underscores, and hyphens")
            )

    def validate_data_source(self):
        """Validate data source configuration"""
        if self.calculation_type == "Simple Aggregation":
            if not self.source_doctype:
                frappe.throw(_("Source DocType is required for Simple Aggregation"))
            if not self.source_field:
                frappe.throw(_("Source Field is required for Simple Aggregation"))
            if not self.aggregation_function:
                frappe.throw(_("Aggregation Function is required for Simple Aggregation"))

        elif self.calculation_type == "Custom Formula" and not self.calculation_script:
            frappe.throw(_("Calculation Script is required for Custom Formula"))

    def calculate_percentage_change(self):
        """Calculate percentage change from previous value"""
        if self.previous_value and self.current_value is not None:
            if self.previous_value != 0:
                change = (
                    (self.current_value - self.previous_value) / abs(self.previous_value)
                ) * 100
                self.percentage_change = flt(change, 2)
            else:
                self.percentage_change = 100.0 if self.current_value > 0 else 0.0
        else:
            self.percentage_change = 0.0

    def determine_trend_direction(self):
        """Determine trend direction based on value changes"""
        if self.current_value is not None and self.previous_value is not None:
            if self.current_value > self.previous_value:
                self.trend_direction = "Up"
            elif self.current_value < self.previous_value:
                self.trend_direction = "Down"
            else:
                self.trend_direction = "Stable"
        else:
            self.trend_direction = "Stable"

    def determine_status(self):
        """Determine status based on target value"""
        if not self.target_value or self.current_value is None:
            self.status = "No Target"
            return

        # Define tolerance (5% of target)
        tolerance = abs(self.target_value * 0.05)

        if abs(self.current_value - self.target_value) <= tolerance:
            self.status = "On Target"
        elif self.current_value > self.target_value:
            self.status = "Above Target"
        else:
            self.status = "Below Target"

    def calculate_kpi_value(self):
        """Calculate KPI value based on configuration"""
        try:
            if self.calculation_type == "Simple Aggregation":
                return self._calculate_simple_aggregation()
            elif self.calculation_type == "Custom Formula":
                return self._execute_custom_calculation()
            elif self.calculation_type == "Manual Entry":
                return self.current_value  # Manual entry, no calculation needed
            else:
                frappe.throw(_("Unsupported calculation type: {0}").format(self.calculation_type))

        except Exception as e:
            frappe.log_error(
                f"Error calculating KPI {self.kpi_code}: {str(e)}", "KPI Calculation Error"
            )
            frappe.throw(_("Error calculating KPI: {0}").format(str(e)))

    def _calculate_simple_aggregation(self):
        """Calculate KPI using simple aggregation"""
        if not self.source_doctype or not self.source_field:
            return 0

        # Parse filters
        filters = {}
        if self.filters_json:
            try:
                filters = json.loads(self.filters_json)
            except json.JSONDecodeError:
                frappe.log_error(
                    f"Invalid JSON in filters for KPI {self.kpi_code}", "KPI Filter Error"
                )

        # Build query based on aggregation function
        if self.aggregation_function == "COUNT":
            result = frappe.db.count(self.source_doctype, filters)
        else:
            sql_function = {"SUM": "SUM", "AVG": "AVG", "MAX": "MAX", "MIN": "MIN"}.get(
                self.aggregation_function, "SUM"
            )

            # Build filter conditions
            conditions = []
            values = []

            for field, value in filters.items():
                conditions.append(f"`{field}` = %s")
                values.append(value)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT {sql_function}(`{self.source_field}`) as value
                FROM `tab{self.source_doctype}`
                WHERE {where_clause}
            """

            result = frappe.db.sql(query, values, as_dict=True)
            result = result[0].get("value", 0) if result else 0

        return flt(result, 3)

    def _execute_custom_calculation(self):
        """Execute custom Python calculation script"""
        if not self.calculation_script:
            return 0

        # Create safe execution context
        context = {
            "frappe": frappe,
            "flt": flt,
            "cint": cint,
            "datetime": datetime,
            "timedelta": timedelta,
            "json": json,
            "kpi": self,
            "result": 0,
        }

        # Execute the custom script
        exec(self.calculation_script, context)

        return flt(context.get("result", 0), 3)

    def update_kpi_value(self):
        """Update KPI value and save historical data"""
        # Store current value as previous
        if self.current_value is not None:
            self.previous_value = self.current_value

        # Calculate new value
        new_value = self.calculate_kpi_value()
        self.current_value = new_value

        # Update calculation timestamp
        self.last_calculated = now_datetime()

        # Trigger validation to recalculate trends and status
        self.validate()

        # Save the document
        self.save()

        # Create historical snapshot
        self._create_historical_snapshot()

        return new_value

    def _create_historical_snapshot(self):
        """Create historical snapshot for trend analysis"""
        snapshot = frappe.new_doc("Analytics KPI History")
        snapshot.kpi_code = self.kpi_code
        snapshot.kpi_name = self.kpi_name
        snapshot.recorded_value = self.current_value
        snapshot.target_value = self.target_value
        snapshot.percentage_change = self.percentage_change
        snapshot.trend_direction = self.trend_direction
        snapshot.status = self.status
        snapshot.recorded_date = now_datetime()
        snapshot.insert()

    def get_historical_data(self, days=30):
        """Get historical KPI data for trend analysis"""
        from_date = datetime.now() - timedelta(days=days)

        return frappe.get_list(
            "Analytics KPI History",
            filters={"kpi_code": self.kpi_code, "recorded_date": [">=", from_date]},
            fields=["recorded_date", "recorded_value", "target_value", "status"],
            order_by="recorded_date asc",
        )


@frappe.whitelist()
def update_all_kpis():
    """Update all active KPIs - can be called via scheduler"""
    active_kpis = frappe.get_list("Analytics KPI", filters={"is_active": 1}, fields=["name"])

    results = []
    for kpi_name in active_kpis:
        try:
            kpi = frappe.get_doc("Analytics KPI", kpi_name.name)
            new_value = kpi.update_kpi_value()
            results.append({"kpi_code": kpi.kpi_code, "status": "success", "value": new_value})
        except Exception as e:
            frappe.log_error(f"Error updating KPI {kpi_name.name}: {str(e)}", "KPI Update Error")
            results.append({"kpi_code": kpi_name.name, "status": "error", "error": str(e)})

    return results


@frappe.whitelist()
def get_kpi_dashboard_data(category=None, limit=20):
    """Get KPI data for dashboard display"""
    filters = {"is_active": 1}
    if category:
        filters["kpi_category"] = category

    kpis = frappe.get_list(
        "Analytics KPI",
        filters=filters,
        fields=[
            "name",
            "kpi_code",
            "kpi_name",
            "kpi_name_ar",
            "kpi_category",
            "current_value",
            "target_value",
            "percentage_change",
            "trend_direction",
            "status",
            "last_calculated",
        ],
        order_by="kpi_category, kpi_name",
        limit=limit,
    )

    return kpis


@frappe.whitelist()
def get_kpi_trend_data(kpi_code, days=30):
    """Get KPI trend data for charts"""
    kpi = frappe.get_doc("Analytics KPI", {"kpi_code": kpi_code})
    return kpi.get_historical_data(days)
