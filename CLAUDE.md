# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Universal Workshop ERP - Frappe/ERPNext Bench Development

This is a Frappe/ERPNext bench containing a comprehensive Arabic-first ERP solution for Omani automotive workshops. The system is built on ERPNext v15.65.2 with the Frappe Framework and includes a custom app called "Universal Workshop".

**Current Status**: Production-ready system with 254 DocType definitions, 429 Python controllers, and 100 JavaScript client scripts. Recently stabilized from technical emergency state with comprehensive architectural fixes including modular restructuring, complete dark mode implementation, and enhanced testing framework.

### Architecture Overview

**Framework Stack:**
- **Backend**: ERPNext v15.65.2, Frappe Framework, Python 3.10+
- **Frontend**: Vue.js 3 + TypeScript + Vite (frontend_v2), Bootstrap 4.6.2, RTL Arabic CSS
- **Database**: MariaDB with Arabic character support
- **Cache/Queue**: Redis (cache: port 13000, queue: port 11000)
- **Real-time**: Socket.IO (port 9000)
- **Build System**: ESBuild with Vue 3 support + Vite for modern frontend
- **Linting**: Ruff (Python), MyPy (type checking), comprehensive pyproject.toml configuration
- **Testing**: Pytest with coverage, multiple test markers (integration, e2e, api, security, performance)

**Site Structure:**
- Default site: `universal.local` (configured in common_site_config.json)
- Development server runs on port 8000
- File watcher on port 6787 for hot reload

### Key Applications

1. **frappe** - Core framework providing the foundation
2. **erpnext** - Standard ERP functionality 
3. **universal_workshop** - Custom automotive workshop management system with:
   - Arabic-first interface with RTL support
   - Vehicle management with VIN decoding
   - Parts inventory with barcode scanning
   - Omani VAT compliance (5%) with QR code generation
   - Customer portal and mobile PWA interface
   - Advanced billing and financial reporting
   - Training management system
   - Session management and security features

### Development Commands

**Starting Development Environment:**
```bash
# Start all services (recommended for development)
bench start

# Start only web server
bench serve
bench serve --port 8080  # custom port

# Individual services
bench worker              # Background workers
bench schedule           # Scheduler process
```

**Asset Building:**
```bash
# Watch mode for development (auto-rebuild on changes)
bench watch

# Production build
bench build

# From Frappe app directory for frontend assets
yarn watch               # Development mode
yarn build              # Production build

# Modern frontend (frontend_v2 with Vue 3 + TypeScript + Vite)
cd apps/universal_workshop/frontend_v2
npm run dev             # Development server with hot reload
npm run build           # Production build
npm run preview         # Preview production build
npm run type-check      # TypeScript type checking
```

**Testing:**
```bash
# Run all tests
bench run-tests

# Run tests for specific app
bench run-tests --app universal_workshop

# Run tests for specific site
bench --site universal.local run-tests

# Run UI/frontend tests
bench run-ui-tests

# Parallel testing for faster execution
bench run-parallel-tests
```

**Code Quality:**
```bash
# Python linting (configured via pyproject.toml)
ruff check              # Lint check
ruff format            # Format code
ruff check --fix       # Auto-fix linting issues

# Type checking
mypy apps/universal_workshop/universal_workshop/

# Coverage testing
pytest --cov=apps/universal_workshop/universal_workshop/ --cov-report=html

# Frontend linting (frontend_v2)
cd apps/universal_workshop/frontend_v2
npm run lint           # ESLint + Prettier
npm run lint:fix       # Auto-fix linting issues
```

**Database & Migrations:**
```bash
# Run migrations, sync schema, rebuild search
bench migrate

# Migrate specific site
bench --site universal.local migrate

# Backup before migrations
bench backup-all-sites
bench --site universal.local backup

# Database console
bench --site universal.local mariadb
```

**Cache & Development Utilities:**
```bash
# Clear caches
bench clear-cache
bench clear-website-cache

# Rebuild search index
bench rebuild-global-search

# Python console with Frappe context
bench --site universal.local console
```

**App Management:**
```bash
# Install new app from repository
bench get-app [git-url]

# Install app on site
bench --site universal.local install-app [appname]

# Create new custom app
bench new-app [appname]
```

### Module Structure (Universal Workshop)

The custom app follows Frappe's modular architecture with these **24 modules** organized by functional areas:

