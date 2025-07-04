/**
 * Parts Auto-Suggestion Frontend
 * Provides real-time parts suggestions with Arabic localization and RTL support
 * Integrates with Service Estimate form for automotive workshop operations
 * Supports arabic language interface with proper RTL text direction
 */

class PartsAutoSuggestionUI {
    constructor() {
        this.currentSuggestions = [];
        this.isLoading = false;
        this.debounceTimer = null;
        this.language = frappe.boot.lang || 'en';
        this.suggestionCache = new Map();
        this.feedbackMode = true;
    }

    /**
     * Initialize parts suggestion for a form
     */
    initializeForForm(frm) {
        this.frm = frm;
        this.setupSuggestionUI();
        this.bindEvents();
        this.loadInitialSuggestions();
    }

    /**
     * Set up the suggestion UI elements
     */
    setupSuggestionUI() {
        // Create suggestion panel
        const $suggestionPanel = $(`
            <div class="parts-suggestion-panel" style="display: none;">
                <div class="suggestion-header">
                    <h6>${__('Suggested Parts')}</h6>
                    <div class="suggestion-controls">
                        <button class="btn btn-xs btn-default refresh-suggestions">
                            <i class="fa fa-refresh"></i> ${__('Refresh')}
                        </button>
                        <button class="btn btn-xs btn-default toggle-suggestions">
                            <i class="fa fa-eye-slash"></i> ${__('Hide')}
                        </button>
                    </div>
                </div>
                <div class="suggestion-content">
                    <div class="suggestion-loading" style="display: none;">
                        <i class="fa fa-spinner fa-spin"></i> ${__('Loading suggestions...')}
                    </div>
                    <div class="suggestion-list"></div>
                    <div class="suggestion-empty" style="display: none;">
                        <p class="text-muted">${__('No suggestions available')}</p>
                    </div>
                </div>
                <div class="suggestion-search">
                    <input type="text" class="form-control parts-search-input" 
                           placeholder="${__('Search parts...')}" 
                           dir="${this.language === 'ar' ? 'rtl' : 'ltr'}">
                    <div class="search-results" style="display: none;"></div>
                </div>
            </div>
        `);

        // Insert after the items table
        const $itemsTable = this.frm.fields_dict.estimate_items.$wrapper;
        $itemsTable.after($suggestionPanel);

        this.$suggestionPanel = $suggestionPanel;
        this.setupSuggestionStyles();
    }

    /**
     * Set up CSS styles for suggestions
     */
    setupSuggestionStyles() {
        if ($('#parts-suggestion-styles').length === 0) {
            $('head').append(`
                <style id="parts-suggestion-styles">
                .parts-suggestion-panel {
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    margin: 15px 0;
                    background: #fff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }

                .suggestion-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 15px;
                    background: #f8f9fa;
                    border-bottom: 1px solid #ddd;
                    border-radius: 6px 6px 0 0;
                }

                .suggestion-header h6 {
                    margin: 0;
                    color: #333;
                    font-weight: 600;
                }

                .suggestion-controls {
                    display: flex;
                    gap: 5px;
                }

                .suggestion-content {
                    padding: 15px;
                    max-height: 400px;
                    overflow-y: auto;
                }

                .suggestion-item {
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 12px;
                    margin-bottom: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    position: relative;
                }

                .suggestion-item:hover {
                    border-color: #007bff;
                    background-color: #f8f9ff;
                    transform: translateY(-1px);
                }

                .suggestion-item.out-of-stock {
                    border-color: #dc3545;
                    background-color: #fff5f5;
                }

                .suggestion-item-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 8px;
                }

                .suggestion-item-name {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 4px;
                }

                .suggestion-confidence {
                    background: #28a745;
                    color: white;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                }

                .suggestion-confidence.medium {
                    background: #ffc107;
                    color: #333;
                }

                .suggestion-confidence.low {
                    background: #6c757d;
                }

                .suggestion-reason {
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 4px;
                }

                .suggestion-details {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 12px;
                    color: #888;
                }

                .suggestion-stock {
                    font-weight: 500;
                }

                .suggestion-stock.in-stock {
                    color: #28a745;
                }

                .suggestion-stock.out-of-stock {
                    color: #dc3545;
                }

                .suggestion-actions {
                    display: flex;
                    gap: 5px;
                    margin-top: 8px;
                }

                .suggestion-search {
                    padding: 15px;
                    border-top: 1px solid #ddd;
                    background: #f8f9fa;
                }

                .search-results {
                    position: absolute;
                    top: 100%;
                    left: 0;
                    right: 0;
                    background: white;
                    border: 1px solid #ddd;
                    border-top: none;
                    max-height: 200px;
                    overflow-y: auto;
                    z-index: 1000;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }

                .search-result-item {
                    padding: 8px 12px;
                    cursor: pointer;
                    border-bottom: 1px solid #f0f0f0;
                }

                .search-result-item:hover {
                    background: #f8f9fa;
                }

                .search-result-item:last-child {
                    border-bottom: none;
                }

                /* Arabic RTL Support */
                .rtl-layout .parts-suggestion-panel,
                [dir="rtl"] .parts-suggestion-panel {
                    direction: rtl;
                    text-align: right;
                }

                .rtl-layout .suggestion-header,
                [dir="rtl"] .suggestion-header {
                    flex-direction: row-reverse;
                }

                .rtl-layout .suggestion-item-header,
                [dir="rtl"] .suggestion-item-header {
                    flex-direction: row-reverse;
                }

                .rtl-layout .suggestion-details,
                [dir="rtl"] .suggestion-details {
                    flex-direction: row-reverse;
                }

                /* Mobile responsive */
                @media (max-width: 768px) {
                    .suggestion-header {
                        flex-direction: column;
                        gap: 10px;
                        text-align: center;
                    }

                    .suggestion-item-header {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                    .suggestion-details {
                        flex-direction: column;
                        gap: 4px;
                    }
                }
                </style>
            `);
        }
    }

