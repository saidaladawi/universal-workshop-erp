# -*- coding: utf-8 -*-
# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, add_days, cint


class ServiceEstimate(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class

    def validate(self):
        """Validate service estimate before saving"""
        self.validate_dates()
        self.validate_customer_vehicle()
        self.validate_arabic_fields()
        self.calculate_totals()
        self.set_default_values()

    def before_save(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.now()
        if not self.estimate_date:
            self.estimate_date = frappe.utils.today()
        if not self.valid_till:
            # Valid for 30 days by default
            self.valid_till = frappe.utils.add_days(frappe.utils.today(), 30)

    def validate_dates(self):
        """Validate estimate and validity dates"""
        if not self.date:
            self.date = getdate()

        if getdate(self.valid_till) < getdate(self.date):
            frappe.throw(_("Valid Till date cannot be before Estimate Date"))

    def validate_customer_vehicle(self):
        """Validate customer and vehicle information"""
        if self.customer:
            # Fetch customer names
            customer_doc = frappe.get_doc("Customer", self.customer)
            self.customer_name = customer_doc.customer_name

            # Get Arabic name if available
            if hasattr(customer_doc, "customer_name_ar") and customer_doc.customer_name_ar:
                self.customer_name_ar = customer_doc.customer_name_ar

        if self.vehicle:
            # Fetch vehicle details
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)

            # Verify vehicle belongs to customer
            if vehicle_doc.customer != self.customer:
                frappe.throw(_("Selected vehicle does not belong to this customer"))

            # Set vehicle details
            self.vehicle_details = f"{vehicle_doc.make} {vehicle_doc.model} {vehicle_doc.year} - {vehicle_doc.license_plate}"

    def validate_arabic_fields(self):
        """Validate Arabic language fields"""
        # If Arabic service description is empty but English is provided, suggest translation
        if self.service_description and not self.service_description_ar:
            # This could be enhanced with automatic translation in the future
            pass
        if self.customer_name_ar and not self.customer_name_ar.strip():
            frappe.throw(_("Arabic customer name cannot be empty"))

    def calculate_totals(self):
        """Calculate total amounts for parts and labor"""
        self.total_parts_amount = 0
        self.total_labor_amount = 0

        # Calculate parts total
        if self.parts:
            for part in self.parts:
                if part.qty and part.rate:
                    part.amount = part.qty * part.rate
                    self.total_parts_amount += part.amount

        # Calculate labor total
        if self.labor:
            for labor in self.labor:
                if labor.hours and labor.rate:
                    labor.amount = labor.hours * labor.rate
                    self.total_labor_amount += labor.amount

        # Calculate grand total
        self.grand_total = self.total_parts_amount + self.total_labor_amount

        # Calculate VAT (5% for Oman)
        if self.apply_vat:
            self.vat_amount = self.grand_total * 0.05
            self.grand_total_with_vat = self.grand_total + self.vat_amount
        else:
            self.vat_amount = 0
            self.grand_total_with_vat = self.grand_total

    def set_default_values(self):
        """Set default values for fields"""
        if not self.priority:
            self.priority = "Medium"

        # Set default terms and conditions
        if not self.terms_and_conditions:
            self.terms_and_conditions = self.get_default_terms()

        if not self.terms_and_conditions_ar:
            self.terms_and_conditions_ar = self.get_default_terms_arabic()

    def get_default_terms(self):
        """Get default terms and conditions in English"""
        return """
1. This estimate is valid for 30 days from the date issued.
2. Prices are subject to change based on actual parts availability.
3. Additional charges may apply for unforeseen complications.
4. Payment is due upon completion of service.
5. All prices include 5% VAT as per Oman Tax Authority regulations.
"""

    def get_default_terms_arabic(self):
        """Get default terms and conditions in Arabic"""
        return """
١. هذا التقدير صالح لمدة ٣٠ يوماً من تاريخ الإصدار.
٢. الأسعار قابلة للتغيير حسب توفر القطع الفعلي.
٣. قد تطبق رسوم إضافية للمضاعفات غير المتوقعة.
٤. الدفع مستحق عند اكتمال الخدمة.
٥. جميع الأسعار تشمل ضريبة القيمة المضافة ٥٪ وفقاً لأنظمة الهيئة الضريبية العمانية.
"""

    def on_submit(self):
        """Actions when estimate is submitted"""
        if self.status == "Draft":
            self.status = "Pending Approval" if self.approval_required else "Approved"
            self.save()

    def approve_estimate(self):
        """Approve the estimate"""
        if not frappe.has_permission(self.doctype, "submit", self):
            frappe.throw(_("Not permitted to approve estimates"))

        self.status = "Approved"
        self.approved_by = frappe.session.user
        self.approval_date = frappe.utils.now()
        self.save()

        frappe.msgprint(_("Service Estimate {0} has been approved").format(self.name))

    def reject_estimate(self, reason, reason_ar=None):
        """Reject the estimate with reason"""
        if not frappe.has_permission(self.doctype, "submit", self):
            frappe.throw(_("Not permitted to reject estimates"))

        self.status = "Rejected"
        self.rejection_reason = reason
        if reason_ar:
            self.rejection_reason_ar = reason_ar
        self.save()

        frappe.msgprint(_("Service Estimate {0} has been rejected").format(self.name))

    def convert_to_service_order(self):
        """Convert estimate to service order"""
        if self.status != "Approved":
            frappe.throw(_("Only approved estimates can be converted to service orders"))

        if self.converted_to_service_order:
            frappe.throw(_("This estimate has already been converted to a service order"))

        # Create Sales Order
        sales_order = frappe.new_doc("Sales Order")
        sales_order.customer = self.customer
        sales_order.delivery_date = add_days(self.date, 7)  # Default 7 days delivery
        sales_order.transaction_date = self.date

        # Add items from estimate
        if self.estimate_items:
            for item in self.estimate_items:
                sales_order.append(
                    "items",
                    {
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "description": item.description,
                        "qty": item.qty,
                        "rate": item.rate,
                        "amount": item.amount,
                    },
                )

        # Add parts as items
        if self.parts_items:
            for part in self.parts_items:
                sales_order.append(
                    "items",
                    {
                        "item_code": part.part_code,
                        "item_name": part.part_name,
                        "description": part.description,
                        "qty": part.qty,
                        "rate": part.rate,
                        "amount": part.amount,
                    },
                )

        # Set taxes (VAT)
        sales_order.append(
            "taxes",
            {
                "charge_type": "On Net Total",
                "account_head": "VAT - UW",  # This should be configured
                "description": "VAT @ 5%",
                "rate": self.vat_rate,
            },
        )

        sales_order.insert()

        # Update estimate
        self.converted_to_service_order = 1
        self.service_order_reference = sales_order.name
        self.status = "Converted"
        self.save()

        frappe.msgprint(_("Service Order {0} created successfully").format(sales_order.name))
        return sales_order.name


@frappe.whitelist()
def approve_estimate(estimate_name):
    """API method to approve estimate"""
    estimate = frappe.get_doc("Service Estimate", estimate_name)
    estimate.approve_estimate()
    return True


@frappe.whitelist()
def reject_estimate(estimate_name, reason, reason_ar=None):
    """API method to reject estimate"""
    estimate = frappe.get_doc("Service Estimate", estimate_name)
    estimate.reject_estimate(reason, reason_ar)
    return True


@frappe.whitelist()
def convert_to_service_order(estimate_name):
    """API method to convert estimate to service order"""
    estimate = frappe.get_doc("Service Estimate", estimate_name)
    return estimate.convert_to_service_order()


@frappe.whitelist()
def get_customer_vehicles(customer):
    """Get vehicles for a specific customer"""
    vehicles = frappe.get_list(
        "Vehicle",
        filters={"customer": customer},
        fields=["name", "make", "model", "year", "license_plate"],
    )
    return vehicles


@frappe.whitelist()
def get_service_history(customer, vehicle=None):
    """Get service history for customer/vehicle"""
    filters = {"customer": customer}
    if vehicle:
        filters["vehicle"] = vehicle

    estimates = frappe.get_list(
        "Service Estimate",
        filters=filters,
        fields=["name", "date", "service_description", "total_amount", "status"],
        order_by="date desc",
        limit=10,
    )
    return estimates
