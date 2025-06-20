---
description: 
globs: 
alwaysApply: true
---
# Python, Frappe & ERPNext Best Practices Guide

Based on [official ERPNext Coding Standards](mdc:https:/github.com/frappe/erpnext/wiki/Coding-Standards) and practical experience from Universal Workshop ERP development.

## **Python Code Quality Standards**

### **Import Organization**
```python
# ✅ DO: Organize imports in standard order
import json
import re
from datetime import datetime
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate

# ❌ DON'T: Mix standard and third-party imports
import frappe, json, re  # Avoid comma-separated imports
```

### **Translation Handling**
```python
# ✅ DO: Always wrap user-facing strings with _()
frappe.throw(_("Arabic technician name is required"))
frappe.msgprint(_("Workshop profile created successfully"))

# ❌ DON'T: Use hardcoded strings
frappe.throw("Arabic technician name is required")  # Not translatable

# ✅ DO: Import translation function properly
from frappe import _

# ❌ DON'T: Use _() without importing
# Will cause F821 (undefined name) error
```

### **Exception Handling**
```python
# ✅ DO: Use specific exception types
try:
    result = frappe.db.sql("SELECT * FROM tabCustomer")
except frappe.ValidationError as e:
    frappe.log_error(f"Validation error: {e}")
except Exception as e:
    frappe.log_error(f"Unexpected error: {e}")

# ❌ DON'T: Use bare except statements
try:
    risky_operation()
except:  # This will cause E722 error
    pass
```

### **SQL Query Best Practices**
```python
# ✅ DO: Use parameterized queries (injection-safe)
customers = frappe.db.sql("""
    SELECT name, customer_name, customer_name_ar
    FROM `tabCustomer`
    WHERE disabled = %s
    AND customer_group = %s
""", [0, customer_group], as_dict=True)

# ❌ DON'T: Use string formatting (SQL injection risk)
customers = frappe.db.sql(f"""
    SELECT * FROM tabCustomer 
    WHERE name = '{customer_name}'
""")  # Dangerous!

# ✅ DO: Handle empty results properly
result = frappe.db.sql("SELECT COUNT(*) FROM tabItem", as_list=True)
count = result[0][0] if result else 0

# ❌ DON'T: Directly access tuple results
count = frappe.db.sql("SELECT COUNT(*) FROM tabItem")[0][0]  # Can fail
```

## **Frappe Framework Patterns**

### **DocType Controller Best Practices**
```python
class WorkshopProfile(Document):
    # ✅ DO: Add pylint disable for dynamic fields
    # pylint: disable=no-member
    # Frappe framework dynamically adds DocType fields to Document class
    
    def validate(self):
        """Validate workshop data before saving"""
        self.validate_arabic_name()
        self.validate_business_license()
        self.set_default_values()
    
    def validate_arabic_name(self):
        """Ensure Arabic workshop name is provided"""
        if not self.workshop_name_ar:
            frappe.throw(_("Arabic workshop name is required"))
    
    def before_save(self):
        """Set default values before saving"""
        if not self.created_by:
            self.created_by = frappe.session.user
        if not self.created_date:
            self.created_date = frappe.utils.today()
```

### **WhiteListed Methods**
```python
# ✅ DO: Properly whitelist API methods
@frappe.whitelist()
def get_workshop_services(workshop_code, language='en'):
    """Get workshop services with Arabic/English support"""
    
    # Validate input parameters
    if not workshop_code:
        frappe.throw(_("Workshop code is required"))
    
    # Use proper field selection
    fields = ['name', 'service_name', 'price']
    if language == 'ar':
        fields.extend(['service_name_ar', 'description_ar'])
    
    return frappe.get_list('Workshop Service', 
                          filters={'workshop': workshop_code}, 
                          fields=fields)

# ❌ DON'T: Forget @frappe.whitelist() decorator
def get_customer_data():  # Not accessible via API
    return frappe.get_list('Customer')
```

### **Database Operations**
```python
# ✅ DO: Use Frappe's database API methods
# Get single value
customer_name = frappe.db.get_value('Customer', customer_id, 'customer_name')

# Get multiple values
customer_data = frappe.db.get_value('Customer', customer_id, 
                                   ['customer_name', 'phone', 'email'], as_dict=True)

# Get list with filters
active_items = frappe.get_list('Item', 
                               filters={'disabled': 0, 'is_stock_item': 1},
                               fields=['item_code', 'item_name', 'standard_rate'])

# ❌ DON'T: Use raw SQL when Frappe APIs exist
customer_name = frappe.db.sql("SELECT customer_name FROM tabCustomer WHERE name = %s", [customer_id])[0][0]
```

## **ERPNext-Specific Guidelines**

