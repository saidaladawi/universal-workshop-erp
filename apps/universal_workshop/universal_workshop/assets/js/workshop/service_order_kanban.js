/**
 * Service Order Kanban Board Frontend
 * ===================================
 * 
 * Interactive Kanban-style service order management board with:
 * - Drag-and-drop functionality for status transitions
 * - Real-time updates via WebSocket connections
 * - Arabic/English dual language support with RTL formatting
 * - Advanced filtering and search capabilities
 * - Mobile-responsive design
 * - Role-based permissions and actions
 */

class ServiceOrderKanban {
    constructor(container, options = {}) {
        this.container = $(container);
        this.options = {
            realtime: true,
            filters: {},
            language: frappe.boot.lang || 'en',
            auto_refresh: 30000, // 30 seconds
            pagination_limit: 50,
            ...options
        };

        this.data = {};
        this.filters = {};
        this.current_page = 0;
        this.is_loading = false;
        this.search_timeout = null;

        this.init();
    }

    init() {
        this.setup_container();
        this.setup_toolbar();
        this.setup_search();
        this.setup_filters();
        this.setup_kanban_board();
        this.load_data();
        this.setup_realtime();
        this.setup_auto_refresh();

        // Setup responsive behavior
        this.setup_responsive();

        // Setup Arabic RTL support
        if (this.options.language === 'ar') {
            this.setup_rtl_support();
        }
    }

    setup_container() {
        this.container.addClass('service-kanban-container');

        if (this.options.language === 'ar') {
            this.container.addClass('rtl-layout');
            this.container.attr('dir', 'rtl');
        }

        // Create main layout
        this.container.html(`
            <div class="kanban-toolbar">
                <div class="toolbar-left">
                    <div class="kanban-search">
                        <input type="text" id="kanban-search" placeholder="${__('Search service orders...')}" class="form-control">
                        <i class="fa fa-search search-icon"></i>
                    </div>
                </div>
                <div class="toolbar-center">
                    <div class="kanban-filters">
                        <select id="filter-technician" class="form-control">
                            <option value="">${__('All Technicians')}</option>
                        </select>
                        <select id="filter-priority" class="form-control">
                            <option value="">${__('All Priorities')}</option>
                        </select>
                        <select id="filter-date-range" class="form-control">
                            <option value="">${__('All Time')}</option>
                        </select>
                    </div>
                </div>
                <div class="toolbar-right">
                    <button class="btn btn-primary btn-sm" id="create-order">
                        <i class="fa fa-plus"></i> ${__('New Service Order')}
                    </button>
                    <button class="btn btn-secondary btn-sm" id="refresh-board">
                        <i class="fa fa-refresh"></i> ${__('Refresh')}
                    </button>
                    <div class="kanban-status-indicator">
                        <span class="status-text">${__('Live')}</span>
                        <span class="status-dot online"></span>
                    </div>
                </div>
            </div>
            
            <div class="kanban-board-wrapper">
                <div class="kanban-board" id="kanban-board">
                    <!-- Kanban columns will be generated here -->
                </div>
            </div>
            
            <div class="kanban-loading" id="kanban-loading" style="display: none;">
                <div class="loading-spinner">
                    <i class="fa fa-spinner fa-spin"></i>
                    <span>${__('Loading...')}</span>
                </div>
            </div>
        `);
    }

    setup_toolbar() {
        // Create new service order button
        this.container.find('#create-order').on('click', () => {
            this.create_new_order();
        });

        // Refresh button
        this.container.find('#refresh-board').on('click', () => {
            this.refresh_data();
        });
    }

    setup_search() {
        const searchInput = this.container.find('#kanban-search');

        searchInput.on('input', (e) => {
            clearTimeout(this.search_timeout);
            const query = e.target.value.trim();

            this.search_timeout = setTimeout(() => {
                this.filters.search = query;
                this.load_data();
            }, 300);
        });

        // Clear search on escape
        searchInput.on('keydown', (e) => {
            if (e.key === 'Escape') {
                e.target.value = '';
                delete this.filters.search;
                this.load_data();
            }
        });
    }

