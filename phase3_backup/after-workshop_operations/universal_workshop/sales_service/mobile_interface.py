import frappe
from frappe import _
from frappe.utils import nowdate, get_datetime, add_days, cint, flt
from frappe.desk.doctype.notification_log.notification_log import make_notification_log
from typing import Dict, List, Optional
import json
import base64
from io import BytesIO
from PIL import Image
import os


class MobileInterfaceAPI:
    """Comprehensive mobile interface API for Universal Workshop ERP"""

    def __init__(self):
        self.current_user = frappe.session.user
        self.user_roles = frappe.get_roles(self.current_user)
        self.is_technician = "Workshop Technician" in self.user_roles
        self.is_customer = "Customer" in self.user_roles
        self.is_manager = "Workshop Manager" in self.user_roles

    def get_user_dashboard(self) -> Dict:
        """Get role-based mobile dashboard data"""
        try:
            if self.is_technician:
                return self._get_technician_dashboard()
            elif self.is_customer:
                return self._get_customer_dashboard()
            elif self.is_manager:
                return self._get_manager_dashboard()
            else:
                return {"status": "error", "message": _("Unauthorized access"), "data": {}}
        except Exception as e:
            frappe.log_error(f"Mobile dashboard error: {str(e)}")
            return {"status": "error", "message": _("Failed to load dashboard"), "data": {}}

    def _get_technician_dashboard(self) -> Dict:
        """Get technician mobile dashboard data"""
        today = nowdate()

        # Get assigned service orders
        assigned_orders = frappe.get_list(
            "Sales Order",
            filters={
                "technician": self.current_user,
                "status": ["in", ["Draft", "To Deliver and Bill", "To Bill"]],
                "transaction_date": [">=", today],
            },
            fields=[
                "name",
                "customer",
                "customer_name_ar",
                "grand_total",
                "status",
                "transaction_date",
                "delivery_date",
            ],
            order_by="transaction_date desc",
            limit=10,
        )

        # Get today's time logs
        time_logs = frappe.get_list(
            "Labor Time Log",
            filters={
                "technician": self.current_user,
                "date": today,
                "status": ["in", ["Active", "Paused", "Completed"]],
            },
            fields=[
                "name",
                "service_order",
                "start_time",
                "end_time",
                "total_hours",
                "status",
                "hourly_rate",
            ],
            order_by="start_time desc",
        )

        # Get pending quality inspections
        pending_inspections = frappe.get_list(
            "Quality Inspection Checklist",
            filters={"inspector": self.current_user, "status": ["in", ["draft", "in_progress"]]},
            fields=[
                "name",
                "service_order",
                "checklist_type",
                "vehicle_type",
                "completion_percentage",
                "status",
                "inspection_date",
            ],
            order_by="creation desc",
            limit=5,
        )

        # Calculate today's stats
        total_hours = sum([flt(log.get("total_hours", 0)) for log in time_logs])
        total_earnings = sum(
            [flt(log.get("total_hours", 0)) * flt(log.get("hourly_rate", 0)) for log in time_logs]
        )

        return {
            "status": "success",
            "data": {
                "user_info": {
                    "name": frappe.get_value("User", self.current_user, "full_name"),
                    "role": _("Technician"),
                    "employee_id": frappe.get_value(
                        "Employee", {"user_id": self.current_user}, "name"
                    ),
                },
                "daily_stats": {
                    "assigned_orders": len(assigned_orders),
                    "total_hours": total_hours,
                    "total_earnings": total_earnings,
                    "pending_inspections": len(pending_inspections),
                },
                "assigned_orders": assigned_orders,
                "active_time_logs": time_logs,
                "pending_inspections": pending_inspections,
                "quick_actions": [
                    {"id": "scan_barcode", "label": _("Scan Barcode"), "icon": "barcode"},
                    {"id": "start_timer", "label": _("Start Timer"), "icon": "play"},
                    {"id": "take_photo", "label": _("Take Photo"), "icon": "camera"},
                    {"id": "voice_note", "label": _("Voice Note"), "icon": "microphone"},
                ],
            },
        }

    def _get_customer_dashboard(self) -> Dict:
        """Get customer mobile dashboard data"""
        customer = frappe.get_value("Customer", {"email_id": self.current_user}, "name")

        if not customer:
            return {"status": "error", "message": _("Customer profile not found"), "data": {}}

        # Get customer's vehicles
        vehicles = frappe.get_list(
            "Vehicle Profile",
            filters={"customer": customer},
            fields=[
                "name",
                "license_plate",
                "make",
                "model",
                "year",
                "color_ar",
                "color_en",
                "last_service_date",
            ],
            order_by="creation desc",
        )

        # Get recent service orders
        recent_orders = frappe.get_list(
            "Sales Order",
            filters={"customer": customer},
            fields=[
                "name",
                "transaction_date",
                "status",
                "grand_total",
                "delivery_status",
                "billing_status",
            ],
            order_by="transaction_date desc",
            limit=5,
        )

        # Get upcoming appointments
        upcoming_appointments = frappe.get_list(
            "Service Appointment",
            filters={
                "customer": customer,
                "appointment_date": [">=", nowdate()],
                "status": ["in", ["Scheduled", "Confirmed"]],
            },
            fields=[
                "name",
                "appointment_date",
                "appointment_time",
                "service_type",
                "status",
                "workshop",
            ],
            order_by="appointment_date asc",
            limit=3,
        )

        return {
            "status": "success",
            "data": {
                "customer_info": {
                    "name": frappe.get_value("Customer", customer, "customer_name"),
                    "name_ar": frappe.get_value("Customer", customer, "customer_name_ar"),
                    "phone": frappe.get_value("Customer", customer, "mobile_no"),
                    "email": frappe.get_value("Customer", customer, "email_id"),
                },
                "vehicles": vehicles,
                "recent_orders": recent_orders,
                "upcoming_appointments": upcoming_appointments,
                "quick_actions": [
                    {"id": "book_appointment", "label": _("Book Appointment"), "icon": "calendar"},
                    {"id": "track_order", "label": _("Track Order"), "icon": "truck"},
                    {"id": "contact_workshop", "label": _("Contact Workshop"), "icon": "phone"},
                    {"id": "view_history", "label": _("Service History"), "icon": "history"},
                ],
            },
        }

    def _get_manager_dashboard(self) -> Dict:
        """Get manager mobile dashboard data"""
        today = nowdate()

        # Get workshop overview stats
        total_orders = frappe.db.count("Sales Order", {"transaction_date": today, "docstatus": 1})

        active_technicians = frappe.db.count("Labor Time Log", {"date": today, "status": "Active"})

        pending_approvals = frappe.db.count(
            "Quality Inspection Checklist", {"status": "in_progress"}
        )

        # Get recent activities
        recent_activities = frappe.get_list(
            "Sales Order",
            filters={"transaction_date": today},
            fields=["name", "customer", "customer_name_ar", "status", "grand_total", "technician"],
            order_by="creation desc",
            limit=10,
        )

        # Get technician performance
        technician_performance = frappe.db.sql(
            """
            SELECT 
                t.technician,
                u.full_name,
                COUNT(t.name) as active_jobs,
                SUM(t.total_hours) as total_hours,
                AVG(t.hourly_rate) as avg_rate
            FROM `tabLabor Time Log` t
            LEFT JOIN `tabUser` u ON t.technician = u.name
            WHERE t.date = %s
            GROUP BY t.technician
            ORDER BY total_hours DESC
        """,
            [today],
            as_dict=True,
        )

        return {
            "status": "success",
            "data": {
                "workshop_stats": {
                    "total_orders_today": total_orders,
                    "active_technicians": active_technicians,
                    "pending_approvals": pending_approvals,
                    "revenue_today": frappe.db.sql(
                        """
                        SELECT SUM(grand_total) FROM `tabSales Order`
                        WHERE transaction_date = %s AND docstatus = 1
                    """,
                        [today],
                    )[0][0]
                    or 0,
                },
                "recent_activities": recent_activities,
                "technician_performance": technician_performance,
                "quick_actions": [
                    {"id": "view_reports", "label": _("View Reports"), "icon": "chart-bar"},
                    {"id": "approve_orders", "label": _("Approve Orders"), "icon": "check"},
                    {"id": "manage_staff", "label": _("Manage Staff"), "icon": "users"},
                    {"id": "inventory_check", "label": _("Inventory Check"), "icon": "boxes"},
                ],
            },
        }

    def start_labor_timer(self, service_order: str, task_description: str = "") -> Dict:
        """Start labor time tracking for mobile technician"""
        try:
            # Check if timer already active
            existing_timer = frappe.get_list(
                "Labor Time Log",
                filters={
                    "technician": self.current_user,
                    "service_order": service_order,
                    "status": "Active",
                },
                limit=1,
            )

            if existing_timer:
                return {
                    "status": "error",
                    "message": _("Timer already active for this service order"),
                }

            # Create new time log
            time_log = frappe.new_doc("Labor Time Log")
            time_log.technician = self.current_user
            time_log.service_order = service_order
            time_log.date = nowdate()
            time_log.start_time = get_datetime()
            time_log.task_description = task_description
            time_log.status = "Active"
            time_log.created_via_mobile = True
            time_log.insert()

            # Send real-time notification
            frappe.publish_realtime(
                event="timer_started",
                message={
                    "service_order": service_order,
                    "technician": self.current_user,
                    "time_log_id": time_log.name,
                },
                user=self.current_user,
            )

            return {
                "status": "success",
                "message": _("Timer started successfully"),
                "timer_id": time_log.name,
                "start_time": time_log.start_time,
            }

        except Exception as e:
            frappe.log_error(f"Timer start error: {str(e)}")
            return {"status": "error", "message": _("Failed to start timer")}

    def stop_labor_timer(self, timer_id: str, notes: str = "") -> Dict:
        """Stop labor time tracking"""
        try:
            time_log = frappe.get_doc("Labor Time Log", timer_id)

            if time_log.technician != self.current_user:
                return {"status": "error", "message": _("Unauthorized access to timer")}

            if time_log.status != "Active":
                return {"status": "error", "message": _("Timer is not active")}

            # Stop timer
            time_log.end_time = get_datetime()
            time_log.status = "Completed"
            time_log.completion_notes = notes
            time_log.calculate_total_hours()
            time_log.save()

            # Send notification
            frappe.publish_realtime(
                event="timer_stopped",
                message={
                    "timer_id": timer_id,
                    "total_hours": time_log.total_hours,
                    "labor_cost": time_log.labor_cost,
                },
                user=self.current_user,
            )

            return {
                "status": "success",
                "message": _("Timer stopped successfully"),
                "total_hours": time_log.total_hours,
                "labor_cost": time_log.labor_cost,
            }

        except Exception as e:
            frappe.log_error(f"Timer stop error: {str(e)}")
            return {"status": "error", "message": _("Failed to stop timer")}

    def upload_mobile_photo(
        self,
        service_order: str,
        photo_data: str,
        description: str = "",
        photo_type: str = "general",
    ) -> Dict:
        """Upload photo from mobile device"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(
                photo_data.split(",")[1] if "," in photo_data else photo_data
            )

            # Create PIL image for processing
            image = Image.open(BytesIO(image_data))

            # Resize if too large (max 1920x1080)
            max_size = (1920, 1080)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save processed image
            output_buffer = BytesIO()
            image.save(output_buffer, format="JPEG", quality=85, optimize=True)
            processed_data = output_buffer.getvalue()

            # Create file record
            file_doc = frappe.new_doc("File")
            file_doc.file_name = (
                f"mobile_photo_{service_order}_{nowdate()}_{frappe.generate_hash(length=8)}.jpg"
            )
            file_doc.attached_to_doctype = "Sales Order"
            file_doc.attached_to_name = service_order
            file_doc.is_private = 0
            file_doc.content = processed_data
            file_doc.decode = False
            file_doc.save()

            # Create mobile photo log
            photo_log = frappe.new_doc("Mobile Photo Log")
            photo_log.service_order = service_order
            photo_log.uploaded_by = self.current_user
            photo_log.photo_type = photo_type
            photo_log.description = description
            photo_log.file_url = file_doc.file_url
            photo_log.upload_timestamp = get_datetime()
            photo_log.insert()

            return {
                "status": "success",
                "message": _("Photo uploaded successfully"),
                "file_url": file_doc.file_url,
                "photo_id": photo_log.name,
            }

        except Exception as e:
            frappe.log_error(f"Photo upload error: {str(e)}")
            return {"status": "error", "message": _("Failed to upload photo")}

    def scan_barcode(self, barcode_data: str, scan_type: str = "part") -> Dict:
        """Process barcode scan from mobile device"""
        try:
            if scan_type == "part":
                # Look up part information
                item = frappe.get_value(
                    "Item",
                    {"item_code": barcode_data},
                    [
                        "name",
                        "item_name",
                        "item_name_ar",
                        "standard_rate",
                        "stock_qty",
                        "item_group",
                        "description",
                    ],
                    as_dict=True,
                )

                if item:
                    # Get current stock
                    current_stock = (
                        frappe.db.get_value("Bin", {"item_code": barcode_data}, "actual_qty") or 0
                    )

                    return {
                        "status": "success",
                        "scan_type": "part",
                        "data": {
                            "item_code": barcode_data,
                            "item_name": item.item_name,
                            "item_name_ar": item.item_name_ar,
                            "current_stock": current_stock,
                            "standard_rate": item.standard_rate,
                            "item_group": item.item_group,
                            "description": item.description,
                        },
                    }
                else:
                    return {
                        "status": "error",
                        "message": _("Part not found: {0}").format(barcode_data),
                    }

            elif scan_type == "vehicle":
                # Look up vehicle by license plate or VIN
                vehicle = frappe.get_value(
                    "Vehicle Profile",
                    {"license_plate": barcode_data},
                    ["name", "customer", "make", "model", "year", "vin"],
                    as_dict=True,
                )

                if vehicle:
                    return {"status": "success", "scan_type": "vehicle", "data": vehicle}
                else:
                    return {
                        "status": "error",
                        "message": _("Vehicle not found: {0}").format(barcode_data),
                    }

            else:
                return {"status": "error", "message": _("Invalid scan type: {0}").format(scan_type)}

        except Exception as e:
            frappe.log_error(f"Barcode scan error: {str(e)}")
            return {"status": "error", "message": _("Failed to process barcode scan")}

    def update_service_status(
        self, service_order: str, status: str, notes: str = "", location: Dict = None
    ) -> Dict:
        """Update service order status from mobile"""
        try:
            order = frappe.get_doc("Sales Order", service_order)

            # Validate technician access
            if not self.is_manager and order.get("technician") != self.current_user:
                return {"status": "error", "message": _("Unauthorized access to service order")}

            # Update status
            order.workflow_state = status
            order.mobile_status_update = True
            order.save()

            # Create status log
            status_log = frappe.new_doc("Service Status Log")
            status_log.service_order = service_order
            status_log.updated_by = self.current_user
            status_log.status = status
            status_log.notes = notes
            status_log.update_timestamp = get_datetime()

            if location:
                status_log.latitude = location.get("latitude")
                status_log.longitude = location.get("longitude")
                status_log.location_accuracy = location.get("accuracy")

            status_log.insert()

            # Send real-time notification
            frappe.publish_realtime(
                event="service_status_updated",
                message={
                    "service_order": service_order,
                    "status": status,
                    "updated_by": self.current_user,
                },
            )

            return {
                "status": "success",
                "message": _("Service status updated successfully"),
                "new_status": status,
            }

        except Exception as e:
            frappe.log_error(f"Status update error: {str(e)}")
            return {"status": "error", "message": _("Failed to update service status")}

    def get_offline_data(self) -> Dict:
        """Get essential data for offline mobile operation"""
        try:
            offline_data = {
                "user_info": {
                    "name": frappe.get_value("User", self.current_user, "full_name"),
                    "roles": self.user_roles,
                },
                "lookup_data": {
                    "service_types": frappe.get_list(
                        "Service Type", fields=["name", "service_name", "service_name_ar"], limit=50
                    ),
                    "common_parts": frappe.get_list(
                        "Item",
                        filters={"is_stock_item": 1, "disabled": 0},
                        fields=["item_code", "item_name", "item_name_ar", "standard_rate"],
                        order_by="item_name",
                        limit=100,
                    ),
                    "status_options": [
                        "Draft",
                        "In Progress",
                        "Quality Check",
                        "Completed",
                        "On Hold",
                    ],
                },
                "sync_timestamp": get_datetime(),
            }

            if self.is_technician:
                # Add technician-specific offline data
                offline_data["assigned_orders"] = frappe.get_list(
                    "Sales Order",
                    filters={"technician": self.current_user, "docstatus": 1},
                    fields=["name", "customer", "customer_name_ar", "status"],
                    limit=20,
                )

            return {"status": "success", "data": offline_data}

        except Exception as e:
            frappe.log_error(f"Offline data error: {str(e)}")
            return {"status": "error", "message": _("Failed to load offline data")}


# WhiteListed API Methods
@frappe.whitelist()
def get_mobile_dashboard():
    """Get mobile dashboard data for current user"""
    api = MobileInterfaceAPI()
    return api.get_user_dashboard()


@frappe.whitelist()
def start_mobile_timer(service_order, task_description=""):
    """Start labor timer from mobile"""
    api = MobileInterfaceAPI()
    return api.start_labor_timer(service_order, task_description)


@frappe.whitelist()
def stop_mobile_timer(timer_id, notes=""):
    """Stop labor timer from mobile"""
    api = MobileInterfaceAPI()
    return api.stop_labor_timer(timer_id, notes)


@frappe.whitelist()
def upload_mobile_photo(service_order, photo_data, description="", photo_type="general"):
    """Upload photo from mobile device"""
    api = MobileInterfaceAPI()
    return api.upload_mobile_photo(service_order, photo_data, description, photo_type)


@frappe.whitelist()
def scan_mobile_barcode(barcode_data, scan_type="part"):
    """Process barcode scan from mobile"""
    api = MobileInterfaceAPI()
    return api.scan_barcode(barcode_data, scan_type)


@frappe.whitelist()
def update_mobile_service_status(service_order, status, notes="", location=None):
    """Update service status from mobile"""
    api = MobileInterfaceAPI()
    if location and isinstance(location, str):
        location = frappe.parse_json(location)
    return api.update_service_status(service_order, status, notes, location)


@frappe.whitelist()
def get_mobile_offline_data():
    """Get offline data for mobile app"""
    api = MobileInterfaceAPI()
    return api.get_offline_data()


@frappe.whitelist()
def sync_mobile_data(sync_data):
    """Sync mobile app data with server"""
    try:
        if isinstance(sync_data, str):
            sync_data = frappe.parse_json(sync_data)

        results = []
        api = MobileInterfaceAPI()

        # Process each sync item
        for item in sync_data.get("items", []):
            item_type = item.get("type")

            if item_type == "status_update":
                result = api.update_service_status(
                    item["service_order"],
                    item["status"],
                    item.get("notes", ""),
                    item.get("location"),
                )
            elif item_type == "timer_action":
                if item["action"] == "start":
                    result = api.start_labor_timer(
                        item["service_order"], item.get("task_description", "")
                    )
                elif item["action"] == "stop":
                    result = api.stop_labor_timer(item["timer_id"], item.get("notes", ""))
            elif item_type == "photo_upload":
                result = api.upload_mobile_photo(
                    item["service_order"],
                    item["photo_data"],
                    item.get("description", ""),
                    item.get("photo_type", "general"),
                )
            else:
                result = {"status": "error", "message": f"Unknown sync item type: {item_type}"}

            results.append({"item_id": item.get("id"), "result": result})

        return {
            "status": "success",
            "message": f"Synced {len(results)} items",
            "results": results,
            "sync_timestamp": get_datetime(),
        }

    except Exception as e:
        frappe.log_error(f"Mobile sync error: {str(e)}")
        return {"status": "error", "message": _("Failed to sync mobile data")}


def test_mobile_interface():
    """Test mobile interface functionality"""
    api = MobileInterfaceAPI()

    # Test dashboard
    dashboard_result = api.get_user_dashboard()

    # Test barcode scan
    scan_result = api.scan_barcode("TEST-PART-001", "part")

    # Test offline data
    offline_result = api.get_offline_data()

    return {
        "dashboard_test": dashboard_result,
        "scan_test": scan_result,
        "offline_test": offline_result,
    }
