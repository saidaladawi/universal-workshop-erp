# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime, timedelta
import json

class ServiceHistoryTracker(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate service history tracker data before saving"""
        self.validate_arabic_fields()
        self.validate_dates()
        self.calculate_costs()
        self.update_progress()
        self.validate_status_workflow()
        
    def before_save(self):
        """Set default values and update tracking before saving"""
        self.set_metadata()
        self.update_last_modified()
        self.sync_with_service_order()
        
    def after_save(self):
        """Post-save operations"""
        self.update_status_timeline()
        self.send_notifications()
        self.update_customer_portal()
        
    def validate_arabic_fields(self):
        """Ensure Arabic fields are properly filled"""
        if not self.service_description_ar and self.service_description:
            frappe.throw(_("Arabic service description is required"))
            
        # Validate Arabic text direction and content
        arabic_fields = ['service_description_ar', 'customer_notes_ar', 
                        'technician_notes_ar', 'stage_description_ar']
        
        for field in arabic_fields:
            if hasattr(self, field) and getattr(self, field):
                self.validate_arabic_text(getattr(self, field), field)
                
    def validate_arabic_text(self, text, field_name):
        """Validate Arabic text contains proper Arabic characters"""
        import re
        if text and not re.search(r'[\u0600-\u06FF]', text):
            frappe.msgprint(_("Field {0} should contain Arabic text").format(_(field_name)))
            
    def validate_dates(self):
        """Validate date fields for logical consistency"""
        if self.service_date and self.estimated_completion:
            if self.estimated_completion < self.service_date:
                frappe.throw(_("Estimated completion cannot be before service date"))
                
        if self.actual_completion and self.service_date:
            if self.actual_completion < self.service_date:
                frappe.throw(_("Actual completion cannot be before service date"))
                
    def calculate_costs(self):
        """Calculate and update cost fields"""
        # Calculate labor cost
        if self.labor_hours and self.hourly_rate:
            self.labor_cost = float(self.labor_hours) * float(self.hourly_rate)
            
        # Calculate parts cost from child tables
        parts_total = 0
        if hasattr(self, 'parts_used') and self.parts_used:
            for part in self.parts_used:
                if hasattr(part, 'total_cost') and part.total_cost:
                    parts_total += float(part.total_cost)
        self.parts_cost = parts_total
        
        # Calculate total cost
        labor_cost = float(self.labor_cost or 0)
        parts_cost = float(self.parts_cost or 0)
        self.total_cost = labor_cost + parts_cost
        
        # Update billing amounts
        if not self.total_amount:
            self.total_amount = self.total_cost
            
        # Calculate balance
        paid_amount = float(self.paid_amount or 0)
        total_amount = float(self.total_amount or 0)
        self.balance_amount = total_amount - paid_amount
        
    def update_progress(self):
        """Update progress percentage based on current stage"""
        stage_progress_map = {
            'Vehicle Received': 10,
            'Diagnosis in Progress': 25,
            'Awaiting Customer Approval': 35,
            'Parts Ordered': 45,
            'Work in Progress': 70,
            'Quality Check': 85,
            'Ready for Pickup': 95,
            'Completed': 100
        }
        
        if self.current_stage and self.current_stage in stage_progress_map:
            self.progress_percentage = stage_progress_map[self.current_stage]
            
    def validate_status_workflow(self):
        """Validate status transitions follow proper workflow"""
        valid_transitions = {
            'Received': ['In Progress', 'Cancelled'],
            'In Progress': ['Pending Parts', 'Quality Check', 'Cancelled'],
            'Pending Parts': ['In Progress', 'Cancelled'],
            'Quality Check': ['Ready for Delivery', 'In Progress', 'Cancelled'],
            'Ready for Delivery': ['Completed', 'Cancelled'],
            'Completed': [],
            'Cancelled': []
        }
        
        if self.is_new():
            return
            
        old_doc = self.get_doc_before_save()
        if old_doc and old_doc.status != self.status:
            if self.status not in valid_transitions.get(old_doc.status, []):
                frappe.throw(_("Invalid status transition from {0} to {1}").format(
                    _(old_doc.status), _(self.status)))
                    
    def set_metadata(self):
        """Set metadata fields"""
        if self.is_new():
            self.created_by = frappe.session.user
            self.created_date = frappe.utils.today()
            
        self.last_modified_by = frappe.session.user
        self.last_modified_date = frappe.utils.now()
        self.last_update = frappe.utils.now()
        
        # Set workshop from service order if not set
        if not self.workshop and self.service_order:
            service_order = frappe.get_doc('Service Order', self.service_order)
            if hasattr(service_order, 'workshop'):
                self.workshop = service_order.workshop
                
    def update_last_modified(self):
        """Update last modified timestamp"""
        self.last_modified_date = frappe.utils.now()
        
    def sync_with_service_order(self):
        """Sync data with related service order"""
        if self.service_order:
            try:
                service_order = frappe.get_doc('Service Order', self.service_order)
                
                # Update service order status if changed
                if service_order.status != self.status:
                    service_order.status = self.status
                    service_order.save(ignore_permissions=True)
                    
                # Sync cost information
                if self.total_cost and service_order.total_cost != self.total_cost:
                    service_order.total_cost = self.total_cost
                    service_order.save(ignore_permissions=True)
                    
            except frappe.DoesNotExistError:
                frappe.log_error(f"Service Order {self.service_order} not found")
                
    def update_status_timeline(self):
        """Add status change to timeline"""
        if not self.is_new():
            old_doc = self.get_doc_before_save()
            if old_doc and old_doc.status != self.status:
                self.add_timeline_entry(
                    old_status=old_doc.status,
                    new_status=self.status,
                    notes=f"Status changed from {old_doc.status} to {self.status}"
                )
                
    def add_timeline_entry(self, old_status=None, new_status=None, notes=None):
        """Add entry to status timeline"""
        if not hasattr(self, 'status_timeline') or not self.status_timeline:
            self.status_timeline = []
            
        timeline_entry = {
            'timestamp': frappe.utils.now(),
            'user': frappe.session.user,
            'old_status': old_status or '',
            'new_status': new_status or self.status,
            'notes': notes or '',
            'stage': self.current_stage or '',
            'progress': self.progress_percentage or 0
        }
        
        self.append('status_timeline', timeline_entry)
        
    def send_notifications(self):
        """Send notifications to customer based on preferences"""
        if not self.is_new():
            old_doc = self.get_doc_before_save()
            
            # Check if status changed or significant progress made
            status_changed = old_doc and old_doc.status != self.status
            progress_increased = (old_doc and 
                               float(old_doc.progress_percentage or 0) < 
                               float(self.progress_percentage or 0))
            
            if status_changed or progress_increased:
                self.send_customer_notification()
                
    def send_customer_notification(self):
        """Send notification to customer"""
        try:
            customer_doc = frappe.get_doc('Customer', self.customer)
            notification_language = self.notification_language or 'English'
            
            # Prepare notification content
            if notification_language == 'Arabic':
                subject = f"تحديث حالة الخدمة - {self.name}"
                message = self.get_arabic_notification_message()
            else:
                subject = f"Service Update - {self.name}"
                message = self.get_english_notification_message()
                
            # Send SMS if enabled
            if self.sms_notifications and customer_doc.mobile_no:
                self.send_sms_notification(customer_doc.mobile_no, message)
                
            # Send email if enabled
            if self.email_notifications and customer_doc.email_id:
                self.send_email_notification(customer_doc.email_id, subject, message)
                
            # Update portal notification
            if self.portal_notifications:
                self.create_portal_notification(message)
                
            self.last_notification_sent = frappe.utils.now()
            
        except Exception as e:
            frappe.log_error(f"Failed to send notification: {str(e)}")
            
    def get_english_notification_message(self):
        """Get English notification message"""
        vehicle_info = ""
        if self.vehicle:
            vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
            vehicle_info = f" for {vehicle_doc.make} {vehicle_doc.model} ({vehicle_doc.license_plate})"
            
        return f"""
Dear Customer,

Your service{vehicle_info} has been updated:

Status: {self.status}
Current Stage: {self.current_stage}
Progress: {self.progress_percentage}%

{self.stage_description or ''}

Best regards,
{self.workshop}
        """.strip()
        
    def get_arabic_notification_message(self):
        """Get Arabic notification message"""
        vehicle_info = ""
        if self.vehicle:
            vehicle_doc = frappe.get_doc('Vehicle', self.vehicle)
            vehicle_info = f" للمركبة {vehicle_doc.make} {vehicle_doc.model} ({vehicle_doc.license_plate})"
            
        return f"""
عزيزي العميل،

تم تحديث حالة الخدمة{vehicle_info}:

الحالة: {self.get_arabic_status()}
المرحلة الحالية: {self.get_arabic_stage()}
نسبة الإنجاز: {self.progress_percentage}%

{self.stage_description_ar or ''}

مع أطيب التحيات،
{self.workshop}
        """.strip()
        
    def get_arabic_status(self):
        """Get Arabic translation of status"""
        status_translations = {
            'Received': 'مستلم',
            'In Progress': 'قيد التنفيذ',
            'Pending Parts': 'في انتظار القطع',
            'Quality Check': 'فحص الجودة',
            'Ready for Delivery': 'جاهز للتسليم',
            'Completed': 'مكتمل',
            'Cancelled': 'ملغى'
        }
        return status_translations.get(self.status, self.status)
        
    def get_arabic_stage(self):
        """Get Arabic translation of current stage"""
        stage_translations = {
            'Vehicle Received': 'استلام المركبة',
            'Diagnosis in Progress': 'التشخيص قيد التنفيذ',
            'Awaiting Customer Approval': 'في انتظار موافقة العميل',
            'Parts Ordered': 'طلب القطع',
            'Work in Progress': 'العمل قيد التنفيذ',
            'Quality Check': 'فحص الجودة',
            'Ready for Pickup': 'جاهز للاستلام',
            'Completed': 'مكتمل'
        }
        return stage_translations.get(self.current_stage, self.current_stage)
        
    def send_sms_notification(self, mobile_no, message):
        """Send SMS notification"""
        # Implementation depends on SMS provider
        frappe.log_error(f"SMS notification to {mobile_no}: {message}")
        
    def send_email_notification(self, email, subject, message):
        """Send email notification"""
        try:
            frappe.sendmail(
                recipients=[email],
                subject=subject,
                message=message,
                delayed=False
            )
        except Exception as e:
            frappe.log_error(f"Failed to send email to {email}: {str(e)}")
            
    def create_portal_notification(self, message):
        """Create portal notification for customer"""
        # This would integrate with customer portal notification system
        frappe.log_error(f"Portal notification: {message}")
        
    def update_customer_portal(self):
        """Update customer portal with latest information"""
        if self.customer_viewed:
            self.customer_viewed = 0  # Reset when updated
            
    @frappe.whitelist()
    def mark_as_viewed_by_customer(self):
        """Mark as viewed by customer"""
        self.customer_viewed = 1
        self.save(ignore_permissions=True)
        
    @frappe.whitelist()
    def update_stage(self, stage, description_en="", description_ar=""):
        """Update current stage and descriptions"""
        self.current_stage = stage
        if description_en:
            self.stage_description = description_en
        if description_ar:
            self.stage_description_ar = description_ar
            
        self.update_progress()
        self.save()
        
        return {
            'status': 'success',
            'message': _('Stage updated successfully'),
            'progress': self.progress_percentage
        }
        
    @frappe.whitelist()
    def get_real_time_status(self):
        """Get real-time status information for portal"""
        return {
            'name': self.name,
            'status': self.status,
            'current_stage': self.current_stage,
            'progress_percentage': self.progress_percentage,
            'estimated_completion': self.estimated_completion,
            'last_update': self.last_update,
            'stage_description': self.stage_description,
            'stage_description_ar': self.stage_description_ar,
            'total_cost': self.total_cost,
            'paid_amount': self.paid_amount,
            'balance_amount': self.balance_amount
        }

@frappe.whitelist()
def get_service_history_for_customer(customer, limit=10):
    """Get service history for customer portal"""
    try:
        history = frappe.get_list(
            'Service History Tracker',
            filters={
                'customer': customer,
                'is_active': 1
            },
            fields=[
                'name', 'service_date', 'vehicle', 'status', 'current_stage',
                'progress_percentage', 'total_cost', 'service_description',
                'service_description_ar', 'estimated_completion'
            ],
            order_by='service_date desc',
            limit=limit
        )
        
        # Enhance with vehicle information
        for record in history:
            if record.vehicle:
                vehicle = frappe.get_doc('Vehicle', record.vehicle)
                record.vehicle_info = f"{vehicle.make} {vehicle.model} ({vehicle.license_plate})"
                
        return {
            'status': 'success',
            'data': history
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching service history: {str(e)}")
        return {
            'status': 'error',
            'message': _('Failed to fetch service history')
        }

@frappe.whitelist()
def get_real_time_updates(tracking_ids):
    """Get real-time updates for multiple service tracking IDs"""
    try:
        if isinstance(tracking_ids, str):
            tracking_ids = json.loads(tracking_ids)
            
        updates = []
        for tracking_id in tracking_ids:
            doc = frappe.get_doc('Service History Tracker', tracking_id)
            updates.append(doc.get_real_time_status())
            
        return {
            'status': 'success',
            'data': updates,
            'timestamp': frappe.utils.now()
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching real-time updates: {str(e)}")
        return {
            'status': 'error',
            'message': _('Failed to fetch updates')
        }

@frappe.whitelist()
def submit_customer_feedback(tracking_id, rating, feedback_en="", feedback_ar="", recommend=False):
    """Submit customer feedback for service"""
    try:
        doc = frappe.get_doc('Service History Tracker', tracking_id)
        
        # Verify customer permission
        if doc.customer != frappe.session.user:
            customer_doc = frappe.get_doc('Customer', doc.customer)
            if customer_doc.email_id != frappe.session.user:
                return {
                    'status': 'error',
                    'message': _('Unauthorized access')
                }
                
        # Update feedback
        doc.satisfaction_rating = rating
        doc.customer_feedback = feedback_en
        doc.customer_feedback_ar = feedback_ar
        doc.would_recommend = recommend
        doc.feedback_date = frappe.utils.today()
        doc.save()
        
        return {
            'status': 'success',
            'message': _('Feedback submitted successfully')
        }
        
    except Exception as e:
        frappe.log_error(f"Error submitting feedback: {str(e)}")
        return {
            'status': 'error',
            'message': _('Failed to submit feedback')
        }

@frappe.whitelist()
def get_service_analytics_for_customer(customer, from_date=None, to_date=None):
    """Get service analytics for customer portal dashboard"""
    try:
        filters = {'customer': customer}
        
        if from_date:
            filters['service_date'] = ['>=', from_date]
        if to_date:
            if 'service_date' in filters:
                filters['service_date'] = ['between', [from_date, to_date]]
            else:
                filters['service_date'] = ['<=', to_date]
                
        # Get service statistics
        services = frappe.get_list(
            'Service History Tracker',
            filters=filters,
            fields=['status', 'total_cost', 'satisfaction_rating', 'service_type']
        )
        
        analytics = {
            'total_services': len(services),
            'total_spent': sum(float(s.total_cost or 0) for s in services),
            'average_rating': 0,
            'status_breakdown': {},
            'service_type_breakdown': {}
        }
        
        # Calculate averages and breakdowns
        if services:
            ratings = [float(s.satisfaction_rating or 0) for s in services if s.satisfaction_rating]
            if ratings:
                analytics['average_rating'] = sum(ratings) / len(ratings)
                
            # Status breakdown
            for service in services:
                status = service.status
                analytics['status_breakdown'][status] = analytics['status_breakdown'].get(status, 0) + 1
                
            # Service type breakdown
            for service in services:
                service_type = service.service_type or 'Other'
                analytics['service_type_breakdown'][service_type] = analytics['service_type_breakdown'].get(service_type, 0) + 1
                
        return {
            'status': 'success',
            'data': analytics
        }
        
    except Exception as e:
        frappe.log_error(f"Error fetching analytics: {str(e)}")
        return {
            'status': 'error',
            'message': _('Failed to fetch analytics')
        } 