    setup_filters() {
        // Load filter options
        this.load_filter_options();

        // Setup filter change handlers
        this.container.find('#filter-technician').on('change', (e) => {
            this.filters.technician = e.target.value;
            this.load_data();
        });

        this.container.find('#filter-priority').on('change', (e) => {
            this.filters.priority = e.target.value;
            this.load_data();
        });

        this.container.find('#filter-date-range').on('change', (e) => {
            this.filters.date_range = e.target.value;
            this.load_data();
        });
    }

    setup_kanban_board() {
        this.board = this.container.find('#kanban-board');

        // Setup drag and drop
        this.setup_drag_drop();
    }

    setup_drag_drop() {
        // Enable sortable for drag and drop between columns
        this.board.on('click', '.kanban-column', function () {
            $(this).find('.kanban-cards').sortable({
                connectWith: '.kanban-cards',
                handle: '.card-drag-handle',
                placeholder: 'card-placeholder',
                tolerance: 'pointer',
                helper: 'clone',
                opacity: 0.8,
                revert: 100,

                start: (event, ui) => {
                    ui.item.addClass('dragging');
                    $('.kanban-column').addClass('drop-zone');

                    // Show allowed drop zones
                    const allowedStatuses = ui.item.data('allowed-transitions') || [];
                    $('.kanban-column').each(function () {
                        const columnStatus = $(this).data('status');
                        if (allowedStatuses.includes(columnStatus)) {
                            $(this).addClass('allowed-drop');
                        } else {
                            $(this).addClass('not-allowed-drop');
                        }
                    });
                },

                stop: (event, ui) => {
                    ui.item.removeClass('dragging');
                    $('.kanban-column').removeClass('drop-zone allowed-drop not-allowed-drop');
                },

                update: (event, ui) => {
                    if (ui.sender) return; // Ignore if moved from another list

                    const cardElement = ui.item;
                    const orderName = cardElement.data('order-name');
                    const newStatus = cardElement.closest('.kanban-column').data('status');
                    const oldStatus = cardElement.data('current-status');

                    if (newStatus !== oldStatus) {
                        this.update_order_status(orderName, newStatus, oldStatus, cardElement);
                    }
                },

                receive: (event, ui) => {
                    const cardElement = ui.item;
                    const orderName = cardElement.data('order-name');
                    const newStatus = cardElement.closest('.kanban-column').data('status');
                    const oldStatus = cardElement.data('current-status');

                    this.update_order_status(orderName, newStatus, oldStatus, cardElement);
                }
            }).disableSelection();
        });
    }

