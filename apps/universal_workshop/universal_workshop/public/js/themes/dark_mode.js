/**
 * Universal Workshop ERP - Dark Mode JavaScript
 * Complete dark mode functionality with user preferences and system integration
 */

// Dark Mode Manager Class
class DarkModeManager {
    constructor() {
        this.currentTheme = this.getUserPreference();
        this.systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.init();
    }

    init() {
        // Apply initial theme
        this.applyTheme(this.currentTheme);
        
        // Create toggle button
        this.createToggleButton();
        
        // Listen for system theme changes
        this.listenForSystemChanges();
        
        // Listen for user preference changes from server
        this.listenForUserChanges();
        
        // Add transition classes for smooth theme switching
        this.addTransitionClasses();
        
        console.log('🌙 Dark Mode Manager initialized');
    }

    getUserPreference() {
        // Check localStorage first
        const localPref = localStorage.getItem('dark-mode-preference');
        if (localPref) {
            return localPref;
        }

        // Check user profile if available
        if (frappe && frappe.user && frappe.user.defaults) {
            const userPref = frappe.user.defaults.dark_mode_preference;
            if (userPref) {
                return userPref;
            }
        }

        // Default to system preference
        return 'system';
    }

    setUserPreference(preference) {
        // Save to localStorage
        localStorage.setItem('dark-mode-preference', preference);
        
        // Save to user profile if frappe is available
        if (frappe && frappe.call) {
            frappe.call({
                method: 'universal_workshop.dark_mode.fixtures.set_user_dark_mode_preference',
                args: {
                    preference: preference,
                    auto_mode: preference === 'system' ? 1 : 0
                },
                callback: (response) => {
                    if (response.message && response.message.status === 'success') {
                        console.log('✅ Dark mode preference saved to server');
                    }
                },
                error: (error) => {
                    console.warn('⚠️ Could not save dark mode preference to server:', error);
                }
            });
        }
    }

    getCurrentTheme() {
        if (this.currentTheme === 'system') {
            return this.systemPrefersDark ? 'dark' : 'light';
        }
        return this.currentTheme;
    }

    applyTheme(theme) {
        const actualTheme = theme === 'system' ? 
            (this.systemPrefersDark ? 'dark' : 'light') : theme;
        
        // Apply to document body
        document.body.setAttribute('data-theme', actualTheme);
        
        // Apply to html element for complete coverage
        document.documentElement.setAttribute('data-theme', actualTheme);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(actualTheme);
        
        // Update toggle button
        this.updateToggleButton(actualTheme);
        
        // Dispatch custom event for other components
        this.dispatchThemeChangeEvent(actualTheme);
        
        console.log(`🎨 Theme applied: ${actualTheme}`);
    }

    toggleTheme() {
        const currentActualTheme = this.getCurrentTheme();
        const newTheme = currentActualTheme === 'dark' ? 'light' : 'dark';
        
        this.currentTheme = newTheme;
        this.setUserPreference(newTheme);
        this.applyTheme(newTheme);
        
        // Show notification
        this.showThemeChangeNotification(newTheme);
    }

    cycleTheme() {
        // Cycle through: light -> dark -> system -> light
        switch (this.currentTheme) {
            case 'light':
                this.currentTheme = 'dark';
                break;
            case 'dark':
                this.currentTheme = 'system';
                break;
            case 'system':
            default:
                this.currentTheme = 'light';
                break;
        }
        
        this.setUserPreference(this.currentTheme);
        this.applyTheme(this.currentTheme);
        this.showThemeChangeNotification(this.currentTheme);
    }

