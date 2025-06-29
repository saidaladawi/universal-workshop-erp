import frappe
from frappe import _
from frappe.utils import flt, nowdate, now, get_url
import json
from datetime import datetime, timedelta

# Stock Transfer Workflow Implementation for Universal Workshop ERP
# Implements dual-approval workflow with barcode integration


@frappe.whitelist()
def create_stock_transfer(source_warehouse, target_warehouse, items, remarks="", priority="Medium"):
    """
    Create a new stock transfer request with approval workflow

    Args:
        source_warehouse (str): Source warehouse code
        target_warehouse (str): Target warehouse code
        items (list): List of items with item_code, qty, and rate
        remarks (str): Transfer remarks
        priority (str): Transfer priority (High, Medium, Low)

    Returns:
        dict: Transfer request details
    """
    try:
        # Parse items if passed as string
        if isinstance(items, str):
            items = json.loads(items)

        # Create Stock Entry document
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.from_warehouse = source_warehouse
        stock_entry.to_warehouse = target_warehouse
        stock_entry.remarks = remarks
        stock_entry.custom_transfer_priority = priority
        stock_entry.custom_transfer_status = "Draft"
        stock_entry.custom_requested_by = frappe.session.user
        stock_entry.custom_requested_date = nowdate()

        # Add items to transfer
        total_value = 0
        for item in items:
            row = stock_entry.append("items", {})
            row.item_code = item["item_code"]
            row.qty = flt(item["qty"])
            row.s_warehouse = source_warehouse
            row.t_warehouse = target_warehouse

            # Get item details
            item_doc = frappe.get_doc("Item", item["item_code"])
            row.item_name = item_doc.item_name
            row.description = item_doc.description
            row.uom = item_doc.stock_uom

            # Calculate rates
            if "rate" in item and item["rate"]:
                row.basic_rate = flt(item["rate"])
            else:
                # Get valuation rate
                valuation_rate = get_item_valuation_rate(item["item_code"], source_warehouse)
                row.basic_rate = valuation_rate

            row.basic_amount = flt(row.qty) * flt(row.basic_rate)
            total_value += row.basic_amount

        # Set workflow status
        stock_entry.workflow_state = "Draft"

        # Save the document
        stock_entry.insert()
        frappe.db.commit()

        # Create transfer tracking record
        create_transfer_log(stock_entry.name, "Draft", "Transfer request created")

        return {
            "success": True,
            "transfer_id": stock_entry.name,
            "total_value": total_value,
            "status": "Draft",
            "message": _("Stock transfer request created successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Stock transfer creation failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to create stock transfer: {0}").format(str(e)),
        }


@frappe.whitelist()
def get_pending_transfers(warehouse=None, status=None, limit=20):
    """
    Get list of pending stock transfers

    Args:
        warehouse (str): Filter by warehouse
        status (str): Filter by status
        limit (int): Number of records to return

    Returns:
        list: Pending transfers
    """
    filters = {"stock_entry_type": "Material Transfer", "docstatus": ["!=", 2]}  # Not cancelled

    if warehouse:
        filters["from_warehouse"] = ["like", f"%{warehouse}%"]

    if status:
        filters["workflow_state"] = status

    transfers = frappe.get_list(
        "Stock Entry",
        filters=filters,
        fields=[
            "name",
            "from_warehouse",
            "to_warehouse",
            "posting_date",
            "workflow_state",
            "custom_transfer_priority",
            "custom_requested_by",
            "total_outgoing_value",
            "remarks",
        ],
        order_by="posting_date desc",
        limit=limit,
    )

    # Add item count and urgency info
    for transfer in transfers:
        # Get item count
        item_count = frappe.db.count("Stock Entry Detail", {"parent": transfer.name})
        transfer["item_count"] = item_count

        # Calculate urgency (days since request)
        posting_date = transfer.posting_date
        if posting_date:
            days_pending = (nowdate() - posting_date).days
            transfer["days_pending"] = days_pending
            transfer["urgency"] = (
                "High" if days_pending > 3 else "Medium" if days_pending > 1 else "Low"
            )

    return transfers


