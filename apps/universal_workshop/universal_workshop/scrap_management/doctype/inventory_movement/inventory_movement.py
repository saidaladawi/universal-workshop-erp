import json
import re
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, get_datetime, now_datetime, time_diff_in_seconds


class InventoryMovement(Document):
	# pylint: disable=no-member
	# Frappe framework dynamically adds DocType fields

	def validate(self):
		"""Validate inventory movement data before saving"""
		self.validate_movement_logic()
		self.validate_part_exists()
		self.validate_location_capacity()
		self.validate_barcode_data()
		self.validate_quantities()

	def before_save(self):
		"""Set default values and calculate fields before saving"""
		self.set_movement_defaults()
		self.calculate_processing_duration()
		self.update_verification_status()
		self.validate_approval_requirements()

	def after_insert(self):
		"""Actions after movement record is created"""
		self.create_movement_log()
		self.send_movement_notifications()

	def on_submit(self):
		"""Actions when movement is submitted/completed"""
		self.update_part_location()
		self.update_storage_utilization()
		self.create_barcode_movement_log()
		self.set_completion_time()

	def on_cancel(self):
		"""Actions when movement is cancelled"""
		self.revert_location_changes()
		self.cancel_movement_log()

	def validate_movement_logic(self):
		"""Validate basic movement logic"""
		# Stock In and Found movements require only 'to_location'
		if self.movement_type in ["Stock In", "Found"]:
			if not self.to_location:
				frappe.throw(_("To Location is required for {0} movement").format(self.movement_type))
			if self.from_location:
				self.from_location = None  # Clear from_location for these types

		# Stock Out and Loss movements require only 'from_location'
		elif self.movement_type in ["Stock Out", "Loss", "Damage"]:
			if not self.from_location:
				frappe.throw(_("From Location is required for {0} movement").format(self.movement_type))
			if self.to_location:
				self.to_location = None  # Clear to_location for these types

		# Transfer movements require both locations
		elif self.movement_type == "Transfer":
			if not self.from_location or not self.to_location:
				frappe.throw(_("Both From and To locations are required for Transfer movement"))
			if self.from_location == self.to_location:
				frappe.throw(_("From and To locations cannot be the same"))

	def validate_part_exists(self):
		"""Validate that the part exists and is accessible"""
		if not self.extracted_part:
			frappe.throw(_("Extracted Part is required"))

		# Check if part exists and is not already in another active movement
		active_movements = frappe.get_list(
			"Inventory Movement",
			filters={
				"extracted_part": self.extracted_part,
				"movement_status": ["in", ["Draft", "In Progress", "Pending Approval"]],
				"name": ["!=", self.name or ""],
			},
		)

		if active_movements:
			frappe.throw(_("Part {0} is already in an active movement").format(self.part_code))

	def validate_location_capacity(self):
		"""Validate that destination location has capacity"""
		if self.to_location and self.movement_type in ["Stock In", "Transfer", "Found"]:
			# Get location capacity
			location_doc = frappe.get_doc("Storage Location", self.to_location)

			# Check if location can accommodate the part
			can_accommodate, reason = location_doc.can_accommodate_part(
				part_weight=self.part_weight_kg or 0, part_volume=self.part_volume_m3 or 0
			)

			if not can_accommodate:
				frappe.throw(_("Destination location cannot accommodate this part: {0}").format(reason))

	def validate_barcode_data(self):
		"""Validate barcode and QR code data"""
		if self.scanned_barcode:
			# Validate barcode format for parts (UW-PARTCODE format)
			if self.scanned_barcode.startswith("UW-"):
				# Verify barcode matches the selected part
				part_barcode = frappe.get_value("Extracted Parts", self.extracted_part, "barcode")
				if part_barcode and part_barcode != self.scanned_barcode:
					frappe.throw(_("Scanned barcode does not match selected part"))

			# Validate location barcode format (LOC-LOCATIONCODE format)
			elif self.scanned_barcode.startswith("LOC-"):
				location_code = self.scanned_barcode.replace("LOC-", "")
				# Verify location exists
				if not frappe.db.exists("Storage Location", {"location_code": location_code}):
					frappe.throw(_("Location with barcode {0} not found").format(self.scanned_barcode))

	def validate_quantities(self):
		"""Validate quantity data"""
		if self.expected_quantity and self.actual_quantity:
			if abs(self.expected_quantity - self.actual_quantity) > 0.01:  # Allow small precision differences
				if not self.discrepancy_reason:
					frappe.throw(
						_("Discrepancy reason is required when expected and actual quantities differ")
					)

		# Ensure quantity_moved is positive
		if self.quantity_moved and self.quantity_moved <= 0:
			frappe.throw(_("Quantity moved must be positive"))

	def set_movement_defaults(self):
		"""Set default values for the movement"""
		# Set current user as scanned_by if not set
		if not self.scanned_by:
			self.scanned_by = frappe.session.user

		# Set creation timestamp if not set
		if not self.creation_timestamp:
			self.creation_timestamp = now_datetime()

		# Set modified user
		self.modified_by_user = frappe.session.user

		# Set default quantity if not set
		if not self.quantity_moved:
			self.quantity_moved = 1

		# Auto-detect GPS location if device supports it (placeholder)
		if not self.gps_location and self.scan_method == "Mobile Camera":
			self.gps_location = self.get_device_location()

	def calculate_processing_duration(self):
		"""Calculate processing duration for completed movements"""
		if self.movement_status == "Completed" and self.completion_time and self.creation_timestamp:
			start_time = get_datetime(self.creation_timestamp)
			end_time = get_datetime(self.completion_time)
			duration_seconds = time_diff_in_seconds(end_time, start_time)

			# Convert to duration format (HH:MM:SS)
			hours = duration_seconds // 3600
			minutes = (duration_seconds % 3600) // 60
			seconds = duration_seconds % 60

			self.processing_duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

	def update_verification_status(self):
		"""Update verification status based on scan data"""
		if self.scanned_barcode or self.qr_code_data:
			if self.verification_status == "Pending":
				# Auto-verify if barcode matches part
				part_barcode = frappe.get_value("Extracted Parts", self.extracted_part, "barcode")
				if part_barcode and part_barcode == self.scanned_barcode:
					self.verification_status = "Verified"
					self.verification_time = now_datetime()
				else:
					self.verification_status = "Mismatch"

	def validate_approval_requirements(self):
		"""Validate approval requirements based on movement type and amount"""
		# High-value parts require approval
		if self.extracted_part:
			part_value = frappe.get_value("Extracted Parts", self.extracted_part, "estimated_price_omr")
			if part_value and flt(part_value) > 500:  # Parts over 500 OMR require approval
				self.approval_required = 1

		# Damage and Loss movements always require approval
		if self.movement_type in ["Damage", "Loss"]:
			self.approval_required = 1

		# Check if approval is required but not provided
		if self.approval_required and self.movement_status in ["Completed", "In Progress"]:
			if not self.approved_by:
				frappe.throw(_("Approval is required for this movement"))

	def get_device_location(self):
		"""Get device GPS location (placeholder for mobile integration)"""
		# This would integrate with mobile app GPS
		# For now, return empty string
		return ""

	def create_movement_log(self):
		"""Create system log for movement tracking"""
		log_message = f"Inventory Movement Created: {self.name}\n"
		log_message += f"Type: {self.movement_type}\n"
		log_message += f"Part: {self.part_code}\n"
		log_message += f"From: {self.from_location_name or 'N/A'}\n"
		log_message += f"To: {self.to_location_name or 'N/A'}\n"
		log_message += f"User: {self.scanned_by}"

		frappe.log_error(log_message, "Inventory Movement")

	def send_movement_notifications(self):
		"""Send notifications for important movements"""
		# Send notification for high-value parts
		if self.extracted_part:
			part_value = frappe.get_value("Extracted Parts", self.extracted_part, "estimated_price_omr")
			if part_value and flt(part_value) > 1000:  # High-value threshold
				self.send_high_value_notification()

		# Send notification for damage/loss
		if self.movement_type in ["Damage", "Loss"]:
			self.send_damage_loss_notification()

	def send_high_value_notification(self):
		"""Send notification for high-value part movements"""
		subject = _("High-Value Part Movement: {0}").format(self.part_code)
		message = _("A high-value part has been moved in the warehouse system.\n\n")
		message += _("Part Code: {0}\n").format(self.part_code)
		message += _("Movement Type: {0}\n").format(self.movement_type)
		message += _("From Location: {0}\n").format(self.from_location_name or _("N/A"))
		message += _("To Location: {0}\n").format(self.to_location_name or _("N/A"))
		message += _("Moved By: {0}\n").format(self.scanned_by)

		# Send to warehouse managers
		warehouse_managers = frappe.get_list(
			"User", filters={"role_profile_name": ["like", "%Warehouse%"]}, fields=["email"]
		)

		for manager in warehouse_managers:
			if manager.email:
				frappe.sendmail(recipients=[manager.email], subject=subject, message=message)

	def send_damage_loss_notification(self):
		"""Send notification for damage/loss movements"""
		subject = _("Part {0} Reported: {1}").format(self.movement_type, self.part_code)
		message = _("A part has been reported as {0} in the warehouse system.\n\n").format(
			self.movement_type.lower()
		)
		message += _("Part Code: {0}\n").format(self.part_code)
		message += _("Location: {0}\n").format(self.from_location_name or _("Unknown"))
		message += _("Reported By: {0}\n").format(self.scanned_by)
		message += _("Notes: {0}\n").format(self.notes or _("No additional notes"))

		# Send to management
		frappe.sendmail(
			recipients=frappe.get_all(
				"User", filters={"role_profile_name": ["like", "%Manager%"]}, pluck="email"
			),
			subject=subject,
			message=message,
		)

	def update_part_location(self):
		"""Update the part's current location"""
		if self.extracted_part:
			part_doc = frappe.get_doc("Extracted Parts", self.extracted_part)

			# Update location based on movement type
			if self.movement_type in ["Stock In", "Transfer", "Found"]:
				part_doc.storage_location = self.to_location
				part_doc.last_movement_date = self.movement_date
				part_doc.last_movement_type = self.movement_type

			elif self.movement_type in ["Stock Out", "Loss", "Damage"]:
				part_doc.storage_location = None  # Remove from storage
				part_doc.last_movement_date = self.movement_date
				part_doc.last_movement_type = self.movement_type

				# Update part status for damage/loss
				if self.movement_type == "Damage":
					part_doc.part_status = "Damaged"
				elif self.movement_type == "Loss":
					part_doc.part_status = "Lost"

			part_doc.save(ignore_permissions=True)

	def update_storage_utilization(self):
		"""Update storage location utilization statistics"""
		# Update 'from' location utilization
		if self.from_location:
			from_location_doc = frappe.get_doc("Storage Location", self.from_location)
			from_location_doc.update_current_usage()

		# Update 'to' location utilization
		if self.to_location:
			to_location_doc = frappe.get_doc("Storage Location", self.to_location)
			to_location_doc.update_current_usage()

	def create_barcode_movement_log(self):
		"""Create barcode tracking log entry"""
		if self.scanned_barcode:
			# Log barcode scan event
			log_data = {
				"barcode": self.scanned_barcode,
				"scan_time": self.verification_time or now_datetime(),
				"scan_method": self.scan_method,
				"movement_type": self.movement_type,
				"location": self.to_location or self.from_location,
				"user": self.scanned_by,
			}

			# Store in system log
			frappe.log_error(json.dumps(log_data), "Barcode Scan Log")

	def set_completion_time(self):
		"""Set completion time when movement is completed"""
		if self.movement_status == "Completed" and not self.completion_time:
			self.completion_time = now_datetime()
			self.db_update()

	def revert_location_changes(self):
		"""Revert location changes when movement is cancelled"""
		if self.extracted_part:
			# Get the previous location from movement history
			previous_movement = frappe.get_list(
				"Inventory Movement",
				filters={
					"extracted_part": self.extracted_part,
					"docstatus": 1,
					"creation": ["<", self.creation],
					"movement_status": "Completed",
				},
				fields=["to_location", "from_location", "movement_type"],
				order_by="creation desc",
				limit=1,
			)

			if previous_movement:
				part_doc = frappe.get_doc("Extracted Parts", self.extracted_part)

				# Determine previous location
				prev_movement = previous_movement[0]
				if prev_movement.movement_type in ["Stock In", "Transfer", "Found"]:
					part_doc.storage_location = prev_movement.to_location
				elif prev_movement.movement_type in ["Stock Out", "Loss", "Damage"]:
					part_doc.storage_location = None

				part_doc.save(ignore_permissions=True)

	def cancel_movement_log(self):
		"""Create log entry for cancelled movement"""
		log_message = f"Inventory Movement Cancelled: {self.name}\n"
		log_message += f"Type: {self.movement_type}\n"
		log_message += f"Part: {self.part_code}\n"
		log_message += f"Cancelled By: {frappe.session.user}"

		frappe.log_error(log_message, "Inventory Movement Cancelled")


