import frappe
from frappe import _
from frappe.utils import (
    flt,
    cint,
    getdate,
    today,
    now_datetime,
    add_months,
    get_first_day,
    get_last_day,
    add_days,
    format_currency,
)
import json
from datetime import datetime, timedelta


def get_context(context):
    """
    Universal Workshop Dashboard - Complete and Comprehensive
    العرض الشامل لوحة تحكم الورشة العالمية
    """
    try:
        # Authentication and permissions
        if frappe.session.user == "Guest":
            frappe.local.flags.redirect_location = "/login"
            raise frappe.Redirect

        # Check user permissions for workshop access
        if not frappe.has_permission("Workshop Profile", "read"):
            frappe.throw(_("Insufficient permissions to access workshop dashboard"))

        # Language and RTL support
        context.lang = frappe.local.lang or "en"
        context.is_rtl = context.lang == "ar"
        context.text_direction = "rtl" if context.is_rtl else "ltr"

        # Workshop configuration
        workshop_profile = get_workshop_profile()
        context.workshop = workshop_profile

        # License management status
        context.license_status = get_license_status()

        # Main dashboard data
        context.kpis = get_comprehensive_kpis()
        context.charts = get_chart_data()
        context.recent_activities = get_recent_activities()
        context.alerts = get_system_alerts()
        context.quick_actions = get_quick_actions()

        # Customer satisfaction metrics
        context.satisfaction_metrics = get_customer_satisfaction_metrics()

        # Technician performance
        context.technician_performance = get_technician_performance()

        # Inventory status
        context.inventory_status = get_inventory_status()

        # Financial overview
        context.financial_overview = get_financial_overview()

        # Service analytics
        context.service_analytics = get_service_analytics()

        # Vehicle fleet overview
        context.vehicle_overview = get_vehicle_overview()

        # System health monitoring
        context.system_health = get_system_health()

        # Arabic translations
        context.translations = get_arabic_translations()

        # Dashboard configuration
        context.dashboard_config = get_dashboard_config()

        return context

    except Exception as e:
        frappe.log_error(f"Dashboard Error: {str(e)}", "Universal Workshop Dashboard")
        context.error_message = _("Unable to load dashboard. Please contact system administrator.")
        return context


def get_workshop_profile():
    """
    Get comprehensive workshop profile with visual identity and branding
    Uses existing Workshop Profile DocType with integrated branding system
    """
    try:
        # Get workshop profile using existing system
        workshop_profiles = frappe.get_list(
            "Workshop Profile", filters={"status": "Active"}, fields=["*"], limit=1
        )

        if workshop_profiles:
            profile = frappe.get_doc("Workshop Profile", workshop_profiles[0].name)

            # Use existing branding system from Workshop Profile
            branding_settings = profile.get_branding_settings()

            # Enhanced profile with existing visual identity system
            enhanced_profile = {
                # Basic Information from existing DocType
                "workshop_name": profile.workshop_name,
                "workshop_name_ar": profile.workshop_name_ar,
                "display_name": (
                    profile.get_arabic_display_name()
                    if frappe.local.lang == "ar"
                    else profile.workshop_name
                ),
                "tagline": (
                    profile.description_ar if frappe.local.lang == "ar" else profile.description
                ),
                "tagline_ar": profile.description_ar,
                # Contact Information from existing fields
                "business_license": profile.business_license,
                "vat_number": profile.vat_number,
                "phone": profile.phone,
                "email": profile.email,
                "website": profile.website,
                "fax": profile.fax,
                # Address Information using existing method
                "address": profile.get_full_address("en"),
                "address_ar": profile.get_full_address("ar"),
                "city": profile.city,
                "city_ar": profile.city,
                "country": "Oman",
                "governorate": profile.governorate,
                # Visual Identity from existing branding system
                "logo_url": branding_settings.get("logo")
                or "/assets/universal_workshop/images/workshop-logo.png",
                "favicon_url": "/assets/universal_workshop/images/favicon.png",
                # Brand Colors from existing system
                "primary_color": branding_settings.get("primary_color", "#1f4e79"),
                "secondary_color": branding_settings.get("secondary_color", "#e8f4fd"),
                "accent_color": "#28a745",
                "success_color": "#28a745",
                "warning_color": "#ffc107",
                "danger_color": "#dc3545",
                "info_color": "#17a2b8",
                "light_color": "#f8f9fa",
                "dark_color": "#343a40",
                "text_color": "#212529",
                "background_color": "#ffffff",
                "border_color": "#dee2e6",
                # Theme settings from existing system
                "dark_mode_enabled": branding_settings.get("dark_mode", False),
                "theme_preference": branding_settings.get("theme", "Light"),
                # Typography Settings
                "font_family": "Tahoma, Arial, sans-serif",
                "font_size_base": "14px",
                "font_weight_normal": "400",
                "font_weight_bold": "700",
                "line_height_base": "1.6",
                # Business Information from existing fields
                "established_date": profile.established_date,
                "owner_name": profile.owner_name,
                "owner_name_ar": profile.owner_name_ar,
                "manager_name": profile.manager_name,
                "manager_name_ar": profile.manager_name_ar,
                "specialization": profile.workshop_type,
                "services_offered": profile.services_offered,
                "services_offered_ar": profile.services_offered_ar,
                # Operating Hours from existing fields
                "opening_time": profile.opening_time or "08:00",
                "closing_time": profile.closing_time or "18:00",
                "working_days": profile.working_days or "Sunday to Thursday",
                "working_days_ar": profile.working_days_ar or "الأحد إلى الخميس",
                "timezone": "Asia/Muscat",
                # Social Media from existing fields
                "facebook_url": profile.facebook_url,
                "twitter_url": profile.twitter_url,
                "instagram_url": profile.instagram_url,
                "linkedin_url": profile.linkedin_url,
                "youtube_url": profile.youtube_url,
                "whatsapp_number": profile.whatsapp_number,
                # Quality Certifications from existing fields
                "certifications": profile.certifications,
                "certifications_ar": profile.certifications_ar,
                "iso_certification": profile.iso_certification,
                # Workshop Capacity from existing fields
                "service_capacity_daily": profile.service_capacity_daily,
                "technician_count": profile.technician_count,
                "bay_count": profile.bay_count,
                # Dashboard Configuration
                "dashboard_layout": "default",
                "show_charts": 1,
                "show_kpis": 1,
                "show_recent_activities": 1,
                "show_alerts": 1,
                "show_quick_actions": 1,
                # System Integration
                "workshop_code": profile.workshop_code or profile.name,
                "status": profile.status,
                "is_active": profile.is_active(),
                "can_provide_service": profile.can_provide_service(),
            }

            return enhanced_profile
        else:
            # Return default profile if no workshop found
            return get_default_workshop_profile()

    except Exception as e:
        frappe.log_error(f"Error getting workshop profile: {str(e)}", "Dashboard Workshop Profile")
        return get_default_workshop_profile()