@frappe.whitelist()
def approve_transfer_source(transfer_id, approved_items=None, remarks=""):
    """
    Approve transfer from source warehouse perspective

    Args:
        transfer_id (str): Stock Entry ID
        approved_items (list): List of approved items with quantities
        remarks (str): Approval remarks

    Returns:
        dict: Approval result
    """
    try:
        stock_entry = frappe.get_doc("Stock Entry", transfer_id)

        # Check permissions
        if not frappe.has_permission("Stock Entry", "write", stock_entry):
            frappe.throw(_("Insufficient permissions to approve transfer"))

        # Update approved quantities if provided
        if approved_items:
            if isinstance(approved_items, str):
                approved_items = json.loads(approved_items)

            for approved_item in approved_items:
                for item in stock_entry.items:
                    if item.item_code == approved_item["item_code"]:
                        item.qty = flt(approved_item["approved_qty"])
                        break

        # Update workflow state
        stock_entry.workflow_state = "Source Approved"
        stock_entry.custom_source_approved_by = frappe.session.user
        stock_entry.custom_source_approved_date = now()
        stock_entry.custom_source_remarks = remarks

        stock_entry.save()
        frappe.db.commit()

        # Log the approval
        create_transfer_log(
            transfer_id, "Source Approved", f"Source approved by {frappe.session.user}"
        )

        # Send notification to target warehouse
        send_transfer_notification(stock_entry, "source_approved")

        return {
            "success": True,
            "message": _("Transfer approved from source warehouse"),
            "status": "Source Approved",
        }

    except Exception as e:
        frappe.log_error(f"Source approval failed: {str(e)}")
        return {"success": False, "message": _("Failed to approve transfer: {0}").format(str(e))}


