# Universal Workshop ERP - Complete File Index

## Quick Navigation Commands

```bash
# Find specific DocType files
find apps/universal_workshop -name "*vehicle*.json" -path "*/doctype/*"
find apps/universal_workshop -name "*service_order*.py" -path "*/doctype/*"
find apps/universal_workshop -name "*customer*.js" -path "*/doctype/*"

# Search by module
find apps/universal_workshop/universal_workshop/workshop_management -type f -name "*.py"
find apps/universal_workshop/universal_workshop/vehicle_management -type f -name "*.js"
find apps/universal_workshop/universal_workshop/parts_inventory -type f -name "*.json"

# Find API endpoints
find apps/universal_workshop -path "*/api/*" -name "*.py"

# Find reports
find apps/universal_workshop -path "*/report/*" -name "*.py"

# Find templates and web pages
find apps/universal_workshop -name "*.html"

# Find CSS and styling
find apps/universal_workshop -name "*.css" -o -name "*.scss"
```

## Module Directory Structure

### Core Business Modules

#### 1. Workshop Management (`workshop_management/`)
**Purpose**: Core workshop operations, service orders, technician management
- **DocTypes**: Service Order, Service Bay, Technician, Quality Control Checklist
- **Key Files**:
  - `doctype/service_order/service_order.py` - Main service order controller
  - `doctype/service_order/service_order.js` - Client-side form logic
  - `doctype/technician/technician.py` - Technician management
  - `api/workshop_api.py` - Workshop REST endpoints

#### 2. Vehicle Management (`vehicle_management/`)
**Purpose**: VIN decoding, vehicle registry, maintenance tracking
- **DocTypes**: Vehicle, Vehicle Inspection, Maintenance Schedule, Service Record
- **Key Files**:
  - `doctype/vehicle/vehicle.py` - VIN decoding and vehicle controller
  - `doctype/vehicle_inspection/vehicle_inspection.py` - Digital inspection system
  - `utils/vin_decoder.py` - VIN validation and specification lookup
  - `api/vehicle_api.py` - Vehicle management endpoints

#### 3. Parts Inventory (`parts_inventory/`)
**Purpose**: Advanced inventory management with barcode scanning
- **DocTypes**: Part, Part Cross Reference, Barcode Scanner, ABC Analysis, Cycle Count
- **Key Files**:
  - `doctype/part/part.py` - Parts master controller
  - `doctype/abc_analysis/abc_analysis.py` - Inventory optimization
  - `utils/barcode_utils.py` - Barcode scanning utilities
  - `mobile/barcode_scanner.js` - Mobile barcode interface

#### 4. Customer Management (`customer_management/`)
**Purpose**: CRM with Arabic support and loyalty programs
- **DocTypes**: Customer (extended), Loyalty Program, Customer Communication
- **Key Files**:
  - `doctype/customer/customer.py` - Extended customer controller
  - `doctype/loyalty_program/loyalty_program.py` - Points management
  - `utils/customer_analytics.py` - Customer behavior analysis

#### 5. Billing Management (`billing_management/`)
**Purpose**: Omani VAT compliance and financial reporting
- **DocTypes**: Sales Invoice (extended), VAT Return, QR Code Invoice, Financial KPI
- **Key Files**:
  - `doctype/sales_invoice/sales_invoice.py` - VAT calculation (5%)
  - `utils/qr_code_generator.py` - E-invoice QR codes
  - `utils/vat_compliance.py` - Omani VAT compliance
  - `report/vat_return/vat_return.py` - VAT reporting

### Technical Support Modules

#### 6. User Management (`user_management/`)
**Purpose**: Enhanced security and session management
- **DocTypes**: User Permission, Session Log, Security Event
- **Key Files**:
  - `security/session_manager.py` - Session timeout and security
  - `security/permission_hooks.py` - Role-based access control
  - `api/auth_api.py` - Authentication endpoints

#### 7. Training Management (`training_management/`)
**Purpose**: H5P content and technician certification
- **DocTypes**: Training Module, Help Content, Knowledge Base Article, Certification
- **Key Files**:
  - `doctype/training_module/training_module.py` - H5P integration
  - `utils/help_system.py` - Contextual help system
  - `api/training_api.py` - Training content API

#### 8. Communication Management (`communication_management/`)
**Purpose**: SMS, WhatsApp, and notification system
- **DocTypes**: SMS Log, Communication Template, Notification Settings
- **Key Files**:
  - `utils/sms_integration.py` - Omani SMS providers (Twilio)
  - `utils/whatsapp_integration.py` - WhatsApp Business API
  - `templates/` - Notification templates (Arabic/English)

