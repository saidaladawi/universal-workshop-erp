# universal_workshop/parts_inventory/warehouse_management.py
"""
Multi-Location Warehouse Management System for Universal Workshop ERP
Supports hierarchical warehouse structures, automated transfer workflows,
and mobile-responsive stock management for automotive workshops.
"""

import json
from typing import Any, Dict, List, Optional

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, now_datetime, nowdate
from universal_workshop.utils.arabic_utils import ArabicTextUtils


class WarehouseLocationManager:
    """Manages multi-location warehouse operations for automotive workshops"""

    @staticmethod
    def get_workshop_warehouse_hierarchy(workshop_id: str) -> dict[str, Any]:
        """Get complete warehouse hierarchy for a workshop"""

        warehouses = frappe.db.sql(
            """
            SELECT
                w.name,
                w.warehouse_name,
                w.parent_warehouse,
                w.warehouse_type,
                w.is_group,
                w.company
            FROM `tabWarehouse` w
            WHERE w.company = %(company)s
            ORDER BY w.lft
        """,
            {"company": frappe.defaults.get_user_default("Company")},
            as_dict=True,
        )

        # Build hierarchy tree
        hierarchy: dict[str, Any] = {
            "main_storage": [],
            "service_bays": [],
            "mobile_units": [],
            "scrap_areas": [],
            "tools_storage": [],
        }

        for warehouse in warehouses:
            # Categorize warehouses based on naming patterns
            wh_name = warehouse.warehouse_name.lower()
            if "service bay" in wh_name or "bay" in wh_name:
                hierarchy["service_bays"].append(warehouse)
            elif "scrap" in wh_name:
                hierarchy["scrap_areas"].append(warehouse)
            elif "tool" in wh_name:
                hierarchy["tools_storage"].append(warehouse)
            elif "mobile" in wh_name:
                hierarchy["mobile_units"].append(warehouse)
            else:
                hierarchy["main_storage"].append(warehouse)

        return hierarchy

    @staticmethod
    def create_workshop_warehouse_structure(workshop_profile: str) -> dict[str, str]:
        """Create default warehouse structure for new workshop"""

        workshop = frappe.get_doc("Workshop Profile", workshop_profile)
        company = workshop.company or frappe.defaults.get_user_default("Company")

        # Main workshop warehouse (group)
        main_warehouse = frappe.new_doc("Warehouse")
        main_warehouse.warehouse_name = f"{workshop.workshop_name} - Main"
        main_warehouse.company = company
        main_warehouse.is_group = 1
        main_warehouse.insert()

        warehouses_created = {"main": main_warehouse.name}

        # Create sub-warehouses
        sub_warehouses = [
            {"name": "Parts Storage", "type": "parts_storage"},
            {"name": "Service Bay 1", "type": "service_bay"},
            {"name": "Service Bay 2", "type": "service_bay"},
            {"name": "Tools Storage", "type": "tools_storage"},
            {"name": "Scrap Area", "type": "scrap_area"},
        ]

        for sub_wh in sub_warehouses:
            warehouse = frappe.new_doc("Warehouse")
            warehouse.warehouse_name = f"{workshop.workshop_name} - {sub_wh['name']}"
            warehouse.parent_warehouse = main_warehouse.name
            warehouse.company = company
            warehouse.is_group = 0
            warehouse.insert()

            warehouses_created[sub_wh["type"]] = warehouse.name

        return warehouses_created


