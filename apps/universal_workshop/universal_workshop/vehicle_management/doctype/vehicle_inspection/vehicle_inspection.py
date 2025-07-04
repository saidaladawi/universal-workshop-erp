import datetime

import frappe
from frappe import _
from frappe.model.document import Document


class VehicleInspection(Document):
	def autoname(self):
		"""Generate inspection ID: VI-YYYY-NNNN"""
		year = datetime.datetime.now().year

		# Get last inspection number for current year
		last_inspection = frappe.db.sql(
			"""
            SELECT inspection_id FROM `tabVehicle Inspection`
            WHERE inspection_id LIKE 'VI-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(year)
		)

		if last_inspection:
			last_num = int(last_inspection[0][0].split("-")[-1])
			new_num = last_num + 1
		else:
			new_num = 1

		self.inspection_id = f"VI-{year}-{new_num:04d}"

	def validate(self):
		"""Validate inspection data"""
		self.validate_basic_data()
		self.set_customer_from_vehicle()
		self.set_arabic_translations()
		self.validate_checklist_items()
		self.calculate_overall_rating()
		self.set_next_inspection_date()

	def validate_basic_data(self):
		"""Validate required fields"""
		if not self.vehicle:
			frappe.throw(_("Vehicle is required"))

		if not self.inspector:
			frappe.throw(_("Inspector is required"))

		if not self.inspection_type:
			frappe.throw(_("Inspection type is required"))

		if self.inspection_date and self.inspection_date > datetime.date.today():
			frappe.throw(_("Inspection date cannot be in the future"))

	def set_customer_from_vehicle(self):
		"""Set customer from vehicle link"""
		if self.vehicle and not self.customer:
			vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
			self.customer = vehicle_doc.owner

	def set_arabic_translations(self):
		"""Set Arabic translations for inspection items"""
		# Set Arabic checklist item translations
		for item in self.checklist_items:
			if not item.inspection_item_ar and item.inspection_item:
				item.inspection_item_ar = self.get_arabic_inspection_item(item.inspection_item)

	def get_arabic_inspection_item(self, english_item):
		"""Get Arabic translation for inspection items"""
		item_translations = {
			# Engine
			"Engine Oil Level": "مستوى زيت المحرك",
			"Engine Oil Condition": "حالة زيت المحرك",
			"Coolant Level": "مستوى سائل التبريد",
			"Belt Condition": "حالة الأحزمة",
			"Air Filter": "فلتر الهواء",
			"Engine Performance": "أداء المحرك",
			# Transmission
			"Transmission Fluid": "زيت ناقل الحركة",
			"Gear Shifting": "تغيير التروس",
			"Clutch Operation": "تشغيل القابض",
			# Brakes
			"Brake Pads": "تيل الفرامل",
			"Brake Fluid": "زيت الفرامل",
			"Brake Performance": "أداء الفرامل",
			"Handbrake": "فرامل اليد",
			# Suspension
			"Shock Absorbers": "ماصات الصدمات",
			"Springs": "السوست",
			"Suspension Noise": "ضوضاء التعليق",
			# Electrical
			"Battery Condition": "حالة البطارية",
			"Alternator": "المولد",
			"Starter Motor": "محرك البداية",
			# Body
			"Body Condition": "حالة الهيكل",
			"Paint Condition": "حالة الطلاء",
			"Rust Check": "فحص الصدأ",
			"Door Operation": "تشغيل الأبواب",
			# Interior
			"Seat Condition": "حالة المقاعد",
			"Dashboard": "لوحة القيادة",
			"Air Conditioning": "تكييف الهواء",
			# Tires
			"Tire Tread Depth": "عمق المداس",
			"Tire Condition": "حالة الإطارات",
			"Tire Pressure": "ضغط الإطارات",
			"Wheel Alignment": "ضبط العجلات",
			# Lights
			"Headlights": "المصابيح الأمامية",
			"Tail Lights": "المصابيح الخلفية",
			"Turn Signals": "الإشارات",
			"Hazard Lights": "أضواء الطوارئ",
			# Safety
			"Seat Belts": "أحزمة الأمان",
			"Airbags": "الوسائد الهوائية",
			"Emergency Equipment": "معدات الطوارئ",
			# Emission
			"Exhaust System": "نظام العادم",
			"Catalytic Converter": "المحول الحفاز",
			"Emission Levels": "مستويات الانبعاثات",
		}

		return item_translations.get(english_item, english_item)

	def validate_checklist_items(self):
		"""Validate checklist items"""
		if not self.checklist_items:
			frappe.throw(_("At least one checklist item is required"))

		# Check for critical failures
		critical_failures = []
		for item in self.checklist_items:
			if item.result == "Fail" and item.priority == "Critical":
				critical_failures.append(item.inspection_item)

		if critical_failures:
			self.immediate_action_required = 1
			if not self.action_description:
				self.action_description = f"Critical failures found: {', '.join(critical_failures)}"

	def calculate_overall_rating(self):
		"""Calculate overall rating based on checklist results"""
		if not self.checklist_items:
			return

		total_items = len(self.checklist_items)
		pass_count = 0
		fail_count = 0
		critical_count = 0

		for item in self.checklist_items:
			if item.result == "Pass":
				pass_count += 1
			elif item.result == "Fail":
				fail_count += 1
				if item.priority == "Critical":
					critical_count += 1

		# Calculate pass percentage
		pass_percentage = (pass_count / total_items) * 100

		# Determine overall rating
		if critical_count > 0:
			self.overall_rating = "Critical"
		elif fail_count > total_items * 0.3:  # More than 30% failures
			self.overall_rating = "Poor"
		elif pass_percentage >= 90:
			self.overall_rating = "Excellent"
		elif pass_percentage >= 75:
			self.overall_rating = "Good"
		else:
			self.overall_rating = "Fair"

	def set_next_inspection_date(self):
		"""Set next inspection date based on type and rating"""
		if not self.next_inspection_date:
			inspection_intervals = {
				"Pre-Purchase": 0,  # One-time
				"Periodic Maintenance": 90,  # 3 months
				"Accident Assessment": 0,  # One-time
				"Insurance Claim": 0,  # One-time
				"Pre-Sale": 0,  # One-time
				"Annual Inspection": 365,  # 1 year
				"Emission Test": 365,  # 1 year
				"Safety Check": 180,  # 6 months
				"Custom": 90,  # Default 3 months
			}

			base_interval = inspection_intervals.get(self.inspection_type, 90)

			if base_interval > 0:
				# Adjust interval based on rating
				if self.overall_rating == "Critical":
					interval = max(30, base_interval // 4)  # Minimum 30 days
				elif self.overall_rating == "Poor":
					interval = base_interval // 2
				elif self.overall_rating == "Fair":
					interval = int(base_interval * 0.75)
				else:
					interval = base_interval

				self.next_inspection_date = datetime.date.today() + datetime.timedelta(days=interval)

	def before_save(self):
		"""Actions before saving"""
		if not self.inspector:
			self.inspector = frappe.session.user

		# Update vehicle mileage if provided
		if self.mileage_at_inspection and self.vehicle:
			vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
			if self.mileage_at_inspection > vehicle_doc.mileage:
				frappe.db.set_value("Vehicle", self.vehicle, "mileage", self.mileage_at_inspection)

	def on_submit(self):
		"""Actions on submission"""
		self.update_vehicle_inspection_history()
		if self.immediate_action_required:
			self.create_maintenance_alert()

	def update_vehicle_inspection_history(self):
		"""Update vehicle with latest inspection info"""
		if self.vehicle:
			frappe.db.set_value(
				"Vehicle",
				self.vehicle,
				{
					"last_inspection_date": self.inspection_date,
					"last_inspection_rating": self.overall_rating,
					"next_inspection_due": self.next_inspection_date,
				},
			)

	def create_maintenance_alert(self):
		"""Create maintenance alert for critical findings"""
		if self.immediate_action_required and self.action_description:
			try:
				alert = frappe.new_doc("Maintenance Alert")
				alert.vehicle = self.vehicle
				alert.customer = self.customer
				alert.service_type = "Critical Inspection Follow-up"
				alert.due_date = datetime.date.today() + datetime.timedelta(days=7)  # 1 week
				alert.alert_type = "Time Based"
				alert.priority = "Critical"
				alert.status = "Active"
				alert.description = (
					f"Critical findings from inspection {self.inspection_id}: {self.action_description}"
				)
				alert.inspection_reference = self.name
				alert.insert()
			except Exception as e:
				frappe.log_error(f"Failed to create maintenance alert: {e!s}")

	@frappe.whitelist()
	def load_standard_checklist(self, vehicle_type=None):
		"""Load standard checklist items based on inspection type"""
		standard_items = self.get_standard_checklist_items(self.inspection_type, vehicle_type)

		# Clear existing items
		self.checklist_items = []

		# Add standard items
		for item_data in standard_items:
			item = self.append("checklist_items")
			item.item_category = item_data["category"]
			item.inspection_item = item_data["item"]
			item.inspection_item_ar = self.get_arabic_inspection_item(item_data["item"])
			item.result = "Pass"  # Default
			item.priority = item_data.get("priority", "Medium")

		return len(standard_items)

	def get_standard_checklist_items(self, inspection_type, vehicle_type=None):
		"""Get standard checklist items for inspection type"""
		base_items = [
			# Engine
			{"category": "Engine", "item": "Engine Oil Level", "priority": "High"},
			{"category": "Engine", "item": "Engine Oil Condition", "priority": "High"},
			{"category": "Engine", "item": "Coolant Level", "priority": "Medium"},
			{"category": "Engine", "item": "Belt Condition", "priority": "Medium"},
			{"category": "Engine", "item": "Air Filter", "priority": "Low"},
			# Brakes
			{"category": "Brakes", "item": "Brake Pads", "priority": "Critical"},
			{"category": "Brakes", "item": "Brake Fluid", "priority": "High"},
			{"category": "Brakes", "item": "Brake Performance", "priority": "Critical"},
			# Tires
			{"category": "Tires", "item": "Tire Tread Depth", "priority": "High"},
			{"category": "Tires", "item": "Tire Condition", "priority": "High"},
			{"category": "Tires", "item": "Tire Pressure", "priority": "Medium"},
			# Lights
			{"category": "Lights", "item": "Headlights", "priority": "High"},
			{"category": "Lights", "item": "Tail Lights", "priority": "High"},
			{"category": "Lights", "item": "Turn Signals", "priority": "Medium"},
			# Safety
			{"category": "Safety", "item": "Seat Belts", "priority": "Critical"},
			{"category": "Safety", "item": "Emergency Equipment", "priority": "Medium"},
		]

		# Add specific items based on inspection type
		if inspection_type == "Pre-Purchase":
			base_items.extend(
				[
					{"category": "Body", "item": "Body Condition", "priority": "Medium"},
					{"category": "Body", "item": "Paint Condition", "priority": "Low"},
					{"category": "Body", "item": "Rust Check", "priority": "High"},
					{"category": "Interior", "item": "Seat Condition", "priority": "Low"},
					{"category": "Interior", "item": "Dashboard", "priority": "Low"},
					{"category": "Transmission", "item": "Gear Shifting", "priority": "High"},
					{"category": "Suspension", "item": "Shock Absorbers", "priority": "Medium"},
				]
			)

		elif inspection_type == "Emission Test":
			base_items.extend(
				[
					{"category": "Emission", "item": "Exhaust System", "priority": "Critical"},
					{"category": "Emission", "item": "Catalytic Converter", "priority": "Critical"},
					{"category": "Emission", "item": "Emission Levels", "priority": "Critical"},
				]
			)

		elif inspection_type == "Safety Check":
			base_items.extend(
				[
					{"category": "Safety", "item": "Airbags", "priority": "Critical"},
					{"category": "Electrical", "item": "Battery Condition", "priority": "Medium"},
					{"category": "Suspension", "item": "Suspension Noise", "priority": "Medium"},
				]
			)

		return base_items


# Utility functions
@frappe.whitelist()
def get_vehicle_inspections(vehicle, limit=5):
	"""Get recent inspections for a vehicle"""
	inspections = frappe.get_all(
		"Vehicle Inspection",
		filters={"vehicle": vehicle, "docstatus": 1},
		fields=["name", "inspection_id", "inspection_date", "inspection_type", "overall_rating", "inspector"],
		order_by="inspection_date desc",
		limit=limit,
	)
	return inspections


@frappe.whitelist()
def get_inspection_statistics(vehicle=None, date_range=None):
	"""Get inspection statistics"""
	filters = {"docstatus": 1}
	if vehicle:
		filters["vehicle"] = vehicle

	if date_range:
		start_date, end_date = date_range.split(" to ")
		filters["inspection_date"] = ["between", [start_date, end_date]]

	# Count by rating
	rating_counts = frappe.db.sql(
		"""
        SELECT overall_rating, COUNT(*) as count
        FROM `tabVehicle Inspection`
        WHERE docstatus = 1 {vehicle_filter} {date_filter}
        GROUP BY overall_rating
    """.format(
			vehicle_filter=f"AND vehicle = '{vehicle}'" if vehicle else "",
			date_filter=f"AND inspection_date BETWEEN '{start_date}' AND '{end_date}'" if date_range else "",
		),
		as_dict=True,
	)

	# Count by type
	type_counts = frappe.db.sql(
		"""
        SELECT inspection_type, COUNT(*) as count
        FROM `tabVehicle Inspection`
        WHERE docstatus = 1 {vehicle_filter} {date_filter}
        GROUP BY inspection_type
    """.format(
			vehicle_filter=f"AND vehicle = '{vehicle}'" if vehicle else "",
			date_filter=f"AND inspection_date BETWEEN '{start_date}' AND '{end_date}'" if date_range else "",
		),
		as_dict=True,
	)

	return {"rating_counts": rating_counts, "type_counts": type_counts}


@frappe.whitelist()
def create_inspection_from_template(vehicle, inspection_type):
	"""Create new inspection from template"""
	inspection = frappe.new_doc("Vehicle Inspection")
	inspection.vehicle = vehicle
	inspection.inspection_type = inspection_type
	inspection.inspection_date = datetime.date.today()
	inspection.inspector = frappe.session.user

	# Load standard checklist
	inspection.load_standard_checklist()

	return inspection.name


@frappe.whitelist()
def get_overdue_inspections():
	"""Get vehicles with overdue inspections"""
	overdue_vehicles = frappe.db.sql(
		"""
        SELECT v.name, v.license_plate, v.make, v.model, v.owner,
               v.next_inspection_due,
               DATEDIFF(CURDATE(), v.next_inspection_due) as days_overdue
        FROM `tabVehicle` v
        WHERE v.next_inspection_due < CURDATE()
        ORDER BY days_overdue DESC
    """,
		as_dict=True,
	)

	return overdue_vehicles


@frappe.whitelist()
def schedule_inspection_reminder():
	"""Daily job to check for upcoming inspections"""
	# Get vehicles due for inspection in next 7 days
	upcoming_inspections = frappe.db.sql(
		"""
        SELECT v.name, v.license_plate, v.make, v.model, v.owner,
               v.next_inspection_due,
               DATEDIFF(v.next_inspection_due, CURDATE()) as days_until_due
        FROM `tabVehicle` v
        WHERE v.next_inspection_due BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
    """,
		as_dict=True,
	)

	for vehicle in upcoming_inspections:
		# Create inspection reminder
		if not frappe.db.exists(
			"Maintenance Alert",
			{"vehicle": vehicle["name"], "service_type": "Inspection Due", "status": "Active"},
		):
			try:
				alert = frappe.new_doc("Maintenance Alert")
				alert.vehicle = vehicle["name"]
				alert.customer = vehicle["owner"]
				alert.service_type = "Inspection Due"
				alert.due_date = vehicle["next_inspection_due"]
				alert.alert_type = "Time Based"
				alert.priority = "Medium"
				alert.status = "Active"
				alert.description = f"Vehicle inspection is due for {vehicle['make']} {vehicle['model']} ({vehicle['license_plate']})"
				alert.insert()
			except Exception as e:
				frappe.log_error(f"Failed to create inspection reminder: {e!s}")

	return len(upcoming_inspections)
