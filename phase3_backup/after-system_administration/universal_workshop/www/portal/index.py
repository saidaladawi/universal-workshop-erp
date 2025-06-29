# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Main Page Controller
Handles routing and authentication for customer portal
"""

import frappe
from frappe import _
from universal_workshop.customer_portal.auth import get_current_customer

def get_context(context):
    """
    Get context for portal main page
    
    Args:
        context: Frappe page context
        
    Returns:
        dict: Page context with customer data
    """
    # Check if customer is authenticated
    customer = get_current_customer()
    
    if not customer:
        # Redirect to login page if not authenticated
        frappe.local.flags.redirect_location = '/portal/login'
        raise frappe.Redirect
    
    # Get customer details and dashboard data
    customer_data = _get_customer_dashboard_data(customer['customer_id'])
    
    context.update({
        'customer': customer,
        'customer_data': customer_data,
        'page_title': _('Customer Portal'),
        'page_title_ar': 'بوابة العملاء',
        'show_sidebar': True,
        'portal_language': frappe.local.lang,
        'is_rtl': frappe.local.lang == 'ar'
    })
    
    return context

def _get_customer_dashboard_data(customer_id):
    """
    Get dashboard data for customer
    
    Args:
        customer_id: Customer ID
        
    Returns:
        dict: Dashboard data including vehicles, appointments, invoices
    """
    try:
        # Get customer vehicles
        vehicles = frappe.get_list(
            'Vehicle Profile',
            filters={'customer': customer_id},
            fields=['name', 'license_plate', 'make', 'model', 'year', 'vehicle_type'],
            limit=5,
            order_by='creation desc'
        )
        
        # Get recent appointments
        appointments = frappe.get_list(
            'Service Appointment',
            filters={'customer': customer_id},
            fields=[
                'name', 'appointment_date', 'appointment_time', 
                'service_type', 'status', 'vehicle'
            ],
            limit=5,
            order_by='appointment_date desc'
        )
        
        # Get recent invoices
        invoices = frappe.get_list(
            'Sales Invoice',
            filters={'customer': customer_id, 'docstatus': 1},
            fields=[
                'name', 'posting_date', 'grand_total', 'outstanding_amount',
                'status', 'due_date'
            ],
            limit=5,
            order_by='posting_date desc'
        )
        
        # Get pending quotations
        quotations = frappe.get_list(
            'Quotation',
            filters={'party_name': customer_id, 'status': 'Open'},
            fields=[
                'name', 'transaction_date', 'grand_total', 'valid_till',
                'quotation_to'
            ],
            limit=3,
            order_by='transaction_date desc'
        )
        
        # Calculate summary statistics
        total_vehicles = len(vehicles)
        pending_appointments = len([a for a in appointments if a.status in ['Scheduled', 'Confirmed']])
        outstanding_amount = sum([inv.outstanding_amount or 0 for inv in invoices])
        pending_quotations = len(quotations)
        
        return {
            'vehicles': vehicles,
            'appointments': appointments,
            'invoices': invoices,
            'quotations': quotations,
            'summary': {
                'total_vehicles': total_vehicles,
                'pending_appointments': pending_appointments,
                'outstanding_amount': outstanding_amount,
                'pending_quotations': pending_quotations
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting customer dashboard data: {str(e)}", "Customer Portal")
        return {
            'vehicles': [],
            'appointments': [],
            'invoices': [],
            'quotations': [],
            'summary': {
                'total_vehicles': 0,
                'pending_appointments': 0,
                'outstanding_amount': 0,
                'pending_quotations': 0
            }
        } 