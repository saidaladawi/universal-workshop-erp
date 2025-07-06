"""
WebSocket Manager for Universal Workshop ERP
Handles real-time connections, Arabic notifications, and PWA sync

Enhanced for ERPNext v15 with:
- Arabic-first messaging system
- Workshop floor real-time updates
- Mobile technician synchronization
- Oman business hours compliance
- Cultural event handling
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cint, flt
import json
import asyncio
import socketio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import redis
from threading import Lock


class WebSocketManager:
    """
    Comprehensive WebSocket management system for Universal Workshop ERP
    Handles real-time communication with Arabic support and PWA integration
    """

    def __init__(self):
        self.sio = None
        self.redis_client = None
        self.connection_lock = Lock()
        self.active_connections: Dict[str, Dict] = {}
        self.workshop_rooms: Dict[str, List[str]] = {}
        self.technician_locations: Dict[str, Dict] = {}

        # Arabic and cultural settings
        self.arabic_enabled = True
        self.default_timezone = "Asia/Muscat"  # Oman timezone
        self.business_hours = {
            "start": "07:00",
            "end": "18:00",
            "weekend": ["friday", "saturday"],  # Oman weekend
        }

        self._initialize_socketio()
        self._initialize_redis()

    def _initialize_socketio(self):
        """Initialize Socket.IO server with Arabic support"""
        try:
            # For AsyncServer, we don't specify async_mode as it's designed for asyncio
            self.sio = socketio.AsyncServer(
                cors_allowed_origins="*", logger=True, engineio_logger=True
            )

            # Register event handlers
            self._register_event_handlers()

            # Use print for initialization logging to avoid file path issues
            print("✅ WebSocket Manager initialized successfully")

        except Exception as e:
            frappe.log_error(f"Failed to initialize Socket.IO server: {e}")
            raise

    def _initialize_redis(self):
        """Initialize Redis connection for pub/sub messaging"""
        try:
            redis_config = frappe.get_conf().get("redis_cache") or {}

            self.redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 1),
                decode_responses=True,
            )

            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection established for WebSocket")

        except Exception as e:
            frappe.log_error(f"Failed to initialize Redis for WebSocket: {e}")
            # Continue without Redis if not available
            self.redis_client = None

    def _register_event_handlers(self):
        """Register all Socket.IO event handlers"""

        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection"""
            await self._handle_client_connect(sid, environ)

        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection"""
            await self._handle_client_disconnect(sid)

        @self.sio.event
        async def join_workshop(sid, data):
            """Join workshop-specific room"""
            await self._handle_join_workshop(sid, data)

        @self.sio.event
        async def technician_location_update(sid, data):
            """Update technician location for mobile tracking"""
            await self._handle_technician_location(sid, data)

        @self.sio.event
        async def service_status_update(sid, data):
            """Handle service order status updates"""
            await self._handle_service_update(sid, data)

        @self.sio.event
        async def arabic_voice_message(sid, data):
            """Handle Arabic voice messages"""
            await self._handle_arabic_voice(sid, data)

        @self.sio.event
        async def pwa_sync_request(sid, data):
            """Handle PWA synchronization requests"""
            await self._handle_pwa_sync(sid, data)

    async def _handle_client_connect(self, sid: str, environ: dict):
        """Handle new client connection with authentication"""
        try:
            # Extract user information from headers or query params
            user_id = environ.get("HTTP_X_USER_ID")
            workshop_id = environ.get("HTTP_X_WORKSHOP_ID")
            user_role = environ.get("HTTP_X_USER_ROLE", "guest")
            language = environ.get("HTTP_X_LANGUAGE", "ar")  # Default to Arabic

            if not user_id:
                await self.sio.disconnect(sid)
                return

            # Store connection info
            with self.connection_lock:
                self.active_connections[sid] = {
                    "user_id": user_id,
                    "workshop_id": workshop_id,
                    "user_role": user_role,
                    "language": language,
                    "connected_at": now_datetime(),
                    "last_activity": now_datetime(),
                    "is_mobile": self._is_mobile_client(environ),
                    "user_agent": environ.get("HTTP_USER_AGENT", ""),
                }

            # Send welcome message in appropriate language
            welcome_message = self._get_welcome_message(language, user_role)
            await self.sio.emit("connection_established", welcome_message, room=sid)

            # Join user to appropriate rooms
            if workshop_id:
                await self.sio.enter_room(sid, f"workshop_{workshop_id}")

            await self.sio.enter_room(sid, f"user_{user_id}")

            print(f"✅ WebSocket client connected: {sid} (User: {user_id})")

        except Exception as e:
            frappe.log_error(f"Error handling client connect: {e}")
            await self.sio.disconnect(sid)

    async def _handle_client_disconnect(self, sid: str):
        """Handle client disconnection cleanup"""
        try:
            with self.connection_lock:
                connection_info = self.active_connections.pop(sid, None)

            if connection_info:
                user_id = connection_info["user_id"]
                workshop_id = connection_info.get("workshop_id")

                # Clean up technician location if mobile user
                if connection_info.get("is_mobile") and user_id in self.technician_locations:
                    del self.technician_locations[user_id]

                    # Notify workshop about technician going offline
                    if workshop_id:
                        await self._broadcast_to_workshop(
                            workshop_id,
                            "technician_offline",
                            {
                                "technician_id": user_id,
                                "timestamp": now_datetime().isoformat(),
                                "message_ar": f"الفني {user_id} غير متصل",
                                "message_en": f"Technician {user_id} went offline",
                            },
                        )

                print(f"✅ WebSocket client disconnected: {sid} (User: {user_id})")

        except Exception as e:
            frappe.log_error(f"Error handling client disconnect: {e}")

    async def _handle_join_workshop(self, sid: str, data: dict):
        """Handle joining workshop-specific room"""
        try:
            workshop_id = data.get("workshop_id")
            if not workshop_id:
                return

            connection_info = self.active_connections.get(sid)
            if not connection_info:
                return

            # Verify user has access to workshop
            if not self._verify_workshop_access(connection_info["user_id"], workshop_id):
                await self.sio.emit(
                    "access_denied",
                    {
                        "message_ar": "ليس لديك صلاحية للوصول لهذه الورشة",
                        "message_en": "You do not have access to this workshop",
                    },
                    room=sid,
                )
                return

            # Join workshop room
            await self.sio.enter_room(sid, f"workshop_{workshop_id}")

            # Update connection info
            with self.connection_lock:
                self.active_connections[sid]["workshop_id"] = workshop_id

            # Add to workshop rooms tracking
            if workshop_id not in self.workshop_rooms:
                self.workshop_rooms[workshop_id] = []
            self.workshop_rooms[workshop_id].append(sid)

            # Send workshop status update
            workshop_status = await self._get_workshop_status(workshop_id)
            await self.sio.emit("workshop_status", workshop_status, room=sid)

        except Exception as e:
            frappe.log_error(f"Error joining workshop: {e}")

    async def _handle_technician_location(self, sid: str, data: dict):
        """Handle mobile technician location updates"""
        try:
            connection_info = self.active_connections.get(sid)
            if not connection_info or not connection_info.get("is_mobile"):
                return

            user_id = connection_info["user_id"]
            workshop_id = connection_info.get("workshop_id")

            location_data = {
                "user_id": user_id,
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "accuracy": data.get("accuracy"),
                "timestamp": now_datetime(),
                "battery_level": data.get("battery_level"),
                "is_charging": data.get("is_charging", False),
                "network_type": data.get("network_type", "unknown"),
            }

            # Store location
            self.technician_locations[user_id] = location_data

            # Broadcast to workshop if user is assigned to one
            if workshop_id:
                await self._broadcast_to_workshop(
                    workshop_id,
                    "technician_location_update",
                    {
                        "technician_id": user_id,
                        "location": location_data,
                        "message_ar": f"تم تحديث موقع الفني {user_id}",
                        "message_en": f"Technician {user_id} location updated",
                    },
                )

        except Exception as e:
            frappe.log_error(f"Error handling technician location: {e}")

    async def _handle_service_update(self, sid: str, data: dict):
        """Handle service order status updates"""
        try:
            connection_info = self.active_connections.get(sid)
            if not connection_info:
                return

            service_order_id = data.get("service_order_id")
            new_status = data.get("status")
            notes = data.get("notes", "")

            if not service_order_id or not new_status:
                return

            # Update service order in database
            service_order = frappe.get_doc("Service Order", service_order_id)
            old_status = service_order.status

            service_order.status = new_status
            if notes:
                service_order.add_comment("Comment", notes)
            service_order.save()

            # Prepare broadcast message
            language = connection_info.get("language", "ar")
            update_message = self._format_service_update_message(
                service_order, old_status, new_status, language
            )

            # Broadcast to workshop
            workshop_id = connection_info.get("workshop_id")
            if workshop_id:
                await self._broadcast_to_workshop(
                    workshop_id, "service_order_updated", update_message
                )

            # Notify customer if enabled
            await self._notify_customer_service_update(service_order, update_message)

        except Exception as e:
            frappe.log_error(f"Error handling service update: {e}")

    async def _handle_arabic_voice(self, sid: str, data: dict):
        """Handle Arabic voice messages and transcription"""
        try:
            connection_info = self.active_connections.get(sid)
            if not connection_info:
                return

            audio_data = data.get("audio_data")
            target_user = data.get("target_user")
            message_type = data.get("type", "voice_note")

            if not audio_data:
                return

            # Process Arabic voice (placeholder for actual ASR integration)
            transcription = await self._process_arabic_voice(audio_data)

            voice_message = {
                "from_user": connection_info["user_id"],
                "to_user": target_user,
                "audio_data": audio_data,
                "transcription_ar": transcription.get("arabic", ""),
                "transcription_en": transcription.get("english", ""),
                "timestamp": now_datetime().isoformat(),
                "message_type": message_type,
            }

            # Send to target user
            if target_user:
                await self.sio.emit(
                    "arabic_voice_received", voice_message, room=f"user_{target_user}"
                )

        except Exception as e:
            frappe.log_error(f"Error handling Arabic voice: {e}")

    async def _handle_pwa_sync(self, sid: str, data: dict):
        """Handle PWA synchronization requests"""
        try:
            connection_info = self.active_connections.get(sid)
            if not connection_info:
                return

            sync_type = data.get("sync_type", "full")
            last_sync = data.get("last_sync")
            offline_changes = data.get("offline_changes", [])

            # Process offline changes first
            sync_results = []
            for change in offline_changes:
                try:
                    result = await self._process_offline_change(change, connection_info["user_id"])
                    sync_results.append(result)
                except Exception as e:
                    sync_results.append(
                        {"id": change.get("id"), "status": "error", "error": str(e)}
                    )

            # Get updates since last sync
            updates = await self._get_updates_since(last_sync, connection_info["user_id"])

            sync_response = {
                "sync_timestamp": now_datetime().isoformat(),
                "offline_sync_results": sync_results,
                "server_updates": updates,
                "sync_type": sync_type,
                "status": "completed",
            }

            await self.sio.emit("pwa_sync_response", sync_response, room=sid)

        except Exception as e:
            frappe.log_error(f"Error handling PWA sync: {e}")

    # Utility methods
    def _is_mobile_client(self, environ: dict) -> bool:
        """Check if client is mobile device"""
        user_agent = environ.get("HTTP_USER_AGENT", "").lower()
        mobile_indicators = ["mobile", "android", "iphone", "ipad", "tablet"]
        return any(indicator in user_agent for indicator in mobile_indicators)

    def _get_welcome_message(self, language: str, user_role: str) -> dict:
        """Get welcome message in appropriate language"""
        if language == "ar":
            return {
                "message": f"مرحباً بك في ورشة العمل - {user_role}",
                "timestamp": now_datetime().isoformat(),
                "language": "ar",
            }
        else:
            return {
                "message": f"Welcome to Universal Workshop - {user_role}",
                "timestamp": now_datetime().isoformat(),
                "language": "en",
            }

    def _verify_workshop_access(self, user_id: str, workshop_id: str) -> bool:
        """Verify user has access to specific workshop"""
        try:
            # Check if user is assigned to workshop or has admin role
            user_roles = frappe.get_roles(user_id)

            if "System Manager" in user_roles or "Workshop Manager" in user_roles:
                return True

            # Check if technician is assigned to workshop
            technician = frappe.db.get_value(
                "Technician", {"user_id": user_id, "workshop": workshop_id}, "name"
            )

            return bool(technician)

        except Exception:
            return False

    async def _get_workshop_status(self, workshop_id: str) -> dict:
        """Get current workshop status"""
        try:
            # Get active service orders
            active_orders = frappe.get_list(
                "Service Order",
                filters={
                    "workshop": workshop_id,
                    "status": ["in", ["Draft", "In Progress", "On Hold"]],
                },
                fields=["name", "customer", "vehicle", "status", "estimated_completion"],
            )

            # Get active technicians
            active_technicians = []
            for sid, conn in self.active_connections.items():
                if (
                    conn.get("workshop_id") == workshop_id
                    and conn.get("is_mobile")
                    and conn["user_id"] in self.technician_locations
                ):

                    active_technicians.append(
                        {
                            "user_id": conn["user_id"],
                            "location": self.technician_locations[conn["user_id"]],
                            "last_activity": conn["last_activity"].isoformat(),
                        }
                    )

            return {
                "workshop_id": workshop_id,
                "active_orders": active_orders,
                "active_technicians": active_technicians,
                "timestamp": now_datetime().isoformat(),
            }

        except Exception as e:
            frappe.log_error(f"Error getting workshop status: {e}")
            return {"error": str(e)}

    def _format_service_update_message(
        self, service_order, old_status: str, new_status: str, language: str
    ) -> dict:
        """Format service update message for broadcasting"""

        if language == "ar":
            message = f"تم تحديث حالة الخدمة {service_order.name} من {old_status} إلى {new_status}"
        else:
            message = f"Service order {service_order.name} status updated from {old_status} to {new_status}"

        return {
            "service_order_id": service_order.name,
            "customer": service_order.customer,
            "vehicle": service_order.vehicle,
            "old_status": old_status,
            "new_status": new_status,
            "message": message,
            "timestamp": now_datetime().isoformat(),
            "language": language,
        }

    async def _broadcast_to_workshop(self, workshop_id: str, event: str, data: dict):
        """Broadcast message to all clients in workshop room"""
        try:
            await self.sio.emit(event, data, room=f"workshop_{workshop_id}")

            # Also publish to Redis for multi-server setup
            if self.redis_client:
                redis_message = {
                    "event": event,
                    "data": data,
                    "workshop_id": workshop_id,
                    "timestamp": now_datetime().isoformat(),
                }
                self.redis_client.publish(f"workshop_{workshop_id}", json.dumps(redis_message))

        except Exception as e:
            frappe.log_error(f"Error broadcasting to workshop: {e}")

    async def _notify_customer_service_update(self, service_order, update_message: dict):
        """Send notification to customer about service update"""
        try:
            customer = frappe.get_doc("Customer", service_order.customer)

            # Check if customer has opted in for notifications
            if not customer.get("custom_communication_opt_in"):
                return

            # Get customer's preferred language
            customer_language = customer.get("custom_preferred_communication_language", "ar")

            # Format message for customer
            if customer_language == "ar":
                customer_message = (
                    f'عزيزنا العميل، تم تحديث حالة خدمة مركبتكم إلى: {update_message["new_status"]}'
                )
            else:
                customer_message = f'Dear customer, your vehicle service status has been updated to: {update_message["new_status"]}'

            # Send via configured communication channels
            # This would integrate with SMS/WhatsApp/Email systems

        except Exception as e:
            frappe.log_error(f"Error notifying customer: {e}")

    async def _process_arabic_voice(self, audio_data: str) -> dict:
        """Process Arabic voice data and return transcription"""
        # Placeholder for Arabic ASR integration
        # This would integrate with services like Google Speech-to-Text Arabic
        # or Azure Cognitive Services for Arabic

        return {
            "arabic": "نص مُحول من الصوت العربي",
            "english": "Transcribed Arabic voice text",
            "confidence": 0.85,
        }

    async def _process_offline_change(self, change: dict, user_id: str) -> dict:
        """Process a single offline change"""
        try:
            change_type = change.get("type")
            doctype = change.get("doctype")
            doc_data = change.get("data")

            if change_type == "create":
                doc = frappe.new_doc(doctype)
                doc.update(doc_data)
                doc.insert()
                return {"id": change.get("id"), "status": "created", "server_id": doc.name}

            elif change_type == "update":
                doc = frappe.get_doc(doctype, doc_data.get("name"))
                doc.update(doc_data)
                doc.save()
                return {"id": change.get("id"), "status": "updated"}

            elif change_type == "delete":
                frappe.delete_doc(doctype, doc_data.get("name"))
                return {"id": change.get("id"), "status": "deleted"}

        except Exception as e:
            return {"id": change.get("id"), "status": "error", "error": str(e)}

    async def _get_updates_since(self, last_sync: str, user_id: str) -> list:
        """Get all updates since last sync timestamp for user"""
        try:
            if not last_sync:
                # First sync - get recent data
                last_sync = (datetime.now() - timedelta(days=7)).isoformat()

            # Get updated documents since last sync
            # This would be customized based on what data each user type needs
            updates = []

            # Example: Get service orders for technicians
            if frappe.db.exists("Technician", {"user_id": user_id}):
                service_orders = frappe.get_list(
                    "Service Order",
                    filters={"modified": [">", last_sync], "assigned_technician": user_id},
                    fields=["*"],
                )

                for order in service_orders:
                    updates.append({"doctype": "Service Order", "action": "update", "data": order})

            return updates

        except Exception as e:
            frappe.log_error(f"Error getting updates since last sync: {e}")
            return []


# Global WebSocket manager instance
websocket_manager = None


def get_websocket_manager() -> WebSocketManager:
    """Get or create global WebSocket manager instance"""
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager()
    return websocket_manager


# API methods for external access
@frappe.whitelist()
def broadcast_workshop_message(workshop_id: str, event: str, message: dict):
    """Broadcast message to workshop room (API endpoint)"""
    manager = get_websocket_manager()
    asyncio.create_task(manager._broadcast_to_workshop(workshop_id, event, message))
    return {"status": "broadcasted"}


@frappe.whitelist()
def get_active_connections(workshop_id: str = None):
    """Get list of active WebSocket connections"""
    manager = get_websocket_manager()

    if workshop_id:
        # Filter connections for specific workshop
        workshop_connections = []
        for sid, conn in manager.active_connections.items():
            if conn.get("workshop_id") == workshop_id:
                workshop_connections.append(
                    {
                        "user_id": conn["user_id"],
                        "user_role": conn["user_role"],
                        "language": conn["language"],
                        "is_mobile": conn["is_mobile"],
                        "connected_at": conn["connected_at"].isoformat(),
                        "last_activity": conn["last_activity"].isoformat(),
                    }
                )
        return workshop_connections
    else:
        # Return all connections summary
        return {
            "total_connections": len(manager.active_connections),
            "workshop_rooms": len(manager.workshop_rooms),
            "active_technicians": len(manager.technician_locations),
        }


@frappe.whitelist()
def get_technician_locations(workshop_id: str):
    """Get current locations of all technicians in workshop"""
    manager = get_websocket_manager()

    workshop_technicians = []
    for user_id, location_data in manager.technician_locations.items():
        # Check if technician belongs to workshop
        if frappe.db.exists("Technician", {"user_id": user_id, "workshop": workshop_id}):
            workshop_technicians.append(location_data)

    return workshop_technicians
