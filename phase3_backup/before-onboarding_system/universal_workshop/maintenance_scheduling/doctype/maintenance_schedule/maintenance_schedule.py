import datetime
import json

from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.model.document import Document


class MaintenanceSchedule(Document):
	def autoname(self):
		"""Generate maintenance schedule code: MS-YYYY-NNNN"""
		year = datetime.datetime.now().year

		# Get last schedule number for current year
		last_schedule = frappe.db.sql(
			"""
            SELECT name FROM `tabMaintenance Schedule`
            WHERE name LIKE 'MS-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(year)
		)

		if last_schedule:
			last_num = int(last_schedule[0][0].split("-")[-1])
			new_num = last_num + 1
		else:
			new_num = 1

		self.name = f"MS-{year}-{new_num:04d}"

	def validate(self):
		"""Comprehensive validation for maintenance schedules"""
		self.validate_basic_data()
		self.validate_schedule_dates()
		self.validate_maintenance_items()
		self.validate_customer_vehicle()
		self.validate_workshop_capacity()
		self.set_arabic_fields()

	def validate_basic_data(self):
		"""Validate basic required data"""
		if not self.customer:
			frappe.throw(_("Customer is required"))

		if not self.vehicle:
			frappe.throw(_("Vehicle is required"))

		if not self.maintenance_type:
			frappe.throw(_("Maintenance type is required"))

		if not self.scheduled_date:
			frappe.throw(_("Scheduled date is required"))

	def validate_schedule_dates(self):
		"""Validate scheduling dates and working hours"""
		if self.scheduled_date:
			scheduled_datetime = datetime.datetime.combine(
				self.scheduled_date, self.scheduled_time or datetime.time(9, 0)
			)

			# Check if scheduled date is in the past
			if scheduled_datetime < datetime.datetime.now():
				frappe.throw(_("Cannot schedule maintenance in the past"))

			# Check Oman working days (Sunday-Thursday)
			if scheduled_datetime.weekday() in [4, 5]:  # Friday, Saturday
				frappe.throw(_("Maintenance cannot be scheduled on weekends (Friday-Saturday)"))

			# Check working hours (8 AM - 6 PM)
			scheduled_time = self.scheduled_time or datetime.time(9, 0)
			if scheduled_time < datetime.time(8, 0) or scheduled_time > datetime.time(18, 0):
				frappe.throw(_("Maintenance must be scheduled during working hours (8 AM - 6 PM)"))

		# Calculate next service date based on interval
		if self.service_interval_type and self.service_interval_value:
			self.calculate_next_service_date()

	def validate_maintenance_items(self):
		"""Validate maintenance items and calculate costs"""
		if not self.maintenance_items:
			frappe.throw(_("At least one maintenance item is required"))

		total_estimated_cost = 0
		total_estimated_time = 0

		for item in self.maintenance_items:
			if not item.item_code:
				frappe.throw(_("Item code is required for all maintenance items"))

			if not item.quantity or item.quantity <= 0:
				frappe.throw(_("Quantity must be greater than 0"))

			# Get item details
			item_doc = frappe.get_doc("Item", item.item_code)
			if not item_doc:
				frappe.throw(_("Item {0} not found").format(item.item_code))

			# Set rate if not provided
			if not item.rate:
				item.rate = item_doc.standard_rate or 0

			# Calculate amount
			item.amount = item.quantity * item.rate
			total_estimated_cost += item.amount

			# Add estimated service time
			if item_doc.service_time_hours:
				total_estimated_time += item_doc.service_time_hours * item.quantity

		self.total_estimated_cost = total_estimated_cost
		self.estimated_duration_hours = total_estimated_time

	def validate_customer_vehicle(self):
		"""Validate customer and vehicle relationship"""
		if self.customer and self.vehicle:
			vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
			if vehicle_doc.owner != self.customer:
				frappe.throw(
					_("Vehicle {0} does not belong to customer {1}").format(self.vehicle, self.customer)
				)

	def validate_workshop_capacity(self):
		"""Check workshop capacity for the scheduled time"""
		if self.scheduled_date and self.scheduled_time:
			scheduled_datetime = datetime.datetime.combine(self.scheduled_date, self.scheduled_time)

			# Check for conflicting schedules (within 2 hours)
			time_buffer = datetime.timedelta(hours=2)
			start_time = scheduled_datetime - time_buffer
			end_time = scheduled_datetime + time_buffer

			existing_schedules = frappe.db.count(
				"Maintenance Schedule",
				{
					"scheduled_date": self.scheduled_date,
					"status": ["in", ["Scheduled", "In Progress"]],
					"name": ["!=", self.name],
					"scheduled_time": ["between", [start_time.time(), end_time.time()]],
				},
			)

			# Get workshop capacity from settings
			workshop_settings = frappe.get_single("Workshop Settings")
			max_concurrent_services = workshop_settings.get("max_concurrent_services", 3)

			if existing_schedules >= max_concurrent_services:
				frappe.throw(_("Workshop capacity exceeded for the selected time slot"))

	def set_arabic_fields(self):
		"""Set Arabic field translations"""
		if self.customer:
			customer_doc = frappe.get_doc("Customer", self.customer)
			self.customer_name_ar = customer_doc.get("customer_name_ar") or customer_doc.customer_name

		if self.vehicle:
			vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
			self.vehicle_info_ar = f"{vehicle_doc.get('make_ar', vehicle_doc.make)} {vehicle_doc.get('model_ar', vehicle_doc.model)} ({vehicle_doc.license_plate})"

		# Set maintenance type in Arabic
		maintenance_types_ar = {
			"Oil Change": "تغيير الزيت",
			"Brake Service": "خدمة الفرامل",
			"Tire Rotation": "تدوير الإطارات",
			"Engine Tune-up": "ضبط المحرك",
			"Transmission Service": "خدمة ناقل الحركة",
			"Air Filter Replacement": "تغيير فلتر الهواء",
			"Battery Check": "فحص البطارية",
			"Cooling System": "نظام التبريد",
			"Electrical System": "النظام الكهربائي",
			"General Inspection": "فحص شامل",
		}

		self.maintenance_type_ar = maintenance_types_ar.get(self.maintenance_type, self.maintenance_type)

	def before_save(self):
		"""Actions before saving the document"""
		self.update_status_based_on_date()
		self.calculate_priority_score()

	def update_status_based_on_date(self):
		"""Auto-update status based on scheduled date"""
		if self.scheduled_date:
			today = datetime.date.today()
			scheduled_date = self.scheduled_date

			if scheduled_date < today and self.status == "Scheduled":
				self.status = "Overdue"
			elif scheduled_date == today and self.status == "Scheduled":
				self.status = "Due Today"

	def calculate_priority_score(self):
		"""Calculate priority score based on various factors"""
		score = 0

		# Base priority
		priority_scores = {"High": 30, "Medium": 20, "Low": 10}
		score += priority_scores.get(self.priority, 10)

		# Urgency based on due date
		if self.scheduled_date:
			days_until_due = (self.scheduled_date - datetime.date.today()).days
			if days_until_due < 0:
				score += 50  # Overdue
			elif days_until_due == 0:
				score += 40  # Due today
			elif days_until_due <= 3:
				score += 30  # Due soon
			elif days_until_due <= 7:
				score += 20  # Due this week

		# Customer priority
		if self.customer:
			customer_doc = frappe.get_doc("Customer", self.customer)
			if customer_doc.get("customer_group") == "VIP":
				score += 25
			elif customer_doc.get("customer_group") == "Premium":
				score += 15

		# Vehicle age factor
		if self.vehicle:
			vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
			if vehicle_doc.year:
				vehicle_age = datetime.date.today().year - int(vehicle_doc.year)
				if vehicle_age > 10:
					score += 15  # Older vehicles need more attention
				elif vehicle_age > 5:
					score += 10

		self.priority_score = score

	def calculate_next_service_date(self):
		"""Calculate next service date based on interval"""
		if not self.service_interval_type or not self.service_interval_value:
			return

		base_date = self.scheduled_date or datetime.date.today()

		if self.service_interval_type == "Days":
			self.next_service_date = base_date + datetime.timedelta(days=self.service_interval_value)
		elif self.service_interval_type == "Weeks":
			self.next_service_date = base_date + datetime.timedelta(weeks=self.service_interval_value)
		elif self.service_interval_type == "Months":
			self.next_service_date = base_date + relativedelta(months=self.service_interval_value)
		elif self.service_interval_type == "Years":
			self.next_service_date = base_date + relativedelta(years=self.service_interval_value)

	def on_submit(self):
		"""Actions when maintenance schedule is submitted"""
		self.create_work_order()
		self.send_customer_notification()
		self.update_vehicle_maintenance_history()

	def create_work_order(self):
		"""Create work order from maintenance schedule"""
		if self.create_work_order_on_submit:
			work_order = frappe.new_doc("Work Order")
			work_order.customer = self.customer
			work_order.vehicle = self.vehicle
			work_order.maintenance_schedule = self.name
			work_order.service_type = self.maintenance_type
			work_order.estimated_cost = self.total_estimated_cost
			work_order.estimated_duration = self.estimated_duration_hours
			work_order.priority = self.priority
			work_order.notes = f"Work order created from maintenance schedule {self.name}"

			# Copy maintenance items
			for item in self.maintenance_items:
				work_order.append(
					"items",
					{
						"item_code": item.item_code,
						"quantity": item.quantity,
						"rate": item.rate,
						"amount": item.amount,
						"description": item.description,
					},
				)

			work_order.insert()
			work_order.submit()

			# Link work order back to schedule
			self.db_set("work_order", work_order.name)

			frappe.msgprint(_("Work Order {0} created successfully").format(work_order.name))

	def send_customer_notification(self):
		"""Send notification to customer about scheduled maintenance"""
		if not self.customer:
			return

		customer_doc = frappe.get_doc("Customer", self.customer)

		# Prepare notification content
		if frappe.db.get_value("Customer", self.customer, "language") == "ar":
			subject = f"تذكير موعد الصيانة - {self.vehicle}"
			message = f"""
            عزيزي/عزيزتي {customer_doc.customer_name_ar or customer_doc.customer_name},

            نذكركم بموعد صيانة مركبتكم:
            - المركبة: {self.vehicle_info_ar}
            - نوع الصيانة: {self.maintenance_type_ar}
            - التاريخ: {self.scheduled_date.strftime("%d/%m/%Y")}
            - الوقت: {self.scheduled_time.strftime("%I:%M %p") if self.scheduled_time else "صباحاً"}
            - التكلفة المقدرة: {self.total_estimated_cost} ر.ع.

            يرجى الحضور في الموعد المحدد.
            شكراً لثقتكم بخدماتنا.
            """
		else:
			subject = f"Maintenance Reminder - {self.vehicle}"
			message = f"""
            Dear {customer_doc.customer_name},

            This is a reminder for your vehicle maintenance:
            - Vehicle: {self.vehicle}
            - Service Type: {self.maintenance_type}
            - Date: {self.scheduled_date.strftime("%d/%m/%Y")}
            - Time: {self.scheduled_time.strftime("%I:%M %p") if self.scheduled_time else "Morning"}
            - Estimated Cost: {self.total_estimated_cost} OMR

            Please arrive on time for your appointment.
            Thank you for choosing our services.
            """

		# Send SMS if mobile number available
		if customer_doc.mobile_no:
			try:
				frappe.sendmail(
					recipients=[customer_doc.mobile_no],
					subject=subject,
					message=message,
					communication_type="SMS",
				)
			except Exception as e:
				frappe.log_error(f"Failed to send SMS notification: {e!s}")

		# Send email if email available
		if customer_doc.email_id:
			try:
				frappe.sendmail(recipients=[customer_doc.email_id], subject=subject, message=message)
			except Exception as e:
				frappe.log_error(f"Failed to send email notification: {e!s}")

	def update_vehicle_maintenance_history(self):
		"""Update vehicle maintenance history"""
		if not self.vehicle:
			return

		# Create maintenance history record
		history = frappe.new_doc("Vehicle Maintenance History")
		history.vehicle = self.vehicle
		history.maintenance_schedule = self.name
		history.service_type = self.maintenance_type
		history.scheduled_date = self.scheduled_date
		history.estimated_cost = self.total_estimated_cost
		history.status = "Scheduled"
		history.notes = f"Scheduled maintenance from {self.name}"
		history.insert()

	def on_cancel(self):
		"""Actions when maintenance schedule is cancelled"""
		# Cancel related work order if exists
		if self.work_order:
			work_order_doc = frappe.get_doc("Work Order", self.work_order)
			if work_order_doc.docstatus == 1:
				work_order_doc.cancel()

		# Update vehicle maintenance history
		history_records = frappe.get_all(
			"Vehicle Maintenance History", filters={"maintenance_schedule": self.name}
		)
		for record in history_records:
			history_doc = frappe.get_doc("Vehicle Maintenance History", record.name)
			history_doc.status = "Cancelled"
			history_doc.save()

	@frappe.whitelist()
	def reschedule_maintenance(self, new_date, new_time=None, reason=None):
		"""Reschedule maintenance appointment"""
		old_date = self.scheduled_date
		old_time = self.scheduled_time

		self.scheduled_date = new_date
		if new_time:
			self.scheduled_time = new_time

		if reason:
			self.add_comment(
				"Info", f"Rescheduled from {old_date} {old_time} to {new_date} {new_time}. Reason: {reason}"
			)

		self.save()

		# Send notification about reschedule
		if self.customer:
			customer_doc = frappe.get_doc("Customer", self.customer)

			if frappe.db.get_value("Customer", self.customer, "language") == "ar":
				subject = f"تغيير موعد الصيانة - {self.vehicle}"
				message = f"""
                تم تغيير موعد صيانة مركبتكم:
                الموعد الجديد: {new_date} في {new_time or "الصباح"}
                """
			else:
				subject = f"Maintenance Rescheduled - {self.vehicle}"
				message = f"""
                Your maintenance appointment has been rescheduled:
                New appointment: {new_date} at {new_time or "Morning"}
                """

			if customer_doc.email_id:
				frappe.sendmail(recipients=[customer_doc.email_id], subject=subject, message=message)

	@frappe.whitelist()
	def mark_completed(self, completion_notes=None, actual_cost=None):
		"""Mark maintenance as completed"""
		self.status = "Completed"
		self.completion_date = datetime.date.today()
		self.completion_time = datetime.datetime.now().time()

		if completion_notes:
			self.completion_notes = completion_notes

		if actual_cost:
			self.actual_cost = actual_cost

		self.save()

		# Update vehicle maintenance history
		history_records = frappe.get_all(
			"Vehicle Maintenance History", filters={"maintenance_schedule": self.name}
		)
		for record in history_records:
			history_doc = frappe.get_doc("Vehicle Maintenance History", record.name)
			history_doc.status = "Completed"
			history_doc.completion_date = self.completion_date
			history_doc.actual_cost = actual_cost
			history_doc.notes = completion_notes
			history_doc.save()

		# Create next maintenance schedule if recurring
		if self.is_recurring and self.next_service_date:
			self.create_next_maintenance_schedule()

	def create_next_maintenance_schedule(self):
		"""Create next recurring maintenance schedule"""
		if not self.is_recurring or not self.next_service_date:
			return

		# Create new maintenance schedule
		new_schedule = frappe.copy_doc(self)
		new_schedule.scheduled_date = self.next_service_date
		new_schedule.status = "Scheduled"
		new_schedule.completion_date = None
		new_schedule.completion_time = None
		new_schedule.completion_notes = None
		new_schedule.actual_cost = None
		new_schedule.work_order = None
		new_schedule.previous_schedule = self.name

		# Calculate next service date for the new schedule
		new_schedule.calculate_next_service_date()

		new_schedule.insert()

		frappe.msgprint(
			_("Next maintenance schedule {0} created for {1}").format(
				new_schedule.name, new_schedule.next_service_date
			)
		)


# Utility functions
@frappe.whitelist()
def get_vehicle_maintenance_history(vehicle):
	"""Get maintenance history for a vehicle"""
	history = frappe.get_all(
		"Maintenance Schedule",
		filters={"vehicle": vehicle, "docstatus": 1},
		fields=[
			"name",
			"maintenance_type",
			"scheduled_date",
			"completion_date",
			"status",
			"total_estimated_cost",
			"actual_cost",
		],
		order_by="scheduled_date desc",
	)
	return history


@frappe.whitelist()
def get_overdue_schedules():
	"""Get overdue maintenance schedules"""
	today = datetime.date.today()
	overdue = frappe.get_all(
		"Maintenance Schedule",
		filters={
			"scheduled_date": ["<", today],
			"status": ["in", ["Scheduled", "Due Today"]],
			"docstatus": 1,
		},
		fields=[
			"name",
			"customer",
			"vehicle",
			"maintenance_type",
			"scheduled_date",
			"priority",
			"priority_score",
		],
		order_by="priority_score desc, scheduled_date asc",
	)
	return overdue


@frappe.whitelist()
def get_today_schedules():
	"""Get today's maintenance schedules"""
	today = datetime.date.today()
	schedules = frappe.get_all(
		"Maintenance Schedule",
		filters={
			"scheduled_date": today,
			"status": ["in", ["Scheduled", "Due Today", "In Progress"]],
			"docstatus": 1,
		},
		fields=[
			"name",
			"customer",
			"vehicle",
			"maintenance_type",
			"scheduled_time",
			"estimated_duration_hours",
			"priority",
		],
		order_by="scheduled_time asc",
	)
	return schedules


@frappe.whitelist()
def auto_schedule_maintenance(vehicle, maintenance_type, priority="Medium"):
	"""Auto-schedule maintenance based on vehicle service intervals"""
	vehicle_doc = frappe.get_doc("Vehicle", vehicle)

	# Get service intervals from vehicle or item master
	service_intervals = {
		"Oil Change": {"months": 3, "km": 5000},
		"Brake Service": {"months": 12, "km": 20000},
		"Tire Rotation": {"months": 6, "km": 10000},
		"Engine Tune-up": {"months": 12, "km": 15000},
		"General Inspection": {"months": 6, "km": 10000},
	}

	interval = service_intervals.get(maintenance_type, {"months": 6, "km": 10000})

	# Calculate next service date
	last_service = frappe.db.get_value(
		"Maintenance Schedule",
		filters={"vehicle": vehicle, "maintenance_type": maintenance_type, "status": "Completed"},
		fieldname="completion_date",
		order_by="completion_date desc",
	)

	if last_service:
		next_date = last_service + relativedelta(months=interval["months"])
	else:
		next_date = datetime.date.today() + relativedelta(months=interval["months"])

	# Find available time slot
	available_time = find_available_time_slot(next_date)

	# Create maintenance schedule
	schedule = frappe.new_doc("Maintenance Schedule")
	schedule.customer = vehicle_doc.owner
	schedule.vehicle = vehicle
	schedule.maintenance_type = maintenance_type
	schedule.scheduled_date = next_date
	schedule.scheduled_time = available_time
	schedule.priority = priority
	schedule.is_auto_scheduled = 1
	schedule.service_interval_type = "Months"
	schedule.service_interval_value = interval["months"]
	schedule.is_recurring = 1

	# Add default maintenance items
	default_items = get_default_maintenance_items(maintenance_type)
	for item in default_items:
		schedule.append("maintenance_items", item)

	schedule.insert()
	return schedule.name


def find_available_time_slot(date):
	"""Find available time slot for given date"""
	# Get workshop working hours (8 AM - 6 PM)
	working_hours = [8, 9, 10, 11, 13, 14, 15, 16, 17]  # Skip 12 PM (lunch)

	# Check existing schedules for the date
	existing_times = frappe.get_all(
		"Maintenance Schedule",
		filters={"scheduled_date": date, "status": ["in", ["Scheduled", "In Progress"]], "docstatus": 1},
		fields=["scheduled_time"],
	)

	occupied_hours = [t.scheduled_time.hour for t in existing_times if t.scheduled_time]

	# Find first available hour
	for hour in working_hours:
		if hour not in occupied_hours:
			return datetime.time(hour, 0)

	# If no slot available, return morning slot
	return datetime.time(8, 0)


def get_default_maintenance_items(maintenance_type):
	"""Get default items for maintenance type"""
	default_items_map = {
		"Oil Change": [
			{"item_code": "ENGINE_OIL_5W30", "quantity": 4, "description": "Engine Oil 5W-30"},
			{"item_code": "OIL_FILTER", "quantity": 1, "description": "Oil Filter"},
		],
		"Brake Service": [
			{"item_code": "BRAKE_PADS_FRONT", "quantity": 1, "description": "Front Brake Pads"},
			{"item_code": "BRAKE_FLUID", "quantity": 1, "description": "Brake Fluid DOT 4"},
		],
		"Air Filter Replacement": [
			{"item_code": "AIR_FILTER", "quantity": 1, "description": "Air Filter"},
			{"item_code": "CABIN_FILTER", "quantity": 1, "description": "Cabin Filter"},
		],
	}

	return default_items_map.get(maintenance_type, [])
