# -*- coding: utf-8 -*-
"""
Communication Management Module for Universal Workshop ERP
Handles SMS and WhatsApp integration with Oman regulatory compliance
and Arabic RTL support for automotive workshop operations
"""

__version__ = "2.0.0"

# Module metadata
APP_NAME = "universal_workshop"
MODULE_NAME = "communication_management"

# Supported communication channels
SUPPORTED_CHANNELS = ["sms", "whatsapp", "email"]

# Oman regulatory compliance features
OMAN_COMPLIANCE_FEATURES = {
    "sender_registration": True,
    "content_filtering": True,
    "vat_integration": True,  # Link with billing system
    "arabic_rtl_support": True,
    "data_privacy_compliance": True,
}

# Default configuration for Oman market
DEFAULT_CONFIG = {
    "country_code": "+968",
    "timezone": "Asia/Muscat",
    "business_hours": {
        "start": "07:00",
        "end": "21:00",  # Compliance with UAE/GCC promotional messaging hours
    },
    "default_language": "ar",
    "fallback_language": "en",
}
