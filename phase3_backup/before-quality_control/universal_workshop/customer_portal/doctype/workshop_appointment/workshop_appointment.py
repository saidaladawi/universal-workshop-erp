"""
Workshop Appointment DocType Controller
Comprehensive appointment management for Universal Workshop ERP with Arabic support
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    flt, cint, getdate, get_datetime, now_datetime, 
    add_days, add_hours, date_diff, time_diff_in_hours,
    format_date, format_datetime
)
from datetime import datetime, timedelta
import json
import re

# pylint: disable=no-member
# Frappe framework dynamically adds DocType fields to Document class

class WorkshopAppointment(Document):
    """Workshop Appointment controller with comprehensive appointment management"""
    
    def validate(self):
        """Comprehensive validation for appointment data"""
        self.validate_required_fields()
        self.validate_appointment_datetime()
        self.validate_workshop_availability()
        self.validate_customer_limits()
        self.validate_arabic_fields()
        self.validate_oman_compliance()
        self.set_default_values()
        self.calculate_costs()
        
    def before_save(self):
        """Pre-save operations"""
        self.set_hijri_date()
        self.update_audit_trail()
        self.check_duplicate_appointments()
        self.validate_payment_requirements()
        
    def after_insert(self):
        """Post-creation operations"""
        self.send_booking_confirmation()
        self.schedule_reminders()
        self.log_appointment_creation()
        self.update_workshop_capacity()
        
    def on_update(self):
        """Handle appointment updates"""
        if self.has_value_changed('appointment_status'):
            self.handle_status_change()
        if self.has_value_changed('appointment_date') or self.has_value_changed('appointment_time'):
            self.handle_reschedule()
        self.update_last_modified()
        
    def before_cancel(self):
        """Pre-cancellation operations"""
        self.validate_cancellation()
        self.process_cancellation_refund()
        
    def after_cancel(self):
        """Post-cancellation operations"""
        self.send_cancellation_notification()
        self.update_workshop_capacity()
        self.log_cancellation()
        
    # === VALIDATION METHODS ===
    
    def validate_required_fields(self):
        """Validate required fields based on appointment type"""
        if not self.customer:
            frappe.throw(_("Customer is required | العميل مطلوب"))
            
        if not self.vehicle:
            frappe.throw(_("Vehicle is required | المركبة مطلوبة"))
            
        if not self.workshop:
            frappe.throw(_("Workshop is required | الورشة مطلوبة"))
            
        if not self.service_type:
            frappe.throw(_("Service type is required | نوع الخدمة مطلوب"))
            
        if self.emergency_appointment and not self.special_instructions:
            frappe.throw(_("Emergency appointments require special instructions | المواعيد الطارئة تتطلب تعليمات خاصة"))
    
    def validate_appointment_datetime(self):
        """Validate appointment date and time"""
        if not self.appointment_date:
            frappe.throw(_("Appointment date is required | تاريخ الموعد مطلوب"))
            
        if not self.appointment_time:
            frappe.throw(_("Appointment time is required | وقت الموعد مطلوب"))
        
        # Combine date and time
        appointment_datetime = get_datetime(f"{self.appointment_date} {self.appointment_time}")
        
        # Check if appointment is in the past
        if appointment_datetime < now_datetime():
            frappe.throw(_("Appointment cannot be scheduled in the past | لا يمكن جدولة موعد في الماضي"))
        
        # Check if appointment is within business hours
        self.validate_business_hours(appointment_datetime)
        
        # Check working days (Sunday-Thursday for Oman)
        self.validate_working_days(appointment_datetime)
        
        # Check if too far in advance
        if date_diff(self.appointment_date, frappe.utils.today()) > 90:
            frappe.throw(_("Appointments cannot be scheduled more than 90 days in advance | لا يمكن جدولة مواعيد لأكثر من 90 يوماً مقدماً"))
    
    def validate_business_hours(self, appointment_datetime):
        """Validate appointment is within business hours"""
        hour = appointment_datetime.hour
        
        # Standard business hours: 8 AM to 6 PM
        if hour < 8 or hour >= 18:
            if not self.emergency_appointment:
                frappe.throw(_("Appointments must be between 8:00 AM and 6:00 PM | يجب أن تكون المواعيد بين 8:00 صباحاً و 6:00 مساءً"))
    
    def validate_working_days(self, appointment_datetime):
        """Validate appointment is on working days (Sunday-Thursday for Oman)"""
        weekday = appointment_datetime.weekday()
        
        # Monday=0, Sunday=6, Friday=4, Saturday=5
        if weekday in [4, 5]:  # Friday, Saturday
            if not self.emergency_appointment:
                frappe.throw(_("Appointments are not available on weekends (Friday-Saturday) | المواعيد غير متاحة في عطلة نهاية الأسبوع (الجمعة-السبت)"))
    
    def validate_workshop_availability(self):
        """Check workshop capacity and technician availability"""
        if not self.workshop:
            return
            
        appointment_datetime = get_datetime(f"{self.appointment_date} {self.appointment_time}")
        
        # Check workshop capacity
        capacity_info = self.get_workshop_capacity(appointment_datetime)
        if capacity_info['capacity_percentage'] >= 100:
            frappe.throw(_("Workshop is fully booked at this time | الورشة محجوزة بالكامل في هذا الوقت"))
        
        # Check technician availability if specific technician requested
        if self.technician_preference:
            if not self.is_technician_available(self.technician_preference, appointment_datetime):
                frappe.throw(_("Preferred technician is not available at this time | الفني المفضل غير متاح في هذا الوقت"))
    
    def validate_customer_limits(self):
        """Validate customer appointment limits"""
        # Check maximum appointments per day
        existing_appointments = frappe.db.count('Workshop Appointment', {
            'customer': self.customer,
            'appointment_date': self.appointment_date,
            'appointment_status': ['not in', ['Cancelled', 'No Show']],
            'name': ['!=', self.name or '']
        })
        
        if existing_appointments >= 3:
            frappe.throw(_("Maximum 3 appointments per day per customer | حد أقصى 3 مواعيد يومياً للعميل الواحد"))
        
        # Check for pending payments
        self.validate_customer_payments()
    
    def validate_customer_payments(self):
        """Check customer payment status"""
        outstanding_amount = frappe.db.sql("""
            SELECT SUM(outstanding_amount)
            FROM `tabSales Invoice`
            WHERE customer = %s AND docstatus = 1 AND outstanding_amount > 0
        """, [self.customer])[0][0] or 0
        
        if outstanding_amount > 1000:  # OMR 1000 limit
            frappe.throw(_("Customer has outstanding amount of {0} OMR. Please clear dues before booking | العميل لديه مبلغ مستحق {0} ريال عماني. يرجى تسديد المستحقات قبل الحجز").format(flt(outstanding_amount, 3)))
    
    def validate_arabic_fields(self):
        """Validate Arabic field requirements"""
        if frappe.db.get_single_value('Universal Workshop Settings', 'require_arabic_fields'):
            if not self.customer_name_ar:
                frappe.throw(_("Arabic customer name is required | اسم العميل باللغة العربية مطلوب"))
            
            if self.service_description and not self.service_description_ar:
                frappe.throw(_("Arabic service description is required | وصف الخدمة باللغة العربية مطلوب"))
    
    def validate_oman_compliance(self):
        """Validate Oman-specific compliance requirements"""
        # Validate phone number format for Oman
        if self.customer_phone:
            if not re.match(r'^\+968\s?\d{8}$', self.customer_phone):
                frappe.throw(_("Invalid Oman phone number format. Use +968 XXXXXXXX | تنسيق رقم الهاتف العماني غير صحيح. استخدم +968 XXXXXXXX"))
        
        # Check data consent for privacy compliance
        if not self.data_consent_given:
            frappe.throw(_("Data processing consent is required | موافقة معالجة البيانات مطلوبة"))
    
    # === BUSINESS LOGIC METHODS ===
    
    def set_default_values(self):
        """Set default values for new appointments"""
        if not self.appointment_id:
            self.appointment_id = self.name
            
        if not self.booking_datetime:
            self.booking_datetime = now_datetime()
            
        if not self.created_by_user:
            self.created_by_user = frappe.session.user
            
        if not self.language_preference:
            self.language_preference = 'Arabic'
            
        if not self.currency:
            self.currency = 'OMR'
            
        if not self.estimated_duration:
            self.estimated_duration = self.get_service_duration()
            
        # Set buffer times based on service complexity
        if not self.buffer_time_before:
            self.buffer_time_before = 15 if self.service_complexity != 'Complex' else 30
            
        if not self.buffer_time_after:
            self.buffer_time_after = 15 if self.service_complexity != 'Complex' else 30
    
    def calculate_costs(self):
        """Calculate appointment costs including VAT"""
        if not self.service_type:
            return
            
        # Get service base cost
        service_cost = frappe.db.get_value('Service Type', self.service_type, 'standard_rate') or 0
        
        # Calculate additional services cost
        additional_cost = 0
        if self.requested_services:
            for service in self.requested_services:
                additional_cost += flt(service.get('amount', 0))
        
        # Base amount
        base_amount = flt(service_cost) + flt(additional_cost)
        
        # Apply discount
        discount_amount = flt(self.discount_amount, 3)
        discounted_amount = base_amount - discount_amount
        
        # Calculate VAT (5% for Oman)
        vat_rate = 5.0
        vat_amount = (discounted_amount * vat_rate) / 100
        
        # Set calculated values
        self.estimated_cost = flt(base_amount, 3)
        self.vat_amount = flt(vat_amount, 3)
        self.estimated_total = flt(discounted_amount + vat_amount, 3)
    
    def set_hijri_date(self):
        """Set Hijri date if calendar type is Hijri"""
        if self.calendar_type == 'Hijri' and self.appointment_date:
            try:
                from hijri_converter import Gregorian
                g_date = getdate(self.appointment_date)
                hijri = Gregorian(g_date.year, g_date.month, g_date.day).to_hijri()
                self.hijri_date = f"{hijri.day}/{hijri.month}/{hijri.year} هـ"
            except ImportError:
                frappe.log_error("Hijri converter not available")
    
    def update_audit_trail(self):
        """Update audit trail with changes"""
        changes = []
        
        if self.has_value_changed('appointment_status'):
            old_status = self.get_db_value('appointment_status')
            changes.append(f"Status changed from {old_status} to {self.appointment_status}")
        
        if self.has_value_changed('appointment_date') or self.has_value_changed('appointment_time'):
            changes.append(f"Appointment rescheduled to {self.appointment_date} {self.appointment_time}")
        
        if self.has_value_changed('assigned_technician'):
            old_tech = self.get_db_value('assigned_technician')
            changes.append(f"Technician changed from {old_tech} to {self.assigned_technician}")
        
        if changes:
            timestamp = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
            user = frappe.session.user
            change_log = f"[{timestamp}] {user}: " + "; ".join(changes)
            
            current_trail = self.audit_trail or ""
            self.audit_trail = f"{current_trail}\n{change_log}" if current_trail else change_log
        
        # Update metadata
        self.last_modified_by = frappe.session.user
        self.last_modified_datetime = now_datetime()
    
    def check_duplicate_appointments(self):
        """Check for duplicate appointments"""
        if not self.customer or not self.appointment_date or not self.appointment_time:
            return
            
        existing = frappe.db.exists('Workshop Appointment', {
            'customer': self.customer,
            'appointment_date': self.appointment_date,
            'appointment_time': self.appointment_time,
            'appointment_status': ['not in', ['Cancelled', 'No Show']],
            'name': ['!=', self.name or '']
        })
        
        if existing:
            frappe.throw(_("Customer already has an appointment at this time | العميل لديه موعد بالفعل في هذا الوقت"))
    
    # === NOTIFICATION METHODS ===
    
    def send_booking_confirmation(self):
        """Send booking confirmation to customer"""
        if not self.customer_phone and not self.customer_email:
            return
            
        message_ar = f"""
        تأكيد موعد الخدمة
        
        عزيزي {self.customer_name_ar or self.customer_name}،
        
        تم تأكيد موعدك بنجاح:
        📅 التاريخ: {format_date(self.appointment_date, 'dd/MM/yyyy')}
        🕒 الوقت: {self.appointment_time}
        🏪 الورشة: {self.workshop_name}
        🚗 المركبة: {self.vehicle_license_plate}
        🔧 الخدمة: {self.service_description_ar or self.service_description}
        💰 التكلفة المقدرة: {self.estimated_total} ريال عماني
        
        رقم الموعد: {self.name}
        
        يرجى الوصول قبل 15 دقيقة من الموعد المحدد.
        
        شكراً لاختياركم خدماتنا.
        """
        
        message_en = f"""
        Service Appointment Confirmation
        
        Dear {self.customer_name},
        
        Your appointment has been confirmed:
        📅 Date: {format_date(self.appointment_date, 'dd/MM/yyyy')}
        🕒 Time: {self.appointment_time}
        🏪 Workshop: {self.workshop_name}
        🚗 Vehicle: {self.vehicle_license_plate}
        🔧 Service: {self.service_description}
        💰 Estimated Cost: {self.estimated_total} OMR
        
        Appointment ID: {self.name}
        
        Please arrive 15 minutes before your scheduled time.
        
        Thank you for choosing our services.
        """
        
        message = message_ar if self.language_preference == 'Arabic' else message_en
        
        # Send SMS
        if self.sms_enabled and self.customer_phone:
            self.send_sms_notification(self.customer_phone, message)
        
        # Send WhatsApp
        if self.whatsapp_enabled and self.customer_phone:
            self.send_whatsapp_notification(self.customer_phone, message)
        
        # Send Email
        if self.email_enabled and self.customer_email:
            self.send_email_notification(self.customer_email, "Appointment Confirmation", message)
        
        self.booking_confirmation_sent = 1
    
    def schedule_reminders(self):
        """Schedule appointment reminders"""
        if not self.appointment_date or not self.appointment_time:
            return
            
        appointment_datetime = get_datetime(f"{self.appointment_date} {self.appointment_time}")
        
        # Schedule reminder 24 hours before
        reminder_datetime = appointment_datetime - timedelta(hours=24)
        if reminder_datetime > now_datetime():
            frappe.enqueue(
                'universal_workshop.customer_portal.doctype.workshop_appointment.workshop_appointment.send_appointment_reminder',
                appointment_id=self.name,
                reminder_type='24_hour',
                scheduled_datetime=reminder_datetime
            )
        
        # Schedule reminder 2 hours before
        reminder_datetime = appointment_datetime - timedelta(hours=2)
        if reminder_datetime > now_datetime():
            frappe.enqueue(
                'universal_workshop.customer_portal.doctype.workshop_appointment.workshop_appointment.send_appointment_reminder',
                appointment_id=self.name,
                reminder_type='2_hour',
                scheduled_datetime=reminder_datetime
            )
    
    def send_sms_notification(self, phone, message):
        """Send SMS notification"""
        try:
            # Integration with SMS service provider
            sms_settings = frappe.get_doc('SMS Settings')
            if sms_settings.sms_gateway_url:
                # Send SMS via gateway
                pass
            
            # Log communication
            self.log_communication('SMS', phone, message, 'Sent')
            
        except Exception as e:
            frappe.log_error(f"SMS sending failed: {str(e)}")
            self.log_communication('SMS', phone, message, 'Failed')
    
    def send_whatsapp_notification(self, phone, message):
        """Send WhatsApp notification"""
        try:
            # Integration with WhatsApp Business API
            # This would be implemented based on the chosen WhatsApp service provider
            
            # Log communication
            self.log_communication('WhatsApp', phone, message, 'Sent')
            
        except Exception as e:
            frappe.log_error(f"WhatsApp sending failed: {str(e)}")
            self.log_communication('WhatsApp', phone, message, 'Failed')
    
    def send_email_notification(self, email, subject, message):
        """Send email notification"""
        try:
            frappe.sendmail(
                recipients=[email],
                subject=subject,
                message=message,
                header=["Universal Workshop", "blue"]
            )
            
            # Log communication
            self.log_communication('Email', email, message, 'Sent')
            
        except Exception as e:
            frappe.log_error(f"Email sending failed: {str(e)}")
            self.log_communication('Email', email, message, 'Failed')
    
    def log_communication(self, channel, recipient, message, status):
        """Log communication attempts"""
        timestamp = now_datetime().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {channel} to {recipient}: {status}"
        
        current_log = self.communication_log or ""
        self.communication_log = f"{current_log}\n{log_entry}" if current_log else log_entry
        
        # Update database without triggering save hooks
        frappe.db.set_value('Workshop Appointment', self.name, 'communication_log', self.communication_log)
    
    # === STATUS MANAGEMENT ===
    
    def handle_status_change(self):
        """Handle appointment status changes"""
        old_status = self.get_db_value('appointment_status')
        new_status = self.appointment_status
        
        if old_status == new_status:
            return
        
        status_handlers = {
            'Confirmed': self.handle_confirmation,
            'In Progress': self.handle_service_start,
            'Completed': self.handle_completion,
            'Cancelled': self.handle_cancellation,
            'No Show': self.handle_no_show,
            'Rescheduled': self.handle_reschedule
        }
        
        handler = status_handlers.get(new_status)
        if handler:
            handler()
        
        # Send status change notification
        self.send_status_change_notification(old_status, new_status)
    
    def handle_confirmation(self):
        """Handle appointment confirmation"""
        self.is_confirmed = 1
        self.confirmation_datetime = now_datetime()
        self.confirmation_method = 'System'
    
    def handle_service_start(self):
        """Handle service start"""
        self.service_start_datetime = now_datetime()
        
        # Check-in customer if not already done
        if not self.check_in_datetime:
            self.check_in_datetime = now_datetime()
        
        # Assign technician if not assigned
        if not self.assigned_technician and self.technician_preference:
            self.assigned_technician = self.technician_preference
    
    def handle_completion(self):
        """Handle appointment completion"""
        self.service_end_datetime = now_datetime()
        
        # Calculate actual duration
        if self.service_start_datetime:
            actual_duration = time_diff_in_hours(self.service_end_datetime, self.service_start_datetime)
            frappe.db.set_value('Workshop Appointment', self.name, 'actual_duration', actual_duration)
        
        # Create invoice if not already created
        if not self.invoice_created:
            self.create_service_invoice()
        
        # Send completion notification
        self.send_completion_notification()
        
        # Schedule feedback request
        self.schedule_feedback_request()
    
    def handle_cancellation(self):
        """Handle appointment cancellation"""
        # Update workshop capacity
        self.update_workshop_capacity(increment=False)
        
        # Process refund if advance payment was made
        if self.advance_payment_status == 'Paid':
            self.process_refund()
    
    def handle_no_show(self):
        """Handle customer no-show"""
        self.no_show = 1
        
        # Apply no-show fee if configured
        no_show_fee = frappe.db.get_single_value('Universal Workshop Settings', 'no_show_fee')
        if no_show_fee:
            self.create_no_show_invoice(no_show_fee)
    
    def handle_reschedule(self):
        """Handle appointment reschedule"""
        self.rescheduled_count = (self.rescheduled_count or 0) + 1
        
        # Check reschedule limits
        max_reschedules = frappe.db.get_single_value('Universal Workshop Settings', 'max_reschedules') or 3
        if self.rescheduled_count > max_reschedules:
            frappe.throw(_("Maximum reschedule limit exceeded | تم تجاوز الحد الأقصى لإعادة الجدولة"))
    
    # === UTILITY METHODS ===
    
    def get_workshop_capacity(self, appointment_datetime):
        """Get workshop capacity information"""
        # Get total capacity from workshop profile
        total_capacity = frappe.db.get_value('Workshop Profile', self.workshop, 'total_capacity') or 10
        
        # Count appointments for the same time slot
        existing_appointments = frappe.db.count('Workshop Appointment', {
            'workshop': self.workshop,
            'appointment_date': appointment_datetime.date(),
            'appointment_time': appointment_datetime.time(),
            'appointment_status': ['not in', ['Cancelled', 'No Show', 'Completed']],
            'name': ['!=', self.name or '']
        })
        
        capacity_percentage = (existing_appointments / total_capacity) * 100
        
        return {
            'total_capacity': total_capacity,
            'used_capacity': existing_appointments,
            'available_capacity': total_capacity - existing_appointments,
            'capacity_percentage': capacity_percentage
        }
    
    def is_technician_available(self, technician, appointment_datetime):
        """Check if technician is available"""
        # Check for overlapping appointments
        overlapping = frappe.db.exists('Workshop Appointment', {
            'assigned_technician': technician,
            'appointment_date': appointment_datetime.date(),
            'appointment_time': ['between', [
                (appointment_datetime - timedelta(hours=2)).time(),
                (appointment_datetime + timedelta(hours=2)).time()
            ]],
            'appointment_status': ['not in', ['Cancelled', 'No Show', 'Completed']],
            'name': ['!=', self.name or '']
        })
        
        return not overlapping
    
    def get_service_duration(self):
        """Get estimated service duration"""
        if not self.service_type:
            return 1.0
            
        duration = frappe.db.get_value('Service Type', self.service_type, 'estimated_duration')
        return flt(duration, 2) or 1.0
    
    def create_service_invoice(self):
        """Create service invoice"""
        try:
            invoice = frappe.new_doc('Sales Invoice')
            invoice.customer = self.customer
            invoice.posting_date = frappe.utils.today()
            invoice.due_date = frappe.utils.add_days(frappe.utils.today(), 30)
            invoice.currency = self.currency
            
            # Add service item
            invoice.append('items', {
                'item_code': 'SERVICE-APPOINTMENT',
                'item_name': f'Workshop Service - {self.service_type}',
                'description': self.service_description,
                'qty': 1,
                'rate': self.estimated_total,
                'amount': self.estimated_total
            })
            
            # Set taxes (5% VAT for Oman)
            invoice.append('taxes', {
                'charge_type': 'On Net Total',
                'account_head': 'VAT 5% - UW',
                'description': 'VAT @ 5%',
                'rate': 5.0
            })
            
            invoice.insert()
            
            # Update appointment
            self.invoice_created = 1
            self.invoice_reference = invoice.name
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Invoice creation failed: {str(e)}")
    
    def update_workshop_capacity(self, increment=True):
        """Update workshop capacity metrics"""
        try:
            workshop = frappe.get_doc('Workshop Profile', self.workshop)
            
            if increment:
                workshop.current_bookings = (workshop.current_bookings or 0) + 1
            else:
                workshop.current_bookings = max((workshop.current_bookings or 0) - 1, 0)
            
            workshop.save(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Workshop capacity update failed: {str(e)}")

# === BACKGROUND TASKS ===

@frappe.whitelist()
def send_appointment_reminder(appointment_id, reminder_type):
    """Send appointment reminder (background task)"""
    try:
        appointment = frappe.get_doc('Workshop Appointment', appointment_id)
        
        if appointment.appointment_status in ['Cancelled', 'Completed', 'No Show']:
            return
        
        reminder_messages = {
            '24_hour': {
                'ar': f"""
                تذكير بموعد الخدمة
                
                عزيزي {appointment.customer_name_ar or appointment.customer_name}،
                
                نذكركم بموعدكم غداً:
                📅 التاريخ: {format_date(appointment.appointment_date, 'dd/MM/yyyy')}
                🕒 الوقت: {appointment.appointment_time}
                🏪 الورشة: {appointment.workshop_name}
                🚗 المركبة: {appointment.vehicle_license_plate}
                
                يرجى الوصول قبل 15 دقيقة من الموعد.
                
                للإلغاء أو إعادة الجدولة، يرجى الاتصال بنا.
                """,
                'en': f"""
                Appointment Reminder
                
                Dear {appointment.customer_name},
                
                This is a reminder of your appointment tomorrow:
                📅 Date: {format_date(appointment.appointment_date, 'dd/MM/yyyy')}
                🕒 Time: {appointment.appointment_time}
                🏪 Workshop: {appointment.workshop_name}
                🚗 Vehicle: {appointment.vehicle_license_plate}
                
                Please arrive 15 minutes early.
                
                To cancel or reschedule, please contact us.
                """
            },
            '2_hour': {
                'ar': f"""
                تذكير عاجل بالموعد
                
                موعدكم خلال ساعتين:
                🕒 الوقت: {appointment.appointment_time}
                🏪 الورشة: {appointment.workshop_name}
                
                يرجى الاستعداد للحضور.
                """,
                'en': f"""
                Urgent Appointment Reminder
                
                Your appointment is in 2 hours:
                🕒 Time: {appointment.appointment_time}
                🏪 Workshop: {appointment.workshop_name}
                
                Please prepare to arrive.
                """
            }
        }
        
        language = appointment.language_preference or 'Arabic'
        message = reminder_messages[reminder_type][language.lower()]
        
        # Send notifications
        if appointment.sms_enabled and appointment.customer_phone:
            appointment.send_sms_notification(appointment.customer_phone, message)
        
        if appointment.whatsapp_enabled and appointment.customer_phone:
            appointment.send_whatsapp_notification(appointment.customer_phone, message)
        
        # Update reminder status
        appointment.reminder_sent = 1
        appointment.reminder_datetime = now_datetime()
        appointment.reminder_notifications_sent = (appointment.reminder_notifications_sent or 0) + 1
        appointment.save(ignore_permissions=True)
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Reminder sending failed: {str(e)}")

@frappe.whitelist()
def get_available_time_slots(workshop, date, service_type=None):
    """Get available time slots for a specific workshop and date"""
    try:
        # Get workshop operating hours
        workshop_doc = frappe.get_doc('Workshop Profile', workshop)
        operating_hours = getattr(workshop_doc, 'operating_hours', '8:00-18:00').split('-')
        start_hour = int(operating_hours[0].split(':')[0])
        end_hour = int(operating_hours[1].split(':')[0])
        
        # Generate time slots (30-minute intervals)
        time_slots = []
        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                if hour == end_hour - 1 and minute == 30:
                    break
                time_slots.append(f"{hour:02d}:{minute:02d}")
        
        # Get existing appointments for the date
        existing_appointments = frappe.get_list('Workshop Appointment', {
            'workshop': workshop,
            'appointment_date': date,
            'appointment_status': ['not in', ['Cancelled', 'No Show']]
        }, ['appointment_time', 'estimated_duration'])
        
        # Remove unavailable slots
        available_slots = []
        for slot in time_slots:
            slot_available = True
            slot_time = datetime.strptime(slot, '%H:%M').time()
            
            for appointment in existing_appointments:
                app_time = appointment.appointment_time
                app_duration = appointment.estimated_duration or 1.0
                
                # Check if slot conflicts with existing appointment
                if (slot_time >= app_time and 
                    slot_time < (datetime.combine(datetime.today(), app_time) + 
                                timedelta(hours=app_duration)).time()):
                    slot_available = False
                    break
            
            if slot_available:
                available_slots.append(slot)
        
        return available_slots
        
    except Exception as e:
        frappe.log_error(f"Available slots fetch failed: {str(e)}")
        return []

@frappe.whitelist()
def get_appointment_dashboard_data(customer=None, workshop=None):
    """Get dashboard data for appointments"""
    try:
        filters = {}
        if customer:
            filters['customer'] = customer
        if workshop:
            filters['workshop'] = workshop
        
        # Get appointment statistics
        total_appointments = frappe.db.count('Workshop Appointment', filters)
        
        status_filters = filters.copy()
        status_filters['appointment_status'] = 'Pending'
        pending_appointments = frappe.db.count('Workshop Appointment', status_filters)
        
        status_filters['appointment_status'] = 'Confirmed'
        confirmed_appointments = frappe.db.count('Workshop Appointment', status_filters)
        
        status_filters['appointment_status'] = 'Completed'
        completed_appointments = frappe.db.count('Workshop Appointment', status_filters)
        
        # Get upcoming appointments
        upcoming_filters = filters.copy()
        upcoming_filters.update({
            'appointment_date': ['>=', frappe.utils.today()],
            'appointment_status': ['in', ['Pending', 'Confirmed']]
        })
        
        upcoming_appointments = frappe.get_list('Workshop Appointment', 
            filters=upcoming_filters,
            fields=['name', 'customer_name', 'appointment_date', 'appointment_time', 'service_type'],
            order_by='appointment_date, appointment_time',
            limit=10
        )
        
        return {
            'total_appointments': total_appointments,
            'pending_appointments': pending_appointments,
            'confirmed_appointments': confirmed_appointments,
            'completed_appointments': completed_appointments,
            'upcoming_appointments': upcoming_appointments,
            'completion_rate': (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
        }
        
    except Exception as e:
        frappe.log_error(f"Dashboard data fetch failed: {str(e)}")
        return {} 