**Core Operations:**
- **Workshop Management** - Core workshop operations, service orders, appointments
- **Workshop Operations** - Advanced workshop workflow management
- **Vehicle Management** - VIN decoding, vehicle registry, service history
- **Parts Inventory** - Inventory management with barcode scanning, ABC analysis

**Business Management:**
- **Customer Management** - CRM with Arabic support, loyalty programs
- **Customer Portal** - Self-service customer interface
- **Billing Management** - Omani VAT compliance, financial reporting, QR invoices
- **Sales Service** - Sales order management and service delivery
- **Purchasing Management** - Supplier management and procurement

**Advanced Features:**
- **Analytics Reporting** - KPI dashboards and business intelligence
- **Analytics Unified** - Unified analytics interface and reporting
- **Mobile Operations** - Mobile-first operational interfaces
- **Communication Management** - SMS, notifications, and customer communication
- **Training Management** - Technician training and certification tracking

**System & Administration:**
- **System Administration** - System configuration and management
- **User Management** - Enhanced security, session management, role-based access
- **License Management** - Business compliance and licensing
- **Search Integration** - Advanced search and indexing capabilities
- **Data Migration** - Data import/export and migration tools

**Specialized Functions:**
- **Dark Mode** - Complete dark mode functionality
- **Environmental Compliance** - Environmental regulations and compliance
- **Marketplace Integration** - Third-party marketplace connections
- **Scrap Management** - Scrap and waste management processes
- **Setup** - Initial system setup and configuration

### Development Best Practices

**Frappe Framework Conventions:**
- All custom code should follow Frappe's naming conventions
- Use DocTypes for data models, preferably through the UI first
- Hook system for extending functionality (see hooks.py files)
- Server-side Python controllers for business logic
- Client-side JavaScript for UI enhancements

**Universal Workshop Specific:**
- Arabic language support is prioritized (RTL layouts, Arabic number formatting)
- All financial calculations must comply with Omani VAT (5%)
- Mobile-first responsive design for technician interfaces
- Security and session management are critical (automotive data sensitivity)

**File Locations:**
- Python controllers: `apps/universal_workshop/universal_workshop/[module]/`
- Client scripts: `apps/universal_workshop/universal_workshop/public/js/`
- CSS/SCSS: `apps/universal_workshop/universal_workshop/public/css/`
- Templates: `apps/universal_workshop/universal_workshop/templates/`

### File Structure & Quick Reference

**Core Module Structure:**
```
apps/universal_workshop/universal_workshop/
├── workshop_management/           # Core workshop operations
├── workshop_operations/          # Advanced workshop workflows
├── vehicle_management/           # VIN decoding, vehicle registry
├── parts_inventory/              # Inventory & barcode scanning
├── customer_management/          # CRM & loyalty programs
├── customer_portal/              # Self-service customer interface
├── billing_management/           # VAT compliance & invoicing
├── sales_service/                # Sales order management
├── purchasing_management/        # Supplier management & procurement
├── user_management/              # Security & permissions
├── training_management/          # H5P content & certification
├── communication_management/     # SMS & notifications
├── analytics_reporting/          # KPIs & dashboards
├── analytics_unified/            # Unified analytics interface
├── mobile_operations/            # Mobile-first operational interfaces
├── system_administration/        # System configuration & management
├── license_management/           # Business compliance
├── search_integration/           # Advanced search capabilities
├── data_migration/               # Data import/export tools
├── dark_mode/                    # Complete dark mode functionality
├── environmental_compliance/     # Environmental regulations
├── marketplace_integration/      # Third-party marketplace connections
├── scrap_management/             # Scrap & waste management
├── setup/                        # Initial system setup
├── api/                          # REST endpoints
├── utilities/                    # Helper functions
└── frontend_v2/                  # Modern Vue 3 + TypeScript frontend
```

**Key DocTypes by Module:**
- **Workshop**: Service Order, Service Bay, Technician, Quality Control Checklist
- **Vehicle**: Vehicle, Vehicle Inspection, Maintenance Schedule, Service Record
- **Parts**: Part, Part Cross Reference, Barcode Scanner, ABC Analysis, Cycle Count
- **Customer**: Customer (extended), Loyalty Program, Customer Communication
- **Billing**: Sales Invoice (extended), VAT Return, QR Code Invoice, Financial KPI
- **Training**: Training Module, Help Content, Knowledge Base Article, Certification
- **Analytics**: Real Time KPI, Workshop Analytics, Performance Metric

