/**
 * Universal Workshop Profile Form Script
 */

frappe.ui.form.on('Workshop Profile', {
    refresh: function (frm) {
        frm.trigger('setup_theme_selector');
        frm.trigger('setup_arabic_fields');
    },

    setup_theme_selector: function (frm) {
        // Add theme selector after the theme_preference field
        if (frm.fields_dict.theme_preference && !frm.theme_selector) {
            const theme_wrapper = $('<div class="theme-selector-wrapper"></div>').insertAfter(
                frm.fields_dict.theme_preference.wrapper
            );

            // Initialize theme selector component
            frm.theme_selector = new universal_workshop.components.ThemeSelector(theme_wrapper, {
                current_theme: frm.doc.theme_preference || 'classic',
                field_name: 'theme_preference',
                frm: frm,
                show_preview: true,
                allow_custom: true
            });
        }
    },

    setup_arabic_fields: function (frm) {
        // Set RTL direction for Arabic fields
        const arabic_fields = ['workshop_name_ar', 'address_ar', 'description_ar'];

        arabic_fields.forEach(field => {
            if (frm.fields_dict[field]) {
                frm.fields_dict[field].$input.attr('dir', 'rtl');
                frm.fields_dict[field].$input.css('text-align', 'right');
            }
        });
    },

    theme_preference: function (frm) {
        if (frm.doc.theme_preference && frm.theme_selector) {
            frm.theme_selector.set_theme(frm.doc.theme_preference);
        }
    }
});
