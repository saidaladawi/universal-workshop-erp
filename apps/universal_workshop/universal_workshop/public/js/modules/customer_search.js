// Copyright (c) 2024, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.provide("universal_workshop.search");

universal_workshop.search.CustomerSearch = class CustomerSearch {
    constructor(options = {}) {
        this.container = options.container || 'body';
        this.callback = options.callback || function() {};
        this.filters = options.filters || {};
        this.page_size = options.page_size || 20;
        this.current_page = 1;
        this.setup_search_interface();
    }

    setup_search_interface() {
        // Create search interface HTML
        const searchHTML = `
            <div class="customer-search-container">
                <div class="search-input-group">
                    <input type="text" 
                           class="form-control customer-search-input" 
                           placeholder="${__('Search customers (Arabic/English)')}"
                           autocomplete="off">
                    <div class="input-group-append">
                        <button class="btn btn-primary search-btn" type="button">
                            <i class="fa fa-search"></i>
                        </button>
                    </div>
                </div>
                <div class="search-suggestions" style="display: none;"></div>
                <div class="search-filters" style="display: none;">
                    <div class="row">
                        <div class="col-md-3">
                            <select class="form-control" id="customer-type-filter">
                                <option value="">${__('All Types')}</option>
                                <option value="Company">${__('Company')}</option>
                                <option value="Individual">${__('Individual')}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" id="language-filter">
                                <option value="">${__('All Languages')}</option>
                                <option value="Arabic">${__('Arabic')}</option>
                                <option value="English">${__('English')}</option>
                                <option value="Both">${__('Both')}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <button class="btn btn-secondary" id="toggle-filters">
                                ${__('Advanced Filters')}
                            </button>
                        </div>
                    </div>
                </div>
                <div class="search-results"></div>
                <div class="search-pagination"></div>
            </div>
        `;

        $(this.container).html(searchHTML);
        this.bind_events();
    }

    bind_events() {
        const self = this;
        
        // Search input events
        $('.customer-search-input').on('input', function() {
            const query = $(this).val();
            if (query.length > 2) {
                self.get_suggestions(query);
            } else {
                $('.search-suggestions').hide();
            }
        });

        $('.customer-search-input').on('keypress', function(e) {
            if (e.which === 13) { // Enter key
                self.perform_search();
            }
        });

        // Search button
        $('.search-btn').on('click', function() {
            self.perform_search();
        });

        // Filter toggles
        $('#toggle-filters').on('click', function() {
            $('.search-filters').toggle();
        });

        // Filter changes
        $('#customer-type-filter, #language-filter').on('change', function() {
            if ($('.customer-search-input').val()) {
                self.perform_search();
            }
        });

        // Suggestion clicks
        $(document).on('click', '.search-suggestion', function() {
            const suggestion = $(this).text();
            $('.customer-search-input').val(suggestion);
            $('.search-suggestions').hide();
            self.perform_search();
        });

        // Pagination clicks
        $(document).on('click', '.pagination-btn', function() {
            const page = $(this).data('page');
            self.current_page = page;
            self.perform_search();
        });
    }

    get_suggestions(query) {
        frappe.call({
            method: 'universal_workshop.search_integration.api.get_customer_suggestions',
            args: {
                field: 'customer_name',
                text: query,
                limit: 5
            },
            callback: (response) => {
                if (response.message && response.message.success) {
                    this.display_suggestions(response.message.suggestions);
                }
            }
        });
    }

    display_suggestions(suggestions) {
        const suggestionsHTML = suggestions.map(suggestion => 
            `<div class="search-suggestion">${suggestion}</div>`
        ).join('');

        $('.search-suggestions').html(suggestionsHTML).show();
    }

    perform_search() {
        const query = $('.customer-search-input').val();
        const filters = this.get_current_filters();
        
        if (!query.trim()) {
            return;
        }

        // Show loading
        $('.search-results').html(`
            <div class="text-center">
                <i class="fa fa-spinner fa-spin"></i> ${__('Searching...')}
            </div>
        `);

        frappe.call({
            method: 'universal_workshop.search_integration.api.search_customers',
            args: {
                query: query,
                filters: JSON.stringify(filters),
                page: this.current_page,
                page_size: this.page_size
            },
            callback: (response) => {
                if (response.message) {
                    if (response.message.success) {
                        this.display_results(response.message.data);
                    } else {
                        // Show fallback results if available
                        if (response.message.fallback) {
                            this.display_results(response.message.fallback);
                        } else {
                            this.show_error(response.message.message);
                        }
                    }
                }
            },
            error: () => {
                this.show_error(__('Search failed. Please try again.'));
            }
        });
    }

    get_current_filters() {
        const filters = {};
        
        const customerType = $('#customer-type-filter').val();
        const language = $('#language-filter').val();
        
        if (customerType) filters.customer_type = customerType;
        if (language) filters.preferred_language = language;
        
        return { ...filters, ...this.filters };
    }

    display_results(data) {
        const customers = data.customers || [];
        const pagination = data.pagination || {};

        if (customers.length === 0) {
            $('.search-results').html(`
                <div class="text-center text-muted">
                    <p>${__('No customers found matching your search.')}</p>
                </div>
            `);
            return;
        }

        // Build results HTML
        let resultsHTML = '<div class="customer-results-list">';
        
        customers.forEach(customer => {
            const arabicName = customer.customer_name_ar || '';
            const displayName = customer.customer_name || customer.name;
            const customerType = customer.customer_type || '';
            const territory = customer.territory || '';
            const email = customer.email_id || '';
            const mobile = customer.mobile_no || '';

            resultsHTML += `
                <div class="customer-result-card" data-customer="${customer.name}">
                    <div class="row">
                        <div class="col-md-8">
                            <h6 class="customer-name">
                                ${displayName}
                                ${arabicName ? `<small class="text-muted">(${arabicName})</small>` : ''}
                            </h6>
                            <p class="customer-details">
                                <span class="badge badge-secondary">${customerType}</span>
                                ${territory ? `<span class="badge badge-info">${territory}</span>` : ''}
                            </p>
                            ${email ? `<p class="text-muted"><i class="fa fa-envelope"></i> ${email}</p>` : ''}
                            ${mobile ? `<p class="text-muted"><i class="fa fa-phone"></i> ${mobile}</p>` : ''}
                        </div>
                        <div class="col-md-4 text-right">
                            <button class="btn btn-sm btn-primary select-customer" 
                                    data-customer="${customer.name}"
                                    data-customer-name="${displayName}">
                                ${__('Select')}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        resultsHTML += '</div>';

        // Add pagination
        if (pagination.total_pages > 1) {
            resultsHTML += this.build_pagination(pagination);
        }

        $('.search-results').html(resultsHTML);
        
        // Bind result selection
        $('.select-customer').on('click', (e) => {
            const customerName = $(e.target).data('customer');
            const customerDisplayName = $(e.target).data('customer-name');
            this.callback({
                customer: customerName,
                customer_name: customerDisplayName
            });
        });
    }

    build_pagination(pagination) {
        let paginationHTML = '<div class="search-pagination-container"><nav><ul class="pagination">';
        
        // Previous button
        if (pagination.has_previous) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link pagination-btn" data-page="${pagination.current_page - 1}">
                        ${__('Previous')}
                    </a>
                </li>
            `;
        }

        // Page numbers
        for (let i = 1; i <= pagination.total_pages; i++) {
            if (i === pagination.current_page) {
                paginationHTML += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link pagination-btn" data-page="${i}">${i}</a>
                    </li>
                `;
            }
        }

        // Next button
        if (pagination.has_next) {
            paginationHTML += `
                <li class="page-item">
                    <a class="page-link pagination-btn" data-page="${pagination.current_page + 1}">
                        ${__('Next')}
                    </a>
                </li>
            `;
        }

        paginationHTML += '</ul></nav></div>';
        return paginationHTML;
    }

    show_error(message) {
        $('.search-results').html(`
            <div class="alert alert-warning">
                <i class="fa fa-exclamation-triangle"></i> ${message}
            </div>
        `);
    }
};

// Convenience function to create customer search
frappe.provide("frappe.ui");
frappe.ui.CustomerSearch = function(options) {
    return new universal_workshop.search.CustomerSearch(options);
};

// Auto-complete enhancement for customer fields
$(document).ready(function() {
    // Enhance customer link fields with search
    frappe.ui.form.on('*', {
        setup: function(frm) {
            // Find customer link fields and enhance them
            frm.fields.forEach(field => {
                if (field.df.fieldtype === 'Link' && field.df.options === 'Customer') {
                    enhance_customer_field(field);
                }
            });
        }
    });
});

function enhance_customer_field(field) {
    // Add search icon next to customer fields
    if (field.$wrapper) {
        const searchIcon = $(`
            <button type="button" class="btn btn-sm btn-default customer-search-icon" 
                    title="${__('Advanced Customer Search')}"
                    style="margin-left: 5px;">
                <i class="fa fa-search"></i>
            </button>
        `);
        
        field.$wrapper.find('.link-field').after(searchIcon);
        
        searchIcon.on('click', function() {
            show_customer_search_dialog(field);
        });
    }
}

function show_customer_search_dialog(field) {
    const dialog = new frappe.ui.Dialog({
        title: __('Search Customers'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'search_container'
            }
        ]
    });

    dialog.show();

    // Initialize search in dialog
    const search = new universal_workshop.search.CustomerSearch({
        container: dialog.fields_dict.search_container.$wrapper,
        callback: function(result) {
            field.set_value(result.customer);
            dialog.hide();
        }
    });
} 