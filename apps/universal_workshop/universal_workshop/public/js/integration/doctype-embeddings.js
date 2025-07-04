/**
 * DocType Component Embedding - Universal Workshop ERP
 * 
 * Specific component embedding examples for key DocTypes
 * Progressive enhancement of traditional Frappe forms with V2 components
 */

class DocTypeEmbeddings {
    constructor() {
        this.embeddings = new Map();
        this.initialized = false;
        this.bridge = null;
        
        this.init();
    }
    
    async init() {
        // Wait for V2 bridge to be available
        if (window.UniversalWorkshopV2 && await window.UniversalWorkshopV2.isV2Available()) {
            this.bridge = window.UniversalWorkshopV2;
            this.initialized = true;
            this.setupDocTypeHooks();
            console.log('✅ DocType embeddings initialized');
        } else {
            // Retry after a delay
            setTimeout(() => this.init(), 1000);
        }
    }
    
    setupDocTypeHooks() {
        // Hook into Frappe form events
        $(document).on('form-refresh', (event, frm) => {
            this.onFormRefresh(frm);
        });
        
        $(document).on('form-load', (event, frm) => {
            this.onFormLoad(frm);
        });
        
        // Hook into list view events
        $(document).on('list-view-refresh', (event, listView) => {
            this.onListViewRefresh(listView);
        });
    }
    
    async onFormRefresh(frm) {
        if (!this.initialized || !frm) return;
        
        try {
            const doctype = frm.doctype;
            const embeddingConfig = this.getEmbeddingConfig(doctype);
            
            if (embeddingConfig) {
                await this.embedComponentsForDocType(frm, embeddingConfig);
            }
        } catch (error) {
            console.error('Form refresh embedding failed:', error);
        }
    }
    
    async onFormLoad(frm) {
        if (!this.initialized || !frm) return;
        
        try {
            // Add V2 enhancement indicators
            this.addV2Indicators(frm);
            
            // Setup progressive enhancement
            await this.setupProgressiveEnhancement(frm);
        } catch (error) {
            console.error('Form load embedding failed:', error);
        }
    }
    
    async onListViewRefresh(listView) {
        if (!this.initialized || !listView) return;
        
        try {
            const doctype = listView.doctype;
            await this.enhanceListView(listView, doctype);
        } catch (error) {
            console.error('List view enhancement failed:', error);
        }
    }
    
    getEmbeddingConfig(doctype) {
        const configs = {
            'Service Order': {
                components: [
                    {
                        name: 'ServiceOrderTimeline',
                        selector: '.form-timeline',
                        position: 'prepend',
                        props: { realtime: true, arabic: true }
                    },
                    {
                        name: 'TechnicianAssignment',
                        selector: '.form-sidebar',
                        position: 'append',
                        props: { showAvailability: true }
                    },
                    {
                        name: 'PartsRequirements',
                        selector: '.form-section[data-section="parts"]',
                        position: 'replace',
                        props: { showInventory: true, allowOrdering: true }
                    }
                ],
                enhancements: [
                    'vehicleSearch',
                    'customerPortal',
                    'realTimeUpdates',
                    'mobileOptimization'
                ]
            },
            
            'Customer': {
                components: [
                    {
                        name: 'CustomerAnalytics',
                        selector: '.form-dashboard',
                        position: 'append',
                        props: { showCharts: true, timeRange: '12M' }
                    },
                    {
                        name: 'VehicleGallery',
                        selector: '.form-section[data-section="vehicles"]',
                        position: 'replace',
                        props: { showThumbnails: true, allowAdd: true }
                    },
                    {
                        name: 'CommunicationCenter',
                        selector: '.form-sidebar',
                        position: 'append',
                        props: { sms: true, whatsapp: true, arabic: true }
                    }
                ],
                enhancements: [
                    'loyaltyProgram',
                    'serviceHistory',
                    'communicationTracking'
                ]
            },
            
            'Vehicle': {
                components: [
                    {
                        name: 'VehicleInspection',
                        selector: '.form-section[data-section="inspection"]',
                        position: 'replace',
                        props: { camera: true, voice: true, arabic: true }
                    },
                    {
                        name: 'MaintenanceSchedule',
                        selector: '.form-dashboard',
                        position: 'prepend',
                        props: { predictive: true, alerts: true }
                    },
                    {
                        name: 'ServiceHistory',
                        selector: '.form-section[data-section="history"]',
                        position: 'replace',
                        props: { timeline: true, costs: true }
                    }
                ],
                enhancements: [
                    'vinDecoder',
                    'partsCompatibility',
                    'serviceReminders'
                ]
            },
            
            'Technician': {
                components: [
                    {
                        name: 'TechnicianDashboard',
                        selector: '.form-dashboard',
                        position: 'replace',
                        props: { workload: true, performance: true, mobile: true }
                    },
                    {
                        name: 'SkillMatrix',
                        selector: '.form-section[data-section="skills"]',
                        position: 'replace',
                        props: { certifications: true, training: true }
                    },
                    {
                        name: 'WorkSchedule',
                        selector: '.form-section[data-section="schedule"]',
                        position: 'replace',
                        props: { calendar: true, availability: true }
                    }
                ],
                enhancements: [
                    'mobileWorkflow',
                    'performanceTracking',
                    'trainingProgress'
                ]
            }
        };
        
        return configs[doctype];
    }
    
