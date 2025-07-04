/**
 * Universal Workshop ERP - Dynamic RTL & Branding System
 * Cross-browser compatible RTL support with dynamic visual identity
 */

class WorkshopRTLManager {
	constructor() {
		this.isRTL = false;
		this.currentLanguage = 'en';
		this.brandingConfig = {};
		this.observers = [];

		this.init();
	}

	/**
	 * Initialize the RTL manager
	 */
	init() {
		this.detectLanguage();
		this.loadBrandingConfig();
		this.setupEventListeners();
		this.applyRTLSupport();
		this.enhanceCrossBrowserCompatibility();

		console.log('🌐 Workshop RTL Manager initialized', {
			isRTL: this.isRTL,
			language: this.currentLanguage,
			userAgent: navigator.userAgent
		});
	}

	/**
	 * Detect current language and RTL requirement
	 */
	detectLanguage() {
		// Check URL parameter
		const urlParams = new URLSearchParams(window.location.search);
		const langParam = urlParams.get('lang');

		// Check localStorage
		const storedLang = localStorage.getItem('workshop_language');

		// Check HTML lang attribute
		const htmlLang = document.documentElement.lang;

		// Check user preference
		const userLang = navigator.language || navigator.userLanguage;

		// Priority order: URL param > localStorage > HTML > browser
		this.currentLanguage = langParam || storedLang || htmlLang || userLang || 'en';

		// RTL languages
		const rtlLanguages = ['ar', 'ar-SA', 'ar-AE', 'ar-OM', 'he', 'fa', 'ur'];
		this.isRTL = rtlLanguages.some(lang => this.currentLanguage.startsWith(lang));

		// Store preference
		localStorage.setItem('workshop_language', this.currentLanguage);

		console.log('🔍 Language detected:', {
			language: this.currentLanguage,
			isRTL: this.isRTL,
			source: langParam ? 'URL' : storedLang ? 'localStorage' : 'browser'
		});
	}

	/**
	 * Load branding configuration
	 */
	async loadBrandingConfig() {
		try {
			// Try to load from API
			const response = await fetch('/api/method/universal_workshop.workshop_management.doctype.workshop_profile.workshop_profile.get_workshop_branding');
			if (response.ok) {
				this.brandingConfig = await response.json();
			}
		} catch (error) {
			console.warn('Could not load branding config from API, using defaults:', error);
		}

		// Load from localStorage as fallback
		const storedConfig = localStorage.getItem('workshop_branding_config');
		if (storedConfig && !this.brandingConfig.message) {
			try {
				this.brandingConfig = JSON.parse(storedConfig);
			} catch (error) {
				console.warn('Invalid stored branding config:', error);
			}
		}

		// Apply default config
		this.brandingConfig = {
			primary_color: '#1f4e79',
			secondary_color: '#e8f4fd',
			accent_color: '#ff6b35',
			logo_url: null,
			workshop_name: 'Universal Workshop',
			theme_mode: 'light',
			...this.brandingConfig
		};

		this.applyBrandingConfig();
	}

	/**
	 * Apply branding configuration to CSS custom properties
	 */
	applyBrandingConfig() {
		const root = document.documentElement;

		// Apply color scheme
		root.style.setProperty('--workshop-primary-color', this.brandingConfig.primary_color);
		root.style.setProperty('--workshop-secondary-color', this.brandingConfig.secondary_color);
		root.style.setProperty('--workshop-accent-color', this.brandingConfig.accent_color);

		// Apply logo if available
		if (this.brandingConfig.logo_url) {
			root.style.setProperty('--workshop-logo-url', `url("${this.brandingConfig.logo_url}")`);

			// Update all logo elements
			const logoElements = document.querySelectorAll('.workshop-dynamic-logo');
			logoElements.forEach(logo => {
				logo.src = this.brandingConfig.logo_url;
				logo.alt = this.brandingConfig.workshop_name || 'Workshop Logo';
			});
		}

		// Apply theme mode
		document.body.classList.toggle('workshop-theme-dark', this.brandingConfig.theme_mode === 'dark');
		document.body.classList.toggle('workshop-theme-light', this.brandingConfig.theme_mode === 'light');

		console.log('🎨 Branding config applied:', this.brandingConfig);
	}

