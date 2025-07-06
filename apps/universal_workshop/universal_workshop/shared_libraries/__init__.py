# -*- coding: utf-8 -*-
"""
Universal Workshop - Shared Libraries Foundation
================================================

This module provides the foundational shared libraries for Universal Workshop ERP
with comprehensive Arabic cultural excellence and traditional business preservation.

Features:
- Arabic Business Logic: Traditional customer relationship patterns
- Islamic Business Principles: Religious compliance and cultural appropriateness  
- Omani Compliance: Local regulatory and business practice integration
- Cultural Validation: Arabic appropriateness and traditional pattern preservation
- Traditional Workflows: Islamic business principle preservation

Author: Universal Workshop Development Team
Version: 3.0 (Phase 3 - Backend Rebuild)
Arabic Support: Native RTL and cultural business intelligence
Cultural Context: Traditional Arabic business excellence with Islamic principles
"""

from __future__ import unicode_literals

__version__ = "3.0.0"
__author__ = "Universal Workshop Development Team"
__description__ = "Shared Libraries Foundation with Arabic Cultural Excellence"

# Arabic Business Logic Imports
from .arabic_business_logic import (
    customer_relations,
    financial_operations, 
    service_workflows,
    cultural_patterns
)

# Traditional Workflows Imports  
from .traditional_workflows import (
    islamic_business_principles,
    omani_compliance,
    traditional_service_patterns,
    cultural_communication
)

# Cultural Validation Imports
from .cultural_validation import (
    arabic_appropriateness,
    religious_compliance,
    local_business_context,
    traditional_patterns
)

# API Standards Imports
from .api_standards import (
    response_utils,
    arabic_api_patterns,
    cultural_api_validation
)

# Utilities Imports
from .utils import (
    arabic_text_processing,
    date_time_cultural,
    number_formatting
)

# Shared Library Registry
SHARED_LIBRARIES = {
    "arabic_business_logic": "Traditional Arabic business rule implementations",
    "traditional_workflows": "Islamic business principle workflow preservation", 
    "cultural_validation": "Arabic cultural appropriateness validation framework",
    "api_standards": "Unified API patterns with Arabic excellence support",
    "utils": "Arabic text processing and cultural utilities"
}

# Cultural Excellence Configuration
ARABIC_EXCELLENCE_CONFIG = {
    "rtl_support": True,
    "arabic_text_processing": True,
    "islamic_business_compliance": True,
    "omani_regulatory_integration": True,
    "traditional_workflow_preservation": True,
    "cultural_appropriateness_validation": True
}

def get_shared_library_info():
    """Get information about available shared libraries with Arabic context"""
    return {
        "libraries": SHARED_LIBRARIES,
        "arabic_excellence": ARABIC_EXCELLENCE_CONFIG,
        "version": __version__,
        "cultural_context": "Traditional Arabic business excellence with Islamic principles"
    }