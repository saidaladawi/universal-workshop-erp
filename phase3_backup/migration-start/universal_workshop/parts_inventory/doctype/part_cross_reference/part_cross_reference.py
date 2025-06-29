# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

from frappe import _
from frappe.model.document import Document


class PartCrossReference(Document):
	"""Child table for storing cross-reference part numbers from different manufacturers"""

	def validate(self):
		"""Validate cross reference data"""
		self.validate_cross_ref_number()
		self.validate_primary_reference()

	def validate_cross_ref_number(self):
		"""Ensure cross reference number is provided and valid"""
		if not self.cross_ref_number:
			frappe.throw(_("Cross Reference Number is required"))

		# Remove extra spaces and convert to uppercase for consistency
		self.cross_ref_number = self.cross_ref_number.strip().upper()

	def validate_primary_reference(self):
		"""Ensure only one primary reference per part"""
		if self.is_primary and self.parent:
			# Check if another primary reference exists
			existing_primary = frappe.db.sql(
				"""
                SELECT name FROM `tabPart Cross Reference`
                WHERE parent = %s AND is_primary = 1 AND name != %s
            """,
				(self.parent, self.name or ""),
			)

			if existing_primary:
				frappe.throw(_("Only one primary cross reference is allowed per part"))