	/**
	 * Setup event listeners
	 */
	setupEventListeners() {
		// Language change listener
		document.addEventListener('languageChange', (event) => {
			this.handleLanguageChange(event.detail.language);
		});

		// Theme change listener
		document.addEventListener('themeChange', (event) => {
			this.handleThemeChange(event.detail.theme);
		});

		// Branding update listener
		document.addEventListener('brandingUpdate', (event) => {
			this.handleBrandingUpdate(event.detail);
		});

		// Window resize for responsive RTL
		window.addEventListener('resize', this.debounce(() => {
			this.handleResize();
		}, 250));

		// DOM mutation observer for dynamic content
		this.setupMutationObserver();
	}

	/**
	 * Apply RTL support to the page
	 */
	applyRTLSupport() {
		if (this.isRTL) {
			// Set HTML direction
			document.documentElement.dir = 'rtl';
			document.documentElement.lang = this.currentLanguage;

			// Add RTL class to body
			document.body.classList.add('rtl');

			// Load Arabic fonts if needed
			this.loadArabicFonts();

			// Apply RTL specific styles
			this.applyRTLStyles();

			// Fix form directions
			this.fixFormDirections();

			// Fix navigation
			this.fixNavigation();

			// Fix tables
			this.fixTables();

			console.log('📐 RTL layout applied');
		} else {
			// Ensure LTR for non-RTL languages
			document.documentElement.dir = 'ltr';
			document.body.classList.remove('rtl');
		}
	}

	/**
	 * Load Arabic fonts dynamically
	 */
	loadArabicFonts() {
		const fontLinks = [
			'https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300;400;500;600;700&display=swap',
			'https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700&display=swap'
		];

		fontLinks.forEach(href => {
			if (!document.querySelector(`link[href="${href}"]`)) {
				const link = document.createElement('link');
				link.rel = 'stylesheet';
				link.href = href;
				link.crossOrigin = 'anonymous';
				document.head.appendChild(link);
			}
		});

		console.log('🔤 Arabic fonts loaded');
	}

	/**
	 * Apply RTL specific styles
	 */
	applyRTLStyles() {
		// Ensure RTL CSS is loaded
		const rtlCssPath = '/assets/universal_workshop/css/arabic-rtl.css';
		if (!document.querySelector(`link[href="${rtlCssPath}"]`)) {
			const link = document.createElement('link');
			link.rel = 'stylesheet';
			link.href = rtlCssPath;
			document.head.appendChild(link);
		}

		// Apply CSS custom properties for RTL
		const root = document.documentElement;
		root.style.setProperty('--direction-start', 'right');
		root.style.setProperty('--direction-end', 'left');
		root.style.setProperty('--transform-rotate-positive', 'rotate(180deg)');
		root.style.setProperty('--transform-rotate-negative', 'rotate(-180deg)');
	}

	/**
	 * Fix form directions for RTL
	 */
	fixFormDirections() {
		const forms = document.querySelectorAll('form, .form-group, .input-group');
		forms.forEach(form => {
			if (this.isRTL) {
				form.classList.add('rtl-form');
			}
		});

		const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea, select');
		inputs.forEach(input => {
			if (this.isRTL) {
				input.style.textAlign = 'right';
				input.style.direction = 'rtl';
				input.classList.add('rtl-input');
			}
		});
	}

	/**
	 * Fix navigation for RTL
	 */
	fixNavigation() {
		const navbars = document.querySelectorAll('.navbar, .nav, .navigation');
		navbars.forEach(navbar => {
			if (this.isRTL) {
				navbar.classList.add('rtl-nav');
			}
		});

		const dropdowns = document.querySelectorAll('.dropdown-menu');
		dropdowns.forEach(dropdown => {
			if (this.isRTL) {
				dropdown.style.right = '0';
				dropdown.style.left = 'auto';
				dropdown.style.textAlign = 'right';
			}
		});
	}

