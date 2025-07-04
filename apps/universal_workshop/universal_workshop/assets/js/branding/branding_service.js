/**
 * Universal Workshop Branding Service
 * Handles dynamic logo injection, theming, and visual identity management
 */

frappe.provide('universal_workshop.branding');

universal_workshop.branding.BrandingService = class BrandingService {
    constructor() {
        this.cache = new Map();
        this.observers = [];
        this.current_branding = null;
        this.init();
    }

    init() {
        // Load branding on app start
        this.load_branding();

        // Set up mutation observer for dynamic injection
        this.setup_mutation_observer();

        // Listen for branding updates
        this.setup_event_listeners();

        // Apply branding when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.apply_branding();
            });
        } else {
            this.apply_branding();
        }
    }

    async load_branding(workshop_name = null) {
        try {
            const cache_key = workshop_name || 'default';

            // Check cache first
            if (this.cache.has(cache_key)) {
                const cached = this.cache.get(cache_key);
                if (Date.now() - cached.timestamp < 300000) { // 5 minutes cache
                    this.current_branding = cached.data;
                    return this.current_branding;
                }
            }

            // Fetch from server
            const response = await frappe.call({
                method: 'universal_workshop.workshop_management.doctype.workshop_profile.workshop_profile.get_workshop_branding',
                args: { workshop_name: workshop_name }
            });

            if (response.message) {
                this.current_branding = response.message;

                // Cache the result
                this.cache.set(cache_key, {
                    data: this.current_branding,
                    timestamp: Date.now()
                });

                // Notify observers
                this.notify_observers('branding_loaded', this.current_branding);

                return this.current_branding;
            }
        } catch (error) {
            console.warn('Failed to load branding, using defaults:', error.message || error);
            this.current_branding = this.get_default_branding();

            // Still notify observers with default branding
            this.notify_observers('branding_loaded', this.current_branding);
        }

        return this.current_branding;
    }

    get_default_branding() {
        return {
            logo: null,
            primary_color: '#1f4e79',
            secondary_color: '#e8f4fd',
            dark_mode: false,
            theme: 'Light'
        };
    }

    apply_branding(branding = null) {
        const brand = branding || this.current_branding || this.get_default_branding();

        // Apply CSS custom properties
        this.apply_css_variables(brand);

        // Inject optimized logos into various UI components
        this.inject_logo_into_header(this.get_logo_variant(brand, 'medium'));
        this.inject_logo_into_sidebar(this.get_logo_variant(brand, 'small'));
        this.inject_logo_into_navbar(this.get_logo_variant(brand, 'small'));
        this.inject_logo_into_login(this.get_logo_variant(brand, 'large'));

        // Apply theme
        this.apply_theme(brand);

        // Update favicon with favicon variant
        this.update_favicon(this.get_logo_variant(brand, 'favicon'));

        // Notify observers
        this.notify_observers('branding_applied', brand);
    }

    get_logo_variant(branding, variant = 'medium') {
        /**
         * Get optimized logo variant URL based on use case
         * @param {Object} branding - Branding object
         * @param {string} variant - Variant type (thumbnail, small, medium, large, print, favicon)
         * @returns {string|null} - Logo URL or null
         */
        if (!branding) return null;

        // Try to get optimized variant first
        const variant_field = `logo_${variant}`;
        if (branding[variant_field]) {
            return branding[variant_field];
        }

        // Fallback to original logo
        return branding.logo || null;
    }

    get_logo_for_context(context) {
        /**
         * Get appropriate logo variant for specific context
         * @param {string} context - Context (header, sidebar, print, favicon, etc.)
         * @returns {string|null} - Logo URL
         */
        const brand = this.current_branding || this.get_default_branding();

        const context_mapping = {
            'header': 'medium',
            'navbar': 'small',
            'sidebar': 'small',
            'login': 'large',
            'print': 'print',
            'favicon': 'favicon',
            'thumbnail': 'thumbnail',
            'list_view': 'thumbnail',
            'form_header': 'small',
            'dashboard': 'medium'
        };

        const variant = context_mapping[context] || 'medium';
        return this.get_logo_variant(brand, variant);
    }

    apply_css_variables(branding) {
        const root = document.documentElement;

        // Set CSS custom properties
        root.style.setProperty('--workshop-primary-color', branding.primary_color);
        root.style.setProperty('--workshop-secondary-color', branding.secondary_color);
        root.style.setProperty('--workshop-logo-url', branding.logo ? `url(${branding.logo})` : 'none');

        // Additional color variations
        const primaryRgb = this.hex_to_rgb(branding.primary_color);
        const secondaryRgb = this.hex_to_rgb(branding.secondary_color);

        root.style.setProperty('--workshop-primary-rgb', `${primaryRgb.r}, ${primaryRgb.g}, ${primaryRgb.b}`);
        root.style.setProperty('--workshop-secondary-rgb', `${secondaryRgb.r}, ${secondaryRgb.g}, ${secondaryRgb.b}`);

        // Dark/light variations
        root.style.setProperty('--workshop-primary-light', this.lighten_color(branding.primary_color, 20));
        root.style.setProperty('--workshop-primary-dark', this.darken_color(branding.primary_color, 20));
        root.style.setProperty('--workshop-secondary-light', this.lighten_color(branding.secondary_color, 20));
        root.style.setProperty('--workshop-secondary-dark', this.darken_color(branding.secondary_color, 20));
    }

    inject_logo_into_header(logo_url) {
        if (!logo_url) return;

        // ERPNext main header
        const header_selectors = [
            '.navbar-brand img',
            '.navbar .navbar-brand img',
            '.navbar-header img',
            '.header-logo img'
        ];

        header_selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(img => {
                if (img) {
                    img.src = logo_url;
                    img.style.maxHeight = '40px';
                    img.style.maxWidth = '150px';
                    img.style.objectFit = 'contain';
                    img.alt = 'Workshop Logo';
                }
            });
        });

        // If no existing logo, create one
        const navbar = document.querySelector('.navbar-brand') || document.querySelector('.navbar .navbar-header');
        if (navbar && !navbar.querySelector('img')) {
            const logo_img = document.createElement('img');
            logo_img.src = logo_url;
            logo_img.style.maxHeight = '40px';
            logo_img.style.maxWidth = '150px';
            logo_img.style.objectFit = 'contain';
            logo_img.style.marginRight = '10px';
            logo_img.alt = 'Workshop Logo';

            navbar.insertBefore(logo_img, navbar.firstChild);
        }
    }

    inject_logo_into_sidebar(logo_url) {
        if (!logo_url) return;

        // ERPNext sidebar
        const sidebar = document.querySelector('.desk-sidebar') || document.querySelector('.sidebar');
        if (sidebar) {
            // Remove existing workshop logo
            const existing = sidebar.querySelector('.workshop-sidebar-logo');
            if (existing) {
                existing.remove();
            }

            // Create new logo container
            const logo_container = document.createElement('div');
            logo_container.className = 'workshop-sidebar-logo';
            logo_container.style.cssText = `
                text-align: center;
                padding: 15px 10px;
                border-bottom: 1px solid #e8e8e8;
                background: var(--workshop-secondary-color, #f8f9fa);
            `;

            const logo_img = document.createElement('img');
            logo_img.src = logo_url;
            logo_img.style.cssText = `
                max-width: 120px;
                max-height: 60px;
                object-fit: contain;
            `;
            logo_img.alt = 'Workshop Logo';

            logo_container.appendChild(logo_img);
            sidebar.insertBefore(logo_container, sidebar.firstChild);
        }
    }

    inject_logo_into_navbar(logo_url) {
        if (!logo_url) return;

        // ERPNext top navigation
        const navbar = document.querySelector('.navbar') || document.querySelector('.nav-container');
        if (navbar) {
            const brand_area = navbar.querySelector('.navbar-brand') || navbar.querySelector('.brand');
            if (brand_area) {
                // Style the brand area
                brand_area.style.cssText = `
                    display: flex;
                    align-items: center;
                    background: var(--workshop-primary-color, #1f4e79);
                    padding: 5px 15px;
                    border-radius: 4px;
                `;

                // Add/update logo
                let logo = brand_area.querySelector('.workshop-navbar-logo');
                if (!logo) {
                    logo = document.createElement('img');
                    logo.className = 'workshop-navbar-logo';
                    brand_area.insertBefore(logo, brand_area.firstChild);
                }

                logo.src = logo_url;
                logo.style.cssText = `
                    height: 30px;
                    margin-right: 10px;
                    object-fit: contain;
                `;
                logo.alt = 'Workshop Logo';
            }
        }
    }

    inject_logo_into_login(logo_url) {
        if (!logo_url) return;

        // Login page logo
        const login_container = document.querySelector('.login-content') ||
            document.querySelector('.page-card') ||
            document.querySelector('.form-signin');

        if (login_container) {
            // Remove existing workshop logo
            const existing = login_container.querySelector('.workshop-login-logo');
            if (existing) {
                existing.remove();
            }

            // Create new logo
            const logo_container = document.createElement('div');
            logo_container.className = 'workshop-login-logo';
            logo_container.style.cssText = `
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
            `;

            const logo_img = document.createElement('img');
            logo_img.src = logo_url;
            logo_img.style.cssText = `
                max-width: 200px;
                max-height: 100px;
                object-fit: contain;
            `;
            logo_img.alt = 'Workshop Logo';

            logo_container.appendChild(logo_img);
            login_container.insertBefore(logo_container, login_container.firstChild);
        }
    }

    apply_theme(branding) {
        const body = document.body;

        // Remove existing theme classes
        body.classList.remove('workshop-light-theme', 'workshop-dark-theme');

        // Apply theme class
        if (branding.dark_mode || branding.theme === 'Dark') {
            body.classList.add('workshop-dark-theme');
        } else {
            body.classList.add('workshop-light-theme');
        }

        // Apply theme-specific styles
        this.inject_theme_styles(branding);
    }

    inject_theme_styles(branding) {
        // Remove existing theme styles
        const existing = document.getElementById('workshop-dynamic-theme');
        if (existing) {
            existing.remove();
        }

        // Create new theme styles
        const style = document.createElement('style');
        style.id = 'workshop-dynamic-theme';
        style.textContent = this.generate_theme_css(branding);

        document.head.appendChild(style);
    }

    generate_theme_css(branding) {
        const isDark = branding.dark_mode || branding.theme === 'Dark';

        return `
            /* Workshop Dynamic Theme */
            :root {
                --workshop-primary: ${branding.primary_color};
                --workshop-secondary: ${branding.secondary_color};
                --workshop-bg: ${isDark ? '#2c3e50' : '#ffffff'};
                --workshop-text: ${isDark ? '#ecf0f1' : '#2c3e50'};
                --workshop-border: ${isDark ? '#34495e' : '#dee2e6'};
            }
            
            /* Header Styling */
            .navbar, .nav-container {
                background: var(--workshop-primary) !important;
                border-bottom: 2px solid var(--workshop-primary-dark);
            }
            
            .navbar-brand, .navbar .brand {
                color: white !important;
            }
            
            /* Sidebar Styling */
            .desk-sidebar, .sidebar {
                border-right: 1px solid var(--workshop-border);
            }
            
            .desk-sidebar .sidebar-item.selected,
            .sidebar .sidebar-item.active {
                background: var(--workshop-secondary) !important;
                border-left: 3px solid var(--workshop-primary);
            }
            
            /* Button Styling */
            .btn-primary {
                background-color: var(--workshop-primary) !important;
                border-color: var(--workshop-primary) !important;
            }
            
            .btn-primary:hover {
                background-color: var(--workshop-primary-dark) !important;
                border-color: var(--workshop-primary-dark) !important;
            }
            
            /* Form Styling */
            .form-control:focus {
                border-color: var(--workshop-primary);
                box-shadow: 0 0 0 0.2rem rgba(var(--workshop-primary-rgb), 0.25);
            }
            
            /* Section Headers */
            .section-head, .form-section .section-head {
                background: var(--workshop-primary) !important;
                color: white !important;
            }
            
            /* Links */
            a {
                color: var(--workshop-primary);
            }
            
            a:hover {
                color: var(--workshop-primary-dark);
            }
            
            /* Dark Theme Specific */
            ${isDark ? `
                body.workshop-dark-theme {
                    background: var(--workshop-bg);
                    color: var(--workshop-text);
                }
                
                .desk, .layout-main {
                    background: var(--workshop-bg);
                }
                
                .form-control, .input-group-text {
                    background: #34495e;
                    border-color: #34495e;
                    color: var(--workshop-text);
                }
                
                .card, .frappe-card {
                    background: #34495e;
                    border-color: #34495e;
                }
            ` : ''}
            
            /* Print Styles */
            @media print {
                .workshop-print-logo {
                    content: var(--workshop-logo-url);
                    max-height: 60px;
                    max-width: 200px;
                }
            }
        `;
    }

    update_favicon(logo_url) {
        if (!logo_url) return;

        // Update favicon
        const favicon = document.querySelector('link[rel="icon"]') ||
            document.querySelector('link[rel="shortcut icon"]');

        if (favicon) {
            favicon.href = logo_url;
        } else {
            // Create new favicon
            const link = document.createElement('link');
            link.rel = 'icon';
            link.href = logo_url;
            document.head.appendChild(link);
        }
    }

    setup_mutation_observer() {
        // Watch for DOM changes to inject logo into new elements
        const observer = new MutationObserver((mutations) => {
            let should_reapply = false;

            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === 1) { // Element node
                            // Check if new navigation elements were added
                            if (node.matches && (
                                node.matches('.navbar') ||
                                node.matches('.sidebar') ||
                                node.matches('.desk-sidebar') ||
                                node.querySelector('.navbar') ||
                                node.querySelector('.sidebar')
                            )) {
                                should_reapply = true;
                            }
                        }
                    });
                }
            });

            if (should_reapply) {
                setTimeout(() => this.apply_branding(), 100);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        this.observers.push(observer);
    }

    setup_event_listeners() {
        // Listen for route changes
        $(document).on('page-change', () => {
            setTimeout(() => this.apply_branding(), 100);
        });

        // Listen for custom branding update events
        $(document).on('workshop:branding_updated', (event, branding) => {
            this.current_branding = branding;
            this.apply_branding(branding);
        });

        // Listen for theme changes
        $(document).on('workshop:theme_changed', (event, theme) => {
            if (this.current_branding) {
                this.current_branding.theme = theme;
                this.current_branding.dark_mode = theme === 'Dark';
                this.apply_branding(this.current_branding);
            }
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

    // Observer pattern for branding changes
    add_observer(callback) {
        this.observers.push(callback);
    }

    remove_observer(callback) {
        const index = this.observers.indexOf(callback);
        if (index > -1) {
            this.observers.splice(index, 1);
        }
    }

    notify_observers(event, data) {
        this.observers.forEach(observer => {
            if (typeof observer === 'function') {
                try {
                    observer(event, data);
                } catch (error) {
                    console.error('Error in branding observer:', error);
                }
            }
        });
    }

    // Public API methods
    refresh_branding() {
        this.cache.clear();
        return this.load_branding().then(() => {
            this.apply_branding();
        });
    }

    update_branding(branding) {
        this.current_branding = branding;
        this.cache.clear();
        this.apply_branding(branding);

        // Trigger custom event
        $(document).trigger('workshop:branding_updated', [branding]);
    }

    get_current_branding() {
        return this.current_branding || this.get_default_branding();
    }

    destroy() {
        // Clean up observers
        this.observers.forEach(observer => {
            if (observer.disconnect) {
                observer.disconnect();
            }
        });
        this.observers = [];

        // Remove event listeners
        $(document).off('page-change workshop:branding_updated workshop:theme_changed');

        // Remove dynamic styles
        const dynamicStyle = document.getElementById('workshop-dynamic-theme');
        if (dynamicStyle) {
            dynamicStyle.remove();
        }
    }
};

// Initialize the branding service when Frappe is ready
frappe.ready(() => {
    if (!window.workshop_branding_service) {
        window.workshop_branding_service = new universal_workshop.branding.BrandingService();
    }
});

// Global helper functions
window.refresh_workshop_branding = () => {
    if (window.workshop_branding_service) {
        return window.workshop_branding_service.refresh_branding();
    }
};

window.update_workshop_branding = (branding) => {
    if (window.workshop_branding_service) {
        window.workshop_branding_service.update_branding(branding);
    }
}; 