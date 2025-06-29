"""
Mobile Inventory Scanner Controller
Handles context and authentication for mobile barcode scanning interface
"""

import frappe
from frappe import _


def get_context(context):
    """
    Get context for mobile inventory scanner page
    
    Args:
        context: Page context dictionary
        
    Returns:
        Updated context with required data
    """
    
    # Check if user is logged in
    if frappe.session.user == 'Guest':
        frappe.throw(_("Please login to access the mobile inventory scanner"), frappe.PermissionError)
    
    # Get user info
    user = frappe.get_doc("User", frappe.session.user)
    context.user = user
    
    # Check user permissions
    if not frappe.has_permission("Item", "read"):
        frappe.throw(_("You do not have permission to access inventory items"), frappe.PermissionError)
    
    # Get default warehouse for user
    default_warehouse = frappe.db.get_value("User", frappe.session.user, "default_warehouse")
    if not default_warehouse:
        # Get first available warehouse
        warehouses = frappe.get_list("Warehouse", {"is_group": 0}, ["name"], limit=1)
        default_warehouse = warehouses[0].name if warehouses else None
    
    context.default_warehouse = default_warehouse
    
    # Get available warehouses for user
    warehouses = frappe.get_list(
        "Warehouse",
        filters={"is_group": 0},
        fields=["name", "warehouse_name"],
        order_by="warehouse_name"
    )
    context.warehouses = warehouses
    
    # Get language preference
    context.language = frappe.local.lang or 'en'
    context.direction = 'rtl' if context.language == 'ar' else 'ltr'
    
    # Add page metadata
    context.title = _("Mobile Inventory Scanner")
    context.show_sidebar = False
    context.show_header = False
    
    # Add translation strings for JavaScript
    context.translations = {
        # Scanner messages
        'scan_barcode': _('Scan Barcode'),
        'manual_entry': _('Manual Entry'),
        'camera_not_supported': _('Camera not supported on this device'),
        'camera_permission_denied': _('Camera permission denied'),
        'barcode_scanned': _('Barcode scanned successfully'),
        'item_not_found': _('Item not found for this barcode'),
        'scanning_error': _('Error scanning barcode'),
        
        # Operation modes
        'lookup_mode': _('Lookup Mode'),
        'receive_mode': _('Receive Mode'),
        'issue_mode': _('Issue Mode'),
        'adjust_mode': _('Adjust Mode'),
        
        # Stock operations
        'stock_take': _('Stock Take'),
        'cycle_count': _('Cycle Count'),
        'stock_transfer': _('Stock Transfer'),
        'batch_scan': _('Batch Scan'),
        
        # Status messages
        'online': _('Online'),
        'offline': _('Offline'),
        'syncing': _('Syncing'),
        'sync_complete': _('Sync Complete'),
        'sync_error': _('Sync Error'),
        'pending_sync': _('Pending Sync'),
        
        # Item details
        'item_code': _('Item Code'),
        'item_name': _('Item Name'),
        'current_stock': _('Current Stock'),
        'warehouse': _('Warehouse'),
        'batch_no': _('Batch No'),
        'serial_no': _('Serial No'),
        'qty_counted': _('Qty Counted'),
        'difference': _('Difference'),
        
        # Actions
        'save': _('Save'),
        'cancel': _('Cancel'),
        'clear_all': _('Clear All'),
        'export_data': _('Export Data'),
        'import_data': _('Import Data'),
        'settings': _('Settings'),
        
        # Validation messages
        'quantity_required': _('Quantity is required'),
        'warehouse_required': _('Warehouse is required'),
        'invalid_quantity': _('Invalid quantity entered'),
        'confirm_clear': _('Are you sure you want to clear all data?'),
        'confirm_save': _('Save changes?'),
        
        # Arabic-specific messages
        'switch_to_arabic': _('Switch to Arabic'),
        'switch_to_english': _('Switch to English'),
        'right_to_left': _('Right to Left'),
        'left_to_right': _('Left to Right'),
    }
    
    return context


