"""
Receivables Management System for Universal Workshop ERP
This module has been refactored into a modular structure.

DEPRECATED: Import from this file will be removed in future versions.
Use: from .receivables import OmanReceivablesManager, ERPNextV15ReceivablesEnhancer
"""

import warnings
from .receivables import OmanReceivablesManager, ERPNextV15ReceivablesEnhancer

# Issue deprecation warning for direct imports
warnings.warn(
    "Importing from receivables_management.py is deprecated. "
    "Use 'from universal_workshop.billing_management.receivables import OmanReceivablesManager, ERPNextV15ReceivablesEnhancer' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Maintain backward compatibility
__all__ = ['OmanReceivablesManager', 'ERPNextV15ReceivablesEnhancer']