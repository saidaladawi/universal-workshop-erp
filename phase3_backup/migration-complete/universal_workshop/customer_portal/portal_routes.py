# Universal Workshop Customer Portal Routes
# URL routing and page configuration for Arabic-first customer portal

import frappe
from frappe import _
from frappe.website.utils import get_home_page

def setup_portal_routes():
    """Setup comprehensive portal routes for Universal Workshop customer portal"""
    
    portal_routes = {
        # Main portal pages
        'portal': {
            'title': _('Customer Portal'),
            'title_ar': 'بوابة العملاء',
            'template': 'customer_portal/dashboard.html',
            'controller': 'universal_workshop.customer_portal.pages.dashboard',
            'requires_auth': True,
            'mobile_optimized': True,
            'rtl_support': True
        },
        
        # Dashboard
        'portal/dashboard': {
            'title': _('Dashboard'),
            'title_ar': 'لوحة التحكم',
            'template': 'customer_portal/dashboard.html',
            'controller': 'universal_workshop.customer_portal.pages.dashboard',
            'requires_auth': True,
            'mobile_optimized': True
        },
        
        # Appointment booking
        'portal/book-appointment': {
            'title': _('Book Appointment'),
            'title_ar': 'حجز موعد',
            'template': 'customer_portal/book_appointment.html',
            'controller': 'universal_workshop.customer_portal.pages.book_appointment',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['calendar', 'time_picker', 'service_selection']
        },
        
        'portal/appointments': {
            'title': _('My Appointments'),
            'title_ar': 'مواعيدي',
            'template': 'customer_portal/appointments.html',
            'controller': 'universal_workshop.customer_portal.pages.appointments',
            'requires_auth': True,
            'mobile_optimized': True
        },
        
        # Service management
        'portal/services': {
            'title': _('My Services'),
            'title_ar': 'خدماتي',
            'template': 'customer_portal/services.html',
            'controller': 'universal_workshop.customer_portal.pages.services',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['real_time_tracking', 'photo_upload', 'progress_timeline']
        },
        
        'portal/track-service': {
            'title': _('Track Service'),
            'title_ar': 'تتبع الخدمة',
            'template': 'customer_portal/track_service.html',
            'controller': 'universal_workshop.customer_portal.pages.track_service',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['real_time_updates', 'live_chat', 'photo_gallery']
        },
        
        'portal/history': {
            'title': _('Service History'),
            'title_ar': 'تاريخ الخدمات',
            'template': 'customer_portal/service_history.html',
            'controller': 'universal_workshop.customer_portal.pages.service_history',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['search', 'filter', 'export']
        },
        
        # Payment management
        'portal/payments': {
            'title': _('Payments'),
            'title_ar': 'المدفوعات',
            'template': 'customer_portal/payments.html',
            'controller': 'universal_workshop.customer_portal.pages.payments',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['online_payment', 'payment_history', 'receipts']
        },
        
        'portal/pay-invoice': {
            'title': _('Pay Invoice'),
            'title_ar': 'دفع الفاتورة',
            'template': 'customer_portal/pay_invoice.html',
            'controller': 'universal_workshop.customer_portal.pages.pay_invoice',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['payment_gateway', 'secure_checkout', 'receipt_generation']
        },
        
        # Document management
        'portal/documents': {
            'title': _('My Documents'),
            'title_ar': 'مستنداتي',
            'template': 'customer_portal/documents.html',
            'controller': 'universal_workshop.customer_portal.pages.documents',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['upload', 'download', 'preview', 'search']
        },
        
        # Profile management
        'portal/profile': {
            'title': _('My Profile'),
            'title_ar': 'ملفي الشخصي',
            'template': 'customer_portal/profile.html',
            'controller': 'universal_workshop.customer_portal.pages.profile',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['edit_profile', 'vehicle_management', 'preferences']
        },
        
        'portal/vehicles': {
            'title': _('My Vehicles'),
            'title_ar': 'مركباتي',
            'template': 'customer_portal/vehicles.html',
            'controller': 'universal_workshop.customer_portal.pages.vehicles',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['add_vehicle', 'edit_vehicle', 'service_history']
        },
        
        # Support and feedback
        'portal/support': {
            'title': _('Support'),
            'title_ar': 'الدعم',
            'template': 'customer_portal/support.html',
            'controller': 'universal_workshop.customer_portal.pages.support',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['live_chat', 'ticket_system', 'faq']
        },
        
        'portal/feedback': {
            'title': _('Feedback'),
            'title_ar': 'التقييم',
            'template': 'customer_portal/feedback.html',
            'controller': 'universal_workshop.customer_portal.pages.feedback',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['rating_system', 'comments', 'photo_upload']
        },
        
        # Notifications
        'portal/notifications': {
            'title': _('Notifications'),
            'title_ar': 'الإشعارات',
            'template': 'customer_portal/notifications.html',
            'controller': 'universal_workshop.customer_portal.pages.notifications',
            'requires_auth': True,
            'mobile_optimized': True,
            'features': ['push_notifications', 'email_settings', 'sms_settings']
        },
        
        # API endpoints
        'api/portal/dashboard-data': {
            'controller': 'universal_workshop.customer_portal.api.dashboard.get_dashboard_data',
            'method': 'GET',
            'requires_auth': True,
            'rate_limit': '100/hour'
        },
        
        'api/portal/appointments': {
            'controller': 'universal_workshop.customer_portal.api.appointments',
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'requires_auth': True,
            'rate_limit': '50/hour'
        },
        
        'api/portal/services': {
            'controller': 'universal_workshop.customer_portal.api.services',
            'methods': ['GET'],
            'requires_auth': True,
            'rate_limit': '100/hour'
        },
        
        'api/portal/payments': {
            'controller': 'universal_workshop.customer_portal.api.payments',
            'methods': ['GET', 'POST'],
            'requires_auth': True,
            'rate_limit': '20/hour'
        },
        
        'api/portal/documents': {
            'controller': 'universal_workshop.customer_portal.api.documents',
            'methods': ['GET', 'POST', 'DELETE'],
            'requires_auth': True,
            'rate_limit': '30/hour'
        },
        
        'api/portal/notifications': {
            'controller': 'universal_workshop.customer_portal.api.notifications',
            'methods': ['GET', 'POST', 'PUT'],
            'requires_auth': True,
            'rate_limit': '200/hour'
        }
    }
    
    return portal_routes

