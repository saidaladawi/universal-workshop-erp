import json
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, get_datetime, getdate, now, nowdate


class ServiceOrder(Document):
	def before_insert(self):
		"""Initialize new service order"""
		self.created_on = now()
		self.add_status_history("Draft", "Service order created")

	def validate(self):
		"""Validate service order data"""
		self.validate_service_date()
		self.validate_mileage()
		self.validate_status_transitions()
		self.set_arabic_translations()
		self.calculate_totals()

	def before_save(self):
		"""Pre-save operations"""
		if self.has_value_changed("status"):
			self.handle_status_change()
		self.update_vehicle_mileage()

	def on_submit(self):
		"""Actions on submission"""
		if self.status == "Draft":
			self.status = "Scheduled"
			self.scheduled_on = now()
		self.add_status_history(self.status, "Service order submitted")

	def validate_service_date(self):
		"""Validate service date is within acceptable range"""
		if self.service_date:
			service_date = getdate(self.service_date)
			today = getdate(nowdate())

			# Service date cannot be more than 30 days in the past
			if service_date < add_days(today, -30):
				frappe.throw(_("Service date cannot be more than 30 days in the past"))

			# Service date cannot be more than 90 days in the future
			if service_date > add_days(today, 90):
				frappe.throw(_("Service date cannot be more than 90 days in the future"))

	def validate_mileage(self):
		"""Validate current mileage against vehicle's last recorded mileage"""
		if not self.vehicle or not self.current_mileage:
			return

		vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
		if vehicle_doc.current_mileage and self.current_mileage < vehicle_doc.current_mileage:
			frappe.msgprint(
				_(
					"Warning: Current mileage ({0} km) is less than vehicle's last recorded mileage ({1} km)"
				).format(self.current_mileage, vehicle_doc.current_mileage),
				alert=True,
			)

	def validate_status_transitions(self):
		"""Validate status transition rules"""
		if not self.has_value_changed("status"):
			return

		old_status = self.get_doc_before_save().status if self.get_doc_before_save() else "Draft"
		new_status = self.status

		# Define valid status transitions
		valid_transitions = {
			"Draft": ["Scheduled", "Cancelled"],
			"Scheduled": ["In Progress", "Cancelled"],
			"In Progress": ["Quality Check", "Completed", "Cancelled"],
			"Quality Check": ["Completed", "In Progress"],
			"Completed": ["Delivered"],
			"Delivered": [],
			"Cancelled": [],
		}

		if new_status not in valid_transitions.get(old_status, []):
			frappe.throw(_("Invalid status transition from {0} to {1}").format(old_status, new_status))

	def set_arabic_translations(self):
		"""Set Arabic translations for service type and other fields"""
		if self.service_type and not self.service_type_ar:
			translations = {
				"Oil Change": "تغيير الزيت",
				"Brake Service": "خدمة الفرامل",
				"Transmission Service": "خدمة ناقل الحركة",
				"Engine Repair": "إصلاح المحرك",
				"Air Conditioning": "تكييف الهواء",
				"Electrical": "كهرباء",
				"Tire Service": "خدمة الإطارات",
				"General Maintenance": "صيانة عامة",
				"Inspection": "فحص",
				"Emergency Repair": "إصلاح طارئ",
				"Custom Service": "خدمة مخصصة",
			}
			self.service_type_ar = translations.get(self.service_type, self.service_type)

	def calculate_totals(self):
		"""Calculate parts total, labor total, and final amounts"""
		# Calculate parts total
		parts_total = 0
		for part in self.parts_used:
			if part.quantity and part.unit_price:
				part.total_amount = flt(part.quantity) * flt(part.unit_price)
				parts_total += part.total_amount

		self.parts_total = parts_total

		# Calculate labor total
		labor_total = 0
		for labor in self.labor_entries:
			if labor.hours and labor.hourly_rate:
				labor.total_amount = flt(labor.hours) * flt(labor.hourly_rate)
				labor_total += labor.total_amount

		self.labor_total = labor_total

		# Calculate subtotal
		self.subtotal = self.parts_total + self.labor_total

		# Calculate discount amount
		if self.discount_percentage:
			self.discount_amount = (self.subtotal * flt(self.discount_percentage)) / 100
		else:
			self.discount_amount = 0

		# Calculate VAT
		discounted_amount = self.subtotal - self.discount_amount
		self.vat_amount = (discounted_amount * flt(self.vat_rate or 5)) / 100

		# Calculate totals
		self.total_amount = discounted_amount + self.vat_amount
		self.final_amount = self.total_amount

	def handle_status_change(self):
		"""Handle status change operations"""
		status_timestamps = {
			"Scheduled": "scheduled_on",
			"In Progress": "started_on",
			"Quality Check": "quality_check_on",
			"Completed": "completed_on",
			"Delivered": "delivered_on",
		}

		# Set timestamp for new status
		if self.status in status_timestamps:
			setattr(self, status_timestamps[self.status], now())

		# Add status history entry
		self.add_status_history(self.status)

		# Send notifications based on status
		self.send_status_notifications()

	def add_status_history(self, status, notes=None):
		"""Add entry to status history"""
		status_translations = {
			"Draft": "مسودة",
			"Scheduled": "مجدول",
			"In Progress": "قيد التنفيذ",
			"Quality Check": "فحص الجودة",
			"Completed": "مكتمل",
			"Delivered": "تم التسليم",
			"Cancelled": "ملغى",
		}

		# Calculate duration in previous status
		duration = None
		if self.status_history:
			last_entry = self.status_history[-1]
			if last_entry.changed_on:
				last_time = get_datetime(last_entry.changed_on)
				current_time = get_datetime(now())
				duration_seconds = (current_time - last_time).total_seconds()

				# Format duration
				if duration_seconds < 3600:  # Less than 1 hour
					duration = f"{int(duration_seconds // 60)} minutes"
				elif duration_seconds < 86400:  # Less than 1 day
					duration = f"{int(duration_seconds // 3600)} hours"
				else:  # 1 day or more
					duration = f"{int(duration_seconds // 86400)} days"

				# Update duration in last entry
				last_entry.duration_in_status = duration

		# Add new status history entry
		self.append(
			"status_history",
			{
				"status": status,
				"status_ar": status_translations.get(status, status),
				"changed_by": frappe.session.user,
				"changed_on": now(),
				"notes": notes or f"Status changed to {status}",
			},
		)

	def update_vehicle_mileage(self):
		"""Update vehicle's current mileage if this is higher"""
		if not self.vehicle or not self.current_mileage:
			return

		vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
		if not vehicle_doc.current_mileage or self.current_mileage > vehicle_doc.current_mileage:
			vehicle_doc.current_mileage = self.current_mileage
			vehicle_doc.last_service_date = self.service_date
			vehicle_doc.save(ignore_permissions=True)

	def send_status_notifications(self):
		"""Send notifications based on status changes"""
		if not self.customer:
			return

		customer_doc = frappe.get_doc("Customer", self.customer)

		# Notification templates based on status
		notifications = {
			"Scheduled": {
				"subject": _("Service Scheduled - {0}").format(self.name),
				"message": _("Your vehicle service has been scheduled for {0}").format(self.service_date),
			},
			"In Progress": {
				"subject": _("Service Started - {0}").format(self.name),
				"message": _("Work has started on your vehicle. Assigned technician: {0}").format(
					self.technician_assigned
				),
			},
			"Quality Check": {
				"subject": _("Service Quality Check - {0}").format(self.name),
				"message": _("Your vehicle service is undergoing quality check"),
			},
			"Completed": {
				"subject": _("Service Completed - {0}").format(self.name),
				"message": _("Your vehicle service has been completed. Total amount: {0}").format(
					self.final_amount
				),
			},
			"Delivered": {
				"subject": _("Vehicle Delivered - {0}").format(self.name),
				"message": _("Your vehicle has been delivered. Thank you for choosing our service!"),
			},
		}

		if self.status in notifications:
			notification = notifications[self.status]

			# Send email notification
			frappe.sendmail(
				recipients=[customer_doc.email_id] if customer_doc.email_id else [],
				subject=notification["subject"],
				message=notification["message"],
				reference_doctype=self.doctype,
				reference_name=self.name,
			)

	@frappe.whitelist()
	def start_service(self):
		"""Mark service as started"""
		if self.status != "Scheduled":
			frappe.throw(_("Can only start scheduled services"))

		self.status = "In Progress"
		self.started_on = now()
		self.add_status_history("In Progress", "Service work started")
		self.save()

		return {"status": "success", "message": _("Service marked as started")}

	@frappe.whitelist()
	def complete_service(self):
		"""Mark service as completed"""
		if self.status not in ["In Progress", "Quality Check"]:
			frappe.throw(_("Can only complete services that are in progress or quality check"))

		# Validate required fields for completion
		if not self.parts_used and not self.labor_entries:
			frappe.throw(_("Please add parts used or labor entries before completing"))

		self.status = "Completed"
		self.completed_on = now()
		self.add_status_history("Completed", "Service work completed")
		self.save()

		return {"status": "success", "message": _("Service marked as completed")}

	@frappe.whitelist()
	def quality_check(self):
		"""Mark service for quality check"""
		if self.status != "In Progress":
			frappe.throw(_("Can only quality check services that are in progress"))

		self.status = "Quality Check"
		self.quality_check_on = now()
		self.add_status_history("Quality Check", "Service under quality check")
		self.save()

		return {"status": "success", "message": _("Service marked for quality check")}

	@frappe.whitelist()
	def deliver_vehicle(self):
		"""Mark vehicle as delivered"""
		if self.status != "Completed":
			frappe.throw(_("Can only deliver completed services"))

		self.status = "Delivered"
		self.delivered_on = now()
		self.add_status_history("Delivered", "Vehicle delivered to customer")
		self.save()

		return {"status": "success", "message": _("Vehicle marked as delivered")}


