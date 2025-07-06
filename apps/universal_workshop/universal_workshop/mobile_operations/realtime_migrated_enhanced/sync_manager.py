"""
PWA Sync Manager for Universal Workshop ERP
Handles offline/online synchronization for Progressive Web App

Features:
- Offline-first data synchronization
- Arabic content sync optimization
- Conflict resolution with business logic
- Mobile technician sync coordination
- Workshop floor real-time updates
- Cultural business rules enforcement
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cint, flt, add_to_date
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio
from threading import Lock
import base64
from enum import Enum


class SyncStatus(Enum):
    """Synchronization status types"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    CANCELLED = "cancelled"


class SyncPriority(Enum):
    """Synchronization priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class ConflictResolution(Enum):
    """Conflict resolution strategies"""

    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE = "merge"
    BUSINESS_LOGIC = "business_logic"


class PWASyncManager:
    """
    Comprehensive PWA synchronization system for Universal Workshop ERP
    Handles offline/online data sync with Arabic content optimization
    """

    def __init__(self):
        self.sync_queue: List[Dict] = []
        self.sync_history: List[Dict] = []
        self.conflict_queue: List[Dict] = []
        self.sync_lock = Lock()

        # Arabic and cultural settings
        self.arabic_enabled = True
        self.cultural_sync_rules = True
        self.business_hours_sync = True

        # Sync configuration
        self.sync_config = {
            "batch_size": 50,
            "max_retries": 3,
            "retry_delay": 60,  # seconds
            "conflict_timeout": 3600,  # 1 hour
            "offline_retention_days": 30,
            "sync_interval": 300,  # 5 minutes
        }

        # Priority DocTypes for workshop operations
        self.priority_doctypes = {
            "Service Order": SyncPriority.CRITICAL,
            "Customer": SyncPriority.HIGH,
            "Vehicle": SyncPriority.HIGH,
            "Technician": SyncPriority.HIGH,
            "Item": SyncPriority.NORMAL,
            "Stock Entry": SyncPriority.HIGH,
            "Service Appointment": SyncPriority.CRITICAL,
            "Workshop Profile": SyncPriority.NORMAL,
        }

        # Sync statistics
        self.stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "conflicts_resolved": 0,
            "arabic_content_synced": 0,
            "by_doctype": {},
            "by_user": {},
            "avg_sync_time": 0,
        }

        self._initialize_sync_handlers()

    def _initialize_sync_handlers(self):
        """Initialize sync handlers for different DocTypes"""

        self.sync_handlers = {
            "Service Order": self._sync_service_order,
            "Customer": self._sync_customer,
            "Vehicle": self._sync_vehicle,
            "Technician": self._sync_technician,
            "Item": self._sync_item,
            "Stock Entry": self._sync_stock_entry,
            "Service Appointment": self._sync_service_appointment,
        }

        self.conflict_resolvers = {
            "Service Order": self._resolve_service_order_conflict,
            "Customer": self._resolve_customer_conflict,
            "Vehicle": self._resolve_vehicle_conflict,
            "default": self._resolve_default_conflict,
        }

    async def queue_sync_operation(
        self,
        operation_type: str,
        doctype: str,
        doc_name: str,
        data: Dict,
        user_id: str,
        workshop_id: str = None,
        priority: SyncPriority = None,
        offline_timestamp: datetime = None,
    ) -> str:
        """Queue a synchronization operation"""

        try:
            # Determine priority if not specified
            if priority is None:
                priority = self.priority_doctypes.get(doctype, SyncPriority.NORMAL)

            # Create sync operation
            sync_operation = {
                "id": frappe.generate_hash(length=12),
                "operation_type": operation_type,  # create, update, delete
                "doctype": doctype,
                "doc_name": doc_name,
                "data": data,
                "user_id": user_id,
                "workshop_id": workshop_id,
                "priority": priority.value,
                "status": SyncStatus.PENDING.value,
                "created_at": now_datetime().isoformat(),
                "offline_timestamp": offline_timestamp.isoformat() if offline_timestamp else None,
                "retry_count": 0,
                "error_log": [],
                "arabic_content": self._contains_arabic_content(data),
                "checksum": self._calculate_checksum(data),
            }

            # Add to queue
            with self.sync_lock:
                self.sync_queue.append(sync_operation)
                self.sync_queue.sort(key=lambda x: (-x["priority"], x["created_at"]))

            frappe.logger().info(
                f"Sync operation queued: {sync_operation['id']} ({operation_type} {doctype})"
            )

            # Process immediately if high priority
            if priority.value >= SyncPriority.HIGH.value:
                await self._process_sync_operation(sync_operation)

            return sync_operation["id"]

        except Exception as e:
            frappe.log_error(f"Failed to queue sync operation: {e}")
            raise

    async def process_sync_queue(self, batch_size: int = None):
        """Process pending sync operations in batches"""

        if batch_size is None:
            batch_size = self.sync_config["batch_size"]

        with self.sync_lock:
            pending_operations = [
                op for op in self.sync_queue if op["status"] == SyncStatus.PENDING.value
            ][:batch_size]

        if not pending_operations:
            return {"processed": 0, "message": "No pending operations"}

        processed_count = 0
        failed_count = 0

        for operation in pending_operations:
            try:
                await self._process_sync_operation(operation)
                processed_count += 1
            except Exception as e:
                failed_count += 1
                frappe.log_error(f"Sync operation failed: {operation['id']} - {e}")

        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(pending_operations),
        }

    async def _process_sync_operation(self, operation: Dict):
        """Process individual sync operation"""

        operation_id = operation["id"]
        operation_type = operation["operation_type"]
        doctype = operation["doctype"]
        doc_name = operation["doc_name"]
        data = operation["data"]

        try:
            # Update status to in progress
            operation["status"] = SyncStatus.IN_PROGRESS.value
            operation["processing_started"] = now_datetime().isoformat()

            # Check for conflicts
            conflict_check = await self._check_for_conflicts(operation)

            if conflict_check["has_conflict"]:
                operation["status"] = SyncStatus.CONFLICT.value
                operation["conflict_details"] = conflict_check["details"]

                # Add to conflict queue for manual resolution
                with self.sync_lock:
                    self.conflict_queue.append(operation.copy())

                frappe.logger().warning(f"Sync conflict detected: {operation_id}")
                return

            # Process the operation based on type
            if operation_type == "create":
                result = await self._process_create_operation(operation)
            elif operation_type == "update":
                result = await self._process_update_operation(operation)
            elif operation_type == "delete":
                result = await self._process_delete_operation(operation)
            else:
                raise ValueError(f"Unknown operation type: {operation_type}")

            # Update operation status
            operation["status"] = SyncStatus.COMPLETED.value
            operation["processing_completed"] = now_datetime().isoformat()
            operation["result"] = result

            # Update statistics
            self._update_sync_stats(operation, True)

            # Move to history
            with self.sync_lock:
                self.sync_history.append(operation.copy())
                try:
                    self.sync_queue.remove(operation)
                except ValueError:
                    pass

            frappe.logger().info(f"Sync operation completed: {operation_id}")

        except Exception as e:
            operation["status"] = SyncStatus.FAILED.value
            operation["error"] = str(e)
            operation["retry_count"] += 1
            operation["error_log"].append(
                {"timestamp": now_datetime().isoformat(), "error": str(e)}
            )

            # Retry if under max retries
            if operation["retry_count"] < self.sync_config["max_retries"]:
                operation["status"] = SyncStatus.PENDING.value
                operation["next_retry"] = (
                    now_datetime() + timedelta(seconds=self.sync_config["retry_delay"])
                ).isoformat()

            self._update_sync_stats(operation, False)
            frappe.log_error(f"Sync operation failed: {operation_id} - {e}")

    async def _check_for_conflicts(self, operation: Dict) -> Dict:
        """Check for synchronization conflicts"""

        doctype = operation["doctype"]
        doc_name = operation["doc_name"]
        operation_type = operation["operation_type"]
        client_checksum = operation["checksum"]
        offline_timestamp = operation.get("offline_timestamp")

        # Skip conflict check for create operations
        if operation_type == "create":
            return {"has_conflict": False}

        try:
            # Check if document exists on server
            if not frappe.db.exists(doctype, doc_name):
                if operation_type == "update":
                    return {
                        "has_conflict": True,
                        "details": {
                            "type": "document_not_found",
                            "message": f"{doctype} {doc_name} not found on server",
                        },
                    }
                return {"has_conflict": False}

            # Get current server document
            server_doc = frappe.get_doc(doctype, doc_name)
            server_checksum = self._calculate_checksum(server_doc.as_dict())

            # Check if document was modified on server after client went offline
            if offline_timestamp:
                offline_dt = get_datetime(offline_timestamp)
                if server_doc.modified > offline_dt:
                    return {
                        "has_conflict": True,
                        "details": {
                            "type": "concurrent_modification",
                            "server_modified": server_doc.modified.isoformat(),
                            "client_offline_since": offline_timestamp,
                            "server_checksum": server_checksum,
                            "client_checksum": client_checksum,
                        },
                    }

            # Check checksum mismatch
            if server_checksum != client_checksum and operation_type == "update":
                return {
                    "has_conflict": True,
                    "details": {
                        "type": "checksum_mismatch",
                        "server_checksum": server_checksum,
                        "client_checksum": client_checksum,
                    },
                }

            return {"has_conflict": False}

        except Exception as e:
            frappe.log_error(f"Conflict check failed: {e}")
            return {
                "has_conflict": True,
                "details": {"type": "conflict_check_error", "error": str(e)},
            }

    async def _process_create_operation(self, operation: Dict) -> Dict:
        """Process document creation operation"""

        doctype = operation["doctype"]
        data = operation["data"]
        user_id = operation["user_id"]

        # Use sync handler if available
        if doctype in self.sync_handlers:
            return await self.sync_handlers[doctype](operation, "create")

        # Default create operation
        try:
            # Set user context
            frappe.set_user(user_id)

            # Create new document
            doc = frappe.new_doc(doctype)
            doc.update(data)

            # Handle Arabic content validation
            if operation.get("arabic_content"):
                self._validate_arabic_content(doc)

            doc.insert()
            frappe.db.commit()

            return {
                "status": "success",
                "doc_name": doc.name,
                "message": f"{doctype} created successfully",
            }

        except Exception as e:
            frappe.db.rollback()
            raise

    async def _process_update_operation(self, operation: Dict) -> Dict:
        """Process document update operation"""

        doctype = operation["doctype"]
        doc_name = operation["doc_name"]
        data = operation["data"]
        user_id = operation["user_id"]

        # Use sync handler if available
        if doctype in self.sync_handlers:
            return await self.sync_handlers[doctype](operation, "update")

        # Default update operation
        try:
            # Set user context
            frappe.set_user(user_id)

            # Get and update document
            doc = frappe.get_doc(doctype, doc_name)
            doc.update(data)

            # Handle Arabic content validation
            if operation.get("arabic_content"):
                self._validate_arabic_content(doc)

            doc.save()
            frappe.db.commit()

            return {
                "status": "success",
                "doc_name": doc.name,
                "message": f"{doctype} updated successfully",
            }

        except Exception as e:
            frappe.db.rollback()
            raise

    async def _process_delete_operation(self, operation: Dict) -> Dict:
        """Process document deletion operation"""

        doctype = operation["doctype"]
        doc_name = operation["doc_name"]
        user_id = operation["user_id"]

        try:
            # Set user context
            frappe.set_user(user_id)

            # Delete document
            frappe.delete_doc(doctype, doc_name)
            frappe.db.commit()

            return {
                "status": "success",
                "doc_name": doc_name,
                "message": f"{doctype} deleted successfully",
            }

        except Exception as e:
            frappe.db.rollback()
            raise

    # Specialized sync handlers for workshop DocTypes
    async def _sync_service_order(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Service Orders"""

        doctype = operation["doctype"]
        data = operation["data"]
        user_id = operation["user_id"]

        try:
            frappe.set_user(user_id)

            if operation_type == "create":
                # Create new service order
                service_order = frappe.new_doc("Service Order")
                service_order.update(data)

                # Validate workshop business rules
                self._validate_service_order_business_rules(service_order)

                service_order.insert()

                # Trigger workshop events
                from .event_bus import get_workshop_event_bus, EventType, EventPriority

                event_bus = get_workshop_event_bus()

                await event_bus.publish(
                    EventType.SERVICE_STARTED,
                    {
                        "service_order_id": service_order.name,
                        "customer": service_order.customer,
                        "vehicle": service_order.vehicle,
                        "service_name": service_order.service_type,
                    },
                    priority=EventPriority.HIGH,
                    workshop_id=operation.get("workshop_id"),
                )

                frappe.db.commit()
                return {"status": "success", "doc_name": service_order.name}

            elif operation_type == "update":
                # Update existing service order
                doc_name = operation["doc_name"]
                service_order = frappe.get_doc("Service Order", doc_name)
                old_status = service_order.status

                service_order.update(data)
                self._validate_service_order_business_rules(service_order)
                service_order.save()

                # Trigger status change events if applicable
                if old_status != service_order.status:
                    from .event_bus import get_workshop_event_bus, EventType, EventPriority

                    event_bus = get_workshop_event_bus()

                    if service_order.status == "Completed":
                        await event_bus.publish(
                            EventType.SERVICE_COMPLETED,
                            {
                                "service_order_id": service_order.name,
                                "customer": service_order.customer,
                                "vehicle": service_order.vehicle,
                            },
                            priority=EventPriority.HIGH,
                            workshop_id=operation.get("workshop_id"),
                        )

                frappe.db.commit()
                return {"status": "success", "doc_name": service_order.name}

        except Exception as e:
            frappe.db.rollback()
            raise

    async def _sync_customer(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Customers"""

        data = operation["data"]
        user_id = operation["user_id"]

        try:
            frappe.set_user(user_id)

            if operation_type == "create":
                customer = frappe.new_doc("Customer")
                customer.update(data)

                # Validate Arabic customer data
                self._validate_arabic_customer_data(customer)

                customer.insert()
                frappe.db.commit()

                return {"status": "success", "doc_name": customer.name}

            elif operation_type == "update":
                doc_name = operation["doc_name"]
                customer = frappe.get_doc("Customer", doc_name)
                customer.update(data)

                self._validate_arabic_customer_data(customer)
                customer.save()
                frappe.db.commit()

                return {"status": "success", "doc_name": customer.name}

        except Exception as e:
            frappe.db.rollback()
            raise

    async def _sync_vehicle(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Vehicles"""

        data = operation["data"]
        user_id = operation["user_id"]

        try:
            frappe.set_user(user_id)

            if operation_type == "create":
                vehicle = frappe.new_doc("Vehicle")
                vehicle.update(data)

                # Validate vehicle data for Oman
                self._validate_oman_vehicle_data(vehicle)

                vehicle.insert()
                frappe.db.commit()

                return {"status": "success", "doc_name": vehicle.name}

            elif operation_type == "update":
                doc_name = operation["doc_name"]
                vehicle = frappe.get_doc("Vehicle", doc_name)
                vehicle.update(data)

                self._validate_oman_vehicle_data(vehicle)
                vehicle.save()
                frappe.db.commit()

                return {"status": "success", "doc_name": vehicle.name}

        except Exception as e:
            frappe.db.rollback()
            raise

    async def _sync_technician(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Technicians"""

        data = operation["data"]
        user_id = operation["user_id"]

        try:
            frappe.set_user(user_id)

            if operation_type == "create":
                technician = frappe.new_doc("Technician")
                technician.update(data)

                # Validate technician data
                self._validate_technician_data(technician)

                technician.insert()
                frappe.db.commit()

                return {"status": "success", "doc_name": technician.name}

            elif operation_type == "update":
                doc_name = operation["doc_name"]
                technician = frappe.get_doc("Technician", doc_name)
                technician.update(data)

                self._validate_technician_data(technician)
                technician.save()
                frappe.db.commit()

                return {"status": "success", "doc_name": technician.name}

        except Exception as e:
            frappe.db.rollback()
            raise

    async def _sync_item(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Items (Parts)"""
        return await self._process_default_sync(operation, operation_type)

    async def _sync_stock_entry(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Stock Entries"""
        return await self._process_default_sync(operation, operation_type)

    async def _sync_service_appointment(self, operation: Dict, operation_type: str) -> Dict:
        """Specialized sync handler for Service Appointments"""
        return await self._process_default_sync(operation, operation_type)

    async def _process_default_sync(self, operation: Dict, operation_type: str) -> Dict:
        """Default sync processing for standard DocTypes"""

        if operation_type == "create":
            return await self._process_create_operation(operation)
        elif operation_type == "update":
            return await self._process_update_operation(operation)
        elif operation_type == "delete":
            return await self._process_delete_operation(operation)

    # Conflict resolution methods
    async def resolve_conflict(
        self, conflict_id: str, resolution: ConflictResolution, manual_data: Dict = None
    ) -> Dict:
        """Resolve synchronization conflict"""

        try:
            # Find conflict in queue
            conflict_operation = None
            with self.sync_lock:
                for operation in self.conflict_queue:
                    if operation["id"] == conflict_id:
                        conflict_operation = operation
                        break

            if not conflict_operation:
                return {"status": "error", "message": "Conflict not found"}

            doctype = conflict_operation["doctype"]

            # Use specialized conflict resolver if available
            if doctype in self.conflict_resolvers:
                result = await self.conflict_resolvers[doctype](
                    conflict_operation, resolution, manual_data
                )
            else:
                result = await self._resolve_default_conflict(
                    conflict_operation, resolution, manual_data
                )

            # Remove from conflict queue and add to history
            with self.sync_lock:
                self.conflict_queue.remove(conflict_operation)
                conflict_operation["status"] = SyncStatus.COMPLETED.value
                conflict_operation["resolution"] = resolution.value
                conflict_operation["resolved_at"] = now_datetime().isoformat()
                self.sync_history.append(conflict_operation)

            self.stats["conflicts_resolved"] += 1

            return result

        except Exception as e:
            frappe.log_error(f"Conflict resolution failed: {e}")
            return {"status": "error", "error": str(e)}

    async def _resolve_service_order_conflict(
        self, operation: Dict, resolution: ConflictResolution, manual_data: Dict = None
    ) -> Dict:
        """Resolve Service Order conflicts with business logic"""

        if resolution == ConflictResolution.BUSINESS_LOGIC:
            # Apply workshop business rules for conflict resolution
            # Priority: Customer satisfaction > Technician efficiency > System consistency

            doc_name = operation["doc_name"]
            client_data = operation["data"]

            # Get current server state
            server_doc = frappe.get_doc("Service Order", doc_name)

            # Business rule: Status changes follow workflow
            if "status" in client_data:
                client_status = client_data["status"]
                server_status = server_doc.status

                # Allow progression but not regression
                status_hierarchy = {
                    "Draft": 0,
                    "Scheduled": 1,
                    "In Progress": 2,
                    "On Hold": 2,
                    "Completed": 3,
                    "Cancelled": 3,
                }

                client_level = status_hierarchy.get(client_status, 0)
                server_level = status_hierarchy.get(server_status, 0)

                if client_level >= server_level:
                    # Client wins for status progression
                    server_doc.status = client_status

            # Business rule: Preserve customer and vehicle data
            customer_fields = ["customer", "vehicle", "customer_name", "vehicle_number"]
            for field in customer_fields:
                if field in client_data and client_data[field]:
                    setattr(server_doc, field, client_data[field])

            # Business rule: Merge technician assignments
            if "assigned_technician" in client_data and client_data["assigned_technician"]:
                if not server_doc.assigned_technician:
                    server_doc.assigned_technician = client_data["assigned_technician"]

            server_doc.save()
            frappe.db.commit()

            return {
                "status": "success",
                "resolution": "business_logic_applied",
                "doc_name": server_doc.name,
            }

        return await self._resolve_default_conflict(operation, resolution, manual_data)

    async def _resolve_customer_conflict(
        self, operation: Dict, resolution: ConflictResolution, manual_data: Dict = None
    ) -> Dict:
        """Resolve Customer conflicts"""

        if resolution == ConflictResolution.BUSINESS_LOGIC:
            # Preserve Arabic names and contact information
            doc_name = operation["doc_name"]
            client_data = operation["data"]

            server_doc = frappe.get_doc("Customer", doc_name)

            # Preserve Arabic content
            arabic_fields = ["customer_name_ar", "address_ar", "notes_ar"]
            for field in arabic_fields:
                if field in client_data and client_data[field]:
                    setattr(server_doc, field, client_data[field])

            # Update contact information if newer
            contact_fields = ["phone", "email", "mobile_no"]
            for field in contact_fields:
                if field in client_data and client_data[field]:
                    setattr(server_doc, field, client_data[field])

            server_doc.save()
            frappe.db.commit()

            return {
                "status": "success",
                "resolution": "customer_data_merged",
                "doc_name": server_doc.name,
            }

        return await self._resolve_default_conflict(operation, resolution, manual_data)

    async def _resolve_vehicle_conflict(
        self, operation: Dict, resolution: ConflictResolution, manual_data: Dict = None
    ) -> Dict:
        """Resolve Vehicle conflicts"""

        if resolution == ConflictResolution.BUSINESS_LOGIC:
            # Preserve vehicle identification and service history
            doc_name = operation["doc_name"]
            client_data = operation["data"]

            server_doc = frappe.get_doc("Vehicle", doc_name)

            # Preserve critical vehicle data
            critical_fields = ["license_plate", "vin", "make", "model", "year"]
            for field in critical_fields:
                if field in client_data and client_data[field]:
                    # Only update if server field is empty
                    if not getattr(server_doc, field, None):
                        setattr(server_doc, field, client_data[field])

            # Update mileage if higher (assumes forward progression)
            if "mileage" in client_data:
                client_mileage = client_data["mileage"]
                if client_mileage > (server_doc.mileage or 0):
                    server_doc.mileage = client_mileage

            server_doc.save()
            frappe.db.commit()

            return {
                "status": "success",
                "resolution": "vehicle_data_merged",
                "doc_name": server_doc.name,
            }

        return await self._resolve_default_conflict(operation, resolution, manual_data)

    async def _resolve_default_conflict(
        self, operation: Dict, resolution: ConflictResolution, manual_data: Dict = None
    ) -> Dict:
        """Default conflict resolution"""

        doc_name = operation["doc_name"]
        doctype = operation["doctype"]
        client_data = operation["data"]

        if resolution == ConflictResolution.SERVER_WINS:
            # Keep server version, discard client changes
            return {"status": "success", "resolution": "server_version_kept", "doc_name": doc_name}

        elif resolution == ConflictResolution.CLIENT_WINS:
            # Apply client changes, overwrite server
            server_doc = frappe.get_doc(doctype, doc_name)
            server_doc.update(client_data)
            server_doc.save()
            frappe.db.commit()

            return {
                "status": "success",
                "resolution": "client_version_applied",
                "doc_name": doc_name,
            }

        elif resolution == ConflictResolution.MANUAL_REVIEW:
            if not manual_data:
                return {"status": "error", "message": "Manual data required"}

            server_doc = frappe.get_doc(doctype, doc_name)
            server_doc.update(manual_data)
            server_doc.save()
            frappe.db.commit()

            return {
                "status": "success",
                "resolution": "manual_resolution_applied",
                "doc_name": doc_name,
            }

        return {"status": "error", "message": "Unknown resolution strategy"}

    # Validation methods
    def _validate_arabic_content(self, doc):
        """Validate Arabic content in document"""

        # Check for Arabic fields and validate encoding
        for field in doc.meta.fields:
            if field.fieldname.endswith("_ar"):
                value = getattr(doc, field.fieldname, None)
                if value and not self._is_valid_arabic_text(value):
                    frappe.throw(_(f"Invalid Arabic text in field {field.label}"))

    def _validate_service_order_business_rules(self, service_order):
        """Validate Service Order business rules"""

        # Check required Arabic fields
        if not service_order.get("customer_name_ar"):
            frappe.throw(_("Arabic customer name is required"))

        # Validate workshop business hours
        if self.business_hours_sync:
            current_time = now_datetime().time()
            if current_time.hour < 7 or current_time.hour > 18:
                if service_order.priority != "Emergency":
                    frappe.throw(
                        _("Service orders outside business hours must be marked as Emergency")
                    )

    def _validate_arabic_customer_data(self, customer):
        """Validate Arabic customer data"""

        if not customer.get("customer_name_ar"):
            frappe.throw(_("Arabic customer name is required"))

        # Validate Oman phone number format
        phone = customer.get("phone") or customer.get("mobile_no")
        if phone and not phone.startswith("+968"):
            frappe.throw(_("Phone number must start with +968 for Oman"))

    def _validate_oman_vehicle_data(self, vehicle):
        """Validate vehicle data for Oman"""

        # Validate license plate format (Oman format)
        license_plate = vehicle.get("license_plate")
        if license_plate:
            # Oman license plate format validation
            import re

            if not re.match(r"^[0-9]{1,6}$", license_plate.replace(" ", "")):
                frappe.throw(_("Invalid Oman license plate format"))

    def _validate_technician_data(self, technician):
        """Validate technician data"""

        if not technician.get("technician_name_ar"):
            frappe.throw(_("Arabic technician name is required"))

    # Utility methods
    def _contains_arabic_content(self, data: Dict) -> bool:
        """Check if data contains Arabic content"""

        def has_arabic(text):
            if not isinstance(text, str):
                return False
            arabic_range = range(0x0600, 0x06FF + 1)
            return any(ord(char) in arabic_range for char in text)

        for key, value in data.items():
            if key.endswith("_ar") or has_arabic(str(value)):
                return True

        return False

    def _is_valid_arabic_text(self, text: str) -> bool:
        """Validate Arabic text encoding and content"""

        try:
            # Check if text can be encoded/decoded properly
            text.encode("utf-8").decode("utf-8")

            # Check for Arabic characters
            arabic_range = range(0x0600, 0x06FF + 1)
            has_arabic = any(ord(char) in arabic_range for char in text)

            return has_arabic

        except UnicodeError:
            return False

    def _calculate_checksum(self, data: Dict) -> str:
        """Calculate checksum for data integrity"""

        # Convert data to sorted JSON string for consistent hashing
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(json_str.encode("utf-8")).hexdigest()

    def _update_sync_stats(self, operation: Dict, success: bool):
        """Update synchronization statistics"""

        self.stats["total_syncs"] += 1

        if success:
            self.stats["successful_syncs"] += 1
        else:
            self.stats["failed_syncs"] += 1

        if operation.get("arabic_content"):
            self.stats["arabic_content_synced"] += 1

        # Update DocType stats
        doctype = operation["doctype"]
        if doctype not in self.stats["by_doctype"]:
            self.stats["by_doctype"][doctype] = {"synced": 0, "success": 0}

        self.stats["by_doctype"][doctype]["synced"] += 1
        if success:
            self.stats["by_doctype"][doctype]["success"] += 1

        # Update user stats
        user_id = operation["user_id"]
        if user_id not in self.stats["by_user"]:
            self.stats["by_user"][user_id] = {"synced": 0, "success": 0}

        self.stats["by_user"][user_id]["synced"] += 1
        if success:
            self.stats["by_user"][user_id]["success"] += 1

    def get_sync_status(self, operation_id: str = None, user_id: str = None) -> Dict:
        """Get synchronization status"""

        if operation_id:
            # Find specific operation
            for operation in self.sync_queue + self.sync_history:
                if operation["id"] == operation_id:
                    return operation
            return {"error": "Operation not found"}

        if user_id:
            # Get operations for specific user
            user_operations = [
                op for op in self.sync_queue + self.sync_history if op["user_id"] == user_id
            ]
            return {
                "user_id": user_id,
                "operations": user_operations[-10:],  # Last 10 operations
                "pending_count": len([op for op in self.sync_queue if op["user_id"] == user_id]),
            }

        # General sync status
        return {
            "queue_size": len(self.sync_queue),
            "conflicts": len(self.conflict_queue),
            "statistics": self.stats,
        }

    def get_conflict_queue(self) -> List[Dict]:
        """Get current conflict queue"""
        return self.conflict_queue.copy()

    def clear_old_history(self, older_than_days: int = 30):
        """Clear old sync history"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cutoff_iso = cutoff_date.isoformat()

        with self.sync_lock:
            self.sync_history = [h for h in self.sync_history if h["created_at"] > cutoff_iso]

        frappe.logger().info(f"Cleared sync history older than {older_than_days} days")


# Global sync manager instance
pwa_sync_manager = None


def get_pwa_sync_manager() -> PWASyncManager:
    """Get or create global PWA sync manager instance"""
    global pwa_sync_manager
    if pwa_sync_manager is None:
        pwa_sync_manager = PWASyncManager()
    return pwa_sync_manager


# API methods for external access
@frappe.whitelist()
def queue_pwa_sync(
    operation_type: str,
    doctype: str,
    doc_name: str,
    data: dict,
    priority: str = "NORMAL",
    offline_timestamp: str = None,
):
    """Queue PWA synchronization operation (API endpoint)"""
    try:
        sync_manager = get_pwa_sync_manager()

        # Convert priority string to enum
        priority_enum = SyncPriority[priority.upper()]

        # Convert offline timestamp
        offline_dt = None
        if offline_timestamp:
            offline_dt = get_datetime(offline_timestamp)

        # Queue sync operation asynchronously
        operation_id = asyncio.create_task(
            sync_manager.queue_sync_operation(
                operation_type=operation_type,
                doctype=doctype,
                doc_name=doc_name,
                data=data,
                user_id=frappe.session.user,
                priority=priority_enum,
                offline_timestamp=offline_dt,
            )
        )

        return {"status": "queued", "operation_type": operation_type}

    except Exception as e:
        frappe.log_error(f"Failed to queue PWA sync: {e}")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def process_pwa_sync_queue(batch_size: int = 50):
    """Process PWA sync queue (API endpoint)"""
    sync_manager = get_pwa_sync_manager()
    return asyncio.create_task(sync_manager.process_sync_queue(batch_size=cint(batch_size)))


@frappe.whitelist()
def get_pwa_sync_status(operation_id: str = None, user_id: str = None):
    """Get PWA sync status (API endpoint)"""
    sync_manager = get_pwa_sync_manager()
    return sync_manager.get_sync_status(operation_id=operation_id, user_id=user_id)


@frappe.whitelist()
def resolve_pwa_conflict(conflict_id: str, resolution: str, manual_data: dict = None):
    """Resolve PWA synchronization conflict (API endpoint)"""
    try:
        sync_manager = get_pwa_sync_manager()
        resolution_enum = ConflictResolution(resolution.lower())

        result = asyncio.create_task(
            sync_manager.resolve_conflict(
                conflict_id=conflict_id, resolution=resolution_enum, manual_data=manual_data
            )
        )

        return result

    except Exception as e:
        frappe.log_error(f"Failed to resolve PWA conflict: {e}")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def get_pwa_conflicts():
    """Get PWA conflict queue (API endpoint)"""
    sync_manager = get_pwa_sync_manager()
    return sync_manager.get_conflict_queue()
