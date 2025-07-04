"""
Frontend Bridge API - Universal Workshop ERP
Provides integration layer between traditional Frappe frontend and Frontend V2
"""

import frappe
from frappe import _
import json
from typing import Dict, List, Any, Optional


@frappe.whitelist(allow_guest=False)
def get_frontend_preference(user: Optional[str] = None) -> Dict[str, Any]:
    """Get user's frontend preference (traditional vs v2)"""
    
    if not user:
        user = frappe.session.user
    
    # Get user preference from User DocType
    preference = frappe.db.get_value("User", user, "frontend_preference") or "traditional"
    
    return {
        "user": user,
        "frontend_preference": preference,
        "available_frontends": ["traditional", "v2"],
        "v2_enabled": get_v2_feature_flag()
    }


@frappe.whitelist(allow_guest=False) 
def set_frontend_preference(frontend: str) -> Dict[str, Any]:
    """Set user's frontend preference"""
    
    if frontend not in ["traditional", "v2"]:
        frappe.throw(_("Invalid frontend preference. Must be 'traditional' or 'v2'"))
    
    # Check if Frontend V2 is enabled
    if frontend == "v2" and not get_v2_feature_flag():
        frappe.throw(_("Frontend V2 is not enabled for this workshop"))
    
    user = frappe.session.user
    
    # Update user preference
    frappe.db.set_value("User", user, "frontend_preference", frontend)
    frappe.db.commit()
    
    return {
        "user": user,
        "frontend_preference": frontend,
        "updated": True
    }


@frappe.whitelist(allow_guest=False)
def get_v2_feature_flag() -> bool:
    """Check if Frontend V2 is enabled globally"""
    
    try:
        # Check workshop settings for V2 enablement
        v2_enabled = frappe.db.get_single_value("Workshop Settings", "enable_frontend_v2")
        return bool(v2_enabled)
    except:
        # Default to False if settings don't exist
        return False


@frappe.whitelist(allow_guest=False)
def get_v2_config() -> Dict[str, Any]:
    """Get Frontend V2 configuration and assets"""
    
    if not get_v2_feature_flag():
        frappe.throw(_("Frontend V2 is not enabled"))
    
    return {
        "assets": {
            "main_js": "/assets/universal_workshop/v2/main.js",
            "analytics_js": "/assets/universal_workshop/v2/analytics.js", 
            "mobile_js": "/assets/universal_workshop/v2/mobile.js",
            "manifest": "/assets/universal_workshop/v2/manifest.json",
            "service_worker": "/assets/universal_workshop/v2/sw.js"
        },
        "features": {
            "offline_support": True,
            "push_notifications": True,
            "real_time_sync": True,
            "arabic_support": True,
            "mobile_optimized": True
        },
        "api_endpoints": {
            "base_url": f"/api/v2",
            "auth": "/api/v2/auth",
            "workshop": "/api/v2/workshop",
            "customers": "/api/v2/customers",
            "vehicles": "/api/v2/vehicles",
            "service_orders": "/api/v2/service-orders"
        }
    }


@frappe.whitelist(allow_guest=False)
def sync_v2_data(data_type: str, last_sync: Optional[str] = None) -> Dict[str, Any]:
    """Sync data between traditional backend and Frontend V2"""
    
    if not get_v2_feature_flag():
        frappe.throw(_("Frontend V2 is not enabled"))
    
    sync_handlers = {
        "service_orders": sync_service_orders,
        "customers": sync_customers,
        "vehicles": sync_vehicles,
        "technicians": sync_technicians,
        "workshop_profile": sync_workshop_profile
    }
    
    if data_type not in sync_handlers:
        frappe.throw(_("Invalid data type for sync: {0}").format(data_type))
    
    return sync_handlers[data_type](last_sync)


def sync_service_orders(last_sync: Optional[str] = None) -> Dict[str, Any]:
    """Sync service orders for Frontend V2"""
    
    filters = {"docstatus": ["!=", 2]}  # Exclude cancelled
    
    if last_sync:
        filters["modified"] = [">", last_sync]
    
    service_orders = frappe.get_list("Service Order", 
        filters=filters,
        fields=[
            "name", "customer", "vehicle", "service_type", "service_type_ar",
            "appointment_date", "status", "technician", "estimated_cost",
            "actual_cost", "created_on", "modified"
        ],
        limit=100,
        order_by="modified desc"
    )
    
    return {
        "data_type": "service_orders",
        "records": service_orders,
        "count": len(service_orders),
        "last_sync": frappe.utils.now(),
        "has_more": len(service_orders) == 100
    }


def sync_customers(last_sync: Optional[str] = None) -> Dict[str, Any]:
    """Sync customers for Frontend V2"""
    
    filters = {"disabled": 0}
    
    if last_sync:
        filters["modified"] = [">", last_sync]
    
    customers = frappe.get_list("Customer",
        filters=filters, 
        fields=[
            "name", "customer_name", "customer_name_ar", "mobile_no",
            "email_id", "customer_group", "territory", "modified"
        ],
        limit=100,
        order_by="modified desc"
    )
    
    return {
        "data_type": "customers",
        "records": customers,
        "count": len(customers),
        "last_sync": frappe.utils.now(),
        "has_more": len(customers) == 100
    }


