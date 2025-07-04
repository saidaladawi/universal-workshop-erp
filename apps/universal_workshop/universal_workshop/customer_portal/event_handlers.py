# -*- coding: utf-8 -*-
"""
Customer Portal Event Handlers
Handles ERPNext document events to trigger customer portal notifications
"""

import frappe
from frappe import _


def handle_appointment_confirmation(doc, method=None):
    """Handle Service Appointment after_insert event"""
    try:
        from universal_workshop.customer_portal.communication_integration import send_booking_confirmation
        
        # Send confirmation notification
        result = send_booking_confirmation(doc.name)
        
        if result.get("error"):
            frappe.log_error(f"Portal booking confirmation failed: {result['error']}", "Customer Portal Events")
        else:
            frappe.logger().info(f"Portal booking confirmation sent for {doc.name}")
            
    except Exception as e:
        frappe.log_error(f"Error in appointment confirmation handler: {str(e)}", "Customer Portal Events")


def handle_appointment_cancellation(doc, method=None):
    """Handle Service Appointment on_cancel event"""
    try:
        from universal_workshop.customer_portal.communication_integration import send_cancellation_notice
        
        # Send cancellation notification
        cancellation_reason = getattr(doc, 'cancellation_reason', '') or _("Appointment cancelled")
        result = send_cancellation_notice(doc.name, cancellation_reason)
        
        if result.get("error"):
            frappe.log_error(f"Portal cancellation notice failed: {result['error']}", "Customer Portal Events")
        else:
            frappe.logger().info(f"Portal cancellation notice sent for {doc.name}")
            
    except Exception as e:
        frappe.log_error(f"Error in appointment cancellation handler: {str(e)}", "Customer Portal Events")


def handle_service_status_update(doc, method=None):
    """Handle Work Order on_update event"""
    try:
        # Check if status actually changed
        if hasattr(doc, '_doc_before_save'):
            old_status = getattr(doc._doc_before_save, 'status', '')
            new_status = doc.status
            
            if old_status != new_status and new_status:
                from universal_workshop.customer_portal.communication_integration import send_service_status_update
                
                # Send status update notification
                result = send_service_status_update(doc.name, new_status)
                
                if result.get("error"):
                    frappe.log_error(f"Portal status update failed: {result['error']}", "Customer Portal Events")
                else:
                    frappe.logger().info(f"Portal status update sent for {doc.name}: {new_status}")
                    
    except Exception as e:
        frappe.log_error(f"Error in service status update handler: {str(e)}", "Customer Portal Events")


def handle_parts_approval_request(doc, method=None):
    """Handle Parts Usage after_insert event"""
    try:
        # Check if parts require customer approval and has service appointment
        if getattr(doc, 'service_appointment', None):
            from universal_workshop.customer_portal.communication_integration import send_parts_approval_request
            
            # Send parts approval request
            result = send_parts_approval_request(doc.name)
            
            if result.get("error"):
                frappe.log_error(f"Portal parts approval request failed: {result['error']}", "Customer Portal Events")
            else:
                frappe.logger().info(f"Portal parts approval request sent for {doc.name}")
                
    except Exception as e:
        frappe.log_error(f"Error in parts approval request handler: {str(e)}", "Customer Portal Events")
