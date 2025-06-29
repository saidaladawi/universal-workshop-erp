# Universal Workshop ERP - Comprehensive File Structure Memory Map

## Project Overview
**Location**: `/home/said/frappe-dev/frappe-bench/apps/universal_workshop/`
**Framework**: ERPNext v15.65.2 with Frappe Framework
**Purpose**: Arabic-first automotive workshop management system for Oman

---

## 1. MODULE STRUCTURE

### Core Modules (from modules.txt)
1. **Workshop Management** - Core workshop operations
2. **License Management** - Business registration and compliance
3. **Customer Management** - CRM with Arabic support
4. **Search Integration** - Elasticsearch integration
5. **Vehicle Management** - VIN decoding, maintenance
6. **Billing Management** - Omani VAT compliance
7. **Analytics Reporting** - KPI dashboards
8. **Data Migration** - Legacy system migration
9. **Parts Inventory** - Barcode scanning, ABC analysis
10. **Purchasing Management** - Supplier management
11. **Scrap Management** - Vehicle dismantling
12. **Training Management** - Technician training
13. **User Management** - Enhanced security
14. **Sales Service** - Service orders, estimates

---

## 2. DOCTYPE MAPPING

### Workshop Management Module
**Location**: `/universal_workshop/workshop_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| backup_manager | ✓ | ✓ | - | Backup automation |
| error_logger | ✓ | ✓ | - | Error tracking |
| integration_manager | ✓ | ✓ | - | Third-party integrations |
| license_manager | ✓ | ✓ | - | License validation |
| mobile_device_management | ✓ | ✓ | - | Mobile device tracking |
| onboarding_performance_log | ✓ | ✓ | - | Setup performance tracking |
| onboarding_progress | ✓ | ✓ | - | Workshop setup progress |
| performance_monitor | ✓ | ✓ | - | System performance |
| quality_control_checkpoint | ✓ | ✓ | - | QC checkpoints |
| quality_control_document | ✓ | ✓ | - | QC documentation |
| quality_control_photo | ✓ | ✓ | - | QC photo management |
| service_bay | ✓ | ✓ | - | Workshop bay management |
| service_order | ✓ | ✓ | ✓ | Core service orders |
| service_order_labor | ✓ | ✓ | - | Labor tracking |
| service_order_parts | ✓ | ✓ | - | Parts usage |
| service_order_status_history | ✓ | ✓ | - | Status tracking |
| skill | ✓ | ✓ | - | Technician skills |
| system_health_monitor | ✓ | ✓ | - | System health |
| technician | ✓ | ✓ | - | Technician management |
| technician_skills | ✓ | ✓ | - | Skills mapping |
| workshop_profile | ✓ | ✓ | - | Workshop configuration |
| workshop_settings | ✓ | ✓ | - | System settings |
| workshop_theme | ✓ | ✓ | - | Theme management |

### Vehicle Management Module
**Location**: `/universal_workshop/vehicle_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| maintenance_alert | ✓ | ✓ | - | Maintenance reminders |
| maintenance_schedule | ✓ | ✓ | - | Scheduled maintenance |
| service_record | ✓ | ✓ | - | Service history |
| service_record_parts | ✓ | ✓ | - | Parts used in service |
| vehicle | ✓ | ✓ | ✓ | Core vehicle data |
| vehicle_document | ✓ | ✓ | - | Vehicle documents |
| vehicle_inspection | ✓ | ✓ | - | Inspection records |
| vehicle_inspection_item | ✓ | ✓ | - | Inspection checklist |
| vehicle_inspection_photo | ✓ | - | - | Inspection photos |
| vehicle_make | ✓ | ✓ | - | Vehicle makes |
| vehicle_model | ✓ | ✓ | - | Vehicle models |

