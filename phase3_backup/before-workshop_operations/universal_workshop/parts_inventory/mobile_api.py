"""
Mobile Inventory API Endpoints
Provides REST API methods for the Progressive Web App mobile interface
"""

import frappe
from frappe import _
import json
from frappe.utils import flt, cint, getdate, now
from universal_workshop.license_management.license_validator import validate_license_for_operation


@frappe.whitelist()
def get_item_by_barcode(barcode):
    """
    Look up item details by barcode

    Args:
        barcode (str): The barcode to search for

    Returns:
        dict: Item details including stock information
    """
    try:
        # Validate license
        validate_license_for_operation("mobile_inventory_access")

        # Find item by barcode
        item_code = frappe.db.get_value("Item", {"barcode": barcode}, "name")

        if not item_code:
            # Try custom barcode field if exists
            item_code = frappe.db.get_value("Item", {"custom_barcode": barcode}, "name")

        if not item_code:
            return {
                "success": False,
                "message": _("Item not found for barcode: {0}").format(barcode),
            }

        # Get item details
        item = frappe.get_doc("Item", item_code)

        # Get current stock levels
        stock_data = frappe.db.sql(
            """
            SELECT 
                warehouse,
                actual_qty,
                valuation_rate
            FROM `tabBin` 
            WHERE item_code = %s 
            AND actual_qty > 0
            ORDER BY actual_qty DESC
        """,
            [item_code],
            as_dict=True,
        )

        # Prepare response
        item_data = {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_name_ar": (
                item.custom_item_name_ar if hasattr(item, "custom_item_name_ar") else ""
            ),
            "description": item.description,
            "stock_uom": item.stock_uom,
            "barcode": barcode,
            "is_stock_item": item.is_stock_item,
            "valuation_rate": flt(item.valuation_rate, 3),
            "standard_rate": flt(item.standard_rate, 3),
            "warehouses": stock_data,
            "actual_qty": sum([flt(stock.actual_qty) for stock in stock_data]),
            "warehouse": stock_data[0]["warehouse"] if stock_data else None,
        }

        return {"success": True, "item": item_data}

    except Exception as e:
        frappe.log_error(f"Mobile API - Barcode lookup error: {str(e)}", "Mobile Inventory API")
        return {"success": False, "message": _("Error looking up item: {0}").format(str(e))}


@frappe.whitelist()
def search_items(query, limit=20):
    """
    Search for items by name, code, or description

    Args:
        query (str): Search query
        limit (int): Maximum number of results

    Returns:
        dict: List of matching items
    """
    try:
        # Validate license
        validate_license_for_operation("mobile_inventory_access")

        limit = cint(limit)
        if limit > 50:
            limit = 50

        sql = """
            SELECT 
                i.item_code,
                i.item_name,
                i.description,
                i.stock_uom,
                i.valuation_rate,
                COALESCE(SUM(b.actual_qty), 0) as actual_qty
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON i.item_code = b.item_code
            WHERE 
                i.disabled = 0 
                AND i.is_stock_item = 1 
                AND (i.item_code LIKE %s OR i.item_name LIKE %s OR i.description LIKE %s)
            GROUP BY i.item_code
            ORDER BY i.item_name
            LIMIT %s
        """

        search_pattern = f"%{query}%"
        items = frappe.db.sql(
            sql, [search_pattern, search_pattern, search_pattern, limit], as_dict=True
        )

        return {"success": True, "items": items, "count": len(items)}

    except Exception as e:
        frappe.log_error(f"Mobile API - Item search error: {str(e)}", "Mobile Inventory API")
        return {"success": False, "message": _("Search failed: {0}").format(str(e))}


@frappe.whitelist()
def get_item_details(item_code):
    """
    Get detailed information for a specific item

    Args:
        item_code (str): The item code to look up

    Returns:
        dict: Comprehensive item details
    """
    try:
        # Validate license
        validate_license_for_operation("mobile_inventory_access")

        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item {0} not found").format(item_code)}

        # Get item document
        item = frappe.get_doc("Item", item_code)

        # Get stock details
        stock_details = frappe.db.sql(
            """
            SELECT 
                b.warehouse,
                w.warehouse_name,
                b.actual_qty,
                b.valuation_rate
            FROM `tabBin` b
            LEFT JOIN `tabWarehouse` w ON b.warehouse = w.name
            WHERE b.item_code = %s
            ORDER BY b.actual_qty DESC
        """,
            [item_code],
            as_dict=True,
        )

        item_data = {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_name_ar": (
                item.custom_item_name_ar if hasattr(item, "custom_item_name_ar") else ""
            ),
            "description": item.description,
            "stock_uom": item.stock_uom,
            "barcode": item.barcode,
            "is_stock_item": item.is_stock_item,
            "valuation_rate": flt(item.valuation_rate, 3),
            "standard_rate": flt(item.standard_rate, 3),
            "item_group": item.item_group,
            "brand": item.brand,
            "stock_details": stock_details,
            "actual_qty": sum([flt(stock.actual_qty) for stock in stock_details]),
        }

        return {"success": True, "item": item_data}

    except Exception as e:
        frappe.log_error(f"Mobile API - Item details error: {str(e)}", "Mobile Inventory API")
        return {"success": False, "message": _("Error retrieving item details: {0}").format(str(e))}


