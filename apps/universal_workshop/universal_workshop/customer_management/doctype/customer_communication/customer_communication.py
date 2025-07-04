# -*- coding: utf-8 -*-
# Copyright (c) 2024, Universal Workshop and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, add_to_date
import json
import requests
from typing import Dict, Any, Optional


class CustomerCommunication(Document):
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields
    
    def validate(self):
        """Validate communication data before saving"""
        self.validate_communication_method()
        self.validate_bilingual_content()
        self.validate_contact_information()
        self.set_default_values()
        
    def before_submit(self):
        """Process communication before submitting"""
        if self.status == "Draft":
            self.send_communication()
            
    def validate_communication_method(self):
        """Validate communication method and required fields"""
        if self.communication_method == "SMS" and not self.phone_number:
            frappe.throw(_("Phone number is required for SMS communication"))
            
        if self.communication_method == "WhatsApp" and not self.phone_number:
            frappe.throw(_("Phone number is required for WhatsApp communication"))
            
        if self.communication_method == "Email" and not self.email_address:
            frappe.throw(_("Email address is required for email communication"))
            
        # Validate Oman phone number format
        if self.phone_number and not self.phone_number.startswith('+968'):
            frappe.throw(_("Phone number must be in Oman format (+968 XXXXXXXX)"))
            
    def validate_bilingual_content(self):
        """Ensure Arabic content is provided for Arabic-speaking customers"""
        customer_doc = frappe.get_doc("Customer", self.customer)
        
        # Check if customer prefers Arabic
        customer_language = getattr(customer_doc, 'preferred_language', 'en')
        if customer_language == 'ar' and not self.message_ar:
            frappe.msgprint(_("Consider adding Arabic message for better customer experience"))
            
    def validate_contact_information(self):
        """Auto-fetch contact information from customer if not provided"""
        if not self.phone_number or not self.email_address:
            customer_doc = frappe.get_doc("Customer", self.customer)
            
            if not self.phone_number:
                self.phone_number = getattr(customer_doc, 'mobile_no', '') or getattr(customer_doc, 'phone', '')
                
            if not self.email_address:
                self.email_address = getattr(customer_doc, 'email_id', '')
                
    def set_default_values(self):
        """Set default values for communication"""
        if not self.sent_date and self.status in ["Sent", "Delivered"]:
            self.sent_date = now_datetime()
            
        if not self.delivery_timestamp and self.delivery_status == "Delivered":
            self.delivery_timestamp = now_datetime()
            
    def send_communication(self):
        """Send communication based on method"""
        try:
            if self.communication_method == "SMS":
                self.send_sms()
            elif self.communication_method == "WhatsApp":
                self.send_whatsapp()
            elif self.communication_method == "Email":
                self.send_email()
            elif self.communication_method == "Push Notification":
                self.send_push_notification()
                
            self.status = "Sent"
            self.sent_date = now_datetime()
            
        except Exception as e:
            self.status = "Failed"
            frappe.log_error(f"Communication failed: {str(e)}", "Customer Communication Error")
            frappe.throw(_("Failed to send communication: {0}").format(str(e)))
            
    def send_sms(self):
        """Send SMS using Oman SMS gateway"""
        message_text = self.get_localized_message()
        
        # Use Oman SMS gateway (Omantel/Ooredoo)
        sms_settings = frappe.get_single("SMS Settings")
        
        if not sms_settings.sms_gateway_url:
            frappe.throw(_("SMS gateway not configured"))
            
        payload = {
            "to": self.phone_number,
            "message": message_text,
            "from": sms_settings.sender_name or "Workshop"
        }
        
        response = self._send_to_gateway(sms_settings.sms_gateway_url, payload, sms_settings.api_key)
        
        if response.get("success"):
            self.message_id = response.get("message_id")
            self.delivery_status = "Sent"
            self.cost = response.get("cost", 0.010)  # 10 baisa typical SMS cost in Oman
        else:
            raise Exception(response.get("error", "SMS sending failed"))
            
    def send_whatsapp(self):
        """Send WhatsApp message using Business API"""
        message_text = self.get_localized_message()
        
        whatsapp_settings = frappe.get_single("WhatsApp Settings")
        
        if not whatsapp_settings.business_api_url:
            frappe.throw(_("WhatsApp Business API not configured"))
            
        payload = {
            "messaging_product": "whatsapp",
            "to": self.phone_number.replace('+', ''),
            "type": "text",
            "text": {
                "body": message_text
            }
        }
        
        headers = {
            "Authorization": f"Bearer {whatsapp_settings.access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            whatsapp_settings.business_api_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            self.message_id = result.get("messages", [{}])[0].get("id")
            self.delivery_status = "Sent"
            self.cost = 0.020  # 20 baisa typical WhatsApp cost in Oman
        else:
            raise Exception(f"WhatsApp sending failed: {response.text}")
            
    def send_email(self):
        """Send email with Arabic support"""
        message_content = self.get_localized_message()
        
        frappe.sendmail(
            recipients=[self.email_address],
            subject=self.subject or _("Communication from Workshop"),
            message=message_content,
            sender=frappe.session.user,
            communication=self.name
        )
        
        self.delivery_status = "Sent"
        self.cost = 0.005  # 5 baisa typical email cost
        
    def send_push_notification(self):
        """Send push notification through mobile app"""
        # Integration with mobile app push service
        push_settings = frappe.get_single("Push Notification Settings")
        
        if not push_settings.firebase_server_key:
            frappe.throw(_("Push notification service not configured"))
            
        # Get customer's device tokens
        device_tokens = self.get_customer_device_tokens()
        
        if not device_tokens:
            frappe.throw(_("No device tokens found for customer"))
            
        for token in device_tokens:
            self._send_push_to_device(token, push_settings.firebase_server_key)
            
        self.delivery_status = "Sent"
        self.cost = 0.001  # 1 baisa typical push notification cost
        
    def get_localized_message(self) -> str:
        """Get message in appropriate language"""
        customer_doc = frappe.get_doc("Customer", self.customer)
        customer_language = getattr(customer_doc, 'preferred_language', 'en')
        
        if customer_language == 'ar' and self.message_ar:
            return self.message_ar
        else:
            return self.message
            
    def get_customer_device_tokens(self) -> list:
        """Get device tokens for push notifications"""
        # Query customer's registered devices
        tokens = frappe.db.sql("""
            SELECT device_token 
            FROM `tabCustomer Device` 
            WHERE customer = %s AND is_active = 1
        """, [self.customer], as_list=True)
        
        return [token[0] for token in tokens if token[0]]
        
    def _send_to_gateway(self, url: str, payload: dict, api_key: str) -> dict:
        """Send request to SMS gateway"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}
            
    def _send_push_to_device(self, device_token: str, server_key: str):
        """Send push notification to specific device"""
        firebase_url = "https://fcm.googleapis.com/fcm/send"
        
        headers = {
            "Authorization": f"key={server_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": device_token,
            "notification": {
                "title": self.subject or _("Workshop Notification"),
                "body": self.get_localized_message()[:100] + "..." if len(self.get_localized_message()) > 100 else self.get_localized_message(),
                "icon": "ic_notification"
            },
            "data": {
                "type": self.communication_type,
                "communication_id": self.name,
                "customer": self.customer
            }
        }
        
        response = requests.post(firebase_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            frappe.log_error(f"Push notification failed: {response.text}", "Push Notification Error")
            
    def schedule_follow_up(self, days: int = 7):
        """Schedule automatic follow-up communication"""
        if self.follow_up_required:
            follow_up_date = add_to_date(self.sent_date, days=days)
            
            follow_up_comm = frappe.new_doc("Customer Communication")
            follow_up_comm.update({
                "customer": self.customer,
                "communication_type": "Follow-up",
                "communication_method": self.communication_method,
                "phone_number": self.phone_number,
                "email_address": self.email_address,
                "subject": f"Follow-up: {self.subject}",
                "message": _("Following up on our previous communication regarding {0}").format(self.subject),
                "message_ar": _("متابعة بخصوص رسالتنا السابقة حول {0}").format(self.subject),
                "scheduled_date": follow_up_date,
                "status": "Scheduled",
                "automation_trigger": f"follow_up_{self.name}"
            })
            follow_up_comm.insert()
            
    def mark_as_read(self):
        """Mark communication as read by customer"""
        self.delivery_status = "Read"
        self.response_received = True
        self.save()
        
    def record_customer_response(self, response_text: str, rating: int = None):
        """Record customer response to communication"""
        self.customer_response = response_text
        self.response_timestamp = now_datetime()
        self.response_received = True
        
        if rating:
            self.satisfaction_rating = rating
            
        self.save()


# Whitelisted API methods
@frappe.whitelist()
def send_bulk_communication(customers: list, communication_data: dict):
    """Send bulk communication to multiple customers"""
    results = []
    
    for customer_id in customers:
        try:
            comm = frappe.new_doc("Customer Communication")
            comm.update(communication_data)
            comm.customer = customer_id
            comm.insert()
            comm.submit()
            
            results.append({
                "customer": customer_id,
                "status": "success",
                "communication_id": comm.name
            })
            
        except Exception as e:
            results.append({
                "customer": customer_id,
                "status": "failed",
                "error": str(e)
            })
            
    return results


@frappe.whitelist()
def get_communication_analytics(from_date: str, to_date: str):
    """Get communication analytics for reporting"""
    
    query = """
        SELECT 
            communication_method,
            communication_type,
            delivery_status,
            COUNT(*) as count,
            SUM(cost) as total_cost,
            AVG(satisfaction_rating) as avg_rating
        FROM `tabCustomer Communication`
        WHERE sent_date BETWEEN %s AND %s
        AND docstatus = 1
        GROUP BY communication_method, communication_type, delivery_status
        ORDER BY communication_method, count DESC
    """
    
    return frappe.db.sql(query, [from_date, to_date], as_dict=True)


@frappe.whitelist()
def mark_communication_read(communication_id: str):
    """Mark communication as read (called from customer portal/mobile app)"""
    comm = frappe.get_doc("Customer Communication", communication_id)
    comm.mark_as_read()
    return {"status": "success", "message": _("Communication marked as read")}


@frappe.whitelist()
def get_customer_communication_history(customer: str, limit: int = 50):
    """Get communication history for a customer"""
    
    communications = frappe.get_list(
        "Customer Communication",
        filters={"customer": customer, "docstatus": 1},
        fields=[
            "name", "communication_type", "subject", "communication_method",
            "sent_date", "delivery_status", "response_received", "satisfaction_rating"
        ],
        order_by="sent_date desc",
        limit=limit
    )
    
    return communications


@frappe.whitelist()
def schedule_service_reminder(customer: str, service_date: str, service_type: str):
    """Schedule automated service reminder communication"""
    
    # Schedule reminder 3 days before service
    reminder_date = add_to_date(service_date, days=-3)
    
    comm = frappe.new_doc("Customer Communication")
    comm.update({
        "customer": customer,
        "communication_type": "Service Reminder",
        "communication_method": "SMS",  # Default to SMS for reminders
        "subject": _("Service Reminder"),
        "message": _("Reminder: Your {0} service is scheduled for {1}. Please confirm your appointment.").format(service_type, service_date),
        "message_ar": _("تذكير: خدمة {0} مجدولة في {1}. يرجى تأكيد موعدك.").format(service_type, service_date),
        "scheduled_date": reminder_date,
        "status": "Scheduled",
        "automation_trigger": f"service_reminder_{service_date}",
        "follow_up_required": True
    })
    comm.insert()
    
    return {"status": "success", "communication_id": comm.name} 