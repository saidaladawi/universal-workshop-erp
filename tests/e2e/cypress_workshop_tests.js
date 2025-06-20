/**
 * Cypress E2E Tests for Universal Workshop ERP System
 * Tests complete UI workflows with Arabic/English support
 */

describe('Workshop Complete E2E Workflow', () => {
    const testData = {
        customer: {
            english: {
                customer_name: 'Ahmed Al-Rashid Motors',
                customer_group: 'Commercial',
                territory: 'Oman',
                customer_type: 'Company',
                language: 'en',
                mobile_no: '+968 9123 4567',
                email_id: 'ahmed@alrashidmotors.om'
            },
            arabic: {
                customer_name: 'ورشة أحمد الراشد للسيارات',
                customer_group: 'Commercial', 
                territory: 'Oman',
                customer_type: 'Company',
                language: 'ar',
                mobile_no: '+968 9123 4567',
                email_id: 'ahmed.ar@alrashidmotors.om'
            }
        },
        vehicle: {
            vin: '1HGBH41JXMN109186',
            license_plate: 'A-12345',
            make: 'Toyota',
            model: 'Camry', 
            year: '2023',
            color: 'White',
            fuel_type: 'Petrol'
        },
        service: {
            service_type: 'Oil Change',
            description: 'Engine oil and filter change',
            description_arabic: 'تغيير زيت المحرك والفلتر',
            estimated_duration: '60'
        }
    };

    beforeEach(() => {
        cy.login('Administrator', 'admin');
        cy.visit('/app');
    });

    it('Complete English Workflow: Customer Registration → Service → Billing', () => {
        // Step 1: Create Customer
        cy.visit('/app/customer/new-customer-1');
        cy.wait(1000);
        
        // Fill customer form
        cy.fill_field('customer_name', testData.customer.english.customer_name);
        cy.fill_field('customer_group', testData.customer.english.customer_group, 'Link');
        cy.fill_field('territory', testData.customer.english.territory, 'Link');
        cy.fill_field('customer_type', testData.customer.english.customer_type, 'Select');
        cy.fill_field('mobile_no', testData.customer.english.mobile_no);
        cy.fill_field('email_id', testData.customer.english.email_id);
        
        // Save customer
        cy.get('.primary-action').click();
        cy.wait(2000);
        
        // Verify customer creation
        cy.get('.indicator-pill').should('contain', 'Enabled');
        cy.url().should('include', '/app/customer/');
        
        // Store customer name for later use
        cy.url().then((url) => {
            const customerName = url.split('/').pop();
            cy.wrap(customerName).as('customerName');
        });

        // Step 2: Register Vehicle
        cy.get('@customerName').then((customerName) => {
            cy.visit('/app/vehicle/new-vehicle-1');
            cy.wait(1000);
            
            // Fill vehicle form
            cy.fill_field('customer', customerName, 'Link');
            cy.fill_field('vin', testData.vehicle.vin);
            cy.fill_field('license_plate', testData.vehicle.license_plate);
            cy.fill_field('make', testData.vehicle.make);
            cy.fill_field('model', testData.vehicle.model);
            cy.fill_field('year', testData.vehicle.year);
            cy.fill_field('color', testData.vehicle.color);
            cy.fill_field('fuel_type', testData.vehicle.fuel_type, 'Select');
            
            // Save vehicle
            cy.get('.primary-action').click();
            cy.wait(2000);
            
            // Verify vehicle creation
            cy.get('.indicator-pill').should('exist');
            cy.url().should('include', '/app/vehicle/');
            
            // Store vehicle name
            cy.url().then((url) => {
                const vehicleName = url.split('/').pop();
                cy.wrap(vehicleName).as('vehicleName');
            });
        });

        // Step 3: Create Service Order
        cy.get('@customerName').then((customerName) => {
            cy.get('@vehicleName').then((vehicleName) => {
                cy.visit('/app/service-order/new-service-order-1');
                cy.wait(1000);
                
                // Fill service order form
                cy.fill_field('customer', customerName, 'Link');
                cy.fill_field('vehicle', vehicleName, 'Link');
                cy.fill_field('service_type', testData.service.service_type);
                cy.fill_field('description', testData.service.description, 'Text Editor');
                cy.fill_field('estimated_duration', testData.service.estimated_duration);
                
                // Save service order
                cy.get('.primary-action').click();
                cy.wait(2000);
                
                // Submit service order
                cy.get('[data-label="Submit"]').click();
                cy.wait(1000);
                
                // Verify service order creation
                cy.get('.indicator-pill').should('contain', 'Submitted');
                
                // Store service order name
                cy.url().then((url) => {
                    const serviceOrderName = url.split('/').pop();
                    cy.wrap(serviceOrderName).as('serviceOrderName');
                });
            });
        });

        // Step 4: Update Service Status to In Progress
        cy.get('@serviceOrderName').then((serviceOrderName) => {
            cy.visit(`/app/service-order/${serviceOrderName}`);
            cy.wait(1000);
            
            // Change status to In Progress
            cy.get('[data-fieldname="status"]').click();
            cy.get('.dropdown-item').contains('In Progress').click();
            
            // Add work notes
            cy.fill_field('work_notes', 'Service work started by technician', 'Text Editor');
            
            // Save changes
            cy.get('.primary-action').click();
            cy.wait(1000);
            
            // Verify status change
            cy.get('[data-fieldname="status"] .control-value').should('contain', 'In Progress');
        });

        // Step 5: Complete Service
        cy.get('@serviceOrderName').then((serviceOrderName) => {
            cy.visit(`/app/service-order/${serviceOrderName}`);
            cy.wait(1000);
            
            // Change status to Completed
            cy.get('[data-fieldname="status"]').click();
            cy.get('.dropdown-item').contains('Completed').click();
            
            // Add completion notes
            cy.fill_field('work_notes', 'Oil change completed successfully. Used 5L synthetic oil.', 'Text Editor');
            cy.fill_field('actual_duration', '65');
            
            // Save completion
            cy.get('.primary-action').click();
            cy.wait(1000);
            
            // Verify completion
            cy.get('[data-fieldname="status"] .control-value').should('contain', 'Completed');
        });

        // Step 6: Create Sales Invoice
        cy.get('@customerName').then((customerName) => {
            cy.get('@serviceOrderName').then((serviceOrderName) => {
                cy.visit('/app/sales-invoice/new-sales-invoice-1');
                cy.wait(1000);
                
                // Fill invoice header
                cy.fill_field('customer', customerName, 'Link');
                cy.fill_field('currency', 'OMR', 'Link');
                
                // Add service item
                cy.get('[data-fieldname="items"] .grid-add-row').click();
                cy.wait(500);
                
                cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="item_code"] input').type('OIL-CHANGE-SVC');
                cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="description"] textarea').type(testData.service.description);
                cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="qty"] input').clear().type('1');
                cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="rate"] input').clear().type('25');
                
                // Add VAT template
                cy.fill_field('taxes_and_charges', 'Oman VAT - UW', 'Link');
                
                // Save invoice
                cy.get('.primary-action').click();
                cy.wait(2000);
                
                // Submit invoice
                cy.get('[data-label="Submit"]').click();
                cy.wait(1000);
                
                // Verify invoice creation and VAT calculation
                cy.get('.indicator-pill').should('contain', 'Submitted');
                cy.get('[data-fieldname="grand_total"] .control-value').should('not.be.empty');
                
                // Verify VAT amount is greater than net total
                cy.get('[data-fieldname="grand_total"] .control-value').invoke('text').then((grandTotal) => {
                    cy.get('[data-fieldname="net_total"] .control-value').invoke('text').then((netTotal) => {
                        const grand = parseFloat(grandTotal.replace(/[^\d.-]/g, ''));
                        const net = parseFloat(netTotal.replace(/[^\d.-]/g, ''));
                        expect(grand).to.be.greaterThan(net);
                    });
                });
            });
        });
    });

    it('Complete Arabic Workflow with RTL Support', () => {
        // Step 1: Create Arabic Customer
        cy.visit('/app/customer/new-customer-1');
        cy.wait(1000);
        
        // Fill customer form with Arabic data
        cy.fill_field('customer_name', testData.customer.arabic.customer_name);
        cy.fill_field('customer_group', testData.customer.arabic.customer_group, 'Link');
        cy.fill_field('territory', testData.customer.arabic.territory, 'Link');
        cy.fill_field('customer_type', testData.customer.arabic.customer_type, 'Select');
        cy.fill_field('language', 'ar', 'Select');
        cy.fill_field('mobile_no', testData.customer.arabic.mobile_no);
        cy.fill_field('email_id', testData.customer.arabic.email_id);
        
        // Save Arabic customer
        cy.get('.primary-action').click();
        cy.wait(2000);
        
        // Verify Arabic text display
        cy.get('[data-fieldname="customer_name"] .control-value').should('contain', 'ورشة أحمد');
        
        // Store customer name
        cy.url().then((url) => {
            const customerName = url.split('/').pop();
            cy.wrap(customerName).as('arabicCustomerName');
        });

        // Step 2: Create Service Order with Arabic Description
        cy.get('@arabicCustomerName').then((customerName) => {
            cy.visit('/app/service-order/new-service-order-1');
            cy.wait(1000);
            
            cy.fill_field('customer', customerName, 'Link');
            cy.fill_field('service_type', testData.service.service_type);
            cy.fill_field('description', testData.service.description_arabic, 'Text Editor');
            
            // Save and verify Arabic description
            cy.get('.primary-action').click();
            cy.wait(2000);
            
            cy.get('[data-fieldname="description"] .control-value').should('contain', 'تغيير زيت');
        });
    });

    it('Test Search Functionality with Arabic Text', () => {
        // Create Arabic customer first
        cy.create_records({
            doctype: 'Customer',
            customer_name: 'ورشة محمد للسيارات',
            customer_group: 'Individual',
            territory: 'Oman',
            language: 'ar'
        });

        // Test search with Arabic text
        cy.visit('/app/customer');
        cy.wait(1000);
        
        // Use search box
        cy.get('.standard-filter-section .input-with-feedback input').type('محمد');
        cy.wait(1000);
        
        // Verify search results contain Arabic text
        cy.get('.list-row-container').should('contain', 'محمد');
    });

    it('Test Appointment Scheduling Workflow', () => {
        // Create customer and vehicle first
        cy.create_records({
            doctype: 'Customer',
            customer_name: 'Test Workshop Customer',
            customer_group: 'Individual',
            territory: 'Oman'
        }).then((customer) => {
            cy.create_records({
                doctype: 'Vehicle',
                customer: customer.name,
                vin: '1HGBH41JXMN109999',
                license_plate: 'T-99999',
                make: 'Honda',
                model: 'Civic'
            }).then((vehicle) => {
                // Create appointment
                cy.visit('/app/appointment/new-appointment-1');
                cy.wait(1000);
                
                cy.fill_field('customer', customer.name, 'Link');
                cy.fill_field('vehicle', vehicle.name, 'Link');
                cy.fill_field('service_type', 'Brake Service');
                
                // Set appointment date (tomorrow)
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                const dateString = tomorrow.toISOString().split('T')[0];
                
                cy.fill_field('scheduled_date', dateString, 'Date');
                cy.fill_field('scheduled_time', '10:00:00', 'Time');
                cy.fill_field('estimated_duration', '90');
                
                // Save appointment
                cy.get('.primary-action').click();
                cy.wait(2000);
                
                // Verify appointment creation
                cy.get('[data-fieldname="status"] .control-value').should('contain', 'Scheduled');
                
                // Convert to service order
                cy.get('[data-label="Create Service Order"]').click();
                cy.wait(2000);
                
                // Verify service order creation from appointment
                cy.url().should('include', '/app/service-order/');
                cy.get('[data-fieldname="appointment"] .control-value').should('not.be.empty');
            });
        });
    });

    it('Test Inventory Integration with Service Orders', () => {
        // Create item first
        cy.create_records({
            doctype: 'Item',
            item_code: 'TEST-OIL-FILTER',
            item_name: 'Test Oil Filter',
            item_group: 'Auto Parts',
            stock_uom: 'Nos',
            is_stock_item: 1
        }).then((item) => {
            // Create customer and vehicle
            cy.create_records({
                doctype: 'Customer', 
                customer_name: 'Inventory Test Customer',
                customer_group: 'Individual',
                territory: 'Oman'
            }).then((customer) => {
                cy.create_records({
                    doctype: 'Vehicle',
                    customer: customer.name,
                    vin: '1HGBH41JXMN108888',
                    license_plate: 'I-88888',
                    make: 'Nissan',
                    model: 'Altima'
                }).then((vehicle) => {
                    // Create service order with parts
                    cy.visit('/app/service-order/new-service-order-1');
                    cy.wait(1000);
                    
                    cy.fill_field('customer', customer.name, 'Link');
                    cy.fill_field('vehicle', vehicle.name, 'Link');
                    cy.fill_field('service_type', 'Oil Change');
                    
                    // Add parts required
                    cy.get('[data-fieldname="parts_required"] .grid-add-row').click();
                    cy.wait(500);
                    
                    cy.get('[data-fieldname="parts_required"] .grid-row:last [data-fieldname="item_code"] input').type(item.item_code);
                    cy.get('[data-fieldname="parts_required"] .grid-row:last [data-fieldname="qty"] input').clear().type('1');
                    cy.get('[data-fieldname="parts_required"] .grid-row:last [data-fieldname="rate"] input').clear().type('15');
                    
                    // Save service order
                    cy.get('.primary-action').click();
                    cy.wait(2000);
                    
                    // Verify parts are listed
                    cy.get('[data-fieldname="parts_required"] .grid-row').should('contain', item.item_code);
                });
            });
        });
    });

    it('Test Multi-Language Invoice Generation', () => {
        // Test English invoice
        cy.create_records({
            doctype: 'Customer',
            customer_name: 'English Invoice Customer',
            customer_group: 'Individual', 
            territory: 'Oman',
            language: 'en'
        }).then((customer) => {
            cy.visit('/app/sales-invoice/new-sales-invoice-1');
            cy.wait(1000);
            
            cy.fill_field('customer', customer.name, 'Link');
            cy.fill_field('language', 'en', 'Select');
            
            // Add item
            cy.get('[data-fieldname="items"] .grid-add-row').click();
            cy.wait(500);
            
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="item_code"] input').type('SERVICE-001');
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="description"] textarea').type('Service Charge');
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="qty"] input').clear().type('1');
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="rate"] input').clear().type('50');
            
            // Save invoice
            cy.get('.primary-action').click();
            cy.wait(2000);
            
            // Verify language setting
            cy.get('[data-fieldname="language"] .control-value').should('contain', 'en');
        });

        // Test Arabic invoice
        cy.create_records({
            doctype: 'Customer',
            customer_name: 'زبون الفاتورة العربية',
            customer_group: 'Individual',
            territory: 'Oman', 
            language: 'ar'
        }).then((customer) => {
            cy.visit('/app/sales-invoice/new-sales-invoice-1');
            cy.wait(1000);
            
            cy.fill_field('customer', customer.name, 'Link');
            cy.fill_field('language', 'ar', 'Select');
            
            // Add item with Arabic description
            cy.get('[data-fieldname="items"] .grid-add-row').click();
            cy.wait(500);
            
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="item_code"] input').type('SERVICE-AR-001');
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="description"] textarea').type('رسوم الخدمة');
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="qty"] input').clear().type('1');
            cy.get('[data-fieldname="items"] .grid-row:last [data-fieldname="rate"] input').clear().type('50');
            
            // Save Arabic invoice
            cy.get('.primary-action').click();
            cy.wait(2000);
            
            // Verify Arabic language and content
            cy.get('[data-fieldname="language"] .control-value').should('contain', 'ar');
            cy.get('[data-fieldname="items"] .grid-row').should('contain', 'رسوم الخدمة');
        });
    });

    it('Test Error Handling and Validation', () => {
        // Test duplicate VIN validation
        cy.visit('/app/vehicle/new-vehicle-1');
        cy.wait(1000);
        
        // Try to create vehicle with duplicate VIN
        cy.fill_field('vin', '1HGBH41JXMN109186'); // Same as test data
        cy.fill_field('license_plate', 'DUP-001');
        
        cy.get('.primary-action').click();
        cy.wait(1000);
        
        // Should show validation error
        cy.get('.msgprint').should('be.visible');
        cy.get('.msgprint').should('contain', 'already exists');
        
        // Close error dialog
        cy.get('.msgprint .btn-primary').click();
        
        // Test required field validation
        cy.visit('/app/customer/new-customer-1');
        cy.wait(1000);
        
        // Try to save without required fields
        cy.get('.primary-action').click();
        cy.wait(1000);
        
        // Should show validation errors
        cy.get('.has-error').should('exist');
        cy.get('.help-block').should('contain', 'is mandatory');
    });

    after(() => {
        // Cleanup test data
        cy.call('frappe.desk.cleanup.delete_test_data');
    });
});