### Parts Inventory Module
**Location**: `/universal_workshop/parts_inventory/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| item_cross_reference | ✓ | ✓ | - | Cross-reference mapping |
| part_cross_reference | ✓ | ✓ | - | Part compatibility |
| stock_transfer_log | ✓ | ✓ | - | Transfer tracking |
| supplier_parts_category | ✓ | ✓ | - | Supplier categorization |

### Sales & Service Module
**Location**: `/universal_workshop/sales_service/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| labor_time_log | ✓ | ✓ | - | Time tracking |
| mobile_photo_log | ✓ | ✓ | - | Mobile photo management |
| parts_suggestion_feedback | ✓ | ✓ | - | AI suggestion feedback |
| quality_inspection_checklist | ✓ | ✓ | - | QC checklist |
| service_estimate | ✓ | ✓ | ✓ | Service estimates |
| service_estimate_item | ✓ | ✓ | - | Estimate line items |
| service_estimate_parts | ✓ | ✓ | - | Estimate parts |
| service_progress_log | ✓ | ✓ | - | Progress tracking |
| vat_configuration | ✓ | ✓ | - | VAT setup |

### Scrap Management Module
**Location**: `/universal_workshop/scrap_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| disassembly_plan | ✓ | ✓ | - | Dismantling planning |
| disassembly_step | ✓ | ✓ | - | Dismantling steps |
| dismantling_work_order | ✓ | ✓ | - | Work orders |
| extracted_parts | ✓ | ✓ | - | Extracted parts tracking |
| inventory_movement | ✓ | ✓ | - | Parts movement |
| part_movement_history | ✓ | ✓ | - | Movement history |
| part_photo | ✓ | ✓ | - | Part photos |
| part_quality_assessment | ✓ | ✓ | - | Quality assessment |
| parts_condition_grade | ✓ | ✓ | - | Condition grading |
| parts_grade_applicable_category | ✓ | ✓ | - | Grade categories |
| parts_grade_history | ✓ | ✓ | - | Grade history |
| part_storage_location | ✓ | ✓ | - | Storage locations |
| profit_analysis | ✓ | ✓ | - | Profitability analysis |
| sales_channel | ✓ | ✓ | - | Sales channels |
| scrap_vehicle | ✓ | ✓ | - | Scrap vehicle records |
| scrap_vehicle_assessment_item | ✓ | ✓ | - | Assessment items |
| scrap_vehicle_document | ✓ | ✓ | - | Vehicle documents |
| scrap_vehicle_extracted_part | ✓ | ✓ | - | Extracted parts |
| scrap_vehicle_part_assessment | ✓ | ✓ | - | Part assessments |
| scrap_vehicle_photo | ✓ | ✓ | - | Vehicle photos |
| storage_location | ✓ | ✓ | - | Storage management |
| storage_zone | ✓ | ✓ | - | Storage zones |
| storage_zone_allowed_category | ✓ | ✓ | - | Zone categories |
| vehicle_dismantling_bom | ✓ | ✓ | - | Dismantling BOM |
| vehicle_dismantling_extractable_part | ✓ | ✓ | - | Extractable parts |
| vehicle_dismantling_operation | ✓ | ✓ | - | Operations |

### Training Management Module
**Location**: `/universal_workshop/training_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| documentation_template | ✓ | ✓ | - | Documentation templates |
| documentation_template_section | ✓ | ✓ | - | Template sections |
| help_content | ✓ | ✓ | ✓ | Help system content |
| help_content_documentation | ✓ | ✓ | - | Content documentation |
| help_content_feedback | ✓ | ✓ | - | User feedback |
| help_content_role | ✓ | ✓ | - | Role-based content |
| help_content_route | ✓ | ✓ | - | Route-based help |
| help_content_training | ✓ | ✓ | - | Training content |
| help_content_video | ✓ | ✓ | - | Video content |
| help_usage_log | ✓ | ✓ | - | Usage analytics |
| knowledge_base_article | ✓ | ✓ | ✓ | Knowledge articles |
| knowledge_base_category | ✓ | ✓ | ✓ | Article categories |
| training_certification | ✓ | ✓ | ✓ | Certifications |
| training_module | ✓ | ✓ | ✓ | Training modules |
| training_path | ✓ | ✓ | ✓ | Learning paths |
| training_path_module | ✓ | ✓ | - | Path modules |
| training_path_prerequisite | ✓ | ✓ | - | Prerequisites |
| training_progress | ✓ | ✓ | ✓ | Progress tracking |
| user_training_path | ✓ | ✓ | ✓ | User assignments |

