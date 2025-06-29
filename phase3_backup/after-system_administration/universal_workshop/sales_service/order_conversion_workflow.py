"""
Order Conversion Workflow Engine for Universal Workshop ERP
Handles conversion of Service Estimates to Sales Orders, Work Orders, and Purchase Orders
Supports Arabic localization and automated document transitions
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate, add_days
from datetime import datetime
import json
from typing import Dict, List, Optional, Tuple

# pylint: disable=no-member


class OrderConversionWorkflow:
    """
    Manages conversion of Service Estimates to various order types
    """

    def __init__(self, estimate_name: str):
        self.estimate = frappe.get_doc("Service Estimate", estimate_name)
        self.conversion_log = []

    @frappe.whitelist()
    def convert_to_sales_order(
        self, include_parts: bool = True, include_labor: bool = True
    ) -> Dict:
        """
        Convert Service Estimate to Sales Order

        Args:
            include_parts: Include parts in sales order
            include_labor: Include labor charges in sales order

        Returns:
            Dictionary with conversion results
        """
        try:
            # Validate estimate status
            if self.estimate.status not in ["Approved"]:
                frappe.throw(_("Only approved estimates can be converted to Sales Orders"))

            # Check if already converted
            if self.estimate.converted_to_service_order:
                frappe.throw(_("This estimate has already been converted"))

            # Create Sales Order
            sales_order = frappe.new_doc("Sales Order")

            # Map basic fields
            sales_order.customer = self.estimate.customer
            sales_order.delivery_date = add_days(nowdate(), 7)  # Default 7 days
            sales_order.transaction_date = nowdate()
            sales_order.company = frappe.defaults.get_defaults().get("company")

            # Add custom fields for reference
            sales_order.service_estimate_reference = self.estimate.name
            sales_order.workshop_bay = self.estimate.workshop_bay
            sales_order.assigned_technician = self.estimate.assigned_technician

            # Map items from estimate
            if include_labor and self.estimate.estimate_items:
                for item in self.estimate.estimate_items:
                    sales_order.append(
                        "items",
                        {
                            "item_code": item.service_code,
                            "item_name": item.service_name,
                            "item_name_ar": getattr(item, "service_name_ar", ""),
                            "description": item.description,
                            "qty": item.quantity or 1,
                            "rate": item.rate,
                            "amount": item.amount,
                            "delivery_date": add_days(nowdate(), 7),
                        },
                    )

            # Map parts from estimate
            if include_parts and self.estimate.parts_items:
                for part in self.estimate.parts_items:
                    sales_order.append(
                        "items",
                        {
                            "item_code": part.part_code,
                            "item_name": part.part_name,
                            "item_name_ar": getattr(part, "part_name_ar", ""),
                            "description": part.description,
                            "qty": part.qty,
                            "rate": part.rate,
                            "amount": part.amount,
                            "delivery_date": add_days(nowdate(), 3),
                        },
                    )

            # Calculate totals
            sales_order.save()
            sales_order.submit()

            # Update estimate status
            self.estimate.db_set("status", "Converted")
            self.estimate.db_set("converted_to_service_order", 1)
            self.estimate.db_set("service_order_reference", sales_order.name)

            # Log conversion
            self._log_conversion("Sales Order", sales_order.name, "success")

            # Send notification
            self._send_conversion_notification("Sales Order", sales_order.name)

            return {
                "status": "success",
                "sales_order": sales_order.name,
                "message": _("Sales Order {0} created successfully").format(sales_order.name),
                "message_ar": "تم إنشاء أمر البيع {0} بنجاح".format(sales_order.name),
            }

        except Exception as e:
            frappe.log_error(f"Sales Order conversion error: {str(e)}")
            self._log_conversion("Sales Order", None, "failed", str(e))
            return {
                "status": "error",
                "message": _("Failed to create Sales Order: {0}").format(str(e)),
                "message_ar": "فشل في إنشاء أمر البيع: {0}".format(str(e)),
            }

    @frappe.whitelist()
    def convert_to_work_order(self, manufacturing_item: str = None) -> Dict:
        """
        Convert Service Estimate to Work Order for manufacturing/assembly work

        Args:
            manufacturing_item: Item to be manufactured

        Returns:
            Dictionary with conversion results
        """
        try:
            # Validate estimate status
            if self.estimate.status not in ["Approved"]:
                frappe.throw(_("Only approved estimates can be converted to Work Orders"))

            # Create Work Order
            work_order = frappe.new_doc("Work Order")

            # Map basic fields
            work_order.production_item = manufacturing_item or self._get_default_service_item()
            work_order.qty = 1
            work_order.company = frappe.defaults.get_defaults().get("company")
            work_order.planned_start_date = nowdate()
            work_order.planned_end_date = add_days(
                nowdate(), cint(self.estimate.estimated_hours / 8) or 1
            )

            # Add custom fields
            work_order.service_estimate_reference = self.estimate.name
            work_order.workshop_bay = self.estimate.workshop_bay
            work_order.assigned_technician = self.estimate.assigned_technician

            # Map operations from estimate
            if self.estimate.estimate_items:
                for idx, item in enumerate(self.estimate.estimate_items):
                    work_order.append(
                        "operations",
                        {
                            "operation": item.service_name,
                            "operation_ar": getattr(item, "service_name_ar", ""),
                            "workstation": self.estimate.workshop_bay,
                            "time_in_mins": (item.quantity or 1) * 60,  # Convert hours to minutes
                            "description": item.description,
                        },
                    )

            work_order.save()
            work_order.submit()

            # Update estimate
            self.estimate.db_set("status", "Converted")
            self.estimate.db_set("service_order_reference", work_order.name)

            # Log conversion
            self._log_conversion("Work Order", work_order.name, "success")

            return {
                "status": "success",
                "work_order": work_order.name,
                "message": _("Work Order {0} created successfully").format(work_order.name),
                "message_ar": "تم إنشاء أمر العمل {0} بنجاح".format(work_order.name),
            }

        except Exception as e:
            frappe.log_error(f"Work Order conversion error: {str(e)}")
            self._log_conversion("Work Order", None, "failed", str(e))
            return {
                "status": "error",
                "message": _("Failed to create Work Order: {0}").format(str(e)),
                "message_ar": "فشل في إنشاء أمر العمل: {0}".format(str(e)),
            }

    @frappe.whitelist()
    def convert_to_purchase_order(self, supplier: str = None, parts_only: bool = True) -> Dict:
        """
        Convert Service Estimate to Purchase Order for parts procurement

        Args:
            supplier: Supplier for purchase order
            parts_only: Include only parts (exclude labor)

        Returns:
            Dictionary with conversion results
        """
        try:
            # Validate estimate status
            if self.estimate.status not in ["Approved"]:
                frappe.throw(_("Only approved estimates can be converted to Purchase Orders"))

            # Get parts that need procurement
            parts_to_purchase = self._get_parts_for_procurement()

            if not parts_to_purchase:
                return {
                    "status": "warning",
                    "message": _("No parts found that require procurement"),
                    "message_ar": "لم يتم العثور على قطع تحتاج للشراء",
                }

            # Create Purchase Order
            po = frappe.new_doc("Purchase Order")
            po.supplier = supplier or "Default Supplier"
            po.transaction_date = nowdate()
            po.schedule_date = add_days(nowdate(), 7)
            po.company = frappe.defaults.get_defaults().get("company")

            # Add reference
            po.service_estimate_reference = self.estimate.name

            # Add parts
            for part in parts_to_purchase:
                po.append(
                    "items",
                    {
                        "item_code": part["item_code"],
                        "item_name": part["item_name"],
                        "item_name_ar": part.get("item_name_ar", ""),
                        "description": part["description"],
                        "qty": part["qty"],
                        "rate": part["rate"],
                        "amount": part["qty"] * part["rate"],
                        "schedule_date": add_days(nowdate(), 7),
                    },
                )

            po.save()
            po.submit()

            # Update estimate
            self.estimate.db_set("status", "Converted")
            self.estimate.db_set("service_order_reference", po.name)

            # Log conversion
            self._log_conversion("Purchase Order", po.name, "success")

            return {
                "status": "success",
                "purchase_order": po.name,
                "message": _("Purchase Order {0} created successfully").format(po.name),
                "message_ar": "تم إنشاء أمر الشراء {0} بنجاح".format(po.name),
            }

        except Exception as e:
            frappe.log_error(f"Purchase Order conversion error: {str(e)}")
            self._log_conversion("Purchase Order", None, "failed", str(e))
            return {
                "status": "error",
                "message": _("Failed to create Purchase Order: {0}").format(str(e)),
                "message_ar": "فشل في إنشاء أمر الشراء: {0}".format(str(e)),
            }

    @frappe.whitelist()
    def convert_to_multiple_orders(self, conversion_config: Dict) -> Dict:
        """
        Convert Service Estimate to multiple order types simultaneously

        Args:
            conversion_config: Configuration for multiple conversions

        Returns:
            Dictionary with all conversion results
        """
        results = {"conversions": [], "success_count": 0, "error_count": 0}

        try:
            # Sales Order conversion
            if conversion_config.get("create_sales_order"):
                so_result = self.convert_to_sales_order(
                    include_parts=conversion_config.get("so_include_parts", True),
                    include_labor=conversion_config.get("so_include_labor", True),
                )
                results["conversions"].append(("Sales Order", so_result))
                if so_result["status"] == "success":
                    results["success_count"] += 1
                else:
                    results["error_count"] += 1

            # Work Order conversion
            if conversion_config.get("create_work_order"):
                wo_result = self.convert_to_work_order(
                    manufacturing_item=conversion_config.get("manufacturing_item")
                )
                results["conversions"].append(("Work Order", wo_result))
                if wo_result["status"] == "success":
                    results["success_count"] += 1
                else:
                    results["error_count"] += 1

            # Purchase Order conversion
            if conversion_config.get("create_purchase_order"):
                po_result = self.convert_to_purchase_order(
                    supplier=conversion_config.get("supplier"),
                    parts_only=conversion_config.get("po_parts_only", True),
                )
                results["conversions"].append(("Purchase Order", po_result))
                if po_result["status"] == "success":
                    results["success_count"] += 1
                else:
                    results["error_count"] += 1

            return results

        except Exception as e:
            frappe.log_error(f"Multiple conversion error: {str(e)}")
            return {
                "status": "error",
                "message": _("Failed to perform multiple conversions: {0}").format(str(e)),
            }

    def _get_parts_for_procurement(self) -> List[Dict]:
        """Get parts that need to be procured (out of stock or not available)"""
        parts_to_purchase = []

        if not self.estimate.parts_items:
            return parts_to_purchase

        for part in self.estimate.parts_items:
            # Check current stock
            stock_qty = (
                frappe.db.get_value(
                    "Bin",
                    {
                        "item_code": part.part_code,
                        "warehouse": frappe.defaults.get_defaults().get("default_warehouse"),
                    },
                    "actual_qty",
                )
                or 0
            )

            # If insufficient stock, add to purchase list
            if stock_qty < part.qty:
                needed_qty = part.qty - stock_qty
                parts_to_purchase.append(
                    {
                        "item_code": part.part_code,
                        "item_name": part.part_name,
                        "item_name_ar": getattr(part, "part_name_ar", ""),
                        "qty": needed_qty,
                        "rate": part.rate,
                        "description": part.description,
                    }
                )

        return parts_to_purchase

    def _get_default_service_item(self) -> str:
        """Get default service item for work orders"""
        # Try to find a service item based on service type
        service_type = self.estimate.service_type or "General Service"

        # Look for existing service item
        service_item = frappe.db.get_value(
            "Item", {"item_name": ["like", f"%{service_type}%"], "is_stock_item": 0}, "item_code"
        )

        if service_item:
            return service_item

        # Create default service item if not found
        return self._create_service_item(service_type)

    def _create_service_item(self, service_type: str) -> str:
        """Create a service item for work orders"""
        item = frappe.new_doc("Item")
        item.item_code = f"SRV-{service_type.upper().replace(' ', '-')}"
        item.item_name = f"{service_type} Service"
        item.item_name_ar = f"خدمة {service_type}"
        item.item_group = "Services"
        item.is_stock_item = 0
        item.is_sales_item = 1
        item.is_service_item = 1

        item.save()
        return item.item_code

    def _log_conversion(self, order_type: str, order_name: str, status: str, error_msg: str = None):
        """Log conversion attempt"""
        log_entry = {
            "timestamp": frappe.utils.now(),
            "order_type": order_type,
            "order_name": order_name,
            "status": status,
            "error_message": error_msg,
            "user": frappe.session.user,
        }

        self.conversion_log.append(log_entry)

        # Also log to system
        frappe.log_error(
            f"Order Conversion: {status} - {order_type} - {order_name or 'Failed'}",
            "Order Conversion Workflow",
        )

    def _send_conversion_notification(self, order_type: str, order_name: str):
        """Send notification about successful conversion"""
        try:
            # Get customer email
            customer_email = frappe.db.get_value("Customer", self.estimate.customer, "email_id")

            if customer_email:
                # Send email notification
                frappe.sendmail(
                    recipients=[customer_email],
                    subject=_("Service Estimate Converted to {0}").format(order_type),
                    message=_("Your service estimate {0} has been converted to {1} {2}").format(
                        self.estimate.name, order_type, order_name
                    ),
                    delayed=False,
                )

        except Exception as e:
            frappe.log_error(f"Notification error: {str(e)}")

    @frappe.whitelist()
    def get_conversion_options(self) -> Dict:
        """Get available conversion options based on estimate content"""
        options = {
            "can_convert_to_sales_order": True,
            "can_convert_to_work_order": False,
            "can_convert_to_purchase_order": False,
            "has_parts": bool(self.estimate.parts_items),
            "has_labor": bool(self.estimate.estimate_items),
            "available_suppliers": [],
            "parts_requiring_procurement": [],
        }

        # Check work order eligibility
        if self.estimate.service_type in ["Engine Repair", "Transmission", "Body Work"]:
            options["can_convert_to_work_order"] = True

        # Check purchase order eligibility
        parts_to_purchase = self._get_parts_for_procurement()
        if parts_to_purchase:
            options["can_convert_to_purchase_order"] = True
            options["parts_requiring_procurement"] = parts_to_purchase

            # Get available suppliers
            suppliers = set()
            for part in parts_to_purchase:
                part_suppliers = frappe.get_all(
                    "Item Supplier", filters={"parent": part["item_code"]}, fields=["supplier"]
                )
                for supp in part_suppliers:
                    suppliers.add(supp.supplier)

            options["available_suppliers"] = list(suppliers)

        return options


# WhiteListed API Methods
@frappe.whitelist()
def convert_estimate_to_sales_order(estimate_name, include_parts=True, include_labor=True):
    """API method to convert estimate to sales order"""
    converter = OrderConversionWorkflow(estimate_name)
    return converter.convert_to_sales_order(
        include_parts=cint(include_parts), include_labor=cint(include_labor)
    )


@frappe.whitelist()
def convert_estimate_to_work_order(estimate_name, manufacturing_item=None):
    """API method to convert estimate to work order"""
    converter = OrderConversionWorkflow(estimate_name)
    return converter.convert_to_work_order(manufacturing_item=manufacturing_item)


@frappe.whitelist()
def convert_estimate_to_purchase_order(estimate_name, supplier=None, parts_only=True):
    """API method to convert estimate to purchase order"""
    converter = OrderConversionWorkflow(estimate_name)
    return converter.convert_to_purchase_order(supplier=supplier, parts_only=cint(parts_only))


@frappe.whitelist()
def get_conversion_options(estimate_name):
    """API method to get conversion options"""
    converter = OrderConversionWorkflow(estimate_name)
    return converter.get_conversion_options()


@frappe.whitelist()
def convert_to_multiple_orders(estimate_name, conversion_config):
    """API method for multiple conversions"""
    if isinstance(conversion_config, str):
        conversion_config = json.loads(conversion_config)

    converter = OrderConversionWorkflow(estimate_name)
    return converter.convert_to_multiple_orders(conversion_config)
