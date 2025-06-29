/**
 * Security Dashboard Frontend for Universal Workshop ERP
 * 
 * Provides real-time security monitoring interface with Arabic localization
 * and comprehensive security metrics visualization.
 */

class SecurityDashboard {
    constructor() {
        this.timeframe = 24; // Default 24 hours
        this.refreshInterval = 30000; // 30 seconds
        this.alertCheckInterval = 60000; // 1 minute for alerts
        this.isRTL = frappe.boot.lang === 'ar';
        this.widgets = {};
        this.alertSounds = true;

        this.init();
    }

    async init() {
        try {
            await this.createDashboardLayout();
            await this.loadInitialData();
            this.setupRealTimeUpdates();
            this.setupEventHandlers();
            this.applyRTLStyles();

            console.log('Security Dashboard initialized successfully');
        } catch (error) {
            console.error('Dashboard initialization error:', error);
            this.showError(__('Failed to initialize security dashboard'));
        }
    }

    createDashboardLayout() {
        const dashboardHtml = `
            <div class="security-dashboard ${this.isRTL ? 'rtl-layout' : ''}">
                <!-- Dashboard Header -->
                <div class="dashboard-header">
                    <div class="header-controls">
                        <h2 class="dashboard-title">
                            <i class="fa fa-shield-alt"></i>
                            ${__('Security Dashboard')}
                        </h2>
                        <div class="timeframe-selector">
                            <label>${__('Timeframe')}:</label>
                            <select id="timeframe-select" class="form-control">
                                <option value="1">${__('Last Hour')}</option>
                                <option value="6">${__('Last 6 Hours')}</option>
                                <option value="24" selected>${__('Last 24 Hours')}</option>
                                <option value="168">${__('Last Week')}</option>
                            </select>
                        </div>
                        <button id="refresh-dashboard" class="btn btn-primary">
                            <i class="fa fa-refresh"></i> ${__('Refresh')}
                        </button>
                    </div>
                    <div class="dashboard-status">
                        <span id="last-updated">${__('Loading...')}</span>
                        <div id="connection-status" class="status-indicator online">
                            <i class="fa fa-circle"></i> ${__('Online')}
                        </div>
                    </div>
                </div>

                <!-- Security Metrics Cards -->
                <div class="metrics-grid">
                    <div class="metric-card" id="security-metrics">
                        <div class="card-header">
                            <h3><i class="fa fa-exclamation-triangle"></i> ${__('Security Metrics')}</h3>
                            <div class="card-actions">
                                <button class="btn btn-sm refresh-widget" data-widget="security_metrics">
                                    <i class="fa fa-refresh"></i>
                                </button>
                            </div>
                        </div>
                        <div class="card-content" id="security-metrics-content">
                            <div class="loading-spinner">
                                <i class="fa fa-spinner fa-spin"></i> ${__('Loading...')}
                            </div>
                        </div>
                    </div>

                    <div class="metric-card" id="system-health">
                        <div class="card-header">
                            <h3><i class="fa fa-heartbeat"></i> ${__('System Health')}</h3>
                            <div class="card-actions">
                                <button class="btn btn-sm refresh-widget" data-widget="system_health">
                                    <i class="fa fa-refresh"></i>
                                </button>
                            </div>
                        </div>
                        <div class="card-content" id="system-health-content">
                            <div class="loading-spinner">
                                <i class="fa fa-spinner fa-spin"></i> ${__('Loading...')}
                            </div>
                        </div>
                    </div>

                    <div class="metric-card" id="license-status">
                        <div class="card-header">
                            <h3><i class="fa fa-certificate"></i> ${__('License Status')}</h3>
                            <div class="card-actions">
                                <button class="btn btn-sm refresh-widget" data-widget="license_status">
                                    <i class="fa fa-refresh"></i>
                                </button>
                            </div>
                        </div>
                        <div class="card-content" id="license-status-content">
                            <div class="loading-spinner">
                                <i class="fa fa-spinner fa-spin"></i> ${__('Loading...')}
                            </div>
                        </div>
                    </div>

                    <div class="metric-card" id="permission-summary">
                        <div class="card-header">
                            <h3><i class="fa fa-users-cog"></i> ${__('Permission Summary')}</h3>
                            <div class="card-actions">
                                <button class="btn btn-sm refresh-widget" data-widget="permission_summary">
                                    <i class="fa fa-refresh"></i>
                                </button>
                            </div>
                        </div>
                        <div class="card-content" id="permission-summary-content">
                            <div class="loading-spinner">
                                <i class="fa fa-spinner fa-spin"></i> ${__('Loading...')}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Security Alerts -->
                <div class="dashboard-section">
                    <div class="section-header">
                        <h3><i class="fa fa-bell"></i> ${__('Security Alerts')}</h3>
                        <div class="alert-controls">
                            <button id="acknowledge-all" class="btn btn-sm btn-warning">
                                ${__('Acknowledge All')}
                            </button>
                            <label class="checkbox-label">
                                <input type="checkbox" id="alert-sounds" ${this.alertSounds ? 'checked' : ''}>
                                ${__('Sound Alerts')}
                            </label>
                        </div>
                    </div>
                    <div id="security-alerts" class="alerts-container">
                        <div class="loading-spinner">
                            <i class="fa fa-spinner fa-spin"></i> ${__('Loading alerts...')}
                        </div>
                    </div>
                </div>

                <!-- Activity Monitoring -->
                <div class="dashboard-section">
                    <div class="section-header">
                        <h3><i class="fa fa-activity"></i> ${__('Recent Activities')}</h3>
                        <div class="activity-controls">
                            <button id="export-activities" class="btn btn-sm btn-secondary">
                                <i class="fa fa-download"></i> ${__('Export')}
                            </button>
                            <div class="severity-filter">
                                <label>${__('Severity')}:</label>
                                <select id="severity-filter" class="form-control">
                                    <option value="">${__('All')}</option>
                                    <option value="critical">${__('Critical')}</option>
                                    <option value="high">${__('High')}</option>
                                    <option value="medium">${__('Medium')}</option>
                                    <option value="low">${__('Low')}</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div id="recent-activities" class="activities-container">
                        <div class="loading-spinner">
                            <i class="fa fa-spinner fa-spin"></i> ${__('Loading activities...')}
                        </div>
                    </div>
                </div>

                <!-- User Analytics -->
                <div class="dashboard-section">
                    <div class="section-header">
                        <h3><i class="fa fa-chart-bar"></i> ${__('User Analytics')}</h3>
                    </div>
                    <div id="user-activities" class="analytics-container">
                        <div class="loading-spinner">
                            <i class="fa fa-spinner fa-spin"></i> ${__('Loading analytics...')}
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Inject dashboard into page
        $('body').append(dashboardHtml);

        // Apply initial styles
        this.loadStyles();
    }

    async loadInitialData() {
        try {
            const data = await this.fetchDashboardData();
            await this.updateAllWidgets(data);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError(__('Failed to load dashboard data'));
        }
    }

    async fetchDashboardData() {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'universal_workshop.user_management.security_dashboard.get_security_dashboard_data',
                args: {
                    timeframe_hours: this.timeframe
                },
                callback: (response) => {
                    if (response.message && !response.message.error) {
                        resolve(response.message);
                    } else {
                        reject(new Error(response.message?.error || 'Unknown error'));
                    }
                },
                error: (xhr) => {
                    reject(new Error(`API Error: ${xhr.status} ${xhr.statusText}`));
                }
            });
        });
    }

    async updateAllWidgets(data) {
        if (!data || data.error) {
            this.showError(data?.error || __('No data received'));
            return;
        }

        // Update individual widgets
        await Promise.all([
            this.updateSecurityMetrics(data.security_metrics),
            this.updateSystemHealth(data.system_health),
            this.updateLicenseStatus(data.license_status),
            this.updatePermissionSummary(data.permission_summary),
            this.updateSecurityAlerts(data.security_alerts),
            this.updateRecentActivities(data.recent_activities),
            this.updateUserActivities(data.user_activities)
        ]);

        // Update last updated timestamp
        $('#last-updated').text(__('Last updated: {0}', [data.generated_at]));
    }

    updateSecurityMetrics(metrics) {
        if (!metrics || metrics.error) {
            $('#security-metrics-content').html(`<div class="error">${metrics?.error || __('Failed to load metrics')}</div>`);
            return;
        }

        const riskClass = this.getRiskClass(metrics.risk_level);
        const html = `
            <div class="metrics-grid-small">
                <div class="metric-item">
                    <div class="metric-value ${metrics.failed_logins > 0 ? 'danger' : 'success'}">${metrics.failed_logins}</div>
                    <div class="metric-label">${__('Failed Logins')}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value ${metrics.permission_violations > 0 ? 'warning' : 'success'}">${metrics.permission_violations}</div>
                    <div class="metric-label">${__('Permission Violations')}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value info">${metrics.active_sessions}</div>
                    <div class="metric-label">${__('Active Sessions')}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value ${metrics.license_violations > 0 ? 'danger' : 'success'}">${metrics.license_violations}</div>
                    <div class="metric-label">${__('License Violations')}</div>
                </div>
            </div>
            <div class="risk-indicator ${riskClass}">
                <i class="fa fa-shield-alt"></i>
                ${__('Risk Level')}: <strong>${__(metrics.risk_level.toUpperCase())}</strong>
            </div>
        `;

        $('#security-metrics-content').html(html);
    }

    updateSystemHealth(health) {
        if (!health || health.error) {
            $('#system-health-content').html(`<div class="error">${health?.error || __('Failed to load health data')}</div>`);
            return;
        }

        const statusClass = this.getHealthClass(health.status);
        const html = `
            <div class="health-overview">
                <div class="health-score ${statusClass}">
                    <div class="score-circle">
                        <span class="score-value">${health.overall_score}</span>
                        <span class="score-max">/100</span>
                    </div>
                    <div class="score-status">${__(health.status.toUpperCase())}</div>
                </div>
                <div class="health-details">
                    <div class="health-item">
                        <span class="health-label">${__('Database Health')}</span>
                        <span class="health-value">${health.database_health}%</span>
                    </div>
                    <div class="health-item">
                        <span class="health-label">${__('Permission Integrity')}</span>
                        <span class="health-value">${health.permission_integrity}%</span>
                    </div>
                    <div class="health-item">
                        <span class="health-label">${__('Session Health')}</span>
                        <span class="health-value">${health.session_health}%</span>
                    </div>
                </div>
            </div>
            <div class="health-footer">
                <small>${__('Last Check')}: ${health.last_check}</small>
            </div>
        `;

        $('#system-health-content').html(html);
    }

    updateSecurityAlerts(alerts) {
        if (!alerts || alerts.error) {
            $('#security-alerts').html(`<div class="error">${alerts?.error || __('Failed to load alerts')}</div>`);
            return;
        }

        if (alerts.length === 0) {
            $('#security-alerts').html(`
                <div class="no-alerts">
                    <i class="fa fa-check-circle"></i>
                    <p>${__('No active security alerts')}</p>
                </div>
            `);
            return;
        }

        // Check for new critical alerts
        const criticalAlerts = alerts.filter(alert => alert.severity === 'critical');
        if (criticalAlerts.length > 0 && this.alertSounds) {
            this.playAlertSound();
        }

        const alertsHtml = alerts.map(alert => this.renderAlert(alert)).join('');
        $('#security-alerts').html(alertsHtml);
    }

    renderAlert(alert) {
        const severityClass = `alert-${alert.severity}`;
        const severityIcon = this.getSeverityIcon(alert.severity);

        return `
            <div class="security-alert ${severityClass}" data-alert-id="${alert.id}">
                <div class="alert-header">
                    <div class="alert-icon">
                        <i class="fa ${severityIcon}"></i>
                    </div>
                    <div class="alert-content">
                        <h4 class="alert-title">${alert.title}</h4>
                        <p class="alert-message">${alert.message}</p>
                    </div>
                    <div class="alert-actions">
                        <button class="btn btn-sm acknowledge-alert" data-alert-id="${alert.id}">
                            ${__('Acknowledge')}
                        </button>
                        <button class="btn btn-sm view-details" data-alert-id="${alert.id}">
                            ${__('Details')}
                        </button>
                    </div>
                </div>
                <div class="alert-footer">
                    <span class="alert-time">${alert.created_at}</span>
                    <span class="alert-user">${__('User')}: ${alert.user || __('System')}</span>
                </div>
            </div>
        `;
    }

    setupEventHandlers() {
        // Timeframe change
        $('#timeframe-select').on('change', (e) => {
            this.timeframe = parseInt(e.target.value);
            this.refreshDashboard();
        });

        // Manual refresh
        $('#refresh-dashboard').on('click', () => {
            this.refreshDashboard();
        });

        // Widget refresh
        $('.refresh-widget').on('click', (e) => {
            const widget = $(e.target).closest('.refresh-widget').data('widget');
            this.refreshWidget(widget);
        });

        // Alert acknowledgment
        $(document).on('click', '.acknowledge-alert', (e) => {
            const alertId = $(e.target).data('alert-id');
            this.acknowledgeAlert(alertId);
        });

        // Alert sounds toggle
        $('#alert-sounds').on('change', (e) => {
            this.alertSounds = e.target.checked;
        });

        // Severity filter
        $('#severity-filter').on('change', (e) => {
            this.filterActivities(e.target.value);
        });
    }

    setupRealTimeUpdates() {
        // Main dashboard refresh
        setInterval(() => {
            this.refreshDashboard();
        }, this.refreshInterval);

        // Alert-specific refresh (more frequent)
        setInterval(() => {
            this.refreshWidget('security_alerts');
        }, this.alertCheckInterval);
    }

    applyRTLStyles() {
        if (this.isRTL) {
            $('.security-dashboard').addClass('rtl-layout');

            // Apply Arabic-specific styling
            $('body').append(`
                <style>
                .rtl-layout .metric-card { direction: rtl; text-align: right; }
                .rtl-layout .alert-header { direction: rtl; }
                .rtl-layout .dashboard-header { direction: rtl; }
                .rtl-layout .form-control { text-align: right; }
                </style>
            `);
        }
    }

    loadStyles() {
        const styles = `
            <style>
            .security-dashboard {
                padding: 20px;
                background: #f8f9fa;
                min-height: 100vh;
            }
            
            .dashboard-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                padding: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .metric-card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
            
            .card-content {
                padding: 20px;
                min-height: 150px;
            }
            
            .security-alert {
                margin-bottom: 15px;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .alert-critical { border-left: 4px solid #dc3545; background: #f8d7da; }
            .alert-high { border-left: 4px solid #fd7e14; background: #fff3cd; }
            .alert-medium { border-left: 4px solid #ffc107; background: #fff3cd; }
            .alert-low { border-left: 4px solid #28a745; background: #d4edda; }
            
            .loading-spinner {
                text-align: center;
                padding: 40px;
                color: #6c757d;
            }
            
            .risk-indicator {
                text-align: center;
                padding: 15px;
                border-radius: 5px;
                margin-top: 15px;
            }
            
            .risk-indicator.critical { background: #f8d7da; color: #721c24; }
            .risk-indicator.high { background: #fff3cd; color: #856404; }
            .risk-indicator.medium { background: #d1ecf1; color: #0c5460; }
            .risk-indicator.low { background: #d4edda; color: #155724; }
            
            .health-score {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .score-circle {
                display: inline-block;
                font-size: 24px;
                font-weight: bold;
            }
            
            .rtl-layout .dashboard-header { direction: rtl; }
            .rtl-layout .metric-card { direction: rtl; }
            </style>
        `;

        $('head').append(styles);
    }

    getRiskClass(riskLevel) {
        const classes = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        };
        return classes[riskLevel] || 'low';
    }

    getHealthClass(status) {
        const classes = {
            'excellent': 'success',
            'good': 'info',
            'fair': 'warning',
            'poor': 'danger'
        };
        return classes[status] || 'info';
    }

    getSeverityIcon(severity) {
        const icons = {
            'critical': 'fa-exclamation-circle',
            'high': 'fa-exclamation-triangle',
            'medium': 'fa-info-circle',
            'low': 'fa-check-circle'
        };
        return icons[severity] || 'fa-info-circle';
    }

    async refreshDashboard() {
        try {
            $('#connection-status').removeClass('online offline').addClass('refreshing').html('<i class="fa fa-spinner fa-spin"></i> ' + __('Refreshing...'));

            const data = await this.fetchDashboardData();
            await this.updateAllWidgets(data);

            $('#connection-status').removeClass('refreshing').addClass('online').html('<i class="fa fa-circle"></i> ' + __('Online'));
        } catch (error) {
            console.error('Dashboard refresh error:', error);
            $('#connection-status').removeClass('refreshing online').addClass('offline').html('<i class="fa fa-circle"></i> ' + __('Offline'));
            this.showError(__('Failed to refresh dashboard'));
        }
    }

    async refreshWidget(widgetName) {
        try {
            const response = await new Promise((resolve, reject) => {
                frappe.call({
                    method: 'universal_workshop.user_management.security_dashboard.refresh_dashboard_widget',
                    args: {
                        widget_name: widgetName,
                        timeframe_hours: this.timeframe
                    },
                    callback: (response) => {
                        if (response.message && !response.message.error) {
                            resolve(response.message);
                        } else {
                            reject(new Error(response.message?.error || 'Unknown error'));
                        }
                    },
                    error: (xhr) => {
                        reject(new Error(`API Error: ${xhr.status} ${xhr.statusText}`));
                    }
                });
            });

            // Update specific widget based on widget name
            switch (widgetName) {
                case 'security_metrics':
                    this.updateSecurityMetrics(response);
                    break;
                case 'system_health':
                    this.updateSystemHealth(response);
                    break;
                case 'security_alerts':
                    this.updateSecurityAlerts(response);
                    break;
                // Add other cases as needed
            }

        } catch (error) {
            console.error(`Widget ${widgetName} refresh error:`, error);
        }
    }

    async acknowledgeAlert(alertId) {
        try {
            const notes = prompt(__('Optional notes for this acknowledgment:'));

            await new Promise((resolve, reject) => {
                frappe.call({
                    method: 'universal_workshop.user_management.security_dashboard.acknowledge_security_alert',
                    args: {
                        alert_id: alertId,
                        notes: notes || ''
                    },
                    callback: (response) => {
                        if (response.message && response.message.success) {
                            resolve(response.message);
                        } else {
                            reject(new Error(response.message?.error || 'Failed to acknowledge alert'));
                        }
                    },
                    error: (xhr) => {
                        reject(new Error(`API Error: ${xhr.status} ${xhr.statusText}`));
                    }
                });
            });

            // Remove alert from display
            $(`.security-alert[data-alert-id="${alertId}"]`).fadeOut();

            frappe.show_alert({
                message: __('Alert acknowledged successfully'),
                indicator: 'green'
            });

        } catch (error) {
            console.error('Alert acknowledgment error:', error);
            frappe.show_alert({
                message: __('Failed to acknowledge alert: {0}', [error.message]),
                indicator: 'red'
            });
        }
    }

    playAlertSound() {
        if (this.alertSounds) {
// Create and play alert sound