# Utility functions for inventory movement management
@frappe.whitelist()
def create_movement_from_barcode(barcode, movement_type, location=None, user=None):
	"""Create inventory movement from barcode scan"""

	if not user:
		user = frappe.session.user

	# Determine if barcode is for part or location
	if barcode.startswith("UW-"):
		# Part barcode
		part = frappe.get_value("Extracted Parts", {"barcode": barcode}, "name")
		if not part:
			return {
				"success": False,
				"message": _("Part with barcode {0} not found").format(barcode),
			}

		# Create movement record
		movement = frappe.new_doc("Inventory Movement")
		movement.extracted_part = part
		movement.movement_type = movement_type
		movement.scanned_barcode = barcode
		movement.scanned_by = user
		movement.scan_method = "Barcode Scanner"

		# Set location based on movement type
		if movement_type in ["Stock In", "Transfer", "Found"] and location:
			movement.to_location = location
		elif movement_type in ["Stock Out", "Loss", "Damage"]:
			# Get current location from part
			current_location = frappe.get_value("Extracted Parts", part, "storage_location")
			movement.from_location = current_location

		movement.insert()

		return {
			"success": True,
			"movement_id": movement.name,
			"message": _("Movement record created successfully"),
		}

	else:
		return {"success": False, "message": _("Invalid barcode format")}


