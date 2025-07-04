"""
P&L Reporting System for Universal Workshop ERP
This module has been refactored into a modular structure.

DEPRECATED: Import from this file will be removed in future versions.
Use: from .pnl_reporting import WorkshopPnLReportingManager
"""

import warnings
from .pnl_reporting import WorkshopPnLReportingManager

# Issue deprecation warning for direct imports
warnings.warn(
    "Importing from pnl_reporting.py is deprecated. "
    "Use 'from universal_workshop.billing_management.pnl_reporting import WorkshopPnLReportingManager' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Maintain backward compatibility
__all__ = ['WorkshopPnLReportingManager']