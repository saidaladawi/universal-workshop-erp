# Universal Workshop Customer Portal Framework
# Arabic-first customer service portal with comprehensive features

import frappe
from frappe import _
from frappe.utils import today, get_datetime, cint, flt
from frappe.website.utils import is_signup_disabled
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Any


class CustomerPortalFramework:
    """
    Comprehensive framework for Universal Workshop customer portal
    Features Arabic-first design, mobile optimization, and full ERPNext v15 integration
    """

    def __init__(self):
        """Initialize portal framework with default settings"""
        self.portal_settings = self.get_portal_settings()
        self.arabic_support = True
        self.mobile_optimized = True
        self.default_language = "ar"

    def get_portal_settings(self) -> Dict[str, Any]:
        """Get comprehensive portal configuration settings"""
        settings = frappe.get_single("Universal Workshop Settings")

        return {
            "portal_enabled": getattr(settings, "portal_enabled", 1),
            "arabic_first": getattr(settings, "arabic_first", 1),
            "mobile_optimized": getattr(settings, "mobile_optimized", 1),
            "rtl_layout": getattr(settings, "rtl_layout", 1),
            "default_language": getattr(settings, "default_portal_language", "ar"),
            "appointment_booking": getattr(settings, "enable_appointment_booking", 1),
            "online_payments": getattr(settings, "enable_online_payments", 1),
            "document_access": getattr(settings, "enable_document_access", 1),
            "feedback_system": getattr(settings, "enable_feedback_system", 1),
            "whatsapp_notifications": getattr(settings, "enable_whatsapp_notifications", 1),
            "sms_notifications": getattr(settings, "enable_sms_notifications", 1),
            "portal_theme": getattr(settings, "portal_theme", "workshop_theme"),
            "max_file_size": getattr(settings, "max_upload_size", 5),  # MB
            "session_timeout": getattr(settings, "portal_session_timeout", 30),  # minutes
        }

    def initialize_portal_structure(self) -> Dict[str, Any]:
        """Initialize complete portal directory structure and configuration"""
        try:
            portal_structure = {
                "base_path": frappe.get_app_path("universal_workshop", "www"),
                "templates_path": frappe.get_app_path(
                    "universal_workshop", "templates", "customer_portal"
                ),
                "static_path": frappe.get_app_path("universal_workshop", "public", "portal"),
                "api_path": frappe.get_app_path("universal_workshop", "customer_portal", "api"),
            }

            # Create directory structure if it doesn't exist
            for path_type, path in portal_structure.items():
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)

            # Initialize portal configuration files
            self._create_portal_config()
            self._setup_arabic_translations()
            self._create_mobile_manifest()

            return {
                "success": True,
                "structure": portal_structure,
                "arabic_support": self.arabic_support,
                "mobile_optimized": self.mobile_optimized,
                "message": _("Portal structure initialized successfully"),
            }

        except Exception as e:
            frappe.log_error(f"Portal structure initialization failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": _("Portal structure initialization failed"),
            }

    def _create_portal_config(self):
        """Create portal configuration files"""
        config = {
            "portal_name": _("Universal Workshop Customer Portal"),
            "portal_name_ar": "بوابة عملاء ورشة يونيفرسال",
            "version": "1.0.0",
            "arabic_first": True,
            "mobile_optimized": True,
            "rtl_support": True,
            "supported_languages": ["ar", "en"],
            "default_language": "ar",
            "modules": {
                "dashboard": True,
                "appointments": True,
                "service_tracking": True,
                "payments": True,
                "documents": True,
                "feedback": True,
                "notifications": True,
            },
            "features": {
                "real_time_tracking": True,
                "mobile_payments": True,
                "whatsapp_integration": True,
                "sms_integration": True,
                "photo_uploads": True,
                "document_download": True,
                "appointment_booking": True,
                "service_history": True,
            },
            "ui_settings": {
                "theme": "workshop_theme",
                "primary_color": "#2E5C8A",
                "secondary_color": "#F39C12",
                "accent_color": "#E74C3C",
                "background_color": "#F8F9FA",
                "text_color": "#2C3E50",
                "arabic_font": "Noto Sans Arabic",
                "english_font": "Inter",
            },
        }

        config_path = frappe.get_app_path(
            "universal_workshop", "customer_portal", "portal_config.json"
        )
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _setup_arabic_translations(self):
        """Setup comprehensive Arabic translations for portal"""
        translations = {
            # Navigation
            "Dashboard": "لوحة التحكم",
            "Book Appointment": "حجز موعد",
            "My Services": "خدماتي",
            "Service History": "تاريخ الخدمات",
            "Payments": "المدفوعات",
            "Documents": "المستندات",
            "Profile": "الملف الشخصي",
            "Notifications": "الإشعارات",
            "Support": "الدعم",
            "Logout": "تسجيل الخروج",
            # Dashboard
            "Welcome to Universal Workshop Portal": "مرحباً بك في بوابة ورشة يونيفرسال",
            "Your Account Summary": "ملخص حسابك",
            "Upcoming Appointments": "المواعيد القادمة",
            "Recent Services": "الخدمات الأخيرة",
            "Outstanding Payments": "المدفوعات المستحقة",
            "Quick Actions": "الإجراءات السريعة",
            # Appointments
            "Book New Appointment": "حجز موعد جديد",
            "Available Time Slots": "المواعيد المتاحة",
            "Select Service Type": "اختر نوع الخدمة",
            "Choose Date and Time": "اختر التاريخ والوقت",
            "Confirm Booking": "تأكيد الحجز",
            "Appointment Confirmed": "تم تأكيد الموعد",
            "Modify Appointment": "تعديل الموعد",
            "Cancel Appointment": "إلغاء الموعد",
            # Service Tracking
            "Track Your Service": "تتبع خدمتك",
            "Service Status": "حالة الخدمة",
            "Estimated Completion": "الوقت المتوقع للإنجاز",
            "Parts Required": "القطع المطلوبة",
            "Labor Progress": "تقدم العمل",
            "Quality Check": "فحص الجودة",
            "Ready for Pickup": "جاهز للاستلام",
            # Payments
            "Pay Online": "ادفع أونلاين",
            "Payment History": "تاريخ المدفوعات",
            "Outstanding Amount": "المبلغ المستحق",
            "Payment Methods": "طرق الدفع",
            "Credit Card": "بطاقة ائتمان",
            "Bank Transfer": "تحويل بنكي",
            "Cash on Delivery": "الدفع عند الاستلام",
            # Documents
            "My Documents": "مستنداتي",
            "Invoices": "الفواتير",
            "Service Reports": "تقارير الخدمة",
            "Warranty Documents": "مستندات الضمان",
            "Upload Document": "رفع مستند",
            "Download": "تحميل",
            "View": "عرض",
            # Forms
            "First Name": "الاسم الأول",
            "Last Name": "اسم العائلة",
            "Email": "البريد الإلكتروني",
            "Phone Number": "رقم الهاتف",
            "Vehicle Information": "معلومات المركبة",
            "Make": "الماركة",
            "Model": "الموديل",
            "Year": "السنة",
            "License Plate": "رقم اللوحة",
            "Submit": "إرسال",
            "Cancel": "إلغاء",
            "Save": "حفظ",
            "Edit": "تعديل",
            # Messages
            "Loading...": "جاري التحميل...",
            "Please wait": "يرجى الانتظار",
            "Success": "تم بنجاح",
            "Error": "خطأ",
            "Warning": "تحذير",
            "Confirmation": "تأكيد",
            "Are you sure?": "هل أنت متأكد؟",
            "Operation completed successfully": "تمت العملية بنجاح",
            "An error occurred": "حدث خطأ",
            "No data available": "لا توجد بيانات متاحة",
            # Mobile-specific
            "Tap to select": "اضغط للاختيار",
            "Swipe to refresh": "اسحب للتحديث",
            "Pull to refresh": "اسحب للتحديث",
            "Back": "رجوع",
            "Menu": "القائمة",
            "Search": "بحث",
            "Filter": "تصفية",
            "Sort": "ترتيب",
        }

        # Save translations to file
        translations_path = frappe.get_app_path(
            "universal_workshop", "customer_portal", "translations.json"
        )
        with open(translations_path, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        return translations

    def _create_mobile_manifest(self):
        """Create Progressive Web App manifest for mobile optimization"""
        manifest = {
            "name": "Universal Workshop",
            "short_name": "ورشة يونيفرسال",
            "description": "Customer portal for Universal Workshop services",
            "description_ar": "بوابة العملاء لخدمات ورشة يونيفرسال",
            "start_url": "/portal",
            "display": "standalone",
            "background_color": "#F8F9FA",
            "theme_color": "#2E5C8A",
            "orientation": "portrait",
            "dir": "rtl",
            "lang": "ar",
            "icons": [
                {
                    "src": "/assets/universal_workshop/images/icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png",
                },
                {
                    "src": "/assets/universal_workshop/images/icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                },
            ],
            "screenshots": [
                {
                    "src": "/assets/universal_workshop/images/screenshots/mobile-dashboard.png",
                    "sizes": "375x812",
                    "type": "image/png",
                    "form_factor": "narrow",
                },
                {
                    "src": "/assets/universal_workshop/images/screenshots/tablet-dashboard.png",
                    "sizes": "768x1024",
                    "type": "image/png",
                    "form_factor": "wide",
                },
            ],
            "categories": ["automotive", "business", "productivity"],
            "shortcuts": [
                {
                    "name": "Book Appointment",
                    "name_ar": "حجز موعد",
                    "short_name": "Book",
                    "description": "Book a new service appointment",
                    "url": "/portal/book-appointment",
                    "icons": [
                        {
                            "src": "/assets/universal_workshop/images/icons/calendar-icon.png",
                            "sizes": "96x96",
                        }
                    ],
                },
                {
                    "name": "Track Service",
                    "name_ar": "تتبع الخدمة",
                    "short_name": "Track",
                    "description": "Track your service progress",
                    "url": "/portal/track-service",
                    "icons": [
                        {
                            "src": "/assets/universal_workshop/images/icons/track-icon.png",
                            "sizes": "96x96",
                        }
                    ],
                },
                {
                    "name": "Pay Online",
                    "name_ar": "ادفع أونلاين",
                    "short_name": "Pay",
                    "description": "Make online payments",
                    "url": "/portal/payments",
                    "icons": [
                        {
                            "src": "/assets/universal_workshop/images/icons/payment-icon.png",
                            "sizes": "96x96",
                        }
                    ],
                },
            ],
        }

        manifest_path = frappe.get_app_path(
            "universal_workshop", "public", "portal", "manifest.json"
        )
        os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    def get_portal_navigation(self, user_role: str = "Customer") -> List[Dict[str, Any]]:
        """Get portal navigation menu based on user role and permissions"""
        base_navigation = [
            {
                "title": _("Dashboard"),
                "title_ar": "لوحة التحكم",
                "route": "/portal",
                "icon": "dashboard",
                "order": 1,
                "enabled": True,
            },
            {
                "title": _("Book Appointment"),
                "title_ar": "حجز موعد",
                "route": "/portal/book-appointment",
                "icon": "calendar_plus",
                "order": 2,
                "enabled": self.portal_settings.get("appointment_booking", True),
            },
            {
                "title": _("My Services"),
                "title_ar": "خدماتي",
                "route": "/portal/services",
                "icon": "tool",
                "order": 3,
                "enabled": True,
            },
            {
                "title": _("Service History"),
                "title_ar": "تاريخ الخدمات",
                "route": "/portal/history",
                "icon": "history",
                "order": 4,
                "enabled": True,
            },
            {
                "title": _("Payments"),
                "title_ar": "المدفوعات",
                "route": "/portal/payments",
                "icon": "credit_card",
                "order": 5,
                "enabled": self.portal_settings.get("online_payments", True),
            },
            {
                "title": _("Documents"),
                "title_ar": "المستندات",
                "route": "/portal/documents",
                "icon": "folder",
                "order": 6,
                "enabled": self.portal_settings.get("document_access", True),
            },
            {
                "title": _("Profile"),
                "title_ar": "الملف الشخصي",
                "route": "/portal/profile",
                "icon": "user",
                "order": 7,
                "enabled": True,
            },
            {
                "title": _("Support"),
                "title_ar": "الدعم",
                "route": "/portal/support",
                "icon": "help_circle",
                "order": 8,
                "enabled": True,
            },
        ]

        # Filter navigation based on enabled features
        enabled_navigation = [nav for nav in base_navigation if nav.get("enabled", True)]

        # Sort by order
        enabled_navigation.sort(key=lambda x: x.get("order", 999))

        return enabled_navigation

    def get_mobile_layout_config(self) -> Dict[str, Any]:
        """Get mobile-specific layout configuration"""
        return {
            "responsive_breakpoints": {
                "mobile": "(max-width: 768px)",
                "tablet": "(min-width: 769px) and (max-width: 1024px)",
                "desktop": "(min-width: 1025px)",
            },
            "touch_settings": {
                "min_touch_target": "44px",
                "touch_padding": "12px",
                "swipe_threshold": "100px",
                "tap_highlight": "transparent",
            },
            "mobile_features": {
                "pull_to_refresh": True,
                "infinite_scroll": True,
                "touch_gestures": True,
                "haptic_feedback": True,
                "orientation_lock": "portrait",
            },
            "performance": {
                "lazy_loading": True,
                "image_compression": True,
                "cache_strategy": "cache_first",
                "offline_support": True,
            },
            "pwa_features": {
                "service_worker": True,
                "push_notifications": True,
                "background_sync": True,
                "install_prompt": True,
            },
        }

    def validate_portal_access(self, user_email: str) -> Dict[str, Any]:
        """Validate user access to portal and return permissions"""
        try:
            # Check if user exists and is active
            user = frappe.get_doc("User", user_email)
            if user.enabled == 0:
                return {
                    "access_granted": False,
                    "reason": "account_disabled",
                    "message": _("Your account has been disabled"),
                }

            # Check if user is a customer
            customer = frappe.db.get_value("Customer", {"user_email": user_email})
            if not customer:
                return {
                    "access_granted": False,
                    "reason": "not_customer",
                    "message": _("Portal access is limited to customers only"),
                }

            # Get customer permissions and settings
            customer_doc = frappe.get_doc("Customer", customer)

            portal_permissions = {
                "dashboard": True,
                "appointments": self.portal_settings.get("appointment_booking", True),
                "services": True,
                "history": True,
                "payments": self.portal_settings.get("online_payments", True)
                and customer_doc.payment_terms,
                "documents": self.portal_settings.get("document_access", True),
                "profile": True,
                "support": True,
                "notifications": True,
            }

            return {
                "access_granted": True,
                "user": user.as_dict(),
                "customer": customer_doc.as_dict(),
                "permissions": portal_permissions,
                "language_preference": user.language or "ar",
                "portal_settings": self.portal_settings,
            }

        except frappe.DoesNotExistError:
            return {
                "access_granted": False,
                "reason": "user_not_found",
                "message": _("User account not found"),
            }
        except Exception as e:
            frappe.log_error(f"Portal access validation failed: {str(e)}")
            return {
                "access_granted": False,
                "reason": "validation_error",
                "message": _("Unable to validate portal access"),
            }


# Portal Framework API Methods
@frappe.whitelist()
def initialize_customer_portal():
    """Initialize customer portal framework"""
    portal = CustomerPortalFramework()
    return portal.initialize_portal_structure()


@frappe.whitelist()
def get_portal_navigation(user_role="Customer"):
    """Get portal navigation menu"""
    portal = CustomerPortalFramework()
    return portal.get_portal_navigation(user_role)


@frappe.whitelist()
def get_mobile_config():
    """Get mobile layout configuration"""
    portal = CustomerPortalFramework()
    return portal.get_mobile_layout_config()


@frappe.whitelist()
def validate_user_access(user_email=None):
    """Validate user portal access"""
    if not user_email:
        user_email = frappe.session.user

    portal = CustomerPortalFramework()
    return portal.validate_portal_access(user_email)


@frappe.whitelist()
def get_portal_settings():
    """Get portal configuration settings"""
    portal = CustomerPortalFramework()
    return portal.get_portal_settings()
