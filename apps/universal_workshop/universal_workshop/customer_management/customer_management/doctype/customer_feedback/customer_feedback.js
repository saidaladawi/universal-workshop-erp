// Copyright (c) 2024, Universal Workshop and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Feedback', {
    refresh: function(frm) {
        frm.trigger('setup_arabic_interface');
        frm.trigger('setup_rating_interface');
        frm.trigger('setup_custom_buttons');
        frm.trigger('setup_realtime_analytics');
    },
    
    onload: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('load_customer_history');
    },
    
    setup_arabic_interface: function(frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = [
            'feedback_title_ar', 'feedback_comments_ar', 'improvement_suggestions_ar',
            'response_comments_ar', 'keywords_extracted_ar'
        ];
        
        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css({
                    'text-align': 'right',
                    'font-family': '"Noto Sans Arabic", Tahoma, Arial, sans-serif'
                });
            }
        });
        
        // Auto-suggest Arabic translations
        frm.trigger('setup_translation_helpers');
    },
    
    setup_translation_helpers: function(frm) {
        // Add translation suggestion buttons
        if (frm.fields_dict.feedback_title_ar) {
            const $title_field = frm.fields_dict.feedback_title_ar.$wrapper;
            
            if (!$title_field.find('.arabic-suggest-btn').length) {
                const $suggest_btn = $('<button class="btn btn-xs btn-default arabic-suggest-btn" style="margin-top: 5px;">')
                    .text('اقتراح ترجمة / Suggest Translation')
                    .click(() => frm.trigger('suggest_arabic_title'));
                    
                $title_field.append($suggest_btn);
            }
        }
    },
    
    suggest_arabic_title: function(frm) {
        if (!frm.doc.feedback_title) {
            frappe.msgprint(__('Please enter English title first'));
            return;
        }
        
        if (frm.doc.feedback_title_ar) {
            frappe.confirm(
                __('Arabic title already exists. Do you want to replace it?'),
                () => frm.trigger('generate_arabic_title')
            );
        } else {
            frm.trigger('generate_arabic_title');
        }
    },
    
    generate_arabic_title: function(frm) {
        // Simple translation suggestions based on rating and content
        const title = frm.doc.feedback_title.toLowerCase();
        const rating = frm.doc.overall_rating || 3;
        
        let arabic_title = '';
        
        if (title.includes('excellent') || title.includes('great') || rating >= 4) {
            arabic_title = 'تقييم ممتاز للخدمة';
        } else if (title.includes('good') || rating >= 3) {
            arabic_title = 'تقييم جيد للخدمة';
        } else if (title.includes('poor') || title.includes('bad') || rating <= 2) {
            arabic_title = 'تقييم سلبي للخدمة';
        } else if (title.includes('complaint')) {
            arabic_title = 'شكوى من العميل';
        } else if (title.includes('suggestion')) {
            arabic_title = 'اقتراح للتحسين';
        } else {
            arabic_title = 'تقييم الخدمة';
        }
        
        frm.set_value('feedback_title_ar', arabic_title);
        frappe.show_alert({
            message: __('Arabic title suggested: {0}', [arabic_title]),
            indicator: 'green'
        });
    },
    
    setup_rating_interface: function(frm) {
        // Create interactive star rating interface
        frm.trigger('create_star_ratings');
        
        // Update rating display when values change
        const rating_fields = [
            'overall_rating', 'service_quality_rating', 'technician_rating',
            'facility_rating', 'communication_rating', 'value_rating'
        ];
        
        rating_fields.forEach(field => {
            frm.fields_dict[field] && frm.fields_dict[field].$input.on('change', () => {
                frm.trigger('update_rating_display');
            });
        });
    },
    
    create_star_ratings: function(frm) {
        // Create visual star rating widgets
        const rating_fields = [
            { field: 'overall_rating', label: 'Overall Rating | التقييم العام' },
            { field: 'service_quality_rating', label: 'Service Quality | جودة الخدمة' },
            { field: 'technician_rating', label: 'Technician | الفني' },
            { field: 'facility_rating', label: 'Facility | المرافق' },
            { field: 'communication_rating', label: 'Communication | التواصل' },
            { field: 'value_rating', label: 'Value for Money | القيمة مقابل المال' }
        ];
        
        rating_fields.forEach(item => {
            const field_wrapper = frm.fields_dict[item.field];
            if (field_wrapper && !field_wrapper.$wrapper.find('.star-rating').length) {
                frm.trigger('create_star_widget', item.field, item.label);
            }
        });
    },
    
    create_star_widget: function(frm, field_name, label) {
        const field_wrapper = frm.fields_dict[field_name];
        if (!field_wrapper) return;
        
        const current_value = frm.doc[field_name] || 0;
        
        const $star_container = $(`
            <div class="star-rating" style="margin: 10px 0;">
                <div class="star-label" style="margin-bottom: 5px; font-weight: bold; color: #555;">
                    ${label}
                </div>
                <div class="stars" style="display: flex; gap: 5px;">
                    ${[1,2,3,4,5].map(i => `
                        <span class="star" data-rating="${i}" style="
                            font-size: 24px; 
                            cursor: pointer; 
                            color: ${i <= current_value ? '#ffc107' : '#ddd'};
                            transition: color 0.2s;
                        ">★</span>
                    `).join('')}
                </div>
                <div class="rating-text" style="margin-top: 5px; font-size: 12px; color: #666;">
                    ${frm.trigger('get_rating_text', current_value)}
                </div>
            </div>
        `);
        
        // Add click handlers
        $star_container.find('.star').on('click', function() {
            const rating = parseInt($(this).data('rating'));
            frm.set_value(field_name, rating);
            
            // Update star colors
            $star_container.find('.star').each(function(index) {
                $(this).css('color', index < rating ? '#ffc107' : '#ddd');
            });
            
            // Update rating text
            $star_container.find('.rating-text').text(frm.trigger('get_rating_text', rating));
        });
        
        // Add hover effects
        $star_container.find('.star').on('mouseenter', function() {
            const rating = parseInt($(this).data('rating'));
            $star_container.find('.star').each(function(index) {
                $(this).css('color', index < rating ? '#ffc107' : '#ddd');
            });
        }).on('mouseleave', function() {
            const current_rating = frm.doc[field_name] || 0;
            $star_container.find('.star').each(function(index) {
                $(this).css('color', index < current_rating ? '#ffc107' : '#ddd');
            });
        });
        
        field_wrapper.$wrapper.append($star_container);
    },
    
    get_rating_text: function(frm, rating) {
        const rating_texts = {
            1: 'Very Poor | ضعيف جداً',
            2: 'Poor | ضعيف',
            3: 'Average | متوسط',
            4: 'Good | جيد',
            5: 'Excellent | ممتاز'
        };
        return rating_texts[rating] || 'No Rating | لا يوجد تقييم';
    },
    
    setup_custom_buttons: function(frm) {
        // Add custom action buttons based on status and permissions
        if (frm.doc.docstatus === 1) {
            // Acknowledge button
            if (frm.doc.feedback_status === 'Submitted' && frappe.user.has_role(['Workshop Manager', 'System Manager'])) {
                frm.add_custom_button(__('Acknowledge'), function() {
                    frm.trigger('acknowledge_feedback');
                }).addClass('btn-primary');
            }
            
            // Resolve button
            if (['Submitted', 'In Review', 'Acknowledged'].includes(frm.doc.feedback_status)) {
                frm.add_custom_button(__('Resolve'), function() {
                    frm.trigger('resolve_feedback');
                }).addClass('btn-success');
            }
            
            // Analytics button
            frm.add_custom_button(__('View Analytics'), function() {
                frm.trigger('show_analytics_dashboard');
            }).addClass('btn-info');
            
            // Customer History button
            if (frm.doc.customer) {
                frm.add_custom_button(__('Customer History'), function() {
                    frm.trigger('show_customer_history');
                }).addClass('btn-default');
            }
        }
        
        // Response required indicator
        if (frm.doc.response_required) {
            frm.dashboard.add_indicator(__('Response Required'), 'orange');
        }
        
        // Priority indicator
        if (frm.doc.priority_level === 'Urgent') {
            frm.dashboard.add_indicator(__('Urgent Priority'), 'red');
        }
    },
    
    acknowledge_feedback: function(frm) {
        frappe.confirm(
            __('Are you sure you want to acknowledge this feedback?'),
            () => {
                frappe.call({
                    method: 'universal_workshop.customer_portal.doctype.customer_feedback.customer_feedback.acknowledge_feedback',
                    args: {
                        feedback_id: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({
                                message: __('Feedback acknowledged successfully'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to acknowledge feedback'));
                        }
                    }
                });
            }
        );
    },
    
    resolve_feedback: function(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Resolve Feedback'),
            fields: [
                {
                    fieldtype: 'Text',
                    fieldname: 'resolution_comments',
                    label: __('Resolution Comments (English)'),
                    reqd: 1
                },
                {
                    fieldtype: 'Text',
                    fieldname: 'resolution_comments_ar',
                    label: __('تعليقات الحل (Arabic)'),
                    description: __('Arabic resolution comments for customer notification')
                }
            ],
            primary_action_label: __('Resolve'),
            primary_action: function(values) {
                frappe.call({
                    method: 'universal_workshop.customer_portal.doctype.customer_feedback.customer_feedback.resolve_feedback',
                    args: {
                        feedback_id: frm.doc.name,
                        resolution_comments: values.resolution_comments,
                        resolution_comments_ar: values.resolution_comments_ar
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({
                                message: __('Feedback resolved successfully'),
                                indicator: 'green'
                            });
                            dialog.hide();
                            frm.reload_doc();
                        } else {
                            frappe.msgprint(__('Failed to resolve feedback'));
                        }
                    }
                });
            }
        });
        
        // Set RTL for Arabic field
        dialog.show();
        dialog.fields_dict.resolution_comments_ar.$input.attr('dir', 'rtl');
    },
    
    show_analytics_dashboard: function(frm) {
        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.customer_feedback.customer_feedback.get_feedback_analytics',
            args: {
                date_range: '30'
            },
            callback: function(r) {
                if (r.message && !r.message.error) {
                    frm.trigger('display_analytics', r.message);
                } else {
                    frappe.msgprint(__('Failed to load analytics data'));
                }
            }
        });
    },
    
    display_analytics: function(frm, analytics) {
        const dialog = new frappe.ui.Dialog({
            title: __('Feedback Analytics (Last 30 Days)'),
            size: 'large'
        });
        
        const analytics_html = `
            <div class="analytics-dashboard" style="padding: 20px;">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Summary | الملخص</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Total Feedback:</strong> ${analytics.summary.total_feedback}</p>
                                <p><strong>Average Rating:</strong> ${analytics.summary.average_rating}/5</p>
                                <p><strong>Period:</strong> ${analytics.summary.date_range}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5>Rating Distribution | توزيع التقييمات</h5>
                            </div>
                            <div class="card-body">
                                ${Object.keys(analytics.rating_distribution).map(key => 
                                    `<p><strong>${key.replace('_', ' ').toUpperCase()}:</strong> ${analytics.rating_distribution[key]}</p>`
                                ).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        dialog.$body.html(analytics_html);
        dialog.show();
    },
    
    show_customer_history: function(frm) {
        frappe.call({
            method: 'universal_workshop.customer_portal.doctype.customer_feedback.customer_feedback.get_customer_feedback_summary',
            args: {
                customer: frm.doc.customer
            },
            callback: function(r) {
                if (r.message && !r.message.error) {
                    frm.trigger('display_customer_history', r.message);
                } else {
                    frappe.msgprint(__('Failed to load customer history'));
                }
            }
        });
    },
    
    display_customer_history: function(frm, history) {
        const dialog = new frappe.ui.Dialog({
            title: __('Customer Feedback History'),
            size: 'large'
        });
        
        const history_html = `
            <div class="customer-history" style="padding: 20px;">
                <div class="summary-stats" style="margin-bottom: 20px;">
                    <h4>Customer: ${frm.doc.customer}</h4>
                    <p><strong>Total Feedback:</strong> ${history.total_feedback}</p>
                    <p><strong>Average Rating:</strong> ${history.average_rating}/5</p>
                    <p><strong>Satisfaction Level:</strong> ${history.satisfaction_level}</p>
                </div>
                
                <div class="recent-feedback">
                    <h5>Recent Feedback:</h5>
                    <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Title</th>
                                <th>Rating</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${history.recent_feedback.map(feedback => `
                                <tr>
                                    <td>${feedback.feedback_date}</td>
                                    <td>${feedback.feedback_title}</td>
                                    <td>${'★'.repeat(feedback.overall_rating)}${'☆'.repeat(5-feedback.overall_rating)}</td>
                                    <td><span class="badge badge-info">${feedback.feedback_status}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        dialog.$body.html(history_html);
        dialog.show();
    },
    
    setup_realtime_analytics: function(frm) {
        // Real-time sentiment analysis and keyword extraction
        if (frm.doc.feedback_comments) {
            frm.trigger('update_sentiment_display');
        }
        
        // Auto-save draft every 30 seconds if form is dirty
        if (frm.doc.feedback_status === 'Draft') {
            setInterval(() => {
                if (frm.is_dirty() && !frm.is_new()) {
                    frm.save();
                }
            }, 30000);
        }
    },
    
    update_sentiment_display: function(frm) {
        // Show sentiment analysis results
        if (frm.doc.sentiment_analysis && frm.doc.emotion_score) {
            const sentiment_color = {
                'Very Positive': 'green',
                'Positive': 'lightgreen',
                'Neutral': 'orange',
                'Negative': 'red',
                'Very Negative': 'darkred'
            };
            
            const color = sentiment_color[frm.doc.sentiment_analysis] || 'gray';
            
            if (!frm.dashboard.find('.sentiment-indicator').length) {
                frm.dashboard.add_indicator(
                    __('Sentiment: {0} ({1}/10)', [frm.doc.sentiment_analysis, frm.doc.emotion_score]),
                    color
                );
            }
        }
    },
    
    setup_field_dependencies: function(frm) {
        // Show/hide fields based on feedback type and status
        frm.toggle_display('response_comments', frm.doc.feedback_status === 'Resolved');
        frm.toggle_display('response_comments_ar', frm.doc.feedback_status === 'Resolved');
        frm.toggle_display('acknowledged_by', frm.doc.feedback_status !== 'Draft');
        frm.toggle_display('resolved_by', frm.doc.feedback_status === 'Resolved');
        
        // Required fields based on feedback type
        if (frm.doc.feedback_type === 'Complaint') {
            frm.toggle_reqd('improvement_suggestions', true);
        }
    },
    
    load_customer_history: function(frm) {
        // Load customer information for context
        if (frm.doc.customer && frm.is_new()) {
            frappe.db.get_value('Customer', frm.doc.customer, ['customer_name', 'email_id'])
                .then(r => {
                    if (r.message) {
                        frm.set_intro(__('Customer: {0} ({1})', [r.message.customer_name, r.message.email_id]));
                    }
                });
        }
    },
    
    // Field change handlers
    overall_rating: function(frm) {
        frm.trigger('update_rating_display');
        frm.trigger('auto_suggest_feedback_type');
    },
    
    auto_suggest_feedback_type: function(frm) {
        if (!frm.doc.feedback_type && frm.doc.overall_rating) {
            let suggested_type = 'Service Review';
            
            if (frm.doc.overall_rating <= 2) {
                suggested_type = 'Complaint';
            } else if (frm.doc.overall_rating >= 4) {
                suggested_type = 'Compliment';
            }
            
            frm.set_value('feedback_type', suggested_type);
        }
    },
    
    feedback_comments: function(frm) {
        // Real-time keyword extraction preview
        if (frm.doc.feedback_comments) {
            frm.trigger('preview_keywords');
        }
    },
    
    preview_keywords: function(frm) {
        // Simple keyword extraction preview
        const text = frm.doc.feedback_comments;
        if (text && text.length > 20) {
            const words = text.toLowerCase().match(/\b\w+\b/g);
            const filtered = words.filter(word => word.length > 3);
            const unique = [...new Set(filtered)];
            const preview = unique.slice(0, 5).join(', ');
            
            if (preview) {
                frm.set_intro(__('Keywords Preview: {0}', [preview]), 'blue');
            }
        }
    },
    
    customer: function(frm) {
        frm.trigger('load_customer_history');
    },
    
    feedback_status: function(frm) {
        frm.trigger('setup_field_dependencies');
        frm.trigger('setup_custom_buttons');
    }
});

// List view customizations
frappe.listview_settings['Customer Feedback'] = {
    get_indicator: function(doc) {
        const status_colors = {
            'Draft': 'orange',
            'Submitted': 'blue',
            'In Review': 'yellow',
            'Acknowledged': 'purple',
            'Resolved': 'green',
            'Closed': 'gray'
        };
        
        return [doc.feedback_status, status_colors[doc.feedback_status] || 'gray', 'feedback_status,=,' + doc.feedback_status];
    },
    
    onload: function(listview) {
        // Add custom filters for quick access
        listview.page.add_menu_item(__('High Priority Only'), function() {
            listview.filter_area.add([[listview.doctype, 'priority_level', '=', 'High']]);
        });
        
        listview.page.add_menu_item(__('Negative Feedback'), function() {
            listview.filter_area.add([[listview.doctype, 'overall_rating', '<=', 2]]);
        });
        
        listview.page.add_menu_item(__('Pending Response'), function() {
            listview.filter_area.add([[listview.doctype, 'response_required', '=', 1]]);
        });
    }
};
