"""
Workshop Appointment Service DocType Controller
Child table for managing multiple services within a single appointment
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, time_diff_in_hours, now_datetime

# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class


class WorkshopAppointmentService(Document):
    """Workshop Appointment Service controller for service line items"""

    def validate(self):
        """Validate service data"""
        self.validate_required_fields()
        self.validate_quantities()
        self.validate_rates()
        self.calculate_amounts()
        self.validate_duration()
        self.validate_arabic_fields()

    def before_save(self):
        """Pre-save operations"""
        self.calculate_actual_duration()
        self.update_completion_status()

    def validate_required_fields(self):
        """Validate required fields"""
        if not self.service_type:
            frappe.throw(_("Service type is required | نوع الخدمة مطلوب"))

        if not self.quantity or self.quantity <= 0:
            frappe.throw(_("Quantity must be greater than zero | الكمية يجب أن تكون أكبر من الصفر"))

        if not self.unit_rate or self.unit_rate < 0:
            frappe.throw(_("Unit rate cannot be negative | السعر للوحدة لا يمكن أن يكون سالباً"))

    def validate_quantities(self):
        """Validate quantity values"""
        if self.quantity and self.quantity > 100:
            frappe.throw(_("Quantity cannot exceed 100 | الكمية لا يمكن أن تتجاوز 100"))

        if self.completion_percentage and (
            self.completion_percentage < 0 or self.completion_percentage > 100
        ):
            frappe.throw(
                _(
                    "Completion percentage must be between 0 and 100 | نسبة الإنجاز يجب أن تكون بين 0 و 100"
                )
            )

    def validate_rates(self):
        """Validate rate and cost values"""
        if self.unit_rate and self.unit_rate > 10000:  # OMR 10,000 limit
            frappe.throw(
                _(
                    "Unit rate seems too high. Please verify | السعر للوحدة يبدو مرتفعاً جداً. يرجى التحقق"
                )
            )

        if self.labor_cost and self.labor_cost < 0:
            frappe.throw(_("Labor cost cannot be negative | تكلفة العمالة لا يمكن أن تكون سالبة"))

        if self.parts_cost and self.parts_cost < 0:
            frappe.throw(_("Parts cost cannot be negative | تكلفة القطع لا يمكن أن تكون سالبة"))

    def calculate_amounts(self):
        """Calculate all amount fields"""
        # Basic amount calculation
        self.amount = flt(self.quantity, 2) * flt(self.unit_rate, 3)

        # Calculate detailed pricing breakdown
        base_amount = flt(self.base_rate or self.unit_rate, 3)
        labor_cost = flt(self.labor_cost, 3)
        parts_cost = flt(self.parts_cost, 3)
        additional_charges = flt(self.additional_charges, 3)
        discount_amount = flt(self.discount_amount, 3)

        # Subtotal before tax
        subtotal = (base_amount + labor_cost + parts_cost + additional_charges) * flt(
            self.quantity, 2
        )
        subtotal_after_discount = subtotal - discount_amount

        # Calculate tax (5% VAT for Oman)
        tax_rate = flt(self.tax_rate, 2) or 5.0
        tax_amount = (subtotal_after_discount * tax_rate) / 100

        # Total amount
        total_amount = subtotal_after_discount + tax_amount

        # Set calculated values
        self.tax_amount = flt(tax_amount, 3)
        self.total_amount = flt(total_amount, 3)

        # Update main amount field with total
        self.amount = self.total_amount

    def validate_duration(self):
        """Validate duration values"""
        if self.estimated_duration and self.estimated_duration < 0:
            frappe.throw(
                _("Estimated duration cannot be negative | المدة المقدرة لا يمكن أن تكون سالبة")
            )

        if self.actual_duration and self.actual_duration < 0:
            frappe.throw(
                _("Actual duration cannot be negative | المدة الفعلية لا يمكن أن تكون سالبة")
            )

        # Warn if actual duration significantly exceeds estimated
        if (
            self.estimated_duration
            and self.actual_duration
            and self.actual_duration > self.estimated_duration * 2
        ):
            frappe.msgprint(
                _(
                    "Actual duration ({0} hours) significantly exceeds estimated duration ({1} hours) | المدة الفعلية ({0} ساعة) تتجاوز بشكل كبير المدة المقدرة ({1} ساعة)"
                ).format(self.actual_duration, self.estimated_duration),
                alert=True,
            )

    def validate_arabic_fields(self):
        """Validate Arabic field requirements"""
        if frappe.db.get_single_value("Universal Workshop Settings", "require_arabic_fields"):
            if self.service_description and not self.service_description_ar:
                frappe.throw(
                    _("Arabic service description is required | وصف الخدمة باللغة العربية مطلوب")
                )

            if self.service_notes and not self.service_notes_ar:
                frappe.throw(
                    _("Arabic service notes are required | ملاحظات الخدمة باللغة العربية مطلوبة")
                )

    def calculate_actual_duration(self):
        """Calculate actual duration if start and end times are set"""
        if self.start_time and self.end_time:
            duration = time_diff_in_hours(self.end_time, self.start_time)
            self.actual_duration = flt(duration, 2)

    def update_completion_status(self):
        """Update service status based on completion percentage"""
        if self.completion_percentage == 100:
            self.service_status = "Completed"
            if not self.end_time:
                self.end_time = now_datetime()
        elif self.completion_percentage > 0:
            self.service_status = "In Progress"
            if not self.start_time:
                self.start_time = now_datetime()
        else:
            self.service_status = "Pending"

    def get_service_summary(self):
        """Get service summary for display"""
        summary = {
            "service_name": self.service_name_ar if frappe.boot.lang == "ar" else self.service_name,
            "quantity": self.quantity,
            "unit_rate": self.unit_rate,
            "amount": self.amount,
            "status": self.service_status,
            "completion_percentage": self.completion_percentage,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration,
        }

        return summary

    def get_pricing_breakdown(self):
        """Get detailed pricing breakdown"""
        breakdown = {
            "base_rate": flt(self.base_rate, 3),
            "labor_cost": flt(self.labor_cost, 3),
            "parts_cost": flt(self.parts_cost, 3),
            "additional_charges": flt(self.additional_charges, 3),
            "subtotal": flt(
                self.base_rate + self.labor_cost + self.parts_cost + self.additional_charges, 3
            )
            * flt(self.quantity, 2),
            "discount_amount": flt(self.discount_amount, 3),
            "tax_rate": flt(self.tax_rate, 2),
            "tax_amount": flt(self.tax_amount, 3),
            "total_amount": flt(self.total_amount, 3),
        }

        return breakdown
