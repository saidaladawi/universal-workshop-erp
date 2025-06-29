import frappe
from frappe import _


def get_context(context):
    """Get context for compatibility matrix page"""
    
    # Get available vehicle makes for filter dropdown
    vehicle_makes = frappe.db.sql("""
        SELECT DISTINCT vehicle_make as name, vehicle_make as label
        FROM `tabItem`
        WHERE vehicle_make IS NOT NULL 
        AND vehicle_make != ''
        AND disabled = 0
        ORDER BY vehicle_make
    """, as_dict=True)
    
    # Get part categories for filter dropdown
    part_categories = frappe.db.sql("""
        SELECT DISTINCT part_category as name, part_category as label
        FROM `tabItem`
        WHERE part_category IS NOT NULL 
        AND part_category != ''
        AND disabled = 0
        ORDER BY part_category
    """, as_dict=True)
    
    # Get brands for additional filtering
    brands = frappe.db.sql("""
        SELECT DISTINCT brand as name, brand as label
        FROM `tabItem`
        WHERE brand IS NOT NULL 
        AND brand != ''
        AND disabled = 0
        ORDER BY brand
    """, as_dict=True)
    
    # Get compatibility statistics
    compatibility_stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_parts,
            COUNT(CASE WHEN vehicle_make IS NOT NULL AND vehicle_make != '' THEN 1 END) as vehicle_specific_parts,
            COUNT(CASE WHEN vehicle_make IS NULL OR vehicle_make = '' THEN 1 END) as universal_parts,
            COUNT(DISTINCT vehicle_make) as supported_makes,
            COUNT(DISTINCT part_category) as part_categories
        FROM `tabItem`
        WHERE disabled = 0 AND is_stock_item = 1
    """, as_dict=True)
    
    context.update({
        "title": _("Parts Compatibility Matrix"),
        "vehicle_makes": vehicle_makes,
        "part_categories": part_categories,
        "brands": brands,
        "compatibility_stats": compatibility_stats[0] if compatibility_stats else {},
        "show_sidebar": False,
        "page_length": 20,
        
        # Localization
        "show_language_toggle": True,
        "default_language": frappe.local.lang or "en",
        
        # API endpoints for frontend
        "api_endpoints": {
            "search_compatible_parts": "/api/method/universal_workshop.parts_inventory.compatibility_matrix.search_compatible_parts",
            "get_part_compatibility": "/api/method/universal_workshop.parts_inventory.compatibility_matrix.get_part_compatibility",
            "decode_vin": "/api/method/universal_workshop.parts_inventory.api.decode_vehicle_vin",
            "check_fitment": "/api/method/universal_workshop.parts_inventory.api.check_part_vehicle_fitment",
            "get_vehicle_specs": "/api/method/universal_workshop.parts_inventory.api.get_vehicle_specifications",
            "get_fitment_recommendations": "/api/method/universal_workshop.parts_inventory.api.get_fitment_recommendations"
        },
        
        # Feature flags
        "features": {
            "vin_decoder": True,
            "advanced_fitment": True,
            "export_results": True,
            "mobile_responsive": True,
            "arabic_support": True
        }
    })
    
    return context


def get_vehicle_models(make):
    """Get vehicle models for a specific make"""
    models = frappe.db.sql("""
        SELECT DISTINCT vehicle_model as name, vehicle_model as label
        FROM `tabItem`
        WHERE vehicle_make = %s
        AND vehicle_model IS NOT NULL 
        AND vehicle_model != ''
        AND disabled = 0
        ORDER BY vehicle_model
    """, (make,), as_dict=True)
    
    return models


def get_compatibility_summary():
    """Get overall compatibility summary for dashboard"""
    summary = frappe.db.sql("""
        SELECT 
            vehicle_make,
            COUNT(*) as part_count,
            COUNT(DISTINCT part_category) as category_count,
            AVG(standard_rate) as avg_price,
            MIN(vehicle_year_from) as year_from,
            MAX(vehicle_year_to) as year_to
        FROM `tabItem`
        WHERE vehicle_make IS NOT NULL 
        AND vehicle_make != ''
        AND disabled = 0
        AND is_stock_item = 1
        GROUP BY vehicle_make
        ORDER BY part_count DESC
        LIMIT 20
    """, as_dict=True)
    
    return summary