@frappe.whitelist()
def get_movement_analytics(warehouse=None, date_range=None):
	"""Get inventory movement analytics"""

	filters = {"docstatus": 1}

	if warehouse:
		# Filter by warehouse through locations
		warehouse_locations = frappe.get_list(
			"Storage Location", filters={"warehouse": warehouse}, pluck="name"
		)
		if warehouse_locations:
			filters["to_location"] = ["in", warehouse_locations]

	if date_range:
		filters["movement_date"] = ["between", date_range]

	# Get movement data
	movements = frappe.get_list(
		"Inventory Movement",
		filters=filters,
		fields=[
			"movement_type",
			"movement_date",
			"part_weight_kg",
			"part_volume_m3",
			"processing_duration",
			"verification_status",
		],
	)

	# Calculate analytics
	analytics = {
		"total_movements": len(movements),
		"by_type": {},
		"by_verification": {},
		"total_weight_moved": 0,
		"total_volume_moved": 0,
		"average_processing_time": 0,
	}

	# Group by movement type
	for movement in movements:
		mov_type = movement.movement_type
		analytics["by_type"][mov_type] = analytics["by_type"].get(mov_type, 0) + 1

		# Verification status
		ver_status = movement.verification_status
		analytics["by_verification"][ver_status] = analytics["by_verification"].get(ver_status, 0) + 1

		# Weight and volume
		analytics["total_weight_moved"] += flt(movement.part_weight_kg or 0)
		analytics["total_volume_moved"] += flt(movement.part_volume_m3 or 0)

	# Calculate average processing time
	processing_times = [m.processing_duration for m in movements if m.processing_duration]
	if processing_times:
		# Convert duration strings to seconds and calculate average
		total_seconds = sum(duration_to_seconds(d) for d in processing_times)
		avg_seconds = total_seconds / len(processing_times)
		analytics["average_processing_time"] = seconds_to_duration(avg_seconds)

	return analytics


