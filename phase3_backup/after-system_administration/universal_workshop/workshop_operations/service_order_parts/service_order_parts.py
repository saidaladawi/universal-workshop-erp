# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ServiceOrderParts(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.Text | None
		description_ar: DF.Text | None
		item: DF.Link
		item_name: DF.Data | None
		item_name_ar: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		part_number: DF.Data | None
		quantity: DF.Float
		supplier: DF.Link | None
		total_amount: DF.Currency
		unit_price: DF.Currency
		warranty_period: DF.Data | None
	# end: auto-generated types

	def validate(self):
		"""Validate Service Order Parts entry"""
		self.validate_quantity()
		self.validate_unit_price()
		self.calculate_total_amount()
		self.validate_warranty_period()
		self.validate_arabic_fields()

	def validate_quantity(self):
		"""Ensure quantity is positive"""
		if not self.quantity or self.quantity <= 0:
			frappe.throw(_("Quantity must be greater than zero"))

	def validate_unit_price(self):
		"""Ensure unit price is positive"""
		if not self.unit_price or self.unit_price <= 0:
			frappe.throw(_("Unit Price must be greater than zero"))

	def calculate_total_amount(self):
		"""Calculate total amount based on quantity and unit price"""
		if self.quantity and self.unit_price:
			self.total_amount = flt(self.quantity * self.unit_price, precision=3)

	def validate_warranty_period(self):
		"""Validate warranty period format if provided"""
		if self.warranty_period:
			# Expected formats: "12 months", "1 year", "6 أشهر", "سنة واحدة"
			valid_patterns = [r"^\d+\s+(months?|years?|أشهر|شهر|سنوات|سنة)$", r"^(سنة واحدة|شهر واحد)$"]

			is_valid = any(
				re.match(pattern, self.warranty_period.strip(), re.IGNORECASE) for pattern in valid_patterns
			)

			if not is_valid:
				frappe.throw(
					_(
						"Invalid warranty period format. Use formats like '12 months', '1 year', '6 أشهر', or 'سنة واحدة'"
					)
				)

	def validate_arabic_fields(self):
		"""Validate Arabic field content"""
		if self.item_name_ar and not self.is_arabic_text(self.item_name_ar):
			frappe.msgprint(_("Item Name Arabic should contain Arabic characters"), indicator="orange")

		if self.description_ar and not self.is_arabic_text(self.description_ar):
			frappe.msgprint(_("Description Arabic should contain Arabic characters"), indicator="orange")

	def is_arabic_text(self, text):
		"""Check if text contains Arabic characters"""
		if not text:
			return False
		arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
		return bool(arabic_pattern.search(text))

	def before_save(self):
		"""Actions before saving"""
		self.set_item_details()
		self.update_description_fields()

	def set_item_details(self):
		"""Auto-populate item details when item is selected"""
		if self.item and not self.item_name:
			item_doc = frappe.get_doc("Item", self.item)
			self.item_name = item_doc.item_name

			# Set Arabic name if available
			if hasattr(item_doc, "item_name_ar") and item_doc.item_name_ar:
				self.item_name_ar = item_doc.item_name_ar

			# Set part number if available
			if hasattr(item_doc, "oem_part_number") and item_doc.oem_part_number:
				self.part_number = item_doc.oem_part_number

			# Set unit price from item if not set
			if not self.unit_price and item_doc.standard_rate:
				self.unit_price = item_doc.standard_rate

	def update_description_fields(self):
		"""Update description fields based on item if empty"""
		if self.item and not self.description:
			item_doc = frappe.get_doc("Item", self.item)
			if item_doc.description:
				self.description = item_doc.description

			# Set Arabic description if available
			if hasattr(item_doc, "description_ar") and item_doc.description_ar and not self.description_ar:
				self.description_ar = item_doc.description_ar

	@frappe.whitelist()
	def get_item_price(self, price_list=None):
		"""Get item price from price list"""
		if not self.item:
			return 0

		if not price_list:
			# Get default selling price list
			price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")

		price = frappe.get_all(
			"Item Price",
			filters={"item_code": self.item, "price_list": price_list, "selling": 1},
			fields=["price_list_rate"],
			limit=1,
		)

		return price[0].price_list_rate if price else 0

	@frappe.whitelist()
	def get_item_stock_qty(self, warehouse=None):
		"""Get current stock quantity of the item"""
		if not self.item:
			return 0

		if not warehouse:
			# Get default warehouse from company or user
			warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")

		stock_qty = (
			frappe.db.get_value("Bin", {"item_code": self.item, "warehouse": warehouse}, "actual_qty") or 0
		)

		return stock_qty

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

	def get_warranty_info(self):
		"""Get warranty information"""
		if not self.warranty_period:
			return {"has_warranty": False, "period": None, "period_ar": None}

		# Convert warranty period to both languages
		warranty_translations = {"months": "أشهر", "month": "شهر", "years": "سنوات", "year": "سنة"}

		period_ar = self.warranty_period
		for en, ar in warranty_translations.items():
			period_ar = period_ar.replace(en, ar)

		return {"has_warranty": True, "period": self.warranty_period, "period_ar": period_ar}
