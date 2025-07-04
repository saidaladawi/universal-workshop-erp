# Unified Analytics Module

## Overview
This module provides a unified interface to both advanced analytics and business reporting capabilities.

## Structure

### Advanced Analytics (from analytics_reporting)
- **Machine Learning**: ML model training and prediction
- **Predictive Analytics**: Forecasting and trend analysis  
- **Performance Monitoring**: KPI tracking and alerts
- **Interactive Dashboards**: Real-time data visualization

### Business Intelligence (from reports_analytics)  
- **Report Building**: Custom report creation and configuration
- **Scheduled Reports**: Automated report generation and delivery
- **Financial Dashboards**: Profit analysis and financial KPIs
- **Data Export**: Report export utilities

## Usage

### Import from Unified Module (Recommended)
```python
from universal_workshop.analytics_unified import MLEngine, ReportScheduler
```

### Import from Individual Modules (Legacy)
```python
# Advanced analytics
from universal_workshop.analytics_reporting.utils.ml_engine import MLEngine

# Business reporting  
from universal_workshop.reports_analytics.scheduler import ReportScheduler
```

## Migration Plan

1. **Phase 1**: Create unified interface (CURRENT)
2. **Phase 2**: Migrate imports to use unified module
3. **Phase 3**: Consolidate overlapping functionality
4. **Phase 4**: Remove individual modules

## Status
- ✅ Unified interface created
- ⏳ Migration in progress
- ⏳ Consolidation pending