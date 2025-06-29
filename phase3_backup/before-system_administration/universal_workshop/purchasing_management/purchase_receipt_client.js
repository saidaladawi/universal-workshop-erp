/**
 * Purchase Receipt Client-Side Quality Inspection Integration
 * Universal Workshop ERP - Purchasing Management
 * Arabic RTL Support and Mobile-Friendly Interface
 */

// Purchase Receipt Form Events
frappe.ui.form.on('Purchase Receipt', {
    refresh: function (frm) {
        setup_quality_inspection_interface(frm);
        setup_arabic_rtl_support(frm);
        setup_mobile_interface(frm);
        add_custom_buttons(frm);
    },

    onload: function (frm) {
        calculate_inspection_requirements(frm);
    },

    validate: function (frm) {
        validate_quality_inspection_requirements(frm);
    },

    before_submit: function (frm) {
        return validate_inspection_completion(frm);
    }
});

// Purchase Receipt Item Events
frappe.ui.form.on('Purchase Receipt Item', {
    item_code: function (frm, cdt, cdn) {
        let item = locals[cdt][cdn];
        check_item_inspection_requirement(frm, item);
    },

    batch_inspections_required: function (frm, cdt, cdn) {
        calculate_inspection_requirements(frm);
    }
});

function setup_quality_inspection_interface(frm) {
    """Setup Quality Inspection interface with status indicators"""

    if (frm.doc.quality_inspection_required) {
        // Add inspection status indicator
        let status_indicator = get_inspection_status_indicator(frm.doc.quality_inspection_status);
        frm.dashboard.set_headline_alert(
            `Quality Inspection Status: ${status_indicator} ${frm.doc.quality_inspection_status}`,
            get_status_color(frm.doc.quality_inspection_status)
        );

        // Show inspection summary
        if (frm.doc.total_inspections_pending > 0) {
            frm.dashboard.add_comment(
                `${frm.doc.total_inspections_pending} quality inspections pending`,
                'orange',
                true
            );
        }
    }
}

function setup_arabic_rtl_support(frm) {
    """Setup Arabic RTL support for Quality Inspection fields"""

    if (frappe.boot.lang === 'ar') {
        // Set RTL direction for Arabic text fields
        const arabic_fields = [
            'quality_inspection_notes_ar',
            'quality_inspection_status_ar'
        ];

        arabic_fields.forEach(fieldname => {
            if (frm.fields_dict[fieldname]) {
                frm.fields_dict[fieldname].$wrapper.addClass('rtl-field');
                frm.fields_dict[fieldname].$input.attr('dir', 'rtl');
                frm.fields_dict[fieldname].$input.css('text-align', 'right');
            }
        });

        // Update child table Arabic names
        frm.fields_dict.items.grid.wrapper.find('[data-fieldname="item_name_ar"]').each(function () {
            $(this).attr('dir', 'rtl').css('text-align', 'right');
        });
    }
}

function setup_mobile_interface(frm) {
    """Setup mobile-friendly interface for quality inspection"""

    // Check if on mobile device
    if (frappe.utils.is_mobile()) {
        // Adjust form layout for mobile
        frm.layout.wrapper.addClass('mobile-purchase-receipt');

        // Make inspection buttons larger for touch
        $('.btn-quality-inspection').css({
            'min-height': '44px',
            'padding': '12px 20px',
            'font-size': '16px'
        });

        // Improve child table display on mobile
        if (frm.fields_dict.items && frm.fields_dict.items.grid) {
            frm.fields_dict.items.grid.wrapper.addClass('mobile-child-table');
        }
    }
}

function add_custom_buttons(frm) {
    """Add custom buttons for Quality Inspection operations"""

    if (frm.doc.docstatus === 0) { // Draft state
        // Create Quality Inspections button
        frm.add_custom_button(__('Create Quality Inspections'), function () {
            create_quality_inspections_bulk(frm);
        }, __('Quality Inspection'));

        // Inspection Summary button
        frm.add_custom_button(__('Inspection Summary'), function () {
            show_inspection_summary(frm);
        }, __('Quality Inspection'));
    }

    if (frm.doc.docstatus === 1 && frm.doc.quality_inspection_required) { // Submitted
        // Refresh Inspection Status button
        frm.add_custom_button(__('Refresh Status'), function () {
            refresh_inspection_status(frm);
        }, __('Quality Inspection'));

        // Mobile Inspection Links button
        frm.add_custom_button(__('Mobile Inspection Links'), function () {
            show_mobile_inspection_links(frm);
        }, __('Quality Inspection'));
    }
}