    createToggleButton() {
        // Remove existing toggle if present
        const existingToggle = document.getElementById('dark-mode-toggle');
        if (existingToggle) {
            existingToggle.remove();
        }

        // Create toggle button
        const toggle = document.createElement('button');
        toggle.id = 'dark-mode-toggle';
        toggle.className = 'dark-mode-toggle';
        toggle.innerHTML = this.getToggleIcon(this.getCurrentTheme());
        toggle.title = 'Toggle Dark Mode (Click for on/off, Right-click for options)';
        
        // Add click handler
        toggle.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleTheme();
        });
        
        // Add right-click handler for cycling
        toggle.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.cycleTheme();
        });
        
        // Add to document
        document.body.appendChild(toggle);
    }

    getToggleIcon(theme) {
        const icons = {
            light: '<i class="fa fa-sun-o" title="Light Mode"></i>',
            dark: '<i class="fa fa-moon-o" title="Dark Mode"></i>',
            system: '<i class="fa fa-adjust" title="System Mode"></i>'
        };
        
        if (this.currentTheme === 'system') {
            return icons.system;
        }
        
        return icons[theme] || icons.light;
    }

    updateToggleButton(theme) {
        const toggle = document.getElementById('dark-mode-toggle');
        if (toggle) {
            toggle.innerHTML = this.getToggleIcon(theme);
        }
    }

    updateMetaThemeColor(theme) {
        let themeColorMeta = document.querySelector('meta[name="theme-color"]');
        
        if (!themeColorMeta) {
            themeColorMeta = document.createElement('meta');
            themeColorMeta.name = 'theme-color';
            document.head.appendChild(themeColorMeta);
        }
        
        themeColorMeta.content = theme === 'dark' ? '#1a1a1a' : '#ffffff';
    }

    addTransitionClasses() {
        // Add transition class to body for smooth theme switching
        document.body.classList.add('theme-transition');
        
        // Add to common elements
        const elements = document.querySelectorAll(
            '.card, .panel, .btn, .form-control, .navbar, .sidebar'
        );
        elements.forEach(el => el.classList.add('theme-transition'));
    }

    listenForSystemChanges() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        mediaQuery.addEventListener('change', (e) => {
            this.systemPrefersDark = e.matches;
            
            // Only apply if user preference is 'system'
            if (this.currentTheme === 'system') {
                this.applyTheme('system');
            }
            
            console.log(`🔄 System theme changed: ${e.matches ? 'dark' : 'light'}`);
        });
    }

    listenForUserChanges() {
        // Listen for custom events from other parts of the app
        document.addEventListener('dark-mode-preference-changed', (event) => {
            const newPreference = event.detail.preference;
            this.currentTheme = newPreference;
            this.applyTheme(newPreference);
        });
    }

    dispatchThemeChangeEvent(theme) {
        const event = new CustomEvent('theme-changed', {
            detail: {
                theme: theme,
                preference: this.currentTheme,
                systemPrefersDark: this.systemPrefersDark
            }
        });
        document.dispatchEvent(event);
    }

    showThemeChangeNotification(theme) {
        // Only show notification if frappe is available
        if (frappe && frappe.show_alert) {
            const themeNames = {
                light: 'Light Mode',
                dark: 'Dark Mode',
                system: 'System Mode'
            };
            
            const themeName = this.currentTheme === 'system' ? 
                `${themeNames.system} (${themeNames[theme]})` : 
                themeNames[this.currentTheme];
            
            frappe.show_alert({
                message: `🎨 Switched to ${themeName}`,
                indicator: 'blue'
            }, 2);
        }
    }

    // Public API methods
    setTheme(theme) {
        if (['light', 'dark', 'system'].includes(theme)) {
            this.currentTheme = theme;
            this.setUserPreference(theme);
            this.applyTheme(theme);
        }
    }

    getTheme() {
        return {
            preference: this.currentTheme,
            actual: this.getCurrentTheme(),
            systemPrefersDark: this.systemPrefersDark
        };
    }
}

// Initialize Dark Mode when DOM is ready
let darkModeManager;

function initializeDarkMode() {
    if (!darkModeManager) {
        darkModeManager = new DarkModeManager();
        
        // Make it globally accessible
        window.darkMode = darkModeManager;
        
        // Add CSS file to head if not already present
        loadDarkModeCSS();
    }
}

function loadDarkModeCSS() {
    const cssId = 'dark-mode-css';
    
    if (!document.getElementById(cssId)) {
        const link = document.createElement('link');
        link.id = cssId;
        link.rel = 'stylesheet';
        link.type = 'text/css';
        link.href = '/assets/universal_workshop/dark_mode/dark_mode.css';
        document.head.appendChild(link);
    }
}

// Frappe integration
if (typeof frappe !== 'undefined') {
    // Initialize when Frappe is ready
    frappe.ready(() => {
        initializeDarkMode();
    });
    
    // Add to frappe namespace for easy access
    frappe.dark_mode = {
        toggle: () => darkModeManager?.toggleTheme(),
        set: (theme) => darkModeManager?.setTheme(theme),
        get: () => darkModeManager?.getTheme()
    };
} else {
    // Initialize when DOM is ready (non-Frappe environments)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeDarkMode);
    } else {
        initializeDarkMode();
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+Shift+D to toggle dark mode
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        darkModeManager?.toggleTheme();
    }
    
    // Ctrl+Shift+T to cycle themes
    if (e.ctrlKey && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        darkModeManager?.cycleTheme();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DarkModeManager, initializeDarkMode };
}