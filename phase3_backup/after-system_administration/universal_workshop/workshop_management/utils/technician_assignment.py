# Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


class TechnicianAssignmentEngine:
	"""Advanced technician assignment algorithm with skills matrix"""

	def __init__(self):
		self.skill_weight = 0.4  # 40% weight for skill matching
		self.availability_weight = 0.3  # 30% weight for availability
		self.performance_weight = 0.2  # 20% weight for performance
		self.proximity_weight = 0.1  # 10% weight for location proximity

	@frappe.whitelist()
	def suggest_assignment(self, service_order_id, department=None, required_skills=None):
		"""Main method to suggest technician assignment for a service order"""
		try:
			# Get available technicians
			available_technicians = self._get_available_technicians(department)

			if not available_technicians:
				return {
					"success": False,
					"message": _("No available technicians found"),
					"technicians": [],
				}

			# Score each technician
			scored_technicians = []
			for tech in available_technicians:
				score_data = self._calculate_technician_score(tech["name"], required_skills)

				if score_data["total_score"] > 0:
					tech.update(score_data)
					scored_technicians.append(tech)

			# Sort by total score (descending)
			scored_technicians.sort(key=lambda x: x["total_score"], reverse=True)

			return {
				"success": True,
				"service_order": service_order_id,
				"recommended_technician": (scored_technicians[0] if scored_technicians else None),
				"alternatives": scored_technicians[1:6],  # Top 5 alternatives
				"total_candidates": len(scored_technicians),
			}

		except Exception as e:
			frappe.log_error(message=str(e), title="Technician Assignment Error")
			return {
				"success": False,
				"message": _("Error in assignment algorithm: {0}").format(str(e)),
				"technicians": [],
			}

	def _get_available_technicians(self, department=None):
		"""Get list of available technicians with basic info"""
		filters = {"is_available": 1, "employment_status": "Active"}

		if department:
			filters["department"] = department

		return frappe.get_all(
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
				"efficiency_rating",
				"quality_rating",
			],
		)

	def _calculate_technician_score(self, technician_id, required_skills):
		"""Calculate overall score for a technician"""
		technician = frappe.get_doc("Technician", technician_id)

		# Calculate component scores
		skill_score = self._calculate_skill_score(technician, required_skills)
		availability_score = self._calculate_availability_score(technician)
		performance_score = self._calculate_performance_score(technician)
		proximity_score = 70.0  # Default proximity score

		# Calculate weighted total score
		total_score = (
			(skill_score * self.skill_weight)
			+ (availability_score * self.availability_weight)
			+ (performance_score * self.performance_weight)
			+ (proximity_score * self.proximity_weight)
		)

		return {
			"skill_score": flt(skill_score, 2),
			"availability_score": flt(availability_score, 2),
			"performance_score": flt(performance_score, 2),
			"proximity_score": flt(proximity_score, 2),
			"total_score": flt(total_score, 2),
		}

	def _calculate_skill_score(self, technician, required_skills):
		"""Calculate skill matching score"""
		if not required_skills:
			return 75  # Default score when no specific skills required

		if isinstance(required_skills, str):
			try:
				required_skills = json.loads(required_skills)
			except ValueError:
				return 75

		total_score = 0
		skill_count = len(required_skills)

		for skill_req in required_skills:
			skill_name = skill_req.get("skill")
			required_level = skill_req.get("level", "Beginner")

			# Get technician's proficiency for this skill
			tech_skill = frappe.db.get_value(
				"Technician Skills",
				{"parent": technician.name, "skill": skill_name, "is_active": 1},
				["proficiency_level", "years_experience"],
				as_dict=True,
			)

			if tech_skill:
				skill_score = self._calculate_single_skill_score(tech_skill, required_level)
				total_score += skill_score
			else:
				total_score += 20  # Partial score for missing skill

		return flt(total_score / skill_count if skill_count > 0 else 75, 2)

	def _calculate_single_skill_score(self, tech_skill, required_level):
		"""Calculate score for a single skill match"""
		level_scores = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}

		tech_level = level_scores.get(tech_skill.proficiency_level, 0)
		req_level = level_scores.get(required_level, 1)

		if tech_level >= req_level:
			base_score = 80
			excess_bonus = (tech_level - req_level) * 10
			exp_bonus = min(tech_skill.years_experience * 2, 10)
			return min(100, base_score + excess_bonus + exp_bonus)
		else:
			shortage_penalty = (req_level - tech_level) * 20
			return max(0, 60 - shortage_penalty)

	def _calculate_availability_score(self, technician):
		"""Calculate availability score based on current workload"""
		current_workload = flt(technician.current_workload_hours)
		capacity_per_week = flt(technician.capacity_hours_per_day) * 5

		if capacity_per_week <= 0:
			return 0

		workload_ratio = current_workload / capacity_per_week

		if workload_ratio <= 0.3:
			return 100
		elif workload_ratio <= 0.6:
			return 80
		elif workload_ratio <= 0.8:
			return 60
		elif workload_ratio <= 1.0:
			return 40
		else:
			return 20

	def _calculate_performance_score(self, technician):
		"""Calculate performance score based on ratings"""
		performance_rating = flt(technician.performance_rating) or 3
		efficiency_rating = flt(technician.efficiency_rating) or 3
		quality_rating = flt(technician.quality_rating) or 3

		# Convert to 100-point scale and calculate weighted average
		performance_score = (performance_rating / 5) * 100
		efficiency_score = (efficiency_rating / 5) * 100
		quality_score = (quality_rating / 5) * 100

		combined_score = performance_score * 0.4 + efficiency_score * 0.3 + quality_score * 0.3

		return flt(combined_score, 2)


# Global instance for use in other modules
assignment_engine = TechnicianAssignmentEngine()


@frappe.whitelist()
def suggest_technician_assignment(service_order_id, department=None, required_skills=None):
	"""Wrapper function for API access"""
	return assignment_engine.suggest_assignment(service_order_id, department, required_skills)


@frappe.whitelist()
def assign_technician_to_service(service_order_id, technician_id, estimated_hours=None):
	"""Assign technician to service order"""
	try:
		service_order = frappe.get_doc("Service Order", service_order_id)
		technician = frappe.get_doc("Technician", technician_id)

		if not technician.is_available:
			frappe.throw(_("Technician {0} is not available").format(technician.technician_name))

		service_order.assigned_technician = technician_id
		service_order.assignment_date = now_datetime()
		service_order.status = "Assigned"

		if estimated_hours:
			service_order.estimated_hours = estimated_hours

		service_order.save()
		technician.save()

		return {"success": True, "message": _("Technician assigned successfully")}

	except Exception as e:
		return {"success": False, "message": str(e)}