    async embedComponentsForDocType(frm, config) {
        const doctype = frm.doctype;
        const docname = frm.docname;
        
        // Store embedding info
        if (!this.embeddings.has(doctype)) {
            this.embeddings.set(doctype, new Map());
        }
        
        const doctypeEmbeddings = this.embeddings.get(doctype);
        
        // Embed components
        for (const componentConfig of config.components) {
            try {
                const componentId = `${doctype}-${componentConfig.name}-${docname}`;
                
                // Check if already embedded
                if (doctypeEmbeddings.has(componentId)) {
                    continue;
                }
                
                // Prepare component props
                const props = {
                    ...componentConfig.props,
                    doctype: doctype,
                    docname: docname,
                    frm: frm,
                    readonly: !frm.perm[0].write
                };
                
                // Find target element
                const targetElement = document.querySelector(componentConfig.selector);
                if (!targetElement) {
                    console.warn(`Target element not found: ${componentConfig.selector}`);
                    continue;
                }
                
                // Create container for component
                const container = this.createComponentContainer(componentId, componentConfig);
                
                // Position the container
                this.positionContainer(targetElement, container, componentConfig.position);
                
                // Embed the component
                const instance = await this.bridge.loadComponent(
                    componentConfig.name,
                    `#${componentId}`,
                    props
                );
                
                // Store embedding info
                doctypeEmbeddings.set(componentId, {
                    component: componentConfig.name,
                    container: container,
                    instance: instance,
                    embedded_at: Date.now()
                });
                
                console.log(`✅ Embedded ${componentConfig.name} for ${doctype}`);
                
            } catch (error) {
                console.error(`Failed to embed ${componentConfig.name}:`, error);
            }
        }
        
        // Apply enhancements
        if (config.enhancements) {
            await this.applyEnhancements(frm, config.enhancements);
        }
    }
    
    createComponentContainer(componentId, componentConfig) {
        const container = document.createElement('div');
        container.id = componentId;
        container.className = 'v2-component-container';
        container.setAttribute('data-component', componentConfig.name);
        container.setAttribute('data-position', componentConfig.position);
        
        // Add loading state
        container.innerHTML = `
            <div class="v2-component-loading">
                <div class="loading-spinner"></div>
                <span>Loading ${componentConfig.name}...</span>
            </div>
        `;
        
        return container;
    }
    
    positionContainer(targetElement, container, position) {
        switch (position) {
            case 'prepend':
                targetElement.insertBefore(container, targetElement.firstChild);
                break;
            case 'append':
                targetElement.appendChild(container);
                break;
            case 'replace':
                // Hide original content and add container
                targetElement.style.display = 'none';
                targetElement.parentNode.insertBefore(container, targetElement.nextSibling);
                break;
            case 'before':
                targetElement.parentNode.insertBefore(container, targetElement);
                break;
            case 'after':
                targetElement.parentNode.insertBefore(container, targetElement.nextSibling);
                break;
            default:
                targetElement.appendChild(container);
        }
    }
    
    async applyEnhancements(frm, enhancements) {
        for (const enhancement of enhancements) {
            try {
                await this.applySpecificEnhancement(frm, enhancement);
            } catch (error) {
                console.error(`Failed to apply enhancement ${enhancement}:`, error);
            }
        }
    }
    