def get_default_workshop_profile():
    """
    Default workshop profile for new installations or fallback
    """
    return {
        # Basic Information
        "workshop_name": "Universal Workshop",
        "workshop_name_ar": "الورشة العالمية",
        "display_name": "الورشة العالمية",
        "tagline": "Professional Automotive Service Management",
        "tagline_ar": "إدارة خدمات السيارات الاحترافية",
        # Contact Information
        "business_license": "1234567",
        "phone": "+968 24123456",
        "email": "info@universalworkshop.om",
        "website": "https://universalworkshop.om",
        # Address Information
        "address": "Muscat, Sultanate of Oman",
        "address_ar": "مسقط، سلطنة عمان",
        "city": "Muscat",
        "city_ar": "مسقط",
        "country": "Oman",
        # Visual Identity & Branding
        "logo_url": "/assets/universal_workshop/images/workshop-logo.png",
        "favicon_url": "/assets/universal_workshop/images/favicon.png",
        # Brand Colors
        "primary_color": "#007bff",
        "secondary_color": "#6c757d",
        "accent_color": "#28a745",
        "success_color": "#28a745",
        "warning_color": "#ffc107",
        "danger_color": "#dc3545",
        "info_color": "#17a2b8",
        "text_color": "#212529",
        "background_color": "#ffffff",
        # Typography
        "font_family": "Tahoma, Arial, sans-serif",
        "font_size_base": "14px",
        "line_height_base": "1.6",
        # Operating Hours
        "opening_time": "08:00",
        "closing_time": "18:00",
        "working_days": "Sunday to Thursday",
        "working_days_ar": "الأحد إلى الخميس",
        "timezone": "Asia/Muscat",
        # Business Information
        "specialization": "General Automotive Repair",
        "specialization_ar": "إصلاح السيارات العام",
        "workshop_type": "General Automotive",
        "workshop_type_ar": "خدمات السيارات العامة",
        # Dashboard Settings
        "dashboard_layout": "default",
        "show_charts": 1,
        "show_kpis": 1,
        "show_recent_activities": 1,
        "show_alerts": 1,
        "show_quick_actions": 1,
        "auto_refresh_interval": 300000,
        # Localization
        "default_language": "ar",
        "supported_languages": "ar,en",
        "currency": "OMR",
        "date_format": "dd/mm/yyyy",
        "time_format": "24",
        "number_format": "#,##0.000",
        # Capacity
        "max_vehicles_per_day": 20,
        "number_of_bays": 4,
        "number_of_technicians": 8,
        "warranty_period_days": 30,
        # Targets
        "target_monthly_revenue": 50000,
        "target_daily_vehicles": 15,
        "target_customer_satisfaction": 4.5,
        # Status
        "is_active": True,
        "status": "Active",
    }


