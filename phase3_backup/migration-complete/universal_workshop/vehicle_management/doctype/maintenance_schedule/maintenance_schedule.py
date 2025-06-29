# pylint: disable=no-member
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cint, flt


class MaintenanceSchedule(Document):
    """Maintenance Schedule DocType for predictive maintenance planning"""

    def validate(self):
        """Validate maintenance schedule data"""
        self.validate_intervals()
        self.validate_vehicle_type()
        self.set_arabic_translations()
        self.calculate_priority_weights()

    def validate_intervals(self):
        """Validate maintenance intervals"""
        if not self.mileage_interval and not self.time_interval_months:
            frappe.throw(_("Either mileage interval or time interval must be specified"))

        if self.mileage_interval and self.mileage_interval <= 0:
            frappe.throw(_("Mileage interval must be greater than 0"))

        if self.time_interval_months and self.time_interval_months <= 0:
            frappe.throw(_("Time interval must be greater than 0 months"))

        # Validate reasonable intervals
        if self.mileage_interval and self.mileage_interval > 100000:  # 100,000 km
            frappe.throw(_("Mileage interval seems too high. Maximum recommended: 100,000 km"))

        if self.time_interval_months and self.time_interval_months > 60:  # 5 years
            frappe.throw(_("Time interval seems too long. Maximum recommended: 60 months"))

    def validate_vehicle_type(self):
        """Validate vehicle type and service type combination"""
        if not self.vehicle_type:
            self.vehicle_type = 'All'

        if not self.service_type:
            frappe.throw(_("Service type is required"))

        # Check for duplicate schedules
        existing = frappe.db.sql("""
            SELECT name FROM `tabMaintenance Schedule`
            WHERE vehicle_type = %s
            AND service_type = %s
            AND name != %s
            AND is_active = 1
        """, [self.vehicle_type, self.service_type, self.name or ''])

        if existing:
            frappe.throw(_("Active maintenance schedule already exists for {0} - {1}")
                        .format(self.vehicle_type, self.service_type))

    def set_arabic_translations(self):
        """Set Arabic translations for service types and vehicle types"""
        # Arabic translations for service types
        service_translations = {
            'Oil Change': 'تغيير الزيت',
            'Brake Service': 'خدمة الفرامل',
            'Tire Rotation': 'تدوير الإطارات',
            'Air Filter Replacement': 'تغيير فلتر الهواء',
            'Spark Plug Replacement': 'تغيير شموع الاحتراق',
            'Battery Check': 'فحص البطارية',
            'Coolant Service': 'خدمة التبريد',
            'Transmission Service': 'خدمة ناقل الحركة',
            'Belt Replacement': 'تغيير السيور',
            'Fuel Filter Replacement': 'تغيير فلتر الوقود',
            'Annual Inspection': 'الفحص السنوي',
            'Major Service': 'الصيانة الكبرى',
            'Minor Service': 'الصيانة الصغرى'
        }

        if self.service_type and not self.service_type_ar:
            self.service_type_ar = service_translations.get(self.service_type, self.service_type)

        # Arabic translations for vehicle types
        vehicle_type_translations = {
            'All': 'جميع السيارات',
            'Sedan': 'سيدان',
            'SUV': 'دفع رباعي',
            'Pickup': 'بيك أب',
            'Hatchback': 'هاتشباك',
            'Coupe': 'كوبيه',
            'Convertible': 'قابل للطي',
            'Wagon': 'عربة',
            'Van': 'فان',
            'Truck': 'شاحنة'
        }

        if self.vehicle_type and not self.vehicle_type_ar:
            self.vehicle_type_ar = vehicle_type_translations.get(self.vehicle_type, self.vehicle_type)

    def calculate_priority_weights(self):
        """Calculate priority weights based on service criticality"""
        # Priority weights based on service type criticality
        priority_weights = {
            'Brake Service': 10,         # Critical safety
            'Oil Change': 9,             # Engine protection
            'Annual Inspection': 8,      # Legal requirement
            'Battery Check': 7,          # Starting system
            'Coolant Service': 7,        # Engine protection
            'Tire Rotation': 6,          # Safety and wear
            'Transmission Service': 6,   # Drivetrain protection
            'Belt Replacement': 5,       # Engine accessories
            'Air Filter Replacement': 4, # Performance
            'Spark Plug Replacement': 4, # Performance
            'Fuel Filter Replacement': 3, # Performance
            'Major Service': 8,          # Comprehensive
            'Minor Service': 5           # Routine
        }

        self.priority_weight = priority_weights.get(self.service_type, 5)

        # Adjust priority based on intervals
        if self.mileage_interval and self.mileage_interval <= 5000:  # Frequent service
            self.priority_weight += 1
        if self.time_interval_months and self.time_interval_months <= 3:  # Quarterly service
            self.priority_weight += 1

    def before_save(self):
        """Actions before saving the maintenance schedule"""
        # Set warning thresholds if not provided
        if not self.warning_mileage_threshold:
            self.warning_mileage_threshold = int(self.mileage_interval * 0.9) if self.mileage_interval else 0

        if not self.warning_time_threshold_days:
            warning_months = self.time_interval_months * 0.9 if self.time_interval_months else 0
            self.warning_time_threshold_days = int(warning_months * 30)  # Approximate days

        # Set description if not provided
        if not self.description:
            self.set_default_description()

    def set_default_description(self):
        """Set default description based on service type"""
        descriptions = {
            'Oil Change': 'Regular engine oil and filter replacement to maintain engine health',
            'Brake Service': 'Inspection and maintenance of brake pads, discs, and brake fluid',
            'Tire Rotation': 'Rotate tires to ensure even wear and extend tire life',
            'Air Filter Replacement': 'Replace air filter to maintain engine performance',
            'Spark Plug Replacement': 'Replace spark plugs for optimal engine performance',
            'Battery Check': 'Test battery condition and clean terminals',
            'Coolant Service': 'Replace coolant and inspect cooling system components',
            'Transmission Service': 'Service transmission fluid and filter',
            'Belt Replacement': 'Replace worn belts to prevent breakdowns',
            'Annual Inspection': 'Comprehensive annual safety and emissions inspection'
        }

        self.description = descriptions.get(self.service_type,
                                          f"Scheduled maintenance for {self.service_type}")


