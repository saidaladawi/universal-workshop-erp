"""
Cash Flow Forecasting System for Universal Workshop ERP
This module has been refactored into a modular structure.
Import classes from the cash_flow submodule.

DEPRECATED: Import from this file will be removed in future versions.
Use: from .cash_flow import CashFlowForecastingManager, ERPNextV15CashFlowEnhancer
"""

import warnings
from .cash_flow import CashFlowForecastingManager, ERPNextV15CashFlowEnhancer

# Issue deprecation warning for direct imports
warnings.warn(
    "Importing from cash_flow_forecasting.py is deprecated. "
    "Use 'from universal_workshop.billing_management.cash_flow import CashFlowForecastingManager, ERPNextV15CashFlowEnhancer' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Maintain backward compatibility
__all__ = ['CashFlowForecastingManager', 'ERPNextV15CashFlowEnhancer']