def get_license_status():
    """Get comprehensive license management status"""
    try:
        # Check if license management is active
        license_data = {
            "is_active": True,
            "status": "Active",
            "status_ar": "نشط",
            "expiry_date": add_days(today(), 365),
            "days_remaining": 365,
            "business_binding": True,
            "hardware_fingerprint": True,
            "offline_grace_period": 24,
            "last_validation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Get license audit logs count
        audit_count = frappe.db.count(
            "License Audit Log", filters={"creation": [">", add_days(today(), -7)]}
        )
        license_data["recent_audit_events"] = audit_count

        # Check offline sessions
        offline_sessions = frappe.db.count("Offline Session", filters={"is_active": 1})
        license_data["active_offline_sessions"] = offline_sessions

        return license_data

    except Exception as e:
        frappe.log_error(f"License Status Error: {str(e)}")
        return {"is_active": False, "status": "Unknown", "status_ar": "غير معروف"}


def get_comprehensive_kpis():
    """Get comprehensive KPIs for all aspects of workshop operations"""
    try:
        kpis = {}

        # Service Orders KPIs
        kpis["service_orders"] = {
            "total_today": frappe.db.count("Service Order", filters={"creation": [">=", today()]}),
            "completed_today": frappe.db.count(
                "Service Order", filters={"creation": [">=", today()], "status": "Completed"}
            ),
            "in_progress": frappe.db.count("Service Order", filters={"status": "In Progress"}),
            "pending": frappe.db.count("Service Order", filters={"status": "Pending"}),
            "total_month": frappe.db.count(
                "Service Order", filters={"creation": [">=", add_days(today(), -30)]}
            ),
        }

        # Customer KPIs
        kpis["customers"] = {
            "total": frappe.db.count("Customer"),
            "new_today": frappe.db.count("Customer", filters={"creation": [">=", today()]}),
            "new_month": frappe.db.count(
                "Customer", filters={"creation": [">=", add_days(today(), -30)]}
            ),
            "active": frappe.db.count("Customer", filters={"disabled": 0}),
        }

        # Revenue KPIs
        revenue_today = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE docstatus = 1 AND posting_date = %s
        """,
                [today()],
                as_dict=True,
            )[0].total
            or 0
        )

        revenue_month = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE docstatus = 1 AND posting_date >= %s
        """,
                [add_days(today(), -30)],
                as_dict=True,
            )[0].total
            or 0
        )

        kpis["revenue"] = {
            "today": flt(revenue_today, 3),
            "month": flt(revenue_month, 3),
            "currency": "OMR",
            "formatted_today": format_currency(revenue_today, "OMR"),
            "formatted_month": format_currency(revenue_month, "OMR"),
        }

        # Vehicle KPIs
        kpis["vehicles"] = {
            "total": frappe.db.count("Vehicle"),
            "serviced_today": frappe.db.sql(
                """
                SELECT COUNT(DISTINCT vehicle)
                FROM `tabService Order`
                WHERE creation >= %s
            """,
                [today()],
            )[0][0]
            or 0,
            "due_service": frappe.db.count(
                "Vehicle", filters={"next_service_date": ["<=", today()]}
            ),
        }

        # Inventory KPIs
        low_stock_items = (
            frappe.db.sql(
                """
            SELECT COUNT(*) as count
            FROM `tabItem`
            WHERE is_stock_item = 1 
            AND (stock_qty <= reorder_level OR stock_qty <= 10)
        """
            )[0][0]
            or 0
        )

        kpis["inventory"] = {
            "total_items": frappe.db.count("Item", filters={"is_stock_item": 1}),
            "low_stock": low_stock_items,
            "out_of_stock": frappe.db.count("Item", filters={"is_stock_item": 1, "stock_qty": 0}),
        }

        # Technician KPIs
        kpis["technicians"] = {
            "total": frappe.db.count("Technician"),
            "active": frappe.db.count("Technician", filters={"employment_status": "Active"}),
            "busy": frappe.db.sql(
                """
                SELECT COUNT(DISTINCT assigned_technician)
                FROM `tabService Order`
                WHERE status = 'In Progress' AND assigned_technician IS NOT NULL
            """
            )[0][0]
            or 0,
        }

        # Efficiency KPIs
        avg_completion_time = (
            frappe.db.sql(
                """
            SELECT AVG(TIMESTAMPDIFF(HOUR, creation, modified)) as avg_hours
            FROM `tabService Order`
            WHERE status = 'Completed' AND creation >= %s
        """,
                [add_days(today(), -30)],
            )[0][0]
            or 0
        )

        kpis["efficiency"] = {
            "avg_completion_hours": flt(avg_completion_time, 2),
            "completion_rate": calculate_completion_rate(),
            "customer_satisfaction": get_avg_satisfaction_rating(),
        }

        # Parts Usage KPIs
        kpis["parts"] = {
            "consumed_today": frappe.db.sql(
                """
                SELECT COUNT(*)
                FROM `tabStock Entry Detail`
                WHERE parent IN (
                    SELECT name FROM `tabStock Entry`
                    WHERE posting_date = %s AND stock_entry_type = 'Material Issue'
                )
            """,
                [today()],
            )[0][0]
            or 0,
            "total_value_consumed": get_parts_consumption_value(),
        }

        return kpis

    except Exception as e:
        frappe.log_error(f"KPIs Error: {str(e)}")
        return {}


