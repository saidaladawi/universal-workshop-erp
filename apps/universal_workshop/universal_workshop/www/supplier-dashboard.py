"""
Supplier Dashboard Web Page Controller
Handles the backend logic for the supplier dashboard web interface
"""

import frappe
from frappe import _
import json


def get_context(context):
    """Get context for supplier dashboard page"""
    context.no_cache = 1
    context.show_sidebar = True
    
    # Set page metadata
    context.title = _("Supplier Dashboard - Universal Workshop")
    context.description = _("Comprehensive supplier performance tracking and automated purchase order management")
    
    # Get initial data
    context.suppliers = get_supplier_summary()
    context.reorder_stats = get_reorder_statistics()
    context.performance_summary = get_performance_summary()
    
    # Get user preferences
    user = frappe.get_doc("User", frappe.session.user)
    context.preferred_language = getattr(user, 'language', 'en')
    
    # Add theme support
    context.theme_colors = get_theme_colors()
    
    return context


def get_supplier_summary():
    """Get summary of suppliers"""
    try:
        suppliers = frappe.get_all(
            "Supplier",
            filters={"disabled": 0},
            fields=["name", "supplier_name", "supplier_group", "country", "default_currency"],
            order_by="supplier_name",
            limit=10
        )
        
        return suppliers
        
    except Exception as e:
        frappe.log_error(f"Error getting supplier summary: {str(e)}")
        return []


def get_reorder_statistics():
    """Get reorder statistics"""
    try:
        # Get count of items needing reorder
        reorder_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON b.item_code = i.name
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND i.reorder_level > 0
            AND COALESCE(b.actual_qty, 0) <= i.reorder_level
        """)[0][0]
        
        # Get critical items (out of stock)
        critical_count = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON b.item_code = i.name
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND COALESCE(b.actual_qty, 0) = 0
        """)[0][0]
        
        return {
            "reorder_needed": reorder_count,
            "critical_items": critical_count,
            "total_items": frappe.db.count("Item", {"disabled": 0, "is_stock_item": 1})
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting reorder statistics: {str(e)}")
        return {"reorder_needed": 0, "critical_items": 0, "total_items": 0}


def get_performance_summary():
    """Get overall performance summary"""
    try:
        # Get recent purchase orders
        po_summary = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(grand_total) as total_value,
                AVG(CASE WHEN status IN ('Completed', 'Closed') THEN 1 ELSE 0 END) * 100 as completion_rate
            FROM `tabPurchase Order`
            WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
        """, as_dict=True)
        
        summary = po_summary[0] if po_summary else {}
        
        return {
            "recent_orders": summary.get("total_orders", 0),
            "total_value": summary.get("total_value", 0),
            "completion_rate": round(summary.get("completion_rate", 0), 1),
            "active_suppliers": frappe.db.count("Supplier", {"disabled": 0})
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting performance summary: {str(e)}")
        return {}


def get_theme_colors():
    """Get current theme colors"""
    try:
        from universal_workshop.themes.api import get_theme_colors
        return get_theme_colors()
    except Exception as e:
        frappe.log_error(f"Error getting theme colors: {str(e)}")
        return {
            "primary_color": "#007bff",
            "secondary_color": "#6c757d",
            "success_color": "#28a745"
        }


@frappe.whitelist()
def get_supplier_performance_metrics():
    """Get detailed supplier performance metrics for the dashboard"""
    try:
        # Get all suppliers with recent activity
        suppliers = frappe.db.sql("""
            SELECT 
                s.name as supplier,
                s.supplier_name,
                s.supplier_group,
                s.country,
                COUNT(po.name) as total_orders,
                COALESCE(SUM(po.grand_total), 0) as total_value,
                AVG(DATEDIFF(po.delivery_date, po.transaction_date)) as avg_lead_time,
                AVG(CASE WHEN po.status IN ('Completed', 'Closed') THEN 100 ELSE 0 END) as delivery_performance
            FROM `tabSupplier` s
            LEFT JOIN `tabPurchase Order` po ON po.supplier = s.name 
                AND po.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            WHERE s.disabled = 0
            GROUP BY s.name
            ORDER BY total_orders DESC, total_value DESC
        """, as_dict=True)
        
        # Enhance with calculated metrics
        enhanced_suppliers = []
        for supplier in suppliers:
            # Calculate quality score (simplified)
            quality_score = calculate_quality_score(supplier.supplier)
            
            # Calculate overall performance score
            delivery_score = supplier.delivery_performance or 0
            lead_time_score = min(100, (7 / max(1, supplier.avg_lead_time or 7)) * 100) if supplier.avg_lead_time else 100
            
            overall_score = (delivery_score * 0.4) + (quality_score * 0.3) + (lead_time_score * 0.3)
            
            enhanced_suppliers.append({
                **supplier,
                "quality_score": quality_score,
                "lead_time_score": lead_time_score,
                "overall_score": overall_score,
                "active": supplier.total_orders > 0
            })
        
        return {
            "success": True,
            "suppliers": enhanced_suppliers
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting supplier performance metrics: {str(e)}")
        return {"success": False, "error": str(e)}


def calculate_quality_score(supplier):
    """Calculate quality score for supplier (simplified implementation)"""
    try:
        # This would typically be based on quality inspection data
        # For now, return a calculated score based on return/complaint rates
        
        # Get recent purchase receipts and any quality issues
        quality_data = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_receipts,
                SUM(CASE WHEN status = 'Rejected' THEN 1 ELSE 0 END) as rejected_receipts
            FROM `tabPurchase Receipt`
            WHERE supplier = %s
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        """, supplier, as_dict=True)
        
        if quality_data and quality_data[0].total_receipts > 0:
            rejection_rate = (quality_data[0].rejected_receipts / quality_data[0].total_receipts) * 100
            quality_score = max(0, 100 - (rejection_rate * 10))  # Penalty for rejections
        else:
            quality_score = 85  # Default score for suppliers with no quality data
        
        return round(quality_score, 1)
        
    except Exception as e:
        frappe.log_error(f"Error calculating quality score: {str(e)}")
        return 80