### User Management Module
**Location**: `/universal_workshop/user_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| workshop_document_permission | ✓ | ✓ | - | Document permissions |
| workshop_field_permission | ✓ | ✓ | - | Field-level permissions |
| workshop_permission_profile | ✓ | ✓ | - | Permission profiles |
| workshop_permission_role | ✓ | ✓ | - | Role permissions |
| workshop_role | ✓ | ✓ | ✓ | Custom roles |
| workshop_role_permission | ✓ | ✓ | - | Role-permission mapping |

### Customer Management Module
**Location**: `/universal_workshop/customer_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| customer_analytics | ✓ | ✓ | - | Customer analytics |
| customer_loyalty_points | ✓ | ✓ | - | Loyalty program |

### License Management Module
**Location**: `/universal_workshop/license_management/doctype/`

| DocType | JSON | Controller (.py) | Client Script (.js) | Purpose |
|---------|------|------------------|-------------------|----------|
| business_registration | ✓ | ✓ | - | Business registration |
| business_registration_document | ✓ | ✓ | - | Registration docs |
| business_workshop_binding | ✓ | ✓ | - | Business binding |
| dashboard_audit_event | ✓ | ✓ | - | Audit events |
| license_activity_log | ✓ | ✓ | - | Activity logging |
| license_audit_log | ✓ | ✓ | - | Audit logs |
| license_key_pair | ✓ | ✓ | - | Key management |
| license_management_dashboard | ✓ | ✓ | ✓ | Dashboard |
| offline_session | ✓ | ✓ | - | Offline sessions |
| revoked_token | ✓ | ✓ | - | Token management |
| security_action_recommendation | ✓ | ✓ | - | Security recommendations |
| security_monitor | ✓ | ✓ | - | Security monitoring |
| security_threat_indicator | ✓ | ✓ | - | Threat indicators |

---

## 3. REPORTS & ANALYTICS

### Standard Reports
**Location**: `/universal_workshop/*/report/`

| Report | Module | JSON | Python | Purpose |
|--------|--------|------|--------|---------|
| service_bay_utilization | analytics_reporting | ✓ | ✓ | Bay efficiency |
| environmental_compliance_dashboard | environmental_compliance | ✓ | ✓ | Compliance tracking |
| vehicle_roi_analysis | reports_analytics | ✓ | ✓ | ROI analysis |
| help_content_analytics | training_management | ✓ | ✓ | Help system analytics |

---

## 4. API ENDPOINTS

### Main API Files
**Location**: `/universal_workshop/*/api/` and `api.py` files

| File | Module | Purpose |
|------|--------|---------|
| `/api.py` | Root | Main API endpoints |
| `/data_migration/api.py` | Data Migration | Migration APIs |
| `/parts_inventory/api.py` | Parts Inventory | Inventory APIs |
| `/purchasing_management/api.py` | Purchasing | Purchase APIs |
| `/search_integration/api.py` | Search | Search APIs |
| `/themes/api.py` | Themes | Theme APIs |
| `/vehicle_management/api.py` | Vehicle | Vehicle APIs |

### API Subdirectories
- `/analytics_reporting/api/` - Analytics APIs
- `/api/` - General APIs (backup, performance monitoring)
- `/communication_management/api/` - Communication APIs
- `/license_management/api/` - License APIs
- `/marketplace_integration/api/` - Marketplace APIs

---

## 5. WEB FORMS

### Available Web Forms
**Location**: `/universal_workshop/*/web_form/`

| Web Form | Module | JSON | Python | Purpose |
|----------|--------|------|--------|---------|
| license_admin_portal | license_management | ✓ | ✓ | License admin interface |
| workshop_onboarding | workshop_management | ✓ | ✓ | Workshop setup wizard |

---

## 6. WORKFLOWS

### Defined Workflows
**Location**: `/universal_workshop/*/workflow/`

| Workflow | Module | JSON | Purpose |
|----------|--------|------|---------|
| environmental_compliance_workflow | environmental_compliance | ✓ | Compliance approval |
| material_request_approval_workflow | purchasing_management | ✓ | Material request approval |
| purchase_order_approval_workflow | purchasing_management | ✓ | PO approval |

---

## 7. FRONTEND ASSETS

### CSS Files
**Location**: `/universal_workshop/public/css/`

