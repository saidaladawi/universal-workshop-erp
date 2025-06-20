---
description: 
globs: 
alwaysApply: true
---
---
description: ERPNext v15 development patterns and Arabic localization for Universal Workshop ERP
globs: apps/universal_workshop/**/*.py, apps/universal_workshop/**/*.js, apps/universal_workshop/**/*.json
alwaysApply: true
---

# ERPNext v15 Development Guide

## **Project Context**
- **Universal Workshop ERP**: Arabic-first ERP solution for Omani automotive workshops
- **Base Framework**: ERPNext v15.65.2 with Frappe v15 framework
- **Localization**: Arabic/English dual language with RTL support
- **Target Market**: Automotive repair workshops in Oman

## **Custom App Development Best Practices**

### **App Creation & Structure**
```bash
# ✅ DO: Follow Frappe v15 app creation pattern
bench new-app universal_workshop
App Title: Universal Workshop
App Description: Arabic-first ERP for Omani automotive workshops
App Publisher: Eng. Saeed Al-Adawi
App Email: saeed@universal-workshop.om
App License: MIT
```

### **App Directory Structure (ERPNext v15)**
```
apps/universal_workshop/
├── MANIFEST.in
├── README.md
├── setup.py
├── requirements.txt              # Python dependencies
├── dev-requirements.txt          # Development dependencies 
├── package.json                  # Node.js dependencies
├── universal_workshop/
│   ├── __init__.py              # App version: __version__ = '1.0.0'
│   ├── hooks.py                 # Frappe hooks configuration
│   ├── modules.txt              # App modules list
│   ├── patches.txt              # Database migration patches
│   ├── config/
│   │   ├── desktop.py           # Desktop workspace configuration
│   │   └── docs.py              # Documentation configuration
│   ├── public/                  # Static assets (CSS, JS, Images)
│   ├── templates/               # Jinja2 templates
│   ├── www/                     # Portal/website pages
│   └── universal_workshop/      # Main app module
│       └── doctype/             # Custom DocTypes
```

## **DocType Development**

### **Custom DocType Creation**
```python
# ✅ DO: Follow ERPNext v15 naming conventions (singular names)
# apps/universal_workshop/universal_workshop/doctype/workshop_profile/workshop_profile.py
import frappe
from frappe.model.document import Document

class WorkshopProfile(Document):
    # ERPNext v15 uses explicit typing
    def validate(self):
        """Validate workshop business license and Arabic name"""
        self.validate_business_license()
        self.validate_arabic_name()
        
    def validate_business_license(self):
        """Validate Oman business license format"""
        if self.business_license:
            # Oman business license format: 1234567
            if not re.match(r'^\d{7}$', self.business_license):
                frappe.throw(_("Business License must be 7 digits"))
                
    def validate_arabic_name(self):
        """Ensure Arabic workshop name is provided"""
        if not self.workshop_name_ar:
            frappe.throw(_("Arabic workshop name is required"))

    def before_save(self):
        """Auto-generate workshop code"""
        if not self.workshop_code:
            self.workshop_code = self.generate_workshop_code()
            
    def generate_workshop_code(self):
        """Generate workshop code: WS-YYYY-0001"""
        from datetime import datetime
        year = datetime.now().year
        
        # Get last workshop number for current year
        last_workshop = frappe.db.sql("""
            SELECT workshop_code FROM `tabWorkshop Profile`
            WHERE workshop_code LIKE 'WS-{}-%%'
            ORDER BY creation DESC LIMIT 1
        """.format(year))
        
        if last_workshop:
            last_num = int(last_workshop[0][0].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"WS-{year}-{new_num:04d}"
```

