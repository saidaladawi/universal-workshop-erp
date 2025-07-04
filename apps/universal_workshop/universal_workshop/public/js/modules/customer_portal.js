/**
 * Universal Workshop Customer Portal JavaScript
 * Arabic-first design with RTL support and mobile optimization
 * Compatible with ERPNext v15 and modern browsers
 */

class CustomerPortal {
    constructor() {
        this.isArabic = document.documentElement.lang === 'ar' || document.documentElement.dir === 'rtl';
        this.isMobile = window.innerWidth <= 768;
        this.isTablet = window.innerWidth > 768 && window.innerWidth <= 1024;
        this.isTouch = 'ontouchstart' in window;

        this.translations = {};
        this.currentLanguage = this.isArabic ? 'ar' : 'en';
        this.apiEndpoints = this.initializeApiEndpoints();

        this.init();
    }

    /**
     * Initialize the portal
     */
    init() {
        this.loadTranslations();
        this.setupEventListeners();
        this.initializeComponents();
        this.setupMobileOptimizations();
        this.setupRTLSupport();
        this.initializeServiceWorker();
        this.setupOfflineSupport();

        // Initialize specific page functionality
        this.initializePage();
    }

    /**
     * Initialize API endpoints
     */
    initializeApiEndpoints() {
        return {
            dashboard: '/api/portal/dashboard-data',
            appointments: '/api/portal/appointments',
            services: '/api/portal/services',
            payments: '/api/portal/payments',
            documents: '/api/portal/documents',
            notifications: '/api/portal/notifications',
            profile: '/api/portal/profile'
        };
    }

    /**
     * Load translations for the current language
     */
    async loadTranslations() {
        try {
            const response = await fetch(`/assets/universal_workshop/translations/${this.currentLanguage}.json`);
            this.translations = await response.json();
        } catch (error) {
            console.warn('Failed to load translations:', error);
            this.translations = {};
        }
    }

