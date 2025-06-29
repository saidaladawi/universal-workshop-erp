# Copyright (c) 2025, Said Al-Adawi and contributors
# For license information, please see license.txt
# pylint: disable=no-member,access-member-before-definition
# Frappe framework dynamically adds DocType fields to Document class

from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time, now_datetime, add_days, flt


class ServiceBay(Document):
    def validate(self):
        """Validate service bay data"""
        self.validate_arabic_name()
        self.validate_operating_hours()
        self.validate_capacity()

    def validate_arabic_name(self):
        """Ensure Arabic name is provided"""
        if not self.bay_name_ar:
            # Auto-translate common bay types
            translations = {
                "General Service": "خدمة عامة",
                "Engine Repair": "إصلاح المحرك",
                "Transmission Repair": "إصلاح ناقل الحركة",
                "Bodywork": "أعمال الهيكل",
                "Painting": "الطلاء",
                "Electrical": "الكهرباء",
                "Tire Service": "خدمة الإطارات",
                "Quick Service": "خدمة سريعة",
            }

            if self.bay_name in translations:
                self.bay_name_ar = translations[self.bay_name]
            else:
                frappe.throw(_("Arabic bay name is required"))

    def validate_operating_hours(self):
        """Validate operating hours"""
        if self.operating_hours_start and self.operating_hours_end:
            start_time = get_time(self.operating_hours_start)
            end_time = get_time(self.operating_hours_end)

            if start_time >= end_time:
                frappe.throw(_("Operating hours end time must be after start time"))

    def validate_capacity(self):
        """Validate capacity settings"""
        if self.max_vehicles and self.max_vehicles < 1:
            frappe.throw(_("Maximum vehicles must be at least 1"))

    def before_save(self):
        """Auto-generate bay code and calculate metrics"""
        if not self.bay_code:
            self.bay_code = self.generate_bay_code()

        self.calculate_daily_capacity()
        self.update_utilization_metrics()

    def generate_bay_code(self):
        """Generate unique bay code"""
        workshop_code = frappe.db.get_value(
            "Workshop Profile", self.workshop_profile, "workshop_code"
        )
        if not workshop_code:
            workshop_code = "WS"

        # Get bay type abbreviation
        bay_type_abbr = {
            "General Service": "GS",
            "Engine Repair": "ER",
            "Transmission Repair": "TR",
            "Bodywork": "BW",
            "Painting": "PT",
            "Electrical": "EL",
            "Tire Service": "TS",
            "Quick Service": "QS",
        }.get(self.bay_type, "GS")

        # Count existing bays for this workshop
        count = frappe.db.count("Service Bay", {"workshop_profile": self.workshop_profile}) + 1

        return f"{workshop_code}-{bay_type_abbr}-{count:02d}"

    def calculate_daily_capacity(self):
        """Calculate daily capacity based on operating hours and service times"""
        if self.operating_hours_start and self.operating_hours_end:
            start_time = get_time(self.operating_hours_start)
            end_time = get_time(self.operating_hours_end)

            # Calculate operating hours per day
            operating_hours = (
                datetime.combine(datetime.today(), end_time)
                - datetime.combine(datetime.today(), start_time)
            ).total_seconds() / 3600

            # Average service time (default 2 hours if not calculated)
            avg_service_time = self.average_service_time or 2.0

            # Calculate capacity per bay
            capacity_per_bay = int(operating_hours / avg_service_time)

            # Total daily capacity
            self.daily_capacity = capacity_per_bay * (self.max_vehicles or 1)

    def update_utilization_metrics(self):
        """Update utilization metrics based on current assignments"""
        # Get current service orders in this bay
        current_orders = frappe.get_all(
            "Service Order",
            filters={"service_bay": self.name, "status": ["in", ["In Progress", "Quality Check"]]},
        )

        self.current_occupancy = len(current_orders)

        # Calculate utilization rate
        if self.max_vehicles:
            self.utilization_rate = (self.current_occupancy / self.max_vehicles) * 100

        # Calculate average service time from historical data
        self.calculate_average_service_time()

    def calculate_average_service_time(self):
        """Calculate average service time from completed orders"""
        completed_orders = frappe.db.sql(
            """
			SELECT 
				TIMESTAMPDIFF(HOUR, service_start_time, service_end_time) as duration
			FROM `tabService Order`
			WHERE service_bay = %s 
			AND status = 'Completed'
			AND service_start_time IS NOT NULL 
			AND service_end_time IS NOT NULL
			AND creation >= DATE_SUB(NOW(), INTERVAL 30 DAY)
		""",
            [self.name],
            as_dict=True,
        )

        if completed_orders:
            total_hours = sum([order.duration for order in completed_orders if order.duration])
            self.average_service_time = flt(total_hours / len(completed_orders), 2)
        else:
            # Default based on bay type
            defaults = {
                "Quick Service": 1.0,
                "Tire Service": 1.5,
                "General Service": 3.0,
                "Electrical": 4.0,
                "Engine Repair": 8.0,
                "Transmission Repair": 10.0,
                "Bodywork": 12.0,
                "Painting": 16.0,
            }
            self.average_service_time = defaults.get(self.bay_type, 3.0)

    @frappe.whitelist()
    def get_bay_schedule(self, date=None):
        """Get bay schedule for a specific date"""
        if not date:
            date = frappe.utils.today()

        # Get service orders scheduled for this bay on this date
        orders = frappe.get_all(
            "Service Order",
            filters={"service_bay": self.name, "service_date": date},
            fields=[
                "name",
                "customer",
                "vehicle",
                "estimated_duration",
                "service_start_time",
                "service_end_time",
                "status",
            ],
            order_by="service_start_time",
        )

        return {
            "bay_info": {
                "bay_code": self.bay_code,
                "bay_name": self.bay_name,
                "bay_name_ar": self.bay_name_ar,
                "max_vehicles": self.max_vehicles,
                "operating_hours": f"{self.operating_hours_start} - {self.operating_hours_end}",
            },
            "scheduled_orders": orders,
            "utilization_rate": self.utilization_rate,
            "available_slots": self.get_available_time_slots(date),
        }

    def get_available_time_slots(self, date):
        """Get available time slots for scheduling"""
        if not self.operating_hours_start or not self.operating_hours_end:
            return []

        # Get scheduled orders for the date
        scheduled_orders = frappe.db.sql(
            """
			SELECT service_start_time, service_end_time, estimated_duration
			FROM `tabService Order`
			WHERE service_bay = %s 
			AND service_date = %s
			AND service_start_time IS NOT NULL
			ORDER BY service_start_time
		""",
            [self.name, date],
            as_dict=True,
        )

        # Generate available slots (simplified logic)
        available_slots = []
        start_time = datetime.combine(
            datetime.strptime(date, "%Y-%m-%d").date(), get_time(self.operating_hours_start)
        )
        end_time = datetime.combine(
            datetime.strptime(date, "%Y-%m-%d").date(), get_time(self.operating_hours_end)
        )

        current_time = start_time
        slot_duration = timedelta(hours=1)  # 1-hour slots

        while current_time + slot_duration <= end_time:
            # Check if slot is available
            slot_end = current_time + slot_duration
            is_available = True

            for order in scheduled_orders:
                if order.service_start_time and order.service_end_time:
                    order_start = order.service_start_time
                    order_end = order.service_end_time

                    # Check for overlap
                    if current_time < order_end and slot_end > order_start:
                        is_available = False
                        break

            if is_available:
                available_slots.append(
                    {
                        "start_time": current_time.strftime("%H:%M"),
                        "end_time": slot_end.strftime("%H:%M"),
                        "duration": 60,  # minutes
                    }
                )

            current_time += slot_duration

        return available_slots

    @staticmethod
    @frappe.whitelist()
    def get_bay_utilization_dashboard():
        """Get dashboard data for all bays"""
        bays = frappe.get_all(
            "Service Bay",
            filters={"is_active": 1},
            fields=[
                "name",
                "bay_code",
                "bay_name",
                "bay_name_ar",
                "bay_type",
                "current_occupancy",
                "max_vehicles",
                "utilization_rate",
                "average_service_time",
                "daily_capacity",
            ],
        )

        # Calculate overall metrics
        total_capacity = sum([bay.max_vehicles for bay in bays])
        total_occupied = sum([bay.current_occupancy for bay in bays])
        overall_utilization = (total_occupied / total_capacity * 100) if total_capacity > 0 else 0

        # Get today's performance
        today_orders = frappe.db.count(
            "Service Order",
            {"service_date": frappe.utils.today(), "status": ["not in", ["Cancelled", "Draft"]]},
        )

        return {
            "summary": {
                "total_bays": len(bays),
                "total_capacity": total_capacity,
                "current_occupied": total_occupied,
                "overall_utilization": flt(overall_utilization, 2),
                "today_orders": today_orders,
            },
            "bays": bays,
            "performance_metrics": ServiceBay.get_performance_metrics(),
        }

    @staticmethod
    def get_performance_metrics():
        """Get performance metrics for the dashboard"""
        # Get metrics for the last 7 days
        metrics = frappe.db.sql(
            """
			SELECT 
				DATE(creation) as date,
				COUNT(*) as orders_count,
				AVG(TIMESTAMPDIFF(HOUR, service_start_time, service_end_time)) as avg_duration,
				SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_orders
			FROM `tabService Order`
			WHERE creation >= DATE_SUB(NOW(), INTERVAL 7 DAY)
			AND service_bay IS NOT NULL
			GROUP BY DATE(creation)
			ORDER BY date
		""",
            as_dict=True,
        )

        return metrics
