"""
V2 Workshop Management API - Universal Workshop ERP
Provides workshop operations and service order management for Frontend V2
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, add_days, nowdate, flt
import json
from typing import Dict, Any, Optional, List


@frappe.whitelist(allow_guest=False)
def get_service_orders(filters: Optional[Dict[str, Any]] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """
    Get service orders with filtering and pagination
    """
    try:
        # Default filters
        default_filters = {}
        if filters:
            default_filters.update(filters)
        
        # Get service orders
        service_orders = frappe.get_all(
            "Service Order",
            filters=default_filters,
            fields=[
                "name", "customer", "customer_name", "vehicle", "vehicle_license_plate",
                "service_date", "estimated_completion", "status", "priority",
                "assigned_technician", "service_advisor", "total_amount",
                "creation", "modified", "owner"
            ],
            order_by="creation desc",
            limit=limit,
            start=offset
        )
        
        # Get total count
        total_count = frappe.db.count("Service Order", default_filters)
        
        # Enrich data with additional information
        enriched_orders = []
        for order in service_orders:
            enriched_order = order.copy()
            
            # Get service items summary
            service_items = frappe.get_all(
                "Service Order Item",
                filters={"parent": order.name},
                fields=["item_code", "item_name", "qty", "rate", "amount"]
            )
            enriched_order["service_items"] = service_items
            enriched_order["items_count"] = len(service_items)
            
            # Get status info
            enriched_order["status_info"] = get_service_order_status_info(order.status)
            
            # Calculate progress
            enriched_order["progress"] = calculate_service_order_progress(order.name)
            
            enriched_orders.append(enriched_order)
        
        return {
            "service_orders": enriched_orders,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        frappe.logger().error(f"Error getting service orders: {str(e)}")
        return {"service_orders": [], "total_count": 0, "error": str(e)}


@frappe.whitelist(allow_guest=False)
def get_service_order(name: str) -> Dict[str, Any]:
    """
    Get detailed service order information
    """
    try:
        # Check permissions
        if not frappe.has_permission("Service Order", "read", doc=name):
            frappe.throw(_("Not permitted to read Service Order"))
        
        # Get service order
        service_order = frappe.get_doc("Service Order", name)
        
        # Get related data
        service_data = {
            "service_order": service_order.as_dict(),
            "customer_info": get_customer_info(service_order.customer),
            "vehicle_info": get_vehicle_info(service_order.vehicle),
            "technician_info": get_technician_info(service_order.assigned_technician),
            "service_history": get_vehicle_service_history(service_order.vehicle, exclude=name),
            "status_timeline": get_service_order_timeline(name),
            "attachments": get_service_order_attachments(name),
            "notes": get_service_order_notes(name)
        }
        
        return service_data
        
    except Exception as e:
        frappe.logger().error(f"Error getting service order {name}: {str(e)}")
        frappe.throw(_("Failed to load service order details"))


@frappe.whitelist(allow_guest=False)
def create_service_order(service_order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new service order
    """
    try:
        # Check permissions
        if not frappe.has_permission("Service Order", "create"):
            frappe.throw(_("Not permitted to create Service Order"))
        
        # Create service order
        service_order = frappe.new_doc("Service Order")
        
        # Set basic fields
        required_fields = ["customer", "vehicle", "service_date"]
        for field in required_fields:
            if field not in service_order_data:
                frappe.throw(_(f"Missing required field: {field}"))
            service_order.set(field, service_order_data[field])
        
        # Set optional fields
        optional_fields = [
            "service_advisor", "assigned_technician", "priority", 
            "estimated_completion", "description", "customer_complaint"
        ]
        for field in optional_fields:
            if field in service_order_data:
                service_order.set(field, service_order_data[field])
        
        # Add service items
        if "service_items" in service_order_data:
            for item_data in service_order_data["service_items"]:
                service_order.append("items", item_data)
        
        # Save and submit if required
        service_order.insert()
        
        if service_order_data.get("submit", False):
            service_order.submit()
        
        return {
            "success": True,
            "service_order": service_order.name,
            "message": _("Service order created successfully")
        }
        
    except Exception as e:
        frappe.logger().error(f"Error creating service order: {str(e)}")
        frappe.throw(_("Failed to create service order"))


