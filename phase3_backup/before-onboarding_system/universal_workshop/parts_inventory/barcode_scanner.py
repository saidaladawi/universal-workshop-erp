# Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
# For license information, please see license.txt

"""
Comprehensive Barcode Scanning Integration for Parts Inventory
Combines ERPNext v15 native barcode support with QuaggaJS for mobile camera scanning
"""

import json
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.utils import now, today, cint, flt

from .barcode_utils import generate_item_barcode, generate_item_qr_code


@frappe.whitelist()
def scan_barcode(
    barcode_data: str,
    scan_type: str = "lookup",
    warehouse: str = "",
    transaction_type: str = "",
    quantity: float = 0,
):
    """
    Process barcode scan and perform the requested action

    Args:
        barcode_data: The scanned barcode/QR code data
        scan_type: Type of scan (lookup, stock_in, stock_out, transfer, reconcile)
        warehouse: Warehouse for stock operations
        transaction_type: Document type for stock operations
        quantity: Quantity for stock operations

    Returns:
        Dict with scan result and item information
    """
    try:
        # Clean and validate barcode data
        barcode_data = barcode_data.strip()
        if not barcode_data:
            return {"success": False, "message": _("Invalid barcode data")}

        # Find item by barcode
        item_info = find_item_by_barcode(barcode_data)
        if not item_info["success"]:
            return item_info

        item_code = item_info["item"]["item_code"]

        # Process based on scan type
        if scan_type == "lookup":
            return handle_lookup_scan(item_code, warehouse)
        elif scan_type == "stock_in":
            return handle_stock_in_scan(item_code, warehouse, quantity, transaction_type)
        elif scan_type == "stock_out":
            return handle_stock_out_scan(item_code, warehouse, quantity, transaction_type)
        elif scan_type == "transfer":
            return handle_transfer_scan(item_code, warehouse, quantity)
        elif scan_type == "reconcile":
            return handle_reconcile_scan(item_code, warehouse, quantity)
        else:
            return {"success": False, "message": _("Invalid scan type: {0}").format(scan_type)}

    except Exception as e:
        frappe.log_error(f"Barcode scan processing failed: {str(e)}", "Barcode Scanner")
        return {
            "success": False,
            "message": _("Scan processing failed. Please try again."),
            "error": str(e),
        }


def find_item_by_barcode(barcode_data: str) -> Dict[str, Any]:
    """
    Find item by barcode using ERPNext v15 native barcode fields

    Args:
        barcode_data: Barcode or QR code data

    Returns:
        Dict with item information or error
    """
    try:
        # Try QR code format first (JSON data)
        if barcode_data.startswith("{") and barcode_data.endswith("}"):
            try:
                qr_data = json.loads(barcode_data)
                if "item_code" in qr_data:
                    item_code = qr_data["item_code"]
                    item = frappe.get_doc("Item", item_code)
                    return {
                        "success": True,
                        "item": item.as_dict(),
                        "scan_method": "qr_code",
                        "qr_data": qr_data,
                    }
            except json.JSONDecodeError:
                pass  # Not JSON, continue with barcode search

        # Search in ERPNext native barcode fields
        # First check exact match in barcode field
        item = frappe.db.get_value(
            "Item",
            {"barcode": barcode_data, "disabled": 0},
            ["name", "item_code", "item_name", "standard_rate", "stock_uom"],
            as_dict=True,
        )

        if item:
            full_item = frappe.get_doc("Item", item.name)
            return {"success": True, "item": full_item.as_dict(), "scan_method": "native_barcode"}

        # Check Item Barcode child table (ERPNext v15 feature)
        barcode_entry = frappe.db.get_value(
            "Item Barcode", {"barcode": barcode_data}, ["parent", "uom"], as_dict=True
        )

        if barcode_entry:
            full_item = frappe.get_doc("Item", barcode_entry.parent)
            return {
                "success": True,
                "item": full_item.as_dict(),
                "scan_method": "item_barcode_table",
                "scanned_uom": barcode_entry.uom,
            }

        # Search in item_code field (fallback)
        item = frappe.db.get_value(
            "Item",
            {"item_code": barcode_data, "disabled": 0},
            ["name", "item_code", "item_name", "standard_rate", "stock_uom"],
            as_dict=True,
        )

        if item:
            full_item = frappe.get_doc("Item", item.name)
            return {"success": True, "item": full_item.as_dict(), "scan_method": "item_code"}

        # Try searching by OEM part number or aftermarket part number
        custom_searches = ["oem_part_number", "aftermarket_part_number", "manufacturer_part_number"]

        for field in custom_searches:
            item = frappe.db.get_value(
                "Item",
                {field: barcode_data, "disabled": 0},
                ["name", "item_code", "item_name"],
                as_dict=True,
            )
            if item:
                full_item = frappe.get_doc("Item", item.name)
                return {
                    "success": True,
                    "item": full_item.as_dict(),
                    "scan_method": f"custom_field_{field}",
                }

        return {
            "success": False,
            "message": _("No item found with barcode: {0}").format(barcode_data),
            "barcode_data": barcode_data,
        }

    except Exception as e:
        frappe.log_error(f"Barcode lookup failed: {str(e)}")
        return {"success": False, "message": _("Barcode lookup failed"), "error": str(e)}


