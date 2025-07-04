# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PartPhoto(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields

	def validate(self):
		"""Validate part photo data"""
		self.validate_required_fields()
		self.translate_photo_type()
		self.validate_defect_information()

	def validate_required_fields(self):
		"""Validate required fields"""
		if not self.photo_type:
			frappe.throw(_("Photo Type is required"))

		if not self.photo_attachment:
			frappe.throw(_("Photo attachment is required"))

	def translate_photo_type(self):
		"""Automatically translate photo type to Arabic"""
		photo_translations = {
			"Front View": "المنظر الأمامي",
			"Back View": "المنظر الخلفي",
			"Left Side": "الجانب الأيسر",
			"Right Side": "الجانب الأيمن",
			"Top View": "المنظر العلوي",
			"Bottom View": "المنظر السفلي",
			"Close-up Detail": "تفاصيل مقربة",
			"Defect/Damage": "عيب/ضرر",
			"Serial Number": "الرقم التسلسلي",
			"Before Cleaning": "قبل التنظيف",
			"After Cleaning": "بعد التنظيف",
			"Installation Point": "نقطة التركيب",
			"Internal View": "المنظر الداخلي",
			"Connections": "التوصيلات",
			"Overall Condition": "الحالة العامة",
		}

		if self.photo_type in photo_translations:
			self.photo_type_ar = photo_translations[self.photo_type]

	def validate_defect_information(self):
		"""Validate defect information if defect is shown"""
		if self.shows_defect:
			if not self.defect_severity:
				frappe.throw(_("Defect severity is required when defect is shown"))
			if not self.defect_description:
				frappe.throw(_("Defect description is required when defect is shown"))
