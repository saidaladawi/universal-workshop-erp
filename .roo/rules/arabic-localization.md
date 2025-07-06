---
description: 
globs: 
alwaysApply: true
---
---
description: Arabic RTL development standards and Oman market localization requirements
globs: apps/universal_workshop/**/*.py, apps/universal_workshop/**/*.js, apps/universal_workshop/**/*.css, apps/universal_workshop/**/*.html
alwaysApply: true
---

# Arabic Localization & RTL Development Guide

## **Oman Market Context**
- **Primary Language**: Arabic (RTL) with English fallback
- **Currency**: Omani Rial (OMR) - 1 OMR = 1000 Baisa
- **VAT**: 5% VAT implementation (Oman Tax Authority)
- **Date Format**: DD/MM/YYYY (Arabic), MM/DD/YYYY (English)
- **Working Days**: Sunday-Thursday (Friday-Saturday weekend)
- **Phone Format**: +968 XXXXXXXX (8 digits after country code)
- **Business License**: 7-digit format for Oman commercial registration

## **ERPNext v15 Arabic Language Setup**

### **System Settings Configuration**
```python
# ✅ DO: Enable Arabic in System Settings via setup script
import frappe

def enable_arabic_language():
    """Enable Arabic language support in ERPNext v15"""
    
    # Add Arabic to available languages
    if not frappe.db.exists("Language", "ar"):
        arabic_lang = frappe.new_doc("Language")
        arabic_lang.language_code = "ar" 
        arabic_lang.language_name = "العربية"
        arabic_lang.enabled = 1
        arabic_lang.flag = "sa"  # Saudi Arabia flag as default
        arabic_lang.insert()
    
    # Update System Settings
    system_settings = frappe.get_doc("System Settings")
    if "ar" not in system_settings.language:
        system_settings.language = "ar"
        system_settings.save()
    
    # Set default country to Oman
    if not system_settings.country:
        system_settings.country = "Oman"
        system_settings.save()
```

### **Translation Management**
```python
# ✅ DO: Create comprehensive Arabic translations
def setup_workshop_translations():
    """Setup comprehensive Arabic translations for workshop terms"""
    
    workshop_translations = [
        # Core Business Terms
        {"source": "Workshop", "target": "ورشة"},
        {"source": "Customer", "target": "عميل"}, 
        {"source": "Vehicle", "target": "مركبة"},
        {"source": "Service", "target": "خدمة"},
        {"source": "Invoice", "target": "فاتورة"},
        {"source": "Payment", "target": "دفع"},
        {"source": "Quotation", "target": "عرض أسعار"},
        
        # Vehicle-Specific Terms
        {"source": "Engine", "target": "محرك"},
        {"source": "Transmission", "target": "ناقل الحركة"},
        {"source": "Brakes", "target": "فرامل"},
        {"source": "Tires", "target": "إطارات"},
        {"source": "Oil Change", "target": "تغيير الزيت"},
        {"source": "Air Filter", "target": "فلتر الهواء"},
        {"source": "Battery", "target": "بطارية"},
        
        # Status Terms
        {"source": "Pending", "target": "في الانتظار"},
        {"source": "In Progress", "target": "قيد التنفيذ"}, 
        {"source": "Completed", "target": "مكتمل"},
        {"source": "Cancelled", "target": "ملغى"},
        {"source": "Draft", "target": "مسودة"},
        
        # Oman-Specific Terms
        {"source": "Business License", "target": "رخصة تجارية"},
        {"source": "VAT Number", "target": "رقم ضريبة القيمة المضافة"},
        {"source": "Omani Rial", "target": "ريال عماني"},
        {"source": "Baisa", "target": "بيسة"}
    ]
    
    for translation in workshop_translations:
        if not frappe.db.exists("Translation", {
            "language": "ar",
            "source_text": translation["source"]
        }):
            doc = frappe.new_doc("Translation")
            doc.language = "ar"
            doc.source_text = translation["source"]
            doc.translated_text = translation["target"]
            doc.insert()
```