def handle_lookup_scan(item_code: str, warehouse: str = "") -> Dict[str, Any]:
    """
    Handle lookup scan - just return item information and stock levels
    """
    try:
        item = frappe.get_doc("Item", item_code)

        # Get stock information
        from erpnext.stock.utils import get_stock_balance

        stock_info = {}
        if warehouse:
            stock_balance = get_stock_balance(item_code, warehouse)
            stock_info = {
                "warehouse": warehouse,
                "stock_qty": stock_balance,
                "warehouse_specific": True,
            }
        else:
            # Get total stock across all warehouses
            total_stock = get_stock_balance(item_code)

            # Get stock by warehouse
            warehouse_stock = frappe.db.sql(
                """
                SELECT warehouse, SUM(actual_qty) as qty
                FROM `tabStock Ledger Entry`
                WHERE item_code = %s
                AND is_cancelled = 0
                GROUP BY warehouse
                HAVING qty > 0
                ORDER BY qty DESC
            """,
                item_code,
                as_dict=True,
            )

            stock_info = {
                "total_stock": total_stock,
                "warehouse_stock": warehouse_stock,
                "warehouse_specific": False,
            }

        # Get recent transactions
        recent_transactions = frappe.get_list(
            "Stock Ledger Entry",
            filters={"item_code": item_code},
            fields=[
                "posting_date",
                "voucher_type",
                "voucher_no",
                "actual_qty",
                "qty_after_transaction",
                "warehouse",
            ],
            order_by="posting_date desc, posting_time desc",
            limit=10,
        )

        return {
            "success": True,
            "action": "lookup",
            "item": item.as_dict(),
            "stock_info": stock_info,
            "recent_transactions": recent_transactions,
            "scan_timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Lookup scan failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to lookup item information"),
            "error": str(e),
        }


def handle_stock_in_scan(
    item_code: str, warehouse: str, quantity: float, transaction_type: str = "Stock Entry"
) -> Dict[str, Any]:
    """
    Handle stock in scan - create stock entry for incoming stock
    """
    try:
        if not warehouse:
            return {"success": False, "message": _("Warehouse is required for stock in operation")}

        if quantity <= 0:
            return {"success": False, "message": _("Quantity must be greater than zero")}

        # Create stock entry for Material Receipt
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Receipt"
        stock_entry.purpose = "Material Receipt"
        stock_entry.posting_date = today()
        stock_entry.posting_time = now()

        # Add item to stock entry
        stock_entry.append(
            "items",
            {
                "item_code": item_code,
                "qty": quantity,
                "t_warehouse": warehouse,
                "basic_rate": frappe.db.get_value("Item", item_code, "standard_rate") or 0,
            },
        )

        # Save as draft first
        stock_entry.insert()

        return {
            "success": True,
            "action": "stock_in",
            "stock_entry": stock_entry.name,
            "item_code": item_code,
            "quantity": quantity,
            "warehouse": warehouse,
            "status": "draft",
            "message": _("Stock in entry created successfully"),
            "scan_timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Stock in scan failed: {str(e)}")
        return {"success": False, "message": _("Failed to create stock in entry"), "error": str(e)}