@frappe.whitelist()
def get_mobile_scanner_config():
    """
    Get configuration for mobile scanner
    
    Returns:
        dict: Scanner configuration
    """
    
    return {
        "default_warehouse": frappe.db.get_value("User", frappe.session.user, "default_warehouse"),
        "language": frappe.local.lang or 'en',
        "company": frappe.defaults.get_defaults().get("company"),
        "currency": frappe.defaults.get_defaults().get("currency"),
        "date_format": frappe.db.get_default("date_format") or "dd-mm-yyyy",
        "time_format": frappe.db.get_default("time_format") or "HH:mm:ss",
        "scanner_settings": {
            "auto_focus": True,
            "enable_flashlight": True,
            "scan_timeout": 30000,  # 30 seconds
            "continuous_scan": False,
            "audio_feedback": True,
            "vibration_feedback": True,
            "supported_formats": ["CODE_128", "EAN_13", "EAN_8", "CODE_39", "QR_CODE"]
        },
        "offline_settings": {
            "enable_offline": True,
            "max_offline_records": 1000,
            "auto_sync_interval": 300000,  # 5 minutes
            "retry_attempts": 3,
            "sync_on_reconnect": True
        }
    }


@frappe.whitelist()
def save_scan_session(session_data):
    """
    Save scan session data for offline sync
    
    Args:
        session_data (dict): Session data to save
        
    Returns:
        dict: Save result
    """
    
    try:
        # Validate session data
        if not session_data or not isinstance(session_data, dict):
            frappe.throw(_("Invalid session data"))
        
        # Create scan session record
        session_doc = frappe.get_doc({
            "doctype": "Mobile Scan Session",
            "user": frappe.session.user,
            "session_id": session_data.get("session_id"),
            "scan_mode": session_data.get("scan_mode"),
            "warehouse": session_data.get("warehouse"),
            "start_time": session_data.get("start_time"),
            "end_time": session_data.get("end_time"),
            "total_scans": len(session_data.get("scans", [])),
            "status": "Completed",
            "sync_status": "Pending"
        })
        
        # Add scan details
        for scan in session_data.get("scans", []):
            session_doc.append("scans", {
                "item_code": scan.get("item_code"),
                "barcode": scan.get("barcode"),
                "warehouse": scan.get("warehouse"),
                "quantity": scan.get("quantity"),
                "operation": scan.get("operation"),
                "timestamp": scan.get("timestamp"),
                "location": scan.get("location")
            })
        
        # Insert session
        session_doc.insert()
        frappe.db.commit()
        
        return {
            "success": True,
            "session_name": session_doc.name,
            "message": _("Scan session saved successfully")
        }
        
    except Exception as e:
        frappe.log_error(f"Error saving scan session: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": _("Error saving scan session")
        }


