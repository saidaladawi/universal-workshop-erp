/**
 * Universal Workshop ERP - Parts Compatibility Matrix UI
 * Interactive interface for visualizing and managing parts compatibility
 * Enhanced with VIN decoding and advanced fitment analysis
 * Copyright (c) 2024, Eng. Saeed Al-Adawi
 */

class CompatibilityMatrixUI {
	constructor(options = {}) {
		this.options = {
			container: options.container || '.compatibility-matrix',
			language: options.language || 'en',
			max_items: options.max_items || 50,
			auto_refresh: options.auto_refresh !== false,
			enable_vin_decoder: options.enable_vin_decoder !== false,
			enable_advanced_fitment: options.enable_advanced_fitment !== false,
			...options
		};

		this.selected_items = [];
		this.compatibility_data = null;
		this.search_results = [];
		this.filters = {};
		this.current_vehicle = null;
		this.current_language = 'en';

		this.init();
	}

	init() {
		this.loadInitialData();
		this.bindEvents();
		this.setupLanguageToggle();
		this.setupVINDecoder();
		console.log('CompatibilityMatrixUI initialized');
	}

	loadInitialData() {
		// Load vehicle makes
		this.loadVehicleMakes();

		// Load part categories
		this.loadPartCategories();

		// Initialize tooltips
		this.initializeTooltips();
	}

	bindEvents() {
		// Search form submission
		$(document).on('submit', '#compatibilitySearchForm', (e) => {
			e.preventDefault();
			this.performCompatibilitySearch();
		});

		// Reset filters
		$(document).on('click', '#resetFilters', () => {
			this.resetFilters();
		});

		// Vehicle make change
		$(document).on('change', '#vehicleMake', (e) => {
			this.loadVehicleModels($(e.target).val());
		});

		// View toggle buttons
		$(document).on('click', '#viewGrid', () => {
			this.switchView('grid');
		});

		$(document).on('click', '#viewList', () => {
			this.switchView('list');
		});

		// Export results
		$(document).on('click', '#exportResults', () => {
			this.exportResults();
		});

		// Part detail modal
		$(document).on('click', '.part-detail-btn', (e) => {
			const itemCode = $(e.target).data('item-code');
			this.showPartDetails(itemCode);
		});

		// Fitment check
		$(document).on('click', '.check-fitment-btn', (e) => {
			const itemCode = $(e.target).data('item-code');
			this.checkPartFitment(itemCode);
		});
	}

	setupLanguageToggle() {
		$(document).on('click', '#langToggle', () => {
			this.toggleLanguage();
		});
	}

	setupVINDecoder() {
		// VIN input formatting
		$(document).on('input', '#vinInput', (e) => {
			let value = $(e.target).val().toUpperCase().replace(/[^A-HJ-NPR-Z0-9]/g, '');
			$(e.target).val(value);
		});

		// VIN decode button
		$(document).on('click', '#decodeVinBtn', () => {
			this.decodeVIN();
		});
	}

	toggleLanguage() {
		this.current_language = this.current_language === 'en' ? 'ar' : 'en';
		this.updateLanguageDisplay();

		// Toggle RTL/LTR
		if (this.current_language === 'ar') {
			$('html').attr('dir', 'rtl').addClass('rtl');
		} else {
			$('html').attr('dir', 'ltr').removeClass('rtl');
		}
	}

	updateLanguageDisplay() {
		$('[data-en][data-ar]').each((i, el) => {
			const $el = $(el);
			const text = this.current_language === 'ar' ? $el.data('ar') : $el.data('en');
			$el.text(text);
		});
	}

	async loadVehicleMakes() {
		try {
			const response = await fetch('/api/method/universal_workshop.parts_inventory.compatibility_matrix.get_compatibility_filters');
			const data = await response.json();

			if (data.message && data.message.success) {
				const makes = data.message.filters.vehicle_makes || [];
				const $select = $('#vehicleMake');

				makes.forEach(make => {
					$select.append(`<option value="${make.name}">${make.name}</option>`);
				});
			}
		} catch (error) {
			console.error('Failed to load vehicle makes:', error);
		}
	}

