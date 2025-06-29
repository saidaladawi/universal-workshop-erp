# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt
# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class


import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class Technician(Document):
	def validate(self):
		"""Validate technician data"""
		self.validate_arabic_name()
		self.validate_phone_number()
		self.validate_capacity()
		self.update_workload_metrics()

	def validate_arabic_name(self):
		"""Ensure Arabic technician name is provided"""
		if not self.technician_name_ar:
			frappe.throw(_("Arabic technician name is required"))

	def validate_phone_number(self):
		"""Validate Oman phone number format"""
		if self.phone and not self.phone.startswith("+968"):
			frappe.throw(_("Phone number must start with +968 for Oman"))

	def validate_capacity(self):
		"""Validate capacity settings"""
		if self.capacity_hours_per_day <= 0:
			frappe.throw(_("Capacity hours per day must be greater than 0"))
		if self.max_concurrent_jobs <= 0:
			frappe.throw(_("Max concurrent jobs must be greater than 0"))

	def before_save(self):
		"""Set default values before saving"""
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_date:
			self.created_date = frappe.utils.today()

		# Update availability based on employment status
		if self.employment_status in ["Inactive", "OnLeave", "Terminated"]:
			self.is_available = 0

	def update_workload_metrics(self):
		"""Update current workload and performance metrics"""
		# Calculate current workload from active service orders
		workload_result = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(estimated_hours - completed_hours), 0)
			FROM `tabService Order`
			WHERE assigned_technician = %s
			AND status IN ('Assigned', 'In Progress')
			""",
			[self.name],
			as_list=True
		)
		current_workload = workload_result[0][0] if workload_result else 0
		self.current_workload_hours = flt(current_workload)

		# Update performance metrics
		self.update_performance_metrics()

	def update_performance_metrics(self):
		"""Calculate and update performance metrics"""
		# Total completed jobs
		completed_jobs = frappe.db.count(
			"Service Order", {"assigned_technician": self.name, "status": "Completed"}
		)
		self.total_jobs_completed = completed_jobs

		# Average job completion time
		if completed_jobs > 0:
			avg_result = frappe.db.sql(
				"""
				SELECT AVG(completed_hours)
				FROM `tabService Order`
				WHERE assigned_technician = %s
				AND status = 'Completed'
				AND completed_hours > 0
				""",
				[self.name],
				as_list=True
			)
			avg_time = avg_result[0][0] if avg_result else 0
			self.average_job_time_hours = flt(avg_time, 2)

		# Update last assignment date
		last_result = frappe.db.sql(
			"""
			SELECT MAX(creation)
			FROM `tabService Order`
			WHERE assigned_technician = %s
			""",
			[self.name],
			as_list=True
		)
		last_assignment = last_result[0][0] if last_result else None

		if last_assignment:
			self.last_assignment_date = last_assignment

	@frappe.whitelist()
	def get_skill_proficiency(self, skill_name):
		"""Get technician's proficiency level for a specific skill"""
		skill_data = frappe.db.get_value(
			"Technician Skills",
			{"parent": self.name, "skill": skill_name},
			["proficiency_level", "years_experience"],
			as_dict=True,
		)
		return skill_data if skill_data else None

	@frappe.whitelist()
	def get_availability_score(self):
		"""Calculate availability score for assignment algorithm"""
		if not self.is_available or self.employment_status != "Active":
			return 0

		# Base score from workload (higher availability = higher score)
		# Calculate workload ratio (5 working days)
		daily_capacity = self.capacity_hours_per_day * 5
		workload_ratio = self.current_workload_hours / daily_capacity
		availability_score = max(0, 100 - (workload_ratio * 100))

		# Adjust based on performance ratings
		# Calculate performance multiplier from ratings
		total_ratings = (
			(self.performance_rating or 3) + 
			(self.efficiency_rating or 3) + 
			(self.quality_rating or 3)
		)
		performance_multiplier = total_ratings / 15  # Average of 3 ratings out of 5

		final_score = availability_score * performance_multiplier
		return flt(final_score, 2)

	@frappe.whitelist()
	def get_skill_match_score(self, required_skills):
		"""Calculate skill matching score for specific service requirements"""
		if not required_skills:
			return 0

		if isinstance(required_skills, str):
			required_skills = json.loads(required_skills)

		total_score = 0
		matched_skills = 0

		for skill_req in required_skills:
			skill_name = skill_req.get("skill")
			required_level = skill_req.get("level", "Beginner")
			is_mandatory = skill_req.get("mandatory", False)

			technician_skill = self.get_skill_proficiency(skill_name)

			if technician_skill:
				# Calculate skill level score
				level_scores = {
					"Beginner": 1,
					"Intermediate": 2,
					"Advanced": 3,
					"Expert": 4,
				}
				tech_level_score = level_scores.get(technician_skill.proficiency_level, 0)
				req_level_score = level_scores.get(required_level, 1)

				if tech_level_score >= req_level_score:
					# Bonus for exceeding requirements
					skill_score = 100 + ((tech_level_score - req_level_score) * 25)
					# Experience bonus
					experience_bonus = min(technician_skill.years_experience * 5, 25)
					skill_score += experience_bonus
				else:
					# Penalty for not meeting requirements
					skill_score = (tech_level_score / req_level_score) * 60

				total_score += skill_score
				matched_skills += 1
			else:
				# No skill found
				if is_mandatory:
					return 0  # Mandatory skill missing
				total_score += 0  # Optional skill missing

		if matched_skills == 0:
			return 0

		average_score = total_score / len(required_skills)
		return flt(average_score, 2)

	@frappe.whitelist()
	def assign_to_service_order(self, service_order_id, estimated_hours=None):
		"""Assign technician to a service order"""
		# Validate availability
		if not self.is_available:
			frappe.throw(_("Technician {0} is not available").format(self.technician_name))

		# Check workload capacity
		if estimated_hours:
			future_workload = self.current_workload_hours + flt(estimated_hours)
			max_workload = self.capacity_hours_per_day * 5  # 5 working days buffer

			if future_workload > max_workload:
				frappe.throw(_("Assignment would exceed technician's capacity"))

		# Update service order
		service_order = frappe.get_doc("Service Order", service_order_id)
		service_order.assigned_technician = self.name
		service_order.assignment_date = now_datetime()
		if estimated_hours:
			service_order.estimated_hours = estimated_hours
		service_order.save()

		# Update technician metrics
		self.update_workload_metrics()
		self.save()

		return service_order

	@staticmethod
	@frappe.whitelist()
	def get_available_technicians(department=None, skills=None):
		"""Get list of available technicians, optionally filtered by department and skills"""
		filters = {"is_available": 1, "employment_status": "Active"}

		if department:
			filters["department"] = department

		technicians = frappe.get_all(
			"Technician",
			filters=filters,
			fields=[
				"name",
				"technician_name",
				"technician_name_ar",
				"department",
				"current_workload_hours",
				"capacity_hours_per_day",
				"performance_rating",
			],
		)

		# If skills are specified, filter by skill requirements
		if skills and isinstance(skills, str):
			skills = json.loads(skills)

		filtered_technicians = []
		for tech in technicians:
			if skills:
				tech_doc = frappe.get_doc("Technician", tech.name)
				skill_score = tech_doc.get_skill_match_score(skills)
				if skill_score > 50:  # Minimum skill threshold
					tech["skill_match_score"] = skill_score
					tech["availability_score"] = tech_doc.get_availability_score()
					filtered_technicians.append(tech)
			else:
				tech_doc = frappe.get_doc("Technician", tech.name)
				tech["availability_score"] = tech_doc.get_availability_score()
				filtered_technicians.append(tech)

		# Sort by availability and skill scores
		filtered_technicians.sort(
			key=lambda x: (x.get("skill_match_score", 0) + x.get("availability_score", 0)),
			reverse=True,
		)

		return filtered_technicians

	@staticmethod
	@frappe.whitelist()
	def suggest_technician_assignment(service_order_id):
		"""Suggest best technician for a service order using assignment algorithm"""
		service_order = frappe.get_doc("Service Order", service_order_id)

		# Get service requirements
		required_skills = []
		if hasattr(service_order, "required_skills"):
			required_skills = service_order.required_skills

		# Get available technicians
		available_technicians = Technician.get_available_technicians(
			department=getattr(service_order, "department", None),
			skills=json.dumps(required_skills) if required_skills else None,
		)

		if not available_technicians:
			return {"error": _("No available technicians found")}

		# Get the best match
		best_technician = available_technicians[0]

		return {
			"recommended_technician": best_technician,
			"all_options": available_technicians[:5],  # Top 5 options
			"assignment_confidence": flt(
				(best_technician.get("skill_match_score", 0) + best_technician.get("availability_score", 0))
				/ 2,
				2,
			),
		}