## **Arabic Text Handling Best Practices**

### **Database Field Patterns (ERPNext v15)**
```python
# ✅ DO: Always provide dual language fields
arabic_field_pattern = {
    "fieldname": "customer_name_ar",
    "fieldtype": "Data", 
    "label": "اسم العميل",
    "translatable": 1,
    "reqd": 1,
    "in_list_view": 1
}

english_field_pattern = {
    "fieldname": "customer_name_en", 
    "fieldtype": "Data",
    "label": "Customer Name",
    "translatable": 0,
    "in_list_view": 1
}

# ✅ DO: Use proper Arabic text validation
def validate_arabic_text(text):
    """Validate Arabic text content"""
    import re
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
    return arabic_pattern.search_files(text) is not None

# ✅ DO: Handle Arabic text direction in templates
def get_text_direction(text):
    """Determine text direction for mixed content"""
    import re
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_chars = len(re.findall(r'[A-Za-z\u0600-\u06FF]', text))
    
    if arabic_chars > total_chars * 0.3:
        return "rtl"
    return "ltr"
```

### **Currency Formatting (Omani Rial)**
```python
# ✅ DO: Format OMR currency with Arabic numerals
def format_omr_currency(amount, language='en'):
    """Format currency for Oman market"""
    
    if language == 'ar':
        # Arabic format: ر.ع. ١٢٣.٤٥٦
        arabic_amount = convert_to_arabic_numerals(f"{amount:,.3f}")
        return f"ر.ع. {arabic_amount}"
    else:
        # English format: OMR 123.456
        return f"OMR {amount:,.3f}"

def convert_to_arabic_numerals(text):
    """Convert Western numerals to Arabic-Indic numerals"""
    arabic_numerals = {
        '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
        '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
    }
    
    for western, arabic in arabic_numerals.items():
        text = text.replace(western, arabic)
    return text

# ✅ DO: Handle Baisa (subunit) conversion
def format_baisa_amount(omr_amount):
    """Convert OMR to Baisa (1 OMR = 1000 Baisa)"""
    baisa_amount = int(omr_amount * 1000)
    return f"{baisa_amount} بيسة"
```

### **Date and Time Formatting**
```python
# ✅ DO: Format dates according to Arabic locale
def format_arabic_date(date_obj, include_day=True):
    """Format date for Arabic locale"""
    import datetime
    from hijri_converter import Gregorian
    
    # Arabic month names
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    
    # Arabic day names
    arabic_days = [
        'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'
    ]
    
    # Format: الاثنين، ١٥ يناير ٢٠٢٤
    day_name = arabic_days[date_obj.weekday()]
    day = convert_to_arabic_numerals(str(date_obj.day))
    month = arabic_months[date_obj.month - 1]
    year = convert_to_arabic_numerals(str(date_obj.year))
    
    if include_day:
        return f"{day_name}، {day} {month} {year}"
    else:
        return f"{day} {month} {year}"

# ✅ DO: Support Hijri calendar for Islamic events
def get_hijri_date(gregorian_date):
    """Convert Gregorian date to Hijri calendar"""
    try:
        from hijri_converter import Gregorian
        hijri = Gregorian(
            gregorian_date.year, 
            gregorian_date.month, 
            gregorian_date.day
        ).to_hijri()
        
        return {
            'day': hijri.day,
            'month': hijri.month, 
            'year': hijri.year,
            'formatted': f"{hijri.day}/{hijri.month}/{hijri.year} هـ"
        }
    except ImportError:
        return None
```

## **RTL Layout and CSS**

