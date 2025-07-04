"""
Supplier Integration Module
Handles automated supplier management, purchase order generation, and supplier performance tracking
"""

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, flt, cint
from datetime import datetime, timedelta
import json


@frappe.whitelist()
def create_auto_purchase_order(items_data, supplier=None, delivery_date=None):
    """Create automated purchase order based on reorder points and stock requirements"""
    try:
        if isinstance(items_data, str):
            items_data = json.loads(items_data)
        
        if not items_data:
            return {"success": False, "message": _("No items provided for purchase order")}
        
        # Group items by supplier if not specified
        if not supplier:
            supplier_groups = group_items_by_preferred_supplier(items_data)
        else:
            supplier_groups = {supplier: items_data}
        
        purchase_orders = []
        
        for supplier_name, items in supplier_groups.items():
            if not supplier_name:
                continue
                
            # Create purchase order
            po = frappe.new_doc("Purchase Order")
            po.supplier = supplier_name
            po.transaction_date = nowdate()
            po.schedule_date = delivery_date or add_days(nowdate(), 7)
            po.company = frappe.defaults.get_user_default("Company")
            
            # Set supplier details
            supplier_doc = frappe.get_doc("Supplier", supplier_name)
            po.supplier_name = supplier_doc.supplier_name
            po.currency = supplier_doc.default_currency or frappe.defaults.get_global_default("currency")
            
            # Add items
            total_amount = 0
            for item_data in items:
                item_code = item_data.get("item_code")
                quantity = flt(item_data.get("quantity", 1))
                
                # Get item details
                item = frappe.get_doc("Item", item_code)
                
                # Get supplier price
                supplier_price = get_supplier_price(item_code, supplier_name)
                
                # Add to purchase order
                po.append("items", {
                    "item_code": item_code,
                    "item_name": item.item_name,
                    "description": item.description,
                    "qty": quantity,
                    "uom": item.stock_uom,
                    "rate": supplier_price,
                    "amount": quantity * supplier_price,
                    "schedule_date": po.schedule_date,
                    "warehouse": get_default_warehouse_for_item(item_code)
                })
                
                total_amount += quantity * supplier_price
            
            # Set totals
            po.run_method("calculate_taxes_and_totals")
            
            # Add workflow and approval logic
            if total_amount > get_purchase_approval_limit():
                po.workflow_state = "Pending Approval"
            else:
                po.workflow_state = "Draft"
            
            # Insert purchase order
            po.insert()
            
            # Submit if auto-approval is enabled and under limit
            if should_auto_submit_po(total_amount):
                po.submit()
            
            purchase_orders.append({
                "name": po.name,
                "supplier": supplier_name,
                "total_amount": total_amount,
                "items_count": len(items),
                "status": po.workflow_state
            })
        
        return {
            "success": True,
            "message": _("Created {0} purchase order(s)").format(len(purchase_orders)),
            "purchase_orders": purchase_orders
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating auto purchase order: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def get_reorder_recommendations():
    """Get items that need reordering based on stock levels and reorder points"""
    try:
        # Query for items below reorder level
        reorder_items = frappe.db.sql("""
            SELECT 
                i.name as item_code,
                i.item_name,
                i.item_group,
                i.reorder_level,
                i.min_stock_level,
                COALESCE(SUM(b.actual_qty), 0) as current_stock,
                i.preferred_supplier,
                i.lead_time_days,
                i.standard_rate
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
        """, as_dict=True)
        
        # Enhance with supplier information and recommended quantities
        recommendations = []
        for item in reorder_items:
            # Calculate recommended order quantity
            recommended_qty = calculate_recommended_order_quantity(
                item.item_code, 
                item.current_stock, 
                item.reorder_level,
                item.min_stock_level
            )
            
            # Get supplier information
            supplier_info = get_item_supplier_info(item.item_code, item.preferred_supplier)
            
            # Get recent consumption data
            consumption_data = get_item_consumption_data(item.item_code)
            
            recommendation = {
                **item,
                "recommended_qty": recommended_qty,
                "supplier_info": supplier_info,
                "consumption_data": consumption_data,
                "urgency_level": get_urgency_level(item.current_stock, item.reorder_level),
                "estimated_cost": recommended_qty * (supplier_info.get("rate", item.standard_rate) or 0)
            }
            
            recommendations.append(recommendation)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "total_items": len(recommendations),
            "total_estimated_cost": sum([r["estimated_cost"] for r in recommendations])
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting reorder recommendations: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_supplier_performance_dashboard():
    """Get comprehensive supplier performance metrics"""
    try:
        # Get all active suppliers
        suppliers = frappe.get_all(
            "Supplier",
            filters={"disabled": 0},
            fields=["name", "supplier_name", "supplier_group", "country"]
        )
        
        supplier_metrics = []
        
        for supplier in suppliers:
            metrics = calculate_supplier_metrics(supplier.name)
            metrics.update({
                "supplier_name": supplier.supplier_name,
                "supplier_group": supplier.supplier_group,
                "country": supplier.country
            })
            supplier_metrics.append(metrics)
        
        # Sort by overall performance score
        supplier_metrics.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        return {
            "success": True,
            "suppliers": supplier_metrics,
            "summary": {
                "total_suppliers": len(suppliers),
                "active_suppliers": len([s for s in supplier_metrics if s.get("active", False)]),
                "avg_delivery_performance": sum([s.get("delivery_performance", 0) for s in supplier_metrics]) / len(supplier_metrics) if supplier_metrics else 0,
                "avg_quality_score": sum([s.get("quality_score", 0) for s in supplier_metrics]) / len(supplier_metrics) if supplier_metrics else 0
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting supplier performance: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def create_supplier_quotation_request(items_data, suppliers=None, deadline=None):
    """Create supplier quotation requests for multiple suppliers"""
    try:
        if isinstance(items_data, str):
            items_data = json.loads(items_data)
        
        if isinstance(suppliers, str):
            suppliers = json.loads(suppliers)
        
        if not suppliers:
            # Get default suppliers for the items
            suppliers = get_recommended_suppliers_for_items(items_data)
        
        quotation_requests = []
        
        for supplier in suppliers:
            # Create Request for Quotation
            rfq = frappe.new_doc("Request for Quotation")
            rfq.transaction_date = nowdate()
            rfq.schedule_date = deadline or add_days(nowdate(), 7)
            rfq.company = frappe.defaults.get_user_default("Company")
            
            # Add supplier
            rfq.append("suppliers", {
                "supplier": supplier,
                "supplier_name": frappe.db.get_value("Supplier", supplier, "supplier_name")
            })
            
            # Add items
            for item_data in items_data:
                item_code = item_data.get("item_code")
                quantity = flt(item_data.get("quantity", 1))
                
                item = frappe.get_doc("Item", item_code)
                
                rfq.append("items", {
                    "item_code": item_code,
                    "item_name": item.item_name,
                    "description": item.description,
                    "qty": quantity,
                    "uom": item.stock_uom,
                    "schedule_date": rfq.schedule_date,
                    "warehouse": get_default_warehouse_for_item(item_code)
                })
            
            rfq.insert()
            
            quotation_requests.append({
                "name": rfq.name,
                "supplier": supplier,
                "items_count": len(items_data),
                "deadline": rfq.schedule_date
            })
        
        return {
            "success": True,
            "message": _("Created {0} quotation request(s)").format(len(quotation_requests)),
            "quotation_requests": quotation_requests
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating quotation requests: {str(e)}")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def compare_supplier_quotations(rfq_name):
    """Compare quotations from different suppliers for the same RFQ"""
    try:
        # Get all supplier quotations for this RFQ
        quotations = frappe.get_all(
            "Supplier Quotation",
            filters={"request_for_quotation": rfq_name},
            fields=["name", "supplier", "supplier_name", "grand_total", "valid_till", "status"]
        )
        
        if not quotations:
            return {"success": False, "message": _("No quotations found for this RFQ")}
        
        # Get detailed comparison
        comparison_data = []
        
        for quotation in quotations:
            # Get quotation items
            items = frappe.get_all(
                "Supplier Quotation Item",
                filters={"parent": quotation.name},
                fields=["item_code", "item_name", "qty", "rate", "amount"]
            )
            
            # Calculate metrics
            total_cost = quotation.grand_total
            delivery_score = get_supplier_delivery_score(quotation.supplier)
            quality_score = get_supplier_quality_score(quotation.supplier)
            
            # Calculate overall score
            cost_score = 100 - ((total_cost / min([q.grand_total for q in quotations])) - 1) * 100
            overall_score = (cost_score * 0.4) + (delivery_score * 0.3) + (quality_score * 0.3)
            
            comparison_data.append({
                "quotation_name": quotation.name,
                "supplier": quotation.supplier,
                "supplier_name": quotation.supplier_name,
                "total_cost": total_cost,
                "valid_till": quotation.valid_till,
                "status": quotation.status,
                "items": items,
                "delivery_score": delivery_score,
                "quality_score": quality_score,
                "cost_score": cost_score,
                "overall_score": overall_score
            })
        
        # Sort by overall score
        comparison_data.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return {
            "success": True,
            "rfq_name": rfq_name,
            "quotations": comparison_data,
            "best_quotation": comparison_data[0] if comparison_data else None
        }
        
    except Exception as e:
        frappe.log_error(f"Error comparing quotations: {str(e)}")
        return {"success": False, "message": str(e)}


# Helper Functions

def group_items_by_preferred_supplier(items_data):
    """Group items by their preferred supplier"""
    supplier_groups = {}
    
    for item_data in items_data:
        item_code = item_data.get("item_code")
        
        # Get preferred supplier
        preferred_supplier = frappe.db.get_value("Item", item_code, "preferred_supplier")
        
        if not preferred_supplier:
            # Get first supplier from Item Supplier table
            supplier_data = frappe.db.get_value(
                "Item Supplier", 
                {"parent": item_code}, 
                "supplier"
            )
            preferred_supplier = supplier_data or "Default Supplier"
        
        if preferred_supplier not in supplier_groups:
            supplier_groups[preferred_supplier] = []
        
        supplier_groups[preferred_supplier].append(item_data)
    
    return supplier_groups


def get_supplier_price(item_code, supplier):
    """Get supplier-specific price for an item"""
    # First check Item Price with supplier-specific price list
    supplier_price_list = frappe.db.get_value("Supplier", supplier, "default_price_list")
    
    if supplier_price_list:
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "price_list": supplier_price_list},
            "price_list_rate"
        )
        if price:
            return price
    
    # Check Item Supplier table
    supplier_price = frappe.db.get_value(
        "Item Supplier",
        {"parent": item_code, "supplier": supplier},
        "price"
    )
    if supplier_price:
        return supplier_price
    
    # Fallback to standard rate
    return frappe.db.get_value("Item", item_code, "standard_rate") or 0


def get_default_warehouse_for_item(item_code):
    """Get default warehouse for item"""
    # Check item default warehouse
    default_warehouse = frappe.db.get_value("Item", item_code, "default_warehouse")
    if default_warehouse:
        return default_warehouse
    
    # Fallback to company default
    company = frappe.defaults.get_user_default("Company")
    return frappe.db.get_value("Company", company, "default_warehouse") or "Main Store - Workshop"


def get_purchase_approval_limit():
    """Get purchase approval limit from settings"""
    # This would typically come from Company settings or User permissions
    return flt(frappe.db.get_single_value("Buying Settings", "auto_approval_limit") or 10000)


def should_auto_submit_po(total_amount):
    """Determine if purchase order should be auto-submitted"""
    auto_submit_limit = flt(frappe.db.get_single_value("Buying Settings", "auto_submit_limit") or 5000)
    return total_amount <= auto_submit_limit


def calculate_recommended_order_quantity(item_code, current_stock, reorder_level, min_stock_level):
    """Calculate recommended order quantity based on consumption patterns"""
    # Get average monthly consumption
    monthly_consumption = get_average_monthly_consumption(item_code)
    
    # Get lead time
    lead_time_days = frappe.db.get_value("Item", item_code, "lead_time_days") or 7
    
    # Calculate safety stock
    safety_stock = (monthly_consumption / 30) * lead_time_days
    
    # Calculate recommended quantity
    target_stock = max(reorder_level * 2, min_stock_level + safety_stock)
    recommended_qty = max(target_stock - current_stock, monthly_consumption)
    
    return max(1, recommended_qty)


def get_average_monthly_consumption(item_code):
    """Get average monthly consumption for an item"""
    try:
        # Get consumption data from last 3 months
        consumption = frappe.db.sql("""
            SELECT AVG(monthly_consumption) as avg_consumption
            FROM (
                SELECT 
                    MONTH(posting_date) as month,
                    SUM(actual_qty) as monthly_consumption
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s
                AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
                AND actual_qty < 0
                GROUP BY MONTH(posting_date)
            ) as monthly_data
        """, item_code)
        
        return abs(consumption[0][0]) if consumption and consumption[0][0] else 1
        
    except:
        return 1


def get_item_supplier_info(item_code, preferred_supplier=None):
    """Get supplier information for an item"""
    try:
        if preferred_supplier:
            supplier_info = frappe.db.get_value(
                "Item Supplier",
                {"parent": item_code, "supplier": preferred_supplier},
                ["supplier_part_no", "lead_time_days", "price"],
                as_dict=True
            )
        else:
            supplier_info = frappe.db.get_value(
                "Item Supplier",
                {"parent": item_code},
                ["supplier", "supplier_part_no", "lead_time_days", "price"],
                as_dict=True
            )
        
        return supplier_info or {}
        
    except:
        return {}


def get_item_consumption_data(item_code):
    """Get recent consumption data for an item"""
    try:
        consumption = frappe.db.sql("""
            SELECT 
                DATE(posting_date) as date,
                ABS(actual_qty) as consumed_qty,
                voucher_type,
                voucher_no
            FROM `tabStock Ledger Entry`
            WHERE item_code = %s
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            AND actual_qty < 0
            ORDER BY posting_date DESC
            LIMIT 10
        """, item_code, as_dict=True)
        
        return consumption
        
    except:
        return []


def get_urgency_level(current_stock, reorder_level):
    """Determine urgency level based on stock levels"""
    if current_stock <= 0:
        return "Critical"
    elif current_stock <= (reorder_level * 0.5):
        return "High"
    elif current_stock <= reorder_level:
        return "Medium"
    else:
        return "Low"


def calculate_supplier_metrics(supplier):
    """Calculate comprehensive performance metrics for a supplier"""
    try:
        # Get purchase orders from last 12 months
        po_data = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_orders,
                SUM(grand_total) as total_value,
                AVG(DATEDIFF(delivery_date, transaction_date)) as avg_lead_time,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_orders
            FROM `tabPurchase Order`
            WHERE supplier = %s
            AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
        """, supplier, as_dict=True)
        
        if not po_data or not po_data[0].total_orders:
            return {
                "supplier": supplier,
                "active": False,
                "total_orders": 0,
                "total_value": 0,
                "delivery_performance": 0,
                "quality_score": 0,
                "overall_score": 0
            }
        
        metrics = po_data[0]
        
        # Calculate delivery performance
        delivery_performance = (metrics.completed_orders / metrics.total_orders) * 100 if metrics.total_orders > 0 else 0
        
        # Get quality score (simplified - would be based on quality inspections)
        quality_score = get_supplier_quality_score(supplier)
        
        # Calculate overall score
        overall_score = (delivery_performance * 0.5) + (quality_score * 0.3) + (min(100, (12 / max(1, metrics.avg_lead_time)) * 100) * 0.2)
        
        return {
            "supplier": supplier,
            "active": True,
            "total_orders": metrics.total_orders,
            "total_value": metrics.total_value,
            "avg_lead_time": metrics.avg_lead_time,
            "delivery_performance": delivery_performance,
            "quality_score": quality_score,
            "overall_score": overall_score
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating supplier metrics: {str(e)}")
        return {
            "supplier": supplier,
            "active": False,
            "error": str(e)
        }


def get_supplier_delivery_score(supplier):
    """Get delivery performance score for a supplier"""
    try:
        # This would typically be calculated from delivery data
        # For now, return a calculated score based on purchase order completion
        completion_rate = frappe.db.sql("""
            SELECT 
                AVG(CASE WHEN status IN ('Completed', 'Closed') THEN 100 ELSE 0 END) as score
            FROM `tabPurchase Order`
            WHERE supplier = %s
            AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        """, supplier)
        
        return completion_rate[0][0] if completion_rate and completion_rate[0][0] else 75
        
    except:
        return 75


def get_supplier_quality_score(supplier):
    """Get quality score for a supplier"""
    try:
        # This would typically be calculated from quality inspection data
        # For now, return a default score
        return 85  # Would be calculated from actual quality data
        
    except:
        return 80


def get_recommended_suppliers_for_items(items_data):
    """Get recommended suppliers for a list of items"""
    suppliers = set()
    
    for item_data in items_data:
        item_code = item_data.get("item_code")
        
        # Get all suppliers for this item
        item_suppliers = frappe.get_all(
            "Item Supplier",
            filters={"parent": item_code},
            fields=["supplier"]
        )
        
        for supplier_info in item_suppliers:
            suppliers.add(supplier_info.supplier)
    
    return list(suppliers)[:5]  # Limit to top 5 suppliers