@frappe.whitelist()
def create_stock_entry(
    item_code, quantity, entry_type="Material Receipt", warehouse=None, source="Mobile App"
):
    """
    Create a stock entry from mobile interface

    Args:
        item_code (str): Item code
        quantity (float): Quantity to adjust
        entry_type (str): Type of stock entry
        warehouse (str): Target warehouse (optional)
        source (str): Source of the entry

    Returns:
        dict: Stock entry creation result
    """
    try:
        # Validate license
        validate_license_for_operation("mobile_stock_entry")

        # Validate inputs
        if not item_code or not quantity:
            return {"success": False, "message": _("Item code and quantity are required")}

        if not frappe.db.exists("Item", item_code):
            return {"success": False, "message": _("Item {0} not found").format(item_code)}

        quantity = flt(quantity)
        if quantity <= 0:
            return {"success": False, "message": _("Quantity must be greater than zero")}

        # Get default warehouse if not provided
        if not warehouse:
            warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
            if not warehouse:
                # Get first available warehouse
                warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")

        if not warehouse:
            return {"success": False, "message": _("No warehouse available for stock entry")}

        # Create stock entry
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = entry_type
        stock_entry.purpose = entry_type
        stock_entry.posting_date = getdate()
        stock_entry.posting_time = now()
        stock_entry.remarks = f"Mobile stock entry - {source}"

        # Add item line
        stock_entry.append(
            "items",
            {
                "item_code": item_code,
                "qty": quantity,
                "s_warehouse": None if entry_type == "Material Receipt" else warehouse,
                "t_warehouse": warehouse if entry_type == "Material Receipt" else None,
                "uom": frappe.db.get_value("Item", item_code, "stock_uom"),
                "stock_uom": frappe.db.get_value("Item", item_code, "stock_uom"),
                "conversion_factor": 1,
            },
        )

        # Save and submit
        stock_entry.insert()
        stock_entry.submit()

        return {
            "success": True,
            "name": stock_entry.name,
            "message": _("Stock entry {0} created successfully").format(stock_entry.name),
        }

    except Exception as e:
        frappe.log_error(
            f"Mobile API - Stock entry creation error: {str(e)}", "Mobile Inventory API"
        )
        return {"success": False, "message": _("Error creating stock entry: {0}").format(str(e))}


@frappe.whitelist()
def get_warehouse_list():
    """
    Get list of available warehouses for mobile interface

    Returns:
        dict: List of warehouses
    """
    try:
        # Validate license
        validate_license_for_operation("mobile_inventory_access")

        warehouses = frappe.get_list(
            "Warehouse",
            filters={"is_group": 0, "disabled": 0},
            fields=["name", "warehouse_name", "warehouse_type", "company"],
            order_by="warehouse_name",
        )

        return {"success": True, "warehouses": warehouses}

    except Exception as e:
        frappe.log_error(f"Mobile API - Warehouse list error: {str(e)}", "Mobile Inventory API")
        return {"success": False, "message": _("Error retrieving warehouses: {0}").format(str(e))}


@frappe.whitelist()
def get_mobile_dashboard_data():
    """
    Get dashboard data for mobile interface

    Returns:
        dict: Dashboard statistics and recent activity
    """
    try:
        # Validate license
        validate_license_for_operation("mobile_inventory_access")

        # Get basic inventory statistics
        total_items = frappe.db.count("Item", {"is_stock_item": 1, "disabled": 0})

        # Get recent stock movements
        recent_movements = frappe.db.sql(
            """
            SELECT 
                sle.item_code,
                i.item_name,
                sle.actual_qty,
                sle.posting_date,
                sle.warehouse
            FROM `tabStock Ledger Entry` sle
            INNER JOIN `tabItem` i ON sle.item_code = i.item_code
            WHERE sle.posting_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            ORDER BY sle.creation DESC
            LIMIT 10
        """,
            as_dict=True,
        )

        dashboard_data = {
            "total_items": total_items,
            "recent_movements": recent_movements,
            "last_updated": now(),
        }

        return {"success": True, "dashboard": dashboard_data}

    except Exception as e:
        frappe.log_error(f"Mobile API - Dashboard data error: {str(e)}", "Mobile Inventory API")
        return {
            "success": False,
            "message": _("Error retrieving dashboard data: {0}").format(str(e)),
        }


@frappe.whitelist()
def record_mobile_activity(activity_type, item_code=None, details=None):
    """
    Record mobile app activity for analytics

    Args:
        activity_type (str): Type of activity
        item_code (str): Related item code (optional)
        details (str): Additional details (optional)

    Returns:
        dict: Recording result
    """
    try:
        # Create activity log entry
        activity_log = {
            "doctype": "Mobile Activity Log",
            "user": frappe.session.user,
            "activity_type": activity_type,
            "item_code": item_code,
            "details": details,
            "timestamp": now(),
            "session_id": frappe.session.sid,
        }

        # Insert if doctype exists, otherwise skip silently
        try:
            frappe.get_doc(activity_log).insert()
            return {"success": True, "message": "Activity recorded"}
        except:
            # DocType might not exist, which is fine
            return {"success": True, "message": "Activity tracking not available"}

    except Exception as e:
        frappe.log_error(f"Mobile API - Activity recording error: {str(e)}", "Mobile Inventory API")
        return {"success": False, "message": _("Error recording activity: {0}").format(str(e))}