@frappe.whitelist()
def get_service_order_dashboard_data():
	"""Get dashboard data for service orders"""
	from frappe.utils import add_days, today

	# Status counts
	status_counts = frappe.db.sql(
		"""
        SELECT status, COUNT(*) as count
        FROM `tabService Order`
        WHERE docstatus < 2
        GROUP BY status
        ORDER BY
            CASE status
                WHEN 'Draft' THEN 1
                WHEN 'Scheduled' THEN 2
                WHEN 'In Progress' THEN 3
                WHEN 'Quality Check' THEN 4
                WHEN 'Completed' THEN 5
                WHEN 'Delivered' THEN 6
                WHEN 'Cancelled' THEN 7
            END
    """,
		as_dict=True,
	)

	# Today's services
	todays_services = frappe.db.count("Service Order", {"service_date": today(), "docstatus": ["<", 2]})

	# Overdue services (scheduled but not started)
	overdue_services = frappe.db.count(
		"Service Order", {"status": "Scheduled", "service_date": ["<", today()], "docstatus": ["<", 2]}
	)

	# Revenue this month
	from frappe.utils import get_first_day, get_last_day

	first_day = get_first_day(today())
	last_day = get_last_day(today())

	revenue_data = frappe.db.sql(
		"""
        SELECT
            SUM(final_amount) as total_revenue,
            COUNT(*) as completed_orders
        FROM `tabService Order`
        WHERE status = 'Delivered'
        AND service_date BETWEEN %s AND %s
        AND docstatus = 1
    """,
		(first_day, last_day),
		as_dict=True,
	)

	revenue = revenue_data[0] if revenue_data else {"total_revenue": 0, "completed_orders": 0}

	# Average service time
	avg_time_data = frappe.db.sql(
		"""
        SELECT AVG(TIMESTAMPDIFF(HOUR, started_on, completed_on)) as avg_hours
        FROM `tabService Order`
        WHERE started_on IS NOT NULL
        AND completed_on IS NOT NULL
        AND TIMESTAMPDIFF(HOUR, started_on, completed_on) > 0
        AND service_date >= %s
    """,
		(add_days(today(), -30),),
		as_dict=True,
	)

	avg_hours = avg_time_data[0]["avg_hours"] if avg_time_data and avg_time_data[0]["avg_hours"] else 0

	return {
		"status_counts": status_counts,
		"todays_services": todays_services,
		"overdue_services": overdue_services,
		"monthly_revenue": flt(revenue["total_revenue"]),
		"completed_orders": revenue["completed_orders"],
		"average_service_hours": flt(avg_hours),
	}


@frappe.whitelist()
def get_technician_workload():
	"""Get current workload for all technicians"""
	workload_data = frappe.db.sql(
		"""
        SELECT
            technician_assigned as technician,
            COUNT(*) as active_orders,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Scheduled' THEN 1 ELSE 0 END) as scheduled
        FROM `tabService Order`
        WHERE status IN ('Scheduled', 'In Progress', 'Quality Check')
        AND technician_assigned IS NOT NULL
        AND docstatus < 2
        GROUP BY technician_assigned
        ORDER BY active_orders DESC
    """,
		as_dict=True,
	)

	# Add technician names
	for row in workload_data:
		if row.technician:
			user_doc = frappe.get_cached_doc("User", row.technician)
			row.technician_name = user_doc.full_name or user_doc.name

	return workload_data