	/**
	 * Fix tables for RTL
	 */
	fixTables() {
		const tables = document.querySelectorAll('table');
		tables.forEach(table => {
			if (this.isRTL) {
				table.classList.add('rtl-table');
				table.style.direction = 'rtl';

				const cells = table.querySelectorAll('th, td');
				cells.forEach(cell => {
					cell.style.textAlign = 'right';
				});
			}
		});
	}

	/**
	 * Enhance cross-browser compatibility
	 */
	enhanceCrossBrowserCompatibility() {
		// Detect browser
		const browser = this.detectBrowser();
		document.body.classList.add(`browser-${browser}`);

		// Apply browser-specific fixes
		this.applyBrowserFixes(browser);

		console.log('🌐 Browser detected and optimized:', browser);
	}

	/**
	 * Detect browser type
	 */
	detectBrowser() {
		const userAgent = navigator.userAgent.toLowerCase();

		if (userAgent.includes('chrome') && !userAgent.includes('edge')) {
			return 'chrome';
		} else if (userAgent.includes('firefox')) {
			return 'firefox';
		} else if (userAgent.includes('edge')) {
			return 'edge';
		} else if (userAgent.includes('safari') && !userAgent.includes('chrome')) {
			return 'safari';
		} else {
			return 'unknown';
		}
	}

	/**
	 * Apply browser-specific fixes
	 */
	applyBrowserFixes(browser) {
		switch (browser) {
			case 'firefox':
				this.applyFirefoxFixes();
				break;
			case 'safari':
				this.applySafariFixes();
				break;
			case 'edge':
				this.applyEdgeFixes();
				break;
			case 'chrome':
			default:
				this.applyChromeFixes();
				break;
		}
	}

	/**
	 * Firefox-specific fixes
	 */
	applyFirefoxFixes() {
		const style = document.createElement('style');
		style.textContent = `
            [dir="rtl"] .firefox-rtl-fix {
                text-align: -moz-right;
            }
            [dir="rtl"] .form-control {
                -moz-appearance: none;
                background-position: left 0.75rem center;
            }
        `;
		document.head.appendChild(style);
	}

	/**
	 * Safari-specific fixes
	 */
	applySafariFixes() {
		const style = document.createElement('style');
		style.textContent = `
            [dir="rtl"] .safari-rtl-fix {
                -webkit-writing-mode: horizontal-tb;
                writing-mode: horizontal-tb;
                direction: rtl;
                text-align: right;
            }
            [dir="rtl"] .form-control {
                -webkit-appearance: none;
                background-position: left 0.75rem center;
            }
        `;
		document.head.appendChild(style);
	}

	/**
	 * Edge-specific fixes
	 */
	applyEdgeFixes() {
		const style = document.createElement('style');
		style.textContent = `
            [dir="rtl"] .edge-rtl-fix {
                -ms-writing-mode: lr-tb;
                writing-mode: horizontal-tb;
                direction: rtl;
                text-align: right;
            }
        `;
		document.head.appendChild(style);
	}

	/**
	 * Chrome-specific optimizations
	 */
	applyChromeFixes() {
		const style = document.createElement('style');
		style.textContent = `
            [dir="rtl"] .chrome-rtl-optimization {
                -webkit-font-feature-settings: "liga" 1, "kern" 1;
                font-feature-settings: "liga" 1, "kern" 1;
                text-rendering: optimizeLegibility;
            }
        `;
		document.head.appendChild(style);
	}

	/**
	 * Setup mutation observer for dynamic content
	 */
	setupMutationObserver() {
		const observer = new MutationObserver((mutations) => {
			mutations.forEach((mutation) => {
				if (mutation.type === 'childList') {
					mutation.addedNodes.forEach((node) => {
						if (node.nodeType === Node.ELEMENT_NODE) {
							this.processNewElement(node);
						}
					});
				}
			});
		});

		observer.observe(document.body, {
			childList: true,
			subtree: true
		});

		this.observers.push(observer);
	}