| File | Purpose |
|------|---------|
| arabic-rtl.css | RTL Arabic support |
| customer_analytics_dashboard.css | Customer analytics styling |
| customer_notifications.css | Notification styling |
| customer_portal.css | Portal styling |
| customer_search.css | Search interface |
| dark_mode.css | Dark mode styling |
| dashboard_layout.css | Dashboard layout |
| demand_forecasting.css | Forecasting UI |
| dynamic_branding.css | Dynamic branding |
| inventory_alerts_dashboard.css | Inventory alerts |
| labor_time_tracking.css | Time tracking UI |
| mobile-app.css | Mobile app styling |
| mobile-workshop.css | Mobile workshop |
| mobile_warehouse.css | Mobile warehouse |
| onboarding_wizard.css | Setup wizard |
| performance_visualizations.css | Performance charts |
| progress_tracking.css | Progress tracking |
| quality_control.css | QC interface |
| quick_action_toolbar.css | Quick actions |
| supplier_dashboard.css | Supplier interface |
| technician-mobile.css | Technician mobile |
| theme_selector.css | Theme selection |
| theme_styles.css | Theme styles |
| vat_automation.css | VAT interface |
| vehicle_form.css | Vehicle forms |

### JavaScript Files
**Location**: `/universal_workshop/public/js/`

| File | Purpose |
|------|---------|
| abc_analysis_ui.js | ABC analysis interface |
| arabic-utils.js | Arabic utilities |
| audit_frontend.js | Audit interface |
| barcode_scanner.js | Barcode scanning |
| branding_service.js | Branding service |
| compatibility_matrix_ui.js | Parts compatibility |
| contextual_help.js | Help system |
| customer_analytics_dashboard.js | Customer analytics |
| customer_notifications.js | Notifications |
| customer_portal.js | Customer portal |
| customer_search.js | Search functionality |
| cycle_counting_ui.js | Cycle counting |
| dark_mode_manager.js | Dark mode |
| demand_forecasting.js | Demand forecasting |
| help_system_tests.js | Help system tests |
| inventory_alerts_dashboard.js | Inventory alerts |
| job-management.js | Job management |
| labor_time_tracking.js | Time tracking |
| logo_upload_widget.js | Logo management |
| mobile-inventory-scanner.js | Mobile scanning |
| mobile-receiving.js | Mobile receiving |
| mobile_inventory.js | Mobile inventory |
| mobile_warehouse.js | Mobile warehouse |
| offline_manager.js | Offline capabilities |
| onboarding_wizard.js | Setup wizard |
| order_conversion_workflow.js | Order conversion |
| parts_suggestion.js | Parts suggestions |
| performance_visualizations.js | Performance charts |
| print_format_integration.js | Print formats |
| progress_tracking_dashboard.js | Progress tracking |
| qr_code_invoice.js | QR code generation |
| quality_control.js | Quality control |
| quick_action_toolbar.js | Quick actions |
| rtl_branding_manager.js | RTL branding |
| sales_invoice.js | Sales invoice |
| security_alerts_frontend.js | Security alerts |
| service-worker.js | Service worker |
| service_worker.js | PWA service worker |
| session_frontend.js | Session management |
| session_management.js | Session handling |
| setup_check.js | Setup checks |
| stock_transfer_ui.js | Stock transfers |
| storage_location.js | Storage management |
| supplier_dashboard.js | Supplier interface |
| technician-app.js | Technician app |
| technician-sw.js | Technician service worker |
| theme_manager.js | Theme management |
| theme_selector.js | Theme selection |
| time-tracker.js | Time tracking |
| vat_automation.js | VAT automation |
| workshop-offline.js | Offline functionality |
| workshop_profile.js | Workshop profile |

---

## 8. WEBSITE PAGES

### Web Pages
**Location**: `/universal_workshop/www/`

| Page | Python | Purpose |
|------|--------|---------|
| abc_analysis.html | - | ABC analysis page |
| compatibility-matrix.html | ✓ | Parts compatibility |
| customer-analytics-dashboard.html | ✓ | Customer analytics |
| login.html | ✓ | Custom login |
| migration-dashboard.html | ✓ | Migration dashboard |
| mobile-inventory-scanner.html | ✓ | Mobile scanner |
| mobile_inventory.html | - | Mobile inventory |
| parts-catalog.html | ✓ | Parts catalog |
| supplier-dashboard.html | ✓ | Supplier dashboard |
| technician.html | ✓ | Technician interface |
| training-dashboard.html | ✓ | Training dashboard |
| training-path-admin.html | ✓ | Training admin |
| universal-workshop-dashboard.html | ✓ | Main dashboard |

