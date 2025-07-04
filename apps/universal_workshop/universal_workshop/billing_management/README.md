# Billing Management Module

## Overview
Comprehensive billing and financial management system for Universal Workshop ERP, designed specifically for Omani automotive workshops with full VAT compliance.

## Structure

### Core Components
- **doctype/** - Billing-related DocTypes and configurations
- **report/** - Financial and VAT reports
- **page/** - Dashboard pages for financial overview
- **dashboard/** - Dashboard configurations

### Key Features
- **Oman VAT Compliance** - 5% VAT calculation and reporting
- **QR Code Invoices** - QR code generation for invoices
- **Multi-currency Support** - Handle multiple currencies
- **Cash Flow Forecasting** - Advanced financial planning
- **Receivables Management** - Customer payment tracking
- **P&L Reporting** - Profit and loss analysis

### Submodules
- **cash_flow/** - Cash flow forecasting and enhancement
- **receivables/** - Receivables management and ERPNext integration
- **pnl_reporting/** - Profit and loss reporting system

### Integration Points
- **ERPNext Sales Invoice** - Enhanced with custom fields
- **ERPNext Payment Entry** - Custom payment processing
- **ERPNext Account** - VAT account configuration
- **Universal Workshop Service Order** - Billing integration

## Dependencies
- ERPNext v15.x
- Python 3.10+
- Redis (for caching)
- qrcode library (for QR generation)

## Configuration
See individual module documentation for setup instructions.