function check_item_inspection_requirement(frm, item) {
    """Check if item requires quality inspection"""

    if (item.item_code) {
        frappe.db.get_value('Item', item.item_code, 'inspection_required_before_delivery')
            .then(r => {
                if (r.message && r.message.inspection_required_before_delivery) {
                    frappe.model.set_value(item.doctype, item.name, 'quality_inspection_required', 1);

                    // Set default batch inspections required
                    if (!item.batch_inspections_required) {
                        frappe.model.set_value(item.doctype, item.name, 'batch_inspections_required', 1);
                    }

                    // Update inspection status
                    frappe.model.set_value(item.doctype, item.name, 'inspection_status', 'Pending');
                } else {
                    frappe.model.set_value(item.doctype, item.name, 'quality_inspection_required', 0);
                    frappe.model.set_value(item.doctype, item.name, 'inspection_status', 'Not Required');
                }

                calculate_inspection_requirements(frm);
            });
    }
}

function calculate_inspection_requirements(frm) {
    """Calculate total inspection requirements"""

    let total_pending = 0;
    let inspection_required = false;

    frm.doc.items.forEach(item => {
        if (item.quality_inspection_required) {
            inspection_required = true;
            let required_inspections = item.batch_inspections_required || 1;
            let completed_inspections = item.inspections_completed || 0;

            if (completed_inspections < required_inspections) {
                total_pending += (required_inspections - completed_inspections);
            }
        }
    });

    frm.set_value('quality_inspection_required', inspection_required ? 1 : 0);
    frm.set_value('total_inspections_pending', total_pending);

    // Update overall status
    update_overall_inspection_status(frm);
}

function update_overall_inspection_status(frm) {
    """Update overall inspection status"""

    if (!frm.doc.quality_inspection_required) {
        frm.set_value('quality_inspection_status', 'Not Required');
        frm.set_value('quality_inspection_status_ar', 'غير مطلوب');
        return;
    }

    let pending_items = frm.doc.items.filter(item => item.inspection_status === 'Pending');
    let failed_items = frm.doc.items.filter(item => item.inspection_status === 'Failed');
    let in_progress_items = frm.doc.items.filter(item => item.inspection_status === 'In Progress');

    if (failed_items.length > 0) {
        frm.set_value('quality_inspection_status', 'Failed');
        frm.set_value('quality_inspection_status_ar', 'فشل');
    } else if (in_progress_items.length > 0) {
        frm.set_value('quality_inspection_status', 'In Progress');
        frm.set_value('quality_inspection_status_ar', 'قيد التنفيذ');
    } else if (pending_items.length > 0) {
        frm.set_value('quality_inspection_status', 'Pending');
        frm.set_value('quality_inspection_status_ar', 'في الانتظار');
    } else {
        frm.set_value('quality_inspection_status', 'Completed');
        frm.set_value('quality_inspection_status_ar', 'مكتمل');
    }
}

function validate_quality_inspection_requirements(frm) {
    """Validate quality inspection requirements"""

    calculate_inspection_requirements(frm);
    return true;
}

function validate_inspection_completion(frm) {
    """Validate inspection completion before submission"""

    if (frm.doc.quality_inspection_required && frm.doc.total_inspections_pending > 0) {
        frappe.msgprint({
            title: __('Quality Inspection Required'),
            message: __('Cannot submit Purchase Receipt. {0} quality inspections are still pending.', [frm.doc.total_inspections_pending]),
            indicator: 'red'
        });
        return false;
    }

    return true;
}

function create_quality_inspections_bulk(frm) {
    """Create quality inspections for all pending items"""

    let pending_items = frm.doc.items.filter(item =>
        item.quality_inspection_required && item.inspection_status === 'Pending'
    );

    if (pending_items.length === 0) {
        frappe.msgprint(__('No items require quality inspection'));
        return;
    }

    let promises = [];

    pending_items.forEach(item => {
        let promise = frappe.call({
            method: 'universal_workshop.purchasing_management.purchase_receipt_extensions.create_quality_inspection_from_purchase_receipt',
            args: {
                purchase_receipt: frm.doc.name,
                item_code: item.item_code,
                item_row: item.name
            }
        });
        promises.push(promise);
    });

    Promise.all(promises).then(results => {
        let created_count = results.filter(r => r.message).length;
        frappe.msgprint({
            title: __('Quality Inspections Created'),
            message: __('Created {0} quality inspection records', [created_count]),
            indicator: 'green'
        });

        refresh_inspection_status(frm);
    }).catch(error => {
        frappe.msgprint({
            title: __('Error'),
            message: __('Failed to create some quality inspections: {0}', [error.message]),
            indicator: 'red'
        });
    });
}

function show_inspection_summary(frm) {
    """Show inspection summary dialog"""

    frappe.call({
        method: 'universal_workshop.purchasing_management.purchase_receipt_extensions.get_inspection_summary',
        args: {
            purchase_receipt: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                let summary = r.message;

                let dialog = new frappe.ui.Dialog({
                    title: __('Quality Inspection Summary'),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'summary_html'
                        }
                    ]
                });

                let html = generate_inspection_summary_html(summary);
                dialog.fields_dict.summary_html.$wrapper.html(html);

                dialog.show();
            }
        }
    });
}