### **ERPNext v15 Hooks Configuration**
```python
# ✅ DO: hooks.py - ERPNext v15 best practices
from frappe import _
from . import __version__ as app_version

# Required App Metadata
app_name = "universal_workshop"
app_title = "Universal Workshop"
app_publisher = "Eng. Saeed Al-Adawi"
app_description = "Arabic-first ERP for Omani automotive workshops"
app_email = "saeed@universal-workshop.om"
app_license = "MIT"
app_version = app_version

# Required apps - ERPNext dependency
required_apps = ["erpnext"]

# Fixtures for data migration
fixtures = [
    "Custom Field",
    "Property Setter", 
    "Custom DocPerm",
    "Translation",
    {"dt": "User Role", "filters": [["role", "like", "Workshop%"]]},
]

# Arabic/RTL Assets
app_include_css = [
    "/assets/universal_workshop/css/arabic-rtl.css",
    "/assets/universal_workshop/css/workshop-theme.css"
]

app_include_js = [
    "/assets/universal_workshop/js/arabic-utils.js",
    "/assets/universal_workshop/js/workshop-common.js"
]

# DocType customizations
doctype_js = {
    "Customer": "public/js/customer.js",
    "Item": "public/js/item.js",
    "Sales Invoice": "public/js/sales_invoice.js"
}

# Document event hooks
doc_events = {
    "Sales Invoice": {
        "before_save": "universal_workshop.overrides.sales_invoice.before_save",
        "on_submit": "universal_workshop.overrides.sales_invoice.create_work_order"
    },
    "Customer": {
        "after_insert": "universal_workshop.overrides.customer.create_vehicle_profile"
    }
}

# Background jobs
scheduler_events = {
    "daily": [
        "universal_workshop.tasks.send_service_reminders",
        "universal_workshop.tasks.update_vehicle_service_history"
    ],
    "weekly": [
        "universal_workshop.tasks.generate_workshop_reports"
    ]
}

# Override WhiteList methods for Arabic support
override_whitelisted_methods = {
    "frappe.desk.search_files.search_link": "universal_workshop.api.arabic_search_link"
}

# Translation support
translate_languages = ["ar", "en"]

# Website settings for Arabic
website_context = {
    "favicon": "/assets/universal_workshop/images/favicon.png",
    "splash_image": "/assets/universal_workshop/images/workshop-splash.jpg"
}

# Jinja methods for Arabic formatting
jinja = {
    "methods": [
        "universal_workshop.utils.format_arabic_date",
        "universal_workshop.utils.format_omr_currency",
        "universal_workshop.utils.get_arabic_number"
    ]
}

# Portal menu for workshop customers
standard_portal_menu_items = [
    {"title": _("My Vehicles"), "route": "/my-vehicles", "role": "Customer"},
    {"title": _("Service History"), "route": "/service-history", "role": "Customer"},
    {"title": _("Appointments"), "route": "/appointments", "role": "Customer"}
]
```

## **Arabic/RTL Form Handling**

### **Client-Side JavaScript (ERPNext v15)**
```javascript
// ✅ DO: public/js/workshop_profile.js
frappe.ui.form.on('Workshop Profile', {
    refresh: function(frm) {
        // Add Arabic form enhancements
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_rtl_layout');
    },
    
    setup_arabic_fields: function(frm) {
        // Auto-direction for Arabic fields
        ['workshop_name_ar', 'address_ar', 'description_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },
    
    setup_rtl_layout: function(frm) {
        // RTL layout for Arabic locale
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },
    
    workshop_name: function(frm) {
        // Auto-generate Arabic transliteration if needed
        if (frm.doc.workshop_name && !frm.doc.workshop_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },
    
    suggest_arabic_name: function(frm) {
        frappe.call({
            method: 'universal_workshop.api.get_arabic_transliteration',
            args: {
                english_text: frm.doc.workshop_name
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value('workshop_name_ar', r.message);
                }
            }
        });
    }
});

// Arabic number formatting
frappe.ui.form.on('Workshop Profile', 'onload', function(frm) {
    // Format numbers for Arabic locale
    if (frappe.boot.lang === 'ar') {
        frm.fields_dict.phone_number.$input.on('input', function() {
            let value = $(this).val();
            // Convert to Arabic-Indic numerals if needed
            $(this).val(convert_to_arabic_numerals(value));
        });
    }
});

function convert_to_arabic_numerals(englishNum) {
    const arabicNumbers = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    return englishNum.replace(/[0-9]/g, function(w) {
        return arabicNumbers[+w];
    });
}
```