    /**
     * Get translated text
     */
    _(text, context = {}) {
        let translated = this.translations[text] || text;

        // Simple template replacement
        Object.keys(context).forEach(key => {
            translated = translated.replace(`{${key}}`, context[key]);
        });

        return translated;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Language switching
        document.querySelectorAll('.language-switch button').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchLanguage(e.target.dataset.lang));
        });

        // Mobile menu toggle
        const mobileMenuBtn = document.querySelector('.mobile-menu-toggle');
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => this.toggleMobileMenu());
        }

        // Window resize handler
        window.addEventListener('resize', () => this.handleResize());

        // Touch gesture handling for mobile
        if (this.isTouch) {
            this.setupTouchGestures();
        }

        // Form submissions
        document.addEventListener('submit', (e) => this.handleFormSubmit(e));

        // Navigation clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-link') || e.target.closest('.nav-link')) {
                this.handleNavigation(e);
            }
        });

        // Real-time updates
        this.setupRealTimeUpdates();
    }

    /**
     * Switch language
     */
    async switchLanguage(lang) {
        if (lang === this.currentLanguage) return;

        this.currentLanguage = lang;
        this.isArabic = lang === 'ar';

        // Update document attributes
        document.documentElement.lang = lang;
        document.documentElement.dir = this.isArabic ? 'rtl' : 'ltr';

        // Add/remove RTL class
        document.body.classList.toggle('rtl-layout', this.isArabic);

        // Reload translations
        await this.loadTranslations();

        // Update text content
        this.updateTextContent();

        // Save preference
        localStorage.setItem('portal_language', lang);

        // Show notification
        this.showNotification(this._('Language changed successfully'), 'success');
    }

    /**
     * Update text content after language change
     */
    updateTextContent() {
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.dataset.translate;
            const translated = this._(key);

            if (element.tagName === 'INPUT' && element.type === 'submit') {
                element.value = translated;
            } else if (element.tagName === 'INPUT' && element.placeholder) {
                element.placeholder = translated;
            } else {
                element.textContent = translated;
            }
        });
    }

    /**
     * Initialize components
     */
    initializeComponents() {
        this.initializeDatePickers();
        this.initializeSearchComponents();
        this.initializeFileUpload();
        this.initializeNotifications();
        this.initializeModals();
        this.initializeTooltips();
    }

    /**
     * Initialize date pickers with Arabic support
     */
    initializeDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');

        dateInputs.forEach(input => {
            // Arabic calendar support
            if (this.isArabic) {
                input.classList.add('arabic-calendar');
            }

            // Mobile optimization
            if (this.isMobile) {
                input.classList.add('mobile-date-picker');
            }
        });
    }

    /**
     * Initialize search components
     */
    initializeSearchComponents() {
        const searchInputs = document.querySelectorAll('.search-input');

        searchInputs.forEach(input => {
            let timeout;

            input.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.performSearch(e.target.value, e.target.dataset.searchType);
                }, 300);
            });

            // Arabic text support
            if (this.isArabic) {
                input.dir = 'rtl';
            }
        });
    }

    /**
     * Initialize file upload components
     */
    initializeFileUpload() {
        const fileInputs = document.querySelectorAll('input[type="file"]');

        fileInputs.forEach(input => {
            const dropZone = input.closest('.file-drop-zone');

            if (dropZone) {
                this.setupFileDragDrop(dropZone, input);
            }

            input.addEventListener('change', (e) => this.handleFileUpload(e));
        });
    }

    /**
     * Setup file drag and drop
     */
    setupFileDragDrop(dropZone, input) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            input.files = files;
            this.handleFileUpload({ target: input });
        });
    }

    /**
     * Handle file upload
     */
    async handleFileUpload(event) {
        const files = event.target.files;
        const formData = new FormData();

        Array.from(files).forEach(file => {
            formData.append('files', file);
        });

        try {
            this.showLoading(event.target.closest('.form-group'));

            const response = await this.apiCall('/api/portal/upload', {
                method: 'POST',
                body: formData
            });

            if (response.success) {
                this.showNotification(this._('Files uploaded successfully'), 'success');
                this.updateFileList(response.files);
            } else {
                throw new Error(response.message);
            }
        } catch (error) {
            this.showNotification(this._('Upload failed: {error}', { error: error.message }), 'error');
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Initialize notifications
     */
    initializeNotifications() {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Setup notification container
        if (!document.querySelector('.notification-container')) {
            const container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.querySelector('.notification-container');
        const notification = document.createElement('div');

        notification.className = `notification notification-${type} ${this.isArabic ? 'rtl' : 'ltr'}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="notification-icon"></i>
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        container.appendChild(notification);

        // Show animation
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto hide
        const timeout = setTimeout(() => this.hideNotification(notification), duration);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            clearTimeout(timeout);
            this.hideNotification(notification);
        });
    }

    /**
     * Hide notification
     */
    hideNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }

    /**
     * Setup mobile optimizations
     */
    setupMobileOptimizations() {
        if (!this.isMobile) return;

        // Add mobile class
        document.body.classList.add('mobile-layout');

        // Setup pull to refresh
        this.setupPullToRefresh();

        // Setup touch navigation
        this.setupTouchNavigation();

        // Optimize form inputs
        this.optimizeFormsForMobile();

        // Setup viewport meta tag
        this.setupViewportMeta();
    }

    /**
     * Setup pull to refresh
     */
    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let pulling = false;

        const refreshIndicator = document.createElement('div');
        refreshIndicator.className = 'pull-to-refresh-indicator';
        refreshIndicator.innerHTML = `<div class="spinner"></div><span>${this._('Pull to refresh')}</span>`;
        document.body.insertBefore(refreshIndicator, document.body.firstChild);

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].pageY;
                pulling = true;
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (!pulling) return;

            currentY = e.touches[0].pageY;
            const diff = currentY - startY;

            if (diff > 0 && diff < 100) {
                refreshIndicator.style.transform = `translateY(${diff}px)`;
                refreshIndicator.classList.add('pulling');
            }
        });

        document.addEventListener('touchend', (e) => {
            if (!pulling) return;

            const diff = currentY - startY;

            if (diff > 80) {
                this.refreshPage();
            }

            refreshIndicator.style.transform = '';
            refreshIndicator.classList.remove('pulling');
            pulling = false;
        });
    }

    /**
     * Setup touch gestures
     */
    setupTouchGestures() {
        let touchStartX = 0;
        let touchStartY = 0;

        document.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        });

        document.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;

            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;

            // Swipe gestures
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    this.handleSwipeRight();
                } else {
                    this.handleSwipeLeft();
                }
            }
        });
    }

    /**
     * Handle swipe right (go back in RTL, forward in LTR)
     */
    handleSwipeRight() {
        if (this.isArabic) {
            this.navigateForward();
        } else {
            this.navigateBack();
        }
    }

    /**
     * Handle swipe left (go forward in RTL, back in LTR)
     */
    handleSwipeLeft() {
        if (this.isArabic) {
            this.navigateBack();
        } else {
            this.navigateForward();
        }
    }

    /**
     * Setup RTL support
     */
    setupRTLSupport() {
        if (!this.isArabic) return;

        // Add RTL class to body
        document.body.classList.add('rtl-layout');

        // Update form controls
        document.querySelectorAll('.form-control').forEach(control => {
            if (control.dataset.arabic !== 'false') {
                control.dir = 'rtl';
                control.style.textAlign = 'right';
            }
        });

        // Update navigation
        document.querySelectorAll('.nav-tabs').forEach(nav => {
            nav.style.direction = 'rtl';
        });
    }

    /**
     * Setup real-time updates
     */
    setupRealTimeUpdates() {
        // WebSocket connection for real-time updates
        if (window.WebSocket) {
            this.setupWebSocket();
        }

        // Fallback to polling
        this.setupPolling();
    }

    /**
     * Setup WebSocket connection
     */
    setupWebSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${location.host}/ws/portal`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleRealTimeUpdate(data);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                setTimeout(() => this.setupWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to setup WebSocket:', error);
        }
    }

    /**
     * Handle real-time updates
     */
    handleRealTimeUpdate(data) {
        switch (data.type) {
            case 'service_update':
                this.updateServiceStatus(data.payload);
                break;
            case 'appointment_update':
                this.updateAppointmentStatus(data.payload);
                break;
            case 'payment_update':
                this.updatePaymentStatus(data.payload);
                break;
            case 'notification':
                this.showNotification(data.payload.message, data.payload.type);
                break;
        }
    }

    /**
     * API call helper
     */
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Frappe-CSRF-Token': frappe.csrf_token
            }
        };

        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    /**
     * Show loading indicator
     */
    showLoading(element = document.body) {
        element.classList.add('loading');
    }

    /**
     * Hide loading indicator
     */
    hideLoading(element = document.body) {
        element.classList.remove('loading');
    }

    /**
     * Initialize Service Worker for PWA
     */
    async initializeServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered:', registration);
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    /**
     * Setup offline support
     */
    setupOfflineSupport() {
        window.addEventListener('online', () => {
            this.showNotification(this._('Connection restored'), 'success');
            this.syncOfflineData();
        });

        window.addEventListener('offline', () => {
            this.showNotification(this._('Connection lost. Working offline.'), 'warning');
        });
    }

    /**
     * Initialize page-specific functionality
     */
    initializePage() {
        const page = document.body.dataset.page;

        switch (page) {
            case 'dashboard':
                this.initializeDashboard();
                break;
            case 'appointments':
                this.initializeAppointments();
                break;
            case 'services':
                this.initializeServices();
                break;
            case 'payments':
                this.initializePayments();
                break;
            case 'documents':
                this.initializeDocuments();
                break;
        }
    }

    /**
     * Utility functions
     */
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    formatCurrency(amount, currency = 'OMR') {
        const formatter = new Intl.NumberFormat(this.isArabic ? 'ar-OM' : 'en-OM', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 3
        });

        return formatter.format(amount);
    }

    formatDate(date, options = {}) {
        const locale = this.isArabic ? 'ar-OM' : 'en-OM';
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };

        return new Intl.DateTimeFormat(locale, { ...defaultOptions, ...options }).format(new Date(date));
    }

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
}

// Page-specific modules
class DashboardModule {
    constructor(portal) {
        this.portal = portal;
        this.init();
    }

    init() {
        this.loadDashboardData();
        this.setupRefreshTimer();
    }

    async loadDashboardData() {
        try {
            const data = await this.portal.apiCall(this.portal.apiEndpoints.dashboard);
            this.renderDashboard(data);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }
}

// Initialize portal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.customerPortal = new CustomerPortal();
});

// Expose portal instance globally
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CustomerPortal;
} 