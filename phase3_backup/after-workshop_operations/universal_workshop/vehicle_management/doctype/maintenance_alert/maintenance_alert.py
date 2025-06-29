import datetime

from dateutil.relativedelta import relativedelta

import frappe
from frappe import _
from frappe.model.document import Document


class MaintenanceAlert(Document):
    def autoname(self):
        """Generate alert ID: MA-YYYY-NNNN"""
        year = datetime.datetime.now().year

        # Get last alert number for current year
        last_alert = frappe.db.sql(
            """
            SELECT alert_id FROM `tabMaintenance Alert`
            WHERE alert_id LIKE 'MA-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(
                year
            )
        )

        if last_alert:
            last_num = int(last_alert[0][0].split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        self.alert_id = f"MA-{year}-{new_num:04d}"

    def validate(self):
        """Validate maintenance alert data"""
        self.validate_basic_data()
        self.set_arabic_translations()
        self.calculate_overdue_values()
        self.set_customer_from_vehicle()
        self.validate_due_dates()

    def validate_basic_data(self):
        """Validate required fields"""
        if not self.vehicle:
            frappe.throw(_("Vehicle is required"))

        if not self.service_type:
            frappe.throw(_("Service type is required"))

        if not self.due_date:
            frappe.throw(_("Due date is required"))

        if not self.alert_type:
            frappe.throw(_("Alert type is required"))

    def set_arabic_translations(self):
        """Set Arabic translations for service types"""
        service_translations = {
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
            "Timing Belt": "سير التوقيت",
            "Spark Plugs": "شمعات الإشعال",
            "Fuel Filter": "فلتر الوقود",
            "Belts and Hoses": "الأحزمة والخراطيم",
            "Wheel Alignment": "ضبط زوايا العجلات",
        }

        self.service_type_ar = service_translations.get(self.service_type, self.service_type)

    def calculate_overdue_values(self):
        """Calculate overdue days and mileage"""
        today = datetime.date.today()

        # Calculate overdue days
        if self.due_date and self.due_date < today:
            self.overdue_days = (today - self.due_date).days
        else:
            self.overdue_days = 0

        # Calculate mileage overdue
        if (
            self.current_mileage
            and self.service_due_mileage
            and self.current_mileage > self.service_due_mileage
        ):
            self.mileage_overdue = self.current_mileage - self.service_due_mileage
        else:
            self.mileage_overdue = 0

    def set_customer_from_vehicle(self):
        """Set customer from vehicle link"""
        if self.vehicle and not self.customer:
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
            self.customer = vehicle_doc.owner

    def validate_due_dates(self):
        """Validate due dates logic"""
        if self.alert_type == "Time Based" and not self.due_date:
            frappe.throw(_("Due date is required for time-based alerts"))

        if self.alert_type == "Mileage Based" and not self.service_due_mileage:
            frappe.throw(_("Service due mileage is required for mileage-based alerts"))

        if self.alert_type == "Combined" and (not self.due_date or not self.service_due_mileage):
            frappe.throw(
                _("Both due date and service due mileage are required for combined alerts")
            )

    def before_save(self):
        """Actions before saving"""
        self.update_current_mileage()
        self.update_last_service_date()
        self.set_priority_based_on_urgency()

    def update_current_mileage(self):
        """Update current mileage from vehicle"""
        if self.vehicle:
            vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
            self.current_mileage = vehicle_doc.mileage

    def update_last_service_date(self):
        """Get last service date for this vehicle and service type"""
        if self.vehicle and self.service_type:
            last_service = frappe.db.get_value(
                "Service Record",
                filters={
                    "vehicle": self.vehicle,
                    "service_type": self.service_type,
                    "status": "Completed",
                    "docstatus": 1,
                },
                fieldname="service_date",
                order_by="service_date desc",
            )

            if last_service:
                self.last_service_date = last_service

    def set_priority_based_on_urgency(self):
        """Set priority based on urgency factors"""
        if not self.priority:
            priority_score = 0

            # Days overdue factor
            if self.overdue_days and self.overdue_days > 30:
                priority_score += 40
            elif self.overdue_days > 7:
                priority_score += 30
            elif self.overdue_days > 0:
                priority_score += 20

            # Days until due factor
            if self.due_date:
                days_until_due = (self.due_date - datetime.date.today()).days
                if days_until_due <= 0:
                    priority_score += 50
                elif days_until_due <= 7:
                    priority_score += 30
                elif days_until_due <= 30:
                    priority_score += 20

            # Mileage overdue factor
            if self.mileage_overdue and self.mileage_overdue > 5000:
                priority_score += 40
            elif self.mileage_overdue > 1000:
                priority_score += 30
            elif self.mileage_overdue > 0:
                priority_score += 20

            # Set priority based on score
            if priority_score >= 70:
                self.priority = "Critical"
            elif priority_score >= 50:
                self.priority = "High"
            elif priority_score >= 30:
                self.priority = "Medium"
            else:
                self.priority = "Low"

    def on_update(self):
        """Actions after update"""
        if self.status == "Active" and not self.notification_sent:
            self.send_notification()

    def send_notification(self):
        """Send notification to customer"""
        if not self.customer:
            return

        customer_doc = frappe.get_doc("Customer", self.customer)

        # Prepare notification content based on language
        if frappe.db.get_value("Customer", self.customer, "language") == "ar":
            subject = f"تنبيه صيانة مطلوبة - {self.vehicle}"
            message = self.get_arabic_message()
        else:
            subject = f"Maintenance Alert - {self.vehicle}"
            message = self.get_english_message()

        # Send email notification
        if customer_doc.email_id:
            try:
                frappe.sendmail(
                    recipients=[customer_doc.email_id], subject=subject, message=message
                )
                self.email_sent = 1
            except Exception as e:
                frappe.log_error(f"Failed to send email notification: {e!s}")

        # Send SMS notification
        if customer_doc.mobile_no:
            try:
                frappe.sendmail(
                    recipients=[customer_doc.mobile_no],
                    subject=subject,
                    message=message,
                    communication_type="SMS",
                )
                self.sms_sent = 1
            except Exception as e:
                frappe.log_error(f"Failed to send SMS notification: {e!s}")

        # Update notification status
        self.notification_sent = 1
        self.notification_date = datetime.datetime.now()
        self.db_update()

    def get_arabic_message(self):
        """Get Arabic notification message"""
        vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
        vehicle_info = f"{vehicle_doc.make} {vehicle_doc.model} ({vehicle_doc.license_plate})"

        message = f"""
        عزيزي/عزيزتي العميل،

        تحتاج مركبتكم إلى صيانة:

        🚗 المركبة: {vehicle_info}
        🔧 نوع الصيانة: {self.service_type_ar}
        📅 تاريخ الاستحقاق: {self.due_date.strftime("%d/%m/%Y")}
        ⚠️ الأولوية: {self.get_priority_arabic()}

        """

        if self.overdue_days > 0:
            message += f"🚨 متأخرة بـ {self.overdue_days} يوم\n"

        if self.mileage_overdue > 0:
            message += f"🛣️ تجاوزت المسافة المطلوبة بـ {self.mileage_overdue} كم\n"

        message += f"""
        {self.description_ar or self.description or ""}

        يرجى الاتصال بنا لحجز موعد الصيانة.
        شكراً لثقتكم بخدماتنا.
        """

        return message

    def get_english_message(self):
        """Get English notification message"""
        vehicle_doc = frappe.get_doc("Vehicle", self.vehicle)
        vehicle_info = f"{vehicle_doc.make} {vehicle_doc.model} ({vehicle_doc.license_plate})"

        message = f"""
        Dear Customer,

        Your vehicle requires maintenance:

        🚗 Vehicle: {vehicle_info}
        🔧 Service Type: {self.service_type}
        📅 Due Date: {self.due_date.strftime("%d/%m/%Y")}
        ⚠️ Priority: {self.priority}

        """

        if self.overdue_days > 0:
            message += f"🚨 Overdue by {self.overdue_days} days\n"

        if self.mileage_overdue > 0:
            message += f"🛣️ Mileage overdue by {self.mileage_overdue} km\n"

        message += f"""
        {self.description or ""}

        Please contact us to schedule your maintenance appointment.
        Thank you for choosing our services.
        """

        return message

    def get_priority_arabic(self):
        """Get priority in Arabic"""
        priority_translations = {
            "Critical": "حرجة",
            "High": "عالية",
            "Medium": "متوسطة",
            "Low": "منخفضة",
        }
        return priority_translations.get(self.priority, self.priority)

    @frappe.whitelist()
    def acknowledge_alert(self, user=None):
        """Mark alert as acknowledged"""
        self.acknowledged = 1
        self.acknowledged_by = user or frappe.session.user
        self.acknowledged_date = datetime.datetime.now()
        self.status = "Acknowledged"
        self.save()

    @frappe.whitelist()
    def dismiss_alert(self, reason=None):
        """Dismiss the alert"""
        self.status = "Dismissed"
        if reason:
            self.add_comment("Info", f"Alert dismissed. Reason: {reason}")
        self.save()

    @frappe.whitelist()
    def schedule_maintenance(self, scheduled_date, scheduled_time=None):
        """Create maintenance schedule from alert"""
        # Create maintenance schedule
        schedule = frappe.new_doc("Maintenance Schedule")
        schedule.customer = self.customer
        schedule.vehicle = self.vehicle
        schedule.maintenance_type = self.service_type
        schedule.scheduled_date = scheduled_date
        schedule.scheduled_time = scheduled_time
        schedule.priority = self.priority
        schedule.maintenance_alert_ref = self.name
        schedule.insert()

        # Update alert status
        self.status = "Scheduled"
        self.maintenance_schedule_ref = schedule.name
        self.save()

        return schedule.name


# Utility functions for scheduled jobs
def generate_maintenance_alerts():
    """Daily job to generate maintenance alerts"""
    vehicles = frappe.get_all("Vehicle", fields=["name", "owner", "mileage", "make", "model"])

    for vehicle in vehicles:
        check_time_based_maintenance(vehicle)
        check_mileage_based_maintenance(vehicle)


def check_time_based_maintenance(vehicle):
    """Check for time-based maintenance alerts"""
    # Get maintenance intervals
    maintenance_intervals = {
        "Oil Change": {"months": 3},
        "Brake Service": {"months": 12},
        "Tire Rotation": {"months": 6},
        "Engine Tune-up": {"months": 12},
        "General Inspection": {"months": 6},
        "Air Filter Replacement": {"months": 6},
        "Battery Check": {"months": 12},
    }

    for service_type, interval in maintenance_intervals.items():
        # Get last service date
        last_service = frappe.db.get_value(
            "Service Record",
            filters={
                "vehicle": vehicle["name"],
                "service_type": service_type,
                "status": "Completed",
            },
            fieldname="service_date",
            order_by="service_date desc",
        )

        # Calculate next due date
        if last_service:
            next_due = last_service + relativedelta(months=interval["months"])
        else:
            # If no service history, use 30 days from now as default
            next_due = datetime.date.today() + datetime.timedelta(days=30)

        # Check if alert needed (30 days before due date or overdue)
        alert_threshold = next_due - datetime.timedelta(days=30)

        if datetime.date.today() >= alert_threshold:
            # Check if alert already exists
            existing_alert = frappe.db.exists(
                "Maintenance Alert",
                {
                    "vehicle": vehicle["name"],
                    "service_type": service_type,
                    "status": ["in", ["Active", "Acknowledged"]],
                    "due_date": next_due,
                },
            )

            if not existing_alert:
                create_maintenance_alert(vehicle, service_type, next_due, "Time Based")


def check_mileage_based_maintenance(vehicle):
    """Check for mileage-based maintenance alerts"""
    # Get mileage intervals
    mileage_intervals = {
        "Oil Change": 5000,
        "Tire Rotation": 10000,
        "Brake Service": 20000,
        "Engine Tune-up": 15000,
        "Air Filter Replacement": 15000,
        "General Inspection": 10000,
    }

    current_mileage = vehicle.get("mileage", 0)

    for service_type, interval in mileage_intervals.items():
        # Get last service mileage
        last_service_mileage = frappe.db.get_value(
            "Service Record",
            filters={
                "vehicle": vehicle["name"],
                "service_type": service_type,
                "status": "Completed",
            },
            fieldname="mileage_at_service",
            order_by="service_date desc",
        )

        # Calculate next due mileage
        if last_service_mileage:
            next_due_mileage = last_service_mileage + interval
        else:
            next_due_mileage = current_mileage + interval

        # Check if alert needed (within 1000 km or overdue)
        if current_mileage >= (next_due_mileage - 1000):
            # Check if alert already exists
            existing_alert = frappe.db.exists(
                "Maintenance Alert",
                {
                    "vehicle": vehicle["name"],
                    "service_type": service_type,
                    "status": ["in", ["Active", "Acknowledged"]],
                    "service_due_mileage": next_due_mileage,
                },
            )

            if not existing_alert:
                # Calculate due date (estimate based on average usage)
                estimated_due_date = estimate_due_date_from_mileage(
                    vehicle["name"], next_due_mileage, current_mileage
                )
                create_maintenance_alert(
                    vehicle, service_type, estimated_due_date, "Mileage Based", next_due_mileage
                )


def create_maintenance_alert(vehicle, service_type, due_date, alert_type, service_due_mileage=None):
    """Create a new maintenance alert"""
    alert = frappe.new_doc("Maintenance Alert")
    alert.vehicle = vehicle["name"]
    alert.customer = vehicle["owner"]
    alert.service_type = service_type
    alert.due_date = due_date
    alert.alert_type = alert_type
    alert.status = "Active"
    alert.created_by_system = 1

    if service_due_mileage:
        alert.service_due_mileage = service_due_mileage

    # Set description
    alert.description = (
        f"Routine {service_type} maintenance is due for your {vehicle['make']} {vehicle['model']}"
    )
    alert.description_ar = (
        f"صيانة {alert.service_type_ar} مطلوبة لمركبتكم {vehicle['make']} {vehicle['model']}"
    )

    alert.insert()
    return alert.name


def estimate_due_date_from_mileage(vehicle, target_mileage, current_mileage):
    """Estimate due date based on mileage usage patterns"""
    # Get mileage history from service records
    mileage_history = frappe.db.sql(
        """
        SELECT service_date, mileage_at_service
        FROM `tabService Record`
        WHERE vehicle = %s AND mileage_at_service IS NOT NULL
        ORDER BY service_date DESC
        LIMIT 5
    """,
        vehicle,
        as_dict=True,
    )

    if len(mileage_history) >= 2:
        # Calculate average daily mileage
        total_days = (mileage_history[0]["service_date"] - mileage_history[-1]["service_date"]).days
        total_mileage = (
            mileage_history[0]["mileage_at_service"] - mileage_history[-1]["mileage_at_service"]
        )

        if total_days > 0:
            daily_mileage = total_mileage / total_days
            remaining_mileage = target_mileage - current_mileage

            if daily_mileage > 0:
                estimated_days = remaining_mileage / daily_mileage
                return datetime.date.today() + datetime.timedelta(days=int(estimated_days))

    # Default: assume 30 days if no history available
    return datetime.date.today() + datetime.timedelta(days=30)


@frappe.whitelist()
def get_vehicle_alerts(vehicle):
    """Get active alerts for a vehicle"""
    alerts = frappe.get_all(
        "Maintenance Alert",
        filters={"vehicle": vehicle, "status": ["in", ["Active", "Acknowledged"]]},
        fields=[
            "name",
            "service_type",
            "service_type_ar",
            "due_date",
            "priority",
            "overdue_days",
            "mileage_overdue",
        ],
        order_by="priority desc, due_date asc",
    )
    return alerts


@frappe.whitelist()
def get_customer_alerts(customer):
    """Get active alerts for a customer"""
    alerts = frappe.get_all(
        "Maintenance Alert",
        filters={"customer": customer, "status": ["in", ["Active", "Acknowledged"]]},
        fields=[
            "name",
            "vehicle",
            "service_type",
            "service_type_ar",
            "due_date",
            "priority",
            "overdue_days",
        ],
        order_by="priority desc, due_date asc",
    )
    return alerts


@frappe.whitelist()
def get_workshop_alerts_dashboard():
    """Get workshop alerts dashboard data"""
    # Count alerts by priority
    priority_counts = frappe.db.sql(
        """
        SELECT priority, COUNT(*) as count
        FROM `tabMaintenance Alert`
        WHERE status IN ('Active', 'Acknowledged')
        GROUP BY priority
    """,
        as_dict=True,
    )

    # Get overdue alerts
    overdue_alerts = frappe.db.count(
        "Maintenance Alert",
        {"status": ["in", ["Active", "Acknowledged"]], "due_date": ["<", datetime.date.today()]},
    )

    # Get due today
    due_today = frappe.db.count(
        "Maintenance Alert",
        {"status": ["in", ["Active", "Acknowledged"]], "due_date": datetime.date.today()},
    )

    # Get due this week
    week_end = datetime.date.today() + datetime.timedelta(days=7)
    due_this_week = frappe.db.count(
        "Maintenance Alert",
        {
            "status": ["in", ["Active", "Acknowledged"]],
            "due_date": ["between", [datetime.date.today(), week_end]],
        },
    )

    return {
        "priority_counts": priority_counts,
        "overdue_alerts": overdue_alerts,
        "due_today": due_today,
        "due_this_week": due_this_week,
    }