@frappe.whitelist()
def get_due_maintenance_alerts():
    """Get vehicles due for maintenance based on active schedules"""
    # Get all active maintenance schedules
    schedules = frappe.get_all('Maintenance Schedule',
                              filters={'is_active': 1},
                              fields=['*'])

    due_alerts = []

    for schedule in schedules:
        # Get vehicles matching this schedule
        vehicle_filters = {}
        if schedule.vehicle_type and schedule.vehicle_type != 'All':
            vehicle_filters['body_type'] = schedule.vehicle_type

        vehicles = frappe.get_all('Vehicle',
                                 filters=vehicle_filters,
                                 fields=['name', 'vin', 'make', 'model', 'current_mileage',
                                        'last_service_date', 'owner'])

        for vehicle in vehicles:
            alert = check_vehicle_maintenance_due(vehicle, schedule)
            if alert:
                due_alerts.append(alert)

    # Sort by priority and due date
    due_alerts.sort(key=lambda x: (x['priority_weight'], x['days_overdue']), reverse=True)

    return due_alerts


def check_vehicle_maintenance_due(vehicle, schedule):
    """Check if a specific vehicle is due for maintenance based on schedule"""
    from datetime import datetime

    # Get last service record for this service type
    last_service = frappe.db.sql("""
        SELECT service_date, mileage_at_service
        FROM `tabService Record`
        WHERE vehicle = %s
        AND service_type = %s
        AND status = 'Completed'
        ORDER BY service_date DESC
        LIMIT 1
    """, [vehicle.name, schedule.service_type], as_dict=True)

    current_date = datetime.now().date()
    current_mileage = flt(vehicle.current_mileage)

    # Check mileage-based due
    mileage_due = False
    mileage_overdue = 0
    if schedule.mileage_interval and current_mileage:
        if last_service:
            last_mileage = flt(last_service[0].mileage_at_service)
            mileage_since_service = current_mileage - last_mileage
            if mileage_since_service >= schedule.mileage_interval:
                mileage_due = True
                mileage_overdue = mileage_since_service - schedule.mileage_interval
        else:
            # No service history, assume due based on current mileage
            if current_mileage >= schedule.mileage_interval:
                mileage_due = True
                mileage_overdue = current_mileage - schedule.mileage_interval

    # Check time-based due
    time_due = False
    days_overdue = 0
    if schedule.time_interval_months:
        if last_service:
            last_service_date = last_service[0].service_date
            months_since_service = (current_date.year - last_service_date.year) * 12 + \
                                 (current_date.month - last_service_date.month)
            if months_since_service >= schedule.time_interval_months:
                time_due = True
                days_overdue = (current_date - last_service_date).days - \
                              (schedule.time_interval_months * 30)
        else:
            # No service history, check against vehicle creation or last known service
            if vehicle.last_service_date:
                days_since_service = (current_date - vehicle.last_service_date).days
                if days_since_service >= (schedule.time_interval_months * 30):
                    time_due = True
                    days_overdue = days_since_service - (schedule.time_interval_months * 30)

    # Return alert if due
    if mileage_due or time_due:
        return {
            'vehicle': vehicle.name,
            'vehicle_vin': vehicle.vin,
            'vehicle_display': f"{vehicle.make} {vehicle.model}",
            'owner': vehicle.owner,
            'service_type': schedule.service_type,
            'service_type_ar': schedule.service_type_ar,
            'schedule_name': schedule.name,
            'priority_weight': schedule.priority_weight,
            'mileage_due': mileage_due,
            'time_due': time_due,
            'mileage_overdue': mileage_overdue,
            'days_overdue': max(days_overdue, 0),
            'current_mileage': current_mileage,
            'description': schedule.description
        }

    return None


