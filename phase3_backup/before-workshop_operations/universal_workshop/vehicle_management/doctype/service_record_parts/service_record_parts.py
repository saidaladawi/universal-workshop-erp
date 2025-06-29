# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ServiceRecordParts(Document):
	def validate(self):
		"""Validate parts data"""
		self.calculate_total()
		self.set_arabic_translation()

	def calculate_total(self):
		"""Calculate total cost for this part"""
		if self.quantity and self.unit_cost:
			self.total_cost = self.quantity * self.unit_cost
		else:
			self.total_cost = 0

	def set_arabic_translation(self):
		"""Set Arabic translation for common parts"""
		if self.part_name and not self.part_name_ar:
			part_translations = {
				"Engine Oil": "زيت المحرك",
				"Oil Filter": "فلتر الزيت",
				"Air Filter": "فلتر الهواء",
				"Fuel Filter": "فلتر الوقود",
				"Brake Pads": "تيل الفرامل",
				"Brake Fluid": "زيت الفرامل",
				"Spark Plugs": "شمعات الإشعال",
				"Battery": "بطارية",
				"Tire": "إطار",
				"Transmission Oil": "زيت ناقل الحركة",
				"Coolant": "سائل التبريد",
				"Radiator": "مشع",
				"Alternator": "دينامو",
				"Starter": "سلف",
				"Clutch": "كلتش",
				"Timing Belt": "سير التوقيت",
				"Water Pump": "طلمبة الماء",
				"Thermostat": "ثرموستات",
				"Shock Absorber": "ماص الصدمات",
			}

			self.part_name_ar = part_translations.get(self.part_name, "")
