# -*- coding: utf-8 -*-
"""
Message Queuing System for Universal Workshop Communication Management
Redis-based reliable message delivery with retry mechanisms
"""

from .redis_queue_manager import RedisQueueManager
from .message_worker import MessageWorker

__version__ = "2.0.0"

# Default queue configurations
DEFAULT_QUEUES = {
    "sms_queue": {
        "name": "sms_queue",
        "default_timeout": 300,  # 5 minutes
        "retry_limit": 3,
        "retry_delay": 60,  # 1 minute
    },
    "whatsapp_queue": {
        "name": "whatsapp_queue",
        "default_timeout": 600,  # 10 minutes
        "retry_limit": 5,
        "retry_delay": 120,  # 2 minutes
    },
    "email_queue": {
        "name": "email_queue",
        "default_timeout": 180,  # 3 minutes
        "retry_limit": 2,
        "retry_delay": 300,  # 5 minutes
    },
    "bulk_communication_queue": {
        "name": "bulk_communication_queue",
        "default_timeout": 900,  # 15 minutes
        "retry_limit": 2,
        "retry_delay": 600,  # 10 minutes
    },
}

# Queue management module for Universal Workshop communication system