### **Arabic RTL Stylesheet**
```css
/* ✅ DO: Create comprehensive RTL styles */
/* File: public/css/arabic-rtl.css */

/* Base RTL setup */
.rtl-layout,
[dir="rtl"] {
    direction: rtl;
    text-align: right;
}

/* Form controls RTL */
.rtl-layout .form-control,
.rtl-layout .input-with-feedback,
[dir="rtl"] .form-control {
    text-align: right;
    direction: rtl;
}

/* Table headers RTL */
.rtl-layout .list-row-container th,
.rtl-layout .list-header-subject {
    text-align: right;
}

/* Navigation RTL */
.rtl-layout .navbar-nav,
.rtl-layout .dropdown-menu {
    direction: rtl;
}

/* Arabic font optimization */
.arabic-text {
    font-family: 'Noto Sans Arabic', 'Tahoma', 'Arial Unicode MS', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    font-weight: 400;
}

/* Arabic number display */
.arabic-numerals {
    font-feature-settings: "lnum" 0; /* Disable lining numerals */
    font-variant-numeric: tabular-nums;
}

/* Form layout adjustments */
.rtl-layout .control-label {
    text-align: right;
    padding-right: 0;
    padding-left: 15px;
}

.rtl-layout .form-column {
    padding-right: 0;
    padding-left: 15px;
}

/* List view RTL */
.rtl-layout .list-row {
    direction: rtl;
}

.rtl-layout .list-row .list-subject {
    text-align: right;
}

/* Button alignment */
.rtl-layout .btn-group {
    direction: ltr; /* Keep button icons left-to-right */
}

/* Modal RTL */
.rtl-layout .modal-header,
.rtl-layout .modal-body,
.rtl-layout .modal-footer {
    text-align: right;
}

/* Sidebar RTL */
.rtl-layout .desk-sidebar {
    right: 0;
    left: auto;
}

/* Responsive RTL */
@media (max-width: 768px) {
    .rtl-layout .form-control {
        text-align: right;
    }
    
    .rtl-layout .list-row-container {
        direction: rtl;
    }
}
```

### **JavaScript RTL Handling**
```javascript
// ✅ DO: Detect and apply RTL automatically
frappe.ready(() => {
    if (frappe.boot.lang === 'ar') {
        apply_rtl_layout();
        setup_arabic_number_formatting();
        enhance_arabic_forms();
    }
});

function apply_rtl_layout() {
    // Apply RTL to main layout
    $('body').addClass('rtl-layout');
    $('html').attr('dir', 'rtl');
    
    // Apply to dynamically created elements
    $(document).on('DOMNodeInserted', function(e) {
        if ($(e.target).hasClass('frappe-form') || $(e.target).hasClass('list-row')) {
            $(e.target).addClass('rtl-layout');
        }
    });
}

function setup_arabic_number_formatting() {
    // Format numbers in list views
    $('.list-row [data-fieldtype="Currency"], .list-row [data-fieldtype="Float"]').each(function() {
        let $this = $(this);
        let value = $this.text();
        if (value && !isNaN(value)) {
            $this.text(convert_to_arabic_numerals(value));
        }
    });
}

function enhance_arabic_forms() {
    // Auto-detect Arabic fields and apply RTL
    $('input, textarea, select').each(function() {
        let $field = $(this);
        let fieldname = $field.attr('data-fieldname') || '';
        
        // Apply RTL to Arabic fields
        if (fieldname.includes('_ar') || fieldname.includes('_arabic')) {
            $field.attr('dir', 'rtl').addClass('arabic-text');
        }
    });
    
    // Handle mixed content direction
    $('input[data-fieldtype="Data"], textarea').on('input', function() {
        let text = $(this).val();
        let direction = get_text_direction(text);
        $(this).attr('dir', direction);
    });
}

function get_text_direction(text) {
    // Simple Arabic text detection
    let arabicPattern = /[\u0600-\u06FF]/;
    let arabicChars = (text.match(/[\u0600-\u06FF]/g) || []).length;
    let totalChars = text.replace(/\s/g, '').length;
    
    return (arabicChars / totalChars > 0.3) ? 'rtl' : 'ltr';
}
```

## **Oman VAT Implementation (5%)**