@frappe.whitelist()
def create_maintenance_alert(vehicle, schedule_name, alert_type='Due'):
    """Create a maintenance alert for a vehicle"""
    schedule = frappe.get_doc('Maintenance Schedule', schedule_name)

    # Check if alert already exists
    existing_alert = frappe.db.exists('Maintenance Alert', {
        'vehicle': vehicle,
        'service_type': schedule.service_type,
        'status': 'Open'
    })

    if existing_alert:
        return {'status': 'exists', 'alert_id': existing_alert}

    # Create new maintenance alert
    alert = frappe.new_doc('Maintenance Alert')
    alert.vehicle = vehicle
    alert.service_type = schedule.service_type
    alert.alert_type = alert_type
    alert.priority = 'High' if schedule.priority_weight >= 8 else 'Medium'
    alert.description = schedule.description
    alert.insert()

    return {'status': 'created', 'alert_id': alert.name}


@frappe.whitelist()
def get_service_types():
    """Get list of available service types with Arabic translations"""
    service_types = [
        {'value': 'Oil Change', 'label': 'Oil Change', 'label_ar': 'تغيير الزيت'},
        {'value': 'Brake Service', 'label': 'Brake Service', 'label_ar': 'خدمة الفرامل'},
        {'value': 'Tire Rotation', 'label': 'Tire Rotation', 'label_ar': 'تدوير الإطارات'},
        {'value': 'Air Filter Replacement', 'label': 'Air Filter Replacement', 'label_ar': 'تغيير فلتر الهواء'},
        {'value': 'Spark Plug Replacement', 'label': 'Spark Plug Replacement', 'label_ar': 'تغيير شموع الاحتراق'},
        {'value': 'Battery Check', 'label': 'Battery Check', 'label_ar': 'فحص البطارية'},
        {'value': 'Coolant Service', 'label': 'Coolant Service', 'label_ar': 'خدمة التبريد'},
        {'value': 'Transmission Service', 'label': 'Transmission Service', 'label_ar': 'خدمة ناقل الحركة'},
        {'value': 'Belt Replacement', 'label': 'Belt Replacement', 'label_ar': 'تغيير السيور'},
        {'value': 'Annual Inspection', 'label': 'Annual Inspection', 'label_ar': 'الفحص السنوي'},
        {'value': 'Major Service', 'label': 'Major Service', 'label_ar': 'الصيانة الكبرى'},
        {'value': 'Minor Service', 'label': 'Minor Service', 'label_ar': 'الصيانة الصغرى'}
    ]

    return service_types