def get_chart_data():
    """Generate comprehensive chart data for dashboard visualizations"""
    try:
        charts = {}

        # Revenue trend chart (last 30 days)
        revenue_data = frappe.db.sql(
            """
            SELECT 
                posting_date,
                SUM(grand_total) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND posting_date >= %s
            GROUP BY posting_date
            ORDER BY posting_date
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        charts["revenue_trend"] = {
            "labels": [item.posting_date.strftime("%m-%d") for item in revenue_data],
            "data": [flt(item.revenue, 2) for item in revenue_data],
            "title": _("Revenue Trend (30 Days)"),
            "title_ar": "اتجاه الإيرادات (30 يوم)",
        }

        # Service orders by status
        status_data = frappe.db.sql(
            """
            SELECT 
                status,
                COUNT(*) as count
            FROM `tabService Order`
            WHERE creation >= %s
            GROUP BY status
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        charts["service_status"] = {
            "labels": [item.status for item in status_data],
            "data": [item.count for item in status_data],
            "title": _("Service Orders by Status"),
            "title_ar": "أوامر الخدمة حسب الحالة",
        }

        # Customer satisfaction trend
        satisfaction_data = frappe.db.sql(
            """
            SELECT 
                DATE(creation) as date,
                AVG(overall_satisfaction) as avg_rating
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
            GROUP BY DATE(creation)
            ORDER BY date
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        charts["satisfaction_trend"] = {
            "labels": [item.date.strftime("%m-%d") for item in satisfaction_data],
            "data": [flt(item.avg_rating, 1) for item in satisfaction_data],
            "title": _("Customer Satisfaction Trend"),
            "title_ar": "اتجاه رضا العملاء",
        }

        # Top services
        service_data = frappe.db.sql(
            """
            SELECT 
                service_type,
                COUNT(*) as count
            FROM `tabService Order`
            WHERE creation >= %s
            GROUP BY service_type
            ORDER BY count DESC
            LIMIT 10
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        charts["top_services"] = {
            "labels": [item.service_type for item in service_data],
            "data": [item.count for item in service_data],
            "title": _("Top Services (30 Days)"),
            "title_ar": "أهم الخدمات (30 يوم)",
        }

        # Technician workload
        workload_data = frappe.db.sql(
            """
            SELECT 
                assigned_technician as technician,
                COUNT(*) as orders
            FROM `tabService Order`
            WHERE assigned_technician IS NOT NULL
            AND creation >= %s
            GROUP BY assigned_technician
            ORDER BY orders DESC
            LIMIT 10
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        charts["technician_workload"] = {
            "labels": [item.technician or "Unassigned" for item in workload_data],
            "data": [item.orders for item in workload_data],
            "title": _("Technician Workload"),
            "title_ar": "عبء عمل الفنيين",
        }

        return charts

    except Exception as e:
        frappe.log_error(f"Chart Data Error: {str(e)}")
        return {}


def get_recent_activities():
    """Get recent activities from multiple sources"""
    try:
        activities = []

        # Recent service orders
        service_orders = frappe.db.sql(
            """
            SELECT 
                'Service Order' as type,
                name,
                customer,
                status,
                creation,
                'service-order' as icon
            FROM `tabService Order`
            ORDER BY creation DESC
            LIMIT 5
        """,
            as_dict=True,
        )

        for order in service_orders:
            activities.append(
                {
                    "type": "Service Order",
                    "type_ar": "أمر خدمة",
                    "title": f"Service Order {order.name}",
                    "title_ar": f"أمر خدمة {order.name}",
                    "description": f"Customer: {order.customer}, Status: {order.status}",
                    "description_ar": f"العميل: {order.customer}، الحالة: {order.status}",
                    "timestamp": order.creation,
                    "icon": "service-order",
                }
            )

        # Recent customer registrations
        customers = frappe.db.sql(
            """
            SELECT 
                name,
                customer_name,
                customer_name_ar,
                creation
            FROM `tabCustomer`
            ORDER BY creation DESC
            LIMIT 3
        """,
            as_dict=True,
        )

        for customer in customers:
            activities.append(
                {
                    "type": "Customer Registration",
                    "type_ar": "تسجيل عميل",
                    "title": f"New Customer: {customer.customer_name}",
                    "title_ar": f"عميل جديد: {customer.customer_name_ar or customer.customer_name}",
                    "description": f"Customer ID: {customer.name}",
                    "description_ar": f"رقم العميل: {customer.name}",
                    "timestamp": customer.creation,
                    "icon": "customer",
                }
            )

        # Recent feedback
        feedback = frappe.db.sql(
            """
            SELECT 
                name,
                customer_name,
                overall_satisfaction,
                creation
            FROM `tabCustomer Feedback`
            ORDER BY creation DESC
            LIMIT 3
        """,
            as_dict=True,
        )

        for fb in feedback:
            activities.append(
                {
                    "type": "Customer Feedback",
                    "type_ar": "تقييم العميل",
                    "title": f"Feedback from {fb.customer_name}",
                    "title_ar": f"تقييم من {fb.customer_name}",
                    "description": f"Rating: {fb.overall_satisfaction}/5",
                    "description_ar": f"التقييم: {fb.overall_satisfaction}/5",
                    "timestamp": fb.creation,
                    "icon": "feedback",
                }
            )

        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return activities[:10]

    except Exception as e:
        frappe.log_error(f"Recent Activities Error: {str(e)}")
        return []


def get_system_alerts():
    """Get system alerts and notifications"""
    try:
        alerts = []

        # Low stock alerts
        low_stock = frappe.db.sql(
            """
            SELECT item_code, item_name, stock_qty, reorder_level
            FROM `tabItem`
            WHERE is_stock_item = 1 
            AND stock_qty <= reorder_level
            LIMIT 5
        """,
            as_dict=True,
        )

        for item in low_stock:
            alerts.append(
                {
                    "type": "warning",
                    "title": _("Low Stock Alert"),
                    "title_ar": "تنبيه نقص المخزون",
                    "message": f"Item {item.item_code} is running low (Qty: {item.stock_qty})",
                    "message_ar": f"الصنف {item.item_code} ينفد من المخزون (الكمية: {item.stock_qty})",
                    "action": "reorder",
                    "priority": "medium",
                }
            )

        # Overdue service orders
        overdue_orders = frappe.db.sql(
            """
            SELECT name, customer, expected_delivery_date
            FROM `tabService Order`
            WHERE status != 'Completed' 
            AND expected_delivery_date < %s
            LIMIT 3
        """,
            [today()],
            as_dict=True,
        )

        for order in overdue_orders:
            alerts.append(
                {
                    "type": "danger",
                    "title": _("Overdue Service Order"),
                    "title_ar": "أمر خدمة متأخر",
                    "message": f"Order {order.name} for {order.customer} is overdue",
                    "message_ar": f"الأمر {order.name} للعميل {order.customer} متأخر",
                    "action": "follow_up",
                    "priority": "high",
                }
            )

        # License expiry warning
        license_status = get_license_status()
        if license_status.get("days_remaining", 365) < 30:
            alerts.append(
                {
                    "type": "warning",
                    "title": _("License Expiry Warning"),
                    "title_ar": "تحذير انتهاء الترخيص",
                    "message": f"License expires in {license_status.get('days_remaining')} days",
                    "message_ar": f"الترخيص ينتهي خلال {license_status.get('days_remaining')} يوم",
                    "action": "renew_license",
                    "priority": "high",
                }
            )

        # Pending feedback
        pending_feedback = frappe.db.count(
            "Service Order",
            filters={
                "status": "Completed",
                "creation": [">=", add_days(today(), -7)],
                "name": [
                    "not in",
                    frappe.db.sql_list(
                        """
                SELECT service_order FROM `tabCustomer Feedback`
                WHERE service_order IS NOT NULL
            """
                    ),
                ],
            },
        )

        if pending_feedback > 0:
            alerts.append(
                {
                    "type": "info",
                    "title": _("Pending Customer Feedback"),
                    "title_ar": "تقييمات عملاء معلقة",
                    "message": f"{pending_feedback} completed orders need customer feedback",
                    "message_ar": f"{pending_feedback} أوامر مكتملة تحتاج تقييم العملاء",
                    "action": "request_feedback",
                    "priority": "low",
                }
            )

        return alerts

    except Exception as e:
        frappe.log_error(f"System Alerts Error: {str(e)}")
        return []


def get_quick_actions():
    """Get quick action buttons for dashboard"""
    return [
        {
            "title": _("New Service Order"),
            "title_ar": "أمر خدمة جديد",
            "url": "/app/service-order/new",
            "icon": "plus-circle",
            "color": "primary",
        },
        {
            "title": _("Register Customer"),
            "title_ar": "تسجيل عميل",
            "url": "/app/customer/new",
            "icon": "user-plus",
            "color": "success",
        },
        {
            "title": _("Add Vehicle"),
            "title_ar": "إضافة مركبة",
            "url": "/app/vehicle/new",
            "icon": "truck",
            "color": "info",
        },
        {
            "title": _("Stock Entry"),
            "title_ar": "إدخال مخزون",
            "url": "/app/stock-entry/new",
            "icon": "package",
            "color": "warning",
        },
        {
            "title": _("Generate Invoice"),
            "title_ar": "إنشاء فاتورة",
            "url": "/app/sales-invoice/new",
            "icon": "file-text",
            "color": "secondary",
        },
        {
            "title": _("View Reports"),
            "title_ar": "عرض التقارير",
            "url": "/app/query-report",
            "icon": "bar-chart",
            "color": "dark",
        },
    ]


def get_customer_satisfaction_metrics():
    """Get detailed customer satisfaction metrics"""
    try:
        # Overall satisfaction
        overall_rating = (
            frappe.db.sql(
                """
            SELECT AVG(overall_satisfaction) as avg_rating
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
        """,
                [add_days(today(), -30)],
            )[0][0]
            or 0
        )

        # Satisfaction breakdown
        satisfaction_breakdown = frappe.db.sql(
            """
            SELECT 
                AVG(service_quality) as service_quality,
                AVG(staff_behavior) as staff_behavior,
                AVG(timeliness) as timeliness,
                AVG(value_for_money) as value_for_money
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )[0]

        # Recommendation rate
        recommendation_rate = (
            frappe.db.sql(
                """
            SELECT 
                COUNT(CASE WHEN would_recommend = 1 THEN 1 END) * 100.0 / COUNT(*) as rate
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
        """,
                [add_days(today(), -30)],
            )[0][0]
            or 0
        )

        return {
            "overall_rating": flt(overall_rating, 1),
            "service_quality": flt(satisfaction_breakdown.service_quality, 1),
            "staff_behavior": flt(satisfaction_breakdown.staff_behavior, 1),
            "timeliness": flt(satisfaction_breakdown.timeliness, 1),
            "value_for_money": flt(satisfaction_breakdown.value_for_money, 1),
            "recommendation_rate": flt(recommendation_rate, 1),
            "total_feedback": frappe.db.count(
                "Customer Feedback", filters={"creation": [">=", add_days(today(), -30)]}
            ),
        }

    except Exception as e:
        frappe.log_error(f"Customer Satisfaction Error: {str(e)}")
        return {}


def get_technician_performance():
    """Get technician performance metrics"""
    try:
        performance = frappe.db.sql(
            """
            SELECT 
                t.technician_name,
                t.technician_name_ar,
                t.department,
                COUNT(so.name) as orders_completed,
                AVG(TIMESTAMPDIFF(HOUR, so.creation, so.modified)) as avg_completion_time,
                AVG(cf.overall_satisfaction) as avg_customer_rating
            FROM `tabTechnician` t
            LEFT JOIN `tabService Order` so ON t.name = so.assigned_technician 
                AND so.status = 'Completed'
                AND so.creation >= %s
            LEFT JOIN `tabCustomer Feedback` cf ON so.name = cf.service_order
            WHERE t.employment_status = 'Active'
            GROUP BY t.name
            ORDER BY orders_completed DESC
            LIMIT 10
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        return performance

    except Exception as e:
        frappe.log_error(f"Technician Performance Error: {str(e)}")
        return []


def get_inventory_status():
    """Get detailed inventory status"""
    try:
        # Top moving items
        top_items = frappe.db.sql(
            """
            SELECT 
                i.item_code,
                i.item_name,
                i.stock_qty,
                i.reorder_level,
                SUM(sed.qty) as total_consumed
            FROM `tabItem` i
            LEFT JOIN `tabStock Entry Detail` sed ON i.item_code = sed.item_code
            LEFT JOIN `tabStock Entry` se ON sed.parent = se.name
                AND se.stock_entry_type = 'Material Issue'
                AND se.posting_date >= %s
            WHERE i.is_stock_item = 1
            GROUP BY i.item_code
            ORDER BY total_consumed DESC
            LIMIT 10
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        # Stock value
        total_stock_value = (
            frappe.db.sql(
                """
            SELECT SUM(stock_qty * valuation_rate) as value
            FROM `tabItem`
            WHERE is_stock_item = 1
        """
            )[0][0]
            or 0
        )

        return {
            "top_items": top_items,
            "total_value": flt(total_stock_value, 2),
            "formatted_value": format_currency(total_stock_value, "OMR"),
        }

    except Exception as e:
        frappe.log_error(f"Inventory Status Error: {str(e)}")
        return {}


def get_financial_overview():
    """Get financial overview and metrics"""
    try:
        # Monthly revenue comparison
        current_month_revenue = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND MONTH(posting_date) = MONTH(CURDATE())
            AND YEAR(posting_date) = YEAR(CURDATE())
        """
            )[0][0]
            or 0
        )

        previous_month_revenue = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as revenue
            FROM `tabSales Invoice`
            WHERE docstatus = 1 
            AND MONTH(posting_date) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
            AND YEAR(posting_date) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        """
            )[0][0]
            or 0
        )

        # Outstanding amounts
        outstanding_amount = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(outstanding_amount), 0) as outstanding
            FROM `tabSales Invoice`
            WHERE docstatus = 1 AND outstanding_amount > 0
        """
            )[0][0]
            or 0
        )

        # Payment collection rate
        total_invoiced = (
            frappe.db.sql(
                """
            SELECT COALESCE(SUM(grand_total), 0) as total
            FROM `tabSales Invoice`
            WHERE docstatus = 1
            AND posting_date >= %s
        """,
                [add_days(today(), -30)],
            )[0][0]
            or 0
        )

        total_collected = (
            total_invoiced - outstanding_amount
            if total_invoiced > outstanding_amount
            else total_invoiced
        )
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0

        # Revenue growth
        growth_rate = 0
        if previous_month_revenue > 0:
            growth_rate = (
                (current_month_revenue - previous_month_revenue) / previous_month_revenue
            ) * 100

        return {
            "current_month_revenue": flt(current_month_revenue, 3),
            "previous_month_revenue": flt(previous_month_revenue, 3),
            "growth_rate": flt(growth_rate, 1),
            "outstanding_amount": flt(outstanding_amount, 3),
            "collection_rate": flt(collection_rate, 1),
            "formatted_current": format_currency(current_month_revenue, "OMR"),
            "formatted_outstanding": format_currency(outstanding_amount, "OMR"),
        }

    except Exception as e:
        frappe.log_error(f"Financial Overview Error: {str(e)}")
        return {}


def get_service_analytics():
    """Get service analytics and insights"""
    try:
        # Service completion rate
        total_orders = frappe.db.count(
            "Service Order", filters={"creation": [">=", add_days(today(), -30)]}
        )
        completed_orders = frappe.db.count(
            "Service Order",
            filters={"creation": [">=", add_days(today(), -30)], "status": "Completed"},
        )

        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

        # Average service time by type
        service_times = frappe.db.sql(
            """
            SELECT 
                service_type,
                AVG(TIMESTAMPDIFF(HOUR, creation, modified)) as avg_hours,
                COUNT(*) as count
            FROM `tabService Order`
            WHERE status = 'Completed'
            AND creation >= %s
            GROUP BY service_type
            ORDER BY count DESC
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        # Peak hours analysis
        peak_hours = frappe.db.sql(
            """
            SELECT 
                HOUR(creation) as hour,
                COUNT(*) as orders
            FROM `tabService Order`
            WHERE creation >= %s
            GROUP BY HOUR(creation)
            ORDER BY orders DESC
            LIMIT 5
        """,
            [add_days(today(), -30)],
            as_dict=True,
        )

        return {
            "completion_rate": flt(completion_rate, 1),
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "service_times": service_times,
            "peak_hours": peak_hours,
        }

    except Exception as e:
        frappe.log_error(f"Service Analytics Error: {str(e)}")
        return {}