	async loadVehicleModels(make) {
		if (!make) {
			$('#vehicleModel').html('<option value="">Select Model / اختر النموذج</option>');
			return;
		}

		try {
			// This would typically call a backend method to get models for the make
			// For now, we'll use a placeholder
			const $select = $('#vehicleModel');
			$select.html('<option value="">Loading models...</option>');

			// Simulate API call
			setTimeout(() => {
				$select.html(`
                    <option value="">Select Model / اختر النموذج</option>
                    <option value="Model A">Model A</option>
                    <option value="Model B">Model B</option>
                    <option value="Model C">Model C</option>
                `);
			}, 500);
		} catch (error) {
			console.error('Failed to load vehicle models:', error);
		}
	}

	async loadPartCategories() {
		try {
			const response = await fetch('/api/method/universal_workshop.parts_inventory.compatibility_matrix.get_compatibility_filters');
			const data = await response.json();

			if (data.message && data.message.success) {
				const categories = data.message.filters.part_categories || [];
				const $select = $('#partCategory');

				categories.forEach(category => {
					$select.append(`<option value="${category.name}">${category.name}</option>`);
				});
			}
		} catch (error) {
			console.error('Failed to load part categories:', error);
		}
	}

	async performCompatibilitySearch() {
		const formData = this.getSearchFormData();

		this.showLoading(true);

		try {
			const response = await fetch('/api/method/universal_workshop.parts_inventory.api.get_fitment_recommendations', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-Frappe-CSRF-Token': frappe.csrf_token || ''
				},
				body: JSON.stringify(formData)
			});

			const data = await response.json();

