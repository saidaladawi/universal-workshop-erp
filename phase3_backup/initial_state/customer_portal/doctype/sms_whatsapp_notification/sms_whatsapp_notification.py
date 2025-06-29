# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

import json
import re
import base64
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    cint, flt, get_datetime, now, today, add_days, 
    format_datetime, get_url, get_request_site_address
)


class SMSWhatsAppNotification(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate notification before saving"""
        self.validate_required_fields()
        self.validate_phone_numbers()
        self.validate_message_content()
        self.validate_scheduling()
        self.validate_compliance()
        
    def before_save(self):
        """Set default values before saving"""
        self.set_default_values()
        self.calculate_message_metrics()
        self.validate_twilio_config()
        
    def on_submit(self):
        """Actions when notification is submitted"""
        if self.send_immediately:
            self.send_notification()
        else:
            self.schedule_notification()
            
    def after_insert(self):
        """Actions after notification is created"""
        self.log_notification_creation()
        
    def validate_required_fields(self):
        """Validate required fields based on context"""
        if not self.notification_title:
            frappe.throw(_("Notification title (English) is required"))
            
        if not self.notification_title_ar:
            frappe.throw(_("Arabic notification title is required"))
            
        if not self.message_body:
            frappe.throw(_("Message body (English) is required"))
            
        if not self.message_body_ar:
            frappe.throw(_("Arabic message body is required"))
            
        if self.recipient_type == 'Individual' and not self.customer:
            frappe.throw(_("Customer is required for individual notifications"))
            
        if self.channel_type in ['SMS', 'Both'] and not self.phone_number:
            frappe.throw(_("Phone number is required for SMS notifications"))
            
        if self.channel_type in ['WhatsApp', 'Both'] and not self.whatsapp_number:
            frappe.throw(_("WhatsApp number is required for WhatsApp notifications"))
            
    def validate_phone_numbers(self):
        """Validate Oman phone number format"""
        if self.phone_number:
            if not self.phone_number.startswith('+968'):
                frappe.throw(_("Phone number must start with +968 for Oman"))
            if not re.match(r'^\+968\d{8}$', self.phone_number):
                frappe.throw(_("Invalid Oman phone number format. Should be +968XXXXXXXX"))
                
        if self.whatsapp_number:
            if not self.whatsapp_number.startswith('+968'):
                frappe.throw(_("WhatsApp number must start with +968 for Oman"))
            if not re.match(r'^\+968\d{8}$', self.whatsapp_number):
                frappe.throw(_("Invalid Oman WhatsApp number format. Should be +968XXXXXXXX"))
                
    def validate_message_content(self):
        """Validate message content and character limits"""
        # SMS character limit (Arabic uses more bytes)
        if self.channel_type in ['SMS', 'Both']:
            english_length = len(self.message_body)
            arabic_length = len(self.message_body_ar.encode('utf-8'))
            
            if english_length > 160:
                frappe.msgprint(_("English SMS message exceeds 160 characters"))
            if arabic_length > 70:  # Arabic SMS limit is lower
                frappe.msgprint(_("Arabic SMS message exceeds 70 characters"))
                
        # WhatsApp has higher limits but still validate
        if self.channel_type in ['WhatsApp', 'Both']:
            if len(self.message_body) > 4096:
                frappe.throw(_("WhatsApp message exceeds 4096 characters"))
            if len(self.message_body_ar) > 4096:
                frappe.throw(_("Arabic WhatsApp message exceeds 4096 characters"))
                
    def validate_scheduling(self):
        """Validate scheduling and delivery windows"""
        if not self.send_immediately and not self.scheduled_datetime:
            frappe.throw(_("Scheduled date/time is required for non-immediate delivery"))
            
        if self.scheduled_datetime:
            scheduled_time = get_datetime(self.scheduled_datetime)
            if scheduled_time <= get_datetime(now()):
                frappe.throw(_("Scheduled time must be in the future"))
                
        if self.delivery_window_start and self.delivery_window_end:
            if self.delivery_window_start >= self.delivery_window_end:
                frappe.throw(_("Delivery window start must be before end time"))
                
    def validate_compliance(self):
        """Validate compliance requirements"""
        if not self.opt_in_consent and self.notification_type != 'Emergency Alert':
            frappe.throw(_("Customer consent is required for non-emergency notifications"))
            
        if not self.privacy_consent:
            frappe.throw(_("Privacy consent is required"))
            
    def set_default_values(self):
        """Set default values for the notification"""
        if not self.notification_id:
            self.notification_id = frappe.generate_hash(length=8)
            
        if not self.created_by:
            self.created_by = frappe.session.user
            
        if not self.created_date:
            self.created_date = now()
            
        if not self.timezone:
            self.timezone = 'Asia/Muscat'
            
        if not self.billing_currency:
            self.billing_currency = 'OMR'
            
        if not self.max_attempts:
            self.max_attempts = 3
            
        if not self.retry_interval:
            self.retry_interval = 30
            
        # Set customer details from linked customer
        if self.customer:
            customer_doc = frappe.get_doc('Customer', self.customer)
            self.customer_name = customer_doc.customer_name
            if hasattr(customer_doc, 'customer_name_ar'):
                self.customer_name_ar = customer_doc.customer_name_ar
            if not self.phone_number and hasattr(customer_doc, 'mobile_no'):
                self.phone_number = customer_doc.mobile_no
            if not self.whatsapp_number and hasattr(customer_doc, 'mobile_no'):
                self.whatsapp_number = customer_doc.mobile_no
            if not self.email_address and customer_doc.email_id:
                self.email_address = customer_doc.email_id
                
    def calculate_message_metrics(self):
        """Calculate message size and character counts"""
        if self.message_body:
            self.character_count = len(self.message_body)
            
        # Calculate message size in bytes
        english_size = len(self.message_body.encode('utf-8')) if self.message_body else 0
        arabic_size = len(self.message_body_ar.encode('utf-8')) if self.message_body_ar else 0
        total_size = english_size + arabic_size
        
        if total_size < 1024:
            self.message_size = f"{total_size} bytes"
        else:
            self.message_size = f"{total_size/1024:.2f} KB"
            
    def validate_twilio_config(self):
        """Validate Twilio configuration"""
        # Get Twilio settings from Universal Workshop Settings
        settings = frappe.get_single('Universal Workshop Settings')
        
        if not hasattr(settings, 'twilio_account_sid') or not settings.twilio_account_sid:
            frappe.throw(_("Twilio Account SID not configured in Workshop Settings"))
            
        if not hasattr(settings, 'twilio_auth_token') or not settings.twilio_auth_token:
            frappe.throw(_("Twilio Auth Token not configured in Workshop Settings"))
            
        # Use settings from Universal Workshop Settings
        self.twilio_account_sid = settings.twilio_account_sid
        self.twilio_auth_token = settings.twilio_auth_token
        
        if hasattr(settings, 'twilio_phone_number'):
            self.twilio_phone_number = settings.twilio_phone_number
        if hasattr(settings, 'twilio_whatsapp_number'):
            self.twilio_whatsapp_number = settings.twilio_whatsapp_number
            
    def send_notification(self):
        """Send the notification immediately"""
        try:
            self.status = 'Sending'
            self.delivery_status = 'Queued'
            self.save()
            
            results = []
            
            # Send SMS if required
            if self.channel_type in ['SMS', 'Both']:
                sms_result = self.send_sms()
                results.append(sms_result)
                
            # Send WhatsApp if required
            if self.channel_type in ['WhatsApp', 'Both']:
                whatsapp_result = self.send_whatsapp()
                results.append(whatsapp_result)
                
            # Update status based on results
            self.process_send_results(results)
            
        except Exception as e:
            self.handle_send_error(str(e))
            
    def send_sms(self) -> Dict:
        """Send SMS via Twilio"""
        try:
            # Prepare message content
            message_content = self.prepare_message_content('sms')
            
            # Twilio SMS API call
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            
            auth_string = f"{self.twilio_account_sid}:{self.twilio_auth_token}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'From': self.twilio_phone_number,
                'To': self.phone_number,
                'Body': message_content,
                'StatusCallback': self.get_webhook_url()
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'channel': 'SMS',
                    'message_sid': result.get('sid'),
                    'status': result.get('status'),
                    'cost': self.calculate_sms_cost()
                }
            else:
                return {
                    'success': False,
                    'channel': 'SMS',
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'channel': 'SMS',
                'error': str(e)
            }
            
    def send_whatsapp(self) -> Dict:
        """Send WhatsApp message via Twilio"""
        try:
            # Prepare message content
            message_content = self.prepare_message_content('whatsapp')
            
            # Twilio WhatsApp API call
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            
            auth_string = f"{self.twilio_account_sid}:{self.twilio_auth_token}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_header}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'From': f"whatsapp:{self.twilio_whatsapp_number}",
                'To': f"whatsapp:{self.whatsapp_number}",
                'Body': message_content,
                'StatusCallback': self.get_webhook_url()
            }
            
            # Add media if present
            if self.media_attachment:
                data['MediaUrl'] = get_url() + self.media_attachment
                
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    'success': True,
                    'channel': 'WhatsApp',
                    'message_sid': result.get('sid'),
                    'status': result.get('status'),
                    'cost': self.calculate_whatsapp_cost()
                }
            else:
                return {
                    'success': False,
                    'channel': 'WhatsApp',
                    'error': response.text,
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'channel': 'WhatsApp',
                'error': str(e)
            }
            
    def prepare_message_content(self, channel: str) -> str:
        """Prepare message content with personalization"""
        # Determine language preference (assume Arabic first for Oman)
        use_arabic = True
        message_template = self.message_body_ar if use_arabic else self.message_body
        
        # Apply template variables if present
        if self.template_variables:
            try:
                variables = json.loads(self.template_variables)
                for key, value in variables.items():
                    message_template = message_template.replace(f"{{{{{key}}}}}", str(value))
            except (json.JSONDecodeError, TypeError):
                pass
                
        # Apply personalization data
        if self.personalization_data:
            try:
                personalization = json.loads(self.personalization_data)
                for key, value in personalization.items():
                    message_template = message_template.replace(f"{{{{{key}}}}}", str(value))
            except (json.JSONDecodeError, TypeError):
                pass
                
        # Add customer name if available
        if self.customer_name_ar and use_arabic:
            message_template = message_template.replace("{{customer_name}}", self.customer_name_ar)
        elif self.customer_name:
            message_template = message_template.replace("{{customer_name}}", self.customer_name)
            
        return message_template
        
    def get_webhook_url(self) -> str:
        """Get webhook URL for status callbacks"""
        if self.webhook_url:
            return self.webhook_url
        return f"{get_request_site_address()}/api/method/universal_workshop.api.twilio_webhook"
        
    def calculate_sms_cost(self) -> float:
        """Calculate SMS cost (Oman rates)"""
        # Typical SMS cost in Oman through Twilio
        base_cost = 0.0075  # USD per SMS
        
        # Convert to OMR (approximate rate 1 USD = 0.385 OMR)
        omr_cost = base_cost * 0.385
        return round(omr_cost, 4)
        
    def calculate_whatsapp_cost(self) -> float:
        """Calculate WhatsApp cost"""
        # WhatsApp Business API cost in Oman
        base_cost = 0.0042  # USD per message
        
        # Convert to OMR
        omr_cost = base_cost * 0.385
        return round(omr_cost, 4)
        
    def process_send_results(self, results: List[Dict]):
        """Process sending results and update status"""
        successful_sends = [r for r in results if r.get('success')]
        failed_sends = [r for r in results if not r.get('success')]
        
        if successful_sends and not failed_sends:
            self.status = 'Sent'
            self.delivery_status = 'Sent'
            self.sent_datetime = now()
            
            # Update costs
            total_cost = sum(r.get('cost', 0) for r in successful_sends)
            self.actual_cost = total_cost
            self.total_cost = total_cost
            
            # Store Twilio message SID
            if len(successful_sends) == 1:
                self.twilio_message_sid = successful_sends[0].get('message_sid')
                self.twilio_status = successful_sends[0].get('status')
                
        elif successful_sends and failed_sends:
            self.status = 'Partially Sent'
            self.delivery_status = 'Partially Sent'
            self.error_message = f"Failed channels: {[r['channel'] for r in failed_sends]}"
            
        else:
            self.status = 'Failed'
            self.delivery_status = 'Failed'
            error_messages = [r.get('error', 'Unknown error') for r in failed_sends]
            self.error_message = '; '.join(error_messages)
            
        self.delivery_attempts = (self.delivery_attempts or 0) + 1
        self.save()
        
        # Schedule retry if needed
        if failed_sends and self.delivery_attempts < self.max_attempts:
            self.schedule_retry()
            
    def handle_send_error(self, error_message: str):
        """Handle sending errors"""
        self.status = 'Failed'
        self.delivery_status = 'Failed'
        self.error_message = error_message
        self.delivery_attempts = (self.delivery_attempts or 0) + 1
        self.save()
        
        frappe.log_error(f"SMS/WhatsApp notification failed: {error_message}", "Notification Error")
        
    def schedule_notification(self):
        """Schedule notification for later delivery"""
        self.status = 'Scheduled'
        self.save()
        
        # Create background job for scheduled delivery
        frappe.enqueue(
            'universal_workshop.customer_portal.doctype.sms_whatsapp_notification.sms_whatsapp_notification.send_scheduled_notification',
            notification_id=self.name,
            at=get_datetime(self.scheduled_datetime),
            queue='default'
        )
        
    def schedule_retry(self):
        """Schedule retry for failed notification"""
        retry_time = datetime.now() + timedelta(minutes=self.retry_interval)
        
        frappe.enqueue(
            'universal_workshop.customer_portal.doctype.sms_whatsapp_notification.sms_whatsapp_notification.retry_notification',
            notification_id=self.name,
            at=retry_time,
            queue='default'
        )
        
    def log_notification_creation(self):
        """Log notification creation"""
        frappe.logger().info(f"SMS/WhatsApp notification created: {self.name} for customer {self.customer}")
        
    def update_delivery_status(self, twilio_status: str, timestamp: str = None):
        """Update delivery status from Twilio webhook"""
        status_mapping = {
            'queued': 'Queued',
            'failed': 'Failed',
            'sent': 'Sent',
            'received': 'Delivered',
            'delivered': 'Delivered',
            'undelivered': 'Undelivered',
            'read': 'Read'
        }
        
        self.delivery_status = status_mapping.get(twilio_status, twilio_status)
        self.twilio_status = twilio_status
        
        if timestamp:
            parsed_time = get_datetime(timestamp)
            
            if twilio_status in ['sent']:
                self.sent_datetime = parsed_time
            elif twilio_status in ['delivered', 'received']:
                self.delivered_datetime = parsed_time
            elif twilio_status in ['read']:
                self.read_datetime = parsed_time
                
        self.save()


# Utility functions for background jobs
@frappe.whitelist()
def send_scheduled_notification(notification_id: str):
    """Send scheduled notification (background job)"""
    try:
        notification = frappe.get_doc('SMS WhatsApp Notification', notification_id)
        if notification.status == 'Scheduled':
            notification.send_notification()
    except Exception as e:
        frappe.log_error(f"Failed to send scheduled notification {notification_id}: {e}")


@frappe.whitelist()
def retry_notification(notification_id: str):
    """Retry failed notification (background job)"""
    try:
        notification = frappe.get_doc('SMS WhatsApp Notification', notification_id)
        if notification.status == 'Failed' and notification.delivery_attempts < notification.max_attempts:
            notification.send_notification()
    except Exception as e:
        frappe.log_error(f"Failed to retry notification {notification_id}: {e}")


@frappe.whitelist()
def get_notification_templates(notification_type: str = None, language: str = 'en'):
    """Get predefined notification templates"""
    templates = {
        'Appointment Reminder': {
            'en': "Hello {{customer_name}}, this is a reminder for your appointment at {{workshop_name}} on {{appointment_date}} at {{appointment_time}}.",
            'ar': "مرحباً {{customer_name}}، هذا تذكير بموعدك في {{workshop_name}} في {{appointment_date}} في {{appointment_time}}."
        },
        'Service Update': {
            'en': "Hello {{customer_name}}, your vehicle service status has been updated to: {{status}}. Expected completion: {{completion_time}}.",
            'ar': "مرحباً {{customer_name}}، تم تحديث حالة خدمة مركبتك إلى: {{status}}. الإنجاز المتوقع: {{completion_time}}."
        },
        'Payment Confirmation': {
            'en': "Thank you {{customer_name}}! Payment of {{amount}} OMR received for invoice {{invoice_number}}.",
            'ar': "شكراً لك {{customer_name}}! تم استلام دفعة {{amount}} ريال عماني للفاتورة {{invoice_number}}."
        },
        'Feedback Request': {
            'en': "Hello {{customer_name}}, please share your feedback about our service. Rate us: {{feedback_link}}",
            'ar': "مرحباً {{customer_name}}، يرجى مشاركة تقييمك لخدمتنا. قيمنا: {{feedback_link}}"
        }
    }
    
    if notification_type:
        return templates.get(notification_type, {}).get(language, '')
    
    return templates


@frappe.whitelist()
def get_notification_analytics(date_range: str = '30', customer: str = None):
    """Get notification analytics and performance metrics"""
    from frappe.utils import add_days, today
    
    start_date = add_days(today(), -int(date_range))
    
    filters = {
        'created_date': ['>=', start_date],
        'docstatus': ['!=', 2]
    }
    
    if customer:
        filters['customer'] = customer
        
    notifications = frappe.get_list(
        'SMS WhatsApp Notification',
        filters=filters,
        fields=[
            'name', 'notification_type', 'channel_type', 'status',
            'delivery_status', 'created_date', 'sent_datetime',
            'delivered_datetime', 'actual_cost', 'engagement_score'
        ]
    )
    
    # Calculate analytics
    total_notifications = len(notifications)
    sent_notifications = len([n for n in notifications if n.status == 'Sent'])
    delivered_notifications = len([n for n in notifications if n.delivery_status == 'Delivered'])
    
    delivery_rate = (delivered_notifications / sent_notifications * 100) if sent_notifications > 0 else 0
    total_cost = sum(n.actual_cost or 0 for n in notifications)
    
    # Channel breakdown
    sms_count = len([n for n in notifications if n.channel_type in ['SMS', 'Both']])
    whatsapp_count = len([n for n in notifications if n.channel_type in ['WhatsApp', 'Both']])
    
    # Type breakdown
    type_breakdown = {}
    for notification in notifications:
        type_name = notification.notification_type
        if type_name not in type_breakdown:
            type_breakdown[type_name] = 0
        type_breakdown[type_name] += 1
        
    return {
        'summary': {
            'total_notifications': total_notifications,
            'sent_notifications': sent_notifications,
            'delivered_notifications': delivered_notifications,
            'delivery_rate': round(delivery_rate, 2),
            'total_cost': round(total_cost, 3),
            'date_range': f"{start_date} to {today()}"
        },
        'channel_breakdown': {
            'sms': sms_count,
            'whatsapp': whatsapp_count
        },
        'type_breakdown': type_breakdown,
        'recent_notifications': notifications[-10:] if notifications else []
    }


@frappe.whitelist()
def process_twilio_webhook(message_sid: str, message_status: str, timestamp: str = None):
    """Process Twilio status webhook"""
    try:
        # Find notification by Twilio message SID
        notifications = frappe.get_list(
            'SMS WhatsApp Notification',
            filters={'twilio_message_sid': message_sid},
            limit=1
        )
        
        if notifications:
            notification = frappe.get_doc('SMS WhatsApp Notification', notifications[0].name)
            notification.update_delivery_status(message_status, timestamp)
            
            return {'status': 'success', 'message': 'Status updated'}
        else:
            return {'status': 'error', 'message': 'Notification not found'}
            
    except Exception as e:
        frappe.log_error(f"Twilio webhook processing failed: {e}")
        return {'status': 'error', 'message': str(e)}


@frappe.whitelist()
def send_bulk_notification(recipients: List[str], notification_data: Dict):
    """Send bulk notifications to multiple recipients"""
    try:
        results = []
        
        for recipient in recipients:
            # Create individual notification
            notification = frappe.new_doc('SMS WhatsApp Notification')
            notification.update(notification_data)
            notification.customer = recipient
            notification.recipient_type = 'Individual'
            notification.insert()
            
            if notification.send_immediately:
                notification.send_notification()
                
            results.append({
                'recipient': recipient,
                'notification_id': notification.name,
                'status': notification.status
            })
            
        return {
            'status': 'success',
            'total_sent': len(results),
            'results': results
        }
        
    except Exception as e:
        frappe.log_error(f"Bulk notification failed: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
