"""
Universal Workshop ERP - Cache Utilities
Provides caching functions for improved performance
"""

import frappe
import json
from typing import Any, Optional

class WorkshopCache:
    """Workshop-specific caching utilities"""
    
    @staticmethod
    def get_service_catalog():
        """Get cached service catalog"""
        cache_key = "workshop:service_catalog"
        catalog = frappe.cache().get_value(cache_key)
        
        if not catalog:
            # Use fallback if Service Type doesn't exist yet
            try:
                catalog = frappe.get_all("Service Type", 
                    fields=["name", "service_name", "standard_rate", "category"],
                    filters={"disabled": 0}
                )
            except:
                # Fallback for development/testing
                catalog = [
                    {"name": "OIL_CHANGE", "service_name": "Oil Change", "standard_rate": 50, "category": "Maintenance"},
                    {"name": "BRAKE_SERVICE", "service_name": "Brake Service", "standard_rate": 150, "category": "Safety"},
                    {"name": "AC_SERVICE", "service_name": "AC Service", "standard_rate": 100, "category": "Comfort"}
                ]
            
            frappe.cache().set_value(cache_key, catalog, expires_in_sec=3600)
        
        return catalog
    
    @staticmethod
    def get_customer_summary(customer_id: str):
        """Get cached customer service summary"""
        cache_key = f"workshop:customer_summary:{customer_id}"
        summary = frappe.cache().get_value(cache_key)
        
        if not summary:
            try:
                summary = frappe.db.sql("""
                    SELECT 
                        COUNT(*) as total_services,
                        COALESCE(SUM(final_amount), 0) as total_spent,
                        MAX(service_date) as last_service_date
                    FROM `tabService Order`
                    WHERE customer = %s AND docstatus = 1
                """, (customer_id,), as_dict=True)
                
                if summary:
                    summary = summary[0]
                    frappe.cache().set_value(cache_key, summary, expires_in_sec=1800)
            except:
                # Fallback for development
                summary = {
                    "total_services": 0,
                    "total_spent": 0,
                    "last_service_date": None
                }
        
        return summary or {}
    
    @staticmethod
    def get_vehicle_history(vehicle_id: str):
        """Get cached vehicle service history summary"""
        cache_key = f"workshop:vehicle_history:{vehicle_id}"
        history = frappe.cache().get_value(cache_key)
        
        if not history:
            try:
                history = frappe.db.sql("""
                    SELECT 
                        COUNT(*) as service_count,
                        MAX(service_date) as last_service,
                        MAX(current_mileage) as last_mileage
                    FROM `tabService Order`
                    WHERE vehicle = %s AND docstatus = 1
                """, (vehicle_id,), as_dict=True)
                
                if history:
                    history = history[0]
                    frappe.cache().set_value(cache_key, history, expires_in_sec=1800)
            except:
                # Fallback for development
                history = {
                    "service_count": 0,
                    "last_service": None,
                    "last_mileage": 0
                }
        
        return history or {}
    
    @staticmethod
    def get_technician_workload(technician_id: str):
        """Get cached technician workload summary"""
        cache_key = f"workshop:technician_workload:{technician_id}"
        workload = frappe.cache().get_value(cache_key)
        
        if not workload:
            try:
                workload = frappe.db.sql("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        SUM(CASE WHEN priority = 'Urgent' THEN 1 ELSE 0 END) as urgent_count
                    FROM `tabService Order`
                    WHERE technician_assigned = %s
                    AND status IN ('Draft', 'Open', 'In Progress')
                    GROUP BY status
                """, (technician_id,), as_dict=True)
                
                frappe.cache().set_value(cache_key, workload, expires_in_sec=900)  # 15 minutes
            except:
                # Fallback for development
                workload = []
        
        return workload or []
    
    @staticmethod
    def get_workshop_dashboard_data():
        """Get cached workshop dashboard data"""
        cache_key = "workshop:dashboard_data"
        dashboard_data = frappe.cache().get_value(cache_key)
        
        if not dashboard_data:
            try:
                # Today's appointments
                today_appointments = frappe.db.count("Appointment", {
                    "appointment_date": frappe.utils.today()
                }) or 0
                
                # Pending service orders
                pending_services = frappe.db.count("Service Order", {
                    "status": ["in", ["Draft", "Open", "In Progress"]]
                }) or 0
                
                # Available technicians
                available_techs = frappe.db.count("Technician", {
                    "status": "Active"
                }) or 0
                
                dashboard_data = {
                    "today_appointments": today_appointments,
                    "pending_services": pending_services,
                    "available_technicians": available_techs,
                    "cache_timestamp": frappe.utils.now()
                }
                
                frappe.cache().set_value(cache_key, dashboard_data, expires_in_sec=300)  # 5 minutes
                
            except:
                # Fallback for development
                dashboard_data = {
                    "today_appointments": 0,
                    "pending_services": 0,
                    "available_technicians": 0,
                    "cache_timestamp": frappe.utils.now()
                }
        
        return dashboard_data
    
    @staticmethod
    def invalidate_customer_cache(customer_id: str):
        """Invalidate customer-related caches"""
        cache_keys = [
            f"workshop:customer_summary:{customer_id}",
            f"workshop:customer_vehicles:{customer_id}",
            "workshop:dashboard_data"
        ]
        
        for key in cache_keys:
            frappe.cache().delete_value(key)
    
    @staticmethod
    def invalidate_vehicle_cache(vehicle_id: str):
        """Invalidate vehicle-related caches"""
        cache_keys = [
            f"workshop:vehicle_history:{vehicle_id}",
            f"workshop:vehicle_summary:{vehicle_id}",
            "workshop:dashboard_data"
        ]
        
        for key in cache_keys:
            frappe.cache().delete_value(key)
    
    @staticmethod
    def invalidate_technician_cache(technician_id: str):
        """Invalidate technician-related caches"""
        cache_keys = [
            f"workshop:technician_workload:{technician_id}",
            "workshop:dashboard_data"
        ]
        
        for key in cache_keys:
            frappe.cache().delete_value(key)
    
    @staticmethod
    def invalidate_service_catalog_cache():
        """Invalidate service catalog cache"""
        frappe.cache().delete_value("workshop:service_catalog")
    
    @staticmethod
    def warm_cache():
        """Warm up frequently used caches"""
        try:
            # Warm service catalog
            WorkshopCache.get_service_catalog()
            
            # Warm dashboard data
            WorkshopCache.get_workshop_dashboard_data()
            
            # Get recent customers and warm their caches
            recent_customers = frappe.db.sql("""
                SELECT DISTINCT customer 
                FROM `tabService Order` 
                WHERE service_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                LIMIT 20
            """, as_dict=True)
            
            for customer in recent_customers:
                WorkshopCache.get_customer_summary(customer.get('customer'))
            
            frappe.log_error("Cache warmed successfully", "Cache Management")
            
        except Exception as e:
            frappe.log_error(f"Cache warming error: {str(e)}", "Cache Management")
    
    @staticmethod
    def get_cache_stats():
        """Get cache performance statistics"""
        try:
            # This would require Redis INFO command in real implementation
            stats = {
                "cache_enabled": bool(frappe.cache()),
                "estimated_entries": 100,  # Placeholder
                "estimated_hit_ratio": 0.85,  # Placeholder
                "cache_size_mb": 50,  # Placeholder
                "last_updated": frappe.utils.now()
            }
            
            return stats
        except Exception as e:
            return {"error": str(e)}
