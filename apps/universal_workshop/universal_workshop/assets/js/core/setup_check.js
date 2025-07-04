// Universal Workshop Setup Check
// تحقق من حالة إعداد الورشة وتوجيه المستخدم للإعداد إذا لزم الأمر

frappe.ready(function () {
    // التحقق من حالة الإعداد عند تحميل النظام
    checkInitialSetupStatus();
});

function checkInitialSetupStatus() {
    // التحقق من معلومات الإعداد في boot info
    if (frappe.boot && frappe.boot.setup_complete === false) {
        // تأخير قصير للسماح للصفحة بالتحميل
        setTimeout(function () {
            redirectToSetupIfNeeded();
        }, 1000);
    }
}

function redirectToSetupIfNeeded() {
    // التحقق من أن المستخدم ليس في صفحة الإعداد بالفعل
    const currentPath = window.location.pathname;

    if (currentPath !== '/workshop-onboarding' && currentPath !== '/login') {
        // التحقق مرة أخرى من حالة الإعداد
        frappe.call({
            method: 'universal_workshop.boot.check_initial_setup_status',
            callback: function (r) {
                if (r.message && !r.message.setup_complete) {
                    // Check if this is license-based setup (admin-only mode)
                    if (r.message.license_has_workshop_data && r.message.setup_mode === 'admin_only') {
                        showAdminOnlySetupMessage();
                    } else {
                        showSetupRequiredMessage();
                    }
                }
            }
        });
    }
}

function showAdminOnlySetupMessage() {
    frappe.msgprint({
        title: __('Administrator Setup Required'),
        message: __('Workshop data has been loaded from your license. Please create an administrator account to complete setup.'),
        primary_action: {
            label: __('Create Administrator Account'),
            action: function () {
                window.location.href = '/admin-setup';
            }
        }
    });
}

function showSetupRequiredMessage() {
    frappe.msgprint({
        title: __('Initial Setup Required'),
        message: __('Universal Workshop needs to be configured before you can use it. Please complete the initial setup process.'),
        primary_action: {
            label: __('Start Initial Setup'),
            action: function () {
                window.location.href = '/workshop-onboarding';
            }
        }
    });
}

// التحقق من حالة الإعداد عند تغيير الصفحة
$(document).on('page:load', function () {
    checkInitialSetupStatus();
});

// تحقق دوري من حالة الإعداد (كل دقيقة)
setInterval(function () {
    if (frappe.boot && frappe.boot.setup_complete === false) {
        // تحديث معلومات الإعداد
        frappe.call({
            method: 'universal_workshop.boot.get_boot_info',
            callback: function (r) {
                if (r.message) {
                    // تحديث boot info
                    frappe.boot.setup_complete = r.message.setup_complete;
                    frappe.boot.setup_status = r.message.setup_status;

                    // إذا اكتمل الإعداد، إعادة تحميل الصفحة
                    if (r.message.setup_complete && window.location.pathname === '/workshop-onboarding') {
                        frappe.show_alert({
                            message: __('Setup completed successfully! Redirecting to login...'),
                            indicator: 'green'
                        });
                        setTimeout(() => {
                            window.location.href = '/login';
                        }, 2000);
                    }
                }
            }
        });
    }
}, 60000);

// إضافة معالج للتحقق من الإعداد عند محاولة الوصول لصفحات النظام
frappe.router.on('change', function () {
    const currentRoute = frappe.get_route();

    // إذا كان المستخدم يحاول الوصول لصفحات النظام دون اكتمال الإعداد
    if (currentRoute[0] === 'app' && frappe.boot && frappe.boot.setup_complete === false) {
        frappe.set_route('login');
        showSetupRequiredMessage();
    }
});