#### 9. Analytics Reporting (`analytics_reporting/`)
**Purpose**: KPI dashboards and business intelligence
- **DocTypes**: Real Time KPI, Workshop Analytics, Performance Metric, Predictive Model
- **Key Files**:
  - `doctype/real_time_kpi/real_time_kpi.py` - Live dashboard data
  - `report/service_bay_utilization/` - Operational efficiency reports
  - `utils/ml_engine.py` - Predictive analytics engine

### Specialized Modules

#### 10. License Management (`license_management/`)
**Purpose**: Business registration and compliance
- **DocTypes**: Business License, Compliance Check, Audit Trail
- **Key Files**:
  - `utils/license_validator.py` - Business registration validation
  - `security/audit_logger.py` - Compliance audit trails

#### 11. Arabic Localization (`arabic_localization/`)
**Purpose**: RTL support and Arabic number formatting
- **Key Files**:
  - `utils/arabic_numbers.py` - Arabic numeral conversion
  - `utils/rtl_formatter.py` - RTL text formatting
  - `fixtures/arabic_translations.json` - Translation data

#### 12. Mobile App (`mobile_app/`)
**Purpose**: PWA and mobile technician interface
- **Key Files**:
  - `pwa/service_worker.js` - Offline capability
  - `mobile/technician_interface.js` - Mobile-optimized UI
  - `utils/offline_sync.py` - Data synchronization

## Asset Files Organization

### CSS/Styling (`public/css/`)
- `arabic-rtl.css` - Main RTL stylesheet
- `mobile-arabic.css` - Mobile Arabic optimization
- `workshop-theme.css` - Workshop-specific styling
- `print-formats.css` - Invoice and report printing

### JavaScript (`public/js/`)
- `universal_workshop.js` - Main application script
- `arabic-support.js` - Arabic input and formatting
- `barcode-scanner.js` - QuaggaJS barcode integration
- `mobile-pwa.js` - Progressive Web App functionality

### Templates (`templates/`)
- `pages/` - Web pages and portals
- `emails/` - Email notification templates
- `includes/` - Reusable template components
- `print_formats/` - Invoice and report templates

## API Endpoints (`api/`)

### Main API Files
- `workshop_api.py` - Core workshop operations
- `vehicle_api.py` - Vehicle management endpoints
- `inventory_api.py` - Parts and inventory API
- `customer_api.py` - Customer management
- `billing_api.py` - Financial and billing operations
- `mobile_api.py` - Mobile app endpoints
- `auth_api.py` - Authentication and security

## Configuration Files

### Application Configuration
- `hooks.py` - Frappe application hooks and event handlers
- `modules.txt` - Module definitions and order
- `patches.txt` - Database migration patches
- `package.json` - Frontend dependencies (Node.js)
- `pyproject.toml` - Python linting configuration (Ruff)

### Data Files
- `fixtures/` - Demo data and initial setup
- `fixtures/arabic_translations.json` - Arabic language pack
- `fixtures/workshop_setup.json` - Default workshop configuration

## Testing Structure

### Test Organization
- Each DocType has `test_[doctype].py` in its directory
- Integration tests in `tests/` subdirectories
- Performance tests marked with `@pytest.mark.performance`
- Arabic language tests marked with `@pytest.mark.arabic`
- Security tests marked with `@pytest.mark.security`

## Reports and Analytics

### Standard Reports (`report/`)
- Financial reports (P&L, VAT returns, cash flow)
- Operational reports (service bay utilization, technician performance)
- Customer analytics (loyalty program performance, retention)
- Inventory reports (ABC analysis, cycle count results)

## Utilities and Helpers (`utilities/`)

### Core Utilities
- `backup_manager.py` - Automated backup system
- `performance_monitor.py` - System performance tracking
- `security_scanner.py` - Security vulnerability scanning
- `data_migration.py` - Data import/export utilities

## Quick Search Patterns

```bash
# Find all controllers for a specific module
find apps/universal_workshop/universal_workshop/[module_name] -name "*.py" -path "*/doctype/*" ! -name "test_*"

# Find all client scripts
find apps/universal_workshop -name "*.js" -path "*/doctype/*"

# Find all reports
find apps/universal_workshop -path "*/report/*" -name "*.py"

# Find templates by type
find apps/universal_workshop -path "*/templates/emails/*" -name "*.html"
find apps/universal_workshop -path "*/templates/pages/*" -name "*.html"

# Find API endpoints
find apps/universal_workshop -path "*/api/*" -name "*.py"

# Find configuration files
find apps/universal_workshop -maxdepth 2 -name "hooks.py" -o -name "modules.txt" -o -name "patches.txt"
```

This file index provides comprehensive navigation for the Universal Workshop ERP system, making it easy to locate any file when working on specific features or debugging issues.