			if (data.message && data.message.success) {
				this.displayCompatibilityResults(data.message.data);
				this.updateVehicleInfoPanel(formData);
			} else {
				this.showError(data.message?.message || 'Search failed');
			}
		} catch (error) {
			console.error('Compatibility search failed:', error);
			this.showError('Search failed. Please try again.');
		} finally {
			this.showLoading(false);
		}
	}

	getSearchFormData() {
		return {
			vehicle_make: $('#vehicleMake').val(),
			vehicle_model: $('#vehicleModel').val(),
			vehicle_year: $('#vehicleYear').val(),
			service_type: $('#serviceType').val(),
			search_query: $('#partSearch').val(),
			part_category: $('#partCategory').val(),
			compatibility_type: $('#compatibilityType').val()
		};
	}

	displayCompatibilityResults(data) {
		const $results = $('#compatibilityResults');

		if (!data.categorized_parts || Object.keys(data.categorized_parts).length === 0) {
			$results.html(this.getNoResultsHTML());
			return;
		}

		let html = '';

		// Display top recommendations first
		if (data.top_recommendations && data.top_recommendations.length > 0) {
			html += this.renderTopRecommendations(data.top_recommendations);
		}

		// Display categorized parts
		html += this.renderCategorizedParts(data.categorized_parts);

		$results.html(html);

		// Update results column layout
		$('#resultsColumn').removeClass('col-md-8').addClass('col-md-8');
		$('#vehicleInfoPanel').show().removeClass('col-md-4').addClass('col-md-4');
	}

	renderTopRecommendations(recommendations) {
		let html = `
            <div class="mb-4">
                <h6 class="text-primary mb-3">
                    <i class="bi bi-star-fill"></i>
                    <span data-en="Top Recommendations" data-ar="أفضل التوصيات">Top Recommendations</span>
                </h6>
                <div class="row">
        `;

		recommendations.slice(0, 6).forEach(part => {
			html += `
                <div class="col-md-6 mb-3">
                    <div class="card part-card h-100">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0">${part.item_name}</h6>
                                <span class="fitment-score ${this.getFitmentScoreClass(part.fitment_score)}">
                                    ${part.fitment_score}%
                                </span>
                            </div>
                            <p class="text-muted small mb-2">${part.item_code}</p>
                            <p class="card-text small">${part.brand || 'N/A'}</p>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="h6 text-primary mb-0">$${(part.standard_rate || 0).toFixed(2)}</span>
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-outline-primary part-detail-btn" data-item-code="${part.item_code}">
                                        <i class="bi bi-info-circle"></i>
                                    </button>
                                    <button class="btn btn-outline-success check-fitment-btn" data-item-code="${part.item_code}">
                                        <i class="bi bi-check-circle"></i>
                                    </button>
                                </div>
                            </div>
                            ${part.fitment_details && part.fitment_details.length > 0 ? `
                                <div class="mt-2">
                                    <small class="text-success">
                                        <i class="bi bi-check"></i> ${part.fitment_details[0]}
                                    </small>
                                </div>
                            ` : ''}
                            ${part.warnings && part.warnings.length > 0 ? `
                                <div class="mt-1">
                                    <small class="text-warning">
                                        <i class="bi bi-exclamation-triangle"></i> ${part.warnings[0]}
                                    </small>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
		});

		html += `
                </div>
            </div>
        `;

		return html;
	}

	renderCategorizedParts(categorizedParts) {
		let html = `
            <div class="mb-4">
                <h6 class="text-secondary mb-3">
                    <i class="bi bi-grid-3x3-gap"></i>
                    <span data-en="Parts by Category" data-ar="القطع حسب الفئة">Parts by Category</span>
                </h6>
        `;

		Object.entries(categorizedParts).forEach(([category, parts]) => {
			html += `
                <div class="mb-4">
                    <h6 class="border-bottom pb-2">${category} (${parts.length})</h6>
                    <div class="row">
            `;

			parts.slice(0, 4).forEach(part => {
				html += `
                    <div class="col-md-6 col-lg-3 mb-3">
                        <div class="card part-card h-100">
                            <div class="card-body p-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <h6 class="card-title small mb-0">${part.item_name}</h6>
                                    <span class="fitment-score ${this.getFitmentScoreClass(part.fitment_score)}">
                                        ${part.fitment_score}%
                                    </span>
                                </div>
                                <p class="text-muted small mb-1">${part.item_code}</p>
                                <p class="small mb-2">${part.brand || 'N/A'}</p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="small text-primary">$${(part.standard_rate || 0).toFixed(2)}</span>
                                    <div class="btn-group btn-group-sm">
                                        <button class="btn btn-outline-primary btn-sm part-detail-btn" data-item-code="${part.item_code}">
                                            <i class="bi bi-info-circle"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
			});

			if (parts.length > 4) {
				html += `
                    <div class="col-12">
                        <button class="btn btn-outline-secondary btn-sm" onclick="this.showMoreParts('${category}')">
                            <span data-en="Show ${parts.length - 4} more parts" data-ar="عرض ${parts.length - 4} قطعة أخرى">
                                Show ${parts.length - 4} more parts
                            </span>
                        </button>
                    </div>
                `;
			}

			html += `
                    </div>
                </div>
            `;
		});

		html += '</div>';
		return html;
	}

	getFitmentScoreClass(score) {
		if (score >= 85) return 'fitment-perfect';
		if (score >= 65) return 'fitment-good';
		if (score >= 40) return 'fitment-possible';
		if (score >= 20) return 'fitment-check';
		return 'fitment-not-recommended';
	}

	updateVehicleInfoPanel(formData) {
		const $content = $('#vehicleInfoContent');

		let html = `
            <div class="text-white">
                <div class="mb-3">
                    <h6 class="text-white-50 mb-1">
                        <span data-en="Make" data-ar="الصانع">Make</span>
                    </h6>
                    <div class="h5">${formData.vehicle_make || 'Any'}</div>
                </div>
                <div class="mb-3">
                    <h6 class="text-white-50 mb-1">
                        <span data-en="Model" data-ar="النموذج">Model</span>
                    </h6>
                    <div class="h6">${formData.vehicle_model || 'Any'}</div>
                </div>
                <div class="mb-3">
                    <h6 class="text-white-50 mb-1">
                        <span data-en="Year" data-ar="السنة">Year</span>
                    </h6>
                    <div class="h6">${formData.vehicle_year || 'Any'}</div>
                </div>
        `;

		if (formData.service_type) {
			html += `
                <div class="mb-3">
                    <h6 class="text-white-50 mb-1">
                        <span data-en="Service Type" data-ar="نوع الخدمة">Service Type</span>
                    </h6>
                    <div class="h6">${formData.service_type}</div>
                </div>
            `;
		}

		html += '</div>';
		$content.html(html);
	}

	async decodeVIN() {
		const vin = $('#vinInput').val().trim();

		if (!vin || vin.length !== 17) {
			this.showError('Please enter a valid 17-character VIN');
			return;
		}

		try {
			$('#decodeVinBtn').prop('disabled', true).html('<i class="spinner-border spinner-border-sm"></i> Decoding...');

			const response = await fetch('/api/method/universal_workshop.parts_inventory.api.decode_vehicle_vin', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-Frappe-CSRF-Token': frappe.csrf_token || ''
				},
				body: JSON.stringify({ vin: vin })
			});

			const data = await response.json();

			if (data.message && data.message.success) {
				this.displayVINResults(data.message.data, data.message.compatible_parts);
			} else {
				this.showError(data.message?.message || 'VIN decoding failed');
			}
		} catch (error) {
			console.error('VIN decoding failed:', error);
			this.showError('VIN decoding failed. Please try again.');
		} finally {
			$('#decodeVinBtn').prop('disabled', false).html('<i class="bi bi-cpu"></i> <span data-en="Decode VIN" data-ar="فك تشفير VIN">Decode VIN</span>');
		}
	}

	displayVINResults(vinData, compatibleParts) {
		const $results = $('#vinResults');

		let html = `
            <div class="alert alert-success">
                <h6><i class="bi bi-check-circle"></i> VIN Decoded Successfully</h6>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <h6>Vehicle Information</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Manufacturer:</strong></td><td>${vinData.manufacturer}</td></tr>
                        <tr><td><strong>Model Year:</strong></td><td>${vinData.model_year || 'Unknown'}</td></tr>
                        <tr><td><strong>Country:</strong></td><td>${vinData.country}</td></tr>
                        <tr><td><strong>VIN:</strong></td><td><code>${vinData.vin}</code></td></tr>
                        <tr><td><strong>Check Digit Valid:</strong></td><td>
                            ${vinData.check_digit_valid ?
				'<span class="badge bg-success">Yes</span>' :
				'<span class="badge bg-warning">No</span>'}
                        </td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Compatible Parts Found</h6>
                    <p class="text-muted">${compatibleParts ? compatibleParts.length : 0} parts found</p>
                    <button class="btn btn-primary btn-sm" id="useVinDataBtn">
                        <i class="bi bi-arrow-right"></i> Use This Vehicle for Search
                    </button>
                </div>
            </div>
        `;

		if (vinData.warning) {
			html = `<div class="alert alert-warning"><small>${vinData.warning}</small></div>` + html;
		}

		$results.html(html).show();

		// Bind the use VIN data button
		$('#useVinDataBtn').on('click', () => {
			this.useVINDataForSearch(vinData);
			$('#vinDecoderModal').modal('hide');
		});
	}

	useVINDataForSearch(vinData) {
		// Populate search form with VIN data
		if (vinData.manufacturer) {
			$('#vehicleMake').val(vinData.manufacturer).trigger('change');
		}
		if (vinData.model_year) {
			$('#vehicleYear').val(vinData.model_year);
		}

		// Auto-trigger search
		setTimeout(() => {
			$('#compatibilitySearchForm').trigger('submit');
		}, 500);
	}

	async checkPartFitment(itemCode) {
		const formData = this.getSearchFormData();

		if (!formData.vehicle_make && !formData.vehicle_year) {
			this.showError('Please specify vehicle details for fitment check');
			return;
		}

		try {
			const vehicleInfo = {
				make: formData.vehicle_make,
				model: formData.vehicle_model,
				year: formData.vehicle_year
			};

			const response = await fetch('/api/method/universal_workshop.parts_inventory.api.check_part_vehicle_fitment', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-Frappe-CSRF-Token': frappe.csrf_token || ''
				},
				body: JSON.stringify({
					item_code: itemCode,
					vehicle_info: JSON.stringify(vehicleInfo),
					service_context: formData.service_type
				})
			});

			const data = await response.json();

			if (data.message && data.message.success) {
				this.showFitmentDetails(data.message.data);
			} else {
				this.showError(data.message?.message || 'Fitment check failed');
			}
		} catch (error) {
			console.error('Fitment check failed:', error);
			this.showError('Fitment check failed. Please try again.');
		}
	}

	showFitmentDetails(fitmentData) {
		// This would typically open a modal with detailed fitment information
		console.log('Fitment Details:', fitmentData);

		const message = `
            <strong>Fitment Status:</strong> ${fitmentData.fitment_status}<br>
            <strong>Confidence Score:</strong> ${fitmentData.confidence_score}%<br>
            <strong>Details:</strong><br>
            ${fitmentData.fitment_details.map(detail => `• ${detail}`).join('<br>')}
        `;

		frappe.msgprint({
			title: 'Part Fitment Analysis',
			message: message,
			indicator: fitmentData.confidence_score >= 70 ? 'green' :
				fitmentData.confidence_score >= 40 ? 'orange' : 'red'
		});
	}

	resetFilters() {
		$('#compatibilitySearchForm')[0].reset();
		$('#vehicleModel').html('<option value="">Select Model / اختر النموذج</option>');
		$('#compatibilityResults').html(this.getEmptyStateHTML());
		$('#vehicleInfoPanel').hide();
		$('#resultsColumn').removeClass('col-md-8').addClass('col-md-12');
	}

	switchView(viewType) {
		// Implementation for grid/list view toggle
		console.log('Switching to view:', viewType);

		$('#viewGrid, #viewList').removeClass('btn-primary').addClass('btn-outline-primary');
		$(`#view${viewType.charAt(0).toUpperCase() + viewType.slice(1)}`).removeClass('btn-outline-primary').addClass('btn-primary');
	}

	exportResults() {
		// Implementation for exporting results
		console.log('Exporting compatibility results');

		frappe.msgprint({
			title: 'Export Results',
			message: 'Export functionality will be implemented soon.',
			indicator: 'blue'
		});
	}

	showPartDetails(itemCode) {
		// Implementation for showing detailed part information
		console.log('Showing part details for:', itemCode);

		// This would typically open a modal with full part details
		frappe.msgprint({
			title: 'Part Details',
			message: `Detailed information for part ${itemCode} will be displayed here.`,
			indicator: 'blue'
		});
	}

	showLoading(show) {
		if (show) {
			$('#loadingSpinner').show();
			$('#compatibilityResults').hide();
		} else {
			$('#loadingSpinner').hide();
			$('#compatibilityResults').show();
		}
	}

	showError(message) {
		frappe.msgprint({
			title: 'Error',
			message: message,
			indicator: 'red'
		});
	}

	getNoResultsHTML() {
		return `
            <div class="text-center py-5">
                <i class="bi bi-search text-muted" style="font-size: 3rem;"></i>
                <h5 class="text-muted mt-3">
                    <span data-en="No compatible parts found" data-ar="لم يتم العثور على قطع متوافقة">
                        No compatible parts found
                    </span>
                </h5>
                <p class="text-muted">
                    <span data-en="Try adjusting your search criteria" data-ar="حاول تعديل معايير البحث">
                        Try adjusting your search criteria
                    </span>
                </p>
            </div>
        `;
	}

	getEmptyStateHTML() {
		return `
            <div class="text-center py-5">
                <i class="bi bi-search text-muted" style="font-size: 3rem;"></i>
                <h5 class="text-muted mt-3">
                    <span data-en="Search for parts to see compatibility matrix" data-ar="ابحث عن القطع لرؤية مصفوفة التوافق">
                        Search for parts to see compatibility matrix
                    </span>
                </h5>
                <p class="text-muted">
                    <span data-en="Use the filters above or decode a VIN to get started" data-ar="استخدم المرشحات أعلاه أو فك تشفير VIN للبدء">
                        Use the filters above or decode a VIN to get started
                    </span>
                </p>
            </div>
        `;
	}

	initializeTooltips() {
		// Initialize Bootstrap tooltips
		var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
		var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
			return new bootstrap.Tooltip(tooltipTriggerEl);
		});
	}
}

// Auto-initialize if jQuery is available
$(document).ready(function () {
	if (typeof window.compatibilityMatrix === 'undefined') {
		window.compatibilityMatrix = new CompatibilityMatrixUI();
	}
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
	module.exports = CompatibilityMatrixUI;
}
