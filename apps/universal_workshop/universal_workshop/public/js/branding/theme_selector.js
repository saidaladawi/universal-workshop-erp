/**
 * Universal Workshop Theme Selector Component
 * Provides theme selection interface for Workshop Profile
 */

frappe.provide('universal_workshop.components');

universal_workshop.components.ThemeSelector = class ThemeSelector {
    constructor(parent, options = {}) {
        this.parent = parent;
        this.options = {
            show_preview: true,
            allow_custom: true,
            current_theme: 'classic',
            ...options
        };

        this.themes = {};
        this.current_selection = this.options.current_theme;

        this.init();
    }

    async init() {
        await this.load_themes();
        this.render();
        this.setup_events();
    }

    async load_themes() {
        try {
            // Load default themes from theme manager
            if (window.workshop_theme_manager) {
                this.themes = window.workshop_theme_manager.get_all_themes();
            } else {
                // Fallback to basic themes
                this.themes = {
                    'classic': {
                        name: 'Classic Blue',
                        name_ar: 'الأزرق الكلاسيكي',
                        colors: { primary: '#1f4e79', secondary: '#e8f4fd' }
                    },
                    'automotive': {
                        name: 'Automotive Green',
                        name_ar: 'الأخضر السيارات',
                        colors: { primary: '#2c5f41', secondary: '#e8f5e8' }
                    },
                    'luxury': {
                        name: 'Luxury Gold',
                        name_ar: 'الذهبي الفاخر',
                        colors: { primary: '#b8860b', secondary: '#fffef7' }
                    }
                };
            }

            // Load custom themes if allowed
            if (this.options.allow_custom) {
                await this.load_custom_themes();
            }

        } catch (error) {
            console.error('Error loading themes:', error);
        }
    }

    async load_custom_themes() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.themes.api.get_custom_themes'
            });

            if (response.message) {
                Object.assign(this.themes, response.message);
            }
        } catch (error) {
            console.warn('Could not load custom themes:', error);
        }
    }

    render() {
        const lang = frappe.boot.lang || 'en';

        this.wrapper = $(`
            <div class="theme-selector-container">
                <div class="theme-selector-header">
                    <h5>${__('Select Theme')}</h5>
                    <p class="text-muted">${__('Choose a visual theme for your workshop')}</p>
                </div>
                <div class="theme-options-grid">
                    ${this.render_theme_options()}
                </div>
                ${this.options.allow_custom ? this.render_custom_options() : ''}
            </div>
        `).appendTo(this.parent);
    }

    render_theme_options() {
        const lang = frappe.boot.lang || 'en';

        return Object.entries(this.themes).map(([key, theme]) => {
            const isSelected = key === this.current_selection;
            const themeName = lang === 'ar' && theme.name_ar ? theme.name_ar : theme.name;

            return `
                <div class="theme-option ${isSelected ? 'selected' : ''}" data-theme="${key}">
                    <div class="theme-preview">
                        ${this.render_color_preview(theme.colors)}
                    </div>
                    <div class="theme-info">
                        <h6>${themeName}</h6>
                        <small class="text-muted">${theme.description || ''}</small>
                    </div>
                    ${isSelected ? '<div class="selected-indicator"><i class="fa fa-check"></i></div>' : ''}
                </div>
            `;
        }).join('');
    }

    render_color_preview(colors) {
        if (!colors) return '<div class="color-preview-placeholder"></div>';

        const primaryColor = colors.primary || '#1f4e79';
        const secondaryColor = colors.secondary || '#e8f4fd';
        const accentColor = colors.accent || primaryColor;

        return `
            <div class="color-preview">
                <div class="color-bar" style="background: linear-gradient(135deg, ${primaryColor} 0%, ${secondaryColor} 50%, ${accentColor} 100%)"></div>
                <div class="color-dots">
                    <span class="color-dot" style="background-color: ${primaryColor}"></span>
                    <span class="color-dot" style="background-color: ${secondaryColor}"></span>
                    <span class="color-dot" style="background-color: ${accentColor}"></span>
                </div>
            </div>
        `;
    }

    render_custom_options() {
        return `
            <div class="custom-theme-actions">
                <button class="btn btn-sm btn-default create-custom-theme">
                    <i class="fa fa-plus"></i> ${__('Create Custom Theme')}
                </button>
                <button class="btn btn-sm btn-default import-theme">
                    <i class="fa fa-upload"></i> ${__('Import Theme')}
                </button>
            </div>
        `;
    }

    setup_events() {
        // Theme selection
        this.wrapper.on('click', '.theme-option', (e) => {
            const themeKey = $(e.currentTarget).data('theme');
            this.select_theme(themeKey);
        });

        // Custom theme creation
        this.wrapper.on('click', '.create-custom-theme', () => {
            this.show_custom_theme_dialog();
        });

        // Theme import
        this.wrapper.on('click', '.import-theme', () => {
            this.show_import_dialog();
        });

        // Preview on hover
        if (this.options.show_preview) {
            this.wrapper.on('mouseenter', '.theme-option', (e) => {
                const themeKey = $(e.currentTarget).data('theme');
                this.preview_theme(themeKey);
            });

            this.wrapper.on('mouseleave', '.theme-option', () => {
                this.preview_theme(this.current_selection);
            });
        }
    }

    select_theme(theme_key) {
        if (!this.themes[theme_key]) return;

        // Update UI
        this.wrapper.find('.theme-option').removeClass('selected');
        this.wrapper.find(`.theme-option[data-theme="${theme_key}"]`).addClass('selected');

        // Update selection
        this.current_selection = theme_key;

        // Apply theme if theme manager is available
        if (window.workshop_theme_manager) {
            window.workshop_theme_manager.apply_theme(theme_key);
        }

        // Trigger selection event
        this.trigger_selection_event(theme_key);
    }

    preview_theme(theme_key) {
        if (!this.themes[theme_key] || !window.workshop_theme_manager) return;

        window.workshop_theme_manager.preview_theme(theme_key);
    }

    trigger_selection_event(theme_key) {
        const theme = this.themes[theme_key];

        $(this.parent).trigger('theme_selected', {
            theme_key: theme_key,
            theme_data: theme
        });

        // If this is part of a form, update the field value
        if (this.options.field_name && this.options.frm) {
            this.options.frm.set_value(this.options.field_name, theme_key);
        }
    }

    show_custom_theme_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: __('Create Custom Theme'),
            fields: [
                {
                    fieldname: 'theme_name',
                    fieldtype: 'Data',
                    label: __('Theme Name'),
                    reqd: 1
                },
                {
                    fieldname: 'base_theme',
                    fieldtype: 'Select',
                    label: __('Base Theme'),
                    options: Object.keys(this.themes).join('\n'),
                    default: 'classic'
                },
                {
                    fieldname: 'primary_color',
                    fieldtype: 'Color',
                    label: __('Primary Color'),
                    default: '#1f4e79'
                },
                {
                    fieldname: 'secondary_color',
                    fieldtype: 'Color',
                    label: __('Secondary Color'),
                    default: '#e8f4fd'
                },
                {
                    fieldname: 'accent_color',
                    fieldtype: 'Color',
                    label: __('Accent Color'),
                    default: '#2490ef'
                }
            ],
            primary_action: (values) => {
                this.create_custom_theme(values);
                dialog.hide();
            },
            primary_action_label: __('Create Theme')
        });

        dialog.show();
    }

    async create_custom_theme(values) {
        try {
            // Get base theme data
            const baseTheme = this.themes[values.base_theme];

            // Create custom theme data
            const customThemeData = {
                ...baseTheme,
                name: values.theme_name,
                colors: {
                    ...baseTheme.colors,
                    primary: values.primary_color,
                    secondary: values.secondary_color,
                    accent: values.accent_color
                }
            };

            // Save custom theme
            const response = await frappe.call({
                method: 'universal_workshop.themes.api.save_custom_theme',
                args: {
                    theme_name: values.theme_name,
                    theme_data: customThemeData
                }
            });

            if (response.message && response.message.success) {
                frappe.show_alert({
                    message: __('Custom theme created successfully'),
                    indicator: 'green'
                });

                // Reload themes and re-render
                await this.load_themes();
                this.wrapper.find('.theme-options-grid').html(this.render_theme_options());
                this.select_theme(values.theme_name);
            }

        } catch (error) {
            frappe.show_alert({
                message: __('Failed to create custom theme'),
                indicator: 'red'
            });
            console.error('Error creating custom theme:', error);
        }
    }

    get_selected_theme() {
        return {
            key: this.current_selection,
            data: this.themes[this.current_selection]
        };
    }

    set_theme(theme_key) {
        if (this.themes[theme_key]) {
            this.select_theme(theme_key);
        }
    }

    refresh() {
        this.load_themes().then(() => {
            this.wrapper.find('.theme-options-grid').html(this.render_theme_options());
        });
    }

    destroy() {
        if (this.wrapper) {
            this.wrapper.remove();
        }
    }
};
