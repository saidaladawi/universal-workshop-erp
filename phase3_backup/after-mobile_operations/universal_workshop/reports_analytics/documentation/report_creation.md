# Interactive Tutorial: Creating Your First Report

## Overview
This hands-on tutorial will guide you through creating your first report in the Universal Workshop ERP Reports & Analytics Engine. You'll learn to build a Customer Service Summary report that shows service history and revenue by customer.

## Prerequisites
- Access to Universal Workshop ERP system
- Workshop data with customers and service orders
- Basic understanding of Arabic/English interface
- Administrator has set up data sources

## Tutorial Objectives
By the end of this tutorial, you will be able to:
1. Navigate the Custom Report Builder interface
2. Select appropriate data sources
3. Configure filters and sorting
4. Add charts and visualizations
5. Export reports in multiple formats
6. Schedule automated report delivery

---

## Step 1: Accessing the Report Builder

### English Interface
1. Log into Universal Workshop ERP
2. Navigate to **Reports** → **Custom Reports**
3. Click **New Custom Report Builder**
4. Enter report name: "Customer Service Summary"

### Arabic Interface (الواجهة العربية)
1. تسجيل الدخول إلى نظام الورشة الشامل
2. انتقل إلى **التقارير** ← **التقارير المخصصة**
3. انقر على **منشئ التقارير الجديد**
4. أدخل اسم التقرير: "ملخص خدمات العملاء"

### Checkpoint 1 ✓
You should now see the Custom Report Builder interface with:
- Report name field filled
- Empty data source selection
- Blank field configuration area

---

## Step 2: Configure Basic Report Information

### Report Details
1. **Report Name (English)**: Customer Service Summary
2. **Report Name (Arabic)**: ملخص خدمات العملاء
3. **Description**: Monthly summary of customer service activities and revenue
4. **Category**: Customer Reports
5. **Access Level**: Manager and above

### Data Source Selection
1. Click **Add Data Source**
2. Select **Primary Source**: Sales Invoice
3. Select **Secondary Source**: Customer
4. Choose **Join Type**: Inner Join
5. **Join Field**: customer (links Sales Invoice to Customer)

### Regional Settings
1. **Time Zone**: Asia/Muscat
2. **Date Format**: DD/MM/YYYY (Arabic: يوم/شهر/سنة)
3. **Currency**: Omani Rial (OMR / ر.ع.)
4. **Number Format**: 123,456.789

---

## Step 3: Field Configuration

### Essential Fields to Include

#### Customer Information
- **Customer Name** (customer_name)
- **Customer Name Arabic** (customer_name_ar)
- **Phone Number** (phone)
- **Customer Group** (customer_group)

#### Service Information
- **Invoice Date** (posting_date)
- **Invoice Number** (name)
- **Net Total** (total)
- **Tax Amount** (total_taxes_and_charges)
- **Grand Total** (grand_total)
- **Status** (status)

---

## Step 4: Charts and Visualizations

### Chart 1: Revenue by Customer (Bar Chart)
1. **Chart Type**: Horizontal Bar Chart
2. **X-Axis**: customer_name_ar (Arabic names)
3. **Y-Axis**: SUM(grand_total)
4. **Title**: "Revenue by Customer / الإيرادات حسب العميل"
5. **Colors**: Blue gradient
6. **Format**: OMR currency on Y-axis

### Chart 2: Services Over Time (Line Chart)
1. **Chart Type**: Line Chart
2. **X-Axis**: posting_date (grouped by week)
3. **Y-Axis**: COUNT(*)
4. **Title**: "Services Trend / اتجاه الخدمات"
5. **Colors**: Green
6. **Format**: Date labels in Arabic

---

## Support Resources

### Help Documentation
- **User Manual**: Complete system documentation
- **Video Tutorials**: Step-by-step visual guides
- **FAQ Section**: Common questions and answers
- **Knowledge Base**: Searchable help articles

### Technical Support
- **Email Support**: support@universal-workshop.om
- **Phone Support**: +968 24 123 456
- **WhatsApp (Arabic)**: +968 92 123 456
- **Live Chat**: Available during business hours

---

## Conclusion

Congratulations! You have successfully completed the Reports & Analytics Engine tutorial. You should now be able to:

✅ **Create Custom Reports** with Arabic and English support
✅ **Configure Data Sources** and filters for your needs
✅ **Design Visualizations** that work on mobile devices
✅ **Export Reports** in multiple formats preserving Arabic content
✅ **Schedule Automated Delivery** for regular reporting
✅ **Troubleshoot Common Issues** and optimize performance

Thank you for choosing Universal Workshop ERP! / شكراً لاختيارك نظام الورشة الشامل!