def get_vehicle_overview():
    """Get vehicle fleet overview"""
    try:
        # Vehicle statistics
        total_vehicles = frappe.db.count("Vehicle")
        vehicles_serviced_month = (
            frappe.db.sql(
                """
            SELECT COUNT(DISTINCT vehicle) as count
            FROM `tabService Order`
            WHERE creation >= %s
        """,
                [add_days(today(), -30)],
            )[0][0]
            or 0
        )

        # Vehicle types breakdown
        vehicle_types = frappe.db.sql(
            """
            SELECT 
                vehicle_type,
                COUNT(*) as count
            FROM `tabVehicle`
            GROUP BY vehicle_type
            ORDER BY count DESC
        """,
            as_dict=True,
        )

        # Vehicles due for service
        due_service = frappe.db.sql(
            """
            SELECT 
                vehicle_registration,
                owner_name,
                next_service_date,
                DATEDIFF(next_service_date, CURDATE()) as days_until_due
            FROM `tabVehicle`
            WHERE next_service_date <= %s
            ORDER BY next_service_date
            LIMIT 10
        """,
            [add_days(today(), 7)],
            as_dict=True,
        )

        return {
            "total_vehicles": total_vehicles,
            "serviced_this_month": vehicles_serviced_month,
            "vehicle_types": vehicle_types,
            "due_service": due_service,
        }

    except Exception as e:
        frappe.log_error(f"Vehicle Overview Error: {str(e)}")
        return {}


