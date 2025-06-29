# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LicenseActivityLog(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class
	
	def validate(self):
		"""Validate license activity log entry"""
		self.validate_license_id()
		self.set_default_timestamp()
		self.set_default_user()
	
	def validate_license_id(self):
		"""Ensure license ID is provided"""
		if not self.license_id:
			frappe.throw(frappe._("License ID is required"))
	
	def set_default_timestamp(self):
		"""Set default timestamp if not provided"""
		if not self.timestamp:
			self.timestamp = frappe.utils.now()
	
	def set_default_user(self):
		"""Set current user if not specified"""
		if not self.user_involved:
			self.user_involved = frappe.session.user 