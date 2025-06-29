# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import contextlib
from datetime import datetime

import frappe
from frappe import _
from frappe.model.document import Document


class OnboardingProgress(Document):
	def validate(self):
		"""Validate onboarding progress data"""
		self.validate_user_uniqueness()
		self.update_progress_percentage()
		self.validate_completion_status()

	def validate_user_uniqueness(self):
		"""Ensure user has only one active onboarding session"""
		if self.docstatus == 0:  # Only for draft documents
			existing = frappe.db.exists(
				"Onboarding Progress", {"user": self.user, "docstatus": 0, "name": ["!=", self.name]}
			)

			if existing:
				frappe.throw(_("User already has an active onboarding session: {0}").format(existing))

	def update_progress_percentage(self):
		"""Calculate and update progress percentage"""
		if self.completed_steps:
			try:
				completed_steps_list = frappe.parse_json(self.completed_steps)
				total_steps = (
					5  # basic_info, business_info, contact_info, operational_details, financial_info
				)
				self.progress_percentage = (len(completed_steps_list) / total_steps) * 100
			except Exception:
				self.progress_percentage = 0
		else:
			self.progress_percentage = 0

	def validate_completion_status(self):
		"""Update status based on completion"""
		if self.progress_percentage == 100 and self.workshop_profile:
			self.status = "Completed"
			if not self.completed_on:
				self.completed_on = datetime.now()
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def get_step_data(self, step_name):
		"""Get data for specific step"""
		if self.data:
			try:
				data = frappe.parse_json(self.data)
				return data.get(step_name, {})
			except Exception:
				return {}
		return {}

	def is_step_completed(self, step_name):
		"""Check if specific step is completed"""
		if self.completed_steps:
			try:
				completed_steps_list = frappe.parse_json(self.completed_steps)
				return step_name in completed_steps_list
			except Exception:
				return False
		return False

	def get_next_step(self):
		"""Get the next step to be completed"""
		steps = ["basic_info", "business_info", "contact_info", "operational_details", "financial_info"]

		if self.completed_steps:
			try:
				completed_steps_list = frappe.parse_json(self.completed_steps)
				for step in steps:
					if step not in completed_steps_list:
						return step
			except Exception:
				return steps[0]

		return steps[0] if self.current_step == 0 else None

	def get_progress_summary(self):
		"""Get comprehensive progress summary"""
		steps = ["basic_info", "business_info", "contact_info", "operational_details", "financial_info"]
		step_labels = {
			"basic_info": _("Basic Information"),
			"business_info": _("Business Information"),
			"contact_info": _("Contact Information"),
			"operational_details": _("Operational Details"),
			"financial_info": _("Financial Information"),
		}

		completed_steps_list = []
		if self.completed_steps:
			with contextlib.suppress(Exception):
				completed_steps_list = frappe.parse_json(self.completed_steps)

		summary = {
			"total_steps": len(steps),
			"completed_count": len(completed_steps_list),
			"progress_percentage": self.progress_percentage,
			"current_step": self.current_step,
			"next_step": self.get_next_step(),
			"status": self.status,
			"steps": [],
		}

		for i, step in enumerate(steps):
			summary["steps"].append(
				{
					"step_name": step,
					"step_label": step_labels.get(step, step),
					"step_number": i + 1,
					"is_completed": step in completed_steps_list,
					"is_current": i == self.current_step,
					"has_data": bool(self.get_step_data(step)),
				}
			)

		return summary


@frappe.whitelist()
def get_user_onboarding_progress(user=None):
	"""Get active onboarding progress for user"""
	if not user:
		user = frappe.session.user

	progress = frappe.db.get_value(
		"Onboarding Progress",
		{"user": user, "docstatus": 0},
		["name", "current_step", "progress_percentage", "status"],
		as_dict=True,
	)

	if progress:
		doc = frappe.get_doc("Onboarding Progress", progress.name)
		return doc.get_progress_summary()

	return None


@frappe.whitelist()
def cancel_user_onboarding(user=None, reason="User requested cancellation"):
	"""Cancel active onboarding for user"""
	if not user:
		user = frappe.session.user

	progress = frappe.db.get_value("Onboarding Progress", {"user": user, "docstatus": 0}, "name")

	if progress:
		doc = frappe.get_doc("Onboarding Progress", progress)
		doc.add_comment("Info", f"Onboarding cancelled: {reason}")
		doc.cancel()

		return {"success": True, "message": _("Onboarding cancelled successfully")}

	return {"success": False, "message": _("No active onboarding found")}
