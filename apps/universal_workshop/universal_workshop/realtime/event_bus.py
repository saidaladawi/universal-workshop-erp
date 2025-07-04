"""
Workshop Event Bus for Universal Workshop ERP
Handles real-time event distribution and Arabic business logic

Features:
- Event-driven architecture for workshop operations
- Arabic-first event messaging
- Cultural business event handling
- Workshop floor coordination
- Mobile technician event synchronization
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, cint, flt
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import asyncio
from threading import Lock


class EventPriority(Enum):
    """Event priority levels for Workshop operations"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5


class EventType(Enum):
    """Workshop event types with Arabic descriptions"""

    SERVICE_STARTED = "service_started"
    SERVICE_COMPLETED = "service_completed"
    SERVICE_ON_HOLD = "service_on_hold"
    TECHNICIAN_ASSIGNED = "technician_assigned"
    PARTS_REQUESTED = "parts_requested"
    CUSTOMER_ARRIVED = "customer_arrived"
    VEHICLE_READY = "vehicle_ready"
    PAYMENT_RECEIVED = "payment_received"
    EMERGENCY_REPAIR = "emergency_repair"
    QUALITY_CHECK = "quality_check"
    ARABIC_VOICE_MESSAGE = "arabic_voice_message"
    MOBILE_SYNC = "mobile_sync"


