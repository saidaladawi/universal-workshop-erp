# Billing System Requirements - Universal Workshop ERP

## Executive Summary
This document outlines the comprehensive requirements for implementing a bilingual (Arabic/English) billing system for Universal Workshop ERP, compliant with Omani VAT regulations and e-invoice mandates effective October 2024.

## 1. Regulatory Compliance Requirements

### 1.1 Oman VAT Compliance
- **VAT Rate**: 5% as mandated by Oman Tax Authority
- **Precision**: 3 decimal places (Baisa level precision: 1 OMR = 1000 Baisa)
- **VAT Registration**: Support for Oman VAT number format (OMxxxxxxxxxxxxxxx)
- **Tax Periods**: Monthly reporting capabilities
- **Invoice Requirements**: Serial numbering, timestamps, seller/buyer details

### 1.2 E-Invoice Mandates (Effective October 2024)
- **CTC Model**: Clearance and disclosure model requiring real-time OTA validation
- **QR Code Requirements**: 
  - TLV encoding format
  - Minimum size: 1.5x1.5cm
  - Base64 encoding for data elements
  - Required data: Seller name, VAT number, timestamp, invoice total, VAT amount, UUID
- **Real-time Processing**: OTA middleware integration for invoice validation
- **Timeline Compliance**: Voluntary April-Sept 2024, mandatory October 2024

## 2. Bilingual Support Requirements

### 2.1 Arabic Language Support
- **RTL Layout**: Right-to-left text direction for Arabic content
- **Arabic Numerals**: Support for Arabic-Indic numerals (٠١٢٣٤٥٦٧٨٩)
- **Date Formats**: Arabic calendar support (Hijri) alongside Gregorian
- **Currency Display**: Arabic format (ر.ع. ١٢٣.٤٥٦)

### 2.2 English Language Support
- **LTR Layout**: Left-to-right text direction for English content
- **Western Numerals**: Standard numeric display (0123456789)
- **International Formats**: Standard date and currency formats
- **Fallback Support**: English as fallback when Arabic translation unavailable

### 2.3 Dynamic Language Switching
- **User Preference**: Per-user language settings
- **Document Language**: Invoice language based on customer preference
- **Real-time Switching**: Dynamic UI language change capability

## 3. Technical Architecture Requirements

### 3.1 ERPNext v15 Integration
- **Custom DocTypes**: 
  - Universal Invoice
  - VAT Settings
  - E-Invoice Log
  - QR Code Generator
- **Print Formats**: Bilingual invoice templates using Jinja2
- **Hooks Integration**: Custom validation and submission hooks
- **API Extensions**: WhiteListed methods for billing operations

### 3.2 Database Schema
```sql
-- Core billing tables
CREATE TABLE `tabUniversal Invoice` (
    `name` VARCHAR(140) PRIMARY KEY,
    `invoice_number` VARCHAR(50) UNIQUE,
    `customer` VARCHAR(140),
    `invoice_date` DATE,
    `total_amount` DECIMAL(18,3),
    `vat_amount` DECIMAL(18,3),
    `qr_code` TEXT,
    `e_invoice_status` VARCHAR(20),
    `language_preference` VARCHAR(5)
);

-- VAT configuration
CREATE TABLE `tabVAT Settings` (
    `name` VARCHAR(140) PRIMARY KEY,
    `vat_rate` DECIMAL(5,2) DEFAULT 5.00,
    `company_vat_number` VARCHAR(20),
    `e_invoice_enabled` BOOLEAN DEFAULT FALSE
);
```

### 3.3 QR Code Implementation
- **Library**: Python `qrcode` library with PIL imaging
- **Data Structure**: TLV (Tag-Length-Value) encoding
- **Generation**: Server-side generation with client-side display
- **Validation**: OTA compliance verification

## 4. Integration Requirements

### 4.1 Payment Gateway Integration
- **Local Banks**: Integration with Omani banking systems
- **International**: Support for Visa/Mastercard processing
- **Multi-currency**: OMR, USD, EUR support
- **Security**: PCI DSS compliance for card processing

### 4.2 External Services
- **OTA Middleware**: Real-time e-invoice validation service
- **Currency Exchange**: Live exchange rate APIs
- **SMS Gateway**: Arabic SMS notifications for invoices
- **Email Services**: Bilingual email invoice delivery

