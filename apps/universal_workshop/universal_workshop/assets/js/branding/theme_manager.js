/**
 * Universal Workshop Theme Manager
 * Handles theme selection, customization, and persistence
 */

frappe.provide('universal_workshop.themes');

universal_workshop.themes.ThemeManager = class ThemeManager {
    constructor() {
        this.current_theme = null;
        this.available_themes = {};
        this.custom_themes = {};
        this.theme_cache = new Map();
        this.init();
    }

    init() {
        // Load default themes
        this.load_default_themes();

        // Load custom themes
        this.load_custom_themes();

        // Load current theme
        this.load_current_theme();

        // Set up event listeners
        this.setup_event_listeners();
    }

    load_default_themes() {
        /**
         * Default theme definitions for Universal Workshop
         */
        this.available_themes = {
            'classic': {
                name: 'Classic Blue',
                name_ar: 'الأزرق الكلاسيكي',
                description: 'Traditional ERPNext blue theme with workshop enhancements',
                description_ar: 'موضوع أزرق تقليدي مع تحسينات الورشة',
                colors: {
                    primary: '#1f4e79',
                    secondary: '#e8f4fd',
                    accent: '#2490ef',
                    success: '#28a745',
                    warning: '#ffc107',
                    danger: '#dc3545',
                    info: '#17a2b8',
                    light: '#f8f9fa',
                    dark: '#343a40'
                },
                fonts: {
                    primary: '"Noto Sans", "Helvetica Neue", Arial, sans-serif',
                    arabic: '"Noto Sans Arabic", "Tahoma", "Arial Unicode MS", sans-serif',
                    monospace: '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace'
                },
                properties: {
                    borderRadius: '4px',
                    shadowLevel: 'medium',
                    spacing: 'normal'
                }
            },

            'automotive': {
                name: 'Automotive Green',
                name_ar: 'الأخضر السيارات',
                description: 'Professional green theme inspired by automotive industry',
                description_ar: 'موضوع أخضر مهني مستوحى من صناعة السيارات',
                colors: {
                    primary: '#2c5f41',
                    secondary: '#e8f5e8',
                    accent: '#4caf50',
                    success: '#388e3c',
                    warning: '#ff9800',
                    danger: '#f44336',
                    info: '#2196f3',
                    light: '#f1f8e9',
                    dark: '#1b5e20'
                },
                fonts: {
                    primary: '"Roboto", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
                    arabic: '"Noto Sans Arabic", "Tahoma", "Arial Unicode MS", sans-serif',
                    monospace: '"Roboto Mono", "SFMono-Regular", Consolas, monospace'
                },
                properties: {
                    borderRadius: '6px',
                    shadowLevel: 'high',
                    spacing: 'comfortable'
                }
            },

            'luxury': {
                name: 'Luxury Gold',
                name_ar: 'الذهبي الفاخر',
                description: 'Premium gold and black theme for luxury workshops',
                description_ar: 'موضوع ذهبي وأسود راقي للورش الفاخرة',
                colors: {
                    primary: '#b8860b',
                    secondary: '#fffef7',
                    accent: '#ffd700',
                    success: '#6a994e',
                    warning: '#f77f00',
                    danger: '#d62828',
                    info: '#457b9d',
                    light: '#fefcf3',
                    dark: '#2f3e46'
                },
                fonts: {
                    primary: '"Playfair Display", Georgia, "Times New Roman", serif',
                    arabic: '"Amiri", "Noto Sans Arabic", "Times New Roman", serif',
                    monospace: '"Source Code Pro", "SFMono-Regular", monospace'
                },
                properties: {
                    borderRadius: '8px',
                    shadowLevel: 'high',
                    spacing: 'spacious'
                }
            },

            'light': {
                name: 'Light Modern',
                name_ar: 'الفاتح العصري',
                description: 'Clean light theme with modern aesthetics',
                description_ar: 'موضوع فاتح نظيف بجماليات عصرية',
                colors: {
                    primary: '#2563eb',
                    secondary: '#f8fafc',
                    accent: '#3b82f6',
                    success: '#10b981',
                    warning: '#f59e0b',
                    danger: '#ef4444',
                    info: '#06b6d4',
                    light: '#ffffff',
                    dark: '#1f2937'
                },
                fonts: {
                    primary: '"Inter", "Segoe UI", Roboto, sans-serif',
                    arabic: '"Noto Sans Arabic", "Segoe UI", Tahoma, sans-serif',
                    monospace: '"JetBrains Mono", "SFMono-Regular", Consolas, monospace'
                },
                properties: {
                    borderRadius: '6px',
                    shadowLevel: 'soft',
                    spacing: 'normal'
                }
            }
        };
    }

    async load_custom_themes() {
        /**
         * Load custom themes from server
         */
        try {
            const response = await frappe.call({
                method: 'universal_workshop.themes.api.get_custom_themes'
            });

            if (response.message) {
                this.custom_themes = response.message;
            }
        } catch (error) {
            console.warn('Could not load custom themes:', error);
        }
    }

    async load_current_theme() {
        /**
         * Load current theme from user preferences or workshop branding
         */
        try {
            // First check user preferences
            const user_theme = frappe.boot.user_theme ||
                localStorage.getItem('workshop_theme') ||
                'classic';

            // Load branding-based theme if available
            if (window.workshop_branding_service) {
                const branding = window.workshop_branding_service.get_current_branding();
                if (branding && branding.theme) {
                    this.current_theme = branding.theme.toLowerCase();
                } else {
                    this.current_theme = user_theme;
                }
            } else {
                this.current_theme = user_theme;
            }

            // Apply the current theme
            await this.apply_theme(this.current_theme);

        } catch (error) {
            console.error('Error loading current theme:', error);
            this.current_theme = 'classic';
            await this.apply_theme('classic');
        }
    }

    async apply_theme(theme_name, persist = true) {
        /**
         * Apply a theme to the interface
         */
        try {
            const theme = this.get_theme(theme_name);
            if (!theme) {
                console.warn(`Theme "${theme_name}" not found, falling back to classic`);
                theme_name = 'classic';
                const fallback_theme = this.get_theme('classic');
                if (!fallback_theme) {
                    throw new Error('Classic theme not found - theme system corrupted');
                }
                return await this.apply_theme('classic', persist);
            }

            // Remove existing theme classes
            document.body.classList.remove(...this.get_theme_classes());

            // Add new theme class
            document.body.classList.add(`theme-${theme_name}`);

            // Apply CSS custom properties
            this.apply_theme_css_variables(theme);

            // Apply fonts
            this.apply_theme_fonts(theme);

            // Apply additional properties
            this.apply_theme_properties(theme);

            // Update current theme
            this.current_theme = theme_name;

            // Persist theme preference
            if (persist) {
                await this.save_theme_preference(theme_name);
            }

            // Trigger theme change event
            $(document).trigger('workshop:theme_changed', [theme_name, theme]);

            // Update branding service if available
            if (window.workshop_branding_service) {
                const current_branding = window.workshop_branding_service.get_current_branding();
                current_branding.theme = theme_name;
                current_branding.primary_color = theme.colors.primary;
                current_branding.secondary_color = theme.colors.secondary;
                window.workshop_branding_service.update_branding(current_branding);
            }

            console.log(`Theme "${theme_name}" applied successfully`);
            return true;

        } catch (error) {
            console.error('Error applying theme:', error);
            frappe.show_alert({
                message: __('Failed to apply theme: {0}', [error.message]),
                indicator: 'red'
            });
            return false;
        }
    }

    apply_theme_css_variables(theme) {
        /**
         * Apply theme colors as CSS custom properties
         */
        const root = document.documentElement;

        // Apply color variables
        Object.entries(theme.colors).forEach(([key, value]) => {
            root.style.setProperty(`--theme-${key}`, value);

            // Create RGB versions for transparency
            const rgb = this.hex_to_rgb(value);
            root.style.setProperty(`--theme-${key}-rgb`, `${rgb.r}, ${rgb.g}, ${rgb.b}`);

            // Create lighter and darker variations
            root.style.setProperty(`--theme-${key}-light`, this.lighten_color(value, 20));
            root.style.setProperty(`--theme-${key}-dark`, this.darken_color(value, 20));
        });

        // Apply property variables
        if (theme.properties) {
            Object.entries(theme.properties).forEach(([key, value]) => {
                root.style.setProperty(`--theme-${key}`, value);
            });
        }
    }

    apply_theme_fonts(theme) {
        /**
         * Apply theme font families
         */
        if (!theme.fonts) return;

        const root = document.documentElement;

        // Apply font variables
        Object.entries(theme.fonts).forEach(([key, value]) => {
            root.style.setProperty(`--theme-font-${key}`, value);
        });

        // Apply Arabic font specifically
        if (theme.fonts.arabic) {
            root.style.setProperty('--arabic-font-family', theme.fonts.arabic);
        }
    }

    apply_theme_properties(theme) {
        /**
         * Apply additional theme properties
         */
        if (!theme.properties) return;

        const root = document.documentElement;

        // Apply spacing
        if (theme.properties.spacing) {
            const spacingMap = {
                'minimal': '0.5rem',
                'normal': '1rem',
                'comfortable': '1.5rem',
                'spacious': '2rem'
            };
            root.style.setProperty('--theme-spacing', spacingMap[theme.properties.spacing] || '1rem');
        }

        // Apply shadow level
        if (theme.properties.shadowLevel) {
            const shadowMap = {
                'none': 'none',
                'soft': '0 2px 4px rgba(0,0,0,0.1)',
                'medium': '0 4px 8px rgba(0,0,0,0.15)',
                'high': '0 8px 16px rgba(0,0,0,0.2)'
            };
            root.style.setProperty('--theme-shadow', shadowMap[theme.properties.shadowLevel] || shadowMap.medium);
        }
    }

    get_theme(theme_name) {
        /**
         * Get theme definition by name
         */
        return this.available_themes[theme_name] ||
            this.custom_themes[theme_name] ||
            null;
    }

    get_all_themes() {
        /**
         * Get all available themes
         */
        return {
            ...this.available_themes,
            ...this.custom_themes
        };
    }

    get_theme_classes() {
        /**
         * Get all possible theme CSS classes
         */
        const all_themes = this.get_all_themes();
        return Object.keys(all_themes).map(name => `theme-${name}`);
    }

    async save_theme_preference(theme_name) {
        /**
         * Save theme preference to user settings
         */
        try {
            // Save to localStorage for immediate persistence
            localStorage.setItem('workshop_theme', theme_name);

            // Save to user preferences on server
            await frappe.call({
                method: 'frappe.desk.doctype.user_permission.user_permission.set_user_permission',
                args: {
                    doctype: 'User',
                    name: frappe.session.user,
                    fieldname: 'theme_preference',
                    value: theme_name
                }
            });

        } catch (error) {
            console.warn('Could not save theme preference to server:', error);
            // LocalStorage save already happened, so this is not critical
        }
    }

    show_theme_selector() {
        /**
         * Show theme selection dialog
         */
        const themes = this.get_all_themes();
        const current = this.current_theme;

        const dialog = new frappe.ui.Dialog({
            title: __('Select Theme'),
            fields: [
                {
                    fieldname: 'theme_preview',
                    fieldtype: 'HTML',
                    options: this.generate_theme_preview_html(themes, current)
                },
                {
                    fieldname: 'selected_theme',
                    fieldtype: 'Select',
                    label: __('Theme'),
                    options: Object.keys(themes).map(key => ({
                        label: themes[key].name,
                        value: key
                    })),
                    default: current,
                    change: () => {
                        const selected = dialog.get_value('selected_theme');
                        this.preview_theme(selected);
                    }
                }
            ],
            primary_action_label: __('Apply Theme'),
            primary_action: async () => {
                const selected = dialog.get_value('selected_theme');
                const success = await this.apply_theme(selected);
                if (success) {
                    dialog.hide();
                    frappe.show_alert({
                        message: __('Theme applied successfully'),
                        indicator: 'green'
                    });
                }
            }
        });

        dialog.show();
    }

    preview_theme(theme_name) {
        /**
         * Preview a theme without applying it permanently
         */
        this.apply_theme(theme_name, false);
    }

    generate_theme_preview_html(themes, current) {
        /**
         * Generate HTML for theme preview
         */
        let html = '<div class="theme-preview-container">';

        Object.entries(themes).forEach(([key, theme]) => {
            const isActive = key === current ? 'active' : '';
            html += `
                <div class="theme-preview-card ${isActive}" data-theme="${key}">
                    <div class="theme-colors">
                        <div class="color-swatch" style="background: ${theme.colors.primary}"></div>
                        <div class="color-swatch" style="background: ${theme.colors.secondary}"></div>
                        <div class="color-swatch" style="background: ${theme.colors.accent}"></div>
                    </div>
                    <div class="theme-info">
                        <h5>${theme.name}</h5>
                        <p class="text-muted">${theme.description}</p>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    setup_event_listeners() {
        /**
         * Set up event listeners for theme management
         */
        // Listen for branding updates
        $(document).on('workshop:branding_updated', (event, branding) => {
            if (branding.theme && branding.theme !== this.current_theme) {
                this.apply_theme(branding.theme, false);
            }
        });

        // Listen for theme change requests
        $(document).on('workshop:change_theme', (event, theme_name) => {
            this.apply_theme(theme_name);
        });

        // Listen for theme selector requests
        $(document).on('workshop:show_theme_selector', () => {
            this.show_theme_selector();
        });
    }

    // Utility methods
    hex_to_rgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : { r: 0, g: 0, b: 0 };
    }

    lighten_color(color, percent) {
        const rgb = this.hex_to_rgb(color);
        const factor = percent / 100;

        const r = Math.round(rgb.r + (255 - rgb.r) * factor);
        const g = Math.round(rgb.g + (255 - rgb.g) * factor);
        const b = Math.round(rgb.b + (255 - rgb.b) * factor);

        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }

    darken_color(color, percent) {
        const rgb = this.hex_to_rgb(color);
        const factor = 1 - (percent / 100);

        const r = Math.round(rgb.r * factor);
        const g = Math.round(rgb.g * factor);
        const b = Math.round(rgb.b * factor);

        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }

    get_current_theme() {
        return this.current_theme;
    }

    get_current_theme_data() {
        return this.get_theme(this.current_theme);
    }

    destroy() {
        // Clean up event listeners
        $(document).off('workshop:branding_updated workshop:change_theme workshop:show_theme_selector');

        // Clear cache
        this.theme_cache.clear();
    }
};

// Initialize theme manager when Frappe is ready
frappe.ready(() => {
    if (!window.workshop_theme_manager) {
        window.workshop_theme_manager = new universal_workshop.themes.ThemeManager();
    }
});

// Global helper functions
window.change_workshop_theme = (theme_name) => {
    if (window.workshop_theme_manager) {
        return window.workshop_theme_manager.apply_theme(theme_name);
    }
};

window.show_theme_selector = () => {
    if (window.workshop_theme_manager) {
        window.workshop_theme_manager.show_theme_selector();
    }
}; 