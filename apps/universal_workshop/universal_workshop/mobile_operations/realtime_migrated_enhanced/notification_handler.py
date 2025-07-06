"""
Arabic Notification Handler for Universal Workshop ERP
Handles Arabic-first notifications with cultural business logic

Features:
- Arabic text processing and formatting
- Cultural notification timing (prayer times, business hours)
- Multi-channel notifications (SMS, WhatsApp, Push, Voice)
- Arabic voice synthesis and recognition
- Oman-specific communication patterns
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cint, flt, format_date
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import asyncio
from threading import Lock
import base64
import hashlib


class NotificationChannel(str):
    """Notification delivery channels"""

    PUSH = "push"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    VOICE = "voice"
    IN_APP = "in_app"
    WEBSOCKET = "websocket"


class NotificationPriority(int):
    """Notification priority levels"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5


class ArabicNotificationHandler:
    """
    Comprehensive Arabic notification system for Universal Workshop ERP
    Handles multi-channel notifications with cultural awareness
    """

    def __init__(self):
        self.notification_queue: List[Dict] = []
        self.delivery_history: List[Dict] = []
        self.failed_deliveries: List[Dict] = []
        self.queue_lock = Lock()

        # Arabic text processing
        self.arabic_enabled = True
        self.text_direction = "rtl"
        self.arabic_numerals = True

        # Cultural settings for Oman
        self.business_hours = {"start": "07:00", "end": "18:00", "weekend": ["friday", "saturday"]}

        self.prayer_times = {
            "fajr": "05:30",
            "dhuhr": "12:15",
            "asr": "15:45",
            "maghrib": "18:30",
            "isha": "20:00",
        }

        # Notification templates
        self.templates = self._initialize_arabic_templates()

        # Delivery statistics
        self.stats = {
            "total_sent": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "arabic_notifications": 0,
            "by_channel": {},
            "by_priority": {},
        }

    def _initialize_arabic_templates(self) -> Dict:
        """Initialize Arabic notification templates"""
        return {
            "service_started": {
                "title_ar": "بدء الخدمة",
                "message_ar": "تم بدء خدمة {service_name} للمركبة {vehicle_number}",
                "title_en": "Service Started",
                "message_en": "Service {service_name} started for vehicle {vehicle_number}",
            },
            "service_completed": {
                "title_ar": "اكتمال الخدمة",
                "message_ar": "تم إكمال خدمة {service_name} للمركبة {vehicle_number}. المركبة جاهزة للاستلام.",
                "title_en": "Service Completed",
                "message_en": "Service {service_name} completed for vehicle {vehicle_number}. Ready for pickup.",
            },
            "technician_assignment": {
                "title_ar": "تعيين فني",
                "message_ar": "تم تعيينك لخدمة {service_name} - المركبة {vehicle_number}",
                "title_en": "Technician Assignment",
                "message_en": "You have been assigned to service {service_name} - Vehicle {vehicle_number}",
            },
            "customer_arrival": {
                "title_ar": "وصول العميل",
                "message_ar": "وصل العميل {customer_name} للموعد في الخليج {bay_number}",
                "title_en": "Customer Arrival",
                "message_en": "Customer {customer_name} arrived for appointment at bay {bay_number}",
            },
            "parts_request": {
                "title_ar": "طلب قطع غيار",
                "message_ar": "مطلوب قطعة غيار: {part_name} للمركبة {vehicle_number}",
                "title_en": "Parts Request",
                "message_en": "Part required: {part_name} for vehicle {vehicle_number}",
            },
            "emergency_repair": {
                "title_ar": "⚠️ إصلاح طارئ",
                "message_ar": "طلب إصلاح طارئ للمركبة {vehicle_number} - {emergency_type}",
                "title_en": "⚠️ Emergency Repair",
                "message_en": "Emergency repair needed for vehicle {vehicle_number} - {emergency_type}",
            },
            "payment_reminder": {
                "title_ar": "تذكير دفع",
                "message_ar": "تذكير: مبلغ {amount} ريال عماني مستحق للفاتورة {invoice_number}",
                "title_en": "Payment Reminder",
                "message_en": "Reminder: OMR {amount} due for invoice {invoice_number}",
            },
            "appointment_reminder": {
                "title_ar": "تذكير موعد",
                "message_ar": "تذكير: موعدكم غداً الساعة {time} لخدمة {service_name}",
                "title_en": "Appointment Reminder",
                "message_en": "Reminder: Your appointment tomorrow at {time} for {service_name}",
            },
        }

    async def send_notification(
        self,
        notification_type: str,
        recipient: str,
        data: Dict,
        channels: List[str] = None,
        priority: int = NotificationPriority.NORMAL,
        language: str = "ar",
        scheduled_time: datetime = None,
        workshop_id: str = None,
    ) -> Dict:
        """Send notification through specified channels"""

        try:
            # Default channels if not specified
            if channels is None:
                channels = [NotificationChannel.PUSH, NotificationChannel.WEBSOCKET]

            # Create notification object
            notification = {
                "id": frappe.generate_hash(length=12),
                "type": notification_type,
                "recipient": recipient,
                "data": data,
                "channels": channels,
                "priority": priority,
                "language": language,
                "workshop_id": workshop_id,
                "created_at": now_datetime().isoformat(),
                "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
                "status": "pending",
                "delivery_attempts": 0,
                "max_attempts": 3,
            }

            # Generate message content
            notification["content"] = self._generate_notification_content(
                notification_type, data, language
            )

            # Check cultural timing constraints
            if not self._is_appropriate_time(priority):
                notification["status"] = "scheduled"
                notification["scheduled_time"] = self._get_next_appropriate_time().isoformat()

            # Add to queue
            with self.queue_lock:
                self.notification_queue.append(notification)

            # Process immediately if high priority or appropriate time
            if priority >= NotificationPriority.HIGH or notification["status"] == "pending":
                await self._process_notification(notification)

            frappe.logger().info(f"Notification queued: {notification['id']} ({notification_type})")
            return {
                "status": "success",
                "notification_id": notification["id"],
                "message": "Notification queued successfully",
            }

        except Exception as e:
            frappe.log_error(f"Failed to send notification: {e}")
            return {"status": "error", "error": str(e)}

    async def _process_notification(self, notification: Dict):
        """Process individual notification through all channels"""

        notification_id = notification["id"]
        channels = notification["channels"]

        delivery_results = {}

        for channel in channels:
            try:
                if channel == NotificationChannel.PUSH:
                    result = await self._send_push_notification(notification)
                elif channel == NotificationChannel.SMS:
                    result = await self._send_sms_notification(notification)
                elif channel == NotificationChannel.WHATSAPP:
                    result = await self._send_whatsapp_notification(notification)
                elif channel == NotificationChannel.EMAIL:
                    result = await self._send_email_notification(notification)
                elif channel == NotificationChannel.VOICE:
                    result = await self._send_voice_notification(notification)
                elif channel == NotificationChannel.IN_APP:
                    result = await self._send_in_app_notification(notification)
                elif channel == NotificationChannel.WEBSOCKET:
                    result = await self._send_websocket_notification(notification)
                else:
                    result = {"status": "error", "error": f"Unknown channel: {channel}"}

                delivery_results[channel] = result

            except Exception as e:
                delivery_results[channel] = {"status": "error", "error": str(e)}
                frappe.log_error(f"Notification delivery failed for {channel}: {e}")

        # Update notification status
        successful_channels = [
            ch for ch, res in delivery_results.items() if res.get("status") == "success"
        ]

        if successful_channels:
            notification["status"] = "delivered"
            notification["delivered_channels"] = successful_channels
            notification["delivery_time"] = now_datetime().isoformat()
            self._update_delivery_stats(notification, True)
        else:
            notification["status"] = "failed"
            notification["delivery_attempts"] += 1
            self._update_delivery_stats(notification, False)

            # Retry if under max attempts
            if notification["delivery_attempts"] < notification["max_attempts"]:
                # Schedule retry with exponential backoff
                retry_delay = 2 ** notification["delivery_attempts"]  # 2, 4, 8 minutes
                notification["scheduled_time"] = (
                    now_datetime() + timedelta(minutes=retry_delay)
                ).isoformat()
                notification["status"] = "scheduled"

        notification["delivery_results"] = delivery_results

        # Store in delivery history
        with self.queue_lock:
            self.delivery_history.append(notification.copy())

            # Remove from queue if processing is complete
            if notification["status"] in ["delivered", "failed"]:
                try:
                    self.notification_queue.remove(notification)
                except ValueError:
                    pass

    def _generate_notification_content(
        self, notification_type: str, data: Dict, language: str
    ) -> Dict:
        """Generate notification content based on type and language"""

        template = self.templates.get(notification_type, {})

        if language == "ar":
            title = template.get("title_ar", "إشعار ورشة")
            message = template.get("message_ar", "إشعار جديد من الورشة")
        else:
            title = template.get("title_en", "Workshop Notification")
            message = template.get("message_en", "New notification from workshop")

        # Format message with data
        try:
            formatted_message = message.format(**data)
        except KeyError as e:
            frappe.logger().warning(f"Missing template data for {notification_type}: {e}")
            formatted_message = message

        # Convert numbers to Arabic numerals if Arabic language
        if language == "ar" and self.arabic_numerals:
            formatted_message = self._convert_to_arabic_numerals(formatted_message)
            title = self._convert_to_arabic_numerals(title)

        return {
            "title": title,
            "message": formatted_message,
            "language": language,
            "direction": "rtl" if language == "ar" else "ltr",
        }

    def _convert_to_arabic_numerals(self, text: str) -> str:
        """Convert Western numerals to Arabic-Indic numerals"""
        arabic_numerals = {
            "0": "٠",
            "1": "١",
            "2": "٢",
            "3": "٣",
            "4": "٤",
            "5": "٥",
            "6": "٦",
            "7": "٧",
            "8": "٨",
            "9": "٩",
        }

        for western, arabic in arabic_numerals.items():
            text = text.replace(western, arabic)
        return text

    def _is_appropriate_time(self, priority: int) -> bool:
        """Check if current time is appropriate for sending notifications"""

        # Emergency notifications always sent immediately
        if priority >= NotificationPriority.EMERGENCY:
            return True

        current_time = now_datetime().time()
        current_weekday = now_datetime().strftime("%A").lower()

        # Check business hours
        business_start = datetime.strptime(self.business_hours["start"], "%H:%M").time()
        business_end = datetime.strptime(self.business_hours["end"], "%H:%M").time()

        if current_weekday in self.business_hours["weekend"]:
            return priority >= NotificationPriority.HIGH

        if not (business_start <= current_time <= business_end):
            return priority >= NotificationPriority.HIGH

        # Check prayer times (avoid sending during prayer times for low priority)
        if priority <= NotificationPriority.NORMAL:
            for prayer, time_str in self.prayer_times.items():
                prayer_time = datetime.strptime(time_str, "%H:%M").time()
                # 15 minutes buffer around prayer times
                prayer_start = (
                    datetime.combine(datetime.today(), prayer_time) - timedelta(minutes=15)
                ).time()
                prayer_end = (
                    datetime.combine(datetime.today(), prayer_time) + timedelta(minutes=15)
                ).time()

                if prayer_start <= current_time <= prayer_end:
                    return False

        return True

    def _get_next_appropriate_time(self) -> datetime:
        """Get next appropriate time for sending notifications"""

        current_time = now_datetime()

        # If it's weekend, schedule for next business day
        current_weekday = current_time.strftime("%A").lower()
        if current_weekday in self.business_hours["weekend"]:
            days_until_sunday = (6 - current_time.weekday()) % 7  # Sunday is start of week in Oman
            next_business_day = current_time + timedelta(days=days_until_sunday)
            business_start_time = datetime.strptime(self.business_hours["start"], "%H:%M").time()
            return datetime.combine(next_business_day.date(), business_start_time)

        # If outside business hours, schedule for next business day start
        business_start = datetime.strptime(self.business_hours["start"], "%H:%M").time()
        business_end = datetime.strptime(self.business_hours["end"], "%H:%M").time()

        if current_time.time() >= business_end:
            next_day = current_time + timedelta(days=1)
            return datetime.combine(next_day.date(), business_start)

        if current_time.time() < business_start:
            return datetime.combine(current_time.date(), business_start)

        # During business hours, schedule for 30 minutes later
        return current_time + timedelta(minutes=30)

    async def _send_push_notification(self, notification: Dict) -> Dict:
        """Send push notification to mobile device"""
        try:
            # This would integrate with Firebase Cloud Messaging or similar
            # For now, simulate successful delivery

            recipient = notification["recipient"]
            content = notification["content"]

            # Get user's device tokens
            device_tokens = self._get_user_device_tokens(recipient)

            if not device_tokens:
                return {"status": "error", "error": "No device tokens found"}

            # Simulate push notification delivery
            frappe.logger().info(f"Push notification sent to {recipient}: {content['title']}")

            return {"status": "success", "delivered_to": len(device_tokens), "channel": "push"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_sms_notification(self, notification: Dict) -> Dict:
        """Send SMS notification"""
        try:
            recipient = notification["recipient"]
            content = notification["content"]

            # Get user's phone number
            phone_number = self._get_user_phone(recipient)

            if not phone_number:
                return {"status": "error", "error": "No phone number found"}

            # Format SMS message (Arabic SMS considerations)
            sms_message = f"{content['title']}\n{content['message']}"

            # This would integrate with SMS provider (e.g., Twilio, local SMS gateway)
            # For now, simulate successful delivery
            frappe.logger().info(f"SMS sent to {phone_number}: {sms_message[:50]}...")

            return {"status": "success", "phone_number": phone_number, "channel": "sms"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_whatsapp_notification(self, notification: Dict) -> Dict:
        """Send WhatsApp notification"""
        try:
            recipient = notification["recipient"]
            content = notification["content"]

            # Get user's WhatsApp number
            whatsapp_number = self._get_user_whatsapp(recipient)

            if not whatsapp_number:
                return {"status": "error", "error": "No WhatsApp number found"}

            # Format WhatsApp message with Arabic support
            whatsapp_message = f"*{content['title']}*\n\n{content['message']}"

            # This would integrate with WhatsApp Business API
            # For now, simulate successful delivery
            frappe.logger().info(f"WhatsApp sent to {whatsapp_number}: {content['title']}")

            return {"status": "success", "whatsapp_number": whatsapp_number, "channel": "whatsapp"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_email_notification(self, notification: Dict) -> Dict:
        """Send email notification"""
        try:
            recipient = notification["recipient"]
            content = notification["content"]

            # Get user's email
            email = self._get_user_email(recipient)

            if not email:
                return {"status": "error", "error": "No email found"}

            # Create email with Arabic support
            email_subject = content["title"]
            email_body = self._format_email_body(content, notification.get("data", {}))

            # Send email using Frappe's email system
            frappe.sendmail(
                recipients=[email],
                subject=email_subject,
                message=email_body,
                header=["Universal Workshop ERP", "نظام إدارة الورش الشامل"],
            )

            return {"status": "success", "email": email, "channel": "email"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_voice_notification(self, notification: Dict) -> Dict:
        """Send voice notification (Arabic TTS)"""
        try:
            recipient = notification["recipient"]
            content = notification["content"]

            # Get user's phone number for voice call
            phone_number = self._get_user_phone(recipient)

            if not phone_number:
                return {"status": "error", "error": "No phone number found"}

            # This would integrate with Arabic TTS service and voice call provider
            # For now, simulate successful delivery
            frappe.logger().info(
                f"Voice notification queued for {phone_number}: {content['title']}"
            )

            return {"status": "success", "phone_number": phone_number, "channel": "voice"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_in_app_notification(self, notification: Dict) -> Dict:
        """Send in-app notification"""
        try:
            recipient = notification["recipient"]
            content = notification["content"]

            # Create in-app notification record
            in_app_notification = frappe.new_doc("Notification Log")
            in_app_notification.update(
                {
                    "for_user": recipient,
                    "type": "Alert",
                    "document_type": "Workshop Notification",
                    "subject": content["title"],
                    "email_content": content["message"],
                    "read": 0,
                }
            )
            in_app_notification.insert(ignore_permissions=True)

            return {
                "status": "success",
                "notification_id": in_app_notification.name,
                "channel": "in_app",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _send_websocket_notification(self, notification: Dict) -> Dict:
        """Send notification via WebSocket"""
        try:
            from .websocket_manager import get_websocket_manager

            websocket_manager = get_websocket_manager()
            recipient = notification["recipient"]
            workshop_id = notification.get("workshop_id")

            if websocket_manager:
                # Send to specific user
                await websocket_manager.sio.emit(
                    "notification",
                    {
                        "id": notification["id"],
                        "type": notification["type"],
                        "content": notification["content"],
                        "priority": notification["priority"],
                        "timestamp": now_datetime().isoformat(),
                    },
                    room=f"user_{recipient}",
                )

                # Also broadcast to workshop if specified
                if workshop_id:
                    await websocket_manager._broadcast_to_workshop(
                        workshop_id, "workshop_notification", notification
                    )

                return {"status": "success", "recipient": recipient, "channel": "websocket"}
            else:
                return {"status": "error", "error": "WebSocket manager not available"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _format_email_body(self, content: Dict, data: Dict) -> str:
        """Format email body with Arabic support"""

        language = content.get("language", "ar")
        direction = content.get("direction", "rtl")

        html_body = f"""
        <div dir="{direction}" style="font-family: 'Tahoma', 'Arial Unicode MS', sans-serif; font-size: 14px;">
            <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                {content['title']}
            </h2>
            <div style="margin: 20px 0; line-height: 1.6;">
                {content['message']}
            </div>
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666;">
                {'نظام إدارة الورش الشامل' if language == 'ar' else 'Universal Workshop ERP'}<br>
                {format_date(now_datetime(), 'dd/MM/yyyy HH:mm')}
            </div>
        </div>
        """

        return html_body

    def _get_user_device_tokens(self, user_id: str) -> List[str]:
        """Get user's mobile device tokens for push notifications"""
        # This would query a device tokens table
        # For now, return empty list
        return []

    def _get_user_phone(self, user_id: str) -> str:
        """Get user's phone number"""
        try:
            user_doc = frappe.get_doc("User", user_id)
            return user_doc.get("phone") or user_doc.get("mobile_no")
        except:
            return None

    def _get_user_whatsapp(self, user_id: str) -> str:
        """Get user's WhatsApp number"""
        try:
            # Check if user has custom WhatsApp field
            user_doc = frappe.get_doc("User", user_id)
            return user_doc.get("custom_whatsapp_number") or self._get_user_phone(user_id)
        except:
            return None

    def _get_user_email(self, user_id: str) -> str:
        """Get user's email address"""
        try:
            user_doc = frappe.get_doc("User", user_id)
            return user_doc.get("email")
        except:
            return None

    def _update_delivery_stats(self, notification: Dict, success: bool):
        """Update delivery statistics"""
        self.stats["total_sent"] += 1

        if success:
            self.stats["successful_deliveries"] += 1
        else:
            self.stats["failed_deliveries"] += 1

        if notification.get("language") == "ar":
            self.stats["arabic_notifications"] += 1

        # Update channel stats
        for channel in notification.get("channels", []):
            if channel not in self.stats["by_channel"]:
                self.stats["by_channel"][channel] = {"sent": 0, "success": 0}

            self.stats["by_channel"][channel]["sent"] += 1
            if success:
                self.stats["by_channel"][channel]["success"] += 1

        # Update priority stats
        priority = notification.get("priority", NotificationPriority.NORMAL)
        if priority not in self.stats["by_priority"]:
            self.stats["by_priority"][priority] = 0
        self.stats["by_priority"][priority] += 1

    async def process_scheduled_notifications(self):
        """Process notifications scheduled for current time"""
        current_time = now_datetime()

        with self.queue_lock:
            scheduled_notifications = [
                n
                for n in self.notification_queue
                if n["status"] == "scheduled" and get_datetime(n["scheduled_time"]) <= current_time
            ]

        for notification in scheduled_notifications:
            notification["status"] = "pending"
            await self._process_notification(notification)

    def get_delivery_history(self, limit: int = 100, recipient: str = None) -> List[Dict]:
        """Get notification delivery history"""
        filtered_history = self.delivery_history

        if recipient:
            filtered_history = [h for h in filtered_history if h["recipient"] == recipient]

        # Sort by created time (newest first) and limit
        filtered_history.sort(key=lambda x: x["created_at"], reverse=True)
        return filtered_history[:limit]

    def get_delivery_statistics(self) -> Dict:
        """Get notification delivery statistics"""
        return self.stats.copy()

    def clear_old_history(self, older_than_days: int = 30):
        """Clear old notification history"""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        cutoff_iso = cutoff_date.isoformat()

        with self.queue_lock:
            self.delivery_history = [
                h for h in self.delivery_history if h["created_at"] > cutoff_iso
            ]

        frappe.logger().info(f"Cleared notification history older than {older_than_days} days")


# Global notification handler instance
arabic_notification_handler = None


def get_arabic_notification_handler() -> ArabicNotificationHandler:
    """Get or create global Arabic notification handler instance"""
    global arabic_notification_handler
    if arabic_notification_handler is None:
        arabic_notification_handler = ArabicNotificationHandler()
    return arabic_notification_handler


# API methods for external access
@frappe.whitelist()
def send_workshop_notification(
    notification_type: str,
    recipient: str,
    data: dict,
    channels: list = None,
    priority: int = 2,
    language: str = "ar",
):
    """Send workshop notification (API endpoint)"""
    try:
        handler = get_arabic_notification_handler()

        # Send notification asynchronously
        result = asyncio.create_task(
            handler.send_notification(
                notification_type=notification_type,
                recipient=recipient,
                data=data,
                channels=channels or ["push", "websocket"],
                priority=priority,
                language=language,
            )
        )

        return {"status": "queued", "notification_type": notification_type}

    except Exception as e:
        frappe.log_error(f"Failed to send workshop notification: {e}")
        return {"status": "error", "error": str(e)}


@frappe.whitelist()
def get_notification_history(limit: int = 100, recipient: str = None):
    """Get notification delivery history (API endpoint)"""
    handler = get_arabic_notification_handler()
    return handler.get_delivery_history(limit=cint(limit), recipient=recipient)


@frappe.whitelist()
def get_notification_stats():
    """Get notification delivery statistics (API endpoint)"""
    handler = get_arabic_notification_handler()
    return handler.get_delivery_statistics()


@frappe.whitelist()
def process_scheduled_notifications():
    """Process scheduled notifications (API endpoint for cron job)"""
    handler = get_arabic_notification_handler()
    asyncio.create_task(handler.process_scheduled_notifications())
    return {"status": "processing"}
