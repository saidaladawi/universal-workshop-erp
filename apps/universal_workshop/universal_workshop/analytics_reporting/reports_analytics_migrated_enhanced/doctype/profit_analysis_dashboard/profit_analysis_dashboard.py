# Copyright (c) 2025, Universal Workshop ERP and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, today, add_days, date_diff, get_datetime
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Optional, Tuple, Any


class ProfitAnalysisDashboard(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate dashboard data before saving"""
        self.validate_date_range()
        self.validate_analysis_period()
        self.validate_arabic_fields()

    def before_save(self):
        """Set default values and calculate metrics before saving"""
        self.set_default_values()
        self.calculate_all_metrics()
        self.update_audit_trail()

    def after_insert(self):
        """Actions after dashboard creation"""
        self.generate_initial_report()
        self.log_dashboard_creation()

    def validate_date_range(self):
        """Validate date range is logical"""
        if self.from_date and self.to_date:
            if getdate(self.from_date) > getdate(self.to_date):
                frappe.throw(_("From Date cannot be greater than To Date"))

            # Check if date range is reasonable (not more than 5 years)
            date_diff_days = date_diff(self.to_date, self.from_date)
            if date_diff_days > 1825:  # 5 years
                frappe.throw(_("Date range cannot exceed 5 years"))

    def validate_analysis_period(self):
        """Validate analysis period matches date range"""
        if not self.analysis_period:
            self.analysis_period = "Monthly"

        # Auto-set date range based on analysis period if not provided
        if not self.from_date or not self.to_date:
            self.set_default_date_range()

    def validate_arabic_fields(self):
        """Validate Arabic field content and encoding"""
        arabic_fields = ["dashboard_name_ar", "dashboard_title_ar", "analysis_notes_ar"]

        for field in arabic_fields:
            if hasattr(self, field) and getattr(self, field):
                text = getattr(self, field)
                if not self.is_arabic_text(text):
                    continue  # Allow non-Arabic text

                # Validate Arabic text encoding
                try:
                    text.encode("utf-8")
                except UnicodeEncodeError:
                    frappe.throw(_("Invalid Arabic text encoding in field {0}").format(field))

    def is_arabic_text(self, text: str) -> bool:
        """Check if text contains Arabic characters"""
        if not text:
            return False
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
        )
        return bool(arabic_pattern.search(text))

    def set_default_values(self):
        """Set default values for dashboard"""
        if not self.created_by:
            self.created_by = frappe.session.user

        if not self.created_date:
            self.created_date = get_datetime()

        if not self.currency:
            self.currency = "OMR"  # Default to Omani Rial

        if not self.exchange_rate:
            self.exchange_rate = 1.0

        if not self.status:
            self.status = "Draft"

        self.last_updated = get_datetime()
        self.last_modified_by = frappe.session.user
        self.last_modified_timestamp = get_datetime()

    def set_default_date_range(self):
        """Set default date range based on analysis period"""
        today_date = getdate(today())

        if self.analysis_period == "Daily":
            self.from_date = today_date
            self.to_date = today_date
        elif self.analysis_period == "Weekly":
            self.from_date = add_days(today_date, -7)
            self.to_date = today_date
        elif self.analysis_period == "Monthly":
            self.from_date = today_date.replace(day=1)
            self.to_date = today_date
        elif self.analysis_period == "Quarterly":
            # Current quarter
            quarter_start = today_date.replace(month=((today_date.month - 1) // 3) * 3 + 1, day=1)
            self.from_date = quarter_start
            self.to_date = today_date
        elif self.analysis_period == "Yearly":
            self.from_date = today_date.replace(month=1, day=1)
            self.to_date = today_date

    def calculate_all_metrics(self):
        """Calculate all financial metrics and KPIs"""
        try:
            # Vehicle Analysis Metrics
            self.calculate_vehicle_metrics()

            # Parts Analysis Metrics
            self.calculate_parts_metrics()

            # Marketplace Analysis Metrics
            self.calculate_marketplace_metrics()

            # Financial Metrics
            self.calculate_financial_metrics()

            # Cost Breakdown
            self.calculate_cost_breakdown()

            # Performance Indicators
            self.calculate_performance_indicators()

            # Update status to Generated
            self.status = "Generated"

        except Exception as e:
            frappe.log_error(f"Error calculating metrics for dashboard {self.name}: {str(e)}")
            frappe.throw(_("Error calculating dashboard metrics: {0}").format(str(e)))

    def calculate_vehicle_metrics(self):
        """Calculate vehicle-related metrics"""
        # Get all scrap vehicles in date range
        vehicles = frappe.get_list(
            "Scrap Vehicle",
            filters={
                "assessment_date": ["between", [self.from_date, self.to_date]],
                "docstatus": ["!=", 2],  # Not cancelled
            },
            fields=[
                "name",
                "total_acquisition_cost",
                "total_processing_cost",
                "total_revenue",
                "status",
                "assessment_date",
                "completion_date",
            ],
        )

        self.total_vehicles_processed = len(vehicles)
        self.vehicles_in_progress = len(
            [v for v in vehicles if v.status in ["In Progress", "Assessment", "Dismantling"]]
        )
        self.vehicles_completed = len([v for v in vehicles if v.status == "Completed"])

        # Calculate financial totals
        self.total_acquisition_cost = sum(flt(v.total_acquisition_cost) for v in vehicles)
        self.total_processing_cost = sum(flt(v.total_processing_cost) for v in vehicles)
        self.total_revenue_generated = sum(flt(v.total_revenue) for v in vehicles)

        # Calculate profit margins
        self.gross_profit = flt(self.total_revenue_generated) - flt(self.total_acquisition_cost)
        if flt(self.total_revenue_generated) > 0:
            self.gross_profit_margin = (
                flt(self.gross_profit) / flt(self.total_revenue_generated)
            ) * 100
        else:
            self.gross_profit_margin = 0

        self.net_profit = flt(self.gross_profit) - flt(self.total_processing_cost)
        if flt(self.total_revenue_generated) > 0:
            self.net_profit_margin = (
                flt(self.net_profit) / flt(self.total_revenue_generated)
            ) * 100
        else:
            self.net_profit_margin = 0

        # Calculate average ROI per vehicle
        total_investment = flt(self.total_acquisition_cost) + flt(self.total_processing_cost)
        if total_investment > 0 and self.total_vehicles_processed > 0:
            vehicle_roi = (flt(self.net_profit) / total_investment) * 100
            self.average_roi_per_vehicle = vehicle_roi / self.total_vehicles_processed
        else:
            self.average_roi_per_vehicle = 0

        # Find best and worst performing vehicles
        self.find_best_worst_vehicles(vehicles)

        # Calculate average processing time
        completed_vehicles = [v for v in vehicles if v.completion_date and v.assessment_date]
        if completed_vehicles:
            total_days = sum(
                date_diff(v.completion_date, v.assessment_date) for v in completed_vehicles
            )
            self.average_processing_time = total_days / len(completed_vehicles)
        else:
            self.average_processing_time = 0

    def find_best_worst_vehicles(self, vehicles: List[Dict]):
        """Find best and worst performing vehicles by ROI"""
        vehicle_performance = []

        for vehicle in vehicles:
            if vehicle.total_revenue and vehicle.total_acquisition_cost:
                total_cost = flt(vehicle.total_acquisition_cost) + flt(
                    vehicle.total_processing_cost or 0
                )
                if total_cost > 0:
                    roi = ((flt(vehicle.total_revenue) - total_cost) / total_cost) * 100
                    vehicle_performance.append({"name": vehicle.name, "roi": roi})

        if vehicle_performance:
            # Sort by ROI
            vehicle_performance.sort(key=lambda x: x["roi"], reverse=True)
            self.best_performing_vehicle = vehicle_performance[0]["name"]
            self.worst_performing_vehicle = vehicle_performance[-1]["name"]
