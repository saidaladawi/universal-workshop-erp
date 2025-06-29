# -*- coding: utf-8 -*-
# pylint: disable=no-member
"""
Customer Portal Login Page Controller
"""

import frappe
from frappe import _
from universal_workshop.customer_portal.auth import get_current_customer

def get_context(context):
    """
    Get context for portal login page
    
    Args:
        context: Frappe page context
        
    Returns:
        dict: Page context
    """
    # Check if customer is already authenticated
    customer = get_current_customer()
    
    if customer:
        # Redirect to dashboard if already logged in
        frappe.local.flags.redirect_location = '/portal'
        raise frappe.Redirect
    
    context.update({
        'page_title': _('Customer Login'),
        'page_title_ar': 'تسجيل دخول العملاء',
        'portal_language': frappe.local.lang,
        'is_rtl': frappe.local.lang == 'ar',
        'show_sidebar': False
    })
    
    return context 