# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ReportDataSource(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class
	
	def validate(self):
		"""Validate report_data_source entry"""
		pass
