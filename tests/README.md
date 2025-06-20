# Universal Workshop ERP - Integration Testing Framework

## Overview

This comprehensive testing framework provides end-to-end integration testing for the Universal Workshop ERP system, including support for Arabic/English dual language workflows, Omani VAT compliance, and automotive workshop-specific features.

## Framework Components

### 1. Python Integration Tests (`tests/e2e/`)
- Complete workflow testing from customer registration to billing
- Arabic Unicode handling and RTL support validation
- Business logic integration testing
- Multi-service and inventory integration scenarios
- Performance testing with bulk data

### 2. Cypress UI Tests (`tests/e2e/cypress_workshop_tests.js`)
- Browser-based end-to-end testing
- Form interaction and validation testing
- Multi-language UI testing (Arabic/English)
- Appointment scheduling and service workflows
- Error handling and validation testing

### 3. API Integration Tests (`tests/integration/`)
- REST API endpoint testing
- Authentication and authorization validation
- CRUD operations testing
- API performance and rate limiting tests
- Security and error handling validation

### 4. Test Fixtures and Utilities
- Realistic test data in both Arabic and English
- Mock data generators for performance testing
- Test environment setup and cleanup utilities
- Workshop-specific data validation helpers

## Quick Start

### Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-json-report requests locust
npm install cypress
```

### Running Tests

#### All Tests
```bash
./tests/run_tests.py
```

#### Specific Test Suites
```bash
# Python integration tests only
./tests/run_tests.py --python-only

# Cypress UI tests only  
./tests/run_tests.py --cypress-only

# API tests only
./tests/run_tests.py --api-only

# Include load and security testing
./tests/run_tests.py --include-load --include-security
```

#### Individual Test Files
```bash
# Run specific Python test file
python -m pytest tests/e2e/test_workshop_workflow.py -v

# Run specific Cypress test
npx cypress run --spec "tests/e2e/cypress_workshop_tests.js"
```

## Test Scenarios Covered

### 1. Complete Workshop Workflows
- **English Workflow**: Customer registration → Vehicle registration → Service order → Technician assignment → Service completion → Billing with VAT
- **Arabic Workflow**: Same workflow with Arabic customer data, RTL UI validation, and Arabic invoice generation
- **Multi-service Scenarios**: Concurrent services, priority handling, resource allocation

### 2. Integration Points
- **Customer Management**: Creation, search (fuzzy matching), profile management
- **Vehicle Registry**: VIN decoding, service history tracking, maintenance alerts
- **Inventory Integration**: Parts consumption, stock updates, reorder alerts
- **Appointment Scheduling**: Calendar integration, conflict resolution, service bay management
- **Billing & VAT**: Omani VAT compliance, QR code generation, multi-currency support

### 3. Communication Systems
- **SMS/WhatsApp Integration**: Message queuing, delivery tracking, opt-in/opt-out management
- **Customer Portal**: Online booking, service tracking, account management
- **Mobile App Integration**: Technician workflows, offline capabilities, real-time sync

### 4. Security & Compliance
- **License Management**: Hardware fingerprinting, business binding, offline grace periods
- **Authentication**: JWT RS256 validation, session management, API security
- **Data Privacy**: Arabic text handling, data residency compliance, audit trails

## Test Data Management

### Fixtures (`tests/fixtures/workshop_test_data.json`)
- Pre-configured customers, vehicles, and service types
- Arabic and English test scenarios
- Realistic Omani business data (phone numbers, addresses, etc.)

### Dynamic Test Data
```python
from tests.utils.test_utils import WorkshopTestUtils

# Create test customer
customer = WorkshopTestUtils.create_test_customer(language="ar", customer_type="Company")

# Create test vehicle
vehicle = WorkshopTestUtils.create_test_vehicle(customer.name, make="Toyota", model="Camry")