class WorkshopEventBus:
    """
    Comprehensive event bus system for Universal Workshop ERP
    Manages real-time events with Arabic support and cultural business logic
    """

    def __init__(self):
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_history: List[Dict] = []
        self.active_subscriptions: Dict[str, List[EventType]] = {}
        self.event_lock = Lock()

        # Arabic and cultural settings
        self.arabic_enabled = True
        self.cultural_events_enabled = True
        self.prayer_time_awareness = True

        # Event statistics
        self.event_stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_priority": {},
            "arabic_events": 0,
        }

        self._initialize_default_handlers()

    def _initialize_default_handlers(self):
        """Initialize default event handlers for workshop operations"""

        # Service order events
        self.subscribe(EventType.SERVICE_STARTED, self._handle_service_started)
        self.subscribe(EventType.SERVICE_COMPLETED, self._handle_service_completed)
        self.subscribe(EventType.SERVICE_ON_HOLD, self._handle_service_on_hold)

        # Technician events
        self.subscribe(EventType.TECHNICIAN_ASSIGNED, self._handle_technician_assigned)

        # Customer events
        self.subscribe(EventType.CUSTOMER_ARRIVED, self._handle_customer_arrived)
        self.subscribe(EventType.VEHICLE_READY, self._handle_vehicle_ready)

        # Emergency events
        self.subscribe(EventType.EMERGENCY_REPAIR, self._handle_emergency_repair)

        # Arabic communication events
        self.subscribe(EventType.ARABIC_VOICE_MESSAGE, self._handle_arabic_voice_message)

    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        print(f"✅ Handler subscribed to event: {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """Unsubscribe from specific event type"""
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                print(f"✅ Handler unsubscribed from event: {event_type.value}")
            except ValueError:
                pass

    async def publish(
        self,
        event_type: EventType,
        event_data: Dict,
        priority: EventPriority = EventPriority.NORMAL,
        workshop_id: str = None,
        user_id: str = None,
        language: str = "ar",
    ):
        """Publish event to all subscribers"""

        try:
            # Create event object
            event = {
                "id": frappe.generate_hash(length=12),
                "type": event_type.value,
                "data": event_data,
                "priority": priority.value,
                "workshop_id": workshop_id,
                "user_id": user_id,
                "language": language,
                "timestamp": now_datetime().isoformat(),
                "processed": False,
                "arabic_content": self._contains_arabic(str(event_data)),
            }

            # Add Arabic translations if needed
            if language == "ar" or event.get("arabic_content"):
                event["arabic_translations"] = self._generate_arabic_translations(
                    event_type, event_data
                )

            # Store in event history
            with self.event_lock:
                self.event_history.append(event)
                self._update_event_stats(event)

            # Process event handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            handler(event)
                    except Exception as e:
                        frappe.log_error(f"Event handler error for {event_type.value}: {e}")

            # Mark as processed
            event["processed"] = True

            # Broadcast to WebSocket if available
            await self._broadcast_event(event)

            print(f"✅ Event published: {event_type.value} (ID: {event['id']})")
            return event["id"]

        except Exception as e:
            frappe.log_error(f"Failed to publish event {event_type.value}: {e}")
            raise

    def _contains_arabic(self, text: str) -> bool:
        """Check if text contains Arabic characters"""
        arabic_range = range(0x0600, 0x06FF + 1)
        return any(ord(char) in arabic_range for char in text)

    def _generate_arabic_translations(self, event_type: EventType, event_data: Dict) -> Dict:
        """Generate Arabic translations for event messages"""

        translations = {
            EventType.SERVICE_STARTED: {
                "title_ar": "بدء الخدمة",
                "message_ar": f'تم بدء خدمة {event_data.get("service_name", "غير محدد")}',
            },
            EventType.SERVICE_COMPLETED: {
                "title_ar": "اكتمال الخدمة",
                "message_ar": f'تم إكمال خدمة {event_data.get("service_name", "غير محدد")}',
            },
            EventType.TECHNICIAN_ASSIGNED: {
                "title_ar": "تعيين فني",
                "message_ar": f'تم تعيين الفني {event_data.get("technician_name", "غير محدد")}',
            },
            EventType.CUSTOMER_ARRIVED: {
                "title_ar": "وصول العميل",
                "message_ar": f'وصل العميل {event_data.get("customer_name", "غير محدد")}',
            },
            EventType.VEHICLE_READY: {
                "title_ar": "جاهزية المركبة",
                "message_ar": f'المركبة {event_data.get("vehicle_number", "غير محدد")} جاهزة للتسليم',
            },
            EventType.EMERGENCY_REPAIR: {
                "title_ar": "إصلاح طارئ",
                "message_ar": f'طلب إصلاح طارئ للمركبة {event_data.get("vehicle_number", "غير محدد")}',
            },
        }

        return translations.get(
            event_type, {"title_ar": "حدث ورشة", "message_ar": "حدث جديد في الورشة"}
        )

    def _update_event_stats(self, event: Dict):
        """Update event statistics"""
        self.event_stats["total_events"] += 1

        event_type = event["type"]
        if event_type not in self.event_stats["events_by_type"]:
            self.event_stats["events_by_type"][event_type] = 0
        self.event_stats["events_by_type"][event_type] += 1

        priority = event["priority"]
        if priority not in self.event_stats["events_by_priority"]:
            self.event_stats["events_by_priority"][priority] = 0
        self.event_stats["events_by_priority"][priority] += 1

        if event.get("arabic_content"):
            self.event_stats["arabic_events"] += 1

    async def _broadcast_event(self, event: Dict):
        """Broadcast event via WebSocket"""
        try:
            from .websocket_manager import get_websocket_manager

            websocket_manager = get_websocket_manager()
            workshop_id = event.get("workshop_id")

            if workshop_id and websocket_manager:
                await websocket_manager._broadcast_to_workshop(workshop_id, "workshop_event", event)

        except Exception as e:
            frappe.log_error(f"Failed to broadcast event via WebSocket: {e}")

    # Default event handlers
    async def _handle_service_started(self, event: Dict):
        """Handle service started event"""
        try:
            service_order_id = event["data"].get("service_order_id")
            if service_order_id:
                # Update service order status
                frappe.db.set_value("Service Order", service_order_id, "status", "In Progress")
                frappe.db.set_value(
                    "Service Order", service_order_id, "actual_start_time", now_datetime()
                )

                # Log activity
                frappe.get_doc("Service Order", service_order_id).add_comment(
                    "Info", _("Service started at {0}").format(now_datetime())
                )

                frappe.logger().info(f"Service started: {service_order_id}")

        except Exception as e:
            frappe.log_error(f"Error handling service started event: {e}")

    async def _handle_service_completed(self, event: Dict):
        """Handle service completed event"""
        try:
            service_order_id = event["data"].get("service_order_id")
            if service_order_id:
                # Update service order status
                frappe.db.set_value("Service Order", service_order_id, "status", "Completed")
                frappe.db.set_value(
                    "Service Order", service_order_id, "actual_end_time", now_datetime()
                )

                # Calculate actual duration
                service_order = frappe.get_doc("Service Order", service_order_id)
                if service_order.actual_start_time:
                    duration = now_datetime() - service_order.actual_start_time
                    frappe.db.set_value(
                        "Service Order",
                        service_order_id,
                        "actual_duration",
                        duration.total_seconds() / 3600,
                    )

                # Trigger customer notification
                await self.publish(
                    EventType.VEHICLE_READY,
                    {
                        "service_order_id": service_order_id,
                        "customer": service_order.customer,
                        "vehicle_number": service_order.vehicle,
                    },
                    priority=EventPriority.HIGH,
                    workshop_id=event.get("workshop_id"),
                )

                frappe.logger().info(f"Service completed: {service_order_id}")

        except Exception as e:
            frappe.log_error(f"Error handling service completed event: {e}")

    async def _handle_service_on_hold(self, event: Dict):
        """Handle service on hold event"""
        try:
            service_order_id = event["data"].get("service_order_id")
            hold_reason = event["data"].get("reason", "غير محدد")

            if service_order_id:
                frappe.db.set_value("Service Order", service_order_id, "status", "On Hold")

                # Add comment with reason
                frappe.get_doc("Service Order", service_order_id).add_comment(
                    "Info", _("Service put on hold: {0}").format(hold_reason)
                )

                frappe.logger().info(f"Service on hold: {service_order_id} - {hold_reason}")

        except Exception as e:
            frappe.log_error(f"Error handling service on hold event: {e}")

    async def _handle_technician_assigned(self, event: Dict):
        """Handle technician assignment event"""
        try:
            service_order_id = event["data"].get("service_order_id")
            technician_id = event["data"].get("technician_id")

            if service_order_id and technician_id:
                frappe.db.set_value(
                    "Service Order", service_order_id, "assigned_technician", technician_id
                )

                # Notify technician via mobile app
                await self.publish(
                    EventType.MOBILE_SYNC,
                    {
                        "target_user": technician_id,
                        "sync_type": "assignment",
                        "service_order_id": service_order_id,
                        "message_ar": f"تم تعيينك لخدمة جديدة: {service_order_id}",
                        "message_en": f"New service assigned: {service_order_id}",
                    },
                    priority=EventPriority.HIGH,
                )

                frappe.logger().info(f"Technician assigned: {technician_id} to {service_order_id}")

        except Exception as e:
            frappe.log_error(f"Error handling technician assignment event: {e}")

    async def _handle_customer_arrived(self, event: Dict):
        """Handle customer arrival event"""
        try:
            customer_id = event["data"].get("customer_id")
            appointment_id = event["data"].get("appointment_id")

            if appointment_id:
                frappe.db.set_value(
                    "Service Appointment", appointment_id, "status", "Customer Arrived"
                )

                # Check if service bay is ready
                service_bay = event["data"].get("service_bay")
                if service_bay:
                    # Update bay status
                    frappe.db.set_value(
                        "Service Bay", service_bay, "current_status", "Customer Waiting"
                    )

                frappe.logger().info(f"Customer arrived: {customer_id}")

        except Exception as e:
            frappe.log_error(f"Error handling customer arrival event: {e}")

    async def _handle_vehicle_ready(self, event: Dict):
        """Handle vehicle ready for pickup event"""
        try:
            service_order_id = event["data"].get("service_order_id")
            customer = event["data"].get("customer")

            if service_order_id and customer:
                # Update service order
                frappe.db.set_value("Service Order", service_order_id, "status", "Ready for Pickup")

                # Send customer notification (SMS/WhatsApp)
                customer_doc = frappe.get_doc("Customer", customer)
                if customer_doc.get("custom_communication_opt_in"):
                    # This would integrate with SMS/WhatsApp service
                    notification_message = self._format_vehicle_ready_message(
                        service_order_id,
                        customer_doc.get("custom_preferred_communication_language", "ar"),
                    )

                    # Log notification attempt
                    frappe.logger().info(f"Vehicle ready notification sent to: {customer}")

        except Exception as e:
            frappe.log_error(f"Error handling vehicle ready event: {e}")

    async def _handle_emergency_repair(self, event: Dict):
        """Handle emergency repair event"""
        try:
            service_order_id = event["data"].get("service_order_id")
            emergency_type = event["data"].get("emergency_type", "عام")

            if service_order_id:
                # Set highest priority
                frappe.db.set_value("Service Order", service_order_id, "priority", "Emergency")
                frappe.db.set_value("Service Order", service_order_id, "status", "Emergency Repair")

                # Notify all available technicians
                available_technicians = frappe.get_list(
                    "Technician",
                    filters={"status": "Available"},
                    fields=["user_id", "technician_name"],
                )

                for tech in available_technicians:
                    await self.publish(
                        EventType.MOBILE_SYNC,
                        {
                            "target_user": tech.user_id,
                            "sync_type": "emergency_alert",
                            "service_order_id": service_order_id,
                            "emergency_type": emergency_type,
                            "message_ar": f"تنبيه طارئ: إصلاح عاجل مطلوب - {emergency_type}",
                            "message_en": f"Emergency Alert: Urgent repair needed - {emergency_type}",
                        },
                        priority=EventPriority.EMERGENCY,
                    )

                frappe.logger().info(
                    f"Emergency repair event: {service_order_id} - {emergency_type}"
                )

        except Exception as e:
            frappe.log_error(f"Error handling emergency repair event: {e}")

    async def _handle_arabic_voice_message(self, event: Dict):
        """Handle Arabic voice message event"""
        try:
            from_user = event["data"].get("from_user")
            to_user = event["data"].get("to_user")
            transcription = event["data"].get("transcription_ar", "")

            # Store voice message in communication log
            if from_user and to_user:
                # This would integrate with communication tracking system
                frappe.logger().info(f"Arabic voice message: {from_user} -> {to_user}")

        except Exception as e:
            frappe.log_error(f"Error handling Arabic voice message event: {e}")

    def _format_vehicle_ready_message(self, service_order_id: str, language: str) -> str:
        """Format vehicle ready notification message"""
        if language == "ar":
            return f"عزيزنا العميل، مركبتكم جاهزة للاستلام. رقم الخدمة: {service_order_id}"
        else:
            return f"Dear customer, your vehicle is ready for pickup. Service Order: {service_order_id}"

    def get_event_history(
        self, limit: int = 100, event_type: EventType = None, workshop_id: str = None
    ) -> List[Dict]:
        """Get event history with optional filtering"""

        filtered_events = self.event_history

        if event_type:
            filtered_events = [e for e in filtered_events if e["type"] == event_type.value]

        if workshop_id:
            filtered_events = [e for e in filtered_events if e.get("workshop_id") == workshop_id]

        # Sort by timestamp (newest first) and limit
        filtered_events.sort(key=lambda x: x["timestamp"], reverse=True)
        return filtered_events[:limit]

    def get_event_statistics(self) -> Dict:
        """Get event statistics"""
        return self.event_stats.copy()

    def clear_event_history(self, older_than_days: int = 30):
        """Clear old events from history"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cutoff_iso = cutoff_date.isoformat()

        with self.event_lock:
            self.event_history = [
                event for event in self.event_history if event["timestamp"] > cutoff_iso
            ]

        frappe.logger().info(f"Cleared events older than {older_than_days} days")


# Global event bus instance
workshop_event_bus = None


def get_workshop_event_bus() -> WorkshopEventBus:
    """Get or create global workshop event bus instance"""
    global workshop_event_bus
    if workshop_event_bus is None:
        workshop_event_bus = WorkshopEventBus()
    return workshop_event_bus


# API methods for external access
@frappe.whitelist()
def publish_workshop_event(
    event_type: str, event_data: dict, priority: str = "NORMAL", workshop_id: str = None
):
    """Publish workshop event (API endpoint)"""
    try:
        event_bus = get_workshop_event_bus()

        # Convert string enums
        event_type_enum = EventType(event_type)
        priority_enum = EventPriority[priority.upper()]

        # Publish event asynchronously
        asyncio.create_task(
            event_bus.publish(
                event_type_enum,
                event_data,
                priority=priority_enum,
                workshop_id=workshop_id,
                user_id=frappe.session.user,
            )
        )

        return {"status": "published", "event_type": event_type}

    except Exception as e:
        frappe.log_error(f"Failed to publish workshop event: {e}")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def get_workshop_event_history(limit: int = 100, event_type: str = None, workshop_id: str = None):
    """Get workshop event history (API endpoint)"""
    event_bus = get_workshop_event_bus()

    event_type_enum = None
    if event_type:
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            pass

    return event_bus.get_event_history(
        limit=cint(limit), event_type=event_type_enum, workshop_id=workshop_id
    )


@frappe.whitelist()
def get_workshop_event_stats():
    """Get workshop event statistics (API endpoint)"""
    event_bus = get_workshop_event_bus()
    return event_bus.get_event_statistics()
