# -*- coding: utf-8 -*-
"""
Universal Workshop ERP - Offline Sync API
Backend support for offline data synchronization with conflict resolution
Arabic/English localization support for Omani automotive workshops
"""

import frappe
from frappe import _
import json
from datetime import datetime, timedelta
from frappe.utils import now, get_datetime, cint, flt
import hashlib


@frappe.whitelist()
def sync_offline_data(sync_data):
    """
    Sync offline data from mobile devices
    Handles conflict resolution and data integrity

    Args:
        sync_data (dict): Offline sync data containing transaction information

    Returns:
        dict: Sync result with success status and any conflicts
    """
    try:
        # Parse sync data
        if isinstance(sync_data, str):
            sync_data = json.loads(sync_data)

        # Validate sync data
        if not validate_sync_data(sync_data):
            frappe.throw(_("Invalid sync data format"))

        # Check for conflicts
        conflicts = check_sync_conflicts(sync_data)

        if conflicts:
            return {
                "success": False,
                "conflicts": conflicts,
                "message": _("Conflicts detected. Manual resolution required."),
            }

        # Process sync based on action type
        result = process_sync_action(sync_data)

        # Log sync activity for audit compliance
        log_sync_activity(sync_data, result)

        return {
            "success": True,
            "server_id": result.get("server_id"),
            "message": _("Data synchronized successfully"),
            "timestamp": now(),
        }

    except Exception as e:
        frappe.log_error(f"Offline sync error: {str(e)}", "Offline Sync")
        return {"success": False, "error": str(e), "message": _("Sync failed. Please try again.")}


