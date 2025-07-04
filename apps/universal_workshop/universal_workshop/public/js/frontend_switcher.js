/**
 * Frontend Switcher - Universal Workshop ERP
 * Handles progressive migration between traditional Frappe frontend and Frontend V2
 */

class FrontendSwitcher {
    constructor() {
        this.currentPreference = 'traditional';
        this.v2Enabled = false;
        this.migrationInProgress = false;
        this.syncQueue = [];
        
        this.init();
    }
    
    async init() {
        try {
            await this.loadUserPreference();
            await this.checkV2Availability();
            this.setupEventListeners();
            this.renderSwitcher();
            
            // Auto-redirect to V2 if user preference is set
            if (this.currentPreference === 'v2' && this.v2Enabled) {
                this.showV2MigrationDialog();
            }
        } catch (error) {
            console.error('Frontend Switcher initialization failed:', error);
        }
    }
    
    async loadUserPreference() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.api.frontend_bridge.get_frontend_preference'
            });
            
            if (response.message) {
                this.currentPreference = response.message.frontend_preference;
                this.v2Enabled = response.message.v2_enabled;
            }
        } catch (error) {
            console.error('Failed to load user preference:', error);
        }
    }
    
    async checkV2Availability() {
        try {
            const response = await frappe.call({
                method: 'universal_workshop.api.frontend_bridge.get_migration_status'
            });
            
            if (response.message) {
                this.v2Enabled = response.message.frontend_v2_enabled;
                this.migrationStatus = response.message;
            }
        } catch (error) {
            console.error('Failed to check V2 availability:', error);
        }
    }
    
    setupEventListeners() {
        // Listen for frontend preference changes
        $(document).on('frontend_preference_changed', (event, preference) => {
            this.currentPreference = preference;
            this.updateSwitcherUI();
        });
        
        // Listen for V2 feature flag changes
        $(document).on('v2_feature_flag_changed', (event, enabled) => {
            this.v2Enabled = enabled;
            this.updateSwitcherUI();
        });
    }
    
    renderSwitcher() {
        if (!this.v2Enabled) {
            return; // Don't show switcher if V2 is not enabled
        }
        
        const switcherHtml = `
            <div class="frontend-switcher" id="frontend-switcher">
                <div class="switcher-container">
                    <span class="switcher-label">${__('Interface')}</span>
                    <div class="switcher-toggle">
                        <button class="switcher-btn ${this.currentPreference === 'traditional' ? 'active' : ''}" 
                                data-preference="traditional">
                            <i class="fa fa-desktop"></i>
                            ${__('Traditional')}
                        </button>
                        <button class="switcher-btn ${this.currentPreference === 'v2' ? 'active' : ''}" 
                                data-preference="v2">
                            <i class="fa fa-mobile"></i>
                            ${__('Modern')}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add switcher to navbar
        if ($('.navbar-right .dropdown').length > 0) {
            $('.navbar-right').prepend(switcherHtml);
        } else {
            $('.navbar-right').append(switcherHtml);
        }
        
        // Add click handlers
        $('.frontend-switcher .switcher-btn').on('click', (event) => {
            const preference = $(event.currentTarget).data('preference');
            this.switchFrontend(preference);
        });
        
        this.addSwitcherStyles();
    }
    
    async switchFrontend(preference) {
        if (preference === this.currentPreference) {
            return;
        }
        
        try {
            // Show loading state
            this.showSwitchingState();
            
            if (preference === 'v2') {
                await this.migrateToV2();
            } else {
                await this.migrateToTraditional();
            }
            
            // Update preference
            await this.updateUserPreference(preference);
            
            this.currentPreference = preference;
            this.updateSwitcherUI();
            
            // Hide loading state
            this.hideSwitchingState();
            
            frappe.show_alert({
                message: __('Frontend switched successfully'),
                indicator: 'green'
            });
            
        } catch (error) {
            console.error('Frontend switch failed:', error);
            this.hideSwitchingState();
            
            frappe.show_alert({
                message: __('Failed to switch frontend: {0}', [error.message]),
                indicator: 'red'
            });
        }
    }
    
    async migrateToV2() {
        // Check if V2 assets are available
        const v2Config = await this.getV2Config();
        
        // Create V2 session
        const sessionData = await this.createV2Session();
        
        // Show migration confirmation dialog
        const confirmed = await this.showV2MigrationDialog();
        
        if (!confirmed) {
            throw new Error('Migration cancelled by user');
        }
        
        // Redirect to V2 interface
        this.redirectToV2(sessionData, v2Config);
    }
    
    async migrateToTraditional() {
        // Simply reload the current page to return to traditional interface
        window.location.reload();
    }
    
    async getV2Config() {
        const response = await frappe.call({
            method: 'universal_workshop.api.frontend_bridge.get_v2_config'
        });
        
        if (!response.message) {
            throw new Error('Failed to get V2 configuration');
        }
        
        return response.message;
    }
    
    async createV2Session() {
        const response = await frappe.call({
            method: 'universal_workshop.api.frontend_bridge.create_v2_user_session'
        });
        
        if (!response.message) {
            throw new Error('Failed to create V2 session');
        }
        
        return response.message;
    }
    
    async updateUserPreference(preference) {
        const response = await frappe.call({
            method: 'universal_workshop.api.frontend_bridge.set_frontend_preference',
            args: { frontend: preference }
        });
        
        if (!response.message || !response.message.updated) {
            throw new Error('Failed to update user preference');
        }
    }
    
    redirectToV2(sessionData, v2Config) {
        // Store session data for V2
        localStorage.setItem('v2_session', JSON.stringify(sessionData));
        localStorage.setItem('v2_config', JSON.stringify(v2Config));
        
        // Redirect to V2 interface
        const v2Url = '/app/universal-workshop-v2';
        window.location.href = v2Url;
    }
    
    showV2MigrationDialog() {
        return new Promise((resolve) => {
            const dialog = new frappe.ui.Dialog({
                title: __('Switch to Modern Interface'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'migration_info',
                        options: `
                            <div class="migration-info">
                                <h4>${__('Enhanced Features in Modern Interface')}</h4>
                                <ul>
                                    <li><i class="fa fa-mobile text-success"></i> ${__('Mobile-optimized design')}</li>
                                    <li><i class="fa fa-wifi text-success"></i> ${__('Offline support')}</li>
                                    <li><i class="fa fa-bell text-success"></i> ${__('Push notifications')}</li>
                                    <li><i class="fa fa-sync text-success"></i> ${__('Real-time synchronization')}</li>
                                    <li><i class="fa fa-language text-success"></i> ${__('Enhanced Arabic support')}</li>
                                </ul>
                                <div class="alert alert-info">
                                    <i class="fa fa-info-circle"></i>
                                    ${__('You can switch back to the traditional interface anytime.')}
                                </div>
                            </div>
                        `
                    }
                ],
                primary_action_label: __('Switch to Modern'),
                primary_action: () => {
                    dialog.hide();
                    resolve(true);
                },
                secondary_action_label: __('Stay Traditional'),
                secondary_action: () => {
                    dialog.hide();
                    resolve(false);
                }
            });
            
            dialog.show();
        });
    }
    
    showSwitchingState() {
        $('.frontend-switcher').addClass('switching');
        $('.switcher-btn').prop('disabled', true);
        
        frappe.freeze_message = __('Switching interface...');
        frappe.freeze();
    }
    
    hideSwitchingState() {
        $('.frontend-switcher').removeClass('switching');
        $('.switcher-btn').prop('disabled', false);
        frappe.unfreeze();
    }
    
    updateSwitcherUI() {
        $('.switcher-btn').removeClass('active');
        $(`.switcher-btn[data-preference="${this.currentPreference}"]`).addClass('active');
    }
    
    addSwitcherStyles() {
        const styles = `
            <style>
                .frontend-switcher {
                    margin-right: 15px;
                    display: inline-block;
                }
                
                .switcher-container {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .switcher-label {
                    font-size: 12px;
                    color: #8d99a6;
                    font-weight: 500;
                }
                
                .switcher-toggle {
                    display: flex;
                    border: 1px solid #d1d8dd;
                    border-radius: 4px;
                    overflow: hidden;
                    background: white;
                }
                
                .switcher-btn {
                    padding: 6px 12px;
                    border: none;
                    background: transparent;
                    font-size: 11px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    transition: all 0.2s ease;
                    color: #8d99a6;
                }
                
                .switcher-btn:hover {
                    background: #f8f9fa;
                    color: #495057;
                }
                
                .switcher-btn.active {
                    background: #007bff;
                    color: white;
                }
                
                .switcher-btn i {
                    font-size: 10px;
                }
                
                .frontend-switcher.switching .switcher-btn {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                
                .migration-info ul {
                    list-style: none;
                    padding: 0;
                }
                
                .migration-info li {
                    padding: 8px 0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .migration-info li i {
                    width: 16px;
                    text-align: center;
                }
                
                /* Arabic RTL support */
                [dir="rtl"] .frontend-switcher {
                    margin-left: 15px;
                    margin-right: 0;
                }
                
                [dir="rtl"] .switcher-container {
                    flex-direction: row-reverse;
                }
            </style>
        `;
        
        if (!$('#frontend-switcher-styles').length) {
            $('head').append(styles.replace('<style>', '<style id="frontend-switcher-styles">'));
        }
    }
}

// Initialize frontend switcher when page loads
$(document).ready(() => {
    // Only initialize on main app pages, not on login/setup pages
    if (window.location.pathname.startsWith('/app') && !window.location.pathname.includes('/setup')) {
        window.frontendSwitcher = new FrontendSwitcher();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FrontendSwitcher;
} 