**File Pattern for Each DocType:**
```
[module]/doctype/[doctype_name]/
├── [doctype_name].json           # DocType definition
├── [doctype_name].py             # Server controller
├── [doctype_name].js             # Client script
├── [doctype_name]_list.js        # List view customization
├── [doctype_name]_dashboard.py   # Dashboard configuration
└── test_[doctype_name].py        # Unit tests
```

**Quick Search Commands:**
```bash
# Find DocType files
find apps/universal_workshop -name "*.json" -path "*/doctype/*"

# Find client scripts
find apps/universal_workshop -name "*.js" -path "*/doctype/*"

# Find Python controllers
find apps/universal_workshop -name "*.py" -path "*/doctype/*" ! -name "test_*"

# Find API endpoints
find apps/universal_workshop -name "*.py" -path "*/api/*"

# Find templates
find apps/universal_workshop -name "*.html" -path "*/templates/*"

# Find CSS/styling files
find apps/universal_workshop -name "*.css" -o -name "*.scss"

# Find reports
find apps/universal_workshop -name "*.py" -path "*/report/*"
```

**Key Configuration Files:**
- `hooks.py` - Application hooks and event handlers
- `modules.txt` - Module definitions (24 modules)
- `patches.txt` - Database migration patches
- `package.json` - Frontend dependencies
- `pyproject.toml` - Comprehensive Python configuration (Ruff, MyPy, Pytest, Coverage)
- `frontend_v2/package.json` - Modern frontend dependencies (Vue 3 + TypeScript + Vite)
- `frontend_v2/tsconfig.json` - TypeScript configuration
- `frontend_v2/vite.config.ts` - Vite build configuration

**Project Statistics:**
- **DocTypes**: 254 definitions
- **Python Controllers**: 429 files
- **JavaScript Clients**: 100 files
- **Modules**: 24 functional modules
- **Production Status**: Stable and production-ready

**Arabic/RTL Files:**
- `public/css/arabic-rtl.css` - Main RTL stylesheet
- `public/css/mobile-arabic.css` - Mobile Arabic styles
- `arabic_localization/` - Arabic number formatting & utilities
- `fixtures/` - Arabic translations and demo data

### Testing Configuration

The system includes comprehensive testing with pytest configuration in `pytest.ini`:
- Test markers: `integration`, `e2e`, `api`, `slow`, `arabic`, `security`, `performance`
- Cross-browser testing for RTL compatibility
- Load testing with concurrent user simulation
- Security validation including authentication and injection testing
- Arabic language stress testing
- Coverage reporting with HTML output
- Parallel test execution for faster development cycles

### Current Development Context

**Branch Status:** Currently on `backup-full-20250704_1334` - a backup/recovery branch used for major system stabilization.

**Recent Architectural Improvements:**
- **Modular Restructuring**: Split large monolithic files into focused modules
- **Complete Dark Mode**: Implemented comprehensive dark mode functionality
- **Enhanced Testing**: Comprehensive pytest configuration with coverage reporting
- **Type Safety**: Added MyPy type checking for better code quality
- **Modern Frontend**: Vue 3 + TypeScript + Vite frontend architecture
- **Production Readiness**: System stabilized from technical emergency state

**Backup Strategy:** Multiple backup versions maintained including:
- `emergency.backup.20250701_232254` - Emergency backup
- `FORENSIC_BACKUP.20250705_235914` - Forensic backup for analysis
- `backup.phase3.20250629_161003` - Phase 3 development backup

### Common Issues & Solutions

**Asset Building:**
- If assets fail to build, check Node.js version (requires 18+)
- Use `yarn` instead of `npm` (configured in package.json)
- Clear cache if encountering build issues: `bench clear-cache`

**Database Issues:**
- Check MariaDB character set supports Arabic: utf8mb4
- Socket timeouts configured to 30s in common_site_config.json
- Use bench migrate for schema changes

**Permission Issues:**
- Universal Workshop implements enhanced role-based permissions
- Check permission hooks in `universal_workshop/user_management/permission_hooks.py`
- Use `bench --site [site] console` to debug permission issues

### Production Considerations

- The system includes Docker configuration for deployment
- Monitoring and alerting configured via deployment scripts
- Backup strategies implemented for automotive data compliance
- Security features include session timeout and MFA capabilities

### Debugging

**Logging:**
- Application logs: `logs/frappe.log`
- Database logs: `logs/database.log`
- Scheduler logs: `logs/scheduler.log`
- Log level configurable in site_config.json

**Development Tools:**
- Live reload enabled for development
- File watcher for automatic asset rebuilding  
- Redis monitoring for queue and cache performance