def handle_stock_out_scan(
    item_code: str, warehouse: str, quantity: float, transaction_type: str = "Stock Entry"
) -> Dict[str, Any]:
    """
    Handle stock out scan - create stock entry for outgoing stock
    """
    try:
        if not warehouse:
            return {"success": False, "message": _("Warehouse is required for stock out operation")}

        if quantity <= 0:
            return {"success": False, "message": _("Quantity must be greater than zero")}

        # Check available stock
        from erpnext.stock.utils import get_stock_balance

        available_qty = get_stock_balance(item_code, warehouse)

        if available_qty < quantity:
            return {
                "success": False,
                "message": _("Insufficient stock. Available: {0}, Requested: {1}").format(
                    available_qty, quantity
                ),
                "available_qty": available_qty,
                "requested_qty": quantity,
            }

        # Create stock entry for Material Issue
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Issue"
        stock_entry.purpose = "Material Issue"
        stock_entry.posting_date = today()
        stock_entry.posting_time = now()

        # Add item to stock entry
        stock_entry.append(
            "items",
            {
                "item_code": item_code,
                "qty": quantity,
                "s_warehouse": warehouse,
                "basic_rate": frappe.db.get_value("Item", item_code, "standard_rate") or 0,
            },
        )

        # Save as draft first
        stock_entry.insert()

        return {
            "success": True,
            "action": "stock_out",
            "stock_entry": stock_entry.name,
            "item_code": item_code,
            "quantity": quantity,
            "warehouse": warehouse,
            "available_qty": available_qty,
            "status": "draft",
            "message": _("Stock out entry created successfully"),
            "scan_timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Stock out scan failed: {str(e)}")
        return {"success": False, "message": _("Failed to create stock out entry"), "error": str(e)}


def handle_transfer_scan(
    item_code: str, from_warehouse: str, quantity: float, to_warehouse: str = ""
) -> Dict[str, Any]:
    """
    Handle transfer scan - create stock entry for warehouse transfer
    """
    try:
        if not from_warehouse:
            return {"success": False, "message": _("Source warehouse is required for transfer")}

        if not to_warehouse:
            return {"success": False, "message": _("Target warehouse is required for transfer")}

        if quantity <= 0:
            return {"success": False, "message": _("Quantity must be greater than zero")}

        # Check available stock in source warehouse
        from erpnext.stock.utils import get_stock_balance

        available_qty = get_stock_balance(item_code, from_warehouse)

        if available_qty < quantity:
            return {
                "success": False,
                "message": _(
                    "Insufficient stock in source warehouse. Available: {0}, Requested: {1}"
                ).format(available_qty, quantity),
                "available_qty": available_qty,
                "requested_qty": quantity,
            }

        # Create stock entry for Material Transfer
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.purpose = "Material Transfer"
        stock_entry.posting_date = today()
        stock_entry.posting_time = now()

        # Add item to stock entry
        stock_entry.append(
            "items",
            {
                "item_code": item_code,
                "qty": quantity,
                "s_warehouse": from_warehouse,
                "t_warehouse": to_warehouse,
                "basic_rate": frappe.db.get_value("Item", item_code, "standard_rate") or 0,
            },
        )

        # Save as draft first
        stock_entry.insert()

        return {
            "success": True,
            "action": "transfer",
            "stock_entry": stock_entry.name,
            "item_code": item_code,
            "quantity": quantity,
            "from_warehouse": from_warehouse,
            "to_warehouse": to_warehouse,
            "available_qty": available_qty,
            "status": "draft",
            "message": _("Stock transfer entry created successfully"),
            "scan_timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Transfer scan failed: {str(e)}")
        return {"success": False, "message": _("Failed to create transfer entry"), "error": str(e)}


