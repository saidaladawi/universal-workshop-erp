"""
Universal Workshop ERP - Service Order Kanban Board Backend
Real-time service order management with drag-and-drop functionality and Arabic localization
"""

import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, flt, cint, format_datetime
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class ServiceOrderKanbanManager:
    """Service Order Kanban board management system"""

    def __init__(self):
        self.language = frappe.local.lang or "en"
        self.user = frappe.session.user
        self.user_roles = frappe.get_roles()
        self.workshop_profile = self._get_user_workshop()

    def _get_user_workshop(self) -> Optional[str]:
        """Get workshop profile for current user"""
        try:
            # Get user's assigned workshop (if any)
            workshop = frappe.db.get_value("User", self.user, "workshop_profile")
            return workshop
        except Exception:
            return None

    def get_kanban_data(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get complete Kanban board data with status columns"""

        # Default filters
        if not filters:
            filters = {}

        # Apply workshop filter if user has assigned workshop
        if self.workshop_profile:
            filters["workshop_profile"] = self.workshop_profile

        # Get service orders for each status
        kanban_data = {
            "columns": self._get_status_columns(),
            "cards": {},
            "summary": {},
            "filters": filters,
            "last_updated": get_datetime(),
            "auto_refresh": True,
            "refresh_interval": 30000,  # 30 seconds
        }

        # Define status groups for Kanban columns
        status_mapping = {
            "pending": ["Draft", "Scheduled"],
            "in_progress": ["In Progress"],
            "quality_check": ["Quality Check"],
            "completed": ["Completed"],
            "delivered": ["Delivered"],
        }

        # Fetch cards for each column
        for column_id, statuses in status_mapping.items():
            cards = self._get_service_order_cards(statuses, filters)
            kanban_data["cards"][column_id] = cards
            kanban_data["summary"][column_id] = {
                "count": len(cards),
                "total_value": sum(flt(card.get("final_amount", 0)) for card in cards),
                "urgent_count": len([c for c in cards if c.get("priority") == "Urgent"]),
                "overdue_count": len([c for c in cards if c.get("is_overdue", False)]),
            }

        return kanban_data

    def _get_status_columns(self) -> List[Dict[str, Any]]:
        """Define Kanban status columns with Arabic support"""
        columns = [
            {
                "id": "pending",
                "title": _("Pending") if self.language == "en" else "في الانتظار",
                "status_list": ["Draft", "Scheduled"],
                "color": "#6c757d",
                "icon": "fa-clock",
                "allow_add": True,
                "max_cards": None,
            },
            {
                "id": "in_progress",
                "title": _("In Progress") if self.language == "en" else "قيد التنفيذ",
                "status_list": ["In Progress"],
                "color": "#fd7e14",
                "icon": "fa-tools",
                "allow_add": False,
                "max_cards": 10,  # Workshop capacity limit
            },
            {
                "id": "quality_check",
                "title": _("Quality Check") if self.language == "en" else "فحص الجودة",
                "status_list": ["Quality Check"],
                "color": "#6f42c1",
                "icon": "fa-search",
                "allow_add": False,
                "max_cards": 5,
            },
            {
                "id": "completed",
                "title": _("Completed") if self.language == "en" else "مكتمل",
                "status_list": ["Completed"],
                "color": "#198754",
                "icon": "fa-check-circle",
                "allow_add": False,
                "max_cards": None,
            },
            {
                "id": "delivered",
                "title": _("Delivered") if self.language == "en" else "مُسلّم",
                "status_list": ["Delivered"],
                "color": "#20c997",
                "icon": "fa-shipping-fast",
                "allow_add": False,
                "max_cards": None,
            },
        ]
        return columns

    def _get_service_order_cards(
        self, statuses: List[str], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get service order cards for specific statuses"""

        # Build SQL filters
        conditions = ["so.docstatus = 1"]  # Only submitted orders
        values = []

        if statuses:
            placeholders = ",".join(["%s"] * len(statuses))
            conditions.append(f"so.status IN ({placeholders})")
            values.extend(statuses)

        # Apply additional filters
        for field, value in filters.items():
            if field == "date_range" and value:
                conditions.append("so.service_date BETWEEN %s AND %s")
                values.extend([value[0], value[1]])
            elif field == "priority" and value:
                conditions.append("so.priority = %s")
                values.append(value)
            elif field == "technician" and value:
                conditions.append("so.technician_assigned = %s")
                values.append(value)
            elif field == "customer" and value:
                conditions.append("so.customer = %s")
                values.append(value)

        where_clause = " AND ".join(conditions)

        # Main query with Arabic support
        query = f"""
            SELECT 
                so.name,
                so.customer,
                so.customer_name,
                so.customer_name_ar,
                so.vehicle,
                so.make,
                so.model,
                so.year,
                so.license_plate,
                so.service_date,
                so.estimated_completion_date,
                so.priority,
                so.status,
                so.service_type,
                so.service_type_ar,
                so.technician_assigned,
                so.final_amount,
                so.created_on,
                so.started_on,
                so.completed_on,
                so.description,
                so.description_ar,
                so.current_mileage,
                tech.full_name as technician_name,
                cust.phone as customer_phone
            FROM 
                `tabService Order` so
            LEFT JOIN 
                `tabUser` tech ON so.technician_assigned = tech.name
            LEFT JOIN 
                `tabCustomer` cust ON so.customer = cust.name
            WHERE 
                {where_clause}
            ORDER BY 
                CASE so.priority 
                    WHEN 'Urgent' THEN 1 
                    WHEN 'High' THEN 2 
                    WHEN 'Medium' THEN 3 
                    ELSE 4 
                END,
                so.service_date ASC,
                so.creation DESC
        """

        service_orders = frappe.db.sql(query, values, as_dict=True)

        # Transform to card format with Arabic support
        cards = []
        for order in service_orders:
            card = self._format_service_order_card(order)
            cards.append(card)

        return cards

    def _format_service_order_card(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Format service order data as Kanban card with Arabic localization"""

        # Calculate elapsed time and overdue status
        now = get_datetime()
        is_overdue = False
        elapsed_hours = 0

        if order.get("estimated_completion_date"):
            completion_date = get_datetime(order["estimated_completion_date"])
            if now > completion_date and order["status"] not in ["Completed", "Delivered"]:
                is_overdue = True

        if order.get("started_on"):
            start_time = get_datetime(order["started_on"])
            elapsed_hours = (now - start_time).total_seconds() / 3600

        # Determine display names based on language
        customer_name = (
            order.get("customer_name_ar")
            if self.language == "ar" and order.get("customer_name_ar")
            else order.get("customer_name")
        )
        service_type = (
            order.get("service_type_ar")
            if self.language == "ar" and order.get("service_type_ar")
            else order.get("service_type")
        )
        description = (
            order.get("description_ar")
            if self.language == "ar" and order.get("description_ar")
            else order.get("description")
        )

        # Priority display with Arabic
        priority_labels = {
            "en": {"Urgent": "Urgent", "High": "High", "Medium": "Medium", "Low": "Low"},
            "ar": {"Urgent": "عاجل", "High": "عالي", "Medium": "متوسط", "Low": "منخفض"},
        }
        priority_label = priority_labels.get(self.language, priority_labels["en"]).get(
            order.get("priority"), order.get("priority")
        )

        card = {
            "id": order["name"],
            "title": f"{order['name']} - {customer_name}",
            "customer": {
                "id": order["customer"],
                "name": customer_name,
                "phone": order.get("customer_phone", ""),
            },
            "vehicle": {
                "display": f"{order.get('make', '')} {order.get('model', '')} {order.get('year', '')}".strip(),
                "license_plate": order.get("license_plate", ""),
                "mileage": order.get("current_mileage", 0),
            },
            "service": {
                "type": service_type,
                "date": order.get("service_date"),
                "description": description or "",
                "estimated_completion": order.get("estimated_completion_date"),
            },
            "status": {
                "current": order["status"],
                "priority": order.get("priority", "Medium"),
                "priority_label": priority_label,
                "is_overdue": is_overdue,
                "elapsed_hours": round(elapsed_hours, 1),
            },
            "technician": {
                "id": order.get("technician_assigned"),
                "name": order.get("technician_name", ""),
            },
            "financial": {
                "amount": flt(order.get("final_amount", 0)),
                "currency": "OMR",
                "formatted": f"OMR {flt(order.get('final_amount', 0)):.3f}",
            },
            "timestamps": {
                "created": order.get("created_on"),
                "started": order.get("started_on"),
                "completed": order.get("completed_on"),
                "last_updated": get_datetime(),
            },
            "actions": self._get_card_actions(order),
            "styling": self._get_card_styling(order),
        }

        return card

    def _get_card_actions(self, order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available actions for service order card"""
        actions = []
        status = order["status"]

        if status == "Scheduled":
            actions.append(
                {
                    "id": "start_service",
                    "label": _("Start Service") if self.language == "en" else "بدء الخدمة",
                    "icon": "fa-play",
                    "color": "primary",
                    "requires_confirmation": True,
                }
            )

        if status == "In Progress":
            actions.extend(
                [
                    {
                        "id": "quality_check",
                        "label": _("Quality Check") if self.language == "en" else "فحص الجودة",
                        "icon": "fa-search",
                        "color": "warning",
                        "requires_confirmation": False,
                    },
                    {
                        "id": "complete_service",
                        "label": _("Complete") if self.language == "en" else "إكمال",
                        "icon": "fa-check",
                        "color": "success",
                        "requires_confirmation": True,
                    },
                ]
            )

        if status == "Quality Check":
            actions.extend(
                [
                    {
                        "id": "approve_complete",
                        "label": (
                            _("Approve & Complete") if self.language == "en" else "موافقة وإكمال"
                        ),
                        "icon": "fa-check-double",
                        "color": "success",
                        "requires_confirmation": True,
                    },
                    {
                        "id": "return_progress",
                        "label": (
                            _("Return to Progress") if self.language == "en" else "العودة للتنفيذ"
                        ),
                        "icon": "fa-undo",
                        "color": "secondary",
                        "requires_confirmation": True,
                    },
                ]
            )

        if status == "Completed":
            actions.append(
                {
                    "id": "deliver_vehicle",
                    "label": _("Deliver Vehicle") if self.language == "en" else "تسليم المركبة",
                    "icon": "fa-shipping-fast",
                    "color": "info",
                    "requires_confirmation": True,
                }
            )

        # Always available actions
        actions.extend(
            [
                {
                    "id": "view_details",
                    "label": _("View Details") if self.language == "en" else "عرض التفاصيل",
                    "icon": "fa-eye",
                    "color": "info",
                    "requires_confirmation": False,
                },
                {
                    "id": "send_update",
                    "label": _("Send Update") if self.language == "en" else "إرسال تحديث",
                    "icon": "fa-sms",
                    "color": "primary",
                    "requires_confirmation": False,
                },
            ]
        )

        return actions

    def _get_card_styling(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Get card styling based on status and priority"""
        priority_colors = {
            "Urgent": "#dc3545",
            "High": "#fd7e14",
            "Medium": "#198754",
            "Low": "#6c757d",
        }

        status_colors = {
            "Draft": "#6c757d",
            "Scheduled": "#0dcaf0",
            "In Progress": "#fd7e14",
            "Quality Check": "#6f42c1",
            "Completed": "#198754",
            "Delivered": "#20c997",
            "Cancelled": "#dc3545",
        }

        return {
            "priority_color": priority_colors.get(order.get("priority"), "#6c757d"),
            "status_color": status_colors.get(order["status"], "#6c757d"),
            "border_left": f"4px solid {priority_colors.get(order.get('priority'), '#6c757d')}",
            "text_direction": "rtl" if self.language == "ar" else "ltr",
        }

    def update_card_status(self, card_id: str, new_status: str, column_id: str) -> Dict[str, Any]:
        """Update service order status via drag-and-drop"""
        try:
            # Validate the move
            if not self._validate_status_transition(card_id, new_status):
                return {
                    "success": False,
                    "message": _("Invalid status transition"),
                    "card_id": card_id,
                }

            # Get service order
            service_order = frappe.get_doc("Service Order", card_id)

            # Check permissions
            if not service_order.has_permission("write"):
                return {
                    "success": False,
                    "message": _("Insufficient permissions"),
                    "card_id": card_id,
                }

            # Update status and timestamps
            old_status = service_order.status
            service_order.status = new_status

            # Set appropriate timestamp fields
            timestamp_field = self._get_timestamp_field(new_status)
            if timestamp_field:
                setattr(service_order, timestamp_field, get_datetime())

            # Add status history entry
            service_order.append(
                "status_history",
                {
                    "status": new_status,
                    "changed_by": frappe.session.user,
                    "changed_on": get_datetime(),
                    "notes": f"Status changed from {old_status} to {new_status} via Kanban board",
                },
            )

            # Save the document
            service_order.save()
            frappe.db.commit()

            # Send notification if configured
            self._send_status_notification(service_order, old_status, new_status)

            return {
                "success": True,
                "message": _("Status updated successfully"),
                "card_id": card_id,
                "new_status": new_status,
                "old_status": old_status,
                "updated_card": self._format_service_order_card(service_order.as_dict()),
            }

        except Exception as e:
            frappe.log_error(f"Kanban status update failed: {str(e)}", "Service Order Kanban")
            return {
                "success": False,
                "message": _("Status update failed: {0}").format(str(e)),
                "card_id": card_id,
            }

    def _validate_status_transition(self, card_id: str, new_status: str) -> bool:
        """Validate if status transition is allowed"""
        try:
            current_status = frappe.db.get_value("Service Order", card_id, "status")

            # Define allowed transitions
            allowed_transitions = {
                "Draft": ["Scheduled", "Cancelled"],
                "Scheduled": ["In Progress", "Cancelled"],
                "In Progress": ["Quality Check", "Completed", "Cancelled"],
                "Quality Check": ["Completed", "In Progress", "Cancelled"],
                "Completed": ["Delivered"],
                "Delivered": [],  # Final status
                "Cancelled": [],  # Final status
            }

            return new_status in allowed_transitions.get(current_status, [])

        except Exception:
            return False

    def _get_timestamp_field(self, status: str) -> Optional[str]:
        """Get the timestamp field for status"""
        timestamp_mapping = {
            "Scheduled": "scheduled_on",
            "In Progress": "started_on",
            "Quality Check": "quality_check_on",
            "Completed": "completed_on",
            "Delivered": "delivered_on",
        }
        return timestamp_mapping.get(status)

    def _send_status_notification(self, service_order, old_status: str, new_status: str):
        """Send notification for status change"""
        try:
            # This would integrate with the communication management system
            # For now, just log the change
            frappe.logger().info(
                f"Service Order {service_order.name} status changed: {old_status} → {new_status}"
            )
        except Exception as e:
            frappe.log_error(f"Notification sending failed: {str(e)}", "Kanban Notification")


# WhiteListed API methods for frontend integration
@frappe.whitelist()
def get_kanban_board_data(filters=None):
    """Get Kanban board data for Service Orders"""
    try:
        if filters and isinstance(filters, str):
            filters = json.loads(filters)

        manager = ServiceOrderKanbanManager()
        return manager.get_kanban_data(filters or {})

    except Exception as e:
        frappe.log_error(f"Kanban data fetch failed: {str(e)}", "Service Order Kanban")
        return {"success": False, "message": _("Failed to load Kanban data: {0}").format(str(e))}


@frappe.whitelist()
def update_service_order_status(card_id, new_status, column_id):
    """Update service order status via drag-and-drop"""
    try:
        manager = ServiceOrderKanbanManager()
        return manager.update_card_status(card_id, new_status, column_id)

    except Exception as e:
        frappe.log_error(f"Kanban status update failed: {str(e)}", "Service Order Kanban")
        return {
            "success": False,
            "message": _("Status update failed: {0}").format(str(e)),
            "card_id": card_id,
        }


@frappe.whitelist()
def get_service_order_filters():
    """Get available filter options for Kanban board"""
    try:
        return {
            "priorities": [
                {"value": "Urgent", "label": _("Urgent")},
                {"value": "High", "label": _("High")},
                {"value": "Medium", "label": _("Medium")},
                {"value": "Low", "label": _("Low")},
            ],
            "technicians": frappe.get_list(
                "User",
                filters={"role_profile_name": ["like", "%Technician%"], "enabled": 1},
                fields=["name", "full_name"],
            ),
            "customers": frappe.get_list(
                "Customer",
                filters={"disabled": 0},
                fields=["name", "customer_name", "customer_name_ar"],
                limit=100,
            ),
        }

    except Exception as e:
        frappe.log_error(f"Filter options fetch failed: {str(e)}", "Service Order Kanban")
        return {"success": False, "message": str(e)}


@frappe.whitelist()
def execute_card_action(card_id, action_id, **kwargs):
    """Execute action on service order card"""
    try:
        service_order = frappe.get_doc("Service Order", card_id)

        if not service_order.has_permission("write"):
            return {"success": False, "message": _("Insufficient permissions")}

        result = {"success": True, "message": _("Action completed successfully")}

        if action_id == "start_service":
            service_order.status = "In Progress"
            service_order.started_on = get_datetime()

        elif action_id == "quality_check":
            service_order.status = "Quality Check"
            service_order.quality_check_on = get_datetime()

        elif action_id == "complete_service" or action_id == "approve_complete":
            service_order.status = "Completed"
            service_order.completed_on = get_datetime()

        elif action_id == "deliver_vehicle":
            service_order.status = "Delivered"
            service_order.delivered_on = get_datetime()

        elif action_id == "return_progress":
            service_order.status = "In Progress"

        elif action_id == "view_details":
            result["action"] = "redirect"
            result["url"] = f"/app/service-order/{card_id}"
            return result

        elif action_id == "send_update":
            # This would integrate with SMS/notification system
            result["message"] = _("Update sent successfully")
            return result

        # Save changes
        service_order.save()
        frappe.db.commit()

        result["updated_card"] = ServiceOrderKanbanManager()._format_service_order_card(
            service_order.as_dict()
        )
        return result

    except Exception as e:
        frappe.log_error(f"Card action execution failed: {str(e)}", "Service Order Kanban")
        return {"success": False, "message": _("Action failed: {0}").format(str(e))}