---

## 9. CONFIGURATION FILES

### Key Configuration Files
| File | Location | Purpose |
|------|----------|---------|
| hooks.py | `/universal_workshop/` | App hooks and configurations |
| modules.txt | `/universal_workshop/` | Module definitions |
| patches.txt | `/universal_workshop/` | Database patches |
| requirements.txt | Root | Python dependencies |
| pyproject.toml | Root | Project configuration |
| manifest.json | `/public/` | PWA manifest |

### Custom Fields & Fixtures
| Location | Purpose |
|----------|---------|
| `/fixtures/custom_fields.json` | Custom field definitions |
| `/billing_management/fixtures/` | VAT and billing fields |
| `/parts_inventory/fixtures/` | Inventory fields |
| `/themes/fixtures.py` | Theme configurations |
| `/dark_mode/fixtures.py` | Dark mode settings |

---

## 10. TESTING FILES

### Test Files Structure
**Location**: Various modules under `test_*.py`

| Module | Test Files |
|--------|------------|
| Root tests | `/tests/` directory with comprehensive tests |
| Module tests | `test_*.py` files in each module |
| DocType tests | `test_[doctype].py` in doctype folders |

### Test Categories
- Integration tests
- API tests
- Security tests
- Performance tests
- Arabic language tests
- Cross-browser tests

---

## 11. UTILITY FILES

### Utility Modules
**Location**: `/universal_workshop/utils/`

| File | Purpose |
|------|---------|
| arabic_utils.py | Arabic language utilities |
| backup_automation.py | Backup automation |
| backup_restore.py | Backup restoration |
| backup_scheduler.py | Backup scheduling |
| boot_session.py | Session initialization |
| cache_utils.py | Cache management |
| data_integrity_checker.py | Data validation |
| error_monitor.py | Error monitoring |
| foreign_key_validator.py | FK validation |
| image_optimizer.py | Image optimization |
| job_utils.py | Background job utilities |
| performance_monitor.py | Performance monitoring |
| rollback_validator.py | Rollback validation |

---

## 12. SCHEDULED TASKS

### Task Categories (from hooks.py)
- **Every minute**: Communication queues, high-frequency KPIs
- **Every 5 minutes**: Delivery alerts, medium-frequency KPIs
- **Every 15 minutes**: Rate limits, low-frequency KPIs
- **Every 6 hours**: Failed message handling
- **Hourly**: Queue health, session cleanup
- **Daily**: Analytics updates, notifications, training reminders
- **Weekly**: Customer segmentation, progress summaries
- **Monthly**: Cleanup tasks, training reports

---

## 13. DOCUMENT EVENT HOOKS

### Major Document Hooks
- **Customer**: Search indexing, VAT validation, permission checks
- **Sales Invoice**: QR code generation, workflow management, notifications
- **Service Order**: Status updates, permission validation
- **Payment Entry**: Receivables management, reconciliation
- **Item**: Barcode generation, inventory tracking
- **Stock Entry**: Transfer validation, warehouse management

---

## 14. QUICK REFERENCE

### Finding Files Quickly
```bash
# Find all DocTypes
find /apps/universal_workshop/universal_workshop -name "*.json" -path "*/doctype/*"

# Find all reports
find /apps/universal_workshop/universal_workshop -name "*.json" -path "*/report/*"

# Find API files
find /apps/universal_workshop/universal_workshop -name "api.py"

# Find client scripts
find /apps/universal_workshop/universal_workshop -name "*.js" -path "*/doctype/*"

# Find workflows
find /apps/universal_workshop/universal_workshop -name "*.json" -path "*workflow*"
```

### Development Patterns
- **DocType Structure**: JSON definition + Python controller + JS client script
- **API Pattern**: Module-level api.py files with whitelisted methods
- **Hook Pattern**: Document events defined in hooks.py
- **Asset Pattern**: CSS/JS files in /public/ directory
- **Test Pattern**: test_*.py files alongside main code

This memory map provides a comprehensive reference for navigating and understanding the Universal Workshop ERP codebase structure.