function generate_inspection_summary_html(summary) {
    """Generate HTML for inspection summary"""

    let html = `
        <div class="inspection-summary">
            <div class="row">
                <div class="col-sm-6">
                    <h5>${__('Overview')}</h5>
                    <p><strong>${__('Total Items')}:</strong> ${summary.total_items}</p>
                    <p><strong>${__('Items Requiring Inspection')}:</strong> ${summary.items_requiring_inspection}</p>
                    <p><strong>${__('Inspections Completed')}:</strong> ${summary.inspections_completed}</p>
                    <p><strong>${__('Inspections Pending')}:</strong> ${summary.inspections_pending}</p>
                    <p><strong>${__('Overall Status')}:</strong> 
                        <span class="label ${get_status_class(summary.overall_status)}">${summary.overall_status}</span>
                    </p>
                </div>
                <div class="col-sm-6">
                    <h5>${__('Items Detail')}</h5>
                    <div class="items-detail">
    `;

    summary.items_detail.forEach(item => {
        html += `
            <div class="item-detail">
                <p><strong>${item.item_code}</strong> - ${item.item_name}</p>
                <p><em>${item.item_name_ar}</em></p>
                <p>Status: <span class="label ${get_status_class(item.inspection_status)}">${item.inspection_status}</span></p>
                <p>Quality Score: ${item.quality_score}%</p>
                <a href="${item.mobile_url}" target="_blank" class="btn btn-sm btn-primary">
                    ${__('Mobile Inspection')}
                </a>
                <hr>
            </div>
        `;
    });

    html += `
                    </div>
                </div>
            </div>
        </div>
    `;

    return html;
}

function refresh_inspection_status(frm) {
    """Refresh inspection status from server"""

    frappe.call({
        method: 'universal_workshop.purchasing_management.purchase_receipt_extensions.update_purchase_receipt_inspection_status',
        args: {
            purchase_receipt: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                frm.reload_doc();
                frappe.show_alert({
                    message: __('Inspection status updated'),
                    indicator: 'green'
                });
            }
        }
    });
}

function show_mobile_inspection_links(frm) {
    """Show mobile inspection links dialog"""

    let pending_items = frm.doc.items.filter(item =>
        item.quality_inspection_required && item.inspection_status === 'Pending'
    );

    if (pending_items.length === 0) {
        frappe.msgprint(__('No pending inspections'));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Mobile Inspection Links'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'links_html'
            }
        ]
    });

    let html = '<div class="mobile-links">';

    pending_items.forEach(item => {
        let mobile_url = frappe.urllib.get_full_url(
            `/app/quality-inspection/new?purchase_receipt=${frm.doc.name}&item_code=${item.item_code}&purchase_receipt_item=${item.name}`
        );

        html += `
            <div class="mobile-link-item">
                <p><strong>${item.item_code}</strong> - ${item.item_name}</p>
                <p><em>${item.item_name_ar || ''}</em></p>
                <div class="btn-group" style="margin-bottom: 10px;">
                    <a href="${mobile_url}" target="_blank" class="btn btn-primary btn-sm">
                        ${__('Open on Mobile')}
                    </a>
                    <button class="btn btn-default btn-sm" onclick="copyToClipboard('${mobile_url}')">
                        ${__('Copy Link')}
                    </button>
                </div>
                <hr>
            </div>
        `;
    });

    html += '</div>';

    dialog.fields_dict.links_html.$wrapper.html(html);
    dialog.show();
}

// Utility Functions
function get_inspection_status_indicator(status) {
    """Get status indicator icon"""
    const indicators = {
        'Pending': '⏳',
        'In Progress': '🔄',
        'Completed': '✅',
        'Failed': '❌',
        'Not Required': '➖'
    };
    return indicators[status] || '❓';
}

function get_status_color(status) {
    """Get status color"""
    const colors = {
        'Pending': 'orange',
        'In Progress': 'blue',
        'Completed': 'green',
        'Failed': 'red',
        'Not Required': 'gray'
    };
    return colors[status] || 'gray';
}

function get_status_class(status) {
    """Get CSS class for status"""
    const classes = {
        'Pending': 'label-warning',
        'In Progress': 'label-info',
        'Completed': 'label-success',
        'Failed': 'label-danger',
        'Not Required': 'label-default'
    };
    return classes[status] || 'label-default';
}

function copyToClipboard(text) {
    """Copy text to clipboard"""
    navigator.clipboard.writeText(text).then(() => {
        frappe.show_alert({
            message: __('Link copied to clipboard'),
            indicator: 'green'
        });
    }).catch(() => {
        frappe.show_alert({
            message: __('Failed to copy link'),
            indicator: 'red'
        });
    });
}

// CSS for mobile responsiveness and Arabic RTL
frappe.require('/assets/universal_workshop/css/purchase_receipt_quality_inspection.css');

// Load Arabic translations
if (frappe.boot.lang === 'ar') {
    frappe.require('/assets/universal_workshop/js/purchase_receipt_quality_inspection_ar.js');
} 