### 4.3 Workshop System Integration
- **Service Orders**: Automatic invoice generation from completed services
- **Parts Inventory**: Real-time parts cost calculation
- **Customer Management**: Integration with customer profiles and preferences
- **Technician Assignment**: Labor cost calculation and allocation

## 5. User Experience Requirements

### 5.1 Invoice Creation Workflow
1. **Service Completion**: Automatic invoice generation trigger
2. **Review Screen**: Bilingual preview with edit capabilities
3. **Approval Process**: Manager approval for high-value invoices
4. **QR Generation**: Automatic QR code creation and validation
5. **Delivery Options**: Print, email, SMS notification

### 5.2 Mobile Responsiveness
- **Touch-friendly**: Large buttons and inputs for mobile devices
- **Offline Capability**: Basic invoice creation without internet
- **Arabic Input**: Mobile keyboard support for Arabic text
- **Print Integration**: Mobile printing for on-site invoice generation

## 6. Performance Requirements

### 6.1 Response Time Targets
- **Invoice Generation**: < 3 seconds for standard invoices
- **QR Code Generation**: < 1 second for code creation
- **OTA Validation**: < 5 seconds for e-invoice clearance
- **Database Queries**: < 2 seconds for complex reporting

### 6.2 Scalability Targets
- **Concurrent Users**: Support for 50+ simultaneous users
- **Invoice Volume**: Handle 10,000+ invoices per month
- **Data Storage**: 5-year invoice retention with efficient archiving
- **Backup/Recovery**: < 4 hour recovery time objective

## 7. Security Requirements

### 7.1 Data Protection
- **Encryption**: AES-256 encryption for sensitive financial data
- **Access Control**: Role-based permissions for invoice operations
- **Audit Trail**: Complete audit log for all invoice modifications
- **GDPR Compliance**: Data protection for customer information

### 7.2 Financial Security
- **Invoice Tampering**: Digital signatures to prevent modification
- **VAT Validation**: Server-side validation for all tax calculations
- **Payment Security**: Secure payment processing with tokenization
- **Backup Integrity**: Encrypted backups with verification

## 8. Testing Requirements

### 8.1 Functional Testing
- **Bilingual Testing**: Comprehensive testing in both Arabic and English
- **VAT Calculation**: Automated testing for all VAT scenarios
- **QR Code Validation**: End-to-end QR code generation and scanning
- **Integration Testing**: Full workflow testing with all connected systems

### 8.2 Performance Testing
- **Load Testing**: Peak usage simulation with 100+ concurrent users
- **Stress Testing**: System behavior under extreme load conditions
- **Volume Testing**: Large dataset processing capabilities
- **Security Testing**: Penetration testing for financial vulnerabilities

## 9. Implementation Timeline

### Phase 1: Foundation (2 weeks)
- DocType creation and basic CRUD operations
- Database schema implementation
- Basic bilingual UI framework

### Phase 2: Core Features (2 weeks)
- VAT calculation engine
- QR code generation system
- Print format development

### Phase 3: Integration (2 weeks)
- OTA middleware integration
- Payment gateway connections
- Workshop system integration

### Phase 4: Testing & Deployment (2 weeks)
- Comprehensive testing suite
- User acceptance testing
- Production deployment

## 10. Success Criteria

### 10.1 Functional Success
- ✅ 100% Oman VAT compliance
- ✅ Bilingual invoice generation capability
- ✅ QR code integration with OTA validation
- ✅ Seamless workshop system integration

### 10.2 Performance Success
- ✅ All response time targets met
- ✅ Scalability targets achieved
- ✅ Security requirements satisfied
- ✅ User acceptance > 90%

## 11. Risk Assessment

### 11.1 Technical Risks
- **OTA Integration Complexity**: Medium risk - mitigated by early testing
- **Arabic Text Rendering**: Low risk - proven ERPNext v15 capabilities
- **QR Code Compliance**: Medium risk - detailed specification adherence required

### 11.2 Business Risks
- **Regulatory Changes**: Medium risk - monitoring of Oman Tax Authority updates
- **Performance Issues**: Low risk - comprehensive testing strategy
- **User Adoption**: Low risk - bilingual support addresses primary concern

## 12. Appendices

### A. Oman Tax Authority References
- Official VAT implementation guidelines
- E-invoice technical specifications
- QR code format documentation

### B. ERPNext v15 Documentation
- Custom DocType development guide
- Bilingual implementation patterns
- Print format customization methods

### C. Integration Specifications
- OTA middleware API documentation
- Payment gateway technical specs
- Workshop system interface definitions