### **DocType Field Naming Conventions**
```json
{
  "fieldname": "customer_name",          // English field
  "fieldname": "customer_name_ar",       // Arabic field with _ar suffix
  "fieldname": "phone_oman",            // Country-specific fields
  "fieldname": "vat_number_oman",       // Regional compliance
  "fieldname": "created_by",            // Standard metadata fields
  "fieldname": "created_date"
}
```

### **Arabic Localization Patterns**
```python
# ✅ DO: Dual language field validation
def validate_customer_names(self):
    """Validate both English and Arabic customer names"""
    if not self.customer_name:
        frappe.throw(_("Customer name (English) is required"))
    if not self.customer_name_ar:
        frappe.throw(_("Customer name (Arabic) is required"))

# ✅ DO: Regional validation for Oman
def validate_oman_business_license(self):
    """Validate Oman business license format (7 digits)"""
    if self.business_license and not re.match(r'^\d{7}$', self.business_license):
        frappe.throw(_("Business License must be 7 digits for Oman"))

def validate_oman_phone(self):
    """Validate Oman phone number format"""
    if self.phone and not self.phone.startswith('+968'):
        frappe.throw(_("Phone number must start with +968 for Oman"))
```

### **Currency and VAT Handling**
```python
# ✅ DO: Proper OMR currency formatting
def format_omr_currency(amount, precision=3):
    """Format currency for Oman market (OMR with 3 decimal places)"""
    return f"OMR {amount:,.{precision}f}"

# ✅ DO: 5% VAT calculation for Oman
def calculate_oman_vat(base_amount):
    """Calculate 5% VAT as per Oman Tax Authority"""
    vat_rate = 5.0
    vat_amount = (base_amount * vat_rate) / 100
    return {
        'base_amount': flt(base_amount, 3),
        'vat_rate': vat_rate,
        'vat_amount': flt(vat_amount, 3),
        'total_amount': flt(base_amount + vat_amount, 3)
    }
```

## **Code Structure & Organization**

### **Function Organization**
```python
# ✅ DO: Order functions with calling function on top
def process_service_order(service_order_id):
    """Main processing function"""
    validate_service_order(service_order_id)
    assign_technician(service_order_id)
    update_inventory(service_order_id)

def validate_service_order(service_order_id):
    """Validation helper function"""
    pass

def assign_technician(service_order_id):
    """Assignment helper function"""
    pass

def update_inventory(service_order_id):
    """Inventory update helper function"""
    pass
```

### **Function Length Guidelines**
```python
# ✅ DO: Keep functions under 10 lines when possible
def get_customer_balance(customer_id):
    """Get customer outstanding balance"""
    balance = frappe.db.sql("""
        SELECT SUM(outstanding_amount)
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1
    """, [customer_id])[0][0] or 0
    return flt(balance, 2)

# ❌ DON'T: Create overly long functions
def process_everything():  # 50+ lines doing multiple things
    # Break this into smaller, focused functions
    pass
```

### **Class Design Patterns**
```python
class TechnicianAssignmentAlgorithm:
    """Encapsulate related functionality in classes"""
    
    def __init__(self, service_order_id):
        self.service_order_id = service_order_id
        self.service_order = frappe.get_doc('Service Order', service_order_id)
    
    def find_best_technician(self):
        """Main algorithm entry point"""
        available_techs = self.get_available_technicians()
        scored_techs = self.score_technicians(available_techs)
        return self.select_best_match(scored_techs)
    
    def get_available_technicians(self):
        """Get list of available technicians"""
        pass
    
    def score_technicians(self, technicians):
        """Score technicians based on skills and availability"""
        pass
```

## **Error Prevention Patterns**

### **Common Anti-Patterns to Avoid**
```python
# ❌ DON'T: Hardcode values
workshop_status = "مكتمل"  # Use _("Completed") instead

# ❌ DON'T: Ignore text direction in mixed content
address_display = f"{english_part} {arabic_part}"  # Consider RTL

# ❌ DON'T: Use deprecated Frappe APIs
cur_frm.set_value()  # Use frappe.form.set_value() instead

# ❌ DON'T: Forget error handling in API calls
customer = frappe.get_doc('Customer', customer_id)  # Can throw exception

# ✅ DO: Proper error handling
try:
    customer = frappe.get_doc('Customer', customer_id)
except frappe.DoesNotExistError:
    frappe.throw(_("Customer {0} not found").format(customer_id))
```

### **Performance Best Practices**
```python
# ✅ DO: Use bulk operations for large datasets
frappe.db.bulk_insert('Customer Log', [
    {'customer': 'CUST-001', 'action': 'created'},
    {'customer': 'CUST-002', 'action': 'updated'},
    # ... many records
])

# ❌ DON'T: Loop with individual database calls
for record in large_dataset:
    frappe.db.sql("INSERT INTO ...", [record])  # Slow

# ✅ DO: Use appropriate indexes
frappe.db.add_index('Customer', ['customer_name_ar', 'phone'])

# ✅ DO: Limit query results
recent_orders = frappe.get_list('Sales Order', 
                               filters={'creation': ['>', '2024-01-01']},
                               limit=100)
```