@frappe.whitelist(allow_guest=False)
def update_service_order(name: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update existing service order
    """
    try:
        # Check permissions
        if not frappe.has_permission("Service Order", "write", doc=name):
            frappe.throw(_("Not permitted to update Service Order"))
        
        service_order = frappe.get_doc("Service Order", name)
        
        # Update allowed fields
        allowed_fields = [
            "status", "assigned_technician", "service_advisor", "priority",
            "estimated_completion", "description", "customer_complaint"
        ]
        
        updated_fields = []
        for field in allowed_fields:
            if field in update_data:
                old_value = service_order.get(field)
                new_value = update_data[field]
                if old_value != new_value:
                    service_order.set(field, new_value)
                    updated_fields.append(field)
        
        if updated_fields:
            service_order.save()
            
            # Log the update
            add_service_order_note(
                name, 
                f"Updated fields: {', '.join(updated_fields)}", 
                "System Update"
            )
        
        return {
            "success": True,
            "updated_fields": updated_fields,
            "message": _("Service order updated successfully")
        }
        
    except Exception as e:
        frappe.logger().error(f"Error updating service order {name}: {str(e)}")
        frappe.throw(_("Failed to update service order"))


@frappe.whitelist(allow_guest=False)
def get_workshop_dashboard() -> Dict[str, Any]:
    """
    Get workshop dashboard data for Frontend V2
    """
    try:
        today = nowdate()
        
        # Get key metrics
        dashboard_data = {
            "today_metrics": {
                "service_orders_today": frappe.db.count("Service Order", {"service_date": today}),
                "completed_today": frappe.db.count("Service Order", {"service_date": today, "status": "Completed"}),
                "in_progress": frappe.db.count("Service Order", {"status": "In Progress"}),
                "pending": frappe.db.count("Service Order", {"status": "Pending"})
            },
            "technician_status": get_technician_status(),
            "service_bay_status": get_service_bay_status(),
            "upcoming_appointments": get_upcoming_appointments(),
            "overdue_orders": get_overdue_service_orders(),
            "revenue_today": get_today_revenue(),
            "recent_activities": get_recent_workshop_activities(),
            "alerts": get_workshop_alerts()
        }
        
        return dashboard_data
        
    except Exception as e:
        frappe.logger().error(f"Error getting workshop dashboard: {str(e)}")
        return {"error": str(e)}


@frappe.whitelist(allow_guest=False)
def get_technicians() -> Dict[str, Any]:
    """
    Get list of technicians with their current status
    """
    try:
        technicians = frappe.get_all(
            "Employee",
            filters={"department": "Workshop", "status": "Active"},
            fields=["name", "employee_name", "designation", "phone", "email"]
        )
        
        # Enrich with current assignments
        for technician in technicians:
            current_assignments = frappe.get_all(
                "Service Order",
                filters={"assigned_technician": technician.name, "status": ["in", ["In Progress", "Pending"]]},
                fields=["name", "customer_name", "vehicle_license_plate", "status", "priority"]
            )
            technician["current_assignments"] = current_assignments
            technician["workload"] = len(current_assignments)
            technician["availability"] = "Available" if len(current_assignments) == 0 else "Busy"
        
        return {"technicians": technicians}
        
    except Exception as e:
        frappe.logger().error(f"Error getting technicians: {str(e)}")
        return {"technicians": [], "error": str(e)}


@frappe.whitelist(allow_guest=False)
def assign_technician(service_order: str, technician: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Assign technician to service order
    """
    try:
        # Update service order
        frappe.db.set_value("Service Order", service_order, "assigned_technician", technician)
        
        # Add note
        note_text = f"Technician assigned: {technician}"
        if notes:
            note_text += f"\nNotes: {notes}"
        
        add_service_order_note(service_order, note_text, "Technician Assignment")
        
        return {
            "success": True,
            "message": _("Technician assigned successfully")
        }
        
    except Exception as e:
        frappe.logger().error(f"Error assigning technician: {str(e)}")
        frappe.throw(_("Failed to assign technician"))


# Helper functions

def get_service_order_status_info(status: str) -> Dict[str, Any]:
    """Get status information including colors and next actions"""
    status_map = {
        "Draft": {"color": "gray", "progress": 0, "next_action": "Confirm Order"},
        "Pending": {"color": "orange", "progress": 25, "next_action": "Start Work"},
        "In Progress": {"color": "blue", "progress": 50, "next_action": "Complete Work"},
        "Quality Check": {"color": "purple", "progress": 75, "next_action": "Approve Quality"},
        "Completed": {"color": "green", "progress": 100, "next_action": "None"},
        "Cancelled": {"color": "red", "progress": 0, "next_action": "None"}
    }
    return status_map.get(status, {"color": "gray", "progress": 0, "next_action": "Unknown"})


def calculate_service_order_progress(service_order: str) -> int:
    """Calculate service order completion progress"""
    try:
        order = frappe.get_doc("Service Order", service_order)
        status_progress = get_service_order_status_info(order.status)["progress"]
        return status_progress
    except:
        return 0


def get_customer_info(customer: str) -> Dict[str, Any]:
    """Get customer information"""
    try:
        if not customer:
            return {}
        
        customer_doc = frappe.get_doc("Customer", customer)
        return {
            "name": customer_doc.name,
            "customer_name": customer_doc.customer_name,
            "phone": customer_doc.mobile_no or customer_doc.phone,
            "email": customer_doc.email_id,
            "customer_group": customer_doc.customer_group,
            "territory": customer_doc.territory
        }
    except:
        return {}


def get_vehicle_info(vehicle: str) -> Dict[str, Any]:
    """Get vehicle information"""
    try:
        if not vehicle:
            return {}
        
        vehicle_doc = frappe.get_doc("Vehicle", vehicle)
        return {
            "name": vehicle_doc.name,
            "license_plate": vehicle_doc.license_plate,
            "make": vehicle_doc.make,
            "model": vehicle_doc.model,
            "year": vehicle_doc.year,
            "vin": vehicle_doc.vin,
            "color": vehicle_doc.color,
            "odometer": vehicle_doc.last_odometer_reading
        }
    except:
        return {}


def get_technician_info(technician: str) -> Dict[str, Any]:
    """Get technician information"""
    try:
        if not technician:
            return {}
        
        tech_doc = frappe.get_doc("Employee", technician)
        return {
            "name": tech_doc.name,
            "employee_name": tech_doc.employee_name,
            "designation": tech_doc.designation,
            "phone": tech_doc.cell_number or tech_doc.personal_phone,
            "email": tech_doc.personal_email
        }
    except:
        return {}


def get_vehicle_service_history(vehicle: str, exclude: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Get vehicle service history"""
    try:
        filters = {"vehicle": vehicle}
        if exclude:
            filters["name"] = ["!=", exclude]
        
        history = frappe.get_all(
            "Service Order",
            filters=filters,
            fields=["name", "service_date", "status", "total_amount", "description"],
            order_by="service_date desc",
            limit=limit
        )
        return history
    except:
        return []


def get_service_order_timeline(service_order: str) -> List[Dict[str, Any]]:
    """Get service order status timeline"""
    try:
        timeline = frappe.get_all(
            "Version",
            filters={"docname": service_order, "ref_doctype": "Service Order"},
            fields=["creation", "data"],
            order_by="creation asc"
        )
        return timeline
    except:
        return []


def get_service_order_attachments(service_order: str) -> List[Dict[str, Any]]:
    """Get service order attachments"""
    try:
        attachments = frappe.get_all(
            "File",
            filters={"attached_to_doctype": "Service Order", "attached_to_name": service_order},
            fields=["name", "file_name", "file_url", "file_size", "creation"]
        )
        return attachments
    except:
        return []


def get_service_order_notes(service_order: str) -> List[Dict[str, Any]]:
    """Get service order notes/comments"""
    try:
        notes = frappe.get_all(
            "Comment",
            filters={"reference_doctype": "Service Order", "reference_name": service_order},
            fields=["name", "content", "creation", "owner"],
            order_by="creation desc"
        )
        return notes
    except:
        return []


def add_service_order_note(service_order: str, note: str, note_type: str = "General") -> None:
    """Add note to service order"""
    try:
        comment = frappe.new_doc("Comment")
        comment.comment_type = "Comment"
        comment.reference_doctype = "Service Order"
        comment.reference_name = service_order
        comment.content = f"[{note_type}] {note}"
        comment.insert(ignore_permissions=True)
    except Exception as e:
        frappe.logger().error(f"Error adding service order note: {str(e)}")


def get_technician_status() -> List[Dict[str, Any]]:
    """Get current technician status"""
    try:
        technicians = frappe.get_all(
            "Employee",
            filters={"department": "Workshop", "status": "Active"},
            fields=["name", "employee_name"]
        )
        
        for tech in technicians:
            active_orders = frappe.db.count(
                "Service Order",
                {"assigned_technician": tech.name, "status": ["in", ["In Progress", "Pending"]]}
            )
            tech["active_orders"] = active_orders
            tech["status"] = "Available" if active_orders == 0 else "Busy"
        
        return technicians
    except:
        return []


def get_service_bay_status() -> List[Dict[str, Any]]:
    """Get service bay status"""
    try:
        # This would integrate with Service Bay DocType if it exists
        bays = []
        for i in range(1, 6):  # Assume 5 bays
            bay = {
                "name": f"Bay {i}",
                "status": "Available",  # Would get from actual data
                "current_vehicle": None,
                "technician": None
            }
            bays.append(bay)
        return bays
    except:
        return []


def get_upcoming_appointments() -> List[Dict[str, Any]]:
    """Get upcoming appointments"""
    try:
        tomorrow = add_days(nowdate(), 1)
        appointments = frappe.get_all(
            "Service Order",
            filters={"service_date": ["between", [nowdate(), tomorrow]], "status": "Pending"},
            fields=["name", "customer_name", "vehicle_license_plate", "service_date"],
            order_by="service_date asc",
            limit=10
        )
        return appointments
    except:
        return []


def get_overdue_service_orders() -> List[Dict[str, Any]]:
    """Get overdue service orders"""
    try:
        overdue = frappe.get_all(
            "Service Order",
            filters={
                "estimated_completion": ["<", nowdate()],
                "status": ["in", ["In Progress", "Pending"]]
            },
            fields=["name", "customer_name", "vehicle_license_plate", "estimated_completion"],
            order_by="estimated_completion asc",
            limit=10
        )
        return overdue
    except:
        return []


def get_today_revenue() -> float:
    """Get today's revenue"""
    try:
        revenue = frappe.db.sql("""
            SELECT SUM(total_amount)
            FROM `tabService Order`
            WHERE service_date = %s AND status = 'Completed'
        """, [nowdate()])[0][0]
        return flt(revenue) or 0.0
    except:
        return 0.0


def get_recent_workshop_activities() -> List[Dict[str, Any]]:
    """Get recent workshop activities"""
    try:
        activities = frappe.get_all(
            "Activity Log",
            filters={"reference_doctype": ["in", ["Service Order", "Customer", "Vehicle"]]},
            fields=["subject", "reference_doctype", "reference_name", "creation", "user"],
            order_by="creation desc",
            limit=10
        )
        return activities
    except:
        return []


def get_workshop_alerts() -> List[Dict[str, Any]]:
    """Get workshop alerts and notifications"""
    try:
        alerts = []
        
        # Check for overdue orders
        overdue_count = frappe.db.count(
            "Service Order",
            {
                "estimated_completion": ["<", nowdate()],
                "status": ["in", ["In Progress", "Pending"]]
            }
        )
        if overdue_count > 0:
            alerts.append({
                "type": "warning",
                "message": f"{overdue_count} service orders are overdue",
                "action": "view_overdue_orders"
            })
        
        # Check for low inventory (if Item DocType exists)
        try:
            low_stock = frappe.db.count("Item", {"actual_qty": ["<", "min_order_qty"]})
            if low_stock > 0:
                alerts.append({
                    "type": "info",
                    "message": f"{low_stock} items are low in stock",
                    "action": "view_inventory"
                })
        except:
            pass
        
        return alerts
    except:
        return []