	/**
	 * Process newly added elements
	 */
	processNewElement(element) {
		if (this.isRTL) {
			// Apply RTL to forms
			if (element.matches('form, .form-group, .input-group')) {
				element.classList.add('rtl-form');
			}

			// Apply RTL to inputs
			if (element.matches('input[type="text"], input[type="email"], input[type="password"], textarea, select')) {
				element.style.textAlign = 'right';
				element.style.direction = 'rtl';
				element.classList.add('rtl-input');
			}

			// Apply RTL to tables
			if (element.matches('table')) {
				element.classList.add('rtl-table');
				element.style.direction = 'rtl';
			}

			// Apply branding to logos
			if (element.matches('.workshop-dynamic-logo') && this.brandingConfig.logo_url) {
				element.src = this.brandingConfig.logo_url;
				element.alt = this.brandingConfig.workshop_name || 'Workshop Logo';
			}
		}
	}

	/**
	 * Handle language change
	 */
	handleLanguageChange(newLanguage) {
		this.currentLanguage = newLanguage;
		localStorage.setItem('workshop_language', newLanguage);

		// Update RTL status
		const rtlLanguages = ['ar', 'ar-SA', 'ar-AE', 'ar-OM', 'he', 'fa', 'ur'];
		const wasRTL = this.isRTL;
		this.isRTL = rtlLanguages.some(lang => newLanguage.startsWith(lang));

		// Reapply RTL if changed
		if (wasRTL !== this.isRTL) {
			this.applyRTLSupport();
		}

		// Update HTML lang
		document.documentElement.lang = newLanguage;

		console.log('🔄 Language changed:', { from: wasRTL ? 'RTL' : 'LTR', to: this.isRTL ? 'RTL' : 'LTR', language: newLanguage });
	}

	/**
	 * Handle theme change
	 */
	handleThemeChange(newTheme) {
		this.brandingConfig.theme_mode = newTheme;
		localStorage.setItem('workshop_theme', newTheme);

		document.body.classList.toggle('workshop-theme-dark', newTheme === 'dark');
		document.body.classList.toggle('workshop-theme-light', newTheme === 'light');

		console.log('🎨 Theme changed:', newTheme);
	}

	/**
	 * Handle branding update
	 */
	handleBrandingUpdate(newBranding) {
		this.brandingConfig = { ...this.brandingConfig, ...newBranding };
		localStorage.setItem('workshop_branding_config', JSON.stringify(this.brandingConfig));

		this.applyBrandingConfig();

		console.log('🖌️ Branding updated:', newBranding);
	}

	/**
	 * Handle window resize
	 */
	handleResize() {
		// Recalculate RTL layouts for responsive design
		if (this.isRTL) {
			this.fixResponsiveRTL();
		}
	}

	/**
	 * Fix responsive RTL layouts
	 */
	fixResponsiveRTL() {
		const viewportWidth = window.innerWidth;

		// Apply mobile-specific RTL fixes
		if (viewportWidth < 768) {
			document.body.classList.add('rtl-mobile');
		} else {
			document.body.classList.remove('rtl-mobile');
		}

		// Apply tablet-specific RTL fixes
		if (viewportWidth >= 768 && viewportWidth < 1024) {
			document.body.classList.add('rtl-tablet');
		} else {
			document.body.classList.remove('rtl-tablet');
		}
	}

	/**
	 * Public API methods
	 */

	/**
	 * Switch language
	 */
	switchLanguage(language) {
		const event = new CustomEvent('languageChange', {
			detail: { language: language }
		});
		document.dispatchEvent(event);
	}

	/**
	 * Switch theme
	 */
	switchTheme(theme) {
		const event = new CustomEvent('themeChange', {
			detail: { theme: theme }
		});
		document.dispatchEvent(event);
	}

	/**
	 * Update branding
	 */
	updateBranding(branding) {
		const event = new CustomEvent('brandingUpdate', {
			detail: branding
		});
		document.dispatchEvent(event);
	}

	/**
	 * Get current configuration
	 */
	getConfiguration() {
		return {
			language: this.currentLanguage,
			isRTL: this.isRTL,
			branding: this.brandingConfig,
			browser: this.detectBrowser()
		};
	}

	/**
	 * Utility functions
	 */

