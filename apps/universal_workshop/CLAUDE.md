# Universal Workshop App - Claude Memory

This file provides Claude Code with context about the Universal Workshop app specifically.

## App Overview

**Universal Workshop** is a comprehensive Arabic-first ERP solution for Omani automotive workshops built on the Frappe Framework.

### App Structure

```
universal_workshop/
├── universal_workshop/               # Main app package
│   ├── analytics_reporting/         # KPI dashboards and business intelligence
│   ├── analytics_unified/           # Unified analytics interface
│   ├── billing_management/          # Omani VAT compliance, financial reporting
│   ├── communication_management/    # SMS, notifications, customer communication
│   ├── customer_management/         # CRM with Arabic support, loyalty programs
│   ├── customer_portal/             # Self-service customer interface
│   ├── dark_mode/                   # Complete dark mode functionality
│   ├── data_migration/              # Data import/export and migration tools
│   ├── environmental_compliance/    # Environmental regulations compliance
│   ├── license_management/          # Business compliance and licensing
│   ├── marketplace_integration/     # Third-party marketplace connections
│   ├── mobile_operations/           # Mobile-first operational interfaces
│   ├── parts_inventory/             # Inventory management with barcode scanning
│   ├── purchasing_management/       # Supplier management and procurement
│   ├── sales_service/               # Sales order management and service delivery
│   ├── scrap_management/            # Scrap and waste management processes
│   ├── search_integration/          # Advanced search and indexing capabilities
│   ├── setup/                       # Initial system setup and configuration
│   ├── system_administration/       # System configuration and management
│   ├── training_management/         # Technician training and certification
│   ├── user_management/             # Enhanced security, session management
│   ├── vehicle_management/          # VIN decoding, vehicle registry
│   ├── workshop_management/         # Core workshop operations, service orders
│   ├── workshop_operations/         # Advanced workshop workflow management
│   ├── api/                         # REST API endpoints
│   └── utilities/                   # Helper functions and utilities
├── frontend_v2/                     # Modern Vue 3 + TypeScript frontend
└── docs/                            # Documentation and guides
```

### Key Features

- **Arabic-First**: RTL support, Arabic number formatting, Arabic translations
- **Automotive Focus**: VIN decoding, parts management, service tracking
- **Omani Compliance**: VAT (5%) compliance, QR code invoicing
- **Modern Architecture**: Vue 3 + TypeScript frontend, Python backend
- **Mobile Ready**: PWA capabilities, mobile-first design
- **Dark Mode**: Complete dark mode implementation
- **Advanced Analytics**: Real-time KPIs, business intelligence

### Technical Details

- **DocTypes**: 254 definitions
- **Python Controllers**: 429 files
- **JavaScript Clients**: 100 files
- **Modules**: 24 functional modules
- **Frontend**: Vue 3 + TypeScript + Vite (frontend_v2)
- **Backend**: Python 3.10+ with Frappe Framework
- **Database**: MariaDB with Arabic character support

### Development Commands

```bash
# App-specific development
cd apps/universal_workshop

# Frontend development (Vue 3)
cd frontend_v2
npm run dev              # Start development server
npm run build           # Production build
npm run type-check      # TypeScript checking
npm run lint            # ESLint + Prettier

# Python development
ruff check              # Lint Python code
ruff format            # Format Python code
pytest                 # Run tests
```

### App Configuration

- **hooks.py**: App hooks and event handlers
- **modules.txt**: 24 module definitions
- **pyproject.toml**: Python configuration (Ruff, MyPy, Pytest)
- **requirements.txt**: Python dependencies
- **frontend_v2/package.json**: Frontend dependencies

### Arabic/RTL Support

- Complete RTL layout support
- Arabic number formatting
- RTL-aware CSS components
- Arabic translations and localization
- Mobile-first Arabic interface

### Production Status

- **Status**: Production-ready and stable
- **Recent**: Architectural improvements and stabilization
- **Testing**: Comprehensive test suite with coverage
- **Quality**: Linting, type checking, and code formatting

This app is the core of the Universal Workshop ERP system, providing comprehensive automotive workshop management with Arabic-first design and modern architecture.