@frappe.whitelist()
def process_batch_scans(scans_data):
    """
    Process multiple scans in batch for better performance
    
    Args:
        scans_data (list): List of scan records
        
    Returns:
        dict: Processing result
    """
    
    try:
        processed_scans = []
        errors = []
        
        for scan in scans_data:
            try:
                # Validate scan data
                if not scan.get("barcode") or not scan.get("operation"):
                    errors.append({
                        "barcode": scan.get("barcode"),
                        "error": _("Missing required fields")
                    })
                    continue
                
                # Process individual scan
                result = process_single_scan(scan)
                processed_scans.append(result)
                
            except Exception as e:
                errors.append({
                    "barcode": scan.get("barcode"),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "processed": len(processed_scans),
            "errors": len(errors),
            "results": processed_scans,
            "error_details": errors
        }
        
    except Exception as e:
        frappe.log_error(f"Error processing batch scans: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": _("Error processing batch scans")
        }


def process_single_scan(scan_data):
    """
    Process a single scan record
    
    Args:
        scan_data (dict): Scan data
        
    Returns:
        dict: Processing result
    """
    
    operation = scan_data.get("operation")
    barcode = scan_data.get("barcode")
    quantity = float(scan_data.get("quantity", 1))
    warehouse = scan_data.get("warehouse")
    
    # Get item by barcode
    item_code = frappe.db.get_value("Item Barcode", {"barcode": barcode}, "parent")
    if not item_code:
        # Try direct item code lookup
        if frappe.db.exists("Item", barcode):
            item_code = barcode
        else:
            frappe.throw(_("Item not found for barcode: {0}").format(barcode))
    
    # Get item details
    item = frappe.get_doc("Item", item_code)
    
    # Process based on operation type
    if operation == "stock_take":
        return process_stock_take(item_code, warehouse, quantity, scan_data)
    elif operation == "cycle_count":
        return process_cycle_count(item_code, warehouse, quantity, scan_data)
    elif operation == "receive":
        return process_stock_receive(item_code, warehouse, quantity, scan_data)
    elif operation == "issue":
        return process_stock_issue(item_code, warehouse, quantity, scan_data)
    elif operation == "adjust":
        return process_stock_adjust(item_code, warehouse, quantity, scan_data)
    else:
        # Default lookup operation
        return {
            "item_code": item_code,
            "item_name": item.item_name,
            "barcode": barcode,
            "operation": "lookup",
            "success": True
        }


def process_stock_take(item_code, warehouse, counted_qty, scan_data):
    """Process stock take operation"""
    
    # Get current stock
    current_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
    difference = counted_qty - current_qty
    
    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "current_qty": current_qty,
        "counted_qty": counted_qty,
        "difference": difference,
        "operation": "stock_take",
        "requires_adjustment": abs(difference) > 0,
        "success": True
    }


def process_cycle_count(item_code, warehouse, counted_qty, scan_data):
    """Process cycle count operation"""
    
    # Similar to stock take but with cycle count specific logic
    current_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
    difference = counted_qty - current_qty
    
    # Create cycle count record
    cycle_count = frappe.get_doc({
        "doctype": "Cycle Count Entry",
        "item_code": item_code,
        "warehouse": warehouse,
        "expected_qty": current_qty,
        "counted_qty": counted_qty,
        "difference": difference,
        "count_date": frappe.utils.now(),
        "counted_by": frappe.session.user,
        "status": "Pending Approval" if abs(difference) > 0 else "Completed"
    })
    
    try:
        cycle_count.insert()
        frappe.db.commit()
        
        return {
            "item_code": item_code,
            "warehouse": warehouse,
            "current_qty": current_qty,
            "counted_qty": counted_qty,
            "difference": difference,
            "operation": "cycle_count",
            "cycle_count_name": cycle_count.name,
            "success": True
        }
    except Exception as e:
        return {
            "item_code": item_code,
            "operation": "cycle_count",
            "error": str(e),
            "success": False
        }


def process_stock_receive(item_code, warehouse, quantity, scan_data):
    """Process stock receive operation"""
    
    # This would typically create a Stock Entry for Material Receipt
    # For now, return the data for batch processing
    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "quantity": quantity,
        "operation": "receive",
        "pending_entry": True,
        "success": True
    }


def process_stock_issue(item_code, warehouse, quantity, scan_data):
    """Process stock issue operation"""
    
    # Check available stock
    available_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
    
    if quantity > available_qty:
        return {
            "item_code": item_code,
            "warehouse": warehouse,
            "requested_qty": quantity,
            "available_qty": available_qty,
            "operation": "issue",
            "error": _("Insufficient stock available"),
            "success": False
        }
    
    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "quantity": quantity,
        "available_qty": available_qty,
        "operation": "issue",
        "pending_entry": True,
        "success": True
    }


def process_stock_adjust(item_code, warehouse, new_quantity, scan_data):
    """Process stock adjustment operation"""
    
    current_qty = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
    difference = new_quantity - current_qty
    
    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "current_qty": current_qty,
        "new_qty": new_quantity,
        "difference": difference,
        "operation": "adjust",
        "pending_entry": True,
        "success": True
    }