# Generate bulk test data
bulk_data = WorkshopTestUtils.generate_test_data_bulk(count=100)
```

## Performance Testing

### Load Testing
```bash
# Test with 50 concurrent users for 5 minutes
./tests/run_tests.py --include-load
```

### Database Performance
- Query optimization validation
- Index usage verification  
- Concurrent transaction testing
- Large dataset handling

### API Performance
- Response time measurement
- Throughput testing
- Rate limiting validation
- Error handling under load

## Security Testing

### Automated Security Scans
```bash
# Include OWASP ZAP security scanning
./tests/run_tests.py --include-security
```

### Security Test Coverage
- **Input Validation**: XSS, SQL injection, CSRF protection
- **Authentication**: JWT token validation, session security
- **Authorization**: Role-based access control, data isolation
- **API Security**: Rate limiting, authentication bypass attempts

## Arabic Language Testing

### Unicode Handling
- Proper UTF-8 encoding/decoding
- Arabic text storage and retrieval
- Search functionality with Arabic text
- Collation and sorting validation

### RTL (Right-to-Left) UI Testing
- Form layout validation
- Data entry and display
- Report generation in Arabic
- Print format compatibility

### Bilingual Workflows
- Language switching between forms
- Mixed Arabic/English data handling
- Invoice generation in both languages
- Email/SMS templates in both languages

## Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Environment
        run: |
          # Setup ERPNext environment
          # Install dependencies
      - name: Run Tests
        run: ./tests/run_tests.py
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test_results/
```

### Test Reporting
- JSON test results for CI integration
- HTML reports for human review
- Coverage reports and metrics
- Performance benchmarking data

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Ensure test site is properly configured
bench set-config developer_mode 1
bench migrate
```

#### Cypress Test Failures
```bash
# Check if ERPNext server is running
bench start
# Verify Cypress base URL matches server
export CYPRESS_baseUrl="http://localhost:8000"
```

#### Arabic Text Display Issues
- Verify UTF-8 encoding in database
- Check font support in test environment
- Validate collation settings for Arabic text

#### API Authentication Failures
- Verify API key/secret configuration
- Check user permissions and roles
- Validate CSRF token handling

### Debug Mode
```bash
# Run tests with verbose output
./tests/run_tests.py --python-only -v

# Run specific test with debugging
python -m pytest tests/e2e/test_workshop_workflow.py::TestWorkshopE2EWorkflow::test_complete_workshop_workflow_english -v -s
```

## Test Environment Setup

### Database Configuration
```python
# tests/conftest.py handles automatic setup
# Manual setup if needed:
frappe.init_site("test.local")
frappe.connect()
```

### Test Data Cleanup
```python
# Automatic cleanup after each test
@pytest.fixture(scope="function")
def clean_db():
    frappe.db.begin()
    yield
    frappe.db.rollback()
```

## Extending the Framework

### Adding New Test Cases
1. Create test file in appropriate directory (`e2e/`, `integration/`)
2. Use existing fixtures and utilities
3. Follow naming conventions (`test_*.py`)
4. Add to test runner if needed

### Custom Test Utilities
```python
# tests/utils/test_utils.py
class WorkshopTestUtils:
    @staticmethod
    def create_custom_test_data():
        # Your custom test data creation logic
        pass
```

### New Test Fixtures
```json
// tests/fixtures/custom_test_data.json
{
  "custom_entities": [
    // Your custom test entities
  ]
}
```

## Test Results and Metrics

### Generated Reports
- `test_results/comprehensive_test_report.json` - Complete test results
- `test_results/test_report.html` - Human-readable HTML report
- `test_results/cypress_tests.json` - Cypress-specific results
- `test_results/load_test_report.html` - Load testing metrics

### Key Metrics Tracked
- Test execution time
- Pass/fail rates by test suite
- Performance benchmarks
- Security vulnerability counts
- Code coverage percentages

## Support and Maintenance

### Regular Maintenance Tasks
1. Update test data to reflect system changes
2. Review and update security test scenarios
3. Performance baseline adjustments
4. Arabic language test data expansion

### Getting Help
- Check test logs in `test_results/` directory
- Review fixture data for expected formats
- Validate test environment setup
- Check ERPNext/Frappe documentation for API changes

---

This testing framework ensures comprehensive validation of the Universal Workshop ERP system across all critical workflows, languages, and integration points, providing confidence for production deployment in the Omani automotive workshop market.
