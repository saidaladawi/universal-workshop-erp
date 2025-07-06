// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Document Storage', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_file_handlers');
        frm.trigger('setup_preview');
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        ['document_title_ar', 'description_ar', 'keywords_ar', 'rejection_reason_ar'].forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
        
        // Apply Arabic styling if current language is Arabic
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },
    
    setup_custom_buttons: function(frm) {
        if (frm.doc.name && !frm.doc.__islocal) {
            // Download button
            if (frm.doc.status === 'Approved' || frm.doc.access_permissions !== 'Restricted') {
                frm.add_custom_button(__('Download'), function() {
                    frm.trigger('download_document');
                });
            }
            
            // Preview button
            if (frm.doc.document_preview) {
                frm.add_custom_button(__('Preview'), function() {
                    frm.trigger('show_preview');
                });
            }
            
            // Approval buttons for managers
            if (frappe.user.has_role('Workshop Manager') || frappe.user.has_role('System Manager')) {
                if (frm.doc.status === 'Pending Approval') {
                    frm.add_custom_button(__('Approve'), function() {
                        frm.trigger('approve_document');
                    }, __('Actions'));
                    
                    frm.add_custom_button(__('Reject'), function() {
                        frm.trigger('reject_document');
                    }, __('Actions'));
                }
            }
            
            // Document stats button
            frm.add_custom_button(__('View Stats'), function() {
                frm.trigger('show_document_stats');
            }, __('Reports'));
        }
    },
    
    setup_file_handlers: function(frm) {
        // Handle file attachment change
        frm.fields_dict.file_attachment.$input.on('change', function() {
            setTimeout(() => {
                frm.trigger('process_file_upload');
            }, 1000);
        });
    },
    
    setup_preview: function(frm) {
        if (frm.doc.document_preview && frm.doc.thumbnail_url) {
            frm.set_df_property('document_preview', 'description', 
                `<img src="${frm.doc.thumbnail_url}" style="max-width: 200px; max-height: 150px;" />`);
        }
    },
    
    document_title: function(frm) {
        // Auto-suggest Arabic translation
        if (frm.doc.document_title && !frm.doc.document_title_ar) {
            frm.trigger('suggest_arabic_translation');
        }
    },
    
    suggest_arabic_translation: function(frm) {
        const translations = {
            'Invoice': 'فاتورة',
            'Service Report': 'تقرير الخدمة',
            'Warranty Document': 'وثيقة الضمان',
            'Receipt': 'إيصال',
            'Quotation': 'عرض أسعار',
            'Contract': 'عقد',
            'Photo': 'صورة',
            'Video': 'فيديو'
        };
        
        const arabic_title = translations[frm.doc.document_title];
        if (arabic_title) {
            frm.set_value('document_title_ar', arabic_title);
        } else {
            frm.set_value('document_title_ar', `ترجمة: ${frm.doc.document_title}`);
        }
    },
    
    process_file_upload: function(frm) {
        if (frm.doc.file_attachment) {
            // Show processing message
            frappe.show_alert({
                message: __('Processing file upload...'),
                indicator: 'blue'
            });
            
            // Auto-detect document properties
            const filename = frm.doc.file_attachment.split('/').pop();
            const extension = filename.split('.').pop().toLowerCase();
            
            // Set document type based on file extension
            if (['pdf', 'doc', 'docx'].includes(extension)) {
                if (!frm.doc.document_type) {
                    if (filename.toLowerCase().includes('invoice') || filename.toLowerCase().includes('فاتورة')) {
                        frm.set_value('document_type', 'Invoice');
                    } else if (filename.toLowerCase().includes('contract') || filename.toLowerCase().includes('عقد')) {
                        frm.set_value('document_type', 'Contract');
                    } else {
                        frm.set_value('document_type', 'Other');
                    }
                }
            } else if (['jpg', 'jpeg', 'png', 'gif'].includes(extension)) {
                frm.set_value('document_type', 'Photo');
            } else if (['mp4', 'avi', 'mov'].includes(extension)) {
                frm.set_value('document_type', 'Video');
            }
            
            // Set Arabic content flag if filename contains Arabic
            if (/[\u0600-\u06FF]/.test(filename)) {
                frm.set_value('arabic_content', 1);
                frm.set_value('rtl_support', 1);
            }
        }
    },
    
    download_document: function(frm) {
        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.customer_document_storage.customer_document_storage.download_document',
            args: {
                doc_id: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.file_url) {
                    window.open(r.message.file_url, '_blank');
                    frappe.show_alert({
                        message: __('Document downloaded successfully'),
                        indicator: 'green'
                    });
                    frm.reload_doc();
                }
            },
            error: function(xhr) {
                frappe.msgprint(__('Failed to download document'));
            }
        });
    },
    
    show_preview: function(frm) {
        if (frm.doc.document_preview) {
            frappe.call({
                method: 'universal_workshop.customer_portal.doctype.customer_document_storage.customer_document_storage.get_document_preview',
                args: {
                    doc_id: frm.doc.name
                },
                callback: function(r) {
                    if (r.message && r.message.thumbnail_url) {
                        const d = new frappe.ui.Dialog({
                            title: __('Document Preview'),
                            fields: [
                                {
                                    fieldtype: 'HTML',
                                    fieldname: 'preview_html',
                                    options: `
                                        <div class="text-center">
                                            <img src="${r.message.thumbnail_url}" 
                                                 style="max-width: 100%; max-height: 500px;" />
                                            <p class="text-muted">${frm.doc.document_title}</p>
                                        </div>
                                    `
                                }
                            ],
                            primary_action_label: __('Download Full Document'),
                            primary_action: function() {
                                frm.trigger('download_document');
                                d.hide();
                            }
                        });
                        d.show();
                    }
                }
            });
        }
    },
    
    approve_document: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Approve Document'),
            fields: [
                {
                    fieldtype: 'Small Text',
                    fieldname: 'approval_reason',
                    label: __('Approval Reason'),
                    reqd: 0
                }
            ],
            primary_action_label: __('Approve'),
            primary_action: function() {
                const values = d.get_values();
                frappe.call({
                    method: 'universal_workshop.customer_portal.doctype.customer_document_storage.customer_document_storage.approve_document',
                    args: {
                        doc_id: frm.doc.name,
                        approval_reason: values.approval_reason || ''
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
                d.hide();
            }
        });
        d.show();
    },
    
    reject_document: function(frm) {
        const d = new frappe.ui.Dialog({
            title: __('Reject Document'),
            fields: [
                {
                    fieldtype: 'Small Text',
                    fieldname: 'rejection_reason',
                    label: __('Rejection Reason (English)'),
                    reqd: 1
                },
                {
                    fieldtype: 'Small Text',
                    fieldname: 'rejection_reason_ar',
                    label: __('سبب الرفض (العربية)'),
                    reqd: 0
                }
            ],
            primary_action_label: __('Reject'),
            primary_action: function() {
                const values = d.get_values();
                if (!values.rejection_reason) {
                    frappe.msgprint(__('Rejection reason is required'));
                    return;
                }
                
                frappe.call({
                    method: 'universal_workshop.customer_portal.doctype.customer_document_storage.customer_document_storage.reject_document',
                    args: {
                        doc_id: frm.doc.name,
                        rejection_reason: values.rejection_reason,
                        rejection_reason_ar: values.rejection_reason_ar || ''
                    },
                    callback: function(r) {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message,
                                indicator: 'orange'
                            });
                            frm.reload_doc();
                        }
                    }
                });
                d.hide();
            }
        });
        
        // Set RTL for Arabic field
        d.fields_dict.rejection_reason_ar.$input.attr('dir', 'rtl');
        d.show();
    },
    
    show_document_stats: function(frm) {
        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.customer_document_storage.customer_document_storage.get_document_stats',
            args: {
                customer: frm.doc.customer
            },
            callback: function(r) {
                if (r.message) {
                    const stats = r.message;
                    const d = new frappe.ui.Dialog({
                        title: __('Document Statistics'),
                        fields: [
                            {
                                fieldtype: 'HTML',
                                fieldname: 'stats_html',
                                options: `
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="card">
                                                <div class="card-body text-center">
                                                    <h3 class="text-primary">${stats.total_documents}</h3>
                                                    <p>${__('Total Documents')}</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card">
                                                <div class="card-body text-center">
                                                    <h3 class="text-success">${stats.approved_documents}</h3>
                                                    <p>${__('Approved')}</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card">
                                                <div class="card-body text-center">
                                                    <h3 class="text-warning">${stats.pending_approval}</h3>
                                                    <p>${__('Pending Approval')}</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="card">
                                                <div class="card-body text-center">
                                                    <h3 class="text-info">${stats.total_downloads}</h3>
                                                    <p>${__('Total Downloads')}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `
                            }
                        ]
                    });
                    d.show();
                }
            }
        });
    }
});

// Document type specific logic
frappe.ui.form.on('Customer Document Storage', 'document_type', function(frm) {
    // Set default access permissions based on document type
    if (frm.doc.document_type) {
        const restrictedTypes = ['Contract', 'Legal Document', 'Financial'];
        if (restrictedTypes.includes(frm.doc.document_type)) {
            frm.set_value('access_permissions', 'Restricted');
            frm.set_value('approval_required', 1);
            frm.set_value('is_private', 1);
        }
    }
});

// Customer change handler
frappe.ui.form.on('Customer Document Storage', 'customer', function(frm) {
    if (frm.doc.customer) {
        // Fetch customer name
        frappe.db.get_value('Customer', frm.doc.customer, 'customer_name')
            .then(r => {
                if (r.message) {
                    frm.set_value('customer_name', r.message.customer_name);
                }
            });
    }
});
