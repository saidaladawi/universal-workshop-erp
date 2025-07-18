---
description: 
globs: 
alwaysApply: true
---
---
description: Task Master AI workflow integration and module development sequence for Universal Workshop ERP
globs: **/*
alwaysApply: true
---

# Universal Workshop ERP Development Workflow

## **Project Overview**
- **Product**: Universal Workshop ERP v2.0 
- **Lead**: Eng. Saeed Al-Adawi
- **Target**: Arabic-first ERP for Omani automotive workshops
- **Tech Stack**: ERPNext v15.65.2, Frappe Framework
- **Task Management**: Task Master AI with MCP integration

## **Development Workflow Integration**

### **Task Master AI Usage Patterns**
Reference workflow guide: [dev_workflow.md](mdc:.roo/rules/dev_workflow.md)

```bash
# ✅ DO: Start each development session with task review
task-master list --status=pending,in-progress
task-master next

# ✅ DO: Use complexity analysis before implementation
task-master analyze-complexity --research --threshold=7
task-master expand --id=1.1 --force --research
```

### **Arabic Localization Development**
Based on PRD requirements from [prd.txt](mdc:.taskmaster/docs/prd.txt):

```python
# ✅ DO: Log progress in Arabic context
task-master update-subtask --id=1.1 --prompt="
Arabic language setup completed:
- Enabled Arabic in System Settings ✅
- Configured RTL layout support ✅  
- Set up dual language (Arabic/English) ✅
- Regional settings (OMR currency, date formats) ✅
- Tested Arabic character rendering ✅
"

# ✅ DO: Update dependent tasks when implementation changes
task-master update --from=2 --prompt="
Arabic localization foundation is complete. 
All subsequent DocTypes should include:
- Arabic field names with _ar suffix
- English field names with _en suffix  
- Proper RTL layout considerations
- Arabic validation patterns
"
```

### **Module Development Sequence**
Following logical dependency chain from PRD:

1. **Workshop Setup & Configuration** (Task 1)
2. **License Management System** (Task 2) 
3. **Vehicle + Customer Management** (Tasks 3-4, parallel)
4. **Parts Inventory Management** (Task 5)
5. **Workshop Management** (Task 6)
6. **Billing & Financial Management** (Task 7)
7. **Scrap Management** (Task 8)

## **Task Documentation Standards**

### **Subtask Implementation Logging**
```bash
# ✅ DO: Document technical decisions and findings
task-master update-subtask --id=2.3 --prompt="
DocType Creation Progress:
- Created Workshop Profile with Arabic/English fields
- Implemented business license validation logic
- Added automatic workshop code generation
- Fixed RTL form layout issues in JavaScript
- Next: Service Type DocType with pricing matrix
"

# ✅ DO: Capture integration challenges
task-master update-subtask --id=3.2 --prompt="
VIN Decoder Integration Findings:
- Tested multiple Arabic VIN input methods
- Implemented fallback for missing Arabic characters  
- Added manual override for local modifications
- Performance: 3.2s average response time (within spec)
- Ready for production deployment
"
```

### **Research Integration**
```bash
# ✅ DO: Research before major implementations
task-master research --query="ERPNext v15 custom DocType Arabic field best practices" --save-to=2.2

task-master research --query="Frappe framework RTL CSS implementation patterns" --save-to=1.1 --tree

# ✅ DO: Research Oman-specific requirements
task-master research --query="Oman VAT e-invoice QR code generation requirements 2024" --save-to=7.1
```

## **Quality Assurance Workflow**

### **Testing Task Patterns**
```python
# ✅ DO: Create specific test subtasks
task-master add-subtask --parent=2 --title="Arabic Form Validation Testing" --description="
Test all Arabic input fields for:
- Character encoding (UTF-8)
- RTL text display 
- Form submission with Arabic data
- Search functionality with Arabic queries
- Export/import with Arabic content
"

# ✅ DO: Track test results
task-master update-subtask --id=2.6 --prompt="
Arabic Testing Results:
✅ UTF-8 encoding works correctly
✅ RTL display renders properly in all browsers
✅ Form submissions preserve Arabic characters
❌ Search with Arabic diacritics needs improvement
✅ Excel export/import maintains Arabic text integrity
Action: Fix Arabic search_files diacritics handling
"
```

### **Performance Monitoring**
```bash
# ✅ DO: Track performance against acceptance criteria
task-master update-subtask --id=3.1 --prompt="
Performance Test Results vs AC1 (VIN decoder <5 seconds):
- Arabic VIN input: 3.2s average ✅
- English VIN input: 2.8s average ✅
- Mixed character input: 4.1s average ✅
- Error handling: 1.2s average ✅
All acceptance criteria met for VIN decoder performance
"
```

## **Module Integration Patterns**

### **Cross-Module Dependencies**
```bash
# ✅ DO: Update related tasks when module interfaces change
task-master update --from=5 --prompt="
Vehicle Management API changes:
- get_vehicle_details() now returns Arabic owner names
- vehicle_search() supports Arabic license plates
- Added workshop_id parameter to all vehicle queries
Update all dependent modules accordingly
" --research

# ✅ DO: Track integration points
task-master add-task --prompt="
Integration testing between Customer Management and Workshop Management:
- Customer profile Arabic names in service orders
- SMS notifications in Arabic language
- Customer search_files from workshop interface
Priority: high, Dependencies: 3,6
"
```

### **License Management Integration**
```bash
# ✅ DO: Validate license binding across modules
task-master update-subtask --id=8.1 --prompt="
License validation integrated across modules:
- Workshop Profile: Business name binding active ✅
- Customer Management: Hardware fingerprint checked ✅  
- Parts Inventory: Device limits enforced ✅
- All modules: 24-hour validation cycle working ✅
License management successfully integrated system-wide
"
```

## **Deployment Readiness**

### **Go-Live Checklist Task**
```bash
# ✅ DO: Create comprehensive deployment verification
task-master add-task --prompt="
Production deployment checklist for Universal Workshop ERP:
- Arabic language pack fully functional
- All 8 modules integrated and tested
- License management system activated
- Performance benchmarks met (all ACs)
- Oman VAT compliance verified
- User training materials in Arabic/English
- Data migration scripts tested
- Backup/recovery procedures validated
Priority: high, Dependencies: 1,2,3,4,5,6,7,8
"
```

## **File Organization Standards**

```
apps/universal_workshop/
├── universal_workshop/
│   ├── workshop_management/
│   │   ├── doctype/
│   │   └── api/
│   ├── vehicle_management/
│   ├── customer_management/
│   ├── parts_inventory/
│   ├── billing_financial/
│   ├── scrap_management/
│   ├── license_management/
│   └── setup_configuration/
├── translations/
│   ├── ar.csv
│   └── en.csv
└── public/
    ├── js/arabic_utils.js
    └── css/rtl_support.css
```

## **Common Development Anti-Patterns**

```bash
# ❌ DON'T: Work on tasks without updating status
# Always update task status when starting work

# ✅ DO: Follow proper task workflow
task-master set-status --id=3.2 --status=in-progress
# ... do the work ...
task-master update-subtask --id=3.2 --prompt="Implementation complete"
task-master set-status --id=3.2 --status=done

# ❌ DON'T: Skip complexity analysis for large tasks
# ✅ DO: Always analyze and expand complex tasks first
task-master analyze-complexity --id=6 --research
task-master expand --id=6 --force --research

# ❌ DON'T: Implement without researching current best practices  
# ✅ DO: Research before major implementations
task-master research --query="latest ERPNext mobile interface patterns 2024"
```

## **Task Master Configuration**
Reference main config: [config.json](mdc:.taskmaster/config.json)

- **Primary Model**: Optimized for Arabic technical documentation
- **Research Model**: Enabled for real-time best practices
- **Project Context**: Arabic automotive workshop domain
- **Complexity Threshold**: 7+ requires mandatory expansion

## **Integration Points**
- Task management: [tasks.json](mdc:.taskmaster/tasks/tasks.json)
- Project requirements: [prd.txt](mdc:.taskmaster/docs/prd.txt)
- ERPNext development: [erpnext-development.md](mdc:.roo/rules/erpnext-development.md)
- Development workflow: [dev_workflow.md](mdc:.roo/rules/dev_workflow.md)