@frappe.whitelist()
def scan_item_for_transfer(transfer_id, barcode, location="source"):
    """
    Scan item during transfer process

    Args:
        transfer_id (str): Stock Entry ID
        barcode (str): Scanned barcode
        location (str): 'source' or 'target' location

    Returns:
        dict: Scan result with item details
    """
    try:
        # Find item by barcode
        item_code = find_item_by_barcode(barcode)
        if not item_code:
            return {
                "success": False,
                "message": _("Item not found for barcode: {0}").format(barcode),
            }

        # Get transfer document
        stock_entry = frappe.get_doc("Stock Entry", transfer_id)

        # Find item in transfer
        transfer_item = None
        for item in stock_entry.items:
            if item.item_code == item_code:
                transfer_item = item
                break

        if not transfer_item:
            return {
                "success": False,
                "message": _("Item {0} not found in this transfer").format(item_code),
            }

        # Update scan status
        if location == "source":
            transfer_item.custom_source_scanned = 1
            transfer_item.custom_source_scan_time = now()
            transfer_item.custom_source_scanned_by = frappe.session.user
        else:  # target
            transfer_item.custom_target_scanned = 1
            transfer_item.custom_target_scan_time = now()
            transfer_item.custom_target_scanned_by = frappe.session.user

        stock_entry.save()
        frappe.db.commit()

        # Get item details
        item_doc = frappe.get_doc("Item", item_code)

        return {
            "success": True,
            "item_code": item_code,
            "item_name": item_doc.item_name,
            "qty": transfer_item.qty,
            "scanned_qty": transfer_item.custom_scanned_qty or 0,
            "remaining_qty": flt(transfer_item.qty) - flt(transfer_item.custom_scanned_qty or 0),
            "location": location,
            "message": _("Item scanned successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Item scan failed: {str(e)}")
        return {"success": False, "message": _("Scan failed: {0}").format(str(e))}


@frappe.whitelist()
def complete_transfer(transfer_id, target_remarks=""):
    """
    Complete the stock transfer after target approval

    Args:
        transfer_id (str): Stock Entry ID
        target_remarks (str): Target warehouse remarks

    Returns:
        dict: Completion result
    """
    try:
        stock_entry = frappe.get_doc("Stock Entry", transfer_id)

        # Validate all items are scanned (if scanning required)
        unscanned_items = []
        for item in stock_entry.items:
            if not item.custom_target_scanned:
                unscanned_items.append(item.item_code)

        if unscanned_items and frappe.db.get_single_value(
            "Workshop Settings", "require_transfer_scanning"
        ):
            return {
                "success": False,
                "message": _(
                    "Please scan all items before completing transfer. Unscanned: {0}"
                ).format(", ".join(unscanned_items)),
            }

        # Update workflow state
        stock_entry.workflow_state = "Completed"
        stock_entry.custom_target_approved_by = frappe.session.user
        stock_entry.custom_target_approved_date = now()
        stock_entry.custom_target_remarks = target_remarks

        # Submit the document to finalize the transfer
        stock_entry.submit()
        frappe.db.commit()

        # Log completion
        create_transfer_log(
            transfer_id, "Completed", f"Transfer completed by {frappe.session.user}"
        )

        # Send completion notifications
        send_transfer_notification(stock_entry, "completed")

        return {
            "success": True,
            "message": _("Stock transfer completed successfully"),
            "status": "Completed",
        }

    except Exception as e:
        frappe.log_error(f"Transfer completion failed: {str(e)}")
        return {"success": False, "message": _("Failed to complete transfer: {0}").format(str(e))}


@frappe.whitelist()
def get_transfer_details(transfer_id):
    """
    Get detailed information about a stock transfer

    Args:
        transfer_id (str): Stock Entry ID

    Returns:
        dict: Transfer details
    """
    try:
        stock_entry = frappe.get_doc("Stock Entry", transfer_id)

        # Get transfer items with scan status
        items = []
        for item in stock_entry.items:
            item_data = {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": item.qty,
                "uom": item.uom,
                "basic_rate": item.basic_rate,
                "basic_amount": item.basic_amount,
                "source_scanned": item.custom_source_scanned or 0,
                "target_scanned": item.custom_target_scanned or 0,
                "source_scan_time": item.custom_source_scan_time,
                "target_scan_time": item.custom_target_scan_time,
            }
            items.append(item_data)

        # Get transfer logs
        logs = get_transfer_logs(transfer_id)

        return {
            "transfer_id": transfer_id,
            "from_warehouse": stock_entry.from_warehouse,
            "to_warehouse": stock_entry.to_warehouse,
            "status": stock_entry.workflow_state,
            "priority": stock_entry.custom_transfer_priority,
            "requested_by": stock_entry.custom_requested_by,
            "requested_date": stock_entry.custom_requested_date,
            "source_approved_by": stock_entry.custom_source_approved_by,
            "target_approved_by": stock_entry.custom_target_approved_by,
            "total_value": stock_entry.total_outgoing_value,
            "remarks": stock_entry.remarks,
            "items": items,
            "logs": logs,
        }

    except Exception as e:
        frappe.log_error(f"Get transfer details failed: {str(e)}")
        return {
            "success": False,
            "message": _("Failed to get transfer details: {0}").format(str(e)),
        }


# Helper Functions


def find_item_by_barcode(barcode):
    """Find item code by barcode"""
    # Check Item Barcode table first
    item_barcode = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
    if item_barcode:
        return item_barcode

    # Check if barcode matches item code directly
    if frappe.db.exists("Item", barcode):
        return barcode

    # Check custom barcode fields
    item_code = frappe.db.get_value("Item", {"custom_barcode": barcode}, "name")
    return item_code


def get_item_valuation_rate(item_code, warehouse):
    """Get item valuation rate for warehouse"""
    valuation_rate = frappe.db.get_value(
        "Stock Ledger Entry",
        {"item_code": item_code, "warehouse": warehouse, "is_cancelled": 0},
        "valuation_rate",
        order_by="posting_date desc, posting_time desc",
    )
    return flt(valuation_rate) if valuation_rate else 0


def create_transfer_log(transfer_id, status, remarks):
    """Create transfer log entry"""
    try:
        log_entry = frappe.new_doc("Stock Transfer Log")
        log_entry.transfer_id = transfer_id
        log_entry.status = status
        log_entry.remarks = remarks
        log_entry.user = frappe.session.user
        log_entry.timestamp = now()
        log_entry.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed to create transfer log: {str(e)}")


def get_transfer_logs(transfer_id):
    """Get transfer logs for a transfer"""
    logs = frappe.get_list(
        "Stock Transfer Log",
        filters={"transfer_id": transfer_id},
        fields=["status", "remarks", "user", "timestamp"],
        order_by="timestamp desc",
    )
    return logs


def send_transfer_notification(stock_entry, event_type):
    """Send transfer notification"""
    try:
        if event_type == "source_approved":
            # Notify target warehouse users
            subject = _("Stock Transfer Ready for Receipt: {0}").format(stock_entry.name)
            message = _(
                "Stock transfer from {0} to {1} has been approved and is ready for receipt."
            ).format(stock_entry.from_warehouse, stock_entry.to_warehouse)
        elif event_type == "completed":
            # Notify requestor and source warehouse
            subject = _("Stock Transfer Completed: {0}").format(stock_entry.name)
            message = _("Stock transfer from {0} to {1} has been completed successfully.").format(
                stock_entry.from_warehouse, stock_entry.to_warehouse
            )

        # Send email notification (implement based on requirements)
        # frappe.sendmail(recipients=recipients, subject=subject, message=message)

    except Exception as e:
        frappe.log_error(f"Notification failed: {str(e)}")


# Dashboard and Analytics Functions


@frappe.whitelist()
def get_transfer_dashboard_data(warehouse=None, date_range=30):
    """
    Get dashboard data for stock transfers

    Args:
        warehouse (str): Filter by warehouse
        date_range (int): Number of days to analyze

    Returns:
        dict: Dashboard data
    """
    try:
        from_date = frappe.utils.add_days(nowdate(), -date_range)

        filters = {"stock_entry_type": "Material Transfer", "posting_date": [">=", from_date]}

        if warehouse:
            filters["from_warehouse"] = warehouse

        # Get transfer statistics
        transfers = frappe.get_list(
            "Stock Entry",
            filters=filters,
            fields=[
                "name",
                "workflow_state",
                "posting_date",
                "total_outgoing_value",
                "custom_transfer_priority",
            ],
        )

        # Calculate metrics
        total_transfers = len(transfers)
        completed_transfers = len([t for t in transfers if t.workflow_state == "Completed"])
        pending_transfers = len(
            [
                t
                for t in transfers
                if t.workflow_state != "Completed" and t.workflow_state != "Cancelled"
            ]
        )
        total_value = sum([flt(t.total_outgoing_value) for t in transfers])

        # Priority breakdown
        high_priority = len([t for t in transfers if t.custom_transfer_priority == "High"])
        medium_priority = len([t for t in transfers if t.custom_transfer_priority == "Medium"])
        low_priority = len([t for t in transfers if t.custom_transfer_priority == "Low"])

        # Calculate completion rate
        completion_rate = (
            (completed_transfers / total_transfers * 100) if total_transfers > 0 else 0
        )

        return {
            "total_transfers": total_transfers,
            "completed_transfers": completed_transfers,
            "pending_transfers": pending_transfers,
            "completion_rate": round(completion_rate, 2),
            "total_value": total_value,
            "priority_breakdown": {
                "high": high_priority,
                "medium": medium_priority,
                "low": low_priority,
            },
            "date_range": date_range,
        }

    except Exception as e:
        frappe.log_error(f"Dashboard data failed: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist()
def get_warehouse_transfer_activity(warehouse, limit=10):
    """
    Get recent transfer activity for a warehouse

    Args:
        warehouse (str): Warehouse name
        limit (int): Number of records

    Returns:
        list: Recent transfer activity
    """
    try:
        # Get transfers involving this warehouse
        transfers = frappe.db.sql(
            """
            SELECT 
                name, from_warehouse, to_warehouse, posting_date,
                workflow_state, total_outgoing_value, custom_transfer_priority,
                CASE 
                    WHEN from_warehouse = %(warehouse)s THEN 'Outgoing'
                    WHEN to_warehouse = %(warehouse)s THEN 'Incoming'
                    ELSE 'Unknown'
                END as direction
            FROM `tabStock Entry`
            WHERE stock_entry_type = 'Material Transfer'
            AND (from_warehouse = %(warehouse)s OR to_warehouse = %(warehouse)s)
            AND posting_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY posting_date DESC, modified DESC
            LIMIT %(limit)s
        """,
            {"warehouse": warehouse, "limit": limit},
            as_dict=True,
        )

        return transfers

    except Exception as e:
        frappe.log_error(f"Warehouse activity failed: {str(e)}")
        return []