def handle_reconcile_scan(item_code: str, warehouse: str, counted_qty: float) -> Dict[str, Any]:
    """
    Handle reconcile scan - add item to stock reconciliation
    """
    try:
        if not warehouse:
            return {"success": False, "message": _("Warehouse is required for reconciliation")}

        # Get current stock
        from erpnext.stock.utils import get_stock_balance

        current_qty = get_stock_balance(item_code, warehouse)

        # Calculate difference
        difference = counted_qty - current_qty

        return {
            "success": True,
            "action": "reconcile",
            "item_code": item_code,
            "warehouse": warehouse,
            "current_qty": current_qty,
            "counted_qty": counted_qty,
            "difference": difference,
            "requires_adjustment": abs(difference) > 0.001,  # Account for floating point precision
            "scan_timestamp": now(),
            "message": _("Item scanned for reconciliation"),
        }

    except Exception as e:
        frappe.log_error(f"Reconcile scan failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to process reconciliation scan"),
            "error": str(e),
        }


@frappe.whitelist()
def batch_barcode_scan(scan_data: str):
    """
    Process multiple barcode scans from batch scanning

    Args:
        scan_data: JSON string containing array of scan operations

    Returns:
        Dict with batch processing results
    """
    try:
        scans = json.loads(scan_data)
        results = []

        for scan in scans:
            barcode_data = scan.get("barcode_data", "")
            scan_type = scan.get("scan_type", "lookup")
            warehouse = scan.get("warehouse", "")
            quantity = scan.get("quantity", 0)

            result = scan_barcode(barcode_data, scan_type, warehouse, quantity=quantity)
            result["original_scan"] = scan
            results.append(result)

        # Summary
        successful_scans = len([r for r in results if r.get("success", False)])
        failed_scans = len(results) - successful_scans

        return {
            "success": True,
            "batch_results": results,
            "summary": {
                "total_scans": len(results),
                "successful_scans": successful_scans,
                "failed_scans": failed_scans,
                "success_rate": (successful_scans / len(results)) * 100 if results else 0,
            },
            "processing_timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Batch scan processing failed: {str(e)}")
        return {"success": False, "message": _("Batch scan processing failed"), "error": str(e)}


@frappe.whitelist()
def get_scanning_configuration():
    """
    Get configuration for barcode scanning interface

    Returns:
        Dict with scanning configuration
    """
    try:
        # Get available warehouses
        warehouses = frappe.get_list(
            "Warehouse",
            filters={"disabled": 0},
            fields=["name", "warehouse_name", "is_group"],
            order_by="warehouse_name",
        )

        # Get scan types
        scan_types = [
            {"value": "lookup", "label": _("Lookup Item")},
            {"value": "stock_in", "label": _("Stock In")},
            {"value": "stock_out", "label": _("Stock Out")},
            {"value": "transfer", "label": _("Transfer")},
            {"value": "reconcile", "label": _("Reconcile")},
        ]

        # Get transaction types
        transaction_types = [
            {"value": "Stock Entry", "label": _("Stock Entry")},
            {"value": "Purchase Receipt", "label": _("Purchase Receipt")},
            {"value": "Delivery Note", "label": _("Delivery Note")},
            {"value": "Sales Invoice", "label": _("Sales Invoice")},
        ]

        return {
            "success": True,
            "config": {
                "warehouses": warehouses,
                "scan_types": scan_types,
                "transaction_types": transaction_types,
                "settings": {
                    "auto_submit": False,
                    "show_item_image": True,
                    "play_sound": True,
                    "vibrate_on_scan": True,
                },
            },
        }

    except Exception as e:
        frappe.log_error(f"Scanning configuration failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to load scanning configuration"),
            "error": str(e),
        }