@frappe.whitelist()
def bulk_movement_import(movement_data):
	"""Import multiple movements from mobile app or external system"""

	results = []

	for movement_item in movement_data:
		try:
			# Create movement record
			movement = frappe.new_doc("Inventory Movement")
			movement.update(movement_item)
			movement.system_generated = 1
			movement.insert()

			results.append({"success": True, "movement_id": movement.name, "part_code": movement.part_code})

		except Exception as e:
			results.append(
				{
					"success": False,
					"error": str(e),
					"part_code": movement_item.get("part_code", "Unknown"),
				}
			)

	return results


@frappe.whitelist()
def get_part_movement_history(part_code, limit=10):
	"""Get movement history for a specific part"""

	movements = frappe.get_list(
		"Inventory Movement",
		filters={"part_code": part_code, "docstatus": 1},
		fields=[
			"name",
			"movement_type",
			"movement_date",
			"movement_time",
			"from_location_name",
			"to_location_name",
			"scanned_by",
			"movement_status",
			"verification_status",
			"notes",
		],
		order_by="movement_date desc, movement_time desc",
		limit=limit,
	)

	return movements


def duration_to_seconds(duration_str):
	"""Convert duration string (HH:MM:SS) to seconds"""
	try:
		time_parts = duration_str.split(":")
		hours = int(time_parts[0])
		minutes = int(time_parts[1])
		seconds = int(time_parts[2])
		return hours * 3600 + minutes * 60 + seconds
	except (ValueError, IndexError):
		return 0


def seconds_to_duration(seconds):
	"""Convert seconds to duration string (HH:MM:SS)"""
	hours = int(seconds // 3600)
	minutes = int((seconds % 3600) // 60)
	secs = int(seconds % 60)
	return f"{hours:02d}:{minutes:02d}:{secs:02d}"
