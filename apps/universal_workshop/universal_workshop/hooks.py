app_name = "universal_workshop"
app_title = "Universal Workshop"
app_publisher = "Said Al-Adowi"
app_description = "automotive workshop management"
app_email = "al.a.dawi@hotmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Workshop Onboarding System (Tasks 1.3 & 1.4)
# ------------------
# Using the web form onboarding system implemented in Tasks 1.3 and 1.4
# Web form location: /setup/onboarding/web_form/workshop_onboarding/
# API endpoints: /setup/onboarding/api/onboarding_wizard.py
# Progress tracking: /setup/onboarding/doctype/onboarding_progress/
# Route: /workshop-onboarding (accessible via website)

# Website
# ------------------
website_route_rules = [
    {"from_route": "/workshop-onboarding", "to_route": "workshop-onboarding"},
    {"from_route": "/onboarding", "to_route": "onboarding"},
    {"from_route": "/login", "to_route": "login"},
    {"from_route": "/universal-workshop-dashboard", "to_route": "universal-workshop-dashboard"},
    {"from_route": "/technician", "to_route": "technician"},
    {
        "from_route": "/api/webhooks/twilio",
        "to_route": "universal_workshop.communication_management.delivery_tracking.twilio_webhook_handler",
    },
]

# User home page determination
get_website_user_home_page = ["universal_workshop.core.boot.boot_manager.get_user_home_page"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
#   {
#       "name": "universal_workshop",
#       "logo": "/assets/universal_workshop/logo.png",
#       "title": "Universal Workshop",
#       "route": "/universal_workshop",
#       "has_permission": "universal_workshop.api.permission.has_app_permission"
#   }
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html

# CSS Assets - Organized by Category (Updated to use /public structure)
app_include_css = [
    # Core Assets
    "/assets/universal_workshop/css/core/technician-core.css",
    # Themes Assets
    "/assets/universal_workshop/css/themes/dark_mode.css",
    "/assets/universal_workshop/css/themes/theme_selector.css",
    "/assets/universal_workshop/css/themes/theme_styles.css",
    # Localization Assets
    "/assets/universal_workshop/css/localization/arabic-rtl.css",
    "/assets/universal_workshop/css/localization/customer_analytics_dashboard.css",
    "/assets/universal_workshop/css/localization/customer_search.css",
    "/assets/universal_workshop/css/localization/dashboard_layout.css",
    "/assets/universal_workshop/css/localization/inventory_alerts_dashboard.css",
    "/assets/universal_workshop/css/localization/mobile_warehouse.css",
    "/assets/universal_workshop/css/localization/onboarding_wizard.css",
    "/assets/universal_workshop/css/localization/quick_action_toolbar.css",
    "/assets/universal_workshop/css/localization/supplier_dashboard.css",
    # Branding Assets
    "/assets/universal_workshop/css/branding/dynamic_branding.css",
    # Workshop Assets
    "/assets/universal_workshop/css/workshop/service_order_kanban.css",
    # Mobile Assets
    "/assets/universal_workshop/css/mobile/mobile-app.css",
    "/assets/universal_workshop/css/mobile/mobile-workshop.css",
    "/assets/universal_workshop/css/mobile/technician-mobile.css",
    # Modules Assets
    "/assets/universal_workshop/css/modules/customer_notifications.css",
    "/assets/universal_workshop/css/modules/customer_portal.css",
    "/assets/universal_workshop/css/modules/demand_forecasting.css",
    "/assets/universal_workshop/css/modules/labor_time_tracking.css",
    "/assets/universal_workshop/css/modules/performance_visualizations.css",
    "/assets/universal_workshop/css/modules/progress_tracking.css",
    "/assets/universal_workshop/css/modules/quality_control.css",
    "/assets/universal_workshop/css/modules/vat_automation.css",
    "/assets/universal_workshop/css/modules/vehicle_form.css",
]
# JavaScript Assets - Organized by Category (Updated to use /public structure)
app_include_js = [
    # Integration Assets (V2 Bridge System)
    "/assets/universal_workshop/js/frontend_switcher.js",
    "/assets/universal_workshop/js/integration/v2-bridge-loader.js",
    "/assets/universal_workshop/js/integration/doctype-embeddings.js",
    "/assets/universal_workshop/js/integration/integration-example.js",
    "/assets/universal_workshop/js/integration/frontend-switching-test.js",
    # Core Assets
    "/assets/universal_workshop/js/core/session_frontend.js",
    "/assets/universal_workshop/js/core/session_management.js",
    "/assets/universal_workshop/js/core/setup_check.js",
    # Setup Assets
    "/assets/universal_workshop/js/setup/onboarding_wizard.js",
    # Branding Assets
    "/assets/universal_workshop/js/branding/branding_service.js",
    "/assets/universal_workshop/js/branding/branding_system.js",
    "/assets/universal_workshop/js/branding/dark_mode_manager.js",
    "/assets/universal_workshop/js/branding/logo_upload_widget.js",
    "/assets/universal_workshop/js/branding/rtl_branding_manager.js",
    "/assets/universal_workshop/js/branding/theme_manager.js",
    "/assets/universal_workshop/js/branding/theme_selector.js",
    # Themes Assets
    "/assets/universal_workshop/js/themes/dark_mode.js",
    # Workshop Assets
    "/assets/universal_workshop/js/workshop/quality_control.js",
    "/assets/universal_workshop/js/workshop/service-worker.js",
    "/assets/universal_workshop/js/workshop/service_order_kanban.js",
    "/assets/universal_workshop/js/workshop/service_worker.js",
    "/assets/universal_workshop/js/workshop/technician-app.js",
    "/assets/universal_workshop/js/workshop/technician-sw.js",
    "/assets/universal_workshop/js/workshop/workshop-offline.js",
    "/assets/universal_workshop/js/workshop/workshop_profile.js",
    # Mobile Assets
    "/assets/universal_workshop/js/mobile/mobile-inventory-scanner.js",
    "/assets/universal_workshop/js/mobile/mobile-receiving.js",
    "/assets/universal_workshop/js/mobile/mobile_inventory.js",
    "/assets/universal_workshop/js/mobile/mobile_warehouse.js",
    # Shared Assets
    "/assets/universal_workshop/js/shared/arabic-utils.js",
    # Analytics Assets
    "/assets/universal_workshop/js/analytics/customer_analytics_dashboard.js",
    "/assets/universal_workshop/js/analytics/labor_time_tracking.js",
    "/assets/universal_workshop/js/analytics/progress_tracking_dashboard.js",
    "/assets/universal_workshop/js/analytics/time-tracker.js",
    # Modules Assets
    "/assets/universal_workshop/js/modules/abc_analysis_ui.js",
    "/assets/universal_workshop/js/modules/audit_frontend.js",
    "/assets/universal_workshop/js/modules/barcode_scanner.js",
    "/assets/universal_workshop/js/modules/compatibility_matrix_ui.js",
    "/assets/universal_workshop/js/modules/contextual_help.js",
    "/assets/universal_workshop/js/modules/customer_notifications.js",
    "/assets/universal_workshop/js/modules/customer_portal.js",
    "/assets/universal_workshop/js/modules/customer_search.js",
    "/assets/universal_workshop/js/modules/cycle_counting_ui.js",
    "/assets/universal_workshop/js/modules/demand_forecasting.js",
    "/assets/universal_workshop/js/modules/help_system_tests.js",
    "/assets/universal_workshop/js/modules/inventory_alerts_dashboard.js",
    "/assets/universal_workshop/js/modules/job-management.js",
    "/assets/universal_workshop/js/modules/offline_manager.js",
    "/assets/universal_workshop/js/modules/order_conversion_workflow.js",
    "/assets/universal_workshop/js/modules/parts_suggestion.js",
    "/assets/universal_workshop/js/modules/performance_visualizations.js",
    "/assets/universal_workshop/js/modules/print_format_integration.js",
    "/assets/universal_workshop/js/modules/qr_code_invoice.js",
    "/assets/universal_workshop/js/modules/quick_action_toolbar.js",
    "/assets/universal_workshop/js/modules/sales_invoice.js",
    "/assets/universal_workshop/js/modules/security_alerts_frontend.js",
    "/assets/universal_workshop/js/modules/stock_transfer_ui.js",
    "/assets/universal_workshop/js/modules/storage_location.js",
    "/assets/universal_workshop/js/modules/supplier_dashboard.js",
    "/assets/universal_workshop/js/modules/vat_automation.js",
]

# include js, css files in header of web template (Updated to use /public structure)
web_include_css = [
    "/assets/universal_workshop/css/onboarding_wizard.css",
    "/assets/universal_workshop/css/mobile_warehouse.css",
    "/assets/universal_workshop/css/branding/dynamic_branding.css",
    "/assets/universal_workshop/css/themes/theme_styles.css",
    "/assets/universal_workshop/css/themes/theme_selector.css",
    "/assets/universal_workshop/css/themes/dark_mode.css",
]
web_include_js = [
    "/assets/universal_workshop/js/onboarding_wizard.js",
    "/assets/universal_workshop/js/branding/logo_upload_widget.js",
    "/assets/universal_workshop/js/branding/branding_service.js",
    "/assets/universal_workshop/js/branding/theme_manager.js",
    "/assets/universal_workshop/js/branding/theme_selector.js",
    "/assets/universal_workshop/js/branding/dark_mode_manager.js",
    "/assets/universal_workshop/js/branding/rtl_branding_manager.js",  # Cross-browser RTL & branding system
    "/assets/universal_workshop/js/mobile/mobile_warehouse.js",
]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "universal_workshop/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views

# Real-time WebSocket System (Phase 3 PWA Enhancement)
# ------------------

# Boot session for real-time features
boot_session = "universal_workshop.realtime.websocket_manager.get_websocket_manager"

# Document events for real-time sync
doc_events = {
    "Service Order": {
        "on_update": "universal_workshop.realtime.event_bus.publish_workshop_event",
        "after_insert": "universal_workshop.realtime.event_bus.publish_workshop_event",
        "on_submit": "universal_workshop.realtime.event_bus.publish_workshop_event",
        "on_cancel": "universal_workshop.realtime.event_bus.publish_workshop_event",
    },
    "Customer": {
        "on_update": "universal_workshop.realtime.sync_manager.queue_pwa_sync",
        "after_insert": "universal_workshop.realtime.sync_manager.queue_pwa_sync",
    },
    "Vehicle": {
        "on_update": "universal_workshop.realtime.sync_manager.queue_pwa_sync",
        "after_insert": "universal_workshop.realtime.sync_manager.queue_pwa_sync",
    },
    "Technician": {
        "on_update": "universal_workshop.realtime.event_bus.publish_workshop_event",
        "after_insert": "universal_workshop.realtime.event_bus.publish_workshop_event",
    },
    "Service Appointment": {
        "on_update": "universal_workshop.realtime.event_bus.publish_workshop_event",
        "after_insert": "universal_workshop.realtime.event_bus.publish_workshop_event",
    },
    # Returns and Exchange System Workflow Events
    "Return Request": {
        "on_update": "universal_workshop.sales_service.utils.workflow_utils.on_update_return_request",
        "validate": "universal_workshop.sales_service.utils.workflow_utils.validate_return_request",
    },
    "Exchange Request": {
        "on_update": "universal_workshop.sales_service.utils.workflow_utils.on_update_exchange_request",
        "validate": "universal_workshop.sales_service.utils.workflow_utils.validate_exchange_request",
    },
}

# Scheduled tasks for real-time system and Week 16 monitoring
scheduler_events = {
    "cron": {
        # Process PWA sync queue every 5 minutes
        "*/5 * * * *": [
            "universal_workshop.realtime.sync_manager.process_pwa_sync_queue",
            # Week 16: Real-time metrics collection
            "universal_workshop.utils.health_monitoring.collect_realtime_health_metrics",
            "universal_workshop.utils.production_deployment.monitor_deployment_health",
        ],
        # Process scheduled notifications every minute
        "* * * * *": [
            "universal_workshop.realtime.notification_handler.process_scheduled_notifications"
        ],
        # Every 10 minutes - Enhanced monitoring
        "*/10 * * * *": [
            "universal_workshop.utils.apm_monitor.collect_realtime_metrics",
            "universal_workshop.utils.database_monitor.collect_realtime_metrics",
            "universal_workshop.utils.health_monitoring.check_critical_alerts",
        ],
        # Clean old sync history daily at 2 AM
        "0 2 * * *": [
            "universal_workshop.realtime.sync_manager.get_pwa_sync_manager().clear_old_history",
            "universal_workshop.realtime.notification_handler.get_arabic_notification_handler().clear_old_history",
            "universal_workshop.realtime.event_bus.get_workshop_event_bus().clear_event_history",
            # Week 16: Daily cleanup and maintenance
            "universal_workshop.utils.load_testing_framework.cleanup_old_test_results",
            "universal_workshop.utils.health_monitoring.cleanup_old_health_data",
        ],
    },
    "hourly": [
        # Week 13: ML system monitoring
        "universal_workshop.ml_analytics.ml_storage.update_ml_usage_stats",
        # Week 14: APM monitoring
        "universal_workshop.utils.apm_monitor.monitor_system_performance_job",
        "universal_workshop.utils.database_monitor.monitor_database_performance_job",
        # Week 16: Health monitoring and load testing
        "universal_workshop.utils.health_monitoring.comprehensive_health_check",
        "universal_workshop.utils.production_deployment.system_health_assessment",
    ],
    "daily": [
        # Week 13: ML model retraining checks
        "universal_workshop.ml_analytics.ml_storage.schedule_auto_retrain_check",
        # Week 14: Performance log cleanup
        "universal_workshop.analytics_reporting.doctype.performance_log.performance_log.cleanup_performance_logs",
        # Week 16: Production deployment validation
        "universal_workshop.utils.production_deployment.validate_deployment_integrity",
        "universal_workshop.utils.load_testing_framework.run_daily_smoke_tests",
    ],
    "weekly": [
        # Week 13: ML usage log cleanup
        "universal_workshop.analytics_reporting.doctype.ml_model_usage_log.ml_model_usage_log.cleanup_old_usage_logs",
        # Week 16: Comprehensive load testing
        "universal_workshop.utils.load_testing_framework.run_weekly_capacity_test",
        "universal_workshop.utils.health_monitoring.generate_weekly_health_report",
    ],
    "monthly": [
        # Week 16: Production deployment optimization
        "universal_workshop.utils.production_deployment.optimize_production_configuration",
        "universal_workshop.utils.health_monitoring.archive_old_health_data",
    ],
}

# WebSocket server configuration
socketio_port = 9000

# Real-time API endpoints
website_route_rules.extend(
    [
        {
            "from_route": "/api/realtime/websocket",
            "to_route": "universal_workshop.realtime.websocket_manager",
        },
        {"from_route": "/api/realtime/events", "to_route": "universal_workshop.realtime.event_bus"},
        {
            "from_route": "/api/realtime/notifications",
            "to_route": "universal_workshop.realtime.notification_handler",
        },
        {
            "from_route": "/api/realtime/sync",
            "to_route": "universal_workshop.realtime.sync_manager",
        },
    ]
)
doctype_js = {"Sales Invoice": "public/js/sales_invoice.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# include js in web form
webform_include_js = {"workshop-onboarding": "public/js/onboarding_wizard.js"}
webform_include_css = {"workshop-onboarding": "public/css/onboarding_wizard.css"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "universal_workshop/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
home_page = "login"

# website user home page (by Role)
role_home_page = {
    "Workshop Manager": "app/workspace/Workshop%20Management",
    "Workshop Technician": "technician",
    "Workshop Owner": "/universal-workshop-dashboard",
    "System Manager": "app/workspace/Workshop%20Management",
    "Administrator": "app/workspace/Workshop%20Management",
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
    "methods": [
        # "universal_workshop.utils.format_arabic_date",  # Temporarily disabled
        # "universal_workshop.utils.format_omr_currency",  # Temporarily disabled
        # "universal_workshop.utils.get_arabic_number",  # Temporarily disabled
        "universal_workshop.themes.api.get_workshop_theme",
        "universal_workshop.themes.api.get_theme_colors",
        "universal_workshop.print_formats.branding_utils.get_print_branding_context",
        "universal_workshop.print_formats.branding_utils.get_workshop_branding_for_print",
    ],
    "filters": [
        # "universal_workshop.utils.arabic_number_filter",  # Temporarily disabled
        # "universal_workshop.utils.format_currency_filter",  # Temporarily disabled
    ],
}

# WhiteListed Methods
# -------------------
# Methods available to client-side calls

override_whitelisted_methods = {
    "universal_workshop.vehicle_management.live_api_test.run_live_api_tests": "universal_workshop.vehicle_management.live_api_test.run_live_api_tests",
    "universal_workshop.vehicle_management.live_api_test.get_api_performance_dashboard": "universal_workshop.vehicle_management.live_api_test.get_api_performance_dashboard",
    "universal_workshop.vehicle_management.live_api_test.optimize_cache_settings": "universal_workshop.vehicle_management.live_api_test.optimize_cache_settings",
    "universal_workshop.training_management.api.contextual_help.get_contextual_help": "universal_workshop.training_management.api.contextual_help.get_contextual_help",
    "universal_workshop.training_management.api.contextual_help.search_help_content": "universal_workshop.training_management.api.contextual_help.search_help_content",
    "universal_workshop.billing_management.workflow_manager.get_workflow_status": "universal_workshop.billing_management.workflow_manager.get_workflow_status",
    "universal_workshop.billing_management.workflow_manager.get_workflow_history": "universal_workshop.billing_management.workflow_manager.get_workflow_history",
    "universal_workshop.billing_management.workflow_manager.get_pending_approvals": "universal_workshop.billing_management.workflow_manager.get_pending_approvals",
    "universal_workshop.billing_management.workflow_manager.approve_workflow_step": "universal_workshop.billing_management.workflow_manager.approve_workflow_step",
    "universal_workshop.billing_management.workflow_manager.reject_workflow_step": "universal_workshop.billing_management.workflow_manager.reject_workflow_step",
    "universal_workshop.billing_management.workflow_manager.get_workflow_analytics": "universal_workshop.billing_management.workflow_manager.get_workflow_analytics",
    "universal_workshop.billing_management.budget_planning.create_workshop_budget_structure": "universal_workshop.billing_management.budget_planning.create_workshop_budget_structure",
    "universal_workshop.billing_management.budget_planning.get_budget_variance_analysis": "universal_workshop.billing_management.budget_planning.get_budget_variance_analysis",
    "universal_workshop.billing_management.budget_planning.get_budget_utilization_dashboard": "universal_workshop.billing_management.budget_planning.get_budget_utilization_dashboard",
    "universal_workshop.billing_management.receivables_management.generate_aging_analysis": "universal_workshop.billing_management.receivables_management.generate_aging_analysis",
    "universal_workshop.billing_management.receivables_management.generate_dunning_sequence": "universal_workshop.billing_management.receivables_management.generate_dunning_sequence",
    "universal_workshop.billing_management.receivables_management.get_customer_payment_behavior": "universal_workshop.billing_management.receivables_management.get_customer_payment_behavior",
    "universal_workshop.billing_management.receivables_management.setup_v15_enhancements": "universal_workshop.billing_management.receivables_management.setup_v15_enhancements",
    "universal_workshop.billing_management.receivables_management.get_realtime_ar_dashboard": "universal_workshop.billing_management.receivables_management.get_realtime_ar_dashboard",
    "universal_workshop.billing_management.receivables_management.update_payment_behavior_scores": "universal_workshop.billing_management.receivables_management.update_payment_behavior_scores",
    "universal_workshop.billing_management.cash_flow_forecasting.setup_v15_cash_flow_format": "universal_workshop.billing_management.cash_flow_forecasting.setup_v15_cash_flow_format",
    "universal_workshop.billing_management.cash_flow_forecasting.generate_integrated_forecast": "universal_workshop.billing_management.cash_flow_forecasting.generate_integrated_forecast",
    "universal_workshop.billing_management.cash_flow_forecasting.get_cash_flow_optimization_dashboard": "universal_workshop.billing_management.cash_flow_forecasting.get_cash_flow_optimization_dashboard",
    "universal_workshop.billing_management.pnl_reporting.generate_workshop_pnl_report": "universal_workshop.billing_management.pnl_reporting.generate_workshop_pnl_report",
    "universal_workshop.billing_management.pnl_reporting.get_pnl_dashboard_data": "universal_workshop.billing_management.pnl_reporting.get_pnl_dashboard_data",
    "universal_workshop.billing_management.pnl_reporting.get_pnl_export_data": "universal_workshop.billing_management.pnl_reporting.get_pnl_export_data",
    "universal_workshop.billing_management.vat_compliance_reporting.generate_vat_return_report": "universal_workshop.billing_management.vat_compliance_reporting.generate_vat_return_report",
    "universal_workshop.billing_management.vat_compliance_reporting.get_vat_compliance_dashboard": "universal_workshop.billing_management.vat_compliance_reporting.get_vat_compliance_dashboard",
    "universal_workshop.billing_management.vat_compliance_reporting.prepare_invoice_einvoicing_data": "universal_workshop.billing_management.vat_compliance_reporting.prepare_invoice_einvoicing_data",
    "universal_workshop.billing_management.vat_compliance_reporting.run_vat_compliance_check": "universal_workshop.billing_management.vat_compliance_reporting.run_vat_compliance_check",
    "universal_workshop.billing_management.automated_notifications.setup_all_financial_notifications": "universal_workshop.billing_management.automated_notifications.setup_all_financial_notifications",
    "universal_workshop.billing_management.automated_notifications.send_test_notification": "universal_workshop.billing_management.automated_notifications.send_test_notification",
    "universal_workshop.billing_management.automated_notifications.get_notification_dashboard": "universal_workshop.billing_management.automated_notifications.get_notification_dashboard",
    # Financial Analytics Dashboard API Methods
    "universal_workshop.billing_management.financial_analytics_dashboard.get_financial_dashboard_data": "universal_workshop.billing_management.financial_analytics_dashboard.get_financial_dashboard_data",
    "universal_workshop.billing_management.financial_analytics_dashboard.save_dashboard_configuration": "universal_workshop.billing_management.financial_analytics_dashboard.save_dashboard_configuration",
    "universal_workshop.billing_management.financial_analytics_dashboard.get_dashboard_kpi_summary": "universal_workshop.billing_management.financial_analytics_dashboard.get_dashboard_kpi_summary",
}

# Installation
# ------------

# before_install = "universal_workshop.install.before_install"
after_install = "universal_workshop.setup.installation.installation_manager.after_install"

# Uninstallation
# ------------

before_uninstall = "universal_workshop.setup.installation.installation_manager.before_uninstall"
# after_uninstall = "universal_workshop.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "universal_workshop.utils.before_app_install"
# after_app_install = "universal_workshop.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "universal_workshop.utils.before_app_uninstall"
# after_app_uninstall = "universal_workshop.utils.after_app_uninstall"

# Boot Session
# ------------

# Boot session hooks for session initialization
boot_session = "universal_workshop.core.boot.boot_manager.get_boot_info"

# Startup
# -------

# Functions called during startup
startup = ["universal_workshop.core.boot.boot_manager.check_initial_setup"]

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "universal_workshop.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
    "Customer": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Vehicle": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Service Order": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Parts Inventory": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Workshop Technician": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Service Appointment": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Workshop Role": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
    "Workshop Permission Profile": "universal_workshop.user_management.permission_hooks.get_permission_query_conditions",
}

has_permission = {
    "Customer": "universal_workshop.user_management.permission_hooks.has_permission",
    "Vehicle": "universal_workshop.user_management.permission_hooks.has_permission",
    "Service Order": "universal_workshop.user_management.permission_hooks.has_permission",
    "Parts Inventory": "universal_workshop.user_management.permission_hooks.has_permission",
    "Workshop Technician": "universal_workshop.user_management.permission_hooks.has_permission",
    "Service Appointment": "universal_workshop.user_management.permission_hooks.has_permission",
    "Workshop Role": "universal_workshop.user_management.permission_hooks.has_permission",
    "Workshop Permission Profile": "universal_workshop.user_management.permission_hooks.has_permission",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Customer": {
        "after_insert": "universal_workshop.search_integration.customer_indexer.index_customer_on_save",
        "on_update": "universal_workshop.search_integration.customer_indexer.index_customer_on_save",
        "on_trash": "universal_workshop.search_integration.customer_indexer.remove_customer_on_delete",
        "validate": [
            "universal_workshop.billing_management.oman_vat_config.validate_oman_vat_number",
            "universal_workshop.user_management.permission_hooks.validate_document_access",
        ],
        "before_save": [
            "universal_workshop.user_management.permission_hooks.validate_field_access",
            "universal_workshop.user_management.permission_hooks.check_business_binding_access",
        ],
        "after_insert": [
            "universal_workshop.search_integration.customer_indexer.index_customer_on_save",
            "universal_workshop.user_management.permission_hooks.log_permission_access",
        ],
        "on_update": [
            "universal_workshop.search_integration.customer_indexer.index_customer_on_save",
            "universal_workshop.user_management.permission_hooks.log_permission_access",
        ],
    },
    "Supplier": {
        "validate": "universal_workshop.billing_management.oman_vat_config.validate_oman_vat_number",
    },
    "Item": {
        "after_insert": "universal_workshop.parts_inventory.barcode_utils.auto_generate_item_codes",
        "on_update": "universal_workshop.parts_inventory.barcode_utils.auto_generate_item_codes",
    },
    "Stock Entry": {
        "before_submit": "universal_workshop.parts_inventory.warehouse_management.validate_stock_transfer",
        "on_submit": "universal_workshop.parts_inventory.warehouse_management.on_stock_transfer_submit",
    },
    "Warehouse": {
        "after_insert": "universal_workshop.parts_inventory.warehouse_management.setup_warehouse_defaults"
    },
    "Sales Invoice": {
        "validate": [
            "universal_workshop.billing_management.utils.validate_oman_business_requirements",
            "universal_workshop.billing_management.qr_code_generator.validate_invoice_for_qr",
            "universal_workshop.billing_management.workflow_manager.validate_workflow_stage",
        ],
        "before_save": [
            "universal_workshop.billing_management.utils.validate_oman_business_requirements",
            "universal_workshop.billing_management.workflow_manager.before_save_workflow_update",
        ],
        "on_submit": [
            "universal_workshop.billing_management.qr_code_generator.generate_qr_on_invoice_submit",
            "universal_workshop.communication_management.notifications.send_invoice_notification",
            "universal_workshop.billing_management.workflow_manager.on_submit_workflow_complete",
        ],
        "on_update_after_submit": "universal_workshop.billing_management.workflow_manager.on_update_workflow_track",
        "after_insert": "universal_workshop.billing_management.receivables_management.initialize_receivables_tracking",
        "on_payment_authorization": "universal_workshop.billing_management.receivables_management.update_payment_tracking",
        "on_payment_received": "universal_workshop.billing_management.receivables_management.process_payment_received",
    },
    "Service Appointment": {
        "after_insert": [
            "universal_workshop.communication_management.notifications.send_appointment_confirmation",
            "universal_workshop.customer_portal.event_handlers.handle_appointment_confirmation",
            "universal_workshop.user_management.permission_hooks.log_permission_access",
        ],
        "before_save": [
            "universal_workshop.communication_management.notifications.send_appointment_reminder_check",
            "universal_workshop.user_management.permission_hooks.validate_field_access",
            "universal_workshop.user_management.permission_hooks.validate_workshop_location_access",
        ],
        "on_cancel": "universal_workshop.customer_portal.event_handlers.handle_appointment_cancellation",
        "validate": "universal_workshop.user_management.permission_hooks.validate_document_access",
    },
    "Service Order": {
        "on_update": [
            "universal_workshop.communication_management.notifications.send_service_status_update",
            "universal_workshop.user_management.permission_hooks.log_permission_access",
        ],
        "on_submit": "universal_workshop.communication_management.notifications.send_service_completion_notification",
        "validate": "universal_workshop.user_management.permission_hooks.validate_document_access",
        "before_save": [
            "universal_workshop.user_management.permission_hooks.validate_field_access",
            "universal_workshop.user_management.permission_hooks.validate_workshop_location_access",
        ],
    },
    "Work Order": {
        "on_update": "universal_workshop.customer_portal.event_handlers.handle_service_status_update",
    },
    "Payment Entry": {
        "validate": "universal_workshop.billing_management.receivables_management.validate_payment_entry",
        "before_save": "universal_workshop.billing_management.receivables_management.setup_background_reconciliation_fields",
        "on_submit": "universal_workshop.billing_management.receivables_management.trigger_background_reconciliation",
        "after_insert": "universal_workshop.billing_management.receivables_management.initialize_payment_tracking",
    },
    "Parts Usage": {
        "after_insert": "universal_workshop.customer_portal.event_handlers.handle_parts_approval_request",
    },
    "Quotation": {
        "on_submit": "universal_workshop.communication_management.notifications.send_quotation_notification",
    },
    "Purchase Invoice": {
        "validate": "universal_workshop.billing_management.workflow_manager.validate_workflow_stage",
        "before_save": "universal_workshop.billing_management.workflow_manager.before_save_workflow_update",
        "on_submit": "universal_workshop.billing_management.workflow_manager.on_submit_workflow_complete",
        "on_update_after_submit": "universal_workshop.billing_management.workflow_manager.on_update_workflow_track",
    },
    "Payment Entry": {
        "validate": "universal_workshop.billing_management.workflow_manager.validate_workflow_stage",
        "before_save": "universal_workshop.billing_management.workflow_manager.before_save_workflow_update",
        "on_submit": "universal_workshop.billing_management.workflow_manager.on_submit_workflow_complete",
        "on_update_after_submit": "universal_workshop.billing_management.workflow_manager.on_update_workflow_track",
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "daily": [
        "universal_workshop.tasks.send_service_reminders",
        "universal_workshop.tasks.update_vehicle_service_history",
        "universal_workshop.analytics_reporting.utils.ml_engine.schedule_retrain_for_all_models",
        "universal_workshop.analytics_reporting.doctype.performance_log.performance_log.cleanup_old_logs",
        "universal_workshop.utils.dashboard_realtime.cleanup_dashboard_cache",
    ],
    "weekly": [
        "universal_workshop.tasks.generate_workshop_reports",
        "universal_workshop.analytics_reporting.doctype.ml_model_usage_log.ml_model_usage_log.cleanup_old_logs",
    ],
    "hourly": [
        "universal_workshop.analytics_reporting.utils.ml_storage.update_redis_usage_stats",
        "universal_workshop.utils.apm_monitor.monitor_system_performance_job",
        "universal_workshop.utils.database_monitor.monitor_database_performance_job",
    ],
    "cron": {
        "*/10 * * * *": [
            "universal_workshop.utils.apm_monitor.collect_realtime_metrics",
            "universal_workshop.utils.database_monitor.collect_realtime_metrics",
        ],
        "*/5 * * * *": [
            "universal_workshop.analytics_reporting.doctype.performance_alert.performance_alert.check_critical_alerts"
        ],
        "*/30 * * * *": ["universal_workshop.utils.dashboard_realtime.update_realtime_dashboards"],
    },
}
#   "monthly": [
#       "universal_workshop.tasks.monthly"
#   ],
# }

# Testing
# -------

# before_tests = "universal_workshop.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "frappe.desk.search.search_link": "universal_workshop.overrides.search.enhanced_search_link",
    # P&L Reporting API Methods
    "universal_workshop.billing_management.pnl_reporting.generate_workshop_pnl_report": "universal_workshop.billing_management.pnl_reporting.generate_workshop_pnl_report",
    "universal_workshop.billing_management.pnl_reporting.get_pnl_dashboard_data": "universal_workshop.billing_management.pnl_reporting.get_pnl_dashboard_data",
    "universal_workshop.billing_management.pnl_reporting.get_pnl_export_data": "universal_workshop.billing_management.pnl_reporting.get_pnl_export_data",
    # Cost Center Analysis API Methods
    "universal_workshop.billing_management.cost_center_analysis.generate_cost_center_analysis_report": "universal_workshop.billing_management.cost_center_analysis.generate_cost_center_analysis_report",
    "universal_workshop.billing_management.cost_center_analysis.get_departmental_profitability_analysis": "universal_workshop.billing_management.cost_center_analysis.get_departmental_profitability_analysis",
    "universal_workshop.billing_management.cost_center_analysis.get_cost_center_efficiency_metrics": "universal_workshop.billing_management.cost_center_analysis.get_cost_center_efficiency_metrics",
    "universal_workshop.billing_management.cost_center_analysis.get_cost_allocation_analysis": "universal_workshop.billing_management.cost_center_analysis.get_cost_allocation_analysis",
    "universal_workshop.billing_management.cost_center_analysis.get_cost_center_dashboard_data": "universal_workshop.billing_management.cost_center_analysis.get_cost_center_dashboard_data",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#   "Task": "universal_workshop.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["universal_workshop.utils.before_request"]
# after_request = ["universal_workshop.utils.after_request"]

# Job Events
# ----------
# before_job = ["universal_workshop.utils.before_job"]
# after_job = ["universal_workshop.utils.after_job"]

# Training management tasks are now integrated above

# User Data Protection
# --------------------

# user_data_fields = [
#   {
#       "doctype": "{doctype_1}",
#       "filter_by": "{filter_by}",
#       "redact_fields": ["{field_1}", "{field_2}"],
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_2}",
#       "filter_by": "{filter_by}",
#       "partial": 1,
#   },
#   {
#       "doctype": "{doctype_3}",
#       "strict": False,
#   },
#   {
#       "doctype": "{doctype_4}"
#   }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#   "universal_workshop.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
#   "Logging DocType Name": 30  # days to retain logs
# }

# DocType JavaScript customizations
doctype_js = {
    "Stock Entry": "public/js/stock_entry.js",
    "Warehouse": "public/js/warehouse.js",
    "Item": "public/js/item.js",
}

# Vehicle API sync tasks are now integrated above