    /**
     * Bind event handlers
     */
    bindEvents() {
        // Refresh suggestions
        this.$suggestionPanel.on('click', '.refresh-suggestions', () => {
            this.loadSuggestions(true);
        });

        // Toggle suggestions panel
        this.$suggestionPanel.on('click', '.toggle-suggestions', (e) => {
            const $btn = $(e.currentTarget);
            const $content = this.$suggestionPanel.find('.suggestion-content, .suggestion-search');

            if ($content.is(':visible')) {
                $content.hide();
                $btn.html('<i class="fa fa-eye"></i> ' + __('Show'));
            } else {
                $content.show();
                $btn.html('<i class="fa fa-eye-slash"></i> ' + __('Hide'));
            }
        });

        // Add suggestion to estimate
        this.$suggestionPanel.on('click', '.add-suggestion', (e) => {
            e.stopPropagation();
            const itemCode = $(e.currentTarget).data('item-code');
            const quantity = $(e.currentTarget).data('quantity') || 1;
            this.addItemToEstimate(itemCode, quantity);
        });

        // Suggestion feedback
        this.$suggestionPanel.on('click', '.suggestion-feedback', (e) => {
            e.stopPropagation();
            const itemCode = $(e.currentTarget).data('item-code');
            const useful = $(e.currentTarget).data('useful');
            this.recordFeedback(itemCode, useful);
        });

        // Search functionality
        this.$suggestionPanel.on('input', '.parts-search-input', (e) => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.performSearch($(e.target).val());
            }, 300);
        });

        // Clear search when clicking outside
        $(document).on('click', (e) => {
            if (!$(e.target).closest('.suggestion-search').length) {
                this.$suggestionPanel.find('.search-results').hide();
            }
        });

        // Form field changes that trigger suggestions
        if (this.frm) {
            this.frm.fields_dict.service_type.$input.on('change', () => {
                this.loadSuggestions();
            });

            if (this.frm.fields_dict.vehicle) {
                this.frm.fields_dict.vehicle.$input.on('change', () => {
                    this.loadSuggestions();
                });
            }

            if (this.frm.fields_dict.customer) {
                this.frm.fields_dict.customer.$input.on('change', () => {
                    this.loadSuggestions();
                });
            }
        }
    }

    /**
     * Load initial suggestions when form opens
     */
    loadInitialSuggestions() {
        // Show panel
        this.$suggestionPanel.show();

        // Load suggestions if we have basic info
        if (this.frm.doc.service_type) {
            this.loadSuggestions();
        } else {
            this.showEmptyState();
        }
    }

    /**
     * Load suggestions from server
     */
    async loadSuggestions(forceRefresh = false) {
        if (this.isLoading) return;

        const cacheKey = this.getCacheKey();

        // Check cache first
        if (!forceRefresh && this.suggestionCache.has(cacheKey)) {
            const cachedData = this.suggestionCache.get(cacheKey);
            this.displaySuggestions(cachedData.suggestions);
            return;
        }

        this.setLoading(true);

        try {
            // Gather form data
            const requestData = {
                service_type: this.frm.doc.service_type,
                customer_id: this.frm.doc.customer,
                language: this.language
            };

            // Add vehicle data if available
            if (this.frm.doc.vehicle) {
                const vehicleData = await this.getVehicleData(this.frm.doc.vehicle);
                if (vehicleData) {
                    requestData.vehicle_make = vehicleData.make;
                    requestData.vehicle_model = vehicleData.model;
                    requestData.vehicle_year = vehicleData.year;
                }
            }

            // Get previous services for this customer
            if (this.frm.doc.customer) {
                const previousServices = await this.getPreviousServices(this.frm.doc.customer);
                requestData.previous_services = previousServices;
            }

            // Call suggestion API
            const response = await frappe.call({
                method: 'universal_workshop.sales_service.auto_suggestion_engine.get_quick_suggestions',
                args: requestData
            });

            if (response.message && !response.message.error) {
                this.currentSuggestions = response.message.suggestions || [];

                // Cache the results
                this.suggestionCache.set(cacheKey, {
                    suggestions: this.currentSuggestions,
                    timestamp: Date.now()
                });

                this.displaySuggestions(this.currentSuggestions);
            } else {
                this.showError(response.message?.error || __('Failed to load suggestions'));
            }
        } catch (error) {
            console.error('Suggestion loading error:', error);
            this.showError(__('Error loading suggestions'));
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Get vehicle data for suggestions
     */
    async getVehicleData(vehicleId) {
        try {
            const response = await frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Vehicle Master',
                    filters: { name: vehicleId },
                    fieldname: ['make', 'model', 'year']
                }
            });
            return response.message;
        } catch (error) {
            console.error('Error getting vehicle data:', error);
            return null;
        }
    }

    /**
     * Get previous services for customer
     */
    async getPreviousServices(customerId) {
        try {
            const response = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Service Estimate',
                    filters: {
                        customer: customerId,
                        docstatus: 1
                    },
                    fields: ['name'],
                    limit_page_length: 10,
                    order_by: 'creation desc'
                }
            });
            return response.message ? response.message.map(s => s.name) : [];
        } catch (error) {
            console.error('Error getting previous services:', error);
            return [];
        }
    }

    /**
     * Display suggestions in the UI
     */
    displaySuggestions(suggestions) {
        const $list = this.$suggestionPanel.find('.suggestion-list');

        if (!suggestions || suggestions.length === 0) {
            this.showEmptyState();
            return;
        }

        this.hideEmptyState();
        $list.empty();

        suggestions.forEach(suggestion => {
            const $item = this.createSuggestionItem(suggestion);
            $list.append($item);
        });
    }

    /**
     * Create HTML for a suggestion item
     */
    createSuggestionItem(suggestion) {
        const confidenceClass = this.getConfidenceClass(suggestion.confidence_score);
        const stockClass = suggestion.in_stock ? 'in-stock' : 'out-of-stock';
        const itemClass = suggestion.in_stock ? '' : 'out-of-stock';

        const $item = $(`
            <div class="suggestion-item ${itemClass}" data-item-code="${suggestion.item_code}">
                <div class="suggestion-item-header">
                    <div>
                        <div class="suggestion-item-name">${suggestion.item_name}</div>
                        <div class="suggestion-reason">${suggestion.reason_text}</div>
                    </div>
                    <div class="suggestion-confidence ${confidenceClass}">
                        ${suggestion.confidence_percent}%
                    </div>
                </div>
                <div class="suggestion-details">
                    <span class="suggestion-stock ${stockClass}">
                        ${suggestion.availability_note} (${suggestion.available_qty})
                    </span>
                    <span class="suggestion-code">${suggestion.item_code}</span>
                </div>
                <div class="suggestion-actions">
                    <button class="btn btn-xs btn-primary add-suggestion" 
                            data-item-code="${suggestion.item_code}"
                            data-quantity="${suggestion.suggested_quantity}"
                            ${!suggestion.in_stock ? 'disabled' : ''}>
                        <i class="fa fa-plus"></i> ${__('Add')} (${suggestion.suggested_quantity})
                    </button>
                    ${this.feedbackMode ? `
                        <button class="btn btn-xs btn-success suggestion-feedback" 
                                data-item-code="${suggestion.item_code}" 
                                data-useful="true"
                                title="${__('Useful suggestion')}">
                            <i class="fa fa-thumbs-up"></i>
                        </button>
                        <button class="btn btn-xs btn-default suggestion-feedback" 
                                data-item-code="${suggestion.item_code}" 
                                data-useful="false"
                                title="${__('Not useful')}">
                            <i class="fa fa-thumbs-down"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `);

        return $item;
    }

    /**
     * Get CSS class for confidence score
     */
    getConfidenceClass(score) {
        if (score >= 0.8) return 'high';
        if (score >= 0.6) return 'medium';
        return 'low';
    }

    /**
     * Add suggested item to estimate
     */
    async addItemToEstimate(itemCode, quantity = 1) {
        try {
            // Get item details
            const itemResponse = await frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: { item_code: itemCode },
                    fieldname: ['item_name', 'item_name_ar', 'standard_rate', 'item_group']
                }
            });

            if (!itemResponse.message) {
                frappe.msgprint(__('Item not found'));
                return;
            }

            const itemData = itemResponse.message;
            const itemName = this.language === 'ar' && itemData.item_name_ar ?
                itemData.item_name_ar : itemData.item_name;

            // Add to child table
            const childDoc = frappe.model.add_child(this.frm.doc, 'Service Estimate Item', 'estimate_items');
            childDoc.item_code = itemCode;
            childDoc.item_name = itemName;
            childDoc.qty = quantity;
            childDoc.rate = itemData.standard_rate || 0;
            childDoc.amount = childDoc.qty * childDoc.rate;

            // Refresh the child table
            this.frm.refresh_field('estimate_items');

            // Calculate totals
            this.frm.trigger('calculate_totals');

            frappe.show_alert({
                message: __('Item {0} added to estimate', [itemName]),
                indicator: 'green'
            });

            // Record positive feedback automatically
            this.recordFeedback(itemCode, true);

        } catch (error) {
            console.error('Error adding item:', error);
            frappe.msgprint(__('Error adding item to estimate'));
        }
    }

    /**
     * Perform parts search
     */
    async performSearch(query) {
        if (!query || query.length < 2) {
            this.$suggestionPanel.find('.search-results').hide();
            return;
        }

        try {
            const response = await frappe.call({
                method: 'universal_workshop.sales_service.auto_suggestion_engine.search_parts_api',
                args: {
                    query: query,
                    limit: 10,
                    language: this.language
                }
            });

            if (response.message && response.message.parts) {
                this.displaySearchResults(response.message.parts);
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    /**
     * Display search results
     */
    displaySearchResults(parts) {
        const $results = this.$suggestionPanel.find('.search-results');
        $results.empty();

        if (parts.length === 0) {
            $results.html(`<div class="search-result-item text-muted">${__('No parts found')}</div>`);
        } else {
            parts.forEach(part => {
                const stockIndicator = part.in_stock ?
                    '<span class="text-success">●</span>' :
                    '<span class="text-danger">●</span>';

                const $item = $(`
                    <div class="search-result-item" data-item-code="${part.item_code}">
                        ${stockIndicator} ${part.item_name}
                        <small class="text-muted d-block">${part.item_code}</small>
                    </div>
                `);

                $item.on('click', () => {
                    this.addItemToEstimate(part.item_code, 1);
                    $results.hide();
                    this.$suggestionPanel.find('.parts-search-input').val('');
                });

                $results.append($item);
            });
        }

        $results.show();
    }

    /**
     * Record user feedback on suggestions
     */
    async recordFeedback(itemCode, useful) {
        if (!this.frm.doc.name) return; // Only for saved estimates

        try {
            await frappe.call({
                method: 'universal_workshop.sales_service.auto_suggestion_engine.update_suggestion_feedback',
                args: {
                    item_code: itemCode,
                    service_estimate_id: this.frm.doc.name,
                    was_useful: useful
                }
            });
        } catch (error) {
            console.error('Feedback error:', error);
        }
    }

    /**
     * Utility methods
     */
    getCacheKey() {
        return `suggestions_${this.frm.doc.service_type}_${this.frm.doc.vehicle}_${this.frm.doc.customer}`;
    }

    setLoading(loading) {
        this.isLoading = loading;
        const $loading = this.$suggestionPanel.find('.suggestion-loading');
        const $list = this.$suggestionPanel.find('.suggestion-list');

        if (loading) {
            $loading.show();
            $list.hide();
        } else {
            $loading.hide();
            $list.show();
        }
    }

    showEmptyState() {
        this.$suggestionPanel.find('.suggestion-list').hide();
        this.$suggestionPanel.find('.suggestion-empty').show();
    }

    hideEmptyState() {
        this.$suggestionPanel.find('.suggestion-empty').hide();
        this.$suggestionPanel.find('.suggestion-list').show();
    }

    showError(message) {
        frappe.msgprint({
            title: __('Suggestion Error'),
            message: message,
            indicator: 'red'
        });
    }
}

// Global instance
frappe.parts_suggestion_ui = new PartsAutoSuggestionUI();

// Integration with Service Estimate form
frappe.ui.form.on('Service Estimate', {
    refresh: function (frm) {
        // Initialize parts suggestions
        if (frm.is_new() || frm.doc.docstatus === 0) {
            frappe.parts_suggestion_ui.initializeForForm(frm);
        }
    },

    service_type: function (frm) {
        if (frappe.parts_suggestion_ui.frm === frm) {
            frappe.parts_suggestion_ui.loadSuggestions();
        }
    },

    vehicle: function (frm) {
        if (frappe.parts_suggestion_ui.frm === frm) {
            frappe.parts_suggestion_ui.loadSuggestions();
        }
    },

    customer: function (frm) {
        if (frappe.parts_suggestion_ui.frm === frm) {
            frappe.parts_suggestion_ui.loadSuggestions();
        }
    }
});

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PartsAutoSuggestionUI;
} 