## **Database Schema Patterns**

### **Arabic-Friendly DocType Fields**
```json
{
    "fields": [
        {
            "fieldname": "workshop_name",
            "fieldtype": "Data",
            "label": "Workshop Name (English)",
            "reqd": 1,
            "in_list_view": 1
        },
        {
            "fieldname": "workshop_name_ar", 
            "fieldtype": "Data",
            "label": "اسم الورشة",
            "translatable": 1,
            "reqd": 1,
            "in_list_view": 1
        },
        {
            "fieldname": "business_license",
            "fieldtype": "Data",
            "label": "Business License (Oman)",
            "unique": 1,
            "reqd": 1
        },
        {
            "fieldname": "vat_number",
            "fieldtype": "Data", 
            "label": "VAT Registration Number",
            "description": "5% VAT - Oman Tax Authority"
        },
        {
            "fieldname": "phone_oman",
            "fieldtype": "Data",
            "label": "Phone Number (+968)",
            "options": "Phone"
        }
    ]
}
```

## **API Development**

### **WhiteListed Methods with Arabic Support**
```python
# ✅ DO: universal_workshop/api.py
import frappe
from frappe import _

@frappe.whitelist()
def get_workshop_services(workshop_code, language='en'):
    """Get workshop services with Arabic/English support"""
    
    fields = ['name', 'service_name', 'service_name_ar', 'price', 'duration']
    if language == 'ar':
        fields.append('description_ar as description')
    else:
        fields.append('description')
        
    services = frappe.get_list(
        'Workshop Service',
        filters={'workshop': workshop_code, 'is_active': 1},
        fields=fields,
        order_by='service_name'
    )
    
    return services

@frappe.whitelist()
def create_service_appointment(customer, workshop, vehicle, service_date, services):
    """Create service appointment with Arabic support"""
    
    # Validate Oman working days (Sunday-Thursday)
    import datetime
    service_date_obj = datetime.datetime.strptime(service_date, '%Y-%m-%d')
    if service_date_obj.weekday() in [4, 5]:  # Friday, Saturday
        frappe.throw(_("Service appointments not available on weekends"))
    
    appointment = frappe.new_doc('Service Appointment')
    appointment.customer = customer
    appointment.workshop = workshop  
    appointment.vehicle = vehicle
    appointment.appointment_date = service_date
    appointment.services = services
    appointment.status = 'Scheduled'
    appointment.insert()
    
    return appointment.name

@frappe.whitelist()
def get_arabic_transliteration(english_text):
    """Simple English to Arabic transliteration helper"""
    # This would integrate with a transliteration service
    # For now, return placeholder
    return f"<Arabic for: {english_text}>"
```

## **Testing Patterns**

### **Arabic Content Unit Tests**
```python
# ✅ DO: tests/test_workshop_profile.py
import unittest
import frappe
from universal_workshop.universal_workshop.doctype.workshop_profile.workshop_profile import WorkshopProfile

class TestWorkshopProfile(unittest.TestCase):
    
    def setUp(self):
        """Setup test data"""
        self.test_workshop_data = {
            'workshop_name': 'Al Khaleej Auto Service',
            'workshop_name_ar': 'خدمة الخليج للسيارات',
            'business_license': '1234567',
            'vat_number': 'OM1234567890123',
            'phone_oman': '+968 24 123456'
        }
    
    def test_workshop_creation_with_arabic(self):
        """Test workshop creation with Arabic fields"""
        workshop = frappe.new_doc('Workshop Profile')
        workshop.update(self.test_workshop_data)
        workshop.insert()
        
        self.assertEqual(workshop.workshop_name_ar, 'خدمة الخليج للسيارات')
        self.assertTrue(workshop.workshop_code.startswith('WS-'))
        
    def test_business_license_validation(self):
        """Test Oman business license validation"""
        workshop = frappe.new_doc('Workshop Profile')
        workshop.update(self.test_workshop_data)
        workshop.business_license = '123'  # Invalid format
        
        with self.assertRaises(frappe.ValidationError):
            workshop.insert()
            
    def test_arabic_name_required(self):
        """Test Arabic name requirement"""
        workshop = frappe.new_doc('Workshop Profile')
        workshop.update(self.test_workshop_data)
        workshop.workshop_name_ar = ''  # Empty Arabic name
        
        with self.assertRaises(frappe.ValidationError):
            workshop.insert()
```

