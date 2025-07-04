/**
 * Dark Mode Manager for Universal Workshop ERP
 * Provides comprehensive dark mode functionality with theme integration
 */

class DarkModeManager {
    constructor() {
        this.STORAGE_KEY = 'workshop_dark_mode';
        this.THEME_STORAGE_KEY = 'workshop_theme_preference';
        this.CSS_CLASS = 'workshop-dark-mode';
        this.isInitialized = false;
        this.currentMode = 'light';
        this.systemPreference = 'light';
        this.userPreference = 'system'; // 'light', 'dark', 'system'

        this.init();
    }

    init() {
        if (this.isInitialized) return;

        // Setup CSS custom properties FIRST
        this.setupCSSProperties();

        // Load saved preferences
        this.loadPreferences();

        // Detect system preference
        this.detectSystemPreference();

        // Apply initial mode
        this.applyMode();

        // Setup system preference listener
        this.setupSystemListener();

        // Setup toggle UI
        this.setupToggleUI();

        this.isInitialized = true;
        console.log('Dark Mode Manager initialized');
    }

    loadPreferences() {
        try {
            // Load from localStorage
            const saved = localStorage.getItem(this.STORAGE_KEY);
            if (saved) {
                const data = JSON.parse(saved);
                this.userPreference = data.preference || 'system';
                this.currentMode = data.currentMode || 'light';
            }

            // Load from user settings if available
            if (frappe.user && frappe.user.defaults) {
                const userDarkMode = frappe.user.defaults.dark_mode_preference;
                if (userDarkMode) {
                    this.userPreference = userDarkMode;
                }
            }
        } catch (error) {
            console.warn('Failed to load dark mode preferences:', error);
        }
    }

    savePreferences() {
        try {
            const data = {
                preference: this.userPreference,
                currentMode: this.currentMode,
                timestamp: new Date().toISOString()
            };

            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));

