# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MarketplaceSyncLog(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class
	
	def validate(self):
		"""Validate marketplace_sync_log entry"""
		pass