    async applySpecificEnhancement(frm, enhancement) {
        const enhancementMap = {
            'vehicleSearch': () => this.enhanceVehicleSearch(frm),
            'customerPortal': () => this.enhanceCustomerPortal(frm),
            'realTimeUpdates': () => this.enableRealTimeUpdates(frm),
            'mobileOptimization': () => this.optimizeForMobile(frm),
            'loyaltyProgram': () => this.enhanceLoyaltyProgram(frm),
            'serviceHistory': () => this.enhanceServiceHistory(frm),
            'communicationTracking': () => this.enhanceCommunicationTracking(frm),
            'vinDecoder': () => this.enhanceVinDecoder(frm),
            'partsCompatibility': () => this.enhancePartsCompatibility(frm),
            'serviceReminders': () => this.enhanceServiceReminders(frm),
            'mobileWorkflow': () => this.enhanceMobileWorkflow(frm),
            'performanceTracking': () => this.enhancePerformanceTracking(frm),
            'trainingProgress': () => this.enhanceTrainingProgress(frm)
        };
        
        const enhancementFn = enhancementMap[enhancement];
        if (enhancementFn) {
            await enhancementFn();
        }
    }
    
    // Enhancement implementations
    async enhanceVehicleSearch(frm) {
        if (frm.fields_dict.vehicle) {
            await this.bridge.replaceComponent(
                frm.fields_dict.vehicle.wrapper,
                'EnhancedVehicleSearch',
                {
                    doctype: 'Vehicle',
                    onSelect: (vehicle) => frm.set_value('vehicle', vehicle.name),
                    showDetails: true,
                    arabic: true
                }
            );
        }
    }
    
    async enhanceCustomerPortal(frm) {
        if (frm.fields_dict.customer) {
            // Add customer portal link
            const portalButton = frm.add_custom_button(__('Customer Portal'), () => {
                const customer = frm.doc.customer;
                if (customer) {
                    window.open(`/customer-portal/${customer}`, '_blank');
                }
            });
            
            $(portalButton).addClass('btn-primary');
        }
    }
    
    async enableRealTimeUpdates(frm) {
        if (this.bridge && frm.docname) {
            // Subscribe to real-time updates for this document
            this.bridge.onEvent('document_updated', (data) => {
                if (data.doctype === frm.doctype && data.docname === frm.docname) {
                    frm.reload_doc();
                }
            });
        }
    }
    