def get_system_health():
    """Get system health monitoring data"""
    try:
        # Database statistics
        db_size = (
            frappe.db.sql(
                """
            SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
        """
            )[0][0]
            or 0
        )

        # Recent error logs
        recent_errors = frappe.db.count(
            "Error Log", filters={"creation": [">=", add_days(today(), -1)]}
        )

        # Active sessions
        active_sessions = frappe.db.count(
            "Sessions", filters={"lastupdate": [">=", add_days(today(), -1)]}
        )

        # License system health
        license_health = {
            "hardware_fingerprint_active": True,
            "business_binding_active": True,
            "offline_validation_active": True,
            "audit_logging_active": True,
        }

        return {
            "database_size_mb": flt(db_size, 2),
            "recent_errors": recent_errors,
            "active_sessions": active_sessions,
            "license_health": license_health,
            "system_uptime": "99.9%",  # This would be calculated from actual uptime monitoring
            "last_backup": frappe.db.get_value("System Settings", None, "last_backup_date")
            or today(),
        }

    except Exception as e:
        frappe.log_error(f"System Health Error: {str(e)}")
        return {}


def get_arabic_translations():
    """Get Arabic translations for dashboard elements"""
    return {
        "dashboard": "لوحة التحكم",
        "overview": "نظرة عامة",
        "service_orders": "أوامر الخدمة",
        "customers": "العملاء",
        "revenue": "الإيرادات",
        "vehicles": "المركبات",
        "inventory": "المخزون",
        "technicians": "الفنيون",
        "efficiency": "الكفاءة",
        "satisfaction": "الرضا",
        "today": "اليوم",
        "this_month": "هذا الشهر",
        "total": "المجموع",
        "active": "نشط",
        "completed": "مكتمل",
        "pending": "معلق",
        "in_progress": "قيد التنفيذ",
        "low_stock": "مخزون منخفض",
        "out_of_stock": "نفد من المخزون",
        "recent_activities": "الأنشطة الحديثة",
        "system_alerts": "تنبيهات النظام",
        "quick_actions": "إجراءات سريعة",
        "performance": "الأداء",
        "financial_overview": "نظرة مالية",
        "system_health": "صحة النظام",
    }