class StockTransferWorkflow:
    """Handles automated stock transfer workflows with approval processes"""

    @staticmethod
    def create_transfer_request(
        source_warehouse: str,
        target_warehouse: str,
        items: list[dict],
        purpose: str = "Material Transfer",
        requester: str | None = None,
        service_order: str | None = None,
        auto_approve: bool = False,
    ) -> str:
        """Create stock transfer request with workflow"""

        # Create Stock Entry
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.stock_entry_type = "Material Transfer"
        stock_entry.purpose = purpose
        stock_entry.from_warehouse = source_warehouse
        stock_entry.to_warehouse = target_warehouse
        stock_entry.posting_date = nowdate()
        stock_entry.posting_time = now_datetime().strftime("%H:%M:%S")

        # Add items
        total_value = 0
        for item_data in items:
            item = stock_entry.append("items", {})
            item.item_code = item_data.get("item_code")
            item.qty = flt(item_data.get("qty"))
            item.s_warehouse = source_warehouse
            item.t_warehouse = target_warehouse

            # Get item details
            item_doc = frappe.get_doc("Item", item.item_code)
            item.uom = item_doc.stock_uom
            item.conversion_factor = 1

            # Get valuation rate
            valuation_rate = (
                frappe.db.get_value(
                    "Stock Ledger Entry",
                    {"item_code": item.item_code, "warehouse": source_warehouse},
                    "valuation_rate",
                )
                or item_doc.valuation_rate
                or 0
            )

            item.basic_rate = valuation_rate
            item.basic_amount = flt(item.qty) * flt(valuation_rate)
            total_value += item.basic_amount

        stock_entry.total_outgoing_value = total_value
        stock_entry.value_difference = 0

        # Set approval status based on transfer value and type
        if auto_approve or StockTransferWorkflow._should_auto_approve(total_value, purpose):
            stock_entry.docstatus = 1
        else:
            stock_entry.docstatus = 0

        stock_entry.insert()

        if stock_entry.docstatus == 1:
            stock_entry.submit()
            StockTransferWorkflow._notify_transfer_completion(stock_entry.name)
        else:
            StockTransferWorkflow._notify_approval_required(stock_entry.name)

        return stock_entry.name

    @staticmethod
    def _should_auto_approve(total_value: float, purpose: str) -> bool:
        """Determine if transfer should be auto-approved"""
        auto_approve_threshold = 1000  # Default threshold

        # Auto approve small value transfers and specific purposes
        if total_value <= auto_approve_threshold:
            return True

        auto_approve_purposes = ["Material Transfer", "Service Bay Transfer", "Tools Movement"]

        return purpose in auto_approve_purposes

    @staticmethod
    def approve_transfer(stock_entry_name: str, approver: str | None = None) -> bool:
        """Approve pending stock transfer"""

        stock_entry = frappe.get_doc("Stock Entry", stock_entry_name)

        if stock_entry.docstatus != 0:
            frappe.throw(_("Transfer is already processed"))

        # Submit the transfer
        stock_entry.submit()

        StockTransferWorkflow._notify_transfer_completion(stock_entry_name)

        return True

    @staticmethod
    def _notify_transfer_completion(stock_entry_name: str):
        """Send notification on transfer completion"""
        try:
            frappe.msgprint(_("Stock transfer {0} completed successfully").format(stock_entry_name))
        except Exception as e:
            frappe.log_error(f"Transfer notification failed: {e!s}")

    @staticmethod
    def _notify_approval_required(stock_entry_name: str):
        """Send notification for approval requirement"""
        try:
            frappe.msgprint(_("Stock transfer {0} requires approval").format(stock_entry_name))
        except Exception as e:
            frappe.log_error(f"Approval notification failed: {e!s}")


