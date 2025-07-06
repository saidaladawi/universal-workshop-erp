# 📚 Shared Libraries Usage Guide

**Created:** Phase 3.2  
**Purpose:** Prevent future code duplication by using centralized business logic  
**Location:** `/universal_workshop/shared_libraries/`

---

## 🎯 Available Shared Libraries

### 1. Arabic Business Logic
**Use for:** Arabic text validation, Omani phone numbers, bilingual content, cultural validation

```python
from universal_workshop.shared_libraries.arabic_business_logic import (
    ArabicTextUtils,
    OmanPhoneValidator,
    BilingualContentValidator,
    ArabicNameFormatter
)

# Example: Validate Omani phone number
phone_validator = OmanPhoneValidator()
if phone_validator.validate("+968 9123 4567"):
    print("Valid Omani phone number")

# Example: Validate Arabic text
if ArabicTextUtils.is_arabic_text("مرحبا"):
    print("Valid Arabic text")

# Example: Format Arabic name
formatted = ArabicNameFormatter.format_full_name("أحمد", "محمد", "الخليلي")
```

---

### 2. Financial Compliance
**Use for:** VAT calculations, QR invoice generation, multi-currency, Islamic finance

```python
from universal_workshop.shared_libraries.financial_compliance import (
    OmanVATCalculator,
    QRInvoiceGenerator,
    MultiCurrencyValidator,
    IslamicFinanceValidator
)

# Example: Calculate Omani VAT
vat_calc = OmanVATCalculator()
result = vat_calc.calculate_vat(amount=100.000, vat_rate=0.05)
# Returns: {'vat_amount': 5.000, 'total_amount': 105.000}

# Example: Generate QR code for invoice
qr_gen = QRInvoiceGenerator()
qr_data = qr_gen.generate_invoice_qr(
    seller_name="Universal Workshop",
    vat_number="OM123456789",
    invoice_total=105.000,
    vat_amount=5.000
)
```

---

### 3. Workshop Operations
**Use for:** Service scheduling, status validation, technician management, quality control

```python
from universal_workshop.shared_libraries.workshop_operations import (
    ServiceScheduler,
    WorkshopStatusValidator,
    TechnicianManager,
    QualityControlValidator
)

# Example: Validate service status transition
validator = WorkshopStatusValidator()
if validator.can_transition("In Progress", "Quality Check"):
    # Update status
    pass

# Example: Schedule service
scheduler = ServiceScheduler()
slot = scheduler.find_next_available_slot(
    service_type="Oil Change",
    duration_hours=1.5,
    technician_skills=["mechanical"]
)
```

---

### 4. Inventory Management
**Use for:** Stock validation, barcode operations, ABC analysis, supplier management

```python
from universal_workshop.shared_libraries.inventory_management import (
    StockValidator,
    BarcodeManager,
    ABCAnalyzer,
    SupplierValidator
)

# Example: Validate stock transfer
stock_val = StockValidator()
if stock_val.validate_transfer(
    item="Oil Filter",
    qty=10,
    from_warehouse="Main Store",
    to_warehouse="Service Bay 1"
):
    # Process transfer
    pass

# Example: Generate barcode
barcode_mgr = BarcodeManager()
barcode = barcode_mgr.generate_part_barcode("FILTER-001")
```

---

### 5. Traditional Workflows
**Use for:** Islamic business validation, cultural patterns, Omani compliance

```python
from universal_workshop.shared_libraries.traditional_workflows import (
    IslamicBusinessValidator,
    TraditionalPatternMatcher,
    OmaniComplianceChecker
)

# Example: Validate Islamic business principles
islamic_val = IslamicBusinessValidator()
if islamic_val.validate_transaction(
    transaction_type="service_payment",
    payment_method="credit",
    includes_interest=False
):
    # Process payment
    pass
```

---

### 6. Database Optimization
**Use for:** Query optimization, caching, bulk operations, Arabic text search

```python
from universal_workshop.shared_libraries.utils.database_optimization import (
    DatabaseOptimizer,
    QueryCache,
    BulkOperationManager
)

# Example: Optimize Arabic search
optimizer = DatabaseOptimizer()
optimizer.optimize_arabic_search(
    table="tabCustomer",
    column="customer_name_arabic"
)

# Example: Cache frequently used query
cache = QueryCache()
customers = cache.get_or_set(
    "active_customers",
    lambda: frappe.get_all("Customer", filters={"disabled": 0}),
    timeout=3600  # 1 hour
)
```

---

## 📋 Best Practices

### 1. Always Check If Shared Library Exists
Before writing validation or business logic, check shared libraries:
```python
# ❌ Don't do this:
def validate_phone(phone):
    pattern = r'^\+968\d{8}$'
    return re.match(pattern, phone)

# ✅ Do this:
from universal_workshop.shared_libraries.arabic_business_logic import OmanPhoneValidator
validator = OmanPhoneValidator()
return validator.validate(phone)
```

### 2. Extend Shared Libraries for New Features
If you need additional functionality, extend the shared library:
```python
# In your module
from universal_workshop.shared_libraries.workshop_operations import ServiceScheduler

class AdvancedServiceScheduler(ServiceScheduler):
    def schedule_with_parts_check(self, service_type, required_parts):
        # Check parts availability first
        if self.check_parts_availability(required_parts):
            return super().find_next_available_slot(service_type)
        return None
```

### 3. Contribute Back to Shared Libraries
If you create reusable logic, add it to shared libraries:
```python
# Add to appropriate shared library
class VehicleValidator:
    @staticmethod
    def validate_vin(vin):
        """Validate Vehicle Identification Number"""
        if len(vin) != 17:
            return False
        # Add to shared_libraries/workshop_operations/validators.py
```

---

## 🚀 Migration Examples

### Migrating Existing Code
```python
# Old code (duplicate logic)
def calculate_service_total(parts_cost, labor_cost):
    subtotal = parts_cost + labor_cost
    vat = subtotal * 0.05
    total = subtotal + vat
    return total

# New code (using shared library)
from universal_workshop.shared_libraries.financial_compliance import OmanVATCalculator

def calculate_service_total(parts_cost, labor_cost):
    calculator = OmanVATCalculator()
    subtotal = parts_cost + labor_cost
    return calculator.calculate_total_with_vat(subtotal)
```

---

## 📊 Impact

Using shared libraries:
- **Prevents** new code duplication
- **Ensures** consistent business logic
- **Maintains** cultural compliance
- **Speeds up** development
- **Reduces** bugs from inconsistent implementation

---

## 🎯 Quick Reference

| Need | Use Library | Import |
|------|------------|---------|
| Arabic validation | arabic_business_logic | `from universal_workshop.shared_libraries.arabic_business_logic import ...` |
| VAT calculation | financial_compliance | `from universal_workshop.shared_libraries.financial_compliance import ...` |
| Service scheduling | workshop_operations | `from universal_workshop.shared_libraries.workshop_operations import ...` |
| Stock validation | inventory_management | `from universal_workshop.shared_libraries.inventory_management import ...` |
| Islamic compliance | traditional_workflows | `from universal_workshop.shared_libraries.traditional_workflows import ...` |
| Query optimization | database_optimization | `from universal_workshop.shared_libraries.utils.database_optimization import ...` |

---

**Remember:** These libraries were built to solve the duplication problem. Use them for ALL new code!