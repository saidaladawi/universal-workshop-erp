"""
Universal Workshop ERP - Real-time WebSocket System
Comprehensive WebSocket implementation for Phase 3 PWA enhancement

Features:
- Arabic-first real-time notifications
- Workshop floor live updates
- Mobile technician synchronization
- PWA offline/online state management
- Cultural business event handling
"""

from .websocket_manager import WebSocketManager
from .event_bus import WorkshopEventBus
from .notification_handler import ArabicNotificationHandler
from .sync_manager import PWASyncManager

__all__ = [
    'WebSocketManager',
    'WorkshopEventBus', 
    'ArabicNotificationHandler',
    'PWASyncManager'
]