    async optimizeForMobile(frm) {
        // Add mobile-specific CSS classes
        $(frm.wrapper).addClass('mobile-optimized');
        
        // Enhance form for touch interaction
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            $(frm.wrapper).addClass('mobile-form');
            
            // Make buttons touch-friendly
            $('.btn', frm.wrapper).addClass('btn-touch');
        }
    }
    
    async enhanceListView(listView, doctype) {
        try {
            // Add V2 list enhancements
            const listContainer = listView.wrapper;
            
            // Add enhanced search
            if (listView.page.wrapper.find('.list-search').length > 0) {
                await this.bridge.embedComponent(
                    listView.page.wrapper.find('.list-search')[0],
                    'EnhancedListSearch',
                    {
                        doctype: doctype,
                        onSearch: (query) => listView.refresh(),
                        arabic: true,
                        realtime: true
                    }
                );
            }
            
            // Add bulk actions
            if (listView.page.wrapper.find('.list-row-check').length > 0) {
                await this.bridge.embedComponent(
                    listView.page.wrapper.find('.page-actions')[0],
                    'BulkActions',
                    {
                        doctype: doctype,
                        onAction: (action, selected) => this.handleBulkAction(action, selected),
                        actions: this.getBulkActionsForDocType(doctype)
                    }
                );
            }
            
        } catch (error) {
            console.error('List view enhancement failed:', error);
        }
    }
    
    getBulkActionsForDocType(doctype) {
        const bulkActions = {
            'Service Order': [
                { label: 'Assign Technician', action: 'assign_technician' },
                { label: 'Update Status', action: 'update_status' },
                { label: 'Send Notifications', action: 'send_notifications' }
            ],
            'Customer': [
                { label: 'Send Marketing', action: 'send_marketing' },
                { label: 'Update Territory', action: 'update_territory' },
                { label: 'Export Data', action: 'export_data' }
            ],
            'Vehicle': [
                { label: 'Schedule Maintenance', action: 'schedule_maintenance' },
                { label: 'Send Reminders', action: 'send_reminders' },
                { label: 'Update Status', action: 'update_status' }
            ]
        };
        
        return bulkActions[doctype] || [];
    }
    
    async handleBulkAction(action, selectedItems) {
        console.log(`Executing bulk action: ${action} on ${selectedItems.length} items`);
        
        // This would implement the actual bulk action logic
        try {
            await frappe.call({
                method: 'universal_workshop.api.bulk_actions.execute_bulk_action',
                args: {
                    action: action,
                    items: selectedItems
                },
                callback: (response) => {
                    if (response.message) {
                        frappe.show_alert({
                            message: __('Bulk action completed successfully'),
                            indicator: 'green'
                        });
                    }
                }
            });
        } catch (error) {
            frappe.show_alert({
                message: __('Bulk action failed: {0}', [error.message]),
                indicator: 'red'
            });
        }
    }
    
    addV2Indicators(frm) {
        // Add indicator that V2 enhancements are available
        const indicator = $(`
            <div class="v2-enhancement-indicator">
                <i class="fa fa-magic"></i>
                <span>V2 Enhanced</span>
            </div>
        `).css({
            position: 'absolute',
            top: '10px',
            right: '10px',
            background: '#28a745',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '11px',
            zIndex: 1000
        });
        
        $(frm.wrapper).css('position', 'relative').append(indicator);
        
        // Fade out after 3 seconds
        setTimeout(() => {
            indicator.fadeOut();
        }, 3000);
    }
    
    async setupProgressiveEnhancement(frm) {
        // Add progressive enhancement button
        const enhancementButton = frm.add_custom_button(__('Enable V2 Features'), async () => {
            try {
                await this.enableAllV2Features(frm);
                frappe.show_alert({
                    message: __('V2 features enabled'),
                    indicator: 'green'
                });
            } catch (error) {
                frappe.show_alert({
                    message: __('Failed to enable V2 features: {0}', [error.message]),
                    indicator: 'red'
                });
            }
        });
        
        $(enhancementButton).addClass('btn-default').css('margin-left', '8px');
    }
    
    async enableAllV2Features(frm) {
        const config = this.getEmbeddingConfig(frm.doctype);
        if (config) {
            await this.embedComponentsForDocType(frm, config);
        }
        
        // Enable feature flags for this user
        await this.bridge.enableFeature(`${frm.doctype.toLowerCase()}_v2_features`, true);
    }
    
    // Cleanup methods
    cleanupEmbeddings(doctype, docname) {
        if (this.embeddings.has(doctype)) {
            const doctypeEmbeddings = this.embeddings.get(doctype);
            const keysToRemove = [];
            
            for (const [key, embedding] of doctypeEmbeddings) {
                if (key.includes(docname)) {
                    // Remove container from DOM
                    if (embedding.container && embedding.container.parentNode) {
                        embedding.container.parentNode.removeChild(embedding.container);
                    }
                    keysToRemove.push(key);
                }
            }
            
            keysToRemove.forEach(key => doctypeEmbeddings.delete(key));
        }
    }
    
    getEmbeddingStats() {
        const stats = {
            total_embeddings: 0,
            by_doctype: {},
            by_component: {}
        };
        
        for (const [doctype, embeddings] of this.embeddings) {
            stats.by_doctype[doctype] = embeddings.size;
            stats.total_embeddings += embeddings.size;
            
            for (const [, embedding] of embeddings) {
                const component = embedding.component;
                stats.by_component[component] = (stats.by_component[component] || 0) + 1;
            }
        }
        
        return stats;
    }
}

// Initialize DocType embeddings
$(document).ready(() => {
    if (window.location.pathname.startsWith('/app')) {
        window.doctypeEmbeddings = new DocTypeEmbeddings();
        
        // Global cleanup on page navigation
        $(window).on('beforeunload', () => {
            if (window.doctypeEmbeddings && cur_frm) {
                window.doctypeEmbeddings.cleanupEmbeddings(cur_frm.doctype, cur_frm.docname);
            }
        });
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DocTypeEmbeddings;
}