def get_portal_context(route_name: str) -> dict:
    """Get context data for portal pages"""
    from .portal_framework import CustomerPortalFramework
    
    portal = CustomerPortalFramework()
    routes = setup_portal_routes()
    
    if route_name not in routes:
        return {}
    
    route_config = routes[route_name]
    
    base_context = {
        'portal_title': _('Universal Workshop'),
        'portal_title_ar': 'ورشة يونيفرسال',
        'page_title': route_config.get('title', ''),
        'page_title_ar': route_config.get('title_ar', ''),
        'navigation': portal.get_portal_navigation(),
        'mobile_config': portal.get_mobile_layout_config(),
        'portal_settings': portal.get_portal_settings(),
        'user_access': portal.validate_portal_access(frappe.session.user),
        'current_route': route_name,
        'arabic_support': True,
        'rtl_layout': True,
        'mobile_optimized': route_config.get('mobile_optimized', True),
        'features': route_config.get('features', [])
    }
    
    return base_context

def register_portal_routes():
    """Register all portal routes with Frappe"""
    routes = setup_portal_routes()
    
    # Register routes with Frappe website
    for route_path, route_config in routes.items():
        if not route_path.startswith('api/'):
            # Register page routes
            frappe.website.router.register_route(
                route_path,
                route_config.get('controller'),
                {
                    'template': route_config.get('template'),
                    'title': route_config.get('title'),
                    'requires_auth': route_config.get('requires_auth', False),
                    'mobile_optimized': route_config.get('mobile_optimized', False)
                }
            )
        else:
            # Register API routes
            frappe.api.register_endpoint(
                route_path,
                route_config.get('controller'),
                {
                    'methods': route_config.get('methods', ['GET']),
                    'requires_auth': route_config.get('requires_auth', True),
                    'rate_limit': route_config.get('rate_limit', '100/hour')
                }
            )

# Route helper functions
@frappe.whitelist(allow_guest=True)
def get_available_routes():
    """Get list of available portal routes"""
    routes = setup_portal_routes()
    
    # Filter out API routes for frontend navigation
    page_routes = {
        path: config for path, config in routes.items() 
        if not path.startswith('api/')
    }
    
    return page_routes

@frappe.whitelist()
def get_route_context(route_name):
    """Get context data for specific route"""
    return get_portal_context(route_name)

@frappe.whitelist(allow_guest=True)
def check_route_access(route_name):
    """Check if current user has access to specific route"""
    routes = setup_portal_routes()
    
    if route_name not in routes:
        return {
            'access': False,
            'reason': 'route_not_found'
        }
    
    route_config = routes[route_name]
    
    # Check authentication requirement
    if route_config.get('requires_auth', False):
        if frappe.session.user == 'Guest':
            return {
                'access': False,
                'reason': 'authentication_required',
                'redirect': '/login'
            }
        
        # Validate portal access
        from .portal_framework import CustomerPortalFramework
        portal = CustomerPortalFramework()
        access_result = portal.validate_portal_access(frappe.session.user)
        
        if not access_result.get('access_granted', False):
            return {
                'access': False,
                'reason': access_result.get('reason', 'access_denied'),
                'message': access_result.get('message', _('Access denied'))
            }
    
    return {
        'access': True,
        'route_config': route_config
    } 