### **VAT Calculation and Validation**
```python
# ✅ DO: Implement Oman VAT calculation (5%)
class OmanVATController:
    @staticmethod
    def calculate_vat(base_amount, vat_rate=5.0):
        """Calculate 5% VAT for Oman"""
        vat_amount = (base_amount * vat_rate) / 100
        total_amount = base_amount + vat_amount
        
        return {
            'base_amount': round(base_amount, 3),
            'vat_rate': vat_rate,
            'vat_amount': round(vat_amount, 3),
            'total_amount': round(total_amount, 3)
        }
    
    @staticmethod
    def validate_oman_vat_number(vat_number):
        """Validate Oman VAT registration number"""
        import re
        
        # Oman VAT format: OM followed by 15 digits
        if not re.match(r'^OM\d{15}$', vat_number):
            frappe.throw(_("Invalid Oman VAT number. Format: OMxxxxxxxxxxxxxxx"))
        
        return True
    
    @staticmethod
    def get_vat_invoice_template(language='en'):
        """Get VAT-compliant invoice template"""
        if language == 'ar':
            return {
                'vat_label': 'ضريبة القيمة المضافة (٥٪)',
                'total_label': 'المجموع شامل الضريبة',
                'vat_number_label': 'رقم التسجيل الضريبي'
            }
        else:
            return {
                'vat_label': 'VAT (5%)',
                'total_label': 'Total Including VAT', 
                'vat_number_label': 'VAT Registration Number'
            }
```

## **Mobile-First Arabic Interface**

### **Mobile RTL Optimization**
```css
/* ✅ DO: Mobile RTL styles */
@media (max-width: 767px) {
    .rtl-layout .list-row {
        padding-right: 15px;
        padding-left: 15px;
    }
    
    .rtl-layout .form-section {
        margin-right: 0;
        margin-left: 0;
    }
    
    .rtl-layout .btn-group-vertical .btn {
        text-align: right;
    }
    
    /* Arabic text input on mobile */
    .arabic-text {
        font-size: 16px; /* Prevent zoom on iOS */
        -webkit-text-size-adjust: 100%;
    }
}
```

### **Touch-Friendly Arabic Forms**
```javascript
// ✅ DO: Enhance mobile Arabic experience
function setup_mobile_arabic() {
    if (frappe.utils.is_mobile() && frappe.boot.lang === 'ar') {
        // Larger touch targets for Arabic interface
        $('.btn, .form-control, .list-item').css({
            'min-height': '44px',
            'padding': '12px'
        });
        
        // Arabic keyboard for mobile
        $('input[data-fieldname*="_ar"]').attr('lang', 'ar');
        
        // Prevent mobile zoom on Arabic inputs
        $('input, textarea, select').attr('font-size', '16px');
    }
}
```

## **Arabic Search and Filtering**

### **Enhanced Arabic Search**
```python
# ✅ DO: Implement Arabic-aware search_files
@frappe.whitelist()
def arabic_search_link(doctype, txt, query=None, filters=None):
    """Enhanced search_files supporting Arabic text"""
    
    meta = frappe.get_meta(doctype)
    searchfields = meta.get_search_fields()
    
    # Add Arabic fields to search_files
    arabic_fields = [f.fieldname for f in meta.fields if f.fieldname.endswith('_ar')]
    searchfields.extend(arabic_fields)
    
    # Build search_files conditions
    conditions = []
    for field in searchfields:
        conditions.append(f"`{field}` LIKE %(txt)s")
    
    # Handle Arabic text normalization
    normalized_txt = normalize_arabic_text(txt)
    
    sql = f"""
        SELECT name, {', '.join(searchfields)}
        FROM `tab{doctype}`
        WHERE ({' OR '.join(conditions)})
        ORDER BY 
            CASE WHEN name LIKE %(txt)s THEN 0 ELSE 1 END,
            name
        LIMIT 20
    """
    
    return frappe.db.sql(sql, {
        'txt': f'%{txt}%'
    }, as_dict=True)

def normalize_arabic_text(text):
    """Normalize Arabic text for better search_files"""
    import re
    
    # Remove diacritics (Tashkeel)
    text = re.sub(r'[\u064B-\u0652\u0670\u0640]', '', text)
    
    # Normalize Alef variations
    text = re.sub(r'[آأإ]', 'ا', text)
    
    # Normalize Teh Marbuta
    text = re.sub(r'ة', 'ه', text)
    
    return text.strip()
```