            // Save to user settings if possible
            if (frappe.user) {
                frappe.call({
                    method: 'frappe.client.set_value',
                    args: {
                        doctype: 'User',
                        name: frappe.session.user,
                        fieldname: 'dark_mode_preference',
                        value: this.userPreference
                    },
                    freeze: false,
                    callback: () => {
                        console.log('Dark mode preference saved to user settings');
                    }
                });
            }
        } catch (error) {
            console.warn('Failed to save dark mode preferences:', error);
        }
    }

    detectSystemPreference() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            this.systemPreference = mediaQuery.matches ? 'dark' : 'light';
            return this.systemPreference;
        }
        return 'light';
    }

    setupSystemListener() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                this.systemPreference = e.matches ? 'dark' : 'light';
                if (this.userPreference === 'system') {
                    this.applyMode();
                }
            });
        }
    }

    getCurrentMode() {
        if (this.userPreference === 'system') {
            return this.systemPreference;
        }
        return this.userPreference;
    }

    applyMode() {
        const newMode = this.getCurrentMode();
        const wasChanged = newMode !== this.currentMode;
        this.currentMode = newMode;

        const $body = $('body');
        const $html = $('html');

        if (this.currentMode === 'dark') {
            $body.addClass(this.CSS_CLASS);
            $html.addClass(this.CSS_CLASS);
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            $body.removeClass(this.CSS_CLASS);
            $html.removeClass(this.CSS_CLASS);
            document.documentElement.setAttribute('data-theme', 'light');
        }

        // Update CSS custom properties
        this.updateCSSProperties();

        // Update toggle UI
        this.updateToggleUI();

        // Trigger events
        if (wasChanged) {
            $(document).trigger('workshop:dark_mode_changed', {
                mode: this.currentMode,
                preference: this.userPreference
            });

            // Refresh branding if available
            if (window.refresh_workshop_branding) {
                window.refresh_workshop_branding();
            }
        }

        // Save preferences
        this.savePreferences();
    }

    setupCSSProperties() {
        // Define dark mode color scheme
        const darkColors = {
            '--workshop-bg-primary': '#1a1a1a',
            '--workshop-bg-secondary': '#2d2d2d',
            '--workshop-bg-tertiary': '#3a3a3a',
            '--workshop-text-primary': '#ffffff',
            '--workshop-text-secondary': '#cccccc',
            '--workshop-text-muted': '#999999',
            '--workshop-border-color': '#4a4a4a',
            '--workshop-shadow': '0 2px 8px rgba(0, 0, 0, 0.3)',
            '--workshop-card-bg': '#2d2d2d',
            '--workshop-input-bg': '#3a3a3a',
            '--workshop-input-border': '#555555',
            '--workshop-button-bg': '#4a4a4a',
            '--workshop-button-hover': '#5a5a5a',
            '--workshop-accent-color': '#4dabf7',
            '--workshop-success-color': '#51cf66',
            '--workshop-warning-color': '#ffd43b',
            '--workshop-danger-color': '#ff6b6b',
            '--workshop-info-color': '#74c0fc'
        };

        const lightColors = {
            '--workshop-bg-primary': '#ffffff',
            '--workshop-bg-secondary': '#f8f9fa',
            '--workshop-bg-tertiary': '#e9ecef',
            '--workshop-text-primary': '#212529',
            '--workshop-text-secondary': '#495057',
            '--workshop-text-muted': '#6c757d',
            '--workshop-border-color': '#dee2e6',
            '--workshop-shadow': '0 2px 8px rgba(0, 0, 0, 0.1)',
            '--workshop-card-bg': '#ffffff',
            '--workshop-input-bg': '#ffffff',
            '--workshop-input-border': '#ced4da',
            '--workshop-button-bg': '#e9ecef',
            '--workshop-button-hover': '#f8f9fa',
            '--workshop-accent-color': '#0066cc',
            '--workshop-success-color': '#28a745',
            '--workshop-warning-color': '#ffc107',
            '--workshop-danger-color': '#dc3545',
            '--workshop-info-color': '#17a2b8'
        };

        this.darkColors = darkColors;
        this.lightColors = lightColors;
    }

    updateCSSProperties() {
        const colors = this.currentMode === 'dark' ? this.darkColors : this.lightColors;
        const root = document.documentElement;

        // Check if colors is defined and is an object
        if (colors && typeof colors === 'object' && Object.keys(colors).length > 0) {
            try {
                Object.entries(colors).forEach(([property, value]) => {
                    if (property && value) {
                        root.style.setProperty(property, value);
                    }
                });
            } catch (error) {
                console.warn('Error updating CSS properties:', error);
            }
        } else {
            console.warn('Colors object is empty or invalid:', colors);
        }

        // Update theme-specific colors if theme manager is available
        if (window.workshop_theme_manager) {
            window.workshop_theme_manager.updateDarkModeColors(this.currentMode);
        }
    }

    setupToggleUI() {
        // Add dark mode toggle to navbar
        this.addNavbarToggle();

        // Add dark mode toggle to user menu
        this.addUserMenuToggle();

        // Add dark mode section to theme selector
        this.addThemeSelectorIntegration();
    }

    addNavbarToggle() {
        // Check if toggle already exists
        if ($('.workshop-dark-mode-toggle').length > 0) return;

        const toggleHTML = `
            <li class="nav-item dropdown workshop-dark-mode-toggle">
                <a class="nav-link" href="#" id="darkModeToggle" title="${__('Toggle Dark Mode')}">
                    <i class="fa fa-moon-o dark-mode-icon" style="font-size: 16px;"></i>
                </a>
            </li>
        `;

        // Add to navbar (try multiple locations)
        const $navbar = $('.navbar-nav:last');
        if ($navbar.length > 0) {
            $navbar.append(toggleHTML);
        } else {
            // Fallback: add to any available navbar
            $('.navbar .navbar-nav').first().append(toggleHTML);
        }

        // Bind click event
        $(document).on('click', '#darkModeToggle', (e) => {
            e.preventDefault();
            this.toggleMode();
        });
    }

    addUserMenuToggle() {
        // Add to user dropdown menu if available
        const userDropdown = $('.navbar .dropdown-menu:contains("' + __('My Settings') + '")');
        if (userDropdown.length > 0) {
            const toggleItem = `
                <a class="dropdown-item workshop-dark-mode-menu-item" href="#" id="userMenuDarkToggle">
                    <i class="fa fa-moon-o"></i> ${__('Dark Mode')}
                    <span class="dark-mode-status">(${this.currentMode === 'dark' ? __('On') : __('Off')})</span>
                </a>
            `;
            userDropdown.append('<div class="dropdown-divider"></div>' + toggleItem);

            $(document).on('click', '#userMenuDarkToggle', (e) => {
                e.preventDefault();
                this.showPreferenceDialog();
            });
        }
    }

    addThemeSelectorIntegration() {
        // Integration with theme selector if available
        if (window.workshop_theme_selector) {
            window.workshop_theme_selector.addDarkModeSection(this);
        }
    }

    updateToggleUI() {
        // Update navbar toggle icon
        const $icon = $('#darkModeToggle .dark-mode-icon');
        if ($icon.length > 0) {
            if (this.currentMode === 'dark') {
                $icon.removeClass('fa-moon-o').addClass('fa-sun-o');
                $('#darkModeToggle').attr('title', __('Switch to Light Mode'));
            } else {
                $icon.removeClass('fa-sun-o').addClass('fa-moon-o');
                $('#darkModeToggle').attr('title', __('Switch to Dark Mode'));
            }
        }

        // Update user menu status
        const $status = $('.dark-mode-status');
        if ($status.length > 0) {
            $status.text(`(${this.currentMode === 'dark' ? __('On') : __('Off')})`);
        }
    }

    toggleMode() {
        if (this.userPreference === 'system') {
            // If currently system, switch to opposite of current system preference
            this.setPreference(this.systemPreference === 'dark' ? 'light' : 'dark');
        } else {
            // Toggle between light and dark
            this.setPreference(this.currentMode === 'dark' ? 'light' : 'dark');
        }
    }

    setPreference(preference) {
        if (['light', 'dark', 'system'].includes(preference)) {
            this.userPreference = preference;
            this.applyMode();

            // Show feedback
            frappe.show_alert({
                message: __('Dark mode preference updated'),
                indicator: 'green'
            });
        }
    }

    showPreferenceDialog() {
        const dialog = new frappe.ui.Dialog({
            title: __('Dark Mode Preferences'),
            fields: [
                {
                    fieldtype: 'Select',
                    fieldname: 'preference',
                    label: __('Dark Mode Preference'),
                    options: [
                        { label: __('System Default'), value: 'system' },
                        { label: __('Light Mode'), value: 'light' },
                        { label: __('Dark Mode'), value: 'dark' }
                    ],
                    default: this.userPreference,
                    description: __('Choose your preferred dark mode setting')
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'info',
                    options: `
                        <div class="alert alert-info">
                            <strong>${__('Current System Preference')}:</strong> ${this.systemPreference}<br>
                            <strong>${__('Current Mode')}:</strong> ${this.currentMode}
                        </div>
                    `
                }
            ],
            primary_action_label: __('Save'),
            primary_action: (values) => {
                this.setPreference(values.preference);
                dialog.hide();
            },
            secondary_action_label: __('Cancel')
        });

        dialog.show();
    }

    // Public API methods
    isDarkMode() {
        return this.currentMode === 'dark';
    }

    getPreference() {
        return this.userPreference;
    }

    getCurrentTheme() {
        return {
            mode: this.currentMode,
            preference: this.userPreference,
            systemPreference: this.systemPreference
        };
    }

    // Integration with existing systems
    integrateWithBranding() {
        // Enhance branding service with dark mode support
        if (window.workshop_branding_service) {
            const originalGetBranding = window.workshop_branding_service.getCurrentBranding;
            window.workshop_branding_service.getCurrentBranding = () => {
                const branding = originalGetBranding.call(window.workshop_branding_service);
                if (branding) {
                    branding.darkMode = this.isDarkMode();
                    branding.theme = this.getCurrentTheme();
                }
                return branding;
            };
        }
    }

    integrateWithThemes() {
        // Enhance theme manager with dark mode support
        if (window.workshop_theme_manager) {
            window.workshop_theme_manager.setDarkModeManager(this);
        }
    }
}