    load_filter_options() {
        frappe.call({
            method: 'universal_workshop.workshop_management.kanban.service_order_kanban.get_kanban_filters_data',
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.populate_filters(r.message.data);
                }
            }
        });
    }

    populate_filters(filterData) {
        // Populate technician filter
        const technicianSelect = this.container.find('#filter-technician');
        technicianSelect.find('option:not(:first)').remove();

        filterData.technicians.forEach(tech => {
            technicianSelect.append(`<option value="${tech.value}">${tech.label}</option>`);
        });

        // Populate priority filter
        const prioritySelect = this.container.find('#filter-priority');
        prioritySelect.find('option:not(:first)').remove();

        filterData.priorities.forEach(priority => {
            prioritySelect.append(`<option value="${priority.value}">${priority.label}</option>`);
        });

        // Populate date range filter
        const dateSelect = this.container.find('#filter-date-range');
        dateSelect.find('option:not(:first)').remove();

        filterData.date_ranges.forEach(range => {
            dateSelect.append(`<option value="${range.value}">${range.label}</option>`);
        });
    }

    load_data() {
        if (this.is_loading) return;

        this.is_loading = true;
        this.show_loading();

        frappe.call({
            method: 'universal_workshop.workshop_management.kanban.service_order_kanban.get_kanban_board_data',
            args: {
                filters: JSON.stringify(this.filters),
                limit: this.options.pagination_limit,
                start: this.current_page * this.options.pagination_limit
            },
            callback: (r) => {
                this.is_loading = false;
                this.hide_loading();

                if (r.message && r.message.success) {
                    this.data = r.message.data;
                    this.render_board();
                    this.update_status_indicator('online');
                } else {
                    this.show_error(r.message?.message || __('Failed to load data'));
                    this.update_status_indicator('error');
                }
            },
            error: () => {
                this.is_loading = false;
                this.hide_loading();
                this.show_error(__('Network error occurred'));
                this.update_status_indicator('offline');
            }
        });
    }

    render_board() {
        const board = this.board;
        board.empty();

        // Define status order for consistent layout
        const statusOrder = ['Draft', 'Scheduled', 'In Progress', 'Quality Check', 'Completed', 'Delivered', 'Cancelled'];

        statusOrder.forEach(status => {
            const columnData = this.data.data[status];
            if (!columnData) return;

            const column = this.create_kanban_column(status, columnData);
            board.append(column);
        });

        // Re-enable drag and drop after rendering
        this.setup_drag_drop();

        // Setup card interactions
        this.setup_card_interactions();
    }

    create_kanban_column(status, columnData) {
        const isRTL = this.options.language === 'ar';
        const titleDirection = isRTL ? 'rtl' : 'ltr';

        const column = $(`
            <div class="kanban-column" data-status="${status}">
                <div class="column-header" style="direction: ${titleDirection};">
                    <div class="column-title">
                        <i class="fa ${columnData.icon}" style="color: ${columnData.color};"></i>
                        <span class="title-text">${columnData.title}</span>
                        <span class="count-badge">${columnData.count}</span>
                    </div>
                    <div class="column-actions">
                        ${columnData.can_create ? `<button class="btn btn-sm btn-link add-card" data-status="${status}"><i class="fa fa-plus"></i></button>` : ''}
                    </div>
                </div>
                <div class="kanban-cards" data-status="${status}">
                    ${columnData.cards.map(card => this.create_service_card(card)).join('')}
                </div>
                ${columnData.count > columnData.cards.length ? `
                    <div class="load-more-cards">
                        <button class="btn btn-sm btn-outline-secondary load-more" data-status="${status}">
                            ${__('Load More')} (${columnData.count - columnData.cards.length})
                        </button>
                    </div>
                ` : ''}
            </div>
        `);

        return column;
    }

    create_service_card(cardData) {
        const isRTL = this.options.language === 'ar';
        const cardDirection = isRTL ? 'rtl' : 'ltr';

        // Format timing display
        const timingDisplay = this.format_timing_display(cardData.timing);

        // Format amount
        const amountDisplay = this.format_currency(cardData.service.amount);

        return `
            <div class="service-card" 
                 data-order-name="${cardData.id}"
                 data-current-status="${cardData.status}"
                 data-allowed-transitions='${JSON.stringify(cardData.permissions.allowed_transitions || [])}'
                 style="direction: ${cardDirection};">
                
                <div class="card-drag-handle">
                    <i class="fa fa-grip-vertical"></i>
                </div>
                
                <div class="card-header">
                    <div class="card-title" title="${cardData.title}">
                        ${cardData.title}
                    </div>
                    <div class="priority-indicator ${cardData.priority_class}">
                        ${__(cardData.priority)}
                    </div>
                </div>
                
                <div class="card-body">
                    <div class="service-info">
                        <div class="service-type">
                            <i class="fa fa-wrench"></i>
                            ${isRTL && cardData.service.type_ar ? cardData.service.type_ar : cardData.service.type}
                        </div>
                        
                        ${cardData.vehicle.license_plate ? `
                            <div class="vehicle-info">
                                <i class="fa fa-car"></i>
                                ${cardData.vehicle.license_plate} - ${cardData.vehicle.info}
                            </div>
                        ` : ''}
                        
                        ${cardData.technician.assigned ? `
                            <div class="technician-info">
                                <i class="fa fa-user"></i>
                                ${cardData.technician.display_name}
                            </div>
                        ` : `
                            <div class="technician-info unassigned">
                                <i class="fa fa-user-times"></i>
                                ${__('Unassigned')}
                            </div>
                        `}
                        
                        ${cardData.service.bay ? `
                            <div class="bay-info">
                                <i class="fa fa-map-marker"></i>
                                ${cardData.service.bay}
                            </div>
                        ` : ''}
                    </div>
                    
                    <div class="card-footer">
                        <div class="timing-info ${timingDisplay.class}">
                            <i class="fa ${timingDisplay.icon}"></i>
                            ${timingDisplay.text}
                        </div>
                        
                        <div class="amount-info">
                            ${amountDisplay}
                        </div>
                    </div>
                </div>
                
                <div class="card-actions">
                    ${cardData.actions.map(action => `
                        <button class="btn ${action.class} card-action" 
                                data-action="${action.action}"
                                data-order="${cardData.id}"
                                ${action.target_status ? `data-target-status="${action.target_status}"` : ''}
                                title="${action.label}">
                            <i class="fa ${action.icon}"></i>
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }

    format_timing_display(timing) {
        const now = new Date();
        const serviceDate = new Date(timing.service_date);
        const estimatedCompletion = timing.estimated_completion ? new Date(timing.estimated_completion) : null;

        if (timing.is_overdue) {
            return {
                text: __('Overdue'),
                icon: 'fa-exclamation-triangle',
                class: 'overdue'
            };
        } else if (timing.is_due_soon) {
            return {
                text: timing.time_remaining,
                icon: 'fa-clock-o',
                class: 'due-soon'
            };
        } else if (estimatedCompletion) {
            return {
                text: timing.time_remaining,
                icon: 'fa-clock-o',
                class: 'normal'
            };
        } else {
            const daysAgo = Math.floor((now - serviceDate) / (1000 * 60 * 60 * 24));
            return {
                text: daysAgo === 0 ? __('Today') : __('Day {0}', [daysAgo]),
                icon: 'fa-calendar',
                class: 'normal'
            };
        }
    }

    format_currency(amount) {
        if (!amount || amount === 0) return '';

        // Format for Omani Rial with 3 decimal places
        const formatted = Number(amount).toLocaleString('en-US', {
            minimumFractionDigits: 3,
            maximumFractionDigits: 3
        });

        return `OMR ${formatted}`;
    }

    setup_card_interactions() {
        // Card click to view details
        this.board.off('click', '.service-card').on('click', '.service-card', (e) => {
            if ($(e.target).closest('.card-actions, .card-drag-handle').length) return;

            const orderName = $(e.currentTarget).data('order-name');
            this.view_order_details(orderName);
        });

        // Card action buttons
        this.board.off('click', '.card-action').on('click', '.card-action', (e) => {
            e.stopPropagation();

            const button = $(e.currentTarget);
            const action = button.data('action');
            const orderName = button.data('order');
            const targetStatus = button.data('target-status');

            this.handle_card_action(action, orderName, targetStatus, button);
        });

        // Add new card buttons
        this.board.off('click', '.add-card').on('click', '.add-card', (e) => {
            e.stopPropagation();
            const status = $(e.currentTarget).data('status');
            this.create_new_order(status);
        });

        // Load more cards
        this.board.off('click', '.load-more').on('click', '.load-more', (e) => {
            const status = $(e.currentTarget).data('status');
            this.load_more_cards(status);
        });
    }

    handle_card_action(action, orderName, targetStatus, button) {
        switch (action) {
            case 'view_details':
                this.view_order_details(orderName);
                break;
            case 'edit':
                this.edit_order(orderName);
                break;
            case 'change_status':
                this.change_order_status(orderName, targetStatus);
                break;
            case 'assign_technician':
                this.assign_technician(orderName);
                break;
            default:
                console.log('Unknown action:', action);
        }
    }

    update_order_status(orderName, newStatus, oldStatus, cardElement) {
        // Show loading state on card
        cardElement.addClass('updating');

        frappe.call({
            method: 'universal_workshop.workshop_management.kanban.service_order_kanban.update_service_order_status',
            args: {
                order_name: orderName,
                new_status: newStatus,
                notes: `Status changed via Kanban board from ${oldStatus} to ${newStatus}`
            },
            callback: (r) => {
                cardElement.removeClass('updating');

                if (r.message && r.message.success) {
                    // Update card data
                    cardElement.data('current-status', newStatus);

                    // Show success message
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });

                    // Refresh card data to reflect changes
                    setTimeout(() => {
                        this.refresh_card(orderName);
                    }, 1000);

                } else {
                    // Revert card position on error
                    this.revert_card_position(cardElement, oldStatus);

                    frappe.show_alert({
                        message: r.message?.message || __('Failed to update status'),
                        indicator: 'red'
                    });
                }
            },
            error: () => {
                cardElement.removeClass('updating');
                this.revert_card_position(cardElement, oldStatus);

                frappe.show_alert({
                    message: __('Network error occurred'),
                    indicator: 'red'
                });
            }
        });
    }

    revert_card_position(cardElement, originalStatus) {
        const originalColumn = this.board.find(`[data-status="${originalStatus}"] .kanban-cards`);
        originalColumn.append(cardElement);
    }

    view_order_details(orderName) {
        frappe.set_route('Form', 'Service Order', orderName);
    }

    edit_order(orderName) {
        frappe.set_route('Form', 'Service Order', orderName);
    }

    change_order_status(orderName, targetStatus) {
        const d = new frappe.ui.Dialog({
            title: __('Change Status'),
            fields: [
                {
                    fieldtype: 'Data',
                    fieldname: 'order_name',
                    label: __('Service Order'),
                    default: orderName,
                    read_only: 1
                },
                {
                    fieldtype: 'Select',
                    fieldname: 'new_status',
                    label: __('New Status'),
                    default: targetStatus,
                    read_only: 1
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'notes',
                    label: __('Notes'),
                    description: __('Optional notes for this status change')
                }
            ],
            primary_action: (values) => {
                this.update_order_status(orderName, values.new_status, null,
                    this.board.find(`[data-order-name="${orderName}"]`));
                d.hide();
            },
            primary_action_label: __('Update Status')
        });

        d.show();
    }

    assign_technician(orderName) {
        // Get available technicians
        frappe.call({
            method: 'universal_workshop.workshop_management.kanban.service_order_kanban.get_kanban_filters_data',
            callback: (r) => {
                if (r.message && r.message.success) {
                    const technicians = r.message.data.technicians;

                    const d = new frappe.ui.Dialog({
                        title: __('Assign Technician'),
                        fields: [
                            {
                                fieldtype: 'Data',
                                fieldname: 'order_name',
                                label: __('Service Order'),
                                default: orderName,
                                read_only: 1
                            },
                            {
                                fieldtype: 'Select',
                                fieldname: 'technician',
                                label: __('Technician'),
                                options: technicians.map(t => ({ value: t.value, label: t.label })),
                                reqd: 1
                            },
                            {
                                fieldtype: 'Small Text',
                                fieldname: 'notes',
                                label: __('Assignment Notes')
                            }
                        ],
                        primary_action: (values) => {
                            frappe.call({
                                method: 'universal_workshop.workshop_management.kanban.service_order_kanban.assign_technician_to_order',
                                args: {
                                    order_name: values.order_name,
                                    technician_user: values.technician,
                                    notes: values.notes
                                },
                                callback: (r) => {
                                    if (r.message && r.message.success) {
                                        frappe.show_alert({
                                            message: r.message.message,
                                            indicator: 'green'
                                        });
                                        this.refresh_card(orderName);
                                    } else {
                                        frappe.show_alert({
                                            message: r.message?.message || __('Failed to assign technician'),
                                            indicator: 'red'
                                        });
                                    }
                                }
                            });
                            d.hide();
                        },
                        primary_action_label: __('Assign')
                    });

                    d.show();
                }
            }
        });
    }

    create_new_order(defaultStatus = 'Draft') {
        frappe.new_doc('Service Order', {
            status: defaultStatus
        });
    }

    refresh_card(orderName) {
        // Reload just this card's data
        // For now, refresh the entire board
        this.load_data();
    }

    refresh_data() {
        this.current_page = 0;
        this.load_data();
    }

    load_more_cards(status) {
        // Implementation for pagination
        console.log('Load more cards for status:', status);
    }

    setup_realtime() {
        if (!this.options.realtime) return;

        // Subscribe to kanban updates
        frappe.realtime.on('kanban_update', (data) => {
            this.handle_realtime_update(data);
        });

        frappe.realtime.on('kanban_refresh', () => {
            this.load_data();
        });
    }

    handle_realtime_update(data) {
        switch (data.type) {
            case 'status_change':
                this.handle_realtime_status_change(data.data);
                break;
            case 'technician_assigned':
                this.handle_realtime_technician_assignment(data.data);
                break;
            default:
                // General refresh for unknown updates
                this.load_data();
        }
    }

    handle_realtime_status_change(updateData) {
        // Find and update the affected card
        const card = this.board.find(`[data-order-name="${updateData.order_name}"]`);
        if (card.length) {
            // Move card to new column
            const newColumn = this.board.find(`[data-status="${updateData.new_status}"] .kanban-cards`);
            newColumn.append(card);

            // Update card data
            card.data('current-status', updateData.new_status);

            // Show notification if change was made by another user
            if (updateData.changed_by !== frappe.session.user) {
                frappe.show_alert({
                    message: __('Order {0} status updated to {1} by {2}',
                        [updateData.order_name, __(updateData.new_status), updateData.changed_by]),
                    indicator: 'blue'
                });
            }
        }
    }

    handle_realtime_technician_assignment(updateData) {
        if (updateData.assigned_by !== frappe.session.user) {
            frappe.show_alert({
                message: __('Technician assigned to order {0} by {1}',
                    [updateData.order_name, updateData.assigned_by]),
                indicator: 'blue'
            });

            // Refresh the specific card
            this.refresh_card(updateData.order_name);
        }
    }

    setup_auto_refresh() {
        if (this.options.auto_refresh > 0) {
            setInterval(() => {
                if (document.visibilityState === 'visible') {
                    this.load_data();
                }
            }, this.options.auto_refresh);
        }
    }

    setup_responsive() {
        // Handle mobile responsive behavior
        $(window).on('resize', () => {
            if ($(window).width() < 768) {
                this.container.addClass('mobile-view');
            } else {
                this.container.removeClass('mobile-view');
            }
        });

        // Initial check
        if ($(window).width() < 768) {
            this.container.addClass('mobile-view');
        }
    }

    setup_rtl_support() {
        // Additional RTL-specific setup
        this.container.find('.kanban-board').addClass('rtl-board');

        // Adjust drag and drop for RTL
        this.container.find('.kanban-cards').sortable('option', 'cursorAt', { right: 10, top: 10 });
    }

    show_loading() {
        this.container.find('#kanban-loading').show();
    }

    hide_loading() {
        this.container.find('#kanban-loading').hide();
    }

    show_error(message) {
        frappe.show_alert({
            message: message,
            indicator: 'red'
        });
    }

    update_status_indicator(status) {
        const indicator = this.container.find('.kanban-status-indicator');
        const statusDot = indicator.find('.status-dot');
        const statusText = indicator.find('.status-text');

        statusDot.removeClass('online offline error').addClass(status);

        switch (status) {
            case 'online':
                statusText.text(__('Live'));
                break;
            case 'offline':
                statusText.text(__('Offline'));
                break;
            case 'error':
                statusText.text(__('Error'));
                break;
        }
    }

    destroy() {
        // Cleanup
        if (this.options.realtime) {
            frappe.realtime.off('kanban_update');
            frappe.realtime.off('kanban_refresh');
        }

        clearTimeout(this.search_timeout);
        this.container.empty();
    }
}

// Initialize Kanban board on page load
frappe.provide('frappe.ui');
frappe.ui.ServiceOrderKanban = ServiceOrderKanban;

// Auto-initialize if container exists
$(document).ready(function () {
    if ($('#service-order-kanban').length) {
        const kanban = new ServiceOrderKanban('#service-order-kanban');

        // Make globally accessible
        window.service_order_kanban = kanban;
    }
}); 