class MobileStockInterface:
    """Mobile-optimized interface for stock operations"""

    @staticmethod
    @frappe.whitelist()
    def get_mobile_dashboard_data(warehouse: str | None = None) -> dict[str, Any]:
        """Get dashboard data optimized for mobile interface"""

        user_warehouses = MobileStockInterface._get_user_warehouses()
        current_warehouse = warehouse or user_warehouses[0]["name"] if user_warehouses else None

        if not current_warehouse:
            return {"error": "No accessible warehouses found"}

        # Get current stock levels
        stock_data = frappe.db.sql(
            """
            SELECT
                i.item_code,
                i.item_name,
                b.actual_qty,
                b.reserved_qty,
                b.projected_qty,
                i.stock_uom
            FROM `tabBin` b
            JOIN `tabItem` i ON b.item_code = i.item_code
            WHERE b.warehouse = %(warehouse)s
            AND b.actual_qty > 0
            ORDER BY b.actual_qty ASC
            LIMIT 50
        """,
            {"warehouse": current_warehouse},
            as_dict=True,
        )

        # Get pending transfers
        pending_transfers = frappe.get_all(
            "Stock Entry",
            {"docstatus": 0, "from_warehouse": current_warehouse},
            ["name", "posting_date", "total_outgoing_value"],
        )

        return {
            "current_warehouse": {
                "name": current_warehouse,
                "display_name": frappe.db.get_value(
                    "Warehouse", current_warehouse, "warehouse_name"
                ),
            },
            "user_warehouses": user_warehouses,
            "stock_summary": {
                "total_items": len(stock_data),
                "pending_transfers": len(pending_transfers),
            },
            "stock_data": stock_data[:20],  # Limit for mobile
            "pending_transfers": pending_transfers,
            "quick_actions": MobileStockInterface._get_quick_actions(current_warehouse),
        }

    @staticmethod
    def _get_user_warehouses() -> list[dict]:
        """Get warehouses accessible to current user"""

        warehouses = frappe.get_all(
            "Warehouse", {"is_group": 0, "disabled": 0}, ["name", "warehouse_name"]
        )

        return warehouses

    @staticmethod
    def _get_quick_actions(warehouse: str) -> list[dict]:
        """Get quick actions for mobile interface"""

        return [
            {
                "id": "scan_item",
                "title": _("Scan Item"),
                "icon": "qr-code",
                "action": "open_scanner",
            },
            {
                "id": "request_transfer",
                "title": _("Request Transfer"),
                "icon": "exchange-alt",
                "action": "open_transfer_form",
            },
            {
                "id": "stock_check",
                "title": _("Stock Check"),
                "icon": "clipboard-list",
                "action": "open_stock_check",
            },
        ]

    @staticmethod
    @frappe.whitelist()
    def create_mobile_transfer_request(
        from_warehouse: str,
        to_warehouse: str,
        items: str,  # JSON string
        purpose: str = "Material Transfer",
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create transfer request from mobile interface"""

        try:
            items_data = json.loads(items) if isinstance(items, str) else items

            # Create transfer request
            transfer_name = StockTransferWorkflow.create_transfer_request(
                source_warehouse=from_warehouse,
                target_warehouse=to_warehouse,
                items=items_data,
                purpose=purpose,
                requester=frappe.session.user,
            )

            return {
                "success": True,
                "transfer_id": transfer_name,
                "message": _("Transfer request created successfully"),
            }

        except Exception as e:
            frappe.log_error(f"Mobile transfer request failed: {e!s}")
            return {"error": _("Failed to create transfer request")}


class LocationBasedStockAllocation:
    """Manages location-based stock allocation and reservation"""

    @staticmethod
    def allocate_parts_for_service_order(service_order: str) -> dict[str, Any]:
        """Allocate parts for service order across multiple locations"""

        # Get service order details
        service_doc = frappe.get_doc("Service Order", service_order)
        required_parts = service_doc.get("required_parts", [])

        if not required_parts:
            return {"message": "No parts required for this service order"}

        # Get workshop warehouses hierarchy
        workshop_warehouses = WarehouseLocationManager.get_workshop_warehouse_hierarchy(
            service_doc.workshop_id
        )

        allocation_results = []

        for part in required_parts:
            item_code = part.get("item_code")
            required_qty = flt(part.get("qty"))

            # Check availability across locations
            availability = LocationBasedStockAllocation._check_item_availability(
                item_code, workshop_warehouses
            )

            # Allocate from best available locations
            allocation = LocationBasedStockAllocation._allocate_item_quantity(
                item_code, required_qty, availability
            )

            allocation_results.append(
                {
                    "item_code": item_code,
                    "required_qty": required_qty,
                    "allocation": allocation,
                    "fully_allocated": sum(a["qty"] for a in allocation) >= required_qty,
                }
            )

        return {
            "service_order": service_order,
            "allocations": allocation_results,
            "requires_procurement": any(
                not result["fully_allocated"] for result in allocation_results
            ),
        }

    @staticmethod
    def _check_item_availability(item_code: str, warehouses: dict) -> list[dict]:
        """Check item availability across warehouse hierarchy"""

        all_warehouses = []
        for _location_type, wh_list in warehouses.items():
            all_warehouses.extend([wh["name"] for wh in wh_list])

        if not all_warehouses:
            return []

        availability = frappe.db.sql(
            """
            SELECT
                b.warehouse,
                b.actual_qty,
                b.reserved_qty,
                (b.actual_qty - b.reserved_qty) as available_qty,
                w.warehouse_name,
                cw.location_type,
                cw.service_bay_number
            FROM `tabBin` b
            JOIN `tabWarehouse` w ON b.warehouse = w.name
            LEFT JOIN `tabCustom Warehouse Fields` cw ON w.name = cw.parent
            WHERE b.item_code = %(item_code)s
            AND b.warehouse IN %(warehouses)s
            AND (b.actual_qty - b.reserved_qty) > 0
            ORDER BY cw.location_type, b.actual_qty DESC
        """,
            {"item_code": item_code, "warehouses": all_warehouses},
            as_dict=True,
        )

        return availability

    @staticmethod
    def _allocate_item_quantity(
        item_code: str, required_qty: float, availability: list[dict]
    ) -> list[dict]:
        """Allocate required quantity from available locations"""

        allocation = []
        remaining_qty = required_qty

        # Prioritize allocation: parts_storage -> main_storage -> service_bays
        priority_order = ["parts_storage", "main_storage", "service_bay", "tools_storage"]

        for location_type in priority_order:
            if remaining_qty <= 0:
                break

            # Get warehouses of this type with available stock
            type_warehouses = [
                wh
                for wh in availability
                if wh.get("location_type") == location_type and wh.available_qty > 0
            ]

            for warehouse in type_warehouses:
                if remaining_qty <= 0:
                    break

                allocated_qty = min(remaining_qty, warehouse.available_qty)

                allocation.append(
                    {
                        "warehouse": warehouse.warehouse,
                        "warehouse_name": warehouse.warehouse_name,
                        "qty": allocated_qty,
                        "location_type": warehouse.location_type,
                    }
                )

                remaining_qty -= allocated_qty

        return allocation


# API Methods for frontend integration
@frappe.whitelist()
def get_workshop_warehouses(workshop_id=None):
    """Get workshop warehouse hierarchy for frontend"""
    if not workshop_id:
        workshop_id = frappe.defaults.get_user_default("workshop_id")

    if not workshop_id:
        return WarehouseLocationManager.get_workshop_warehouse_hierarchy(None)

    return WarehouseLocationManager.get_workshop_warehouse_hierarchy(workshop_id)


@frappe.whitelist()
def create_transfer_request(from_warehouse, to_warehouse, items, purpose="Material Transfer"):
    """API method to create transfer request"""
    try:
        items_data = json.loads(items) if isinstance(items, str) else items

        transfer_id = StockTransferWorkflow.create_transfer_request(
            source_warehouse=from_warehouse,
            target_warehouse=to_warehouse,
            items=items_data,
            purpose=purpose,
            requester=frappe.session.user,
        )

        return {"success": True, "transfer_id": transfer_id}

    except Exception as e:
        frappe.log_error(f"Transfer request creation failed: {e!s}")
        return {"error": str(e)}


@frappe.whitelist()
def get_mobile_dashboard():
    """Get mobile dashboard data"""
    return MobileStockInterface.get_mobile_dashboard_data()


@frappe.whitelist()
def approve_stock_transfer(transfer_id):
    """Approve a pending stock transfer (mobile API)"""
    try:
        return StockTransferWorkflow.approve_transfer(transfer_id, frappe.session.user)
    except Exception as e:
        frappe.log_error(f"Stock transfer approval failed: {str(e)}")
        return {"success": False, "message": str(e)}


def validate_stock_transfer(doc, method):
    """Validate stock transfer operations for automotive parts"""
    try:
        # Skip validation for non-parts transfers
        if doc.purpose not in ['Material Transfer', 'Material Transfer for Manufacture']:
            return

        # Validate source and target warehouses
        if not doc.from_warehouse or not doc.to_warehouse:
            frappe.throw(_("Source and target warehouses are required for parts transfer"))

        # Check if warehouses belong to the same workshop
        from_company = frappe.db.get_value("Warehouse", doc.from_warehouse, "company")
        to_company = frappe.db.get_value("Warehouse", doc.to_warehouse, "company")

        if from_company != to_company:
            frappe.throw(_("Stock transfer between different companies requires approval"))

        # Validate item quantities and availability
        for item in doc.items:
            if item.qty <= 0:
                frappe.throw(_("Transfer quantity must be greater than zero for item {0}").format(item.item_code))

            # Check stock availability
            available_qty = frappe.db.get_value("Bin",
                {"item_code": item.item_code, "warehouse": doc.from_warehouse},
                "actual_qty") or 0

            if available_qty < item.qty:
                frappe.throw(_("Insufficient stock for item {0}. Available: {1}, Required: {2}")
                    .format(item.item_code, available_qty, item.qty))

        # Log validation for audit trail
        create_transfer_log(doc, "validation_passed", method)

    except Exception as e:
        frappe.log_error(f"Stock transfer validation error: {str(e)}", "Parts Inventory")
        raise


def on_stock_transfer_submit(doc, method):
    """Handle post-submission processing for stock transfers"""
    try:
        # Update stock levels and create movement history
        for item in doc.items:
            # Create stock movement record
            create_stock_movement_record(doc, item)

            # Update reorder alerts if needed
            check_reorder_levels(item.item_code, doc.to_warehouse)

            # Update parts location tracking
            update_parts_location(item.item_code, doc.from_warehouse, doc.to_warehouse, item.qty)

        # Create transfer completion log
        create_transfer_log(doc, "completed", method)

        # Send notifications if configured
        send_transfer_notifications(doc)

    except Exception as e:
        frappe.log_error(f"Stock transfer submit error: {str(e)}", "Parts Inventory")
        raise


def setup_warehouse_defaults(doc, method):
    """Setup default configurations for new warehouses"""
    try:
        # Set default warehouse properties for automotive parts
        if not doc.warehouse_type:
            doc.warehouse_type = "Stock"

        # Create default bins for common automotive part categories
        default_categories = [
            "Engine Parts", "Transmission Parts", "Brake Parts",
            "Suspension Parts", "Electrical Parts", "Body Parts",
            "Interior Parts", "Exhaust Parts", "Cooling Parts", "Fuel Parts"
        ]

        # Setup bin locations based on warehouse type
        if doc.warehouse_type == "Stock":
            setup_stock_warehouse_bins(doc, default_categories)
        elif doc.warehouse_type == "Service":
            setup_service_bay_bins(doc)
        elif doc.warehouse_type == "Mobile":
            setup_mobile_unit_bins(doc)

        # Configure reorder settings
        setup_warehouse_reorder_settings(doc)

        # Create warehouse-specific permissions
        setup_warehouse_permissions(doc)

    except Exception as e:
        frappe.log_error(f"Warehouse setup error: {str(e)}", "Parts Inventory")


def setup_stock_warehouse_bins(warehouse_doc, categories):
    """Setup bin locations for stock warehouses"""
    for category in categories:
        bin_code = f"{warehouse_doc.name}-{category.replace(' ', '-').upper()}"

        # Create bin if not exists
        if not frappe.db.exists("Warehouse", bin_code):
            bin_doc = frappe.new_doc("Warehouse")
            bin_doc.warehouse_name = f"{warehouse_doc.warehouse_name} - {category}"
            bin_doc.parent_warehouse = warehouse_doc.name
            bin_doc.company = warehouse_doc.company
            bin_doc.warehouse_type = "Stock"
            bin_doc.is_group = 0
            bin_doc.insert()


def setup_service_bay_bins(warehouse_doc):
    """Setup bin locations for service bay warehouses"""
    service_areas = ["Tools", "Consumables", "Common Parts", "Work in Progress"]

    for area in service_areas:
        bin_code = f"{warehouse_doc.name}-{area.replace(' ', '-').upper()}"

        if not frappe.db.exists("Warehouse", bin_code):
            bin_doc = frappe.new_doc("Warehouse")
            bin_doc.warehouse_name = f"{warehouse_doc.warehouse_name} - {area}"
            bin_doc.parent_warehouse = warehouse_doc.name
            bin_doc.company = warehouse_doc.company
            bin_doc.warehouse_type = "Stock"
            bin_doc.is_group = 0
            bin_doc.insert()


def setup_mobile_unit_bins(warehouse_doc):
    """Setup bin locations for mobile unit warehouses"""
    mobile_areas = ["Emergency Parts", "Common Tools", "Fluids", "Diagnostics"]

    for area in mobile_areas:
        bin_code = f"{warehouse_doc.name}-{area.replace(' ', '-').upper()}"

        if not frappe.db.exists("Warehouse", bin_code):
            bin_doc = frappe.new_doc("Warehouse")
            bin_doc.warehouse_name = f"{warehouse_doc.warehouse_name} - {area}"
            bin_doc.parent_warehouse = warehouse_doc.name
            bin_doc.company = warehouse_doc.company
            bin_doc.warehouse_type = "Stock"
            bin_doc.is_group = 0
            bin_doc.insert()


def setup_warehouse_reorder_settings(warehouse_doc):
    """Configure default reorder settings for warehouse"""
    # Set default reorder method
    if not hasattr(warehouse_doc, 'reorder_method'):
        warehouse_doc.reorder_method = "Manual"

    # Set default lead time
    if not hasattr(warehouse_doc, 'default_lead_time_days'):
        warehouse_doc.default_lead_time_days = 7


def setup_warehouse_permissions(warehouse_doc):
    """Setup role-based permissions for warehouse"""
    try:
        # Define default permissions by role
        permissions = {
            "Workshop Manager": ["read", "write", "create", "delete"],
            "Inventory Manager": ["read", "write", "create", "delete"],
            "Technician": ["read", "write"],
            "Customer Service": ["read"],
        }

        for role, perms in permissions.items():
            if frappe.db.exists("Role", role):
                for perm in perms:
                    # This would typically integrate with ERPNext's permission system
                    pass

    except Exception as e:
        frappe.log_error(f"Warehouse permissions setup error: {str(e)}", "Parts Inventory")


def create_transfer_log(transfer_doc, status, method):
    """Create audit log for stock transfers"""
    try:
        log_doc = frappe.new_doc("Stock Transfer Log")
        log_doc.transfer_document = transfer_doc.name
        log_doc.transfer_type = transfer_doc.purpose
        log_doc.from_warehouse = transfer_doc.from_warehouse
        log_doc.to_warehouse = transfer_doc.to_warehouse
        log_doc.status = status
        log_doc.method = method
        log_doc.total_items = len(transfer_doc.items)
        log_doc.user = frappe.session.user
        log_doc.insert()

    except Exception as e:
        frappe.log_error(f"Transfer log creation error: {str(e)}", "Parts Inventory")


def create_stock_movement_record(transfer_doc, item):
    """Create detailed stock movement tracking"""
    try:
        # This would integrate with ERPNext's Stock Ledger Entry
        movement_data = {
            "item_code": item.item_code,
            "warehouse": transfer_doc.to_warehouse,
            "actual_qty": item.qty,
            "voucher_type": "Stock Entry",
            "voucher_no": transfer_doc.name,
            "posting_date": transfer_doc.posting_date,
            "posting_time": transfer_doc.posting_time,
        }

        # Log movement for tracking
        frappe.logger().info(f"Stock movement: {movement_data}")

    except Exception as e:
        frappe.log_error(f"Stock movement record error: {str(e)}", "Parts Inventory")


def check_reorder_levels(item_code, warehouse):
    """Check and trigger reorder alerts"""
    try:
        # Get current stock level
        current_qty = frappe.db.get_value("Bin",
            {"item_code": item_code, "warehouse": warehouse},
            "actual_qty") or 0

        # Get reorder level
        reorder_level = frappe.db.get_value("Item", item_code, "reorder_level") or 0

        if reorder_level > 0 and current_qty <= reorder_level:
            # Trigger reorder alert
            create_reorder_alert(item_code, warehouse, current_qty, reorder_level)

    except Exception as e:
        frappe.log_error(f"Reorder level check error: {str(e)}", "Parts Inventory")


def create_reorder_alert(item_code, warehouse, current_qty, reorder_level):
    """Create reorder alert notification"""
    try:
        # This would typically create a notification or alert document
        alert_message = f"Item {item_code} in {warehouse} has reached reorder level. Current: {current_qty}, Reorder Level: {reorder_level}"
        frappe.logger().warning(alert_message)

    except Exception as e:
        frappe.log_error(f"Reorder alert creation error: {str(e)}", "Parts Inventory")


def update_parts_location(item_code, from_warehouse, to_warehouse, qty):
    """Update parts location tracking"""
    try:
        # Track parts location for better inventory management
        location_data = {
            "item_code": item_code,
            "from_location": from_warehouse,
            "to_location": to_warehouse,
            "quantity": qty,
            "timestamp": frappe.utils.now()
        }

        # Log location change
        frappe.logger().info(f"Parts location update: {location_data}")

    except Exception as e:
        frappe.log_error(f"Parts location update error: {str(e)}", "Parts Inventory")


def send_transfer_notifications(transfer_doc):
    """Send notifications for completed transfers"""
    try:
        # Get notification recipients
        recipients = frappe.db.get_list("User",
            filters={"role_profile_name": ["in", ["Inventory Manager", "Workshop Manager"]]},
            fields=["email"]
        )

        if recipients:
            # This would typically send email notifications
            notification_message = f"Stock transfer {transfer_doc.name} completed successfully"
            frappe.logger().info(f"Notification: {notification_message}")

    except Exception as e:
        frappe.log_error(f"Transfer notification error: {str(e)}", "Parts Inventory")
