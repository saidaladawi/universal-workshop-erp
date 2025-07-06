# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate
import json
from typing import Dict, List, Any


class SupplierComparison(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields

    def validate(self):
        """Validate supplier comparison data before saving"""
        self.validate_arabic_title()
        self.validate_dates()
        self.calculate_totals()
        self.validate_supplier_quotations()

    def validate_arabic_title(self):
        """Ensure Arabic title is provided if title exists"""
        if self.title and not self.title_ar:
            self.title_ar = self.title  # Default to English title if Arabic not provided

    def validate_dates(self):
        """Validate required by date is in the future"""
        if self.required_by and getdate(self.required_by) <= getdate():
            frappe.throw(_("Required By date must be in the future"))

    def calculate_totals(self):
        """Calculate total amounts from supplier quotations"""
        total = 0
        if self.supplier_quotations:
            for quotation in self.supplier_quotations:
                if quotation.quoted_rate and quotation.qty:
                    quotation.amount = flt(quotation.quoted_rate) * flt(quotation.qty)
                    if quotation.is_selected:
                        total += flt(quotation.amount)

        self.total_amount = total

    def validate_supplier_quotations(self):
        """Validate supplier quotation data"""
        if not self.supplier_quotations:
            return

        selected_count = 0
        for quotation in self.supplier_quotations:
            if quotation.is_selected:
                selected_count += 1
                if not self.selected_supplier:
                    self.selected_supplier = quotation.supplier

        if selected_count > 1:
            frappe.throw(_("Only one supplier can be selected for each item"))

    def before_save(self):
        """Actions before saving the document"""
        if not self.title and self.material_request:
            material_request_doc = frappe.get_doc("Material Request", self.material_request)
            self.title = f"Supplier Comparison for {material_request_doc.name}"
            if not self.title_ar:
                self.title_ar = f"مقارنة موردين لـ {material_request_doc.name}"

    def on_submit(self):
        """Actions when document is submitted"""
        self.status = "Analysis Complete"
        if self.selected_supplier:
            self.status = "Supplier Selected"
            self.create_purchase_order()

    def create_purchase_order(self):
        """Create purchase order for selected supplier"""
        if not self.selected_supplier:
            frappe.throw(_("Please select a supplier before submitting"))

        # Get selected items
        selected_items = []
        for quotation in self.supplier_quotations:
            if quotation.is_selected and quotation.supplier == self.selected_supplier:
                selected_items.append(
                    {
                        "item_code": quotation.item_code,
                        "qty": quotation.qty,
                        "rate": quotation.quoted_rate,
                        "schedule_date": self.required_by or getdate(),
                        "warehouse": quotation.warehouse,
                    }
                )

        if not selected_items:
            frappe.throw(_("No items selected for the chosen supplier"))

        # Create Purchase Order
        po = frappe.new_doc("Purchase Order")
        po.supplier = self.selected_supplier
        po.company = self.company
        po.currency = self.currency or "OMR"
        po.set_posting_time = 1
        po.schedule_date = self.required_by or getdate()

        for item in selected_items:
            po.append("items", item)

        po.insert()
        po.submit()

        # Update status
        self.db_set("status", "PO Created")

        # Add comment
        frappe.msgprint(_("Purchase Order {0} created successfully").format(po.name))

        return po.name


@frappe.whitelist()
def get_supplier_quotations(material_request):
    """Get existing supplier quotations for a material request"""

    if not material_request:
        return []

    # Get Material Request items
    mr_items = frappe.get_all(
        "Material Request Item",
        filters={"parent": material_request},
        fields=["item_code", "qty", "warehouse"],
    )

    # Get existing Supplier Quotations
    quotations = []
    for item in mr_items:
        existing_quotes = frappe.get_all(
            "Supplier Quotation Item",
            filters={"item_code": item.item_code},
            fields=["parent", "rate", "qty", "amount"],
        )

        for quote in existing_quotes:
            sq_doc = frappe.get_doc("Supplier Quotation", quote.parent)
            quotations.append(
                {
                    "item_code": item.item_code,
                    "supplier": sq_doc.supplier,
                    "supplier_name": sq_doc.supplier_name,
                    "quoted_rate": quote.rate,
                    "qty": quote.qty,
                    "amount": quote.amount,
                    "quotation_date": sq_doc.transaction_date,
                    "lead_time_days": sq_doc.get("lead_time_days", 0),
                    "warehouse": item.warehouse,
                }
            )

    return quotations


@frappe.whitelist()
def create_comparison_from_material_request(material_request):
    """Create supplier comparison from material request"""

    if not material_request:
        frappe.throw(_("Material Request is required"))

    mr_doc = frappe.get_doc("Material Request", material_request)

    # Create Supplier Comparison
    comparison = frappe.new_doc("Supplier Comparison")
    comparison.title = f"Supplier Comparison for {mr_doc.name}"
    comparison.title_ar = f"مقارنة موردين لـ {mr_doc.name}"
    comparison.material_request = material_request
    comparison.required_by = mr_doc.schedule_date
    comparison.company = mr_doc.company
    comparison.currency = "OMR"
    comparison.status = "Draft"

    # Add items from Material Request
    for item in mr_doc.items:
        comparison.append(
            "comparison_items",
            {
                "item_code": item.item_code,
                "description": item.description,
                "qty": item.qty,
                "uom": item.uom,
                "warehouse": item.warehouse,
            },
        )

    comparison.insert()

    return comparison.name


@frappe.whitelist()
def get_supplier_comparison_analytics(comparison_name):
    """Get analytics data for supplier comparison"""

    comparison = frappe.get_doc("Supplier Comparison", comparison_name)

    analytics = {
        "total_suppliers": 0,
        "total_items": len(comparison.comparison_items),
        "supplier_stats": {},
        "price_analysis": {},
    }

    suppliers = set()
    item_prices = {}

    for quotation in comparison.supplier_quotations:
        suppliers.add(quotation.supplier)

        if quotation.item_code not in item_prices:
            item_prices[quotation.item_code] = []

        item_prices[quotation.item_code].append(
            {
                "supplier": quotation.supplier,
                "rate": flt(quotation.quoted_rate),
                "lead_time": cint(quotation.lead_time_days),
            }
        )

    analytics["total_suppliers"] = len(suppliers)

    # Calculate price statistics for each item
    for item_code, prices in item_prices.items():
        if len(prices) > 1:
            rates = [p["rate"] for p in prices]
            analytics["price_analysis"][item_code] = {
                "min_price": min(rates),
                "max_price": max(rates),
                "avg_price": sum(rates) / len(rates),
                "price_variance": max(rates) - min(rates),
                "total_quotes": len(prices),
            }

    return analytics
