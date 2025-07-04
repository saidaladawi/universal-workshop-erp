/**
 * Print Format Integration
 * Handles real-time branding updates in print formats and preview functionality
 */

class PrintFormatIntegration {
    constructor() {
        this.init();
    }

    init() {
        this.setupPrintFormatEnhancements();
        this.setupBrandingUpdates();
        this.setupPrintPreview();
    }

    setupPrintFormatEnhancements() {
        // Enhance print format selection dialogs
        $(document).on('show.bs.modal', '.print-format-dialog', () => {
            this.enhancePrintDialog();
        });

        // Add branding preview to print format list
        this.addBrandingPreviewToPrintFormats();
    }

    enhancePrintDialog() {
        // Add branding options to print dialog
        const dialog = $('.print-format-dialog');
        if (dialog.length && !dialog.find('.branding-options').length) {
            const brandingOptions = this.createBrandingOptionsHTML();
            dialog.find('.modal-body').prepend(brandingOptions);
            this.bindBrandingEvents(dialog);
        }
    }

    createBrandingOptionsHTML() {
        return `
            <div class="branding-options" style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                <h5>${__('Branding Options')}</h5>
                <div class="row">
                    <div class="col-md-6">
                        <label>
                            <input type="checkbox" id="include-logo" checked> 
                            ${__('Include Workshop Logo')}
                        </label>
                    </div>
                    <div class="col-md-6">
                        <label>
                            <input type="checkbox" id="use-theme-colors" checked> 
                            ${__('Use Theme Colors')}
                        </label>
                    </div>
                </div>
                <div class="row" style="margin-top: 10px;">
                    <div class="col-md-6">
                        <label>
                            <input type="checkbox" id="include-contact-info" checked> 
                            ${__('Include Contact Information')}
                        </label>
                    </div>
                    <div class="col-md-6">
                        <label>
                            <input type="checkbox" id="include-business-info" checked> 
                            ${__('Include Business License Info')}
                        </label>
                    </div>
                </div>
                <div class="row" style="margin-top: 10px;">
                    <div class="col-md-12">
                        <label for="print-language">${__('Print Language')}:</label>
                        <select id="print-language" class="form-control" style="width: 200px; display: inline-block; margin-left: 10px;">
                            <option value="en">English</option>
                            <option value="ar">العربية</option>
                            <option value="auto">${__('Auto Detect')}</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }

    bindBrandingEvents(dialog) {
        // Update preview when branding options change
        dialog.find('.branding-options input, .branding-options select').on('change', () => {
            this.updatePrintPreview(dialog);
        });

        // Add preview button
        if (!dialog.find('.preview-with-branding').length) {
            const previewBtn = `
                <button class="btn btn-default preview-with-branding" style="margin-right: 10px;">
                    ${__('Preview with Branding')}
                </button>
            `;
            dialog.find('.modal-footer .btn-primary').before(previewBtn);

            dialog.find('.preview-with-branding').on('click', () => {
                this.showBrandedPreview(dialog);
            });
        }
    }

    updatePrintPreview(dialog) {
        // Get current settings
        const settings = this.getBrandingSettings(dialog);

        // Update preview if it exists
        const previewFrame = dialog.find('#print-preview iframe');
        if (previewFrame.length) {
            this.applyBrandingToPreview(previewFrame[0], settings);
        }
    }

    getBrandingSettings(dialog) {
        return {
            includeLogo: dialog.find('#include-logo').is(':checked'),
            useThemeColors: dialog.find('#use-theme-colors').is(':checked'),
            includeContactInfo: dialog.find('#include-contact-info').is(':checked'),
            includeBusinessInfo: dialog.find('#include-business-info').is(':checked'),
            language: dialog.find('#print-language').val()
        };
    }

    showBrandedPreview(dialog) {
        const settings = this.getBrandingSettings(dialog);
        const doctype = dialog.data('doctype');
        const docname = dialog.data('docname');
        const printFormat = dialog.find('select[data-fieldname="print_format"]').val();

        // Show loading
        frappe.show_progress(__('Generating Preview'), 50, 100, __('Applying branding...'));

        // Get branded preview
        frappe.call({
            method: 'universal_workshop.print_formats.branding_utils.preview_print_format_with_branding',
            args: {
                doctype: doctype,
                docname: docname,
                print_format: printFormat,
                language: settings.language === 'auto' ? frappe.boot.lang : settings.language
            },
            callback: (r) => {
                frappe.hide_progress();

                if (r.message) {
                    this.showPreviewModal(r.message, settings);
                } else {
                    frappe.msgprint(__('Failed to generate branded preview'));
                }
            },
            error: () => {
                frappe.hide_progress();
                frappe.msgprint(__('Error generating preview'));
            }
        });
    }

    showPreviewModal(htmlContent, settings) {
        const previewModal = new frappe.ui.Dialog({
            title: __('Branded Print Preview'),
            size: 'extra-large',
            fields: [
                {
                    fieldtype: 'HTML',
                    options: `
                        <div class="print-preview-container" style="height: 600px; overflow: auto; border: 1px solid #ddd;">
                            ${htmlContent}
                        </div>
                        <div class="preview-actions" style="margin-top: 15px; text-align: center;">
                            <button class="btn btn-primary btn-print-now">${__('Print Now')}</button>
                            <button class="btn btn-default btn-download-pdf">${__('Download PDF')}</button>
                            <button class="btn btn-default btn-email-pdf">${__('Email PDF')}</button>
                        </div>
                    `
                }
            ]
        });

        previewModal.show();

        // Bind action buttons
        previewModal.$wrapper.find('.btn-print-now').on('click', () => {
            window.print();
        });

        previewModal.$wrapper.find('.btn-download-pdf').on('click', () => {
            this.downloadBrandedPDF(settings);
        });

        previewModal.$wrapper.find('.btn-email-pdf').on('click', () => {
            this.emailBrandedPDF(settings);
        });
    }

    setupBrandingUpdates() {
        // Listen for branding changes
        frappe.realtime.on('workshop_branding_updated', (data) => {
            this.refreshPrintFormats();
        });

        // Listen for theme changes
        frappe.realtime.on('workshop_theme_changed', (data) => {
            this.updatePrintFormatThemes(data.theme_data);
        });
    }

    refreshPrintFormats() {
        // Update all print formats with new branding
        frappe.call({
            method: 'universal_workshop.print_formats.print_format_manager.update_print_formats_branding',
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: __('Print formats updated with new branding'),
                        indicator: 'green'
                    });
                }
            }
        });
    }

    updatePrintFormatThemes(themeData) {
        // Apply new theme colors to current print previews
        const printFrames = $('iframe[src*="printview"]');
        printFrames.each((index, frame) => {
            this.applyThemeToFrame(frame, themeData);
        });
    }

    applyThemeToFrame(frame, themeData) {
        try {
            const frameDoc = frame.contentDocument || frame.contentWindow.document;
            const primaryColor = themeData.colors?.primary || '#1f4e79';
            const secondaryColor = themeData.colors?.secondary || '#2980b9';

            // Update CSS variables in frame
            const style = frameDoc.createElement('style');
            style.textContent = `
                :root {
                    --primary-color: ${primaryColor};
                    --secondary-color: ${secondaryColor};
                }
                .workshop-header { border-bottom-color: ${primaryColor} !important; }
                .workshop-name { color: ${primaryColor} !important; }
                .document-title { color: ${primaryColor} !important; border-bottom-color: ${secondaryColor} !important; }
                .table-header { background-color: ${primaryColor} !important; }
                .total-section { border-top-color: ${primaryColor} !important; }
                .workshop-footer { border-top-color: ${secondaryColor} !important; }
            `;
            frameDoc.head.appendChild(style);
        } catch (e) {
            console.warn('Could not apply theme to print frame:', e);
        }
    }

    setupPrintPreview() {
        // Enhance existing print preview functionality
        this.enhanceExistingPrintViews();

        // Add print format management interface
        this.addPrintFormatManagement();
    }

    enhanceExistingPrintViews() {
        // Intercept print view requests to add branding
        const originalPrintView = window.print_view;
        if (originalPrintView) {
            window.print_view = function (doctype, docname, print_format) {
                // Add branding parameters
                const url = new URL(window.location.origin + '/printview');
                url.searchParams.set('doctype', doctype);
                url.searchParams.set('name', docname);
                url.searchParams.set('format', print_format || 'Standard');
                url.searchParams.set('branded', '1');
                url.searchParams.set('language', frappe.boot.lang || 'en');

                window.open(url.toString(), '_blank');
            };
        }
    }

    addPrintFormatManagement() {
        // Add print format management to workspace
        if (frappe.boot.user.can_write.includes('Print Format')) {
            this.addPrintFormatWorkspaceCard();
        }
    }

    addPrintFormatWorkspaceCard() {
        // Add to Workshop workspace if it exists
        $(document).on('page-render', () => {
            if (frappe.get_route()[0] === 'workspace' && frappe.get_route()[1] === 'workshop') {
                this.injectPrintFormatCard();
            }
        });
    }

    injectPrintFormatCard() {
        const workspace = $('.workspace-container');
        if (workspace.length && !workspace.find('.print-format-management').length) {
            const card = `
                <div class="print-format-management widget" style="margin: 20px 0;">
                    <div class="widget-head">
                        <h4>${__('Print Format Management')}</h4>
                    </div>
                    <div class="widget-body">
                        <p>${__('Manage branded print formats for workshop documents')}</p>
                        <div class="btn-group">
                            <button class="btn btn-default btn-install-formats">
                                ${__('Install Default Formats')}
                            </button>
                            <button class="btn btn-default btn-update-branding">
                                ${__('Update Branding')}
                            </button>
                            <button class="btn btn-default btn-preview-formats">
                                ${__('Preview Formats')}
                            </button>
                        </div>
                    </div>
                </div>
            `;

            workspace.find('.workspace-body').append(card);
            this.bindPrintFormatCardEvents();
        }
    }

    bindPrintFormatCardEvents() {
        $('.btn-install-formats').on('click', () => {
            this.installDefaultFormats();
        });

        $('.btn-update-branding').on('click', () => {
            this.updateAllBranding();
        });

        $('.btn-preview-formats').on('click', () => {
            this.showFormatPreview();
        });
    }

    installDefaultFormats() {
        frappe.confirm(
            __('This will install default branded print formats. Continue?'),
            () => {
                frappe.show_progress(__('Installing'), 0, 100, __('Installing print formats...'));

                frappe.call({
                    method: 'universal_workshop.print_formats.print_format_manager.install_branded_print_formats',
                    callback: (r) => {
                        frappe.hide_progress();

                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                        } else {
                            frappe.msgprint(__('Failed to install print formats'));
                        }
                    }
                });
            }
        );
    }

    updateAllBranding() {
        frappe.show_progress(__('Updating'), 0, 100, __('Updating print format branding...'));

        frappe.call({
            method: 'universal_workshop.print_formats.print_format_manager.update_print_formats_branding',
            callback: (r) => {
                frappe.hide_progress();

                if (r.message && r.message.success) {
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });
                } else {
                    frappe.msgprint(__('Failed to update print format branding'));
                }
            }
        });
    }

    showFormatPreview() {
        frappe.call({
            method: 'universal_workshop.print_formats.print_format_manager.get_available_print_formats',
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.displayFormatPreview(r.message.formats);
                }
            }
        });
    }

    displayFormatPreview(formats) {
        const previewDialog = new frappe.ui.Dialog({
            title: __('Print Format Preview'),
            size: 'large',
            fields: [
                {
                    fieldtype: 'HTML',
                    options: this.generateFormatPreviewHTML(formats)
                }
            ]
        });

        previewDialog.show();
    }

    generateFormatPreviewHTML(formats) {
        let html = '<div class="format-preview-grid">';

        formats.forEach(format => {
            html += `
                <div class="format-card" style="border: 1px solid #ddd; margin: 10px; padding: 15px; border-radius: 5px;">
                    <h5>${format.name}</h5>
                    <p><strong>${__('Document Type')}:</strong> ${format.doctype}</p>
                    <p><strong>${__('Arabic Support')}:</strong> ${format.supports_arabic ? __('Yes') : __('No')}</p>
                    <button class="btn btn-sm btn-default preview-format" data-format="${format.name}" data-doctype="${format.doctype}">
                        ${__('Preview')}
                    </button>
                </div>
            `;
        });

        html += '</div>';

        // Add event handlers
        setTimeout(() => {
            $('.preview-format').on('click', function () {
                const formatName = $(this).data('format');
                const doctype = $(this).data('doctype');
                frappe.msgprint(__('Preview functionality coming soon for {0}', [formatName]));
            });
        }, 100);

        return html;
    }

    downloadBrandedPDF(settings) {
        frappe.msgprint(__('PDF download functionality will be implemented in the next phase'));
    }

    emailBrandedPDF(settings) {
        frappe.msgprint(__('Email PDF functionality will be implemented in the next phase'));
    }

    addBrandingPreviewToPrintFormats() {
        // Add branding preview to existing print format lists
        $(document).on('render', '.list-row', function () {
            const row = $(this);
            if (row.data('doctype') === 'Print Format') {
                if (!row.find('.branding-indicator').length) {
                    row.find('.list-row-col:last').append(
                        '<span class="branding-indicator label label-info" style="margin-left: 5px;">Branded</span>'
                    );
                }
            }
        });
    }
}

// Initialize when DOM is ready
$(document).ready(() => {
    if (frappe.session.user !== 'Guest') {
        window.printFormatIntegration = new PrintFormatIntegration();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PrintFormatIntegration;
} 