# 🚗 Universal Workshop ERP

**Arabic-First Automotive Workshop Management System**

A comprehensive ERP solution designed specifically for Omani automotive workshops, built on ERPNext v15.65.2 with native Arabic support, Islamic business principles, and traditional business patterns.

---

## 🌟 **Key Features**

### **🌍 Arabic-First Design**
- **Native RTL Support** - Right-to-left interface with Arabic typography
- **Bilingual Excellence** - Seamless Arabic-English switching
- **Cultural Intelligence** - Traditional Arabic business patterns and Islamic compliance
- **Omani Integration** - Local regulatory compliance and business customs

### **🔧 Workshop Management**
- **Service Orders** - Complete service lifecycle management
- **Vehicle Registry** - VIN decoding and service history
- **Parts Inventory** - Arabic parts database with barcode scanning
- **Technician Management** - Skill tracking and Islamic compliance
- **Quality Control** - Cultural appropriateness validation

### **💰 Financial Management**
- **Omani VAT Compliance** - 5% VAT with QR invoice generation
- **Islamic Finance** - Religious business principle compliance
- **Arabic Invoicing** - Traditional Arabic billing patterns
- **Multi-currency** - Support for OMR, USD, EUR with Arabic formatting

### **📱 Mobile & PWA**
- **Arabic Mobile Interface** - Cultural mobile patterns
- **Progressive Web App** - Offline capability with Arabic support
- **Technician Portal** - Mobile-first interface for workshop floor
- **Customer Portal** - Self-service with Arabic excellence

---

## 🏗️ **Architecture**

### **Current Status: 24-Module Stable Architecture**
Universal Workshop uses a **validated 24-module architecture** that has been thoroughly tested and proven effective in production environments.

```
Core Services (7 modules):
├── Analytics Reporting & Analytics Unified
├── Mobile Operations & System Administration  
├── Search Integration & Dark Mode
└── Data Migration

Workshop Operations (8 modules):
├── License Management & Customer Management
├── Communication Management & Customer Portal
├── Vehicle Management & Workshop Management
├── Workshop Operations & Sales Service
└── Training Management

Financial & Inventory (6 modules):
├── Billing Management & Parts Inventory
├── Purchasing Management & Scrap Management
├── Marketplace Integration & User Management

System Infrastructure (3 modules):
├── Environmental Compliance & Setup
└── Additional system modules
```

### **📚 Shared Libraries**
Built-in reusable business logic libraries:
- **Arabic Business Logic** - Cultural validation and text processing
- **Financial Compliance** - VAT calculation and Islamic finance
- **Workshop Operations** - Service scheduling and workflow
- **Inventory Management** - Stock validation and barcode operations
- **Traditional Workflows** - Islamic business compliance
- **Database Optimization** - Query optimization and caching

---

## 🚀 **Installation**

### **Prerequisites**
- ERPNext v15.65.2 or higher
- Python 3.10+
- Node.js 18+
- MariaDB with Arabic character support

### **Installation Steps**

```bash
# 1. Get the app
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/[repo-url] --branch main
bench install-app universal_workshop

# 2. Setup Arabic support
bench --site [site-name] migrate
bench --site [site-name] clear-cache

# 3. Start development
bench start
```

### **Development Setup**

```bash
# Install development dependencies
cd apps/universal_workshop
pre-commit install

# Start with hot reload
bench watch

# Run tests
bench run-tests --app universal_workshop

# Code quality
ruff check
ruff format
```

---

## 📖 **Documentation**

### **📋 For Developers**
- [Architecture Decision Record](ARCHITECTURE_DECISION_RECORD.md) - Current architectural decisions
- [Shared Libraries Usage Guide](docs/SHARED_LIBRARIES_USAGE_GUIDE.md) - How to use built libraries
- [Deep Integration Review](docs/deep_integration_review.md) - System analysis and recommendations
- [Task Execution Plan](docs/task_execution_plan.md) - Project status and next steps

### **📚 For Users**
- [Installation Guide](docs/installation_guide.md) - Detailed setup instructions
- [User Guide](docs/user_guide.md) - How to use the system
- [API Documentation](docs/README_API_CONFIG.md) - API reference

### **🔧 For System Administrators**
- [Performance Optimization](docs/fixes/performance_optimizations_to_apply.md) - Available optimizations
- [Smart Fixes Summary](docs/fixes/SMART_FIXES_SUMMARY.md) - Applied improvements

---

## 🔧 **Development Guidelines**

### **✅ Best Practices**
- **Use Shared Libraries** - Prevent code duplication
- **Arabic-First** - All features must support Arabic properly
- **Islamic Compliance** - Follow religious business principles
- **Cultural Appropriateness** - Validate against traditional patterns
- **Performance First** - Consider Arabic interface performance

### **🛠️ Development Commands**

```bash
# Development server
bench start                    # All services
bench serve --port 8000       # Web server only

# Asset building
bench watch                    # Development mode with auto-rebuild
bench build                    # Production build

# Testing
bench run-tests --app universal_workshop
bench run-ui-tests
bench --site [site] run-tests

# Code quality
ruff check                     # Python linting
ruff format                    # Python formatting

# Database operations
bench --site [site] migrate
bench --site [site] backup
bench clear-cache
```

---

## 🤝 **Contributing**

### **Code Quality Tools**
- **ruff** - Python linting and formatting
- **eslint** - JavaScript linting  
- **prettier** - Code formatting
- **pyupgrade** - Python syntax modernization

### **CI/CD**
- **GitHub Actions** - Automated testing on push to main
- **Semgrep Rules** - Security and quality checks
- **pip-audit** - Security vulnerability scanning

### **Pull Request Guidelines**
1. Use shared libraries for new functionality
2. Ensure Arabic interface support
3. Test cultural appropriateness
4. Include performance considerations
5. Update documentation

---

## 🎯 **Current Focus**

### **✅ Completed**
- 24-module architecture validated
- 6 shared libraries built and ready
- Performance optimization strategies documented
- Arabic excellence framework established

### **🚀 Immediate Priorities**
1. **Feature Development** - Complete remaining features in existing modules
2. **User Experience** - Improve Arabic mobile interface
3. **Performance** - Apply optimizations when needed
4. **Documentation** - Enhance user guides

### **📈 Future Roadmap**
- Enhanced Arabic localization
- Advanced Islamic business features
- Mobile performance optimization
- Customer portal improvements

---

## 📊 **Performance & Metrics**

### **Current Baseline**
- ✅ **24 Active Modules** - All functional and serving business needs
- ✅ **208 DocTypes** - Supporting comprehensive workshop management
- ✅ **Acceptable Performance** - All benchmarks passing
- ✅ **User Satisfaction** - No complaints, system in active use

### **Available Optimizations**
- **Database Queries** - 70% improvement potential available
- **Asset Loading** - 95% reduction in HTTP requests possible
- **Memory Usage** - 50% reduction potential documented
- **Mobile Performance** - 97% improvement strategies ready

---

## 📄 **License**

MIT License - See [LICENSE](LICENSE) file for details

---

## 🆘 **Support & Community**

- **Documentation** - Check `/docs` folder for comprehensive guides
- **Issues** - Report bugs and feature requests in GitHub Issues
- **Development** - See contribution guidelines above

---

**Built with ❤️ for the Omani automotive industry** 🇴🇲