/**
 * Integration Bridge Usage Examples - Universal Workshop ERP
 * 
 * This file demonstrates how to use the integration bridge system
 * for progressive migration between traditional and V2 frontends
 */

// Wait for bridge to be available
$(document).ready(async () => {
    // Check if V2 bridge is available
    if (window.UniversalWorkshopV2 && await window.UniversalWorkshopV2.isV2Available()) {
        console.log('🎉 V2 Bridge is available! Running examples...');
        runIntegrationExamples();
    } else {
        console.log('ℹ️ V2 Bridge not available - traditional frontend only');
    }
});

async function runIntegrationExamples() {
    const bridge = window.UniversalWorkshopV2;
    
    try {
        // Example 1: Progressive Component Replacement
        await demonstrateComponentReplacement(bridge);
        
        // Example 2: Data Synchronization
        await demonstrateDataSync(bridge);
        
        // Example 3: Event Communication
        await demonstrateEventSystem(bridge);
        
        // Example 4: Form Integration
        await demonstrateFormIntegration(bridge);
        
        console.log('✅ All integration examples completed successfully');
        
    } catch (error) {
        console.error('❌ Integration examples failed:', error);
    }
}

// Example 1: Progressive Component Replacement
async function demonstrateComponentReplacement(bridge) {
    console.log('📱 Example 1: Progressive Component Replacement');
    
    try {
        // Replace traditional data tables with V2 DataTable component
        const dataTableContainers = document.querySelectorAll('.datatable-wrapper');
        
        if (dataTableContainers.length > 0) {
            console.log(`Found ${dataTableContainers.length} data tables to upgrade`);
            
            for (let i = 0; i < Math.min(2, dataTableContainers.length); i++) {
                const container = dataTableContainers[i];
                
                // Create unique selector for this container
                const containerId = `datatable-v2-${i}`;
                container.id = containerId;
                
                // Replace with V2 DataTable
                await bridge.replaceComponent(
                    `#${containerId}`,
                    'DataTable',
                    {
                        columns: [
                            { key: 'name', label: 'Name', sortable: true },
                            { key: 'status', label: 'Status', filterable: true },
                            { key: 'modified', label: 'Modified', type: 'date' }
                        ],
                        data: [],
                        arabic: true,
                        pagination: true,
                        search: true
                    }
                );
                
                console.log(`✅ Replaced data table ${i + 1} with V2 component`);
            }
        }
        
        // Embed V2 components in specific areas
        bridge.embedComponent('.page-actions', 'QuickActions', {
            actions: [
                { label: 'New Service Order', action: 'create_service_order' },
                { label: 'Scan Barcode', action: 'scan_barcode' },
                { label: 'Customer Search', action: 'search_customers' }
            ]
        });
        
    } catch (error) {
        console.error('Component replacement example failed:', error);
    }
}

// Example 2: Data Synchronization
async function demonstrateDataSync(bridge) {
    console.log('🔄 Example 2: Data Synchronization');
    
    try {
        // Sync service orders
        console.log('Syncing service orders...');
        const serviceOrdersSync = await bridge.syncState('serviceOrders');
        console.log('✅ Service orders synced:', serviceOrdersSync);
        
        // Sync customers
        console.log('Syncing customers...');
        const customersSync = await bridge.syncState('customers');
        console.log('✅ Customers synced:', customersSync);
        
        // Bridge form data from traditional to V2
        if (cur_frm && cur_frm.doctype) {
            const formData = cur_frm.get_values();
            const bridgedData = await bridge.bridgeFormData(cur_frm.doctype, formData);
            console.log('✅ Form data bridged:', bridgedData);
        }
        
    } catch (error) {
        console.error('Data sync example failed:', error);
    }
}

// Example 3: Event Communication
async function demonstrateEventSystem(bridge) {
    console.log('📡 Example 3: Event Communication');
    
    try {
        // Listen to V2 events
        bridge.onEvent('component_embedded', (data) => {
            console.log('🎯 V2 component embedded:', data.componentName);
            
            // Show notification in traditional UI
            frappe.show_alert({
                message: `V2 component "${data.componentName}" loaded`,
                indicator: 'green'
            });
        });
        
        bridge.onEvent('data_synced', (data) => {
            console.log('🔄 Data synchronized:', data.dataType);
        });
        
        // Emit events to V2
        bridge.emitEvent('traditional_form_updated', {
            doctype: cur_frm?.doctype,
            docname: cur_frm?.docname,
            timestamp: Date.now()
        });
        
        // Bridge Frappe events to V2
        $(document).on('form-refresh', (event, frm) => {
            bridge.emitEvent('frappe_form_refreshed', {
                doctype: frm.doctype,
                docname: frm.docname,
                is_new: frm.is_new()
            });
        });
        
        console.log('✅ Event system configured');
        
    } catch (error) {
        console.error('Event system example failed:', error);
    }
}

