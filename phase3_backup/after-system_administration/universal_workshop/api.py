import frappe
from frappe import _


@frappe.whitelist()
def get_service_order_items(service_order):
    """
    Get items from a service order for invoice generation

    Args:
        service_order (str): Service Order ID

    Returns:
        list: List of items with quantities and rates
    """
    if not service_order:
        frappe.throw(_("Service Order is required"))

    # Check if service order exists
    if not frappe.db.exists("Service Order", service_order):
        frappe.throw(_("Service Order {0} not found").format(service_order))

    # Get service order document
    service_order_doc = frappe.get_doc("Service Order", service_order)

    items = []

    # Add labor items from services
    if hasattr(service_order_doc, "services") and service_order_doc.services:
        for service in service_order_doc.services:
            items.append(
                {
                    "item_code": service.get("service_item_code")
                    or f'SERVICE-{service.get("service_type", "GENERAL")}',
                    "item_name": service.get("service_name") or service.get("service_type"),
                    "item_name_ar": service.get("service_name_ar"),
                    "qty": 1,
                    "rate": service.get("service_charge") or 0,
                    "amount": service.get("service_charge") or 0,
                    "description": f"{_('Service')}: {service.get('service_name') or service.get('service_type')}",
                }
            )

    # Add parts from service order
    if hasattr(service_order_doc, "parts") and service_order_doc.parts:
        for part in service_order_doc.parts:
            items.append(
                {
                    "item_code": part.get("item_code"),
                    "item_name": part.get("item_name"),
                    "item_name_ar": part.get("item_name_ar"),
                    "qty": part.get("qty") or 1,
                    "rate": part.get("rate") or 0,
                    "amount": (part.get("qty") or 1) * (part.get("rate") or 0),
                    "description": f"{_('Part')}: {part.get('item_name')}",
                }
            )

    # If no items found, return default service item
    if not items:
        items.append(
            {
                "item_code": "SERVICE-GENERAL",
                "item_name": "General Service",
                "item_name_ar": "خدمة عامة",
                "qty": 1,
                "rate": service_order_doc.get("total_amount") or 0,
                "amount": service_order_doc.get("total_amount") or 0,
                "description": f"{_('Service Order')}: {service_order}",
            }
        )

    return items


@frappe.whitelist()
def get_customer_vehicles(customer):
    """
    Get vehicles registered to a customer

    Args:
        customer (str): Customer ID

    Returns:
        list: List of vehicles
    """
    if not customer:
        return []

    vehicles = frappe.get_list(
        "Vehicle",
        filters={"owner": customer},
        fields=["name", "license_plate", "make", "model", "year", "vin_number"],
        order_by="creation desc",
    )

    return vehicles


@frappe.whitelist()
def get_workshop_technicians():
    """
    Get list of available technicians

    Returns:
        list: List of technicians
    """
    technicians = frappe.get_list(
        "Technician",
        filters={"employment_status": "Active"},
        fields=["name", "technician_name", "technician_name_ar", "department", "skill_level"],
        order_by="technician_name",
    )

    return technicians


@frappe.whitelist()
def get_service_types():
    """
    Get available service types

    Returns:
        list: List of service types
    """
    service_types = frappe.get_list(
        "Service Type",
        filters={"is_active": 1},
        fields=["name", "service_name", "service_name_ar", "standard_rate", "estimated_time"],
        order_by="service_name",
    )

    return service_types


@frappe.whitelist()
def get_payment_methods():
    """
    Get available payment methods

    Returns:
        list: List of payment methods
    """
    payment_methods = frappe.get_list(
        "Mode of Payment",
        filters={"enabled": 1},
        fields=["name", "mode_of_payment", "type"],
        order_by="mode_of_payment",
    )

    return payment_methods