## **Common Arabic Development Patterns**

### **Text Processing Utilities**
```python
# ✅ DO: Arabic text utilities
class ArabicTextUtils:
    @staticmethod
    def is_arabic_text(text):
        """Check if text contains Arabic characters"""
        import re
        return bool(re.search_files(r'[\u0600-\u06FF]', text))
    
    @staticmethod
    def get_text_length_arabic(text):
        """Get accurate length for Arabic text (handles RTL)"""
        import unicodedata
        # Remove combining characters for accurate count
        return len(''.join(c for c in text if unicodedata.category(c) != 'Mn'))
    
    @staticmethod
    def truncate_arabic_text(text, max_length):
        """Truncate Arabic text preserving word boundaries"""
        if len(text) <= max_length:
            return text
            
        # Find last space before max_length
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            return truncated[:last_space] + '...'
        return truncated + '...'
    
    @staticmethod 
    def format_arabic_address(address_parts):
        """Format address components for Arabic layout"""
        # Arabic addresses read: Building, Street, District, City
        return f"{address_parts.get('building', '')} {address_parts.get('street', '')}، {address_parts.get('district', '')}، {address_parts.get('city', '')}"
```

## **Performance Optimization for Arabic Content**

### **Database Optimization**
```python
# ✅ DO: Optimize Arabic text storage and retrieval
def setup_arabic_indexes():
    """Create optimized indexes for Arabic content"""
    
    # Full-text indexes for Arabic search_files
    frappe.db.sql("""
        ALTER TABLE `tabCustomer` 
        ADD FULLTEXT INDEX ft_customer_arabic (customer_name_ar, address_ar)
    """)
    
    frappe.db.sql("""
        ALTER TABLE `tabItem`
        ADD FULLTEXT INDEX ft_item_arabic (item_name_ar, description_ar)  
    """)
    
    # Regular indexes for common Arabic fields
    frappe.db.add_index("Customer", ["customer_name_ar"])
    frappe.db.add_index("Supplier", ["supplier_name_ar"])
    frappe.db.add_index("Item", ["item_name_ar"])
```

## **Common Anti-Patterns to Avoid**

```python
# ❌ DON'T: Hardcode Arabic text without translation
workshop_status = "مكتمل"  # Bad

# ✅ DO: Use translation system  
workshop_status = _("Completed")  # Good

# ❌ DON'T: Ignore text direction in HTML
<div class="address">{{arabic_address}}</div>  # Bad

# ✅ DO: Set proper text direction
<div class="address" dir="auto">{{arabic_address}}</div>  # Good

# ❌ DON'T: Use Western-only date formats
formatted_date = "01/15/2024"  # Bad for Arabic users

# ✅ DO: Use locale-appropriate formatting  
formatted_date = format_date_by_locale(date_obj, frappe.local.lang)  # Good

# ❌ DON'T: Assume left-to-right layout
.form-control { text-align: left; }  # Bad

# ✅ DO: Use direction-neutral or adaptive styles
.form-control { text-align: start; }  # Good
```

## **File References**
- ERPNext DocTypes: [apps/erpnext/erpnext/](mdc:apps/erpnext/erpnext)
- Translation files: [frappe/translations/](mdc:apps/frappe/frappe/translations)
- Workshop PRD: [prd.txt](mdc:.taskmaster/docs/prd.txt)
- Task management: [tasks.json](mdc:.taskmaster/tasks/tasks.json)