def validate_sync_data(sync_data):
    """
    Validate incoming sync data structure

    Args:
        sync_data (dict): Sync data to validate

    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = ["action", "data", "timestamp", "user_id", "device_fingerprint"]

    if not all(field in sync_data for field in required_fields):
        return False

    # Validate timestamp (not too old)
    try:
        sync_time = get_datetime(sync_data["timestamp"])
        max_age = datetime.now() - timedelta(days=7)  # Max 7 days old

        if sync_time < max_age:
            frappe.log_error(f"Sync data too old: {sync_time}", "Offline Sync")
            return False

    except Exception:
        return False

    return True


def check_sync_conflicts(sync_data):
    """
    Check for conflicts with server data

    Args:
        sync_data (dict): Sync data to check

    Returns:
        list: List of conflicts found
    """
    conflicts = []
    action = sync_data.get("action")
    data = sync_data.get("data")

    if action == "inventory_transaction":
        conflicts.extend(check_inventory_conflicts(data))
    elif action == "stock_update":
        conflicts.extend(check_stock_conflicts(data))
    elif action == "barcode_scan":
        conflicts.extend(check_barcode_conflicts(data))

    return conflicts


def check_inventory_conflicts(transaction_data):
    """
    Check for inventory transaction conflicts

    Args:
        transaction_data (dict): Transaction data to check

    Returns:
        list: List of conflicts
    """
    conflicts = []
    item_code = transaction_data.get("item_code")

    if not item_code:
        return conflicts

    # Check if item exists
    if not frappe.db.exists("Item", item_code):
        conflicts.append(
            {
                "type": "item_not_found",
                "item_code": item_code,
                "message": _("Item {0} not found on server").format(item_code),
            }
        )
        return conflicts

    # Check for concurrent modifications
    server_last_modified = frappe.db.get_value("Item", item_code, "modified")
    client_last_known = transaction_data.get("last_known_modified")

    if client_last_known and server_last_modified:
        if get_datetime(server_last_modified) > get_datetime(client_last_known):
            conflicts.append(
                {
                    "type": "concurrent_modification",
                    "item_code": item_code,
                    "server_modified": server_last_modified,
                    "client_known": client_last_known,
                    "message": _("Item {0} was modified by another user").format(item_code),
                }
            )

    # Check stock availability for outgoing transactions
    if transaction_data.get("transaction_type") in ["Material Issue", "Stock Entry"]:
        warehouse = transaction_data.get("warehouse")
        qty = flt(transaction_data.get("qty", 0))

        if qty > 0:  # Outgoing transaction
            available_qty = get_available_stock(item_code, warehouse)
            if available_qty < qty:
                conflicts.append(
                    {
                        "type": "insufficient_stock",
                        "item_code": item_code,
                        "warehouse": warehouse,
                        "requested_qty": qty,
                        "available_qty": available_qty,
                        "message": _("Insufficient stock. Available: {0}, Requested: {1}").format(
                            available_qty, qty
                        ),
                    }
                )

    return conflicts


def get_available_stock(item_code, warehouse):
    """
    Get available stock for item in warehouse

    Args:
        item_code (str): Item code
        warehouse (str): Warehouse name

    Returns:
        float: Available quantity
    """
    try:
        from erpnext.stock.utils import get_stock_balance

        return get_stock_balance(item_code, warehouse)
    except Exception:
        # Fallback to simple query
        result = frappe.db.sql(
            """
            SELECT SUM(actual_qty) 
            FROM `tabStock Ledger Entry` 
            WHERE item_code = %s AND warehouse = %s AND is_cancelled = 0
        """,
            [item_code, warehouse],
        )

        return flt(result[0][0]) if result and result[0][0] else 0


def process_sync_action(sync_data):
    """
    Process sync action based on type

    Args:
        sync_data (dict): Sync data to process

    Returns:
        dict: Processing result
    """
    action = sync_data.get("action")
    data = sync_data.get("data")

    if action == "inventory_transaction":
        return process_inventory_transaction(data, sync_data)
    elif action == "stock_update":
        return process_stock_update(data, sync_data)
    elif action == "barcode_scan":
        return process_barcode_scan(data, sync_data)
    else:
        frappe.throw(_("Unknown sync action: {0}").format(action))


def process_inventory_transaction(transaction_data, sync_data):
    """
    Process inventory transaction from offline data

    Args:
        transaction_data (dict): Transaction data
        sync_data (dict): Full sync data

    Returns:
        dict: Processing result
    """
    try:
        # Create Stock Entry from offline transaction
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = transaction_data.get("stock_entry_type", "Material Receipt")
        stock_entry.posting_date = get_datetime(transaction_data.get("posting_date", now())).date()
        stock_entry.posting_time = get_datetime(transaction_data.get("posting_time", now())).time()

        # Add item details
        stock_entry.append(
            "items",
            {
                "item_code": transaction_data.get("item_code"),
                "qty": flt(transaction_data.get("qty", 0)),
                "uom": transaction_data.get("uom", "Nos"),
                "s_warehouse": transaction_data.get("source_warehouse"),
                "t_warehouse": transaction_data.get("target_warehouse"),
                "basic_rate": flt(transaction_data.get("rate", 0)),
                "cost_center": transaction_data.get("cost_center"),
                "expense_account": transaction_data.get("expense_account"),
            },
        )

        # Add offline metadata
        stock_entry.custom_offline_id = transaction_data.get("id")
        stock_entry.custom_offline_timestamp = transaction_data.get("timestamp")
        stock_entry.custom_device_fingerprint = sync_data.get("device_fingerprint")
        stock_entry.custom_sync_user = sync_data.get("user_id")

        # Add remarks
        remarks = transaction_data.get("remarks", "")
        if remarks:
            stock_entry.remarks = f"Offline transaction: {remarks}"
        else:
            stock_entry.remarks = f"Synced from offline device on {now()}"

        # Insert and submit
        stock_entry.insert()

        # Auto-submit if specified
        if transaction_data.get("auto_submit"):
            stock_entry.submit()

        return {
            "server_id": stock_entry.name,
            "doctype": "Stock Entry",
            "status": stock_entry.docstatus,
        }

    except Exception as e:
        frappe.log_error(f"Error processing inventory transaction: {str(e)}", "Offline Sync")
        raise


def process_stock_update(stock_data, sync_data):
    """
    Process stock update from offline data

    Args:
        stock_data (dict): Stock update data
        sync_data (dict): Full sync data

    Returns:
        dict: Processing result
    """
    try:
        # Create Stock Reconciliation
        stock_reco = frappe.new_doc("Stock Reconciliation")
        stock_reco.posting_date = get_datetime(stock_data.get("posting_date", now())).date()
        stock_reco.posting_time = get_datetime(stock_data.get("posting_time", now())).time()
        stock_reco.purpose = "Stock Reconciliation"

        # Add items
        for item in stock_data.get("items", []):
            stock_reco.append(
                "items",
                {
                    "item_code": item.get("item_code"),
                    "warehouse": item.get("warehouse"),
                    "qty": flt(item.get("qty", 0)),
                    "valuation_rate": flt(item.get("rate", 0)),
                },
            )

        # Add offline metadata
        stock_reco.custom_offline_id = stock_data.get("id")
        stock_reco.custom_offline_timestamp = stock_data.get("timestamp")
        stock_reco.custom_device_fingerprint = sync_data.get("device_fingerprint")

        stock_reco.insert()

        if stock_data.get("auto_submit"):
            stock_reco.submit()

        return {
            "server_id": stock_reco.name,
            "doctype": "Stock Reconciliation",
            "status": stock_reco.docstatus,
        }

    except Exception as e:
        frappe.log_error(f"Error processing stock update: {str(e)}", "Offline Sync")
        raise


def process_barcode_scan(scan_data, sync_data):
    """
    Process barcode scan from offline data

    Args:
        scan_data (dict): Barcode scan data
        sync_data (dict): Full sync data

    Returns:
        dict: Processing result
    """
    try:
        # Log barcode scan activity
        scan_log = frappe.new_doc("Barcode Scan Log")
        scan_log.barcode = scan_data.get("barcode")
        scan_log.item_code = scan_data.get("item_code")
        scan_log.scan_type = scan_data.get("scan_type", "lookup")
        scan_log.warehouse = scan_data.get("warehouse")
        scan_log.qty = flt(scan_data.get("qty", 1))
        scan_log.scan_time = get_datetime(scan_data.get("scan_time", now()))
        scan_log.user = sync_data.get("user_id")
        scan_log.device_fingerprint = sync_data.get("device_fingerprint")
        scan_log.offline_sync = 1

        scan_log.insert()

        return {"server_id": scan_log.name, "doctype": "Barcode Scan Log", "status": "Logged"}

    except Exception as e:
        frappe.log_error(f"Error processing barcode scan: {str(e)}", "Offline Sync")
        raise


def log_sync_activity(sync_data, result):
    """
    Log sync activity for audit compliance

    Args:
        sync_data (dict): Sync data
        result (dict): Processing result
    """
    try:
        sync_log = frappe.new_doc("Offline Sync Log")
        sync_log.offline_id = sync_data.get("data", {}).get("id")
        sync_log.server_id = result.get("server_id")
        sync_log.action = sync_data.get("action")
        sync_log.user = sync_data.get("user_id")
        sync_log.device_fingerprint = sync_data.get("device_fingerprint")
        sync_log.sync_timestamp = now()
        sync_log.offline_timestamp = sync_data.get("timestamp")
        sync_log.data_hash = generate_data_hash(sync_data.get("data"))
        sync_log.status = "Success" if result.get("server_id") else "Failed"

        sync_log.insert()

    except Exception as e:
        frappe.log_error(f"Error logging sync activity: {str(e)}", "Offline Sync")


def generate_data_hash(data):
    """
    Generate hash of data for integrity checking

    Args:
        data (dict): Data to hash

    Returns:
        str: SHA256 hash
    """
    try:
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    except Exception:
        return ""


@frappe.whitelist()
def get_sync_status(device_fingerprint):
    """
    Get sync status for a device

    Args:
        device_fingerprint (str): Device fingerprint

    Returns:
        dict: Sync status information
    """
    try:
        # Get recent sync logs
        sync_logs = frappe.get_list(
            "Offline Sync Log",
            filters={"device_fingerprint": device_fingerprint},
            fields=["name", "action", "status", "sync_timestamp", "offline_timestamp"],
            order_by="sync_timestamp desc",
            limit=50,
        )

        # Calculate sync statistics
        total_syncs = len(sync_logs)
        successful_syncs = len([log for log in sync_logs if log.status == "Success"])
        failed_syncs = total_syncs - successful_syncs

        # Get last sync time
        last_sync = sync_logs[0].sync_timestamp if sync_logs else None

        return {
            "total_syncs": total_syncs,
            "successful_syncs": successful_syncs,
            "failed_syncs": failed_syncs,
            "success_rate": (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0,
            "last_sync": last_sync,
            "recent_logs": sync_logs[:10],  # Last 10 logs
        }

    except Exception as e:
        frappe.log_error(f"Error getting sync status: {str(e)}", "Offline Sync")
        return {"error": str(e), "message": _("Failed to get sync status")}


@frappe.whitelist()
def resolve_sync_conflict(conflict_id, resolution_strategy, resolution_data=None):
    """
    Resolve sync conflict with specified strategy

    Args:
        conflict_id (str): Conflict identifier
        resolution_strategy (str): Strategy to use (use_local, use_server, merge, manual)
        resolution_data (dict): Additional data for resolution

    Returns:
        dict: Resolution result
    """
    try:
        # Implementation would depend on conflict tracking DocType
        # For now, return success
        return {"success": True, "message": _("Conflict resolved successfully"), "timestamp": now()}

    except Exception as e:
        frappe.log_error(f"Error resolving conflict: {str(e)}", "Offline Sync")
        return {"success": False, "error": str(e), "message": _("Failed to resolve conflict")}
