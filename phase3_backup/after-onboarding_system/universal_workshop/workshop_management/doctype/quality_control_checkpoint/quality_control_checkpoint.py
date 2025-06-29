# Copyright (c) 2025, Said Al-Adowi and contributors
# For license information, please see license.txt
# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

import json
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, get_time, flt


class QualityControlCheckpoint(Document):
	def validate(self):
		"""Validate quality control checkpoint data"""
		self.validate_arabic_names()
		self.validate_dates()
		self.validate_assignments()
		self.validate_workflow_status()

	def validate_arabic_names(self):
		"""Ensure Arabic names are provided"""
		if not self.checkpoint_name_ar:
			# Auto-translate common checkpoint names
			translations = {
				"Pre-Service Inspection": "فحص ما قبل الخدمة",
				"In-Progress Check": "فحص أثناء العمل", 
				"Quality Control": "مراقبة الجودة",
				"Final Inspection": "الفحص النهائي",
				"Customer Handover": "تسليم العميل"
			}
			
			if self.checkpoint_name in translations:
				self.checkpoint_name_ar = translations[self.checkpoint_name]
			else:
				frappe.throw(_("Arabic checkpoint name is required"))

	def validate_dates(self):
		"""Validate date constraints"""
		if self.assigned_date and self.due_date:
			if self.assigned_date > self.due_date:
				frappe.throw(_("Due date cannot be before assigned date"))
		
		if self.completion_date and self.assigned_date:
			if self.completion_date < self.assigned_date:
				frappe.throw(_("Completion date cannot be before assigned date"))

	def validate_assignments(self):
		"""Validate technician and supervisor assignments"""
		if self.assigned_technician:
			# Check if technician is available and active
			tech_doc = frappe.get_doc("Technician", self.assigned_technician)
			if not tech_doc.is_available:
				frappe.throw(_("Assigned technician {0} is not available").format(
					tech_doc.technician_name
				))

		if self.status in ["Completed", "Approved"] and not self.assigned_supervisor:
			if self.is_mandatory or self.priority_level in ["High", "Critical"]:
				frappe.throw(_("Supervisor assignment required for mandatory/critical checkpoints"))

	def validate_workflow_status(self):
		"""Validate status transitions"""
		if self.has_value_changed("status"):
			old_status = self.get_doc_before_save().get("status") if self.get_doc_before_save() else None
			new_status = self.status
			
			# Define valid status transitions
			valid_transitions = {
				"Pending": ["In Progress", "Skipped"],
				"In Progress": ["Completed", "Pending"],
				"Completed": ["Approved", "Rejected", "In Progress"],
				"Approved": [],  # Final state
				"Rejected": ["In Progress", "Pending"],
				"Skipped": ["In Progress", "Pending"]
			}
			
			if old_status and new_status not in valid_transitions.get(old_status, []):
				frappe.throw(_("Invalid status transition from {0} to {1}").format(
					old_status, new_status
				))

	def before_save(self):
		"""Set default values and auto-assignments"""
		if not self.checkpoint_id:
			self.checkpoint_id = self.generate_checkpoint_id()
		
		if not self.assigned_date and self.assigned_technician:
			self.assigned_date = now_datetime()
		
		# Auto-set due date based on checkpoint type
		if not self.due_date and self.assigned_date:
			self.due_date = self.calculate_due_date()
		
		# Set completion timestamp
		if self.status == "Completed" and not self.completion_date:
			self.completion_date = now_datetime()
			self.completed_by = frappe.session.user
		
		# Set approval timestamp
		if self.status == "Approved" and not self.approval_date:
			self.approval_date = now_datetime()
			self.approval_by = frappe.session.user

	def on_update(self):
		"""Update related documents and trigger notifications"""
		self.update_service_order_status()
		self.send_notifications()
		self.update_quality_metrics()

	def generate_checkpoint_id(self):
		"""Generate unique checkpoint ID"""
		service_order_id = self.service_order.split("-")[-1] if self.service_order else "0000"
		checkpoint_type_abbr = {
			"Pre-Service": "PS",
			"In-Progress": "IP", 
			"Pre-Delivery": "PD",
			"Final Quality Check": "FQ",
			"Customer Handover": "CH"
		}.get(self.checkpoint_type, "GN")
		
		# Count existing checkpoints for this service order
		count = frappe.db.count("Quality Control Checkpoint", {
			"service_order": self.service_order,
			"checkpoint_type": self.checkpoint_type
		}) + 1
		
		return f"QC-{service_order_id}-{checkpoint_type_abbr}-{count:02d}"

	def calculate_due_date(self):
		"""Calculate due date based on checkpoint type"""
		if not self.assigned_date:
			return None
		
		# Default durations in hours
		durations = {
			"Pre-Service": 2,
			"In-Progress": 4,
			"Pre-Delivery": 1,
			"Final Quality Check": 2,
			"Customer Handover": 0.5
		}
		
		duration_hours = durations.get(self.checkpoint_type, 2)
		return self.assigned_date + timedelta(hours=duration_hours)

	def update_service_order_status(self):
		"""Update related service order status based on checkpoint completion"""
		if not self.service_order:
			return
		
		service_order = frappe.get_doc("Service Order", self.service_order)
		
		# Get all checkpoints for this service order
		checkpoints = frappe.get_all(
			"Quality Control Checkpoint",
			filters={"service_order": self.service_order},
			fields=["status", "is_mandatory", "checkpoint_type"]
		)
		
		# Check if all mandatory checkpoints are approved
		mandatory_checkpoints = [cp for cp in checkpoints if cp.is_mandatory]
		approved_mandatory = [cp for cp in mandatory_checkpoints if cp.status == "Approved"]
		
		# Update service order status based on checkpoint progress
		if len(approved_mandatory) == len(mandatory_checkpoints) and mandatory_checkpoints:
			if service_order.status != "Quality Check Passed":
				service_order.status = "Quality Check Passed"
				service_order.save()
				
				frappe.msgprint(_("All mandatory quality checkpoints approved. Service order ready for delivery."))

	def send_notifications(self):
		"""Send notifications for status changes"""
		if self.has_value_changed("status"):
			self.send_status_notification()
		
		if self.has_value_changed("assigned_technician"):
			self.send_assignment_notification()
		
		if self.status == "Completed" and self.assigned_supervisor:
			self.send_approval_request()

	def send_status_notification(self):
		"""Send status change notification"""
		recipients = []
		
		if self.assigned_technician:
			tech_user = frappe.db.get_value("Technician", self.assigned_technician, "user_id")
			if tech_user:
				recipients.append(tech_user)
		
		if self.assigned_supervisor:
			recipients.append(self.assigned_supervisor)
		
		if recipients:
			frappe.sendmail(
				recipients=recipients,
				subject=_("Quality Checkpoint Status Update: {0}").format(self.checkpoint_name),
				message=_("Checkpoint {0} status changed to {1}").format(
					self.checkpoint_name, self.status
				)
			)

	def send_assignment_notification(self):
		"""Send assignment notification to technician"""
		if self.assigned_technician:
			tech_user = frappe.db.get_value("Technician", self.assigned_technician, "user_id")
			if tech_user:
				frappe.sendmail(
					recipients=[tech_user],
					subject=_("New Quality Checkpoint Assignment: {0}").format(self.checkpoint_name),
					message=_("You have been assigned checkpoint: {0}").format(self.checkpoint_name)
				)

	def send_approval_request(self):
		"""Send approval request to supervisor"""
		if self.assigned_supervisor:
			frappe.sendmail(
				recipients=[self.assigned_supervisor],
				subject=_("Quality Checkpoint Approval Required: {0}").format(self.checkpoint_name),
				message=_("Checkpoint {0} requires your approval").format(self.checkpoint_name)
			)

	def update_quality_metrics(self):
		"""Update quality metrics and scores"""
		if self.status == "Approved":
			self.calculate_quality_score()

	def calculate_quality_score(self):
		"""Calculate quality score based on various factors"""
		score = 100  # Start with perfect score
		
		# Deduct points for defects
		if self.defects_found:
			score -= min(self.defects_found * 5, 30)  # Max 30 points deduction
		
		# Deduct points for rework
		if self.rework_required:
			score -= 15
		
		# Deduct points for delays
		if self.completion_date and self.due_date:
			if self.completion_date > self.due_date:
				delay_hours = (self.completion_date - self.due_date).total_seconds() / 3600
				score -= min(delay_hours * 2, 20)  # Max 20 points for delays
		
		# Adjust based on customer impact
		impact_penalties = {
			"Critical": 25,
			"High": 15,
			"Medium": 10,
			"Low": 5,
			"None": 0
		}
		score -= impact_penalties.get(self.customer_impact, 0)
		
		self.quality_score = max(0, score)  # Ensure non-negative score

	@frappe.whitelist()
	def complete_checkpoint(self, inspection_results=None, photos=None):
		"""Complete checkpoint with results and documentation"""
		if self.status != "In Progress":
			frappe.throw(_("Only in-progress checkpoints can be completed"))
		
		self.status = "Completed"
		self.completion_date = now_datetime()
		self.completed_by = frappe.session.user
		
		if inspection_results:
			self.inspection_results = inspection_results
		
		if photos:
			self.add_photos(photos)
		
		self.save()
		
		return {
			"success": True,
			"message": _("Checkpoint completed successfully"),
			"message_ar": "تم إكمال نقطة التفتيش بنجاح"
		}

	@frappe.whitelist()
	def approve_checkpoint(self, approval_notes=None):
		"""Approve completed checkpoint"""
		if self.status != "Completed":
			frappe.throw(_("Only completed checkpoints can be approved"))
		
		# Check if user has supervisor permissions
		if not self.can_approve():
			frappe.throw(_("You don't have permission to approve this checkpoint"))
		
		self.status = "Approved"
		self.approval_date = now_datetime()
		self.approval_by = frappe.session.user
		
		if approval_notes:
			self.approval_notes = approval_notes
		
		self.save()
		
		return {
			"success": True,
			"message": _("Checkpoint approved successfully"),
			"message_ar": "تم اعتماد نقطة التفتيش بنجاح"
		}

	@frappe.whitelist()
	def reject_checkpoint(self, rejection_reason):
		"""Reject checkpoint with reason"""
		if self.status != "Completed":
			frappe.throw(_("Only completed checkpoints can be rejected"))
		
		if not self.can_approve():
			frappe.throw(_("You don't have permission to reject this checkpoint"))
		
		self.status = "Rejected"
		self.approval_notes = rejection_reason
		
		self.save()
		
		return {
			"success": True,
			"message": _("Checkpoint rejected"),
			"message_ar": "تم رفض نقطة التفتيش"
		}

	def can_approve(self):
		"""Check if current user can approve this checkpoint"""
		user_roles = frappe.get_roles(frappe.session.user)
		
		# Workshop managers and quality inspectors can approve
		if "Workshop Manager" in user_roles or "Quality Control Inspector" in user_roles:
			return True
		
		# Assigned supervisor can approve
		if self.assigned_supervisor == frappe.session.user:
			return True
		
		return False

	def add_photos(self, photos_data):
		"""Add photos from mobile camera or upload"""
		if not isinstance(photos_data, list):
			photos_data = [photos_data]
		
		for photo_data in photos_data:
			if isinstance(photo_data, str) and photo_data.startswith('data:image'):
				# Handle base64 image data from mobile camera
				file_doc = self.save_base64_image(photo_data)
				
				self.append('photos', {
					'photo': file_doc.name,
					'description': 'Quality Control Photo',
					'taken_by': frappe.session.user,
					'taken_date': now_datetime()
				})

	def save_base64_image(self, base64_data):
		"""Save base64 image data as file"""
		import base64
		from frappe.utils.file_manager import save_file
		
		# Extract image data and format
		header, encoded = base64_data.split(',', 1)
		ext = header.split(';')[0].split('/')[-1]
		
		# Decode image data
		image_data = base64.b64decode(encoded)
		
		# Generate filename
		filename = f"qc_checkpoint_{self.name}_{frappe.utils.random_string(8)}.{ext}"
		
		# Save file
		file_doc = save_file(
			filename,
			image_data,
			"Quality Control Checkpoint",
			self.name,
			is_private=1
		)
		
		return file_doc

	@staticmethod
	@frappe.whitelist()
	def get_service_order_checkpoints(service_order):
		"""Get all checkpoints for a service order"""
		checkpoints = frappe.get_all(
			"Quality Control Checkpoint",
			filters={"service_order": service_order},
			fields=[
				"name", "checkpoint_name", "checkpoint_name_ar", "checkpoint_type",
				"status", "priority_level", "assigned_technician", "completion_date",
				"quality_score", "defects_found", "rework_required"
			],
			order_by="creation"
		)
		
		return checkpoints

	@staticmethod
	@frappe.whitelist()
	def get_pending_approvals(supervisor=None):
		"""Get checkpoints pending approval"""
		filters = {"status": "Completed"}
		
		if supervisor:
			filters["assigned_supervisor"] = supervisor
		
		pending = frappe.get_all(
			"Quality Control Checkpoint",
			filters=filters,
			fields=[
				"name", "checkpoint_name", "service_order", "assigned_technician",
				"completion_date", "priority_level", "checkpoint_type"
			],
			order_by="completion_date"
		)
		
		return pending

	@staticmethod
	@frappe.whitelist()
	def get_quality_metrics_summary(date_range=None):
		"""Get quality metrics summary for dashboard"""
		conditions = "WHERE 1=1"
		
		if date_range:
			start_date, end_date = date_range.split(" to ")
			conditions += f" AND completion_date BETWEEN '{start_date}' AND '{end_date}'"
		
		query = f"""
			SELECT 
				COUNT(*) as total_checkpoints,
				SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) as approved_count,
				SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count,
				AVG(quality_score) as avg_quality_score,
				SUM(defects_found) as total_defects,
				SUM(CASE WHEN rework_required = 1 THEN 1 ELSE 0 END) as rework_count
			FROM `tabQuality Control Checkpoint`
			{conditions}
		"""
		
		result = frappe.db.sql(query, as_dict=True)[0]
		
		# Calculate approval rate
		if result.total_checkpoints > 0:
			result.approval_rate = flt(result.approved_count / result.total_checkpoints * 100, 2)
		else:
			result.approval_rate = 0
		
		return result 