	/**
	 * Debounce function calls
	 */
	debounce(func, wait) {
		let timeout;
		return function executedFunction(...args) {
			const later = () => {
				clearTimeout(timeout);
				func(...args);
			};
			clearTimeout(timeout);
			timeout = setTimeout(later, wait);
		};
	}

	/**
	 * Cleanup method
	 */
	destroy() {
		this.observers.forEach(observer => observer.disconnect());
		this.observers = [];

		console.log('🧹 Workshop RTL Manager destroyed');
	}

	/**
	 * Set RTL direction manually
	 * @param {boolean} isRTL - Whether to enable RTL
	 */
	setRTL(isRTL) {
		this.isRTL = isRTL;
		this.applyRTLSupport();
		console.log(`🔄 RTL mode ${isRTL ? 'enabled' : 'disabled'}`);
	}

	/**
	 * Set language and update RTL accordingly
	 * @param {string} language - Language code (e.g., 'ar', 'en')
	 */
	setLanguage(language) {
		this.currentLanguage = language;

		// Update RTL based on language
		const rtlLanguages = ['ar', 'ar-SA', 'ar-AE', 'ar-OM', 'he', 'fa', 'ur'];
		this.isRTL = rtlLanguages.some(lang => language.startsWith(lang));

		// Store preference
		localStorage.setItem('workshop_language', language);

		// Apply changes
		this.applyRTLSupport();
		this.updateLanguageAttributes();

		console.log(`🌍 Language set to: ${language} (RTL: ${this.isRTL})`);
	}

	/**
	 * Update language attributes on document
	 */
	updateLanguageAttributes() {
		document.documentElement.lang = this.currentLanguage;
		document.documentElement.dir = this.isRTL ? 'rtl' : 'ltr';

		// Update body classes
		document.body.classList.toggle('rtl-layout', this.isRTL);
		document.body.classList.toggle('ltr-layout', !this.isRTL);
	}

	/**
	 * Enhance authentication UI specifically
	 */
	enhanceAuthenticationUI() {
		// Enhance login forms
		const loginForms = document.querySelectorAll('.login-form, .auth-form, [class*="login"], [class*="auth"]');
		loginForms.forEach(form => {
			form.classList.add('workshop-enhanced-auth');

			// RTL input handling
			if (this.isRTL) {
				const inputs = form.querySelectorAll('input, textarea, select');
				inputs.forEach(input => {
					input.style.textAlign = 'right';
					input.style.direction = 'rtl';
				});
			}

			// Add brand styling
			form.classList.add('workshop-brand');
		});

		// Enhance authentication buttons
		const authButtons = document.querySelectorAll('.btn-login, .btn-signin, .auth-button, [class*="login-btn"]');
		authButtons.forEach(btn => {
			btn.classList.add('workshop-brand-primary');
		});

		// Logo enhancement for auth pages
		this.enhanceAuthenticationLogo();

		console.log('🔐 Authentication UI enhanced for RTL/branding');
	}

	/**
	 * Enhance logo display on authentication pages
	 */
	enhanceAuthenticationLogo() {
		const logoContainers = document.querySelectorAll('.login-logo, .auth-logo, .brand-logo, [class*="logo"]');
		logoContainers.forEach(container => {
			if (this.brandingConfig.logo_url) {
				// Create or update logo image
				let logoImg = container.querySelector('img');
				if (!logoImg) {
					logoImg = document.createElement('img');
					container.appendChild(logoImg);
				}

				logoImg.src = this.brandingConfig.logo_url;
				logoImg.alt = this.brandingConfig.workshop_name || 'Universal Workshop';
				logoImg.style.maxHeight = '60px';
				logoImg.style.maxWidth = '200px';
				logoImg.classList.add('workshop-logo-enhanced');
			}
		});
	}
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
	if (typeof window.workshopRTLManager === 'undefined') {
		window.workshopRTLManager = new WorkshopRTLManager();

		// Make it globally accessible
		window.switchLanguage = (lang) => window.workshopRTLManager.switchLanguage(lang);
		window.switchTheme = (theme) => window.workshopRTLManager.switchTheme(theme);
		window.updateBranding = (branding) => window.workshopRTLManager.updateBranding(branding);
	}
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
	module.exports = WorkshopRTLManager;
}