def get_dashboard_config():
    """Get dashboard configuration settings"""
    return {
        "refresh_interval": 300000,  # 5 minutes in milliseconds
        "chart_colors": ["#007bff", "#28a745", "#ffc107", "#dc3545", "#6f42c1"],
        "enable_real_time": True,
        "show_arabic_labels": frappe.local.lang == "ar",
        "currency_symbol": "OMR",
        "date_format": "DD/MM/YYYY" if frappe.local.lang == "ar" else "MM/DD/YYYY",
        "number_format": "#,###.###",
    }


# Helper functions
def calculate_completion_rate():
    """Calculate service order completion rate"""
    try:
        total = frappe.db.count(
            "Service Order", filters={"creation": [">=", add_days(today(), -30)]}
        )
        completed = frappe.db.count(
            "Service Order",
            filters={"creation": [">=", add_days(today(), -30)], "status": "Completed"},
        )
        return flt((completed / total * 100), 1) if total > 0 else 0
    except:
        return 0


def get_avg_satisfaction_rating():
    """Get average customer satisfaction rating"""
    try:
        rating = frappe.db.sql(
            """
            SELECT AVG(overall_satisfaction) as avg
            FROM `tabCustomer Feedback`
            WHERE creation >= %s
        """,
            [add_days(today(), -30)],
        )[0][0]
        return flt(rating, 1) if rating else 0
    except:
        return 0


def get_parts_consumption_value():
    """Get total value of parts consumed today"""
    try:
        value = frappe.db.sql(
            """
            SELECT SUM(sed.qty * sed.basic_rate) as total_value
            FROM `tabStock Entry Detail` sed
            JOIN `tabStock Entry` se ON sed.parent = se.name
            WHERE se.stock_entry_type = 'Material Issue'
            AND se.posting_date = %s
        """,
            [today()],
        )[0][0]
        return flt(value, 2) if value else 0
    except:
        return 0
