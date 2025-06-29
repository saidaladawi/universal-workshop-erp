# -*- coding: utf-8 -*-
# Copyright (c) 2025, Universal Workshop and contributors
# For license information, please see license.txt

"""
Service Order Kanban Board Backend
==================================

This module provides the backend API and logic for the Service Order Kanban board
with drag-and-drop functionality, status transitions, and real-time updates.

Features:
- Drag-and-drop status updates with automatic workflow transitions
- Real-time WebSocket updates for collaborative management
- Arabic/English dual language support with RTL formatting
- Role-based permissions and field visibility
- Advanced filtering and search with Arabic keyword support
- Performance optimization with caching and pagination
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, get_datetime, now
from frappe.desk.reportview import get_filters_cond, get_match_cond
from frappe.model.db_query import DatabaseQuery


class ServiceOrderKanbanEngine:
    """
    Core engine for Service Order Kanban board functionality.
    Handles data retrieval, status transitions, and real-time updates.
    """

    # Kanban status definitions with Arabic translations
    KANBAN_STATUSES = {
        "Draft": {
            "en": "Draft",
            "ar": "مسودة",
            "color": "#6c757d",
            "icon": "fa-edit",
            "next_statuses": ["Scheduled"],
        },
        "Scheduled": {
            "en": "Scheduled",
            "ar": "مجدولة",
            "color": "#007bff",
            "icon": "fa-calendar",
            "next_statuses": ["In Progress", "Cancelled"],
        },
        "In Progress": {
            "en": "In Progress",
            "ar": "قيد التنفيذ",
            "color": "#ffc107",
            "icon": "fa-cog",
            "next_statuses": ["Quality Check", "Cancelled"],
        },
        "Quality Check": {
            "en": "Quality Check",
            "ar": "فحص الجودة",
            "color": "#fd7e14",
            "icon": "fa-search",
            "next_statuses": ["Completed", "In Progress"],
        },
        "Completed": {
            "en": "Completed",
            "ar": "مكتمل",
            "color": "#28a745",
            "icon": "fa-check",
            "next_statuses": ["Delivered"],
        },
        "Delivered": {
            "en": "Delivered",
            "ar": "تم التسليم",
            "color": "#17a2b8",
            "icon": "fa-truck",
            "next_statuses": [],
        },
        "Cancelled": {
            "en": "Cancelled",
            "ar": "ملغى",
            "color": "#dc3545",
            "icon": "fa-times",
            "next_statuses": [],
        },
    }

    def __init__(self):
        self.language = frappe.local.lang or "en"
        self.user = frappe.session.user
        self.user_roles = frappe.get_roles(self.user)

    def get_kanban_data(
        self, filters: Dict = None, limit: int = 50, start: int = 0
    ) -> Dict[str, Any]:
        """
        Get Kanban board data with service orders grouped by status.

        Args:
            filters: Optional filters for service orders
            limit: Maximum number of orders per status
            start: Starting offset for pagination

        Returns:
            Dictionary with status columns and service order cards
        """

        # Build base filters
        base_filters = self._build_base_filters(filters or {})

        # Get service orders for each status
        kanban_data = {}
        total_counts = {}

        for status, status_info in self.KANBAN_STATUSES.items():
            try:
                # Get orders for this status
                status_filters = {**base_filters, "status": status}
                orders = self._get_service_orders(status_filters, limit, start)

                # Get total count for pagination
                total_count = self._get_order_count(status_filters)

                # Format cards data
                cards = [self._format_service_order_card(order) for order in orders]

                kanban_data[status] = {
                    "title": status_info[self.language],
                    "color": status_info["color"],
                    "icon": status_info["icon"],
                    "cards": cards,
                    "count": total_count,
                    "next_statuses": status_info["next_statuses"],
                    "can_drag_to": self._get_allowed_transitions(status),
                    "can_create": self._can_create_in_status(status),
                }

                total_counts[status] = total_count

            except Exception as e:
                frappe.log_error(f"Error loading Kanban data for status {status}: {str(e)}")
                kanban_data[status] = {
                    "title": status_info[self.language],
                    "color": status_info["color"],
                    "icon": status_info["icon"],
                    "cards": [],
                    "count": 0,
                    "error": _("Failed to load data"),
                }

        return {
            "data": kanban_data,
            "totals": total_counts,
            "language": self.language,
            "user_permissions": self._get_user_permissions(),
            "filters_applied": filters or {},
            "pagination": {
                "limit": limit,
                "start": start,
                "has_more": any(total_counts[s] > start + limit for s in total_counts),
            },
        }

    def _build_base_filters(self, filters: Dict) -> Dict:
        """Build base filters for service order queries."""
        base_filters = {}

        # Date range filter
        if filters.get("date_range"):
            if filters["date_range"] == "today":
                base_filters["service_date"] = [">=", getdate()]
            elif filters["date_range"] == "this_week":
                base_filters["service_date"] = [">=", getdate() - timedelta(days=7)]
            elif filters["date_range"] == "this_month":
                base_filters["service_date"] = [">=", getdate().replace(day=1)]

        # Priority filter
        if filters.get("priority"):
            base_filters["priority"] = filters["priority"]

        # Technician filter
        if filters.get("technician"):
            base_filters["technician_assigned"] = filters["technician"]

        # Customer filter
        if filters.get("customer"):
            base_filters["customer"] = filters["customer"]

        # Service type filter
        if filters.get("service_type"):
            base_filters["service_type"] = filters["service_type"]

        # Workshop filter (for multi-workshop support)
        if filters.get("workshop"):
            base_filters["workshop"] = filters["workshop"]

        return base_filters

    def _get_service_orders(self, filters: Dict, limit: int, start: int) -> List[Dict]:
        """Get service orders with filters and pagination."""

        # Build query
        query = DatabaseQuery("Service Order")
        query.fields = [
            "name",
            "customer",
            "customer_name",
            "customer_name_ar",
            "vehicle",
            "make",
            "model",
            "year",
            "license_plate",
            "service_type",
            "service_type_ar",
            "status",
            "priority",
            "technician_assigned",
            "service_bay",
            "service_date",
            "estimated_completion_date",
            "final_amount",
            "description",
            "description_ar",
            "creation",
            "modified",
        ]

        # Apply filters
        for field, value in filters.items():
            if isinstance(value, list) and len(value) == 2:
                query.filters.append([field, value[0], value[1]])
            else:
                query.filters.append([field, "=", value])

        # Add permissions
        query.filters.extend(get_match_cond("Service Order"))

        # Order by priority and creation date
        query.order_by = 'FIELD(priority, "Urgent", "High", "Medium", "Low"), creation desc'

        # Apply pagination
        query.limit_start = start
        query.limit_page_length = limit

        return query.run(as_dict=True)

    def _get_order_count(self, filters: Dict) -> int:
        """Get total count of service orders for filters."""
        try:
            conditions = []
            values = []

            for field, value in filters.items():
                if isinstance(value, list) and len(value) == 2:
                    conditions.append(f"`{field}` {value[0]} %s")
                    values.append(value[1])
                else:
                    conditions.append(f"`{field}` = %s")
                    values.append(value)

            # Add permissions
            match_conditions = get_match_cond("Service Order")
            for condition in match_conditions:
                conditions.append(condition)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            result = frappe.db.sql(
                f"""
                SELECT COUNT(*) as count
                FROM `tabService Order`
                {where_clause}
            """,
                values,
                as_dict=True,
            )

            return result[0]["count"] if result else 0

        except Exception as e:
            frappe.log_error(f"Error getting order count: {str(e)}")
            return 0

    def _format_service_order_card(self, order: Dict) -> Dict:
        """Format service order data for Kanban card display."""

        # Calculate time information
        time_info = self._calculate_time_info(order)

        # Get customer display name (Arabic/English)
        customer_name = (
            order.get("customer_name_ar") if self.language == "ar" else order.get("customer_name")
        ) or order.get("customer_name", "")

        # Get service description (Arabic/English)
        description = (
            order.get("description_ar") if self.language == "ar" else order.get("description")
        ) or order.get("description", "")

        # Format vehicle info
        vehicle_info = f"{order.get('make', '')} {order.get('model', '')} {order.get('year', '')}"
        vehicle_info = vehicle_info.strip()

        return {
            "id": order["name"],
            "title": f"{customer_name} - {vehicle_info}",
            "customer": {
                "name": order.get("customer"),
                "display_name": customer_name,
                "arabic_name": order.get("customer_name_ar", ""),
                "english_name": order.get("customer_name", ""),
            },
            "vehicle": {
                "info": vehicle_info,
                "license_plate": order.get("license_plate", ""),
                "make": order.get("make", ""),
                "model": order.get("model", ""),
                "year": order.get("year", ""),
            },
            "service": {
                "type": order.get("service_type", ""),
                "type_ar": order.get("service_type_ar", ""),
                "description": description[:100] + "..." if len(description) > 100 else description,
                "bay": order.get("service_bay", ""),
                "amount": flt(order.get("final_amount", 0)),
            },
            "status": order.get("status"),
            "priority": order.get("priority", "Medium"),
            "priority_class": self._get_priority_class(order.get("priority")),
            "technician": {
                "assigned": order.get("technician_assigned"),
                "display_name": self._get_technician_name(order.get("technician_assigned")),
            },
            "timing": time_info,
            "permissions": self._get_card_permissions(order),
            "actions": self._get_card_actions(order),
            "creation": order.get("creation"),
            "modified": order.get("modified"),
        }

    def _calculate_time_info(self, order: Dict) -> Dict:
        """Calculate timing information for service order."""
        now_dt = get_datetime()
        service_date = get_datetime(order.get("service_date"))
        estimated_completion = (
            get_datetime(order.get("estimated_completion_date"))
            if order.get("estimated_completion_date")
            else None
        )

        time_info = {
            "service_date": service_date,
            "estimated_completion": estimated_completion,
            "is_overdue": False,
            "is_due_soon": False,
            "time_remaining": "",
            "days_since_creation": (now_dt - get_datetime(order.get("creation"))).days,
        }

        if estimated_completion:
            time_diff = estimated_completion - now_dt

            if time_diff.total_seconds() < 0:
                time_info["is_overdue"] = True
                time_info["time_remaining"] = _("Overdue")
            elif time_diff.total_seconds() < 3600:  # Less than 1 hour
                time_info["is_due_soon"] = True
                minutes = int(time_diff.total_seconds() / 60)
                time_info["time_remaining"] = _("{0} minutes remaining").format(minutes)
            elif time_diff.days == 0:  # Same day
                time_info["is_due_soon"] = True
                hours = int(time_diff.total_seconds() / 3600)
                time_info["time_remaining"] = _("{0} hours remaining").format(hours)
            else:
                time_info["time_remaining"] = _("{0} days remaining").format(time_diff.days)

        return time_info

    def _get_priority_class(self, priority: str) -> str:
        """Get CSS class for priority display."""
        priority_classes = {
            "Urgent": "priority-urgent",
            "High": "priority-high",
            "Medium": "priority-medium",
            "Low": "priority-low",
        }
        return priority_classes.get(priority, "priority-medium")

    def _get_technician_name(self, technician: str) -> str:
        """Get technician display name."""
        if not technician:
            return _("Unassigned")

        try:
            user_doc = frappe.get_doc("User", technician)
            return user_doc.full_name or user_doc.name
        except:
            return technician

    def _get_card_permissions(self, order: Dict) -> Dict:
        """Get permissions for service order card actions."""
        permissions = {
            "can_edit": False,
            "can_delete": False,
            "can_assign": False,
            "can_change_status": False,
            "can_view_details": True,
        }

        # Check user permissions
        if "Workshop Manager" in self.user_roles:
            permissions.update(
                {
                    "can_edit": True,
                    "can_delete": True,
                    "can_assign": True,
                    "can_change_status": True,
                }
            )
        elif "Workshop Technician" in self.user_roles:
            permissions.update(
                {
                    "can_edit": order.get("technician_assigned") == self.user,
                    "can_change_status": order.get("technician_assigned") == self.user,
                }
            )

        return permissions

    def _get_card_actions(self, order: Dict) -> List[Dict]:
        """Get available actions for service order card."""
        actions = []
        permissions = self._get_card_permissions(order)
        current_status = order.get("status")

        # View details action (always available)
        actions.append(
            {
                "label": _("View Details"),
                "icon": "fa-eye",
                "action": "view_details",
                "class": "btn-outline-primary btn-sm",
            }
        )

        # Edit action
        if permissions["can_edit"]:
            actions.append(
                {
                    "label": _("Edit"),
                    "icon": "fa-edit",
                    "action": "edit",
                    "class": "btn-outline-secondary btn-sm",
                }
            )

        # Status-specific actions
        if permissions["can_change_status"]:
            if current_status == "Draft":
                actions.append(
                    {
                        "label": _("Schedule"),
                        "icon": "fa-calendar",
                        "action": "change_status",
                        "target_status": "Scheduled",
                        "class": "btn-outline-primary btn-sm",
                    }
                )
            elif current_status == "Scheduled":
                actions.append(
                    {
                        "label": _("Start Work"),
                        "icon": "fa-play",
                        "action": "change_status",
                        "target_status": "In Progress",
                        "class": "btn-outline-success btn-sm",
                    }
                )
            elif current_status == "In Progress":
                actions.append(
                    {
                        "label": _("Quality Check"),
                        "icon": "fa-search",
                        "action": "change_status",
                        "target_status": "Quality Check",
                        "class": "btn-outline-warning btn-sm",
                    }
                )
            elif current_status == "Quality Check":
                actions.append(
                    {
                        "label": _("Complete"),
                        "icon": "fa-check",
                        "action": "change_status",
                        "target_status": "Completed",
                        "class": "btn-outline-success btn-sm",
                    }
                )
            elif current_status == "Completed":
                actions.append(
                    {
                        "label": _("Deliver"),
                        "icon": "fa-truck",
                        "action": "change_status",
                        "target_status": "Delivered",
                        "class": "btn-outline-info btn-sm",
                    }
                )

        # Assign technician action
        if permissions["can_assign"] and not order.get("technician_assigned"):
            actions.append(
                {
                    "label": _("Assign Technician"),
                    "icon": "fa-user-plus",
                    "action": "assign_technician",
                    "class": "btn-outline-warning btn-sm",
                }
            )

        return actions

    def _get_allowed_transitions(self, from_status: str) -> List[str]:
        """Get allowed status transitions for drag-and-drop."""
        status_info = self.KANBAN_STATUSES.get(from_status, {})
        next_statuses = status_info.get("next_statuses", [])

        # Filter based on user permissions
        allowed = []
        for status in next_statuses:
            if self._can_transition_to_status(from_status, status):
                allowed.append(status)

        return allowed

    def _can_transition_to_status(self, from_status: str, to_status: str) -> bool:
        """Check if user can transition between statuses."""
        # Workshop Managers can make any valid transition
        if "Workshop Manager" in self.user_roles:
            return True

        # Technicians can only transition their assigned orders
        if "Workshop Technician" in self.user_roles:
            # Additional logic would check if technician is assigned to the order
            return True

        return False

    def _can_create_in_status(self, status: str) -> bool:
        """Check if user can create new orders in this status."""
        if status == "Draft":
            return "Workshop Manager" in self.user_roles or "Workshop Technician" in self.user_roles
        return False

    def _get_user_permissions(self) -> Dict:
        """Get user permissions for Kanban board features."""
        return {
            "can_create_orders": "Workshop Manager" in self.user_roles
            or "Workshop Technician" in self.user_roles,
            "can_manage_all_orders": "Workshop Manager" in self.user_roles,
            "can_assign_technicians": "Workshop Manager" in self.user_roles,
            "can_view_all_orders": True,
            "can_edit_own_orders": "Workshop Technician" in self.user_roles,
            "can_filter_by_technician": True,
            "can_export_data": "Workshop Manager" in self.user_roles,
        }


# API Methods for Frontend Integration


@frappe.whitelist()
def get_kanban_board_data(filters=None, limit=50, start=0):
    """
    API method to get Kanban board data for frontend.

    Args:
        filters: JSON string of filters to apply
        limit: Maximum number of records per status
        start: Starting offset for pagination

    Returns:
        Dictionary with Kanban board data
    """
    try:
        # Parse filters if provided
        if filters and isinstance(filters, str):
            filters = json.loads(filters)

        # Initialize Kanban engine
        engine = ServiceOrderKanbanEngine()

        # Get board data
        board_data = engine.get_kanban_data(
            filters=filters or {}, limit=cint(limit), start=cint(start)
        )

        return {
            "success": True,
            "data": board_data,
            "message": _("Kanban board data loaded successfully"),
        }

    except Exception as e:
        frappe.log_error(f"Error loading Kanban board: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Failed to load Kanban board data")}


@frappe.whitelist()
def update_service_order_status(order_name, new_status, notes=None):
    """
    API method to update service order status via drag-and-drop.

    Args:
        order_name: Name of the service order
        new_status: New status to set
        notes: Optional notes for the status change

    Returns:
        Success/error response
    """
    try:
        # Validate order exists and user has permission
        if not frappe.db.exists("Service Order", order_name):
            return {
                "success": False,
                "message": _("Service Order {0} not found").format(order_name),
            }

        # Get service order
        service_order = frappe.get_doc("Service Order", order_name)

        # Check permissions
        engine = ServiceOrderKanbanEngine()
        permissions = engine._get_card_permissions(service_order.as_dict())

        if not permissions.get("can_change_status"):
            return {
                "success": False,
                "message": _("You don't have permission to change this order's status"),
            }

        # Validate status transition
        current_status = service_order.status
        allowed_transitions = engine._get_allowed_transitions(current_status)

        if new_status not in allowed_transitions:
            return {
                "success": False,
                "message": _("Invalid status transition from {0} to {1}").format(
                    _(current_status), _(new_status)
                ),
            }

        # Update status with timestamp tracking
        old_status = service_order.status
        service_order.status = new_status

        # Set status-specific timestamps
        now_time = now()
        if new_status == "Scheduled":
            service_order.scheduled_on = now_time
        elif new_status == "In Progress":
            service_order.started_on = now_time
        elif new_status == "Quality Check":
            service_order.quality_check_on = now_time
        elif new_status == "Completed":
            service_order.completed_on = now_time
        elif new_status == "Delivered":
            service_order.delivered_on = now_time

        # Add status history entry
        if not hasattr(service_order, "status_history"):
            service_order.status_history = []

        service_order.append(
            "status_history",
            {
                "from_status": old_status,
                "to_status": new_status,
                "changed_by": frappe.session.user,
                "change_date": now_time,
                "notes": notes or "",
                "duration_in_previous_status": _calculate_status_duration(
                    service_order, old_status
                ),
            },
        )

        # Save changes
        service_order.save()

        # Send real-time update via WebSocket
        _send_kanban_update(
            "status_change",
            {
                "order_name": order_name,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": frappe.session.user,
                "timestamp": now_time,
            },
        )

        return {
            "success": True,
            "message": _("Status updated from {0} to {1}").format(_(old_status), _(new_status)),
            "data": {"old_status": old_status, "new_status": new_status, "timestamp": now_time},
        }

    except Exception as e:
        frappe.log_error(f"Error updating service order status: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Failed to update status")}


@frappe.whitelist()
def assign_technician_to_order(order_name, technician_user, notes=None):
    """
    API method to assign technician to service order.

    Args:
        order_name: Name of the service order
        technician_user: User ID of technician to assign
        notes: Optional assignment notes

    Returns:
        Success/error response
    """
    try:
        # Validate inputs
        if not frappe.db.exists("Service Order", order_name):
            return {
                "success": False,
                "message": _("Service Order {0} not found").format(order_name),
            }

        if not frappe.db.exists("User", technician_user):
            return {"success": False, "message": _("User {0} not found").format(technician_user)}

        # Check if user has technician role
        user_roles = frappe.get_roles(technician_user)
        if "Workshop Technician" not in user_roles:
            return {
                "success": False,
                "message": _("User {0} is not a Workshop Technician").format(technician_user),
            }

        # Check permissions
        engine = ServiceOrderKanbanEngine()
        if not engine._get_user_permissions().get("can_assign_technicians"):
            return {
                "success": False,
                "message": _("You don't have permission to assign technicians"),
            }

        # Update service order
        service_order = frappe.get_doc("Service Order", order_name)
        old_technician = service_order.technician_assigned
        service_order.technician_assigned = technician_user

        # Add assignment note
        if notes:
            current_notes = service_order.internal_notes or ""
            timestamp = now()
            assignment_note = (
                f"\n[{timestamp}] Technician assigned: {technician_user}\nNotes: {notes}"
            )
            service_order.internal_notes = current_notes + assignment_note

        service_order.save()

        # Send real-time update
        _send_kanban_update(
            "technician_assigned",
            {
                "order_name": order_name,
                "old_technician": old_technician,
                "new_technician": technician_user,
                "assigned_by": frappe.session.user,
                "timestamp": now(),
            },
        )

        return {
            "success": True,
            "message": _("Technician {0} assigned successfully").format(technician_user),
            "data": {"old_technician": old_technician, "new_technician": technician_user},
        }

    except Exception as e:
        frappe.log_error(f"Error assigning technician: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Failed to assign technician")}


@frappe.whitelist()
def search_service_orders(query, filters=None, limit=20):
    """
    API method for Arabic/English search functionality.

    Args:
        query: Search query string
        filters: Optional additional filters
        limit: Maximum number of results

    Returns:
        List of matching service orders
    """
    try:
        if not query or len(query.strip()) < 2:
            return {"success": False, "message": _("Search query must be at least 2 characters")}

        query = query.strip()

        # Build search conditions for both Arabic and English
        search_conditions = []
        search_params = []

        # Customer name search (both languages)
        search_conditions.append("(customer_name LIKE %s OR customer_name_ar LIKE %s)")
        search_params.extend([f"%{query}%", f"%{query}%"])

        # Vehicle details search
        search_conditions.append("(make LIKE %s OR model LIKE %s OR license_plate LIKE %s)")
        search_params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

        # Service description search (both languages)
        search_conditions.append("(description LIKE %s OR description_ar LIKE %s)")
        search_params.extend([f"%{query}%", f"%{query}%"])

        # Service order name/number search
        search_conditions.append("name LIKE %s")
        search_params.append(f"%{query}%")

        # Build WHERE clause
        where_conditions = [f"({' OR '.join(search_conditions)})"]

        # Add additional filters
        if filters:
            if isinstance(filters, str):
                filters = json.loads(filters)

            for field, value in filters.items():
                if value:
                    where_conditions.append(f"{field} = %s")
                    search_params.append(value)

        # Add permissions
        match_conditions = get_match_cond("Service Order")
        where_conditions.extend(match_conditions)

        where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""

        # Execute search query
        sql = f"""
            SELECT 
                name, customer, customer_name, customer_name_ar,
                vehicle, make, model, year, license_plate,
                service_type, service_type_ar, status, priority,
                technician_assigned, service_date, final_amount,
                description, description_ar
            FROM `tabService Order`
            {where_clause}
            ORDER BY 
                CASE 
                    WHEN name LIKE %s THEN 1
                    WHEN customer_name LIKE %s THEN 2
                    WHEN customer_name_ar LIKE %s THEN 2
                    ELSE 3
                END,
                modified DESC
            LIMIT {cint(limit)}
        """

        # Add order relevance parameters
        search_params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])

        results = frappe.db.sql(sql, search_params, as_dict=True)

        # Format results for frontend
        engine = ServiceOrderKanbanEngine()
        formatted_results = []

        for result in results:
            formatted_results.append(
                {
                    "id": result["name"],
                    "title": f"{result.get('customer_name', '')} - {result.get('make', '')} {result.get('model', '')}",
                    "subtitle": result.get("service_type", ""),
                    "status": result.get("status"),
                    "priority": result.get("priority"),
                    "amount": flt(result.get("final_amount", 0)),
                    "date": result.get("service_date"),
                    "customer_ar": result.get("customer_name_ar", ""),
                    "description": result.get("description", ""),
                    "description_ar": result.get("description_ar", ""),
                    "url": f"/app/service-order/{result['name']}",
                }
            )

        return {
            "success": True,
            "data": formatted_results,
            "count": len(formatted_results),
            "query": query,
            "message": _("Found {0} results").format(len(formatted_results)),
        }

    except Exception as e:
        frappe.log_error(f"Error searching service orders: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Search failed")}


@frappe.whitelist()
def get_kanban_filters_data():
    """
    API method to get filter options for Kanban board.

    Returns:
        Dictionary with filter options
    """
    try:
        # Get technicians
        technicians = frappe.get_list(
            "User",
            filters={"enabled": 1, "name": ["!=", "Guest"]},
            fields=["name", "full_name"],
            order_by="full_name",
        )

        # Filter technicians with Workshop role
        workshop_technicians = []
        for tech in technicians:
            user_roles = frappe.get_roles(tech["name"])
            if "Workshop Technician" in user_roles or "Workshop Manager" in user_roles:
                workshop_technicians.append(
                    {"value": tech["name"], "label": tech["full_name"] or tech["name"]}
                )

        # Get service types
        service_types = [
            "Oil Change",
            "Brake Service",
            "Transmission Service",
            "Engine Repair",
            "Air Conditioning",
            "Electrical",
            "Tire Service",
            "General Maintenance",
            "Inspection",
            "Emergency Repair",
            "Custom Service",
        ]

        # Get customers (recent ones)
        recent_customers = frappe.get_list(
            "Customer",
            filters={"disabled": 0},
            fields=["name", "customer_name", "customer_name_ar"],
            order_by="modified desc",
            limit=100,
        )

        return {
            "success": True,
            "data": {
                "technicians": workshop_technicians,
                "service_types": [{"value": st, "label": _(st)} for st in service_types],
                "priorities": [
                    {"value": "Urgent", "label": _("Urgent")},
                    {"value": "High", "label": _("High")},
                    {"value": "Medium", "label": _("Medium")},
                    {"value": "Low", "label": _("Low")},
                ],
                "date_ranges": [
                    {"value": "today", "label": _("Today")},
                    {"value": "this_week", "label": _("This Week")},
                    {"value": "this_month", "label": _("This Month")},
                    {"value": "all", "label": _("All Time")},
                ],
                "customers": [
                    {
                        "value": c["name"],
                        "label": c.get("customer_name_ar") or c.get("customer_name", ""),
                        "label_en": c.get("customer_name", ""),
                    }
                    for c in recent_customers
                ],
            },
        }

    except Exception as e:
        frappe.log_error(f"Error getting filter data: {str(e)}")
        return {"success": False, "error": str(e), "message": _("Failed to load filter options")}


# Utility Functions


def _calculate_status_duration(service_order, status):
    """Calculate duration spent in a specific status."""
    try:
        status_history = service_order.get("status_history", [])

        # Find when the status was entered
        status_start = None
        for entry in reversed(status_history):
            if entry.get("to_status") == status:
                status_start = get_datetime(entry.get("change_date"))
                break

        if not status_start:
            # If no history entry, use creation date for first status
            if status == "Draft":
                status_start = get_datetime(service_order.creation)
            else:
                return 0

        # Calculate duration until now
        duration = get_datetime() - status_start
        return duration.total_seconds() / 3600  # Return hours

    except Exception:
        return 0


def _send_kanban_update(event_type, data):
    """Send real-time update via WebSocket."""
    try:
        frappe.publish_realtime(
            event="kanban_update",
            message={"type": event_type, "data": data, "timestamp": now()},
            room="workshop_kanban",
        )
    except Exception as e:
        frappe.log_error(f"Error sending real-time update: {str(e)}")


# Background job for periodic data refresh
def refresh_kanban_cache():
    """Background job to refresh Kanban cache periodically."""
    try:
        # Clear any cached data
        frappe.cache().delete_key("kanban_*")

        # Trigger refresh for active sessions
        frappe.publish_realtime(
            event="kanban_refresh", message={"timestamp": now()}, room="workshop_kanban"
        )

    except Exception as e:
        frappe.log_error(f"Error refreshing Kanban cache: {str(e)}")