@frappe.whitelist()
def get_reorder_dashboard_data():
    """Get comprehensive reorder data for dashboard"""
    try:
        # Get items needing reorder with detailed information
        reorder_items = frappe.db.sql("""
            SELECT 
                i.name as item_code,
                i.item_name,
                i.item_group,
                i.reorder_level,
                i.min_stock_level,
                i.preferred_supplier,
                i.lead_time_days,
                i.standard_rate,
                i.stock_uom,
                COALESCE(SUM(b.actual_qty), 0) as current_stock,
                COALESCE(SUM(b.reserved_qty), 0) as reserved_stock
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON b.item_code = i.name
            WHERE i.disabled = 0 
            AND i.is_stock_item = 1
            AND i.reorder_level > 0
            GROUP BY i.name
            HAVING current_stock <= i.reorder_level
            ORDER BY 
                CASE WHEN current_stock = 0 THEN 0 ELSE 1 END,
                (i.reorder_level - current_stock) DESC
            LIMIT 50
        """, as_dict=True)
        
        # Enhance with additional data
        enhanced_items = []
        for item in reorder_items:
            # Calculate recommended order quantity
            recommended_qty = calculate_recommended_quantity(
                item.item_code, 
                item.current_stock, 
                item.reorder_level
            )
            
            # Get supplier information
            supplier_info = get_supplier_info(item.item_code, item.preferred_supplier)
            
            # Determine urgency
            urgency = determine_urgency(item.current_stock, item.reorder_level)
            
            # Calculate estimated cost
            supplier_rate = supplier_info.get("rate", item.standard_rate) or 0
            estimated_cost = recommended_qty * supplier_rate
            
            enhanced_items.append({
                **item,
                "recommended_qty": recommended_qty,
                "supplier_info": supplier_info,
                "urgency_level": urgency,
                "estimated_cost": estimated_cost,
                "available_stock": item.current_stock - item.reserved_stock
            })
        
        # Calculate summary statistics
        total_estimated_cost = sum([item["estimated_cost"] for item in enhanced_items])
        urgency_counts = {}
        for item in enhanced_items:
            urgency = item["urgency_level"]
            urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
        
        return {
            "success": True,
            "items": enhanced_items,
            "summary": {
                "total_items": len(enhanced_items),
                "total_estimated_cost": total_estimated_cost,
                "urgency_breakdown": urgency_counts,
                "critical_items": urgency_counts.get("Critical", 0),
                "high_priority": urgency_counts.get("High", 0)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting reorder dashboard data: {str(e)}")
        return {"success": False, "error": str(e)}


def calculate_recommended_quantity(item_code, current_stock, reorder_level):
    """Calculate recommended order quantity"""
    try:
        # Get average consumption over last 3 months
        consumption_data = frappe.db.sql("""
            SELECT AVG(ABS(actual_qty)) as avg_consumption
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            AND actual_qty < 0
        """, item_code)
        
        avg_consumption = consumption_data[0][0] if consumption_data and consumption_data[0][0] else 1
        
        # Calculate based on consumption and safety stock
        lead_time_days = frappe.db.get_value("Item", item_code, "lead_time_days") or 7
        safety_stock = (avg_consumption / 30) * lead_time_days  # Lead time consumption
        
        # Target stock = reorder level + safety stock
        target_stock = reorder_level + safety_stock
        recommended_qty = max(target_stock - current_stock, avg_consumption)
        
        return max(1, round(recommended_qty))
        
    except Exception as e:
        frappe.log_error(f"Error calculating recommended quantity: {str(e)}")
        return max(1, reorder_level - current_stock)


def get_supplier_info(item_code, preferred_supplier=None):
    """Get supplier information for item"""
    try:
        if preferred_supplier:
            supplier_data = frappe.db.get_value(
                "Item Supplier",
                {"parent": item_code, "supplier": preferred_supplier},
                ["supplier_part_no", "lead_time_days", "min_order_qty"],
                as_dict=True
            )
        else:
            supplier_data = frappe.db.get_value(
                "Item Supplier",
                {"parent": item_code},
                ["supplier", "supplier_part_no", "lead_time_days", "min_order_qty"],
                as_dict=True
            )
        
        if supplier_data:
            # Get supplier price
            supplier = preferred_supplier or supplier_data.get("supplier")
            if supplier:
                rate = get_supplier_rate(item_code, supplier)
                supplier_data["rate"] = rate
        
        return supplier_data or {}
        
    except Exception as e:
        frappe.log_error(f"Error getting supplier info: {str(e)}")
        return {}


def get_supplier_rate(item_code, supplier):
    """Get supplier-specific rate for item"""
    try:
        # Check supplier-specific price list
        supplier_price_list = frappe.db.get_value("Supplier", supplier, "default_price_list")
        
        if supplier_price_list:
            rate = frappe.db.get_value(
                "Item Price",
                {"item_code": item_code, "price_list": supplier_price_list},
                "price_list_rate"
            )
            if rate:
                return rate
        
        # Check Item Supplier table
        supplier_rate = frappe.db.get_value(
            "Item Supplier",
            {"parent": item_code, "supplier": supplier},
            "price"
        )
        if supplier_rate:
            return supplier_rate
        
        # Fallback to standard rate
        return frappe.db.get_value("Item", item_code, "standard_rate") or 0
        
    except Exception as e:
        frappe.log_error(f"Error getting supplier rate: {str(e)}")
        return 0


def determine_urgency(current_stock, reorder_level):
    """Determine urgency level based on stock"""
    if current_stock <= 0:
        return "Critical"
    elif current_stock <= (reorder_level * 0.3):
        return "High"
    elif current_stock <= (reorder_level * 0.7):
        return "Medium"
    else:
        return "Low"
