// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Knowledge Base Article', {
    refresh: function (frm) {
        // Setup Arabic RTL support
        frm.trigger('setup_arabic_fields');

        // Setup custom buttons
        frm.trigger('setup_custom_buttons');

        // Setup field visibility
        frm.trigger('setup_field_visibility');

        // Setup status-based actions
        frm.trigger('setup_status_actions');
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'title_ar', 'content_ar', 'excerpt_ar',
            'meta_title_ar', 'meta_description_ar', 'search_keywords_ar'
        ];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': 'Tahoma, "Arial Unicode MS", sans-serif'
                });
            }
        });

        // Handle text editor fields
        ['content_ar'].forEach(field => {
            if (frm.fields_dict[field] && frm.fields_dict[field].editor) {
                // Set RTL for Frappe editor
                setTimeout(() => {
                    let editor_element = frm.fields_dict[field].$wrapper.find('.ql-editor');
                    if (editor_element.length) {
                        editor_element.attr('dir', 'rtl').css('text-align', 'right');
                    }
                }, 1000);
            }
        });
    },

    setup_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();

        if (!frm.doc.__islocal) {
            // Preview button
            frm.add_custom_button(__('Preview'), function () {
                frm.trigger('preview_article');
            }, __('Actions'));

            // Publish/Unpublish button
            if (frm.doc.status === 'Approved') {
                frm.add_custom_button(__('Publish'), function () {
                    frm.trigger('publish_article');
                }, __('Actions'));
            } else if (frm.doc.status === 'Published') {
                frm.add_custom_button(__('Unpublish'), function () {
                    frm.trigger('unpublish_article');
                }, __('Actions'));
            }

            // Translation buttons
            if (frm.doc.translation_status !== 'Complete') {
                frm.add_custom_button(__('Request Translation'), function () {
                    frm.trigger('request_translation');
                }, __('Translation'));
            }

            // View analytics
            if (frm.doc.status === 'Published') {
                frm.add_custom_button(__('View Analytics'), function () {
                    frm.trigger('view_analytics');
                }, __('Analytics'));
            }

            // Duplicate article
            frm.add_custom_button(__('Duplicate'), function () {
                frm.trigger('duplicate_article');
            }, __('Actions'));
        }
    },

    setup_field_visibility: function (frm) {
        // Hide/show fields based on status
        const is_published = frm.doc.status === 'Published';
        const is_public = frm.doc.is_public;

        // Show analytics fields only for published articles
        frm.toggle_display(['view_count', 'feedback_rating', 'helpfulness_score'], is_published);

        // Show SEO fields only for public articles
        frm.toggle_display(['meta_title_en', 'meta_title_ar', 'meta_description_en', 'meta_description_ar'], is_public);

        // Show workflow fields based on status
        const show_workflow = ['In Review (EN)', 'In Review (AR)', 'Approved'].includes(frm.doc.status);
        frm.toggle_display(['approval_notes', 'reviewer'], show_workflow);
    },

    setup_status_actions: function (frm) {
        // Status-specific validations and actions
        if (frm.doc.status === 'Published' && !frm.doc.published_date) {
            frm.set_value('published_date', frappe.datetime.now_datetime());
        }
    },

    // Field change handlers
    title_en: function (frm) {
        // Auto-generate article code if needed
        if (!frm.doc.article_code && frm.doc.title_en) {
            frm.trigger('generate_article_code');
        }

        // Auto-fill meta title
        if (frm.doc.title_en && !frm.doc.meta_title_en) {
            frm.set_value('meta_title_en', frm.doc.title_en);
        }
    },

    title_ar: function (frm) {
        // Validate Arabic text
        if (frm.doc.title_ar && !frm.trigger('is_arabic_text', frm.doc.title_ar)) {
            frappe.msgprint({
                title: __('Warning'),
                message: __('Arabic title appears to contain no Arabic characters'),
                indicator: 'orange'
            });
        }

        // Auto-fill Arabic meta title
        if (frm.doc.title_ar && !frm.doc.meta_title_ar) {
            frm.set_value('meta_title_ar', frm.doc.title_ar);
        }
    },

    content_en: function (frm) {
        // Auto-generate excerpt if not provided
        if (frm.doc.content_en && !frm.doc.excerpt_en) {
            frm.trigger('generate_excerpt', 'en');
        }

        // Update translation status
        frm.trigger('update_translation_status');
    },

    content_ar: function (frm) {
        // Validate Arabic content
        if (frm.doc.content_ar && !frm.trigger('is_arabic_text', frm.doc.content_ar)) {
            frappe.msgprint({
                title: __('Warning'),
                message: __('Arabic content appears to contain no Arabic characters'),
                indicator: 'orange'
            });
        }

        // Auto-generate Arabic excerpt
        if (frm.doc.content_ar && !frm.doc.excerpt_ar) {
            frm.trigger('generate_excerpt', 'ar');
        }

        // Update translation status
        frm.trigger('update_translation_status');
    },

    status: function (frm) {
        frm.trigger('setup_field_visibility');
        frm.trigger('setup_custom_buttons');
    },

    is_public: function (frm) {
        frm.trigger('setup_field_visibility');
    },

    review_frequency: function (frm) {
        if (frm.doc.review_frequency && frm.doc.review_frequency !== 'As Needed') {
            frm.trigger('calculate_next_review_date');
        }
    },

    // Helper methods
    is_arabic_text: function (frm, text) {
        if (!text) return false;
        const arabic_pattern = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+/;
        return arabic_pattern.test(text);
    },

    generate_excerpt: function (frm, language) {
        const content = language === 'ar' ? frm.doc.content_ar : frm.doc.content_en;
        if (!content) return;

        // Remove HTML tags and generate excerpt
        const clean_text = content.replace(/<[^>]*>/g, '');
        let excerpt = clean_text.substring(0, 150).trim();

        if (clean_text.length > 150) {
            const last_space = excerpt.lastIndexOf(' ');
            if (last_space > 100) {
                excerpt = excerpt.substring(0, last_space);
            }
            excerpt += '...';
        }

        if (language === 'ar') {
            frm.set_value('excerpt_ar', excerpt);
        } else {
            frm.set_value('excerpt_en', excerpt);
        }
    },

    update_translation_status: function (frm) {
        const has_english = !!(frm.doc.content_en && frm.doc.title_en);
        const has_arabic = !!(frm.doc.content_ar && frm.doc.title_ar);

        let status;
        if (has_english && has_arabic) {
            status = 'Complete';
        } else if (has_english || has_arabic) {
            status = 'Partial';
        } else {
            status = 'Missing';
        }

        if (frm.doc.translation_status !== status) {
            frm.set_value('translation_status', status);
        }
    },

    calculate_next_review_date: function (frm) {
        if (!frm.doc.review_frequency || frm.doc.review_frequency === 'As Needed') {
            return;
        }

        const frequency_days = {
            'Monthly': 30,
            'Quarterly': 90,
            'Bi-annually': 180,
            'Annually': 365
        };

        const days = frequency_days[frm.doc.review_frequency];
        if (days) {
            const base_date = frm.doc.last_reviewed_date || frappe.datetime.today();
            const next_date = frappe.datetime.add_days(base_date, days);
            frm.set_value('next_review_date', next_date);
        }
    },

    // Custom button actions
    preview_article: function (frm) {
        if (frm.doc.has_web_view) {
            const route = `/knowledge-base/${frm.doc.name}`;
            window.open(route, '_blank');
        } else {
            frappe.msgprint(__('Article preview not available'));
        }
    },

    publish_article: function (frm) {
        if (frm.doc.translation_status === 'Missing') {
            frappe.msgprint(__('Cannot publish article without content'));
            return;
        }

        frappe.call({
            method: 'publish_article',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                }
            }
        });
    },

    unpublish_article: function (frm) {
        frappe.call({
            method: 'unpublish_article',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                }
            }
        });
    },

    request_translation: function (frm) {
        const missing_lang = frm.doc.content_en ? 'Arabic' : 'English';

        frappe.prompt([
            {
                fieldname: 'translator',
                fieldtype: 'Link',
                options: 'User',
                label: __('Assign Translator'),
                reqd: 1
            },
            {
                fieldname: 'notes',
                fieldtype: 'Small Text',
                label: __('Translation Notes')
            }
        ], function (values) {
            frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: {
                        doctype: 'Translation Request',
                        article: frm.doc.name,
                        target_language: missing_lang,
                        translator: values.translator,
                        notes: values.notes,
                        status: 'Pending'
                    }
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.msgprint(__('Translation request created successfully'));
                        frm.reload_doc();
                    }
                }
            });
        }, __('Request Translation'), __('Create Request'));
    },

    view_analytics: function (frm) {
        frappe.route_options = {
            'article': frm.doc.name
        };
        frappe.set_route('query-report', 'Knowledge Base Analytics');
    },

    duplicate_article: function (frm) {
        frappe.model.open_mapped_doc({
            method: 'universal_workshop.training_management.doctype.knowledge_base_article.knowledge_base_article.duplicate_article',
            frm: frm
        });
    }
});

// Auto-save draft functionality
let auto_save_timeout;
frappe.ui.form.on('Knowledge Base Article', {
    content_en: function (frm) {
        frm.trigger('setup_auto_save');
    },
    content_ar: function (frm) {
        frm.trigger('setup_auto_save');
    },

    setup_auto_save: function (frm) {
        if (frm.doc.status === 'Draft' && !frm.doc.__islocal) {
            clearTimeout(auto_save_timeout);
            auto_save_timeout = setTimeout(() => {
                if (frm.dirty) {
                    frm.save();
                }
            }, 30000); // Auto-save after 30 seconds of inactivity
        }
    }
});

// Global search integration
frappe.ready(function () {
    // Add to global search
    if (frappe.search) {
        frappe.search.add_source({
            doctype: 'Knowledge Base Article',
            title: __('Knowledge Base'),
            search_field: 'title_en',
            filters: {
                'status': 'Published'
            }
        });
    }
}); 