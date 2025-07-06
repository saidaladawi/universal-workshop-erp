// Copyright (c) 2025, Eng. Saeed Al-Adawi and contributors
// For license information, please see license.txt

frappe.ui.form.on('Training Module', {
    refresh: function (frm) {
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_arabic_fields');
        frm.trigger('setup_conditional_fields');
        frm.trigger('setup_content_preview');
    },

    setup_custom_buttons: function (frm) {
        // Clear existing custom buttons
        frm.clear_custom_buttons();

        // Add publish/unpublish buttons
        if (frm.doc.name && !frm.doc.__islocal) {
            if (frm.doc.is_published) {
                frm.add_custom_button(__('Unpublish'), function () {
                    frm.trigger('unpublish_module');
                }, __('Actions'));

                frm.add_custom_button(__('Preview Content'), function () {
                    frm.trigger('preview_content');
                }, __('Actions'));
            } else {
                frm.add_custom_button(__('Publish'), function () {
                    frm.trigger('publish_module');
                }, __('Actions'));
            }

            // Add content management buttons
            frm.add_custom_button(__('Upload H5P'), function () {
                frm.trigger('upload_h5p_content');
            }, __('Content'));

            frm.add_custom_button(__('Test Module'), function () {
                frm.trigger('test_module');
            }, __('Content'));
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['title_ar', 'description_ar', 'learning_objectives_ar'];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');

                // Add Arabic language attribute for proper keyboard support
                frm.fields_dict[field].$input.attr('lang', 'ar');
            }
        });

        // Apply RTL layout if Arabic is the primary language
        if (frappe.boot.lang === 'ar') {
            frm.page.main.addClass('rtl-layout');
        }
    },

    setup_conditional_fields: function (frm) {
        // Show/hide fields based on content type
        frm.trigger('toggle_content_fields');

        // Show/hide assessment fields
        frm.toggle_display(['passing_score', 'max_attempts', 'quiz_questions'], frm.doc.has_quiz);
    },

    setup_content_preview: function (frm) {
        // Add content preview section if content exists
        if (frm.doc.content_file || frm.doc.video_url || frm.doc.h5p_content_id) {
            frm.trigger('show_content_preview');
        }
    },

    content_type: function (frm) {
        frm.trigger('toggle_content_fields');
        frm.trigger('clear_irrelevant_content');
    },

    has_quiz: function (frm) {
        frm.toggle_display(['passing_score', 'max_attempts', 'quiz_questions'], frm.doc.has_quiz);

        if (frm.doc.has_quiz && !frm.doc.passing_score) {
            frm.set_value('passing_score', 80);
        }

        if (frm.doc.has_quiz && !frm.doc.max_attempts) {
            frm.set_value('max_attempts', 3);
        }
    },

    toggle_content_fields: function (frm) {
        const content_type = frm.doc.content_type;

        // Reset all content field visibility
        frm.toggle_display('h5p_content_id', false);
        frm.toggle_display('video_url', false);
        frm.toggle_reqd('content_file', false);

        // Show relevant fields based on content type
        switch (content_type) {
            case 'H5P Interactive':
                frm.toggle_display('h5p_content_id', true);
                frm.toggle_reqd('content_file', true);
                break;
            case 'Video Tutorial':
                frm.toggle_display('video_url', true);
                break;
            case 'Document/PDF':
                frm.toggle_reqd('content_file', true);
                break;
            case 'External Link':
                frm.toggle_display('video_url', true);
                frm.fields_dict['video_url'].df.label = __('External Link URL');
                frm.refresh_field('video_url');
                break;
            default:
                // Hybrid - show all fields
                frm.toggle_display('h5p_content_id', true);
                frm.toggle_display('video_url', true);
                break;
        }
    },

    clear_irrelevant_content: function (frm) {
        const content_type = frm.doc.content_type;

        // Clear fields not relevant to current content type
        if (content_type !== 'H5P Interactive' && content_type !== 'Hybrid (Multiple Types)') {
            frm.set_value('h5p_content_id', '');
        }

        if (content_type !== 'Video Tutorial' && content_type !== 'External Link' && content_type !== 'Hybrid (Multiple Types)') {
            frm.set_value('video_url', '');
        }
    },

    video_url: function (frm) {
        if (frm.doc.video_url) {
            frm.trigger('validate_video_url');
        }
    },

    validate_video_url: function (frm) {
        const url = frm.doc.video_url;
        const video_patterns = [
            /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\//i,
            /^(https?:\/\/)?(www\.)?vimeo\.com\//i,
            /^(https?:\/\/)?.*\.(mp4|avi|mov|wmv|flv|webm)$/i
        ];

        const isValid = video_patterns.some(pattern => pattern.test(url));

        if (!isValid) {
            frappe.msgprint({
                title: __('Invalid Video URL'),
                message: __('Please enter a valid YouTube, Vimeo, or direct video file URL'),
                indicator: 'orange'
            });
        }
    },

    quiz_questions: function (frm) {
        if (frm.doc.quiz_questions) {
            frm.trigger('validate_quiz_json');
        }
    },

    validate_quiz_json: function (frm) {
        try {
            const quiz_data = JSON.parse(frm.doc.quiz_questions);
            if (!Array.isArray(quiz_data) || quiz_data.length === 0) {
                frappe.msgprint({
                    title: __('Invalid Quiz Format'),
                    message: __('Quiz questions must be a non-empty JSON array'),
                    indicator: 'orange'
                });
            }
        } catch (e) {
            frappe.msgprint({
                title: __('Invalid JSON'),
                message: __('Quiz questions must be valid JSON format'),
                indicator: 'red'
            });
        }
    },

    publish_module: function (frm) {
        frappe.call({
            method: 'publish_module',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('Training module published successfully'),
                        indicator: 'green'
                    });
                }
            }
        });
    },

    unpublish_module: function (frm) {
        frappe.confirm(
            __('Are you sure you want to unpublish this training module?'),
            function () {
                frappe.call({
                    method: 'unpublish_module',
                    doc: frm.doc,
                    callback: function (r) {
                        if (r.message !== undefined) {
                            frm.reload_doc();
                            frappe.show_alert({
                                message: __('Training module unpublished'),
                                indicator: 'blue'
                            });
                        }
                    }
                });
            }
        );
    },

    preview_content: function (frm) {
        if (!frm.doc.is_published) {
            frappe.msgprint(__('Module must be published to preview content'));
            return;
        }

        // Open training module in new window/tab for preview
        const preview_url = `/app/training-player/${frm.doc.name}`;
        window.open(preview_url, '_blank');
    },

    upload_h5p_content: function (frm) {
        // Create file upload dialog for H5P content
        new frappe.ui.FileUploader({
            doctype: frm.doc.doctype,
            docname: frm.doc.name,
            fieldname: 'content_file',
            method: 'upload_file',
            allowed_file_types: ['.h5p'],
            max_file_size: 50 * 1024 * 1024, // 50MB
            callback: function (attachment) {
                frm.set_value('content_file', attachment.file_url);

                // Auto-generate H5P content ID if not set
                if (!frm.doc.h5p_content_id) {
                    const content_id = 'h5p_' + Date.now();
                    frm.set_value('h5p_content_id', content_id);
                }

                frappe.show_alert({
                    message: __('H5P content uploaded successfully'),
                    indicator: 'green'
                });
            }
        });
    },

    test_module: function (frm) {
        if (!frm.doc.name || frm.doc.__islocal) {
            frappe.msgprint(__('Please save the module first'));
            return;
        }

        // Open test interface
        frappe.call({
            method: 'universal_workshop.training_management.doctype.training_module.training_module.get_module_content',
            args: {
                module_name: frm.doc.name
            },
            callback: function (r) {
                if (r.message) {
                    frm.trigger('show_test_dialog', r.message);
                }
            }
        });
    },

    show_test_dialog: function (frm, content_data) {
        const d = new frappe.ui.Dialog({
            title: __('Test Training Module'),
            size: 'large',
            fields: [
                {
                    fieldname: 'content_preview',
                    fieldtype: 'HTML',
                    options: frm.trigger('generate_content_preview_html', content_data)
                }
            ],
            primary_action_label: __('Close'),
            primary_action: function () {
                d.hide();
            }
        });

        d.show();
    },

    generate_content_preview_html: function (frm, content_data) {
        let html = `<div class="training-content-preview">`;

        if (content_data.content_type === 'Video Tutorial' && content_data.content_url) {
            html += `<video controls width="100%" style="max-height: 400px;">
                        <source src="${content_data.content_url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>`;
        } else if (content_data.content_type === 'H5P Interactive') {
            html += `<div class="h5p-placeholder">
                        <p><strong>H5P Content Preview</strong></p>
                        <p>Content ID: ${content_data.h5p_content?.content_id || 'Not set'}</p>
                        <p><em>H5P content would be rendered here in the actual training player</em></p>
                    </div>`;
        } else if (content_data.content_url) {
            html += `<iframe src="${content_data.content_url}" width="100%" height="400px" frameborder="0"></iframe>`;
        }

        // Show quiz preview if available
        if (content_data.quiz_data && content_data.quiz_data.length > 0) {
            html += `<div class="quiz-preview" style="margin-top: 20px;">
                        <h4>Quiz Preview</h4>
                        <p><strong>Number of Questions:</strong> ${content_data.quiz_data.length}</p>
                        <p><strong>Sample Question:</strong> ${content_data.quiz_data[0].question || 'N/A'}</p>
                    </div>`;
        }

        html += `</div>`;
        return html;
    },

    show_content_preview: function (frm) {
        // Add content preview to form if not already present
        if (!frm.fields_dict.content_preview_html) {
            // This would be implemented with a custom field in the DocType
            // For now, we'll show preview in dialogs only
        }
    }
});

// Auto-suggest module code on title change
frappe.ui.form.on('Training Module', 'title', function (frm) {
    if (!frm.doc.module_code && frm.doc.title) {
        // Generate suggested module code from title
        const title_clean = frm.doc.title.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
        const suggested_code = `TM-${title_clean.substring(0, 3)}${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`;

        frappe.show_alert({
            message: __(`Suggested module code: ${suggested_code}`),
            indicator: 'blue'
        });
    }
});

// Arabic text validation helpers
function validate_arabic_input(text) {
    const arabic_pattern = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
    return arabic_pattern.test(text);
}

// Real-time Arabic content validation
frappe.ui.form.on('Training Module', 'title_ar', function (frm) {
    if (frm.doc.title_ar && !validate_arabic_input(frm.doc.title_ar)) {
        frappe.show_alert({
            message: __('Warning: Arabic title appears to contain no Arabic characters'),
            indicator: 'orange'
        });
    }
});

frappe.ui.form.on('Training Module', 'description_ar', function (frm) {
    if (frm.doc.description_ar && !validate_arabic_input(frm.doc.description_ar)) {
        frappe.show_alert({
            message: __('Warning: Arabic description appears to contain no Arabic characters'),
            indicator: 'orange'
        });
    }
}); 