## **JavaScript Best Practices**

### **Frappe Form Events**
```javascript
// ✅ DO: Organize form events properly
frappe.ui.form.on('Workshop Profile', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        ['workshop_name_ar', 'address_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
            }
        });
    },
    
    workshop_name: function(frm) {
        // Auto-suggest Arabic name when English name is entered
        if (frm.doc.workshop_name && !frm.doc.workshop_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    }
});

// ❌ DON'T: Put all logic in refresh event
frappe.ui.form.on('Workshop Profile', {
    refresh: function(frm) {
        // 100+ lines of mixed logic here
    }
});
```

### **API Calls in JavaScript**
```javascript
// ✅ DO: Proper error handling in JS API calls
frappe.call({
    method: 'universal_workshop.api.get_workshop_services',
    args: {
        workshop_code: frm.doc.workshop_code,
        language: frappe.boot.lang || 'en'
    },
    callback: function(r) {
        if (r.message) {
            // Handle success
            frm.set_value('services', r.message);
        }
    },
    error: function(xhr) {
        frappe.msgprint(__('Failed to load workshop services'));
    }
});
```

## **Testing Patterns**

### **Unit Test Structure**
```python
# ✅ DO: Comprehensive test coverage
import unittest
import frappe
from universal_workshop.workshop_management.doctype.technician.technician import Technician

class TestTechnician(unittest.TestCase):
    def setUp(self):
        """Setup test data"""
        self.test_technician_data = {
            'employee_id': 'EMP-TEST-001',
            'technician_name': 'Ahmed Al-Rashid',
            'technician_name_ar': 'أحمد الراشد',
            'phone': '+968 24123456',
            'department': 'Engine',
            'employment_status': 'Active'
        }
    
    def test_technician_creation(self):
        """Test basic technician creation"""
        tech = frappe.new_doc('Technician')
        tech.update(self.test_technician_data)
        tech.insert()
        
        self.assertEqual(tech.technician_name_ar, 'أحمد الراشد')
        self.assertTrue(tech.employee_id.startswith('EMP-'))
    
    def test_arabic_name_validation(self):
        """Test Arabic name requirement"""
        tech = frappe.new_doc('Technician')
        tech.update(self.test_technician_data)
        tech.technician_name_ar = ''  # Remove Arabic name
        
        with self.assertRaises(frappe.ValidationError):
            tech.insert()
    
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()
```

## **Documentation Standards**

### **Docstring Patterns**
```python
def calculate_service_cost(service_type, labor_hours, parts_cost=0):
    """
    Calculate total service cost including labor and parts.
    
    Args:
        service_type (str): Type of service (Engine, Transmission, etc.)
        labor_hours (float): Number of labor hours required
        parts_cost (float, optional): Cost of parts used. Defaults to 0.
    
    Returns:
        dict: Dictionary containing:
            - labor_cost (float): Cost of labor
            - parts_cost (float): Cost of parts
            - total_cost (float): Total service cost including VAT
            - vat_amount (float): VAT amount (5% for Oman)
    
    Raises:
        ValidationError: If service_type is not valid
        ValidationError: If labor_hours is negative
    
    Example:
        >>> calculate_service_cost('Engine', 2.5, 150.0)
        {
            'labor_cost': 50.0,
            'parts_cost': 150.0,
            'total_cost': 210.0,
            'vat_amount': 10.0
        }
    """
    # Implementation here
    pass
```

## **File References**

- ERPNext development patterns: [erpnext-development.md](mdc:.roo/rules/erpnext-development.md)
- Arabic localization: [arabic-localization.md](mdc:.roo/rules/arabic-localization.md)
- Task management workflow: [dev_workflow.md](mdc:.roo/rules/dev_workflow.md)
- Universal Workshop PRD: [prd.txt](mdc:.taskmaster/docs/prd.txt)
- Project tasks: [tasks.json](mdc:.taskmaster/tasks/tasks.json)

## **IDE Configuration**

### **VS Code Settings for Frappe Development**
```json
{
    "python.linting.pylintArgs": [
        "--disable=no-member",
        "--disable=import-error",
        "--load-plugins=frappe.linting"
    ],
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "files.associations": {
        "*.md": "markdown"
    }
}
```

Remember: These patterns prevent the 101+ linting errors we encountered in Universal Workshop ERP. Following these guidelines ensures clean, maintainable, and error-free Frappe/ERPNext applications.
