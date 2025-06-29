// Purchase Receipt Quality Inspection Integration
// Universal Workshop ERP - Mobile & Arabic Support

frappe.ui.form.on('Purchase Receipt', {
    refresh: function (frm) {
        setup_quality_inspection_interface(frm);
        add_quality_inspection_buttons(frm);
    },

    onload: function (frm) {
        calculate_inspection_requirements(frm);
    },

    before_submit: function (frm) {
        return validate_inspection_completion(frm);
    }
});

frappe.ui.form.on('Purchase Receipt Item', {
    item_code: function (frm, cdt, cdn) {
        let item = locals[cdt][cdn];
        check_item_inspection_requirement(frm, item);
    }
});

function setup_quality_inspection_interface(frm) {
    if (frm.doc.quality_inspection_required) {
        let status = frm.doc.quality_inspection_status || 'Not Required';
        frm.dashboard.set_headline_alert(
            `Quality Inspection: ${status}`,
            get_status_color(status)
        );

        if (frm.doc.total_inspections_pending > 0) {
            frm.dashboard.add_comment(
                `${frm.doc.total_inspections_pending} inspections pending`,
                'orange'
            );
        }
    }
}

function add_quality_inspection_buttons(frm) {
    if (frm.doc.docstatus === 0) {
        frm.add_custom_button(__('Create Quality Inspections'), function () {
            create_quality_inspections_bulk(frm);
        }, __('Quality Inspection'));

        frm.add_custom_button(__('Inspection Summary'), function () {
            show_inspection_summary(frm);
        }, __('Quality Inspection'));
    }

    if (frm.doc.docstatus === 1 && frm.doc.quality_inspection_required) {
        frm.add_custom_button(__('Refresh Status'), function () {
            refresh_inspection_status(frm);
        }, __('Quality Inspection'));

        frm.add_custom_button(__('Mobile Links'), function () {
            show_mobile_inspection_links(frm);
        }, __('Quality Inspection'));
    }
}

function check_item_inspection_requirement(frm, item) {
    if (item.item_code) {
        frappe.db.get_value('Item', item.item_code, 'inspection_required_before_delivery')
            .then(r => {
                if (r.message && r.message.inspection_required_before_delivery) {
                    frappe.model.set_value(item.doctype, item.name, 'quality_inspection_required', 1);
                    frappe.model.set_value(item.doctype, item.name, 'inspection_status', 'Pending');
                    if (!item.batch_inspections_required) {
                        frappe.model.set_value(item.doctype, item.name, 'batch_inspections_required', 1);
                    }
                } else {
                    frappe.model.set_value(item.doctype, item.name, 'quality_inspection_required', 0);
                    frappe.model.set_value(item.doctype, item.name, 'inspection_status', 'Not Required');
                }
                calculate_inspection_requirements(frm);
            });
    }
}

function calculate_inspection_requirements(frm) {
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
    update_overall_inspection_status(frm);
}

function update_overall_inspection_status(frm) {
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

function validate_inspection_completion(frm) {
    if (frm.doc.quality_inspection_required && frm.doc.total_inspections_pending > 0) {
        frappe.msgprint({
            title: __('Quality Inspection Required'),
            message: __('Cannot submit Purchase Receipt. {0} quality inspections pending.', [frm.doc.total_inspections_pending]),
            indicator: 'red'
        });
        return false;
    }
    return true;
}

function create_quality_inspections_bulk(frm) {
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
    });
}

function show_inspection_summary(frm) {
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
                    fields: [{
                        fieldtype: 'HTML',
                        fieldname: 'summary_html'
                    }]
                });

                let html = `
                    <div class="inspection-summary">
                        <h5>${__('Overview')}</h5>
                        <p><strong>${__('Total Items')}:</strong> ${summary.total_items}</p>
                        <p><strong>${__('Items Requiring Inspection')}:</strong> ${summary.items_requiring_inspection}</p>
                        <p><strong>${__('Inspections Completed')}:</strong> ${summary.inspections_completed}</p>
                        <p><strong>${__('Inspections Pending')}:</strong> ${summary.inspections_pending}</p>
                        <p><strong>${__('Overall Status')}:</strong> ${summary.overall_status}</p>
                    </div>
                `;

                dialog.fields_dict.summary_html.$wrapper.html(html);
                dialog.show();
            }
        }
    });
}

function refresh_inspection_status(frm) {
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
    let pending_items = frm.doc.items.filter(item =>
        item.quality_inspection_required && item.inspection_status === 'Pending'
    );

    if (pending_items.length === 0) {
        frappe.msgprint(__('No pending inspections'));
        return;
    }

    let dialog = new frappe.ui.Dialog({
        title: __('Mobile Inspection Links'),
        fields: [{
            fieldtype: 'HTML',
            fieldname: 'links_html'
        }]
    });

    let html = '<div class="mobile-links">';

    pending_items.forEach(item => {
        let mobile_url = `/app/quality-inspection/new?purchase_receipt=${frm.doc.name}&item_code=${item.item_code}&purchase_receipt_item=${item.name}`;

        html += `
            <div class="mobile-link-item" style="margin-bottom: 15px;">
                <p><strong>${item.item_code}</strong> - ${item.item_name}</p>
                <p><em>${item.item_name_ar || ''}</em></p>
                <a href="${mobile_url}" target="_blank" class="btn btn-primary btn-sm">
                    ${__('Open Mobile Inspection')}
                </a>
            </div>
        `;
    });

    html += '</div>';

    dialog.fields_dict.links_html.$wrapper.html(html);
    dialog.show();
}

function get_status_color(status) {
    const colors = {
        'Pending': 'orange',
        'In Progress': 'blue',
        'Completed': 'green',
        'Failed': 'red',
        'Not Required': 'gray'
    };
    return colors[status] || 'gray';
} 