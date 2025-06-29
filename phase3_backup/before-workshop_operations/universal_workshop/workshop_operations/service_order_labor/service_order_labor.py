# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_datetime, nowtime, time_diff_in_hours


class ServiceOrderLabor(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        activity: DF.Data
        activity_ar: DF.Data | None
        end_time: DF.Datetime | None
        hourly_rate: DF.Currency
        hours: DF.Float
        notes: DF.Text | None
        parent: DF.Data
        parentfield: DF.Data
        parenttype: DF.Data
        start_time: DF.Datetime | None
        technician: DF.Link
        technician_name: DF.Data | None
        total_amount: DF.Currency
    # end: auto-generated types

    def validate(self):
        """Validate Service Order Labor entry"""
        self.validate_hours()
        self.validate_hourly_rate()
        self.validate_time_entries()
        self.validate_technician()
        self.calculate_total_amount()
        self.validate_arabic_fields()

    def validate_hours(self):
        """Ensure hours is positive and reasonable"""
        if not self.hours or self.hours <= 0:
            frappe.throw(_("Hours must be greater than zero"))

        # Check for reasonable work hours (max 16 hours per day)
        if self.hours > 16:
            frappe.msgprint(
                _("Labor hours exceed 16 hours. Please verify this is correct."), indicator="yellow"
            )

    def validate_hourly_rate(self):
        """Ensure hourly rate is positive"""
        if not self.hourly_rate or self.hourly_rate <= 0:
            frappe.throw(_("Hourly Rate must be greater than zero"))

    def validate_time_entries(self):
        """Validate start and end time entries"""
        if self.start_time and self.end_time:
            start_dt = get_datetime(self.start_time)
            end_dt = get_datetime(self.end_time)

            # Check that end time is after start time
            if end_dt <= start_dt:
                frappe.throw(_("End Time must be after Start Time"))

            # Calculate actual hours from time difference
            calculated_hours = time_diff_in_hours(end_dt, start_dt)

            # If hours field is empty, auto-calculate
            if not self.hours:
                self.hours = flt(calculated_hours, precision=2)
            else:
                # Check for significant discrepancy (more than 15 minutes)
                hour_diff = abs(calculated_hours - self.hours)
                if hour_diff > 0.25:  # 15 minutes
                    frappe.msgprint(
                        _(
                            "Time difference ({0} hours) doesn't match entered hours ({1}). Please verify."
                        ).format(flt(calculated_hours, precision=2), flt(self.hours, precision=2)),
                        indicator="orange",
                    )

    def validate_technician(self):
        """Validate technician assignment"""
        if self.technician:
            # Check if technician is active
            technician_active = frappe.db.get_value("User", self.technician, "enabled")
            if not technician_active:
                frappe.throw(_("Selected technician is not active"))

            # Check if technician has workshop role
            has_workshop_role = frappe.db.exists(
                "Has Role",
                {
                    "parent": self.technician,
                    "role": ["in", ["Workshop Technician", "Workshop Manager"]],
                },
            )

            if not has_workshop_role:
                frappe.msgprint(
                    _("Selected user does not have workshop access roles"), indicator="orange"
                )

    def validate_arabic_fields(self):
        """Validate Arabic field content"""
        if self.activity_ar and not self.is_arabic_text(self.activity_ar):
            frappe.msgprint(
                _("Activity Arabic should contain Arabic characters"), indicator="orange"
            )

    def is_arabic_text(self, text):
        """Check if text contains Arabic characters"""
        if not text:
            return False
        arabic_pattern = re.compile(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]"
        )
        return bool(arabic_pattern.search(text))

    def calculate_total_amount(self):
        """Calculate total amount based on hours and hourly rate"""
        if self.hours and self.hourly_rate:
            self.total_amount = flt(self.hours * self.hourly_rate, precision=3)

    def before_save(self):
        """Actions before saving"""
        self.set_technician_details()
        self.set_activity_arabic()
        self.set_default_hourly_rate()

    def set_technician_details(self):
        """Auto-populate technician details"""
        if self.technician and not self.technician_name:
            technician_doc = frappe.get_doc("User", self.technician)
            self.technician_name = technician_doc.full_name or technician_doc.first_name

    def set_activity_arabic(self):
        """Auto-set Arabic activity name if available"""
        if self.activity and not self.activity_ar:
            # Common workshop activities translations
            activity_translations = {
                "Oil Change": "تغيير الزيت",
                "Brake Service": "خدمة الفرامل",
                "Engine Repair": "إصلاح المحرك",
                "Transmission Service": "خدمة ناقل الحركة",
                "Tire Replacement": "تغيير الإطارات",
                "Battery Replacement": "تغيير البطارية",
                "Air Filter Replacement": "تغيير فلتر الهواء",
                "Spark Plug Replacement": "تغيير شمعات الإشعال",
                "Cooling System Service": "خدمة نظام التبريد",
                "Electrical Repair": "إصلاح كهربائي",
                "General Maintenance": "صيانة عامة",
                "Inspection": "فحص",
                "Diagnostic": "تشخيص",
                "Welding": "لحام",
                "Painting": "دهان",
                "Body Work": "أعمال هيكل",
                "Suspension Repair": "إصلاح التعليق",
                "Exhaust System": "نظام العادم",
                "Fuel System": "نظام الوقود",
                "Steering System": "نظام التوجيه",
            }

            if self.activity in activity_translations:
                self.activity_ar = activity_translations[self.activity]

    def set_default_hourly_rate(self):
        """Set default hourly rate if not provided"""
        if not self.hourly_rate and self.technician:
            # Try to get technician's hourly rate from Employee record
            employee = frappe.db.get_value("Employee", {"user_id": self.technician}, "name")
            if employee:
                hourly_rate = frappe.db.get_value("Employee", employee, "hourly_rate")
                if hourly_rate:
                    self.hourly_rate = hourly_rate
                else:
                    # Set default hourly rate from workshop settings
                    default_rate = frappe.db.get_single_value(
                        "Workshop Settings", "default_hourly_rate"
                    )
                    if default_rate:
                        self.hourly_rate = default_rate

    @frappe.whitelist()
    def start_timer(self):
        """Start work timer for this activity"""
        if self.start_time:
            frappe.throw(_("Timer already started for this activity"))

        self.start_time = frappe.utils.now()
        self.save()

        return {"message": _("Timer started successfully"), "start_time": self.start_time}

    @frappe.whitelist()
    def stop_timer(self):
        """Stop work timer and calculate hours"""
        if not self.start_time:
            frappe.throw(_("Timer not started for this activity"))

        if self.end_time:
            frappe.throw(_("Timer already stopped for this activity"))

        self.end_time = frappe.utils.now()

        # Calculate hours automatically
        start_dt = get_datetime(self.start_time)
        end_dt = get_datetime(self.end_time)
        calculated_hours = time_diff_in_hours(end_dt, start_dt)
        self.hours = flt(calculated_hours, precision=2)

        # Recalculate total
        self.calculate_total_amount()
        self.save()

        return {
            "message": _("Timer stopped successfully"),
            "end_time": self.end_time,
            "hours": self.hours,
            "total_amount": self.total_amount,
        }

    @frappe.whitelist()
    def get_technician_workload(self, date=None):
        """Get technician's workload for specified date"""
        if not self.technician:
            return {}

        if not date:
            date = frappe.utils.today()

        # Get all labor entries for this technician on this date
        labor_entries = frappe.get_all(
            "Service Order Labor",
            filters={"technician": self.technician, "start_time": ["like", f"{date}%"]},
            fields=["hours", "total_amount", "activity"],
            order_by="start_time",
        )

        total_hours = sum(entry.hours or 0 for entry in labor_entries)
        total_amount = sum(entry.total_amount or 0 for entry in labor_entries)

        return {
            "date": date,
            "technician": self.technician,
            "technician_name": self.technician_name,
            "total_hours": total_hours,
            "total_amount": total_amount,
            "activities_count": len(labor_entries),
            "activities": labor_entries,
        }

    def get_formatted_total(self, language="en"):
        """Get formatted total amount in specified language"""
        if not self.total_amount:
            return "0"

        if language == "ar":
            # Format for Arabic: ر.ع. ١٢٣.٤٥٦
            arabic_amount = self.convert_to_arabic_numerals(f"{self.total_amount:,.3f}")
            return f"ر.ع. {arabic_amount}"
        else:
            # Format for English: OMR 123.456
            return f"OMR {self.total_amount:,.3f}"

    def convert_to_arabic_numerals(self, text):
        """Convert Western numerals to Arabic-Indic numerals"""
        arabic_numerals = {
            "0": "٠",
            "1": "١",
            "2": "٢",
            "3": "٣",
            "4": "٤",
            "5": "٥",
            "6": "٦",
            "7": "٧",
            "8": "٨",
            "9": "٩",
        }

        for western, arabic in arabic_numerals.items():
            text = text.replace(western, arabic)
        return text

    def get_work_duration_display(self):
        """Get work duration in human-readable format"""
        if not self.hours:
            return ""

        hours = int(self.hours)
        minutes = int((self.hours - hours) * 60)

        if frappe.local.lang == "ar":
            if hours > 0 and minutes > 0:
                return f"{self.convert_to_arabic_numerals(str(hours))} ساعات و {self.convert_to_arabic_numerals(str(minutes))} دقائق"
            elif hours > 0:
                return f"{self.convert_to_arabic_numerals(str(hours))} ساعات"
            else:
                return f"{self.convert_to_arabic_numerals(str(minutes))} دقائق"
        else:
            if hours > 0 and minutes > 0:
                return f"{hours} hours {minutes} minutes"
            elif hours > 0:
                return f"{hours} hours"
            else:
                return f"{minutes} minutes"