// Auto-initialize when DOM is ready
$(document).ready(() => {
    // Initialize dark mode manager
    window.workshop_dark_mode = new DarkModeManager();

    // Setup integrations
    window.workshop_dark_mode.integrateWithBranding();
    window.workshop_dark_mode.integrateWithThemes();

    // Global helper functions
    window.toggleDarkMode = () => window.workshop_dark_mode.toggleMode();
    window.setDarkModePreference = (pref) => window.workshop_dark_mode.setPreference(pref);
    window.isDarkMode = () => window.workshop_dark_mode.isDarkMode();

    console.log('Dark Mode Manager loaded and ready');
});

// CSS injection for immediate dark mode styles
const darkModeCSS = `
    /* Dark Mode Base Styles */
    .workshop-dark-mode {
        background-color: var(--workshop-bg-primary, #1a1a1a) !important;
        color: var(--workshop-text-primary, #ffffff) !important;
    }
    
    .workshop-dark-mode .navbar {
        background-color: var(--workshop-bg-secondary, #2d2d2d) !important;
        border-color: var(--workshop-border-color, #4a4a4a) !important;
    }
    
    .workshop-dark-mode .navbar-nav .nav-link {
        color: var(--workshop-text-secondary, #cccccc) !important;
    }
    
    .workshop-dark-mode .navbar-nav .nav-link:hover {
        color: var(--workshop-text-primary, #ffffff) !important;
    }
    
    .workshop-dark-mode .card,
    .workshop-dark-mode .form-control,
    .workshop-dark-mode .list-group-item {
        background-color: var(--workshop-card-bg, #2d2d2d) !important;
        color: var(--workshop-text-primary, #ffffff) !important;
        border-color: var(--workshop-border-color, #4a4a4a) !important;
    }
    
    .workshop-dark-mode .btn-default {
        background-color: var(--workshop-button-bg, #4a4a4a) !important;
        color: var(--workshop-text-primary, #ffffff) !important;
        border-color: var(--workshop-border-color, #4a4a4a) !important;
    }
    
    .workshop-dark-mode .btn-default:hover {
        background-color: var(--workshop-button-hover, #5a5a5a) !important;
    }
    
    .workshop-dark-mode .sidebar {
        background-color: var(--workshop-bg-secondary, #2d2d2d) !important;
    }
    
    .workshop-dark-mode .sidebar .sidebar-item {
        color: var(--workshop-text-secondary, #cccccc) !important;
    }
    
    .workshop-dark-mode .sidebar .sidebar-item:hover {
        background-color: var(--workshop-bg-tertiary, #3a3a3a) !important;
        color: var(--workshop-text-primary, #ffffff) !important;
    }
    
    /* Dark mode toggle styles */
    .workshop-dark-mode-toggle .nav-link {
        padding: 0.5rem 0.75rem !important;
        cursor: pointer;
    }
    
    .workshop-dark-mode-toggle .nav-link:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 4px;
    }
    
    .dark-mode-icon {
        transition: all 0.3s ease;
    }
    
    /* RTL support for dark mode toggle */
    [dir="rtl"] .workshop-dark-mode-toggle {
        margin-left: 0;
        margin-right: auto;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .workshop-dark-mode-toggle {
            order: -1;
        }
    }
`;

// Inject CSS immediately
const styleSheet = document.createElement('style');
styleSheet.textContent = darkModeCSS;
document.head.appendChild(styleSheet); 