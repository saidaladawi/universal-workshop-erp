#!/usr/bin/env python3
"""
Disassembly Plan Controller - Virtual Dismantling Planning System
Comprehensive dismantling plan management with intelligent sequencing algorithms
for automotive scrap yard operations in Oman and UAE markets.
"""

import json
import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document


class DisassemblyPlan(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields to Document class

	def validate(self):
		"""Validate disassembly plan before saving"""
		self.validate_scrap_vehicle_status()
		self.validate_plan_configuration()
		self.calculate_totals()
		self.validate_step_dependencies()

	def before_save(self):
		"""Auto-populate fields and generate plan ID"""
		if not self.plan_id:
			self.plan_id = self.generate_plan_id()

		if not self.created_by:
			self.created_by = frappe.session.user

		if not self.plan_date:
			self.plan_date = frappe.utils.today()

		# Auto-populate vehicle information
		if self.scrap_vehicle:
			self.populate_vehicle_info()

	def on_update(self):
		"""Update related records when plan is modified"""
		if self.has_value_changed("status") and self.status == "In Progress":
			self.create_plan_started_log()

	def validate_scrap_vehicle_status(self):
		"""Ensure scrap vehicle is ready for dismantling"""
		if not self.scrap_vehicle:
			frappe.throw(_("Scrap Vehicle is required"))

		vehicle = frappe.get_doc("Scrap Vehicle", self.scrap_vehicle)

		if vehicle.status not in ["Assessment Complete", "Dismantling Planned"]:
			frappe.throw(
				_("Scrap Vehicle must have completed condition assessment before creating dismantling plan")
			)

	def validate_plan_configuration(self):
		"""Validate dismantling configuration settings"""
		if not self.extraction_strategy:
			self.extraction_strategy = "Value-First"

		if not self.safety_level:
			self.safety_level = "Standard"

		if not self.technician_skill_required:
			self.technician_skill_required = "Intermediate"

	def validate_step_dependencies(self):
		"""Validate that step dependencies are logical"""
		if not self.disassembly_steps:
			return

		steps = {step.step_number: step for step in self.disassembly_steps}

		for step in self.disassembly_steps:
			if step.dependency_step:
				if step.dependency_step not in steps:
					frappe.throw(
						_("Step {0} depends on step {1} which does not exist").format(
							step.step_number, step.dependency_step
						)
					)

				if step.dependency_step >= step.step_number:
					frappe.throw(
						_("Step {0} cannot depend on a later step {1}").format(
							step.step_number, step.dependency_step
						)
					)

	def calculate_totals(self):
		"""Calculate totals from disassembly steps"""
		if not self.disassembly_steps:
			return

		total_time = 0
		total_parts_value = 0
		total_labor_cost = 0
		total_steps = len(self.disassembly_steps)
		completed_steps = 0

		for step in self.disassembly_steps:
			if step.estimated_time_minutes:
				total_time += step.estimated_time_minutes

			if step.estimated_part_value:
				total_parts_value += step.estimated_part_value

			if step.labor_cost:
				total_labor_cost += step.labor_cost

			if step.status == "Completed":
				completed_steps += 1

			# Calculate step totals
			step.total_step_cost = (step.estimated_part_value or 0) + (step.labor_cost or 0)
			if step.labor_cost and step.labor_cost > 0:
				step.value_ratio = ((step.estimated_part_value or 0) / step.labor_cost) * 100

		# Update main totals
		self.estimated_total_time = total_time / 60  # Convert to hours
		self.estimated_parts_value = total_parts_value
		self.estimated_labor_cost = total_labor_cost
		self.total_estimated_cost = total_parts_value + total_labor_cost
		self.total_steps = total_steps
		self.completed_steps = completed_steps

		if total_steps > 0:
			self.progress_percentage = (completed_steps / total_steps) * 100

		# Calculate expected profit
		if self.scrap_vehicle:
			vehicle = frappe.get_doc("Scrap Vehicle", self.scrap_vehicle)
			acquisition_cost = vehicle.acquisition_cost or 0
			self.expected_profit = total_parts_value - acquisition_cost - total_labor_cost

			if total_parts_value > 0:
				self.profit_margin_percentage = (self.expected_profit / total_parts_value) * 100

	def populate_vehicle_info(self):
		"""Auto-populate vehicle information from linked scrap vehicle"""
		vehicle = frappe.get_doc("Scrap Vehicle", self.scrap_vehicle)
		self.vehicle_title = vehicle.vehicle_title
		self.vehicle_title_ar = vehicle.vehicle_title_ar or vehicle.vehicle_title

	def generate_plan_id(self):
		"""Generate unique plan ID: DPLAN-YYYY-0001"""
		year = datetime.now().year

		# Get last plan number for current year
		last_plan = frappe.db.sql(
			"""
            SELECT plan_id FROM `tabDisassembly Plan`
            WHERE plan_id LIKE 'DPLAN-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(year)
		)

		if last_plan and last_plan[0][0]:
			last_num = int(last_plan[0][0].split("-")[-1])
			new_num = last_num + 1
		else:
			new_num = 1

		return f"DPLAN-{year}-{new_num:04d}"

	def create_plan_started_log(self):
		"""Create log entry when plan starts"""
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Disassembly Plan",
				"reference_name": self.name,
				"content": _("Disassembly plan started for {0}").format(self.vehicle_title),
			}
		).insert(ignore_permissions=True)

	@frappe.whitelist()
	def generate_optimal_plan(self):
		"""Generate optimal disassembly plan using intelligent algorithms"""
		if not self.scrap_vehicle:
			frappe.throw(_("Scrap Vehicle is required to generate plan"))

		vehicle = frappe.get_doc("Scrap Vehicle", self.scrap_vehicle)

		# Clear existing steps
		self.disassembly_steps = []

		# Generate steps based on vehicle condition and strategy
		steps = self.calculate_optimal_sequence(vehicle)

		for i, step_data in enumerate(steps):
			step = frappe.new_doc("Disassembly Step")
			step.update(step_data)
			step.step_number = i + 1
			self.append("disassembly_steps", step)

		# Recalculate totals
		self.calculate_totals()

		frappe.msgprint(_("Optimal disassembly plan generated with {0} steps").format(len(steps)))

	def calculate_optimal_sequence(self, vehicle):
		"""Calculate optimal dismantling sequence based on strategy and vehicle condition"""
		# Base part templates with estimated values and extraction difficulty
		part_templates = self.get_part_templates()

		# Filter parts based on vehicle condition and assessment
		available_parts = self.filter_available_parts(part_templates, vehicle)

		# Apply optimization strategy
		if self.extraction_strategy == "Value-First":
			sequence = self.optimize_by_value(available_parts)
		elif self.extraction_strategy == "Safety-First":
			sequence = self.optimize_by_safety(available_parts)
		elif self.extraction_strategy == "Accessibility-First":
			sequence = self.optimize_by_accessibility(available_parts)
		else:
			sequence = self.optimize_custom(available_parts)

		return sequence

	def get_part_templates(self):
		"""Get standardized part templates with extraction data"""
		return [
			{
				"part_category": "Safety Systems",
				"target_part": "Airbag System",
				"target_part_ar": "نظام الوسائد الهوائية",
				"description": "Remove all airbag modules and sensors",
				"description_ar": "إزالة جميع وحدات الوسائد الهوائية والحساسات",
				"safety_instructions": "⚠️ HIGH VOLTAGE RISK - Disconnect battery first, wait 10 minutes",
				"safety_instructions_ar": "⚠️ خطر الجهد العالي - افصل البطارية أولاً، انتظر 10 دقائق",
				"extraction_method": "Special Tools",
				"priority_level": "Critical",
				"estimated_time_minutes": 45,
				"estimated_part_value": 150.000,
				"labor_cost": 15.000,
				"technician_skill_level": "Advanced",
				"safety_level": "Hazardous",
				"required_tools": "Airbag removal tools, multimeter, insulated gloves",
				"dependency_step": None,
				"accessibility_score": 3,
				"safety_priority": 1,
			},
			{
				"part_category": "Electrical",
				"target_part": "Battery",
				"target_part_ar": "البطارية",
				"description": "Disconnect and remove main battery",
				"description_ar": "فصل وإزالة البطارية الرئيسية",
				"safety_instructions": "Wear protective gloves, ensure ignition is OFF",
				"safety_instructions_ar": "ارتدِ قفازات واقية، تأكد من إيقاف تشغيل السيارة",
				"extraction_method": "Manual Removal",
				"priority_level": "Critical",
				"estimated_time_minutes": 15,
				"estimated_part_value": 45.000,
				"labor_cost": 5.000,
				"technician_skill_level": "Beginner",
				"safety_level": "Elevated",
				"required_tools": "10mm wrench, battery terminal puller",
				"dependency_step": None,
				"accessibility_score": 5,
				"safety_priority": 2,
			},
			{
				"part_category": "Engine",
				"target_part": "Catalytic Converter",
				"target_part_ar": "المحول الحفاز",
				"description": "Remove catalytic converter from exhaust system",
				"description_ar": "إزالة المحول الحفاز من نظام العادم",
				"safety_instructions": "Hot surface warning, use safety goggles",
				"safety_instructions_ar": "تحذير من السطح الساخن، استخدم نظارات الأمان",
				"extraction_method": "Cutting Required",
				"priority_level": "High",
				"estimated_time_minutes": 30,
				"estimated_part_value": 200.000,
				"labor_cost": 12.000,
				"technician_skill_level": "Intermediate",
				"safety_level": "Elevated",
				"required_tools": "Angle grinder, safety goggles, heat-resistant gloves",
				"dependency_step": None,
				"accessibility_score": 4,
				"safety_priority": 3,
			},
			{
				"part_category": "Engine",
				"target_part": "Engine Block",
				"target_part_ar": "كتلة المحرك",
				"description": "Remove complete engine assembly",
				"description_ar": "إزالة مجموعة المحرك الكاملة",
				"safety_instructions": "Use engine hoist, ensure stable positioning",
				"safety_instructions_ar": "استخدم رافعة المحرك، تأكد من الوضعية المستقرة",
				"extraction_method": "Hydraulic Lift",
				"priority_level": "High",
				"estimated_time_minutes": 180,
				"estimated_part_value": 800.000,
				"labor_cost": 60.000,
				"technician_skill_level": "Expert",
				"safety_level": "High-Risk",
				"required_tools": "Engine hoist, socket set, hydraulic jack",
				"dependency_step": 2,  # After battery removal
				"accessibility_score": 2,
				"safety_priority": 5,
			},
			{
				"part_category": "Transmission",
				"target_part": "Transmission",
				"target_part_ar": "ناقل الحركة",
				"description": "Remove transmission assembly",
				"description_ar": "إزالة مجموعة ناقل الحركة",
				"safety_instructions": "Heavy component - use transmission jack",
				"safety_instructions_ar": "مكون ثقيل - استخدم رافعة ناقل الحركة",
				"extraction_method": "Hydraulic Lift",
				"priority_level": "Medium",
				"estimated_time_minutes": 120,
				"estimated_part_value": 600.000,
				"labor_cost": 40.000,
				"technician_skill_level": "Advanced",
				"safety_level": "High-Risk",
				"required_tools": "Transmission jack, socket set, drain pan",
				"dependency_step": 4,  # After engine removal
				"accessibility_score": 2,
				"safety_priority": 6,
			},
			{
				"part_category": "Body Parts",
				"target_part": "Front Bumper",
				"target_part_ar": "الصادم الأمامي",
				"description": "Remove front bumper assembly",
				"description_ar": "إزالة مجموعة الصادم الأمامي",
				"safety_instructions": "Check for embedded sensors or wiring",
				"safety_instructions_ar": "تحقق من وجود حساسات أو أسلاك مدمجة",
				"extraction_method": "Manual Removal",
				"priority_level": "Low",
				"estimated_time_minutes": 25,
				"estimated_part_value": 120.000,
				"labor_cost": 8.000,
				"technician_skill_level": "Beginner",
				"safety_level": "Standard",
				"required_tools": "Socket set, trim removal tools",
				"dependency_step": None,
				"accessibility_score": 5,
				"safety_priority": 7,
			},
			{
				"part_category": "Wheels",
				"target_part": "Alloy Wheels",
				"target_part_ar": "الجنوط المعدنية",
				"description": "Remove wheels and tires",
				"description_ar": "إزالة العجلات والإطارات",
				"safety_instructions": "Use proper jack points, wheel chocks",
				"safety_instructions_ar": "استخدم نقاط الرفع الصحيحة، أسافين العجلات",
				"extraction_method": "Manual Removal",
				"priority_level": "Medium",
				"estimated_time_minutes": 20,
				"estimated_part_value": 300.000,
				"labor_cost": 6.000,
				"technician_skill_level": "Beginner",
				"safety_level": "Standard",
				"required_tools": "Jack, lug wrench, wheel chocks",
				"dependency_step": None,
				"accessibility_score": 5,
				"safety_priority": 8,
			},
		]

	def filter_available_parts(self, part_templates, vehicle):
		"""Filter parts based on vehicle condition assessment"""
		available_parts = []

		for part in part_templates:
			# Check if part is likely recoverable based on vehicle condition
			if self.is_part_recoverable(part, vehicle):
				available_parts.append(part.copy())

		return available_parts

	def is_part_recoverable(self, part, vehicle):
		"""Determine if a part is recoverable based on vehicle condition"""
		# Basic logic - can be enhanced with AI/ML in future
		overall_condition = vehicle.overall_condition or "Poor"

		if overall_condition == "Excellent":
			return True
		elif overall_condition == "Good":
			return part["part_category"] != "Body Parts" or part["target_part"] != "Front Bumper"
		elif overall_condition == "Fair":
			return part["part_category"] in [
				"Engine",
				"Transmission",
				"Electrical",
				"Safety Systems",
			]
		else:  # Poor condition
			return part["part_category"] in ["Engine", "Electrical"] and part["target_part"] in [
				"Battery",
				"Catalytic Converter",
			]

	def optimize_by_value(self, parts):
		"""Optimize sequence by part value (highest first)"""
		# Sort by value/cost ratio descending
		parts.sort(
			key=lambda x: (x["estimated_part_value"] or 0) / max(x["labor_cost"] or 1, 1),
			reverse=True,
		)

		# Ensure safety-critical parts (airbags, battery) come first
		safety_critical = [p for p in parts if p["safety_priority"] <= 3]
		other_parts = [p for p in parts if p["safety_priority"] > 3]

		safety_critical.sort(key=lambda x: x["safety_priority"])

		return safety_critical + other_parts

	def optimize_by_safety(self, parts):
		"""Optimize sequence by safety priority"""
		parts.sort(key=lambda x: x["safety_priority"])
		return parts

	def optimize_by_accessibility(self, parts):
		"""Optimize sequence by accessibility (easiest first)"""
		# Sort by accessibility score descending (5 = most accessible)
		parts.sort(key=lambda x: x["accessibility_score"], reverse=True)

		# Still prioritize safety-critical parts
		safety_critical = [p for p in parts if p["safety_priority"] <= 3]
		other_parts = [p for p in parts if p["safety_priority"] > 3]

		safety_critical.sort(key=lambda x: x["safety_priority"])
		other_parts.sort(key=lambda x: x["accessibility_score"], reverse=True)

		return safety_critical + other_parts

	def optimize_custom(self, parts):
		"""Custom optimization balancing all factors"""
		# Weighted scoring: 40% value, 30% safety, 30% accessibility
		for part in parts:
			value_score = (part["estimated_part_value"] or 0) / 100  # Normalize to 0-10 range
			safety_score = 10 - part["safety_priority"]  # Invert so higher is better
			accessibility_score = part["accessibility_score"] * 2  # Scale to 0-10 range

			part["combined_score"] = value_score * 0.4 + safety_score * 0.3 + accessibility_score * 0.3

		parts.sort(key=lambda x: x["combined_score"], reverse=True)

		# Ensure battery and airbags still come first for safety
		battery_parts = [p for p in parts if p["target_part"] in ["Battery", "Airbag System"]]
		other_parts = [p for p in parts if p["target_part"] not in ["Battery", "Airbag System"]]

		battery_parts.sort(key=lambda x: x["safety_priority"])

		return battery_parts + other_parts

	@frappe.whitelist()
	def start_dismantling(self):
		"""Start the dismantling process"""
		if self.status != "Planned":
			frappe.throw(_("Plan must be in Planned status to start dismantling"))

		self.status = "In Progress"

		# Set first step as in progress
		if self.disassembly_steps:
			self.disassembly_steps[0].status = "In Progress"
			self.disassembly_steps[0].started_time = frappe.utils.now()

		self.save()
		frappe.msgprint(_("Dismantling process started"))

	@frappe.whitelist()
	def complete_step(self, step_number, actual_time_minutes=None, technician_notes=None):
		"""Mark a step as completed and advance to next step"""
		step = None
		for s in self.disassembly_steps:
			if s.step_number == int(step_number):
				step = s
				break

		if not step:
			frappe.throw(_("Step {0} not found").format(step_number))

		if step.status != "In Progress":
			frappe.throw(_("Step {0} is not in progress").format(step_number))

		# Mark current step as completed
		step.status = "Completed"
		step.completed_time = frappe.utils.now()

		if actual_time_minutes:
			step.actual_time_minutes = int(actual_time_minutes)

		# Start next available step
		next_step = self.get_next_available_step(int(step_number))
		if next_step:
			next_step.status = "In Progress"
			next_step.started_time = frappe.utils.now()

		# Update totals and check if plan is complete
		self.calculate_totals()

		if self.progress_percentage >= 100:
			self.status = "Completed"

		self.save()

		if next_step:
			frappe.msgprint(
				_("Step {0} completed. Step {1} started.").format(step_number, next_step.step_number)
			)
		else:
			frappe.msgprint(_("Step {0} completed. All steps finished!").format(step_number))

	def get_next_available_step(self, completed_step_number):
		"""Get the next step that can be started"""
		for step in self.disassembly_steps:
			if step.status == "Pending":
				# Check if dependencies are satisfied
				if not step.dependency_step or step.dependency_step <= completed_step_number:
					return step
		return None

	@frappe.whitelist()
	def get_mobile_checklist(self):
		"""Generate mobile-friendly checklist for technicians"""
		checklist = {
			"plan_id": self.plan_id,
			"vehicle": self.vehicle_title,
			"status": self.status,
			"progress": self.progress_percentage,
			"steps": [],
		}

		for step in self.disassembly_steps:
			step_data = {
				"number": step.step_number,
				"title": step.step_title,
				"title_ar": step.step_title_ar,
				"part": step.target_part,
				"part_ar": step.target_part_ar,
				"status": step.status,
				"estimated_time": step.estimated_time_minutes,
				"safety_level": step.safety_level,
				"required_tools": step.required_tools,
				"safety_instructions": step.safety_instructions,
				"safety_instructions_ar": step.safety_instructions_ar,
				"can_start": self.can_start_step(step),
			}
			checklist["steps"].append(step_data)

		return checklist

	def can_start_step(self, step):
		"""Check if a step can be started based on dependencies"""
		if step.status != "Pending":
			return False

		if step.dependency_step:
			dependency = None
			for s in self.disassembly_steps:
				if s.step_number == step.dependency_step:
					dependency = s
					break
			if dependency and dependency.status != "Completed":
				return False

		return True


# Whitelisted API methods for external access
@frappe.whitelist()
def get_disassembly_plans(status=None, limit=20):
	"""Get list of disassembly plans with optional status filter"""
	filters = {}
	if status:
		filters["status"] = status

	return frappe.get_list(
		"Disassembly Plan",
		filters=filters,
		fields=[
			"name",
			"plan_id",
			"scrap_vehicle",
			"vehicle_title",
			"vehicle_title_ar",
			"status",
			"plan_date",
			"progress_percentage",
			"estimated_total_time",
			"expected_profit",
		],
		order_by="plan_date desc",
		limit=limit,
	)


@frappe.whitelist()
def get_plan_statistics():
	"""Get statistics for planning dashboard"""
	stats = frappe.db.sql(
		"""
        SELECT 
            status,
            COUNT(*) as count,
            AVG(progress_percentage) as avg_progress,
            SUM(expected_profit) as total_expected_profit
        FROM `tabDisassembly Plan`
        GROUP BY status
    """,
		as_dict=True,
	)

	return stats


@frappe.whitelist()
def create_plan_from_vehicle(scrap_vehicle_id, extraction_strategy="Value-First"):
	"""Create a new disassembly plan for a scrap vehicle"""
	# Validate vehicle exists and is ready
	vehicle = frappe.get_doc("Scrap Vehicle", scrap_vehicle_id)

	if vehicle.status not in ["Assessment Complete", "Dismantling Planned"]:
		frappe.throw(_("Vehicle must complete condition assessment first"))

	# Create new plan
	plan = frappe.new_doc("Disassembly Plan")
	plan.scrap_vehicle = scrap_vehicle_id
	plan.extraction_strategy = extraction_strategy
	plan.status = "Draft"
	plan.insert()

	# Generate optimal plan
	plan.generate_optimal_plan()
	plan.status = "Planned"
	plan.save()

	return plan.name