## **Migration & Deployment**

### **Patch Files for Updates**
```python
# ✅ DO: patches/v1_0/setup_arabic_translations.py
import frappe

def execute():
    """Setup Arabic translations for Universal Workshop"""
    
    # Create custom translations
    translations = [
        {'language': 'ar', 'source_text': 'Workshop Profile', 'translated_text': 'ملف الورشة'},
        {'language': 'ar', 'source_text': 'Service History', 'translated_text': 'تاريخ الخدمة'},
        {'language': 'ar', 'source_text': 'Vehicle Details', 'translated_text': 'تفاصيل المركبة'},
    ]
    
    for translation in translations:
        if not frappe.db.exists('Translation', 
                               {'language': translation['language'], 
                                'source_text': translation['source_text']}):
            doc = frappe.new_doc('Translation')
            doc.update(translation)
            doc.insert()
    
    frappe.db.commit()
    frappe.clear_cache()
```

## **Error Handling & Logging**

### **Arabic-Aware Error Messages** 
```python
# ✅ DO: utils/error_handling.py
import frappe
from frappe import _

def validate_oman_vat_number(vat_number):
    """Validate Oman VAT number format"""
    if not vat_number:
        return True
        
    # Oman VAT format: OM followed by 15 digits
    if not re.match(r'^OM\d{15}$', vat_number):
        frappe.throw(_("Invalid Oman VAT number format. Should be OMxxxxxxxxxxxxxxx"))
        
    return True

def validate_oman_phone(phone_number):
    """Validate Oman phone number"""
    if not phone_number:
        return True
        
    # Oman phone: +968 followed by 8 digits
    if not re.match(r'^\+968\s?\d{8}$', phone_number):
        frappe.throw(_("Invalid Oman phone number. Format: +968 XXXXXXXX"))
        
    return True

class WorkshopException(frappe.ValidationError):
    """Custom exception for workshop-specific errors"""
    pass
```

## **Security Patterns**

### **Role-Based Access for Workshop Users**
```python
# ✅ DO: setup/setup_roles.py
import frappe

def setup_workshop_roles():
    """Setup role-based permissions for workshop operations"""
    
    roles = [
        {
            'role_name': 'Workshop Manager',
            'permissions': ['read', 'write', 'create', 'delete', 'submit', 'cancel']
        },
        {
            'role_name': 'Workshop Technician', 
            'permissions': ['read', 'write', 'create']
        },
        {
            'role_name': 'Workshop Customer',
            'permissions': ['read']
        }
    ]
    
    for role_data in roles:
        if not frappe.db.exists('Role', role_data['role_name']):
            role = frappe.new_doc('Role')
            role.role_name = role_data['role_name']
            role.insert()
```

## **Performance Optimization**

### **Database Indexing for Arabic Content**
```python
# ✅ DO: Database indexes for Arabic search_files
def setup_arabic_indexes():
    """Setup database indexes for Arabic content search_files"""
    
    # Add indexes for Arabic fields
    frappe.db.sql("""
        ALTER TABLE `tabWorkshop Profile` 
        ADD INDEX idx_workshop_name_ar (workshop_name_ar)
    """)
    
    frappe.db.sql("""
        ALTER TABLE `tabCustomer`
        ADD INDEX idx_customer_name_ar (customer_name_ar)
    """)
```