def sync_vehicles(last_sync: Optional[str] = None) -> Dict[str, Any]:
    """Sync vehicles for Frontend V2"""
    
    filters = {"disabled": 0}
    
    if last_sync:
        filters["modified"] = [">", last_sync]
    
    vehicles = frappe.get_list("Vehicle",
        filters=filters,
        fields=[
            "name", "license_plate", "license_plate_ar", "make", "model",
            "year", "vin", "engine_no", "owner", "current_mileage", "modified"
        ],
        limit=100,
        order_by="modified desc"  
    )
    
    return {
        "data_type": "vehicles", 
        "records": vehicles,
        "count": len(vehicles),
        "last_sync": frappe.utils.now(),
        "has_more": len(vehicles) == 100
    }


def sync_technicians(last_sync: Optional[str] = None) -> Dict[str, Any]:
    """Sync technicians for Frontend V2"""
    
    filters = {"status": "Active"}
    
    if last_sync:
        filters["modified"] = [">", last_sync]
    
    technicians = frappe.get_list("Technician",
        filters=filters,
        fields=[
            "name", "employee_id", "technician_name", "technician_name_ar", 
            "department", "skill_level", "hourly_rate", "phone", "modified"
        ],
        limit=100,
        order_by="modified desc"
    )
    
    return {
        "data_type": "technicians",
        "records": technicians, 
        "count": len(technicians),
        "last_sync": frappe.utils.now(),
        "has_more": len(technicians) == 100
    }


def sync_workshop_profile(last_sync: Optional[str] = None) -> Dict[str, Any]:
    """Sync workshop profile for Frontend V2"""
    
    workshop_profile = frappe.get_list("Workshop Profile",
        filters={"disabled": 0},
        fields=[
            "name", "workshop_name", "workshop_name_ar", "business_license",
            "phone_number", "address", "address_ar", "workshop_logo",
            "primary_color", "secondary_color", "modified"
        ],
        limit=1
    )
    
    return {
        "data_type": "workshop_profile",
        "records": workshop_profile,
        "count": len(workshop_profile),
        "last_sync": frappe.utils.now(),
        "has_more": False
    }


@frappe.whitelist(allow_guest=False)
def get_migration_status() -> Dict[str, Any]:
    """Get the current migration status between frontends"""
    
    # Count records in each module
    modules_status = {}
    
    core_doctypes = [
        ("Service Order", "service_orders"),
        ("Customer", "customers"), 
        ("Vehicle", "vehicles"),
        ("Technician", "technicians"),
        ("Workshop Profile", "workshop_profile")
    ]
    
    for doctype, key in core_doctypes:
        try:
            count = frappe.db.count(doctype)
            modules_status[key] = {
                "doctype": doctype,
                "total_records": count,
                "last_sync": frappe.db.get_value(doctype, {"docstatus": ["!=", 2]}, "max(modified)"),
                "status": "ready" if count > 0 else "empty"
            }
        except Exception as e:
            modules_status[key] = {
                "doctype": doctype,
                "total_records": 0,
                "error": str(e),
                "status": "error"
            }
    
    return {
        "frontend_v2_enabled": get_v2_feature_flag(),
        "user_preference": get_frontend_preference()["frontend_preference"],
        "modules": modules_status,
        "migration_complete": all(m["status"] in ["ready", "empty"] for m in modules_status.values()),
        "assets_available": {
            "main_js": frappe.local.conf.get("developer_mode", 0) == 0,
            "service_worker": True,
            "offline_support": True
        }
    }


@frappe.whitelist(allow_guest=False) 
def create_v2_user_session() -> Dict[str, Any]:
    """Create session data for Frontend V2"""
    
    if not get_v2_feature_flag():
        frappe.throw(_("Frontend V2 is not enabled"))
    
    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)
    
    # Get user roles and permissions
    user_roles = frappe.get_roles(user)
    
    # Get workshop context
    workshop_context = None
    if "Workshop Manager" in user_roles or "Workshop Technician" in user_roles:
        workshop_profiles = frappe.get_list("Workshop Profile", 
            filters={"disabled": 0}, 
            fields=["name", "workshop_name", "workshop_name_ar"],
            limit=1
        )
        workshop_context = workshop_profiles[0] if workshop_profiles else None
    
    return {
        "user": {
            "name": user,
            "full_name": user_doc.full_name,
            "email": user_doc.email,
            "mobile_no": user_doc.mobile_no,
            "language": user_doc.language or "en",
            "roles": user_roles
        },
        "workshop": workshop_context,
        "session": {
            "session_id": frappe.session.sid,
            "created": frappe.utils.now(),
            "csrf_token": frappe.local.csrf_token
        },
        "settings": {
            "currency": "OMR",
            "date_format": "dd/mm/yyyy", 
            "time_format": "24 hour",
            "language": user_doc.language or "en",
            "rtl_enabled": (user_doc.language or "en") == "ar"
        }
    } 