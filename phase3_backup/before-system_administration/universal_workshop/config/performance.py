"""
Universal Workshop ERP - Performance Configuration
Application-level performance settings and optimizations
"""

# List view pagination settings
LIST_VIEW_PAGE_SIZE = {
    "Service Order": 50,
    "Customer": 100,
    "Vehicle": 100,
    "Appointment": 25,
    "Parts Request": 50
}

# Search result limits
SEARCH_RESULT_LIMITS = {
    "customer_search": 50,
    "vehicle_search": 50,
    "parts_search": 100,
    "service_search": 25
}

# Cache TTL settings (in seconds)
CACHE_TTL = {
    "service_catalog": 3600,  # 1 hour
    "customer_summary": 1800,  # 30 minutes
    "vehicle_history": 1800,  # 30 minutes
    "technician_skills": 7200,  # 2 hours
    "workshop_schedule": 900,  # 15 minutes
    "parts_availability": 300  # 5 minutes
}

# Background job queue settings
JOB_QUEUE_SETTINGS = {
    "notification_queue": "short",
    "report_generation": "long",
    "analytics_update": "long",
    "email_queue": "short",
    "sms_queue": "short"
}

# Performance monitoring thresholds
PERFORMANCE_THRESHOLDS = {
    "slow_query_time": 2.0,  # seconds
    "cache_hit_ratio_min": 0.8,  # 80%
    "response_time_warning": 1.0,  # seconds
    "response_time_critical": 3.0  # seconds
}

# Database connection pool settings
DB_POOL_SETTINGS = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
}

# File upload optimizations
FILE_UPLOAD_SETTINGS = {
    "max_file_size": 25 * 1024 * 1024,  # 25MB
    "allowed_file_types": [
        "jpg", "jpeg", "png", "pdf", "doc", "docx", 
        "xls", "xlsx", "csv", "txt"
    ],
    "compress_images": True,
    "image_quality": 85
}

# API rate limiting
API_RATE_LIMITS = {
    "per_minute": {
        "default": 100,
        "search": 200,
        "read": 300,
        "write": 50
    },
    "per_hour": {
        "default": 1000,
        "search": 2000,
        "read": 3000,
        "write": 500
    }
}