// Example 4: Form Integration
async function demonstrateFormIntegration(bridge) {
    console.log('📝 Example 4: Form Integration');
    
    try {
        // Add V2 components to current form if available
        if (cur_frm && cur_frm.doctype) {
            const doctype = cur_frm.doctype;
            
            // Add file upload component for attachments
            if (cur_frm.fields_dict.attachments) {
                bridge.embedComponent(
                    cur_frm.fields_dict.attachments.wrapper,
                    'FileUpload',
                    {
                        doctype: doctype,
                        docname: cur_frm.docname,
                        multiple: true,
                        allowedTypes: ['image/*', '.pdf', '.doc', '.docx'],
                        maxSize: 10 * 1024 * 1024, // 10MB
                        arabic: true
                    }
                );
            }
            
            // Add enhanced search for link fields
            cur_frm.fields.forEach(field => {
                if (field.df.fieldtype === 'Link' && field.df.options) {
                    // Enhance link field with V2 search component
                    bridge.embedComponent(
                        field.input_area,
                        'EnhancedSearch',
                        {
                            doctype: field.df.options,
                            placeholder: `Search ${field.df.options}...`,
                            arabic: true,
                            onSelect: (value) => {
                                cur_frm.set_value(field.df.fieldname, value);
                            }
                        }
                    );
                }
            });
            
            console.log(`✅ Enhanced form for ${doctype}`);
        }
        
        // Progressive migration for specific doctypes
        const migrationMap = {
            'Service Order': {
                components: [
                    { 
                        name: 'ServiceOrderKanban', 
                        selector: '.layout-main-section',
                        props: { arabic: true, realtime: true }
                    }
                ],
                syncData: ['serviceOrders', 'vehicles', 'technicians']
            },
            'Customer': {
                components: [
                    {
                        name: 'CustomerPortal',
                        selector: '.form-dashboard',
                        props: { showVehicles: true, showHistory: true }
                    }
                ],
                syncData: ['customers', 'vehicles']
            }
        };
        
        if (cur_frm && migrationMap[cur_frm.doctype]) {
            await bridge.migrateView(cur_frm.doctype, migrationMap[cur_frm.doctype]);
            console.log(`✅ Migrated view for ${cur_frm.doctype}`);
        }
        
    } catch (error) {
        console.error('Form integration example failed:', error);
    }
}

// Feature flag management example
async function demonstrateFeatureFlags(bridge) {
    console.log('🚀 Example: Feature Flag Management');
    
    try {
        // Enable/disable V2 features progressively
        const features = [
            'enhanced_search',
            'real_time_sync',
            'offline_support',
            'push_notifications',
            'arabic_voice_commands'
        ];
        
        for (const feature of features) {
            // Check if feature should be enabled for current user
            const shouldEnable = await checkFeatureEligibility(feature);
            
            if (shouldEnable) {
                await bridge.enableFeature(feature, true);
                console.log(`✅ Enabled feature: ${feature}`);
            }
        }
        
    } catch (error) {
        console.error('Feature flag example failed:', error);
    }
}

// Helper function to check feature eligibility
async function checkFeatureEligibility(feature) {
    // This would typically check user roles, license level, etc.
    const userRoles = frappe.user_roles || [];
    
    const featureRequirements = {
        'enhanced_search': () => true, // Available to all
        'real_time_sync': () => userRoles.includes('Workshop Manager'),
        'offline_support': () => userRoles.includes('Workshop Technician'),
        'push_notifications': () => userRoles.includes('Workshop Manager'),
        'arabic_voice_commands': () => frappe.boot.lang === 'ar'
    };
    
    const requirement = featureRequirements[feature];
    return requirement ? requirement() : false;
}

// Automated testing for integration
async function runIntegrationTests() {
    console.log('🧪 Running Integration Tests');
    
    const tests = [
        {
            name: 'Bridge Availability',
            test: () => window.UniversalWorkshopV2 !== undefined
        },
        {
            name: 'V2 Config Access',
            test: async () => {
                const config = window.UniversalWorkshopV2.getConfig();
                return config && config.assets;
            }
        },
        {
            name: 'Module Loading',
            test: async () => {
                try {
                    await window.UniversalWorkshopV2.loadModule('main');
                    return true;
                } catch (error) {
                    return false;
                }
            }
        },
        {
            name: 'Data Sync',
            test: async () => {
                try {
                    await window.UniversalWorkshopV2.syncState('customers');
                    return true;
                } catch (error) {
                    return false;
                }
            }
        }
    ];
    
    const results = [];
    
    for (const test of tests) {
        try {
            const result = await test.test();
            results.push({ name: test.name, passed: result });
            console.log(`${result ? '✅' : '❌'} ${test.name}: ${result ? 'PASS' : 'FAIL'}`);
        } catch (error) {
            results.push({ name: test.name, passed: false, error: error.message });
            console.log(`❌ ${test.name}: FAIL (${error.message})`);
        }
    }
    
    const passedTests = results.filter(r => r.passed).length;
    const totalTests = results.length;
    
    console.log(`\n📊 Integration Test Results: ${passedTests}/${totalTests} passed`);
    
    return results;
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.UniversalWorkshopIntegrationExamples = {
        runIntegrationExamples,
        demonstrateComponentReplacement,
        demonstrateDataSync,
        demonstrateEventSystem,
        demonstrateFormIntegration,
        demonstrateFeatureFlags,
        runIntegrationTests
    };
}