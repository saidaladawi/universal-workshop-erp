"""
Configuration file for Universal Workshop Real-time System
Contains settings for WebSocket, notifications, and sync management
"""

import frappe
from frappe import get_site_config

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    "host": "0.0.0.0",
    "port": 9000,
    "cors_allowed_origins": "*",
    "logger": True,
    "engineio_logger": True,
    "ping_timeout": 60,
    "ping_interval": 25,
    "max_http_buffer_size": 1000000,  # 1MB
}

# Arabic and Cultural Settings
CULTURAL_CONFIG = {
    "default_language": "ar",
    "timezone": "Asia/Muscat",
    "business_hours": {"start": "07:00", "end": "18:00", "weekend": ["friday", "saturday"]},
    "prayer_times": {
        "fajr": "05:30",
        "dhuhr": "12:15",
        "asr": "15:45",
        "maghrib": "18:30",
        "isha": "20:00",
    },
    "arabic_numerals": True,
    "rtl_direction": True,
}

# Notification Configuration
NOTIFICATION_CONFIG = {
    "default_channels": ["push", "websocket"],
    "high_priority_channels": ["push", "websocket", "sms"],
    "emergency_channels": ["push", "websocket", "sms", "voice"],
    "max_retries": 3,
    "retry_delay": 60,  # seconds
    "batch_size": 50,
    "queue_timeout": 3600,  # 1 hour
}

# PWA Sync Configuration
SYNC_CONFIG = {
    "batch_size": 50,
    "max_retries": 3,
    "retry_delay": 60,  # seconds
    "conflict_timeout": 3600,  # 1 hour
    "offline_retention_days": 30,
    "sync_interval": 300,  # 5 minutes
    "priority_doctypes": {
        "Service Order": 5,  # Critical
        "Customer": 4,  # High
        "Vehicle": 4,  # High
        "Technician": 4,  # High
        "Item": 2,  # Normal
        "Stock Entry": 4,  # High
        "Service Appointment": 5,  # Critical
        "Workshop Profile": 2,  # Normal
    },
}

# Event Bus Configuration
EVENT_CONFIG = {
    "max_history_size": 1000,
    "cleanup_interval": 86400,  # 24 hours
    "event_timeout": 3600,  # 1 hour
    "priority_levels": {"LOW": 1, "NORMAL": 2, "HIGH": 3, "URGENT": 4, "EMERGENCY": 5},
}


# Redis Configuration
def get_redis_config():
    """Get Redis configuration from site config"""
    site_config = get_site_config()
    return {
        "host": site_config.get("redis_cache", {}).get("host", "localhost"),
        "port": site_config.get("redis_cache", {}).get("port", 6379),
        "db": site_config.get("redis_cache", {}).get("db", 1),
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }


# Workshop-specific Configuration
WORKSHOP_CONFIG = {
    "default_workshop_id": "main_workshop",
    "max_concurrent_services": 10,
    "service_bay_count": 8,
    "technician_capacity": {
        "junior": 2,  # 2 concurrent services
        "senior": 3,  # 3 concurrent services
        "expert": 4,  # 4 concurrent services
    },
    "emergency_response_time": 15,  # minutes
    "customer_wait_threshold": 30,  # minutes
}

# Security Configuration
SECURITY_CONFIG = {
    "enable_rate_limiting": True,
    "rate_limit_per_minute": 60,
    "enable_authentication": True,
    "session_timeout": 3600,  # 1 hour
    "max_connections_per_user": 5,
    "enable_encryption": True,
    "allowed_origins": ["*"],  # Configure for production
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "enable_file_logging": True,
    "log_file_path": "logs/realtime.log",
    "max_log_file_size": 10485760,  # 10MB
    "backup_count": 5,
    "enable_console_logging": True,
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "enable_caching": True,
    "cache_ttl": 300,  # 5 minutes
    "max_cache_size": 1000,
    "enable_compression": True,
    "compression_threshold": 1024,  # 1KB
    "max_message_size": 1048576,  # 1MB
    "connection_pool_size": 100,
}


def get_config(config_type: str):
    """Get configuration by type"""
    configs = {
        "websocket": WEBSOCKET_CONFIG,
        "cultural": CULTURAL_CONFIG,
        "notification": NOTIFICATION_CONFIG,
        "sync": SYNC_CONFIG,
        "event": EVENT_CONFIG,
        "redis": get_redis_config(),
        "workshop": WORKSHOP_CONFIG,
        "security": SECURITY_CONFIG,
        "logging": LOGGING_CONFIG,
        "performance": PERFORMANCE_CONFIG,
    }

    return configs.get(config_type, {})


def update_config(config_type: str, updates: dict):
    """Update configuration dynamically"""
    try:
        if config_type == "websocket":
            WEBSOCKET_CONFIG.update(updates)
        elif config_type == "cultural":
            CULTURAL_CONFIG.update(updates)
        elif config_type == "notification":
            NOTIFICATION_CONFIG.update(updates)
        elif config_type == "sync":
            SYNC_CONFIG.update(updates)
        elif config_type == "event":
            EVENT_CONFIG.update(updates)
        elif config_type == "workshop":
            WORKSHOP_CONFIG.update(updates)
        elif config_type == "security":
            SECURITY_CONFIG.update(updates)
        elif config_type == "logging":
            LOGGING_CONFIG.update(updates)
        elif config_type == "performance":
            PERFORMANCE_CONFIG.update(updates)

        frappe.logger().info(f"Configuration updated: {config_type}")
        return True

    except Exception as e:
        frappe.log_error(f"Failed to update configuration {config_type}: {e}")
        return False


def validate_config():
    """Validate all configurations"""
    errors = []

    # Validate WebSocket config
    if WEBSOCKET_CONFIG["port"] < 1024 or WEBSOCKET_CONFIG["port"] > 65535:
        errors.append("WebSocket port must be between 1024 and 65535")

    # Validate business hours
    try:
        from datetime import datetime

        datetime.strptime(CULTURAL_CONFIG["business_hours"]["start"], "%H:%M")
        datetime.strptime(CULTURAL_CONFIG["business_hours"]["end"], "%H:%M")
    except ValueError:
        errors.append("Invalid business hours format")

    # Validate sync config
    if SYNC_CONFIG["batch_size"] <= 0:
        errors.append("Sync batch size must be positive")

    if SYNC_CONFIG["max_retries"] < 0:
        errors.append("Max retries cannot be negative")

    # Validate notification config
    if NOTIFICATION_CONFIG["max_retries"] < 0:
        errors.append("Notification max retries cannot be negative")

    return errors


# Export all configurations
__all__ = [
    "WEBSOCKET_CONFIG",
    "CULTURAL_CONFIG",
    "NOTIFICATION_CONFIG",
    "SYNC_CONFIG",
    "EVENT_CONFIG",
    "WORKSHOP_CONFIG",
    "SECURITY_CONFIG",
    "LOGGING_CONFIG",
    "PERFORMANCE_CONFIG",
    "get_config",
    "update_config",
    "validate_config",
    "get_redis_config",
]
