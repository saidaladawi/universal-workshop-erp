# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document


class ServiceRecord(Document):
    def validate(self):
        """Validate service record data before saving"""
        self.validate_mileage()
        self.validate_service_date()
        self.calculate_totals()
        self.set_next_service_due()
        self.set_arabic_translations()

    def validate_mileage(self):
        """Validate that mileage is reasonable"""
        if self.mileage_at_service and self.vehicle:
            # Get vehicle's current mileage
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)

            if (
                vehicle_doc.current_mileage
                and self.mileage_at_service < vehicle_doc.current_mileage
            ):
                # Allow if this is an older service record being added
                if not self.is_new():
                    return

                frappe.msgprint(
                    _(
                        "Service mileage ({0} KM) is less than vehicle's current mileage ({1} KM). Please verify."
                    ).format(self.mileage_at_service, vehicle_doc.current_mileage),
                    indicator="orange",
                )

    def validate_service_date(self):
        """Validate service date"""
        if self.service_date:
            # Convert to datetime for comparison
            service_date = datetime.strptime(str(self.service_date), "%Y-%m-%d")
            today = datetime.today()

            # Allow future dates up to 30 days for scheduling
            if service_date > today + timedelta(days=30):
                frappe.throw(_("Service date cannot be more than 30 days in the future"))

    def calculate_totals(self):
        """Calculate parts total and overall total cost"""
        parts_total = 0

        # Calculate parts total from child table
        if self.parts_used:
            for part in self.parts_used:
                if part.quantity and part.unit_cost:
                    line_total = part.quantity * part.unit_cost
                    part.total_cost = line_total
                    parts_total += line_total

        self.parts_total_cost = parts_total

        # Calculate overall total
        labor_cost = self.labor_cost or 0
        self.total_cost = parts_total + labor_cost

    def set_next_service_due(self):
        """Set next service due based on service interval"""
        if self.mileage_at_service and not self.next_service_due_km and self.vehicle:
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
            service_interval = vehicle_doc.service_interval_km or 10000
            self.next_service_due_km = self.mileage_at_service + service_interval

    def set_arabic_translations(self):
        """Set Arabic translations for service types"""
        if self.service_type and not self.service_type_ar:
            service_translations = {
                "Oil Change": "تغيير الزيت",
                "Brake Service": "خدمة الفرامل",
                "Engine Repair": "إصلاح المحرك",
                "Transmission Service": "خدمة ناقل الحركة",
                "Tire Replacement": "استبدال الإطارات",
                "Battery Replacement": "استبدال البطارية",
                "Air Filter Replacement": "استبدال فلتر الهواء",
                "Spark Plug Replacement": "استبدال شمعات الإشعال",
                "Cooling System Service": "خدمة نظام التبريد",
                "Electrical Repair": "إصلاح كهربائي",
                "General Maintenance": "صيانة عامة",
                "Inspection": "فحص",
                "Other": "أخرى",
            }

            self.service_type_ar = service_translations.get(self.service_type, "")

    def before_save(self):
        """Operations before saving"""
        self.update_vehicle_service_data()

    def update_vehicle_service_data(self):
        """Update vehicle's service-related fields"""
        if self.vehicle and self.status == "Completed":
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)

            # Update vehicle's current mileage if this service has higher mileage
            if self.mileage_at_service and (
                not vehicle_doc.current_mileage
                or self.mileage_at_service > vehicle_doc.current_mileage
            ):
                vehicle_doc.current_mileage = self.mileage_at_service

            # Update last service date
            if (
                self.service_date and not vehicle_doc.last_service_date
            ) or self.service_date > vehicle_doc.last_service_date:
                vehicle_doc.last_service_date = self.service_date

            # Update next service due
            if self.next_service_due_km:
                vehicle_doc.next_service_due = self.calculate_next_service_date()

            vehicle_doc.save(ignore_permissions=True)

    def calculate_next_service_date(self):
        """Calculate next service date based on average usage"""
        if not self.vehicle or not self.next_service_due_km:
            return None

        # Get vehicle's service history to calculate average KM per month
        service_records = frappe.get_all(
            "Service Record",
            filters={"vehicle": self.vehicle, "status": "Completed"},
            fields=["service_date", "mileage_at_service"],
            order_by="service_date asc",
        )

        if len(service_records) < 2:
            # Default to 3 months if no historical data
            return frappe.utils.add_months(self.service_date, 3)

        # Calculate average KM per month
        first_record = service_records[0]
        last_record = service_records[-1]

        km_difference = last_record.mileage_at_service - first_record.mileage_at_service
        date_difference = frappe.utils.date_diff(
            last_record.service_date, first_record.service_date
        )

        if date_difference > 0:
            avg_km_per_day = km_difference / date_difference
            avg_km_per_month = avg_km_per_day * 30

            if avg_km_per_month > 0:
                remaining_km = self.next_service_due_km - self.mileage_at_service
                months_to_next_service = remaining_km / avg_km_per_month
                return frappe.utils.add_months(self.service_date, int(months_to_next_service))

        # Fallback to 3 months
        return frappe.utils.add_months(self.service_date, 3)

    def on_submit(self):
        """Actions when service record is submitted"""
        self.status = "Completed"
        self.completion_date = frappe.utils.now()

    def on_cancel(self):
        """Actions when service record is cancelled"""
        self.status = "Cancelled"

    @frappe.whitelist()
    def get_vehicle_info(self):
        """Get vehicle information for display"""
        if not self.vehicle:
            return {}

        vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
        return {
            "vehicle_display_name": f"{vehicle_doc.year} {vehicle_doc.make} {vehicle_doc.model}",
            "license_plate": vehicle_doc.license_plate,
            "current_mileage": vehicle_doc.current_mileage,
            "last_service_date": vehicle_doc.last_service_date,
            "customer": vehicle_doc.customer,
        }

    @frappe.whitelist()
    def get_service_history(self):
        """Get service history for this vehicle"""
        if not self.vehicle:
            return []

        service_history = frappe.get_all(
            "Service Record",
            filters={"vehicle": self.vehicle, "name": ["!=", self.name]},
            fields=[
                "name",
                "service_date",
                "service_type",
                "mileage_at_service",
                "total_cost",
                "status",
            ],
            order_by="service_date desc",
        )

        return service_history

    @frappe.whitelist()
    def get_cost_breakdown(self):
        """Get detailed cost breakdown"""
        breakdown = {
            "labor_cost": self.labor_cost or 0,
            "parts_cost": self.parts_total_cost or 0,
            "total_cost": self.total_cost or 0,
            "parts_details": [],
        }

        if self.parts_used:
            for part in self.parts_used:
                breakdown["parts_details"].append(
                    {
                        "part_name": part.part_name,
                        "part_number": part.part_number,
                        "quantity": part.quantity,
                        "unit_cost": part.unit_cost,
                        "total_cost": part.total_cost,
                    }
                )

        return breakdown

    def get_dashboard_data(self):
        """Get data for dashboard display"""
        return {
            "vehicle_link": f"/app/vehicle/{self.vehicle}",
            "service_summary": f"{self.service_type} - {self.service_date}",
            "cost_summary": f"OMR {self.total_cost:.3f}",
            "status_color": {
                "Draft": "blue",
                "In Progress": "orange",
                "Completed": "green",
                "Cancelled": "red",
            }.get(self.status, "gray"),
        }
