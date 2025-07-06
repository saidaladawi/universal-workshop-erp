// -*- coding: utf-8 -*-

frappe.ui.form.on('Knowledge Base Category', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_hierarchy_display');
    },
    
    setup_arabic_fields: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['category_name_ar', 'description_ar'];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
                frm.fields_dict[field].$input.addClass('arabic-text');
            }
        });
    },
    
    setup_custom_buttons: function(frm) {
        if (!frm.doc.__islocal) {
            // Add custom buttons for category management
            frm.add_custom_button(__('View Articles'), function() {
                frappe.route_options = {
                    "category": frm.doc.name
                };
                frappe.set_route("List", "Knowledge Base Article");
            }, __("Actions"));
            
            frm.add_custom_button(__('Add Child Category'), function() {
                frappe.new_doc('Knowledge Base Category', {
                    parent_category: frm.doc.name
                });
            }, __("Actions"));
            
            if (frm.doc.status === 'Active') {
                frm.add_custom_button(__('Archive Category'), function() {
                    frm.set_value('status', 'Archived');
                    frm.save();
                }, __("Actions"));
            }
        }
    },
    
    setup_hierarchy_display: function(frm) {
        if (frm.doc.parent_category) {
            // Show hierarchy breadcrumb
            frappe.call({
                method: 'universal_workshop.training_management.doctype.knowledge_base_category.knowledge_base_category.get_category_tree',
                args: {
                    language: frappe.boot.lang || 'en'
                },
                callback: function(r) {
                    if (r.message) {
                        frm.trigger('display_hierarchy_path');
                    }
                }
            });
        }
    },
    
    category_name_en: function(frm) {
        // Auto-generate category code when English name changes
        if (frm.doc.category_name_en && !frm.doc.category_code) {
            frm.trigger('generate_category_code');
        }
        
        // Suggest Arabic name if not provided
        if (frm.doc.category_name_en && !frm.doc.category_name_ar) {
            frm.trigger('suggest_arabic_name');
        }
    },
    
    category_name_ar: function(frm) {
        // Validate Arabic text
        if (frm.doc.category_name_ar) {
            const is_arabic = /[\u0600-\u06FF]/.test(frm.doc.category_name_ar);
            if (!is_arabic) {
                frappe.msgprint({
                    title: __('Arabic Text Validation'),
                    indicator: 'orange',
                    message: __('Arabic category name should contain Arabic characters')
                });
            }
        }
    },
    
    parent_category: function(frm) {
        // Validate hierarchy and update sort order
        if (frm.doc.parent_category) {
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Knowledge Base Category',
                    name: frm.doc.parent_category
                },
                callback: function(r) {
                    if (r.message) {
                        // Set default sort order based on siblings
                        frm.trigger('set_default_sort_order');
                    }
                }
            });
        }
    },
    
    generate_category_code: function(frm) {
        if (frm.doc.category_name_en) {
            let code = frm.doc.category_name_en
                .replace(/[^a-zA-Z0-9\s]/g, '')
                .replace(/\s+/g, '_')
                .toUpperCase();
            
            frm.set_value('category_code', code);
        }
    },
    
    suggest_arabic_name: function(frm) {
        // Placeholder for Arabic name suggestion
        // In a real implementation, this could call a translation service
        frappe.msgprint({
            title: __('Arabic Name Needed'),
            message: __('Please provide the Arabic translation for the category name'),
            indicator: 'blue'
        });
    },
    
    set_default_sort_order: function(frm) {
        if (!frm.doc.sort_order) {
            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Knowledge Base Category',
                    filters: {
                        parent_category: frm.doc.parent_category || ['is', 'null']
                    },
                    fields: ['sort_order'],
                    order_by: 'sort_order desc',
                    limit: 1
                },
                callback: function(r) {
                    if (r.message && r.message.length > 0) {
                        frm.set_value('sort_order', (r.message[0].sort_order || 0) + 10);
                    } else {
                        frm.set_value('sort_order', 10);
                    }
                }
            });
        }
    },
    
    display_hierarchy_path: function(frm) {
        // Display category hierarchy path
        if (frm.doc.parent_category) {
            const hierarchy_html = `
                <div class="hierarchy-path" style="margin: 10px 0; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                    <small><i class="fa fa-sitemap"></i> <strong>${__('Category Path')}:</strong></small>
                    <div class="hierarchy-breadcrumb" style="margin-top: 5px;">
                        <!-- Path will be populated here -->
                    </div>
                </div>
            `;
            
            frm.fields_dict.category_name_en.$wrapper.before(hierarchy_html);
        }
    }
});

// Global utilities for Knowledge Base Category
frappe.knowledge_base = {
    
    // Format category display name based on language
    format_category_name: function(category, language) {
        if (!category) return '';
        
        if (language === 'ar' && category.category_name_ar) {
            return category.category_name_ar;
        }
        return category.category_name_en || category.category_name_ar || category.name;
    },
    
    // Get category icon with fallback
    get_category_icon: function(category) {
        return category.icon_class || 'fa fa-folder-o';
    },
    
    // Build category hierarchy breadcrumb
    build_breadcrumb: function(categories, language) {
        if (!categories || !categories.length) return '';
        
        return categories.map(cat => {
            const name = frappe.knowledge_base.format_category_name(cat, language);
            return `<span class="breadcrumb-item">${name}</span>`;
        }).join(' <i class="fa fa-chevron-right"></i> ');
    }
};

// Custom CSS for Arabic support
if (frappe.boot.lang === 'ar') {
    $('head').append(`
        <style>
        .arabic-text {
            font-family: 'Noto Sans Arabic', 'Tahoma', 'Arial Unicode MS', sans-serif;
            direction: rtl;
            text-align: right;
        }
        
        .hierarchy-breadcrumb {
            direction: ltr;
        }
        
        .rtl-layout .form-control {
            text-align: right;
        }
        </style>
    `);
}
