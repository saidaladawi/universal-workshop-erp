/**
 * Universal Workshop Contextual Help System
 * Global JavaScript for in-application help and guidance
 * Copyright (c) 2024, Universal Workshop
 */

class ContextualHelpSystem {
	constructor() {
		this.helpContent = {};
		this.currentContext = {};
		this.helpWidget = null;
		this.activeTooltips = [];
		this.isInitialized = false;

		this.init();
	}

	init() {
		if (this.isInitialized) return;

		// Wait for Frappe to be ready
		if (typeof frappe === 'undefined') {
			setTimeout(() => this.init(), 100);
			return;
		}

		this.setupEventListeners();
		this.loadHelpContent();
		this.createHelpWidget();
		this.setupRouteMonitoring();

		this.isInitialized = true;
		console.log('Contextual Help System initialized');
	}

	setupEventListeners() {
		// Global help shortcut (F1 key)
		$(document).on('keydown', (e) => {
			if (e.key === 'F1') {
				e.preventDefault();
				this.showContextualHelp();
			}
		});

		// Help icon clicks
		$(document).on('click', '.help-icon', (e) => {
			e.preventDefault();
			const helpKey = $(e.target).data('help-key');
			if (helpKey) {
				this.showHelpContent(helpKey);
			} else {
				this.showContextualHelp();
			}
		});

		// Form field help
		$(document).on('mouseenter', '.frappe-control[data-fieldname]', (e) => {
			const fieldname = $(e.target).closest('.frappe-control').data('fieldname');
			const doctype = this.getCurrentDoctype();

			if (fieldname && doctype) {
				this.showFieldHelp(doctype, fieldname, e.target);
			}
		});

		// Help widget interactions
		$(document).on('click', '.help-widget-toggle', () => {
			this.toggleHelpWidget();
		});

		$(document).on('click', '.contextual-help-close', (e) => {
			$(e.target).closest('.contextual-help-overlay').remove();
		});
	}

	setupRouteMonitoring() {
		// Monitor route changes
		let currentRoute = window.location.pathname;

		const checkRouteChange = () => {
			if (window.location.pathname !== currentRoute) {
				currentRoute = window.location.pathname;
				this.onRouteChange(currentRoute);
			}
		};

		// Check for route changes periodically
		setInterval(checkRouteChange, 500);

		// Initial route setup
		this.onRouteChange(currentRoute);
	}

	onRouteChange(route) {
		this.currentContext.route = route;
		this.currentContext.doctype = this.getCurrentDoctype();
		this.currentContext.page = this.getCurrentPage();

		// Clear existing help overlays
		this.clearActiveTooltips();

		// Load contextual help for new route
		this.loadContextualHelp();

		// Update help widget
		this.updateHelpWidget();
	}

	getCurrentDoctype() {
		// Extract doctype from current page
		if (frappe.ui.form && frappe.ui.form.doc) {
			return frappe.ui.form.doc.doctype;
		}

		if (frappe.router && frappe.router.current_route) {
			const route = frappe.router.current_route;
			if (route[0] === 'Form' && route[1]) {
				return route[1];
			}
			if (route[0] === 'List' && route[1]) {
				return route[1];
			}
		}

		return null;
	}

	getCurrentPage() {
		if (frappe.router && frappe.router.current_route) {
			return frappe.router.current_route.join('/');
		}
		return window.location.pathname;
	}

