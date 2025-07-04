"""
Unified Analytics Module - Universal Workshop ERP
Combines advanced analytics and business reporting capabilities

This module unifies:
- Advanced Analytics & ML (from analytics_reporting)
- Business Intelligence & Reporting (from reports_analytics)
"""

# Import from advanced analytics (with graceful error handling)
try:
    from ..analytics_reporting.data_aggregation import *
    ANALYTICS_AVAILABLE = True
except (ImportError, AttributeError, Exception):
    ANALYTICS_AVAILABLE = False

try:
    from ..analytics_reporting.utils.ml_engine import *
    ML_AVAILABLE = True
except (ImportError, AttributeError, Exception):
    ML_AVAILABLE = False

try:
    from ..analytics_reporting.utils.prediction_engine import *
    PREDICTION_AVAILABLE = True
except (ImportError, AttributeError, Exception):
    PREDICTION_AVAILABLE = False

# Import from business reporting (with graceful error handling)
try:
    from ..reports_analytics.scheduler import *
    REPORTING_AVAILABLE = True
except (ImportError, AttributeError, Exception):
    REPORTING_AVAILABLE = False

__all__ = [
    # Advanced Analytics
    'MLEngine',
    'PredictionEngine', 
    'DataAggregation',
    
    # Business Reporting
    'ReportScheduler',
]