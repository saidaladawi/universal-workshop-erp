/**
 * Universal Workshop ERP - Session Management Frontend
 * Enhanced session handling with Arabic interface support and security features
 */

class UniversalWorkshopSessionManager {
    constructor() {
        this.sessionCheckInterval = 5 * 60 * 1000; // 5 minutes
        this.warningTime = 5 * 60 * 1000; // 5 minutes before expiry
        this.deviceFingerprint = this.generateDeviceFingerprint();

        this.init();
    }

    init() {
        // Start periodic session validation
        this.startSessionMonitoring();

        // Set up session activity tracking
        this.setupActivityTracking();

        // Handle page visibility changes
        this.setupVisibilityTracking();
    }

    generateDeviceFingerprint() {
        /**
         * Generate device fingerprint for security validation
         */
        const fingerprint = {
            user_agent: navigator.userAgent,
            accept_language: navigator.language || navigator.languages.join(','),
            screen_resolution: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            platform: navigator.platform
        };

        return btoa(JSON.stringify(fingerprint)).slice(0, 32);
    }

    startSessionMonitoring() {
        /**
         * Start monitoring session validity
         */
        setInterval(() => {
            this.validateCurrentSession();
        }, this.sessionCheckInterval);

        // Initial check
        this.validateCurrentSession();
    }

    validateCurrentSession() {
        /**
         * Validate current session with enhanced security
         */
        if (frappe.session.user === 'Guest') {
            return;
        }

        frappe.call({
            method: 'universal_workshop.session_management.get_current_session_info',
            callback: (r) => {
                if (r.message && r.message.error) {
                    this.handleSessionExpired();
                } else if (r.message) {
                    this.updateSessionInfo(r.message);
                }
            },
            error: () => {
                this.handleSessionError();
            }
        });
    }

    updateSessionInfo(sessionInfo) {
        /**
         * Update UI with current session information
         */
        // Store session info for display
        this.currentSession = sessionInfo;

        // Check if session is near expiry
        this.checkSessionExpiry(sessionInfo);
    }

    checkSessionExpiry(sessionInfo) {
        /**
         * Check if session is near expiry and show warning
         */
        const lastActivity = new Date(sessionInfo.last_activity);
        const now = new Date();
        const timeSinceActivity = now - lastActivity;

        // Assuming 4 hour session timeout (240 minutes)
        const sessionTimeout = 240 * 60 * 1000;
        const timeUntilExpiry = sessionTimeout - timeSinceActivity;

        if (timeUntilExpiry <= this.warningTime && timeUntilExpiry > 0) {
            this.showSessionWarning(Math.floor(timeUntilExpiry / 60000)); // minutes
        }
    }

    showSessionWarning(minutesLeft) {
        /**
         * Show session expiry warning dialog
         */
        const isArabic = frappe.boot.lang === 'ar';

        const dialog = new frappe.ui.Dialog({
            title: isArabic ? 'تحذير انتهاء الجلسة' : 'Session Expiry Warning',
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'warning_message',
                    options: `
                        <div class="session-warning ${isArabic ? 'rtl' : ''}">
                            <div class="alert alert-warning">
                                <i class="fa fa-clock-o"></i>
                                ${isArabic
                            ? `ستنتهي جلستك خلال ${minutesLeft} دقيقة. هل تريد تمديد الجلسة؟`
                            : `Your session will expire in ${minutesLeft} minutes. Would you like to extend your session?`
                        }
                            </div>
                        </div>
                    `
                }
            ],
            primary_action_label: isArabic ? 'تمديد الجلسة' : 'Extend Session',
            primary_action: () => {
                this.extendSession();
                dialog.hide();
            },
            secondary_action_label: isArabic ? 'تسجيل الخروج' : 'Logout',
            secondary_action: () => {
                this.logout();
                dialog.hide();
            }
        });

        dialog.show();
    }

    extendSession() {
        /**
         * Extend current session by making an API call
         */
        frappe.call({
            method: 'frappe.auth.get_logged_user',
            callback: (r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: frappe.boot.lang === 'ar'
                            ? 'تم تمديد الجلسة بنجاح'
                            : 'Session extended successfully',
                        indicator: 'green'
                    });
                }
            }
        });
    }

    handleSessionExpired() {
        /**
         * Handle expired session
         */
        const isArabic = frappe.boot.lang === 'ar';

        frappe.msgprint({
            title: isArabic ? 'انتهت الجلسة' : 'Session Expired',
            message: isArabic
                ? 'انتهت جلستك. سيتم إعادة توجيهك إلى صفحة تسجيل الدخول.'
                : 'Your session has expired. You will be redirected to the login page.',
            indicator: 'red'
        });

        setTimeout(() => {
            this.logout();
        }, 3000);
    }

    handleSessionError() {
        /**
         * Handle session validation errors
         */
        console.warn('Session validation failed');
    }

    logout() {
        /**
         * Perform logout
         */
        frappe.app.logout();
    }

    setupActivityTracking() {
        /**
         * Track user activity to extend session
         */
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

        events.forEach(event => {
            document.addEventListener(event, this.debounce(() => {
                this.recordActivity();
            }, 30000)); // Record activity at most once per 30 seconds
        });
    }

    recordActivity() {
        /**
         * Record user activity (extends session automatically)
         */
        if (frappe.session.user !== 'Guest') {
            // Activity is automatically recorded by ERPNext session update
        }
    }

    setupVisibilityTracking() {
        /**
         * Handle page visibility changes
         */
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                // Page became visible, validate session
                this.validateCurrentSession();
            }
        });
    }

    // Utility methods
    debounce(func, wait) {
        /**
         * Debounce function execution
         */
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

// Initialize session management when DOM is ready
$(document).ready(() => {
    if (frappe.session && frappe.session.user !== 'Guest') {
        window.universalWorkshopSessionManager = new UniversalWorkshopSessionManager();
    }
});

// Export for use in other modules
window.UniversalWorkshopSessionManager = UniversalWorkshopSessionManager;