	loadHelpContent() {
		// Load help content from cache or server
		const cached = this.getCachedHelpContent();
		if (cached) {
			this.helpContent = cached;
			return;
		}

		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_help_widget_data',
			callback: (r) => {
				if (r.message) {
					this.helpContent = r.message;
					this.cacheHelpContent(r.message);
				}
			}
		});
	}

	loadContextualHelp() {
		const { route, doctype } = this.currentContext;

		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_contextual_help',
			args: {
				route: route,
				doctype: doctype
			},
			callback: (r) => {
				if (r.message && r.message.length > 0) {
					this.displayContextualHelp(r.message);
				}
			}
		});
	}

	displayContextualHelp(helpItems) {
		// Display contextual help based on help type
		helpItems.forEach(item => {
			switch (item.help_type) {
				case 'Tooltip':
					this.showTooltip(item);
					break;
				case 'Contextual Banner':
					this.showContextualBanner(item);
					break;
				case 'Inline Help':
					this.showInlineHelp(item);
					break;
				default:
					// Store for manual access
					this.storeHelpItem(item);
			}
		});
	}

	showTooltip(helpItem) {
		// Find target element
		let target = null;

		if (helpItem.target_field && helpItem.target_doctype) {
			target = $(`.frappe-control[data-fieldname="${helpItem.target_field}"]`);
		}

		if (target && target.length > 0) {
			const tooltip = this.createTooltip(helpItem.tooltip_text || helpItem.content, target[0]);
			this.activeTooltips.push(tooltip);
		}
	}

	showContextualBanner(helpItem) {
		const banner = $(`
            <div class="contextual-help-banner alert alert-info" data-help-key="${helpItem.content_key}">
                <button type="button" class="close contextual-help-close" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
                <div class="help-banner-content">
                    <h6><i class="fa fa-info-circle"></i> ${helpItem.title}</h6>
                    <div>${helpItem.content}</div>
                    ${this.getRelatedLinksHtml(helpItem)}
                </div>
            </div>
        `);

		// Insert banner at top of content area
		const contentArea = $('.layout-main-section, .page-content').first();
		if (contentArea.length > 0) {
			contentArea.prepend(banner);
		}
	}

	showInlineHelp(helpItem) {
		// Add inline help next to relevant field or section
		if (helpItem.target_field && helpItem.target_doctype) {
			const field = $(`.frappe-control[data-fieldname="${helpItem.target_field}"]`);
			if (field.length > 0) {
				const inlineHelp = $(`
                    <div class="inline-help-content">
                        <small class="text-muted">
                            <i class="fa fa-question-circle"></i>
                            ${helpItem.content}
                        </small>
                    </div>
                `);
				field.after(inlineHelp);
			}
		}
	}

	showFieldHelp(doctype, fieldname, target) {
		// Show field-specific help on hover
		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_contextual_help',
			args: {
				route: this.currentContext.route,
				doctype: doctype,
				field: fieldname
			},
			callback: (r) => {
				if (r.message && r.message.length > 0) {
					const helpItem = r.message[0]; // Get first matching help
					if (helpItem.help_type === 'Tooltip') {
						this.createTemporaryTooltip(helpItem.tooltip_text || helpItem.content, target);
					}
				}
			}
		});
	}

	createTooltip(content, target) {
		// Use Frappe's tooltip system or create custom
		if (typeof frappe.ui.Tooltip !== 'undefined') {
			return new frappe.ui.Tooltip({
				target: target,
				content: content,
				position: 'bottom'
			});
		} else {
			// Fallback to simple tooltip
			return this.createSimpleTooltip(content, target);
		}
	}

	createTemporaryTooltip(content, target) {
		const tooltip = this.createTooltip(content, target);

		// Auto-remove after 3 seconds
		setTimeout(() => {
			if (tooltip && tooltip.destroy) {
				tooltip.destroy();
			}
		}, 3000);

		return tooltip;
	}

	createSimpleTooltip(content, target) {
		const tooltip = $(`
            <div class="custom-tooltip">
                <div class="custom-tooltip-content">${content}</div>
                <div class="custom-tooltip-arrow"></div>
            </div>
        `);

		const $target = $(target);
		const offset = $target.offset();

		tooltip.css({
			position: 'absolute',
			top: offset.top + $target.outerHeight() + 5,
			left: offset.left,
			zIndex: 1000
		});

		$('body').append(tooltip);

		return {
			destroy: () => tooltip.remove()
		};
	}

	createHelpWidget() {
		// Create floating help widget
		this.helpWidget = $(`
            <div class="help-widget" id="contextual-help-widget">
                <div class="help-widget-toggle" title="Help & Guidance">
                    <i class="fa fa-question-circle"></i>
                </div>
                <div class="help-widget-content" style="display: none;">
                    <div class="help-widget-header">
                        <h6><i class="fa fa-question-circle"></i> ${__('Help & Guidance')}</h6>
                        <button class="btn btn-sm help-widget-close">×</button>
                    </div>
                    <div class="help-widget-body">
                        <div class="help-search">
                            <input type="text" class="form-control form-control-sm" 
                                   placeholder="${__('Search help...')}" id="help-search-input">
                        </div>
                        <div class="help-categories">
                            <div class="help-category" data-category="contextual">
                                <h6>${__('Current Page')}</h6>
                                <div id="contextual-help-list"></div>
                            </div>
                            <div class="help-category" data-category="popular">
                                <h6>${__('Popular')}</h6>
                                <div id="popular-help-list"></div>
                            </div>
                            <div class="help-category" data-category="recent">
                                <h6>${__('Recent')}</h6>
                                <div id="recent-help-list"></div>
                            </div>
                        </div>
                        <div class="help-actions">
                            <button class="btn btn-sm btn-primary" id="show-all-help">
                                ${__('Browse All Help')}
                            </button>
                            <button class="btn btn-sm btn-secondary" id="help-feedback">
                                ${__('Give Feedback')}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `);

		// Add CSS styles
		this.addHelpWidgetStyles();

		// Append to body
		$('body').append(this.helpWidget);

		// Setup widget interactions
		this.setupHelpWidgetEvents();
	}

	addHelpWidgetStyles() {
		if ($('#contextual-help-styles').length > 0) return;

		const styles = `
            <style id="contextual-help-styles">
                .help-widget {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 1000;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                
                .help-widget-toggle {
                    width: 50px;
                    height: 50px;
                    background: #007bff;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    cursor: pointer;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    transition: all 0.3s ease;
                }
                
                .help-widget-toggle:hover {
                    background: #0056b3;
                    transform: scale(1.1);
                }
                
                .help-widget-content {
                    position: absolute;
                    bottom: 60px;
                    right: 0;
                    width: 350px;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    border: 1px solid #ddd;
                    max-height: 500px;
                    overflow-y: auto;
                }
                
                .help-widget-header {
                    padding: 15px;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    background: #f8f9fa;
                    border-radius: 8px 8px 0 0;
                }
                
                .help-widget-body {
                    padding: 15px;
                }
                
                .help-search input {
                    margin-bottom: 15px;
                }
                
                .help-category {
                    margin-bottom: 20px;
                }
                
                .help-category h6 {
                    color: #6c757d;
                    font-size: 12px;
                    text-transform: uppercase;
                    margin-bottom: 8px;
                }
                
                .help-item {
                    padding: 8px 0;
                    border-bottom: 1px solid #f0f0f0;
                    cursor: pointer;
                }
                
                .help-item:hover {
                    background: #f8f9fa;
                    margin: 0 -10px;
                    padding: 8px 10px;
                    border-radius: 4px;
                }
                
                .help-item-title {
                    font-weight: 500;
                    color: #333;
                    font-size: 13px;
                }
                
                .help-item-type {
                    font-size: 11px;
                    color: #6c757d;
                    text-transform: uppercase;
                }
                
                .help-actions {
                    border-top: 1px solid #eee;
                    padding-top: 15px;
                    margin-top: 15px;
                }
                
                .help-actions button {
                    width: 100%;
                    margin-bottom: 5px;
                }
                
                .contextual-help-banner {
                    margin-bottom: 20px;
                    border-left: 4px solid #007bff;
                }
                
                .custom-tooltip {
                    background: rgba(0,0,0,0.8);
                    color: white;
                    padding: 8px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    max-width: 250px;
                    word-wrap: break-word;
                }
                
                .custom-tooltip-arrow {
                    position: absolute;
                    top: -5px;
                    left: 10px;
                    width: 0;
                    height: 0;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-bottom: 5px solid rgba(0,0,0,0.8);
                }
                
                .inline-help-content {
                    margin-top: 5px;
                    padding: 5px;
                    background: #f8f9fa;
                    border-radius: 3px;
                    border-left: 3px solid #007bff;
                }
                
                .help-widget-close {
                    background: none;
                    border: none;
                    font-size: 18px;
                    color: #6c757d;
                    cursor: pointer;
                }
                
                @media (max-width: 768px) {
                    .help-widget-content {
                        width: 300px;
                        right: -280px;
                    }
                }
            </style>
        `;

		$('head').append(styles);
	}

	setupHelpWidgetEvents() {
		// Toggle widget
		$(document).on('click', '.help-widget-toggle', () => {
			this.toggleHelpWidget();
		});

		// Close widget
		$(document).on('click', '.help-widget-close', () => {
			this.hideHelpWidget();
		});

		// Search functionality
		$(document).on('input', '#help-search-input', (e) => {
			this.searchHelp(e.target.value);
		});

		// Help item clicks
		$(document).on('click', '.help-item', (e) => {
			const contentKey = $(e.currentTarget).data('content-key');
			if (contentKey) {
				this.showHelpContent(contentKey);
			}
		});

		// Action buttons
		$(document).on('click', '#show-all-help', () => {
			frappe.set_route('List', 'Help Content');
		});

		$(document).on('click', '#help-feedback', () => {
			this.showFeedbackDialog();
		});
	}

	toggleHelpWidget() {
		const content = this.helpWidget.find('.help-widget-content');
		if (content.is(':visible')) {
			this.hideHelpWidget();
		} else {
			this.showHelpWidget();
		}
	}

	showHelpWidget() {
		this.helpWidget.find('.help-widget-content').slideDown(200);
		this.updateHelpWidget();
	}

	hideHelpWidget() {
		this.helpWidget.find('.help-widget-content').slideUp(200);
	}

	updateHelpWidget() {
		// Update popular and recent help
		this.updatePopularHelp();
		this.updateRecentHelp();
		this.updateContextualHelp();
	}

	updatePopularHelp() {
		if (this.helpContent.popular) {
			const list = $('#popular-help-list');
			list.empty();

			this.helpContent.popular.forEach(item => {
				const helpItem = $(`
                    <div class="help-item" data-content-key="${item.content_key}">
                        <div class="help-item-title">${item.title}</div>
                        <div class="help-item-type">${item.help_type}</div>
                    </div>
                `);
				list.append(helpItem);
			});
		}
	}

	updateRecentHelp() {
		if (this.helpContent.recent) {
			const list = $('#recent-help-list');
			list.empty();

			this.helpContent.recent.forEach(item => {
				const helpItem = $(`
                    <div class="help-item" data-content-key="${item.content_key}">
                        <div class="help-item-title">${item.title}</div>
                        <div class="help-item-type">${item.help_type}</div>
                    </div>
                `);
				list.append(helpItem);
			});
		}
	}

	updateContextualHelp() {
		// Load contextual help for current page
		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_contextual_help',
			args: {
				route: this.currentContext.route,
				doctype: this.currentContext.doctype
			},
			callback: (r) => {
				const list = $('#contextual-help-list');
				list.empty();

				if (r.message && r.message.length > 0) {
					r.message.forEach(item => {
						const helpItem = $(`
                            <div class="help-item" data-content-key="${item.content_key}">
                                <div class="help-item-title">${item.title}</div>
                                <div class="help-item-type">${item.help_type}</div>
                            </div>
                        `);
						list.append(helpItem);
					});
				} else {
					list.html('<div class="text-muted">' + __('No help available for this page') + '</div>');
				}
			}
		});
	}

	showContextualHelp() {
		// Show contextual help modal
		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_contextual_help',
			args: {
				route: this.currentContext.route,
				doctype: this.currentContext.doctype
			},
			callback: (r) => {
				if (r.message && r.message.length > 0) {
					this.displayHelpModal(r.message);
				} else {
					frappe.msgprint(__('No help available for this page'));
				}
			}
		});
	}

	displayHelpModal(helpItems) {
		let content = '<div class="contextual-help-modal">';

		helpItems.forEach(item => {
			content += `
                <div class="help-modal-item">
                    <h6>${item.title}</h6>
                    <div class="help-content">${item.content || item.tooltip_text}</div>
                    ${this.getRelatedLinksHtml(item)}
                </div>
            `;
		});

		content += '</div>';

		frappe.msgprint({
			title: __('Help & Guidance'),
			message: content,
			wide: true
		});
	}

	showHelpContent(contentKey) {
		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.get_help_content_details',
			args: {
				content_key: contentKey
			},
			callback: (r) => {
				if (r.message) {
					this.displayHelpContentModal(r.message);
				}
			}
		});
	}

	displayHelpContentModal(helpData) {
		const content = helpData.content;
		let html = `
            <div class="help-content-detail">
                <div class="help-content-body">
                    ${content.content || content.tooltip_text}
                </div>
        `;

		if (helpData.related_documentation && helpData.related_documentation.length > 0) {
			html += '<h6>' + __('Related Documentation') + '</h6><ul>';
			helpData.related_documentation.forEach(doc => {
				html += `<li><a href="${doc.url}" target="_blank">${doc.title}</a></li>`;
			});
			html += '</ul>';
		}

		if (helpData.related_training && helpData.related_training.length > 0) {
			html += '<h6>' + __('Related Training') + '</h6><ul>';
			helpData.related_training.forEach(training => {
				html += `<li>${training.title} (${training.estimated_duration}h)</li>`;
			});
			html += '</ul>';
		}

		html += `
                <div class="help-content-actions">
                    <button class="btn btn-sm btn-success" onclick="contextualHelp.rateHelpful('${content.content_key}', 5)">
                        <i class="fa fa-thumbs-up"></i> Helpful
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="contextualHelp.rateHelpful('${content.content_key}', 2)">
                        <i class="fa fa-thumbs-down"></i> Not Helpful
                    </button>
                </div>
            </div>
        `;

		frappe.msgprint({
			title: content.title,
			message: html,
			wide: true
		});
	}

	getRelatedLinksHtml(helpItem) {
		// Generate HTML for related links (placeholder)
		return `
            <div class="help-related-links">
                <small class="text-muted">
                    <i class="fa fa-external-link"></i> 
                    <a href="#" onclick="contextualHelp.showHelpContent('${helpItem.content_key}')">${__('View Details')}</a>
                </small>
            </div>
        `;
	}

	searchHelp(query) {
		if (!query || query.length < 2) return;

		frappe.call({
			method: 'universal_workshop.training_management.doctype.help_content.help_content.search_help_content',
			args: {
				query: query
			},
			callback: (r) => {
				if (r.message) {
					this.displaySearchResults(r.message);
				}
			}
		});
	}

	displaySearchResults(results) {
		// Display search results in widget
		const categories = this.helpWidget.find('.help-categories');
		categories.hide();

		const searchResults = $(`
            <div class="help-search-results">
                <h6>${__('Search Results')}</h6>
                <div id="search-results-list"></div>
                <button class="btn btn-sm btn-link" id="clear-search">${__('Clear Search')}</button>
            </div>
        `);

		const resultsList = searchResults.find('#search-results-list');
		results.forEach(item => {
			const helpItem = $(`
                <div class="help-item" data-content-key="${item.content_key}">
                    <div class="help-item-title">${item.title}</div>
                    <div class="help-item-type">${item.help_type}</div>
                </div>
            `);
			resultsList.append(helpItem);
		});

		this.helpWidget.find('.help-widget-body').append(searchResults);

		// Clear search handler
		$(document).on('click', '#clear-search', () => {
			this.clearSearch();
		});
	}

	clearSearch() {
		this.helpWidget.find('.help-search-results').remove();
		this.helpWidget.find('.help-categories').show();
		this.helpWidget.find('#help-search-input').val('');
	}

	clearActiveTooltips() {
		this.activeTooltips.forEach(tooltip => {
			if (tooltip && tooltip.destroy) {
				tooltip.destroy();
			}
		});
		this.activeTooltips = [];

		// Remove custom tooltips and banners
		$('.custom-tooltip, .contextual-help-banner, .inline-help-content').remove();
	}

	rateHelpful(contentKey, rating) {
		frappe.call({
			method: 'frappe.client.get_value',
			args: {
				doctype: 'Help Content',
				filters: { content_key: contentKey },
				fieldname: 'name'
			},
			callback: (r) => {
				if (r.message && r.message.name) {
					frappe.call({
						method: 'record_helpfulness_rating',
						doc: {
							doctype: 'Help Content',
							name: r.message.name
						},
						args: {
							rating: rating
						},
						callback: () => {
							frappe.show_alert({
								message: __('Thank you for your feedback!'),
								indicator: 'green'
							});
						}
					});
				}
			}
		});
	}

	showFeedbackDialog() {
		const d = new frappe.ui.Dialog({
			title: __('Help System Feedback'),
			fields: [
				{
					label: __('How would you rate the help system?'),
					fieldname: 'rating',
					fieldtype: 'Rating',
					reqd: 1
				},
				{
					label: __('Comments'),
					fieldname: 'comments',
					fieldtype: 'Text',
					description: __('Tell us how we can improve the help system')
				}
			],
			primary_action_label: __('Submit Feedback'),
			primary_action: (values) => {
				// Submit feedback (implement as needed)
				frappe.show_alert({
					message: __('Thank you for your feedback!'),
					indicator: 'green'
				});
				d.hide();
			}
		});

		d.show();
	}

	getCachedHelpContent() {
		try {
			const cached = localStorage.getItem('contextual_help_cache');
			if (cached) {
				const data = JSON.parse(cached);
				if (Date.now() - data.timestamp < 30 * 60 * 1000) { // 30 minutes
					return data.content;
				}
			}
		} catch (e) {
			console.warn('Error reading help cache:', e);
		}
		return null;
	}

	cacheHelpContent(content) {
		try {
			localStorage.setItem('contextual_help_cache', JSON.stringify({
				content: content,
				timestamp: Date.now()
			}));
		} catch (e) {
			console.warn('Error caching help content:', e);
		}
	}

	storeHelpItem(item) {
		// Store help item for later access
		if (!this.helpContent.contextual) {
			this.helpContent.contextual = [];
		}
		this.helpContent.contextual.push(item);
	}
}

// Initialize the contextual help system
let contextualHelp;

$(document).ready(() => {
	// Wait a bit for Frappe to fully load
	setTimeout(() => {
		contextualHelp = new ContextualHelpSystem();

		// Make it globally available
		window.contextualHelp = contextualHelp;

		// Expose key methods globally
		window.showContextualHelp = () => contextualHelp.showContextualHelp();
		window.showHelpContent = (key) => contextualHelp.showHelpContent(key);
	}, 1000);
});
