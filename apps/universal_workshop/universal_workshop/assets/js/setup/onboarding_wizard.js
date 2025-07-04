/**
 * Universal Workshop Onboarding Wizard
 * معالج الإعداد الأولي لنظام إدارة الورش الشامل
 * دعم اللغتين العربية والإنجليزية مع تصميم RTL
 */

class OnboardingWizard {
    constructor() {
        this.currentStep = 0;
        this.totalSteps = 6;
        this.progressId = null;
        this.stepData = {};
        this.validationErrors = {};

        this.steps = [
            'basic_info',
            'admin_account',
            'business_info',
            'contact_info',
            'operational_details',
            'financial_info'
        ];

        this.stepTitles = {
            'basic_info': {
                'en': 'Basic Information',
                'ar': 'المعلومات الأساسية'
            },
            'admin_account': {
                'en': 'Administrator Account',
                'ar': 'حساب المدير'
            },
            'business_info': {
                'en': 'Business Information',
                'ar': 'المعلومات التجارية'
            },
            'contact_info': {
                'en': 'Contact Information',
                'ar': 'معلومات الاتصال'
            },
            'operational_details': {
                'en': 'Operational Details',
                'ar': 'التفاصيل التشغيلية'
            },
            'financial_info': {
                'en': 'Financial Information',
                'ar': 'المعلومات المالية'
            }
        };

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkExistingProgress();
        this.setupRTLSupport();
    }

    setupEventListeners() {
        // Navigation buttons
        $(document).on('click', '.wizard-next-btn', () => this.nextStep());
        $(document).on('click', '.wizard-prev-btn', () => this.prevStep());
        $(document).on('click', '.wizard-finish-btn', () => this.finishWizard());
        $(document).on('click', '.wizard-cancel-btn', () => this.cancelWizard());

        // Form validation on input
        $(document).on('blur', '.wizard-form input, .wizard-form select, .wizard-form textarea', (e) => {
            this.validateField($(e.target));
        });

        // Step navigation via progress indicators
        $(document).on('click', '.step-indicator', (e) => {
            const stepIndex = parseInt($(e.target).data('step'));
            if (stepIndex <= this.currentStep) {
                this.goToStep(stepIndex);
            }
        });

        // Arabic field auto-formatting
        $(document).on('input', '[data-arabic="true"]', (e) => {
            this.handleArabicInput($(e.target));
        });

        // Phone number auto-formatting
        $(document).on('input', '[data-phone="oman"]', (e) => {
            this.formatOmanPhone($(e.target));
        });
    }

    checkExistingProgress() {
        frappe.call({
            method: 'universal_workshop.workshop_management.doctype.onboarding_progress.onboarding_progress.get_user_onboarding_progress',
            callback: (r) => {
                if (r.message) {
                    this.loadExistingProgress(r.message);
                } else {
                    this.startNewWizard();
                }
            }
        });
    }

    loadExistingProgress(progress) {
        this.progressId = progress.progress_id;
        this.currentStep = progress.current_step || 0;
        this.stepData = progress.data || {};

        frappe.msgprint({
            title: __('Resume Onboarding'),
            message: __('You have an existing onboarding session. Would you like to continue?'),
            primary_action: {
                'label': __('Continue'),
                'action': () => {
                    this.resumeWizard();
                }
            },
            secondary_action: {
                'label': __('Start Over'),
                'action': () => {
                    this.startNewWizard();
                }
            }
        });
    }

    startNewWizard() {
        frappe.call({
            method: 'universal_workshop.workshop_management.api.onboarding_wizard.start_onboarding_wizard',
            callback: (r) => {
                if (r.message && r.message.success) {
                    this.progressId = r.message.progress_id;
                    this.currentStep = 0;
                    this.stepData = {};
                    this.buildWizard();
                    this.showStep(0);
                } else {
                    this.showError(__('Failed to start onboarding wizard'));
                }
            }
        });
    }

    resumeWizard() {
        this.buildWizard();
        this.populateExistingData();
        this.showStep(this.currentStep);
    }

    buildWizard() {
        const wizardContainer = $('.onboarding-wizard-container');

        if (!wizardContainer.length) {
            $('body').append(this.getWizardHTML());
        }

        this.buildProgressIndicators();
        this.setupRTLSupport();
    }

    getWizardHTML() {
        const lang = frappe.boot.lang || 'en';
        const direction = lang === 'ar' ? 'rtl' : 'ltr';

        return `
            <div class="onboarding-wizard-container" dir="${direction}">
                <div class="wizard-overlay"></div>
                <div class="wizard-modal">
                    <div class="wizard-header">
                        <h2 class="wizard-title">${this.getLocalizedText('Workshop Setup Wizard', 'معالج إعداد الورشة')}</h2>
                        <button class="wizard-close-btn" aria-label="Close">&times;</button>
                    </div>
                    <div class="wizard-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 0%"></div>
                        </div>
                        <div class="step-indicators"></div>
                    </div>
                    <div class="wizard-content">
                        <div class="wizard-step-content"></div>
                    </div>
                    <div class="wizard-footer">
                        <button class="btn btn-secondary wizard-cancel-btn">${this.getLocalizedText('Cancel', 'إلغاء')}</button>
                        <div class="wizard-nav-buttons">
                            <button class="btn btn-default wizard-prev-btn" style="display: none;">${this.getLocalizedText('Previous', 'السابق')}</button>
                            <button class="btn btn-primary wizard-next-btn">${this.getLocalizedText('Next', 'التالي')}</button>
                            <button class="btn btn-success wizard-finish-btn" style="display: none;">${this.getLocalizedText('Finish', 'إنهاء')}</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    buildProgressIndicators() {
        const container = $('.step-indicators');
        container.empty();

        this.steps.forEach((step, index) => {
            const title = this.stepTitles[step][frappe.boot.lang] || this.stepTitles[step]['en'];
            const isCompleted = index < this.currentStep;
            const isCurrent = index === this.currentStep;

            const indicator = $(`
                <div class="step-indicator ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}" data-step="${index}">
                    <div class="step-number">${isCompleted ? '✓' : index + 1}</div>
                    <div class="step-title">${title}</div>
                </div>
            `);

            container.append(indicator);
        });
    }

    showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.totalSteps) return;

        this.currentStep = stepIndex;
        this.updateProgressIndicators();
        this.updateProgressBar();
        this.loadStepContent();
        this.updateNavigationButtons();
    }

    async loadStepContent() {
        const stepName = this.steps[this.currentStep];

        try {
            // Get field configuration for current step
            const fieldConfig = await this.getStepFields(stepName);

            // Build form HTML
            const formHTML = this.buildStepForm(stepName, fieldConfig);

            // Update content
            $('.wizard-step-content').html(formHTML);

            // Populate existing data
            this.populateStepData(stepName);

            // Setup step-specific functionality
            this.setupStepFeatures(stepName);

        } catch (error) {
            console.error('Error loading step content:', error);
            this.showError(__('Failed to load step content'));
        }
    }

    getStepFields(stepName) {
        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'universal_workshop.workshop_management.api.onboarding_wizard.get_onboarding_step_fields',
                args: { step_name: stepName },
                callback: (r) => {
                    if (r.message) {
                        resolve(r.message);
                    } else {
                        reject(new Error('Failed to get step fields'));
                    }
                }
            });
        });
    }

    buildStepForm(stepName, fields) {
        const lang = frappe.boot.lang || 'en';
        const title = this.stepTitles[stepName][lang] || this.stepTitles[stepName]['en'];

        let formHTML = `
            <div class="wizard-step" data-step="${stepName}">
                <h3 class="step-title">${title}</h3>
                <form class="wizard-form">
        `;

        fields.forEach(field => {
            formHTML += this.buildFieldHTML(field);
        });

        formHTML += `
                </form>
            </div>
        `;

        return formHTML;
    }

    buildFieldHTML(field) {
        const fieldName = field.fieldname;
        const label = field.label;
        const fieldType = field.fieldtype;
        const required = field.reqd ? 'required' : '';
        const options = field.options || '';

        // Determine if field is Arabic
        const isArabic = fieldName.includes('_ar') || label.includes('ا') || label.includes('ع');
        const direction = isArabic ? 'rtl' : 'ltr';
        const arabicAttr = isArabic ? 'data-arabic="true"' : '';

        let fieldHTML = `
            <div class="form-group">
                <label for="${fieldName}" class="control-label ${required}">${label}</label>
        `;

        if (fieldType === 'Data' || fieldType === 'Int') {
            const phoneAttr = fieldName.includes('phone') || fieldName.includes('mobile') ? 'data-phone="oman"' : '';
            fieldHTML += `
                <input type="${fieldType === 'Int' ? 'number' : 'text'}"
                       class="form-control"
                       id="${fieldName}"
                       name="${fieldName}"
                       dir="${direction}"
                       ${required}
                       ${arabicAttr}
                       ${phoneAttr}>
            `;
        } else if (fieldType === 'Select') {
            fieldHTML += `<select class="form-control" id="${fieldName}" name="${fieldName}" ${required}>`;
            fieldHTML += '<option value="">' + __('Select...') + '</option>';

            if (options) {
                options.split('\n').forEach(option => {
                    fieldHTML += `<option value="${option.trim()}">${option.trim()}</option>`;
                });
            }
            fieldHTML += '</select>';
        } else if (fieldType === 'Small Text' || fieldType === 'Text' || fieldType === 'Long Text') {
            const rows = fieldType === 'Long Text' ? 5 : 3;
            fieldHTML += `
                <textarea class="form-control"
                          id="${fieldName}"
                          name="${fieldName}"
                          rows="${rows}"
                          dir="${direction}"
                          ${required}
                          ${arabicAttr}></textarea>
            `;
        } else if (fieldType === 'Date') {
            fieldHTML += `
                <input type="date"
                       class="form-control"
                       id="${fieldName}"
                       name="${fieldName}"
                       ${required}>
            `;
        } else if (fieldType === 'Time') {
            fieldHTML += `
                <input type="time"
                       class="form-control"
                       id="${fieldName}"
                       name="${fieldName}"
                       ${required}>
            `;
        }

        fieldHTML += `
                <div class="field-error text-danger"></div>
            </div>
        `;

        return fieldHTML;
    }

    setupStepFeatures(stepName) {
        // Setup Arabic character validation
        $('[data-arabic="true"]').on('input', function () {
            const value = $(this).val();
            const hasArabic = /[\u0600-\u06FF]/.test(value);

            if (value && !hasArabic) {
                $(this).addClass('is-invalid');
                $(this).siblings('.field-error').text(__('This field must contain Arabic characters'));
            } else {
                $(this).removeClass('is-invalid');
                $(this).siblings('.field-error').text('');
            }
        });

        // Setup phone number formatting
        $('[data-phone="oman"]').on('input', function () {
            let value = $(this).val().replace(/\D/g, '');

            if (value.startsWith('968')) {
                value = '+' + value;
            } else if (value.length === 8) {
                value = '+968' + value;
            }

            $(this).val(value);
        });

        // Step-specific setups
        if (stepName === 'business_info') {
            this.setupBusinessValidation();
        } else if (stepName === 'contact_info') {
            this.setupContactValidation();
        } else if (stepName === 'operational_details') {
            this.setupOperationalValidation();
        }
    }

    setupBusinessValidation() {
        // Business license validation (7 digits)
        $('#business_license').on('input', function () {
            const value = $(this).val();
            const isValid = /^\d{7}$/.test(value);

            if (value && !isValid) {
                $(this).addClass('is-invalid');
                $(this).siblings('.field-error').text(__('Business license must be exactly 7 digits'));
            } else {
                $(this).removeClass('is-invalid');
                $(this).siblings('.field-error').text('');
            }
        });

        // VAT number validation
        $('#vat_number').on('input', function () {
            const value = $(this).val().toUpperCase();
            const isValid = /^OM\d{15}$/.test(value);

            if (value && !isValid) {
                $(this).addClass('is-invalid');
                $(this).siblings('.field-error').text(__('VAT number must be in format: OMxxxxxxxxxxxxxxx'));
            } else {
                $(this).removeClass('is-invalid');
                $(this).siblings('.field-error').text('');
            }

            $(this).val(value);
        });
    }

    setupContactValidation() {
        // Email validation
        $('#email').on('blur', function () {
            const value = $(this).val();
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (value && !emailRegex.test(value)) {
                $(this).addClass('is-invalid');
                $(this).siblings('.field-error').text(__('Invalid email address'));
            } else {
                $(this).removeClass('is-invalid');
                $(this).siblings('.field-error').text('');
            }
        });

        // Website validation
        $('#website').on('blur', function () {
            const value = $(this).val();
            const urlRegex = /^https?:\/\/.+/;

            if (value && !urlRegex.test(value)) {
                $(this).addClass('is-invalid');
                $(this).siblings('.field-error').text(__('Website must start with http:// or https://'));
            } else {
                $(this).removeClass('is-invalid');
                $(this).siblings('.field-error').text('');
            }
        });
    }

    setupOperationalValidation() {
        // Working hours validation
        $('#working_hours_start, #working_hours_end').on('change', function () {
            const startTime = $('#working_hours_start').val();
            const endTime = $('#working_hours_end').val();

            if (startTime && endTime && startTime >= endTime) {
                $('#working_hours_end').addClass('is-invalid');
                $('#working_hours_end').siblings('.field-error').text(__('End time must be after start time'));
            } else {
                $('#working_hours_end').removeClass('is-invalid');
                $('#working_hours_end').siblings('.field-error').text('');
            }
        });
    }

    populateStepData(stepName) {
        const data = this.stepData[stepName] || {};

        Object.keys(data).forEach(fieldName => {
            const field = $(`#${fieldName}`);
            if (field.length) {
                field.val(data[fieldName]);
            }
        });
    }

    populateExistingData() {
        // Populate all steps with existing data
        Object.keys(this.stepData).forEach(stepName => {
            this.populateStepData(stepName);
        });
    }

    collectStepData() {
        const stepName = this.steps[this.currentStep];
        const formData = {};

        $(`.wizard-step[data-step="${stepName}"] .wizard-form input, .wizard-step[data-step="${stepName}"] .wizard-form select, .wizard-step[data-step="${stepName}"] .wizard-form textarea`).each(function () {
            const field = $(this);
            const fieldName = field.attr('name');
            const value = field.val();

            if (fieldName && value) {
                formData[fieldName] = value;
            }
        });

        this.stepData[stepName] = formData;
        return formData;
    }

    async validateCurrentStep() {
        const stepName = this.steps[this.currentStep];
        const stepData = this.collectStepData();

        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'universal_workshop.workshop_management.api.onboarding_wizard.validate_step_data',
                args: {
                    step_name: stepName,
                    data: JSON.stringify(stepData)
                },
                callback: (r) => {
                    if (r.message && r.message.valid) {
                        resolve(true);
                    } else {
                        this.showValidationErrors(r.message.errors || []);
                        resolve(false);
                    }
                }
            });
        });
    }

    showValidationErrors(errors) {
        // Clear previous errors
        $('.field-error').text('');
        $('.form-control').removeClass('is-invalid');

        // Show new errors
        errors.forEach(error => {
            frappe.msgprint({
                title: __('Validation Error'),
                message: error,
                indicator: 'red'
            });
        });
    }

    async saveCurrentStep() {
        const stepName = this.steps[this.currentStep];
        const stepData = this.collectStepData();

        return new Promise((resolve, reject) => {
            frappe.call({
                method: 'universal_workshop.workshop_management.api.onboarding_wizard.save_step_data',
                args: {
                    progress_id: this.progressId,
                    step_name: stepName,
                    data: JSON.stringify(stepData)
                },
                callback: (r) => {
                    if (r.message && r.message.success) {
                        resolve(r.message);
                    } else {
                        this.showValidationErrors(r.message.errors || []);
                        reject(new Error('Failed to save step data'));
                    }
                }
            });
        });
    }

    async nextStep() {
        // Validate current step
        const isValid = await this.validateCurrentStep();
        if (!isValid) return;

        // Save current step
        try {
            await this.saveCurrentStep();
        } catch (error) {
            console.error('Error saving step:', error);
            return;
        }

        // Move to next step
        if (this.currentStep < this.totalSteps - 1) {
            this.showStep(this.currentStep + 1);
        }
    }

    prevStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }

    goToStep(stepIndex) {
        if (stepIndex >= 0 && stepIndex < this.totalSteps) {
            this.showStep(stepIndex);
        }
    }

    async finishWizard() {
        // Validate final step
        const isValid = await this.validateCurrentStep();
        if (!isValid) return;

        // Save final step
        try {
            await this.saveCurrentStep();
        } catch (error) {
            console.error('Error saving final step:', error);
            return;
        }

        // Complete onboarding
        frappe.call({
            method: 'universal_workshop.workshop_management.api.onboarding_wizard.complete_onboarding',
            args: {
                progress_id: this.progressId
            },
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.msgprint({
                        title: __('Onboarding Complete'),
                        message: __('Workshop onboarding completed successfully! Workshop Code: {0}').format(r.message.workshop_code),
                        primary_action: {
                            'label': __('Go to Workshop Profile'),
                            'action': () => {
                                frappe.set_route('Form', 'Workshop Profile', r.message.workshop_profile);
                            }
                        }
                    });

                    this.closeWizard();
                } else {
                    this.showError(__('Failed to complete onboarding'));
                }
            }
        });
    }

    cancelWizard() {
        frappe.confirm(
            __('Are you sure you want to cancel the onboarding process?'),
            () => {
                if (this.progressId) {
                    frappe.call({
                        method: 'universal_workshop.workshop_management.api.onboarding_wizard.rollback_onboarding',
                        args: {
                            progress_id: this.progressId,
                            reason: 'User cancelled'
                        },
                        callback: () => {
                            this.closeWizard();
                        }
                    });
                } else {
                    this.closeWizard();
                }
            }
        );
    }

    closeWizard() {
        $('.onboarding-wizard-container').remove();
    }

    updateProgressIndicators() {
        $('.step-indicator').each((index, element) => {
            const $indicator = $(element);
            $indicator.removeClass('completed current');

            if (index < this.currentStep) {
                $indicator.addClass('completed');
                $indicator.find('.step-number').text('✓');
            } else if (index === this.currentStep) {
                $indicator.addClass('current');
                $indicator.find('.step-number').text(index + 1);
            } else {
                $indicator.find('.step-number').text(index + 1);
            }
        });
    }

    updateProgressBar() {
        const progress = ((this.currentStep + 1) / this.totalSteps) * 100;
        $('.progress-fill').css('width', progress + '%');
    }

    updateNavigationButtons() {
        const prevBtn = $('.wizard-prev-btn');
        const nextBtn = $('.wizard-next-btn');
        const finishBtn = $('.wizard-finish-btn');

        // Previous button
        if (this.currentStep === 0) {
            prevBtn.hide();
        } else {
            prevBtn.show();
        }

        // Next/Finish buttons
        if (this.currentStep === this.totalSteps - 1) {
            nextBtn.hide();
            finishBtn.show();
        } else {
            nextBtn.show();
            finishBtn.hide();
        }
    }

    setupRTLSupport() {
        const lang = frappe.boot.lang || 'en';
        if (lang === 'ar') {
            $('.onboarding-wizard-container').addClass('rtl-layout');
            $('input[data-arabic="true"], textarea[data-arabic="true"]').attr('dir', 'rtl');
        }
    }

    handleArabicInput($field) {
        const value = $field.val();
        const hasArabic = /[\u0600-\u06FF]/.test(value);

        if (hasArabic) {
            $field.attr('dir', 'rtl');
        } else {
            $field.attr('dir', 'ltr');
        }
    }

    formatOmanPhone($field) {
        let value = $field.val().replace(/\D/g, '');

        if (value.length > 0) {
            if (value.startsWith('968')) {
                value = '+' + value.slice(0, 11);
            } else if (value.length <= 8) {
                value = '+968' + value;
            }
        }

        $field.val(value);
    }

    getLocalizedText(englishText, arabicText) {
        const lang = frappe.boot.lang || 'en';
        return lang === 'ar' ? arabicText : englishText;
    }

    showError(message) {
        frappe.msgprint({
            title: __('Error'),
            message: message,
            indicator: 'red'
        });
    }
}

// Initialize wizard when needed
frappe.ready(() => {
    // Make OnboardingWizard globally available
    window.OnboardingWizard = OnboardingWizard;
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OnboardingWizard;
}

/**
 * معالج التوجه التلقائي للداشبورد بعد إكمال الإعداد
 * Automatic redirect handler after setup completion
 */
frappe.setup_wizard_complete_handler = function (response) {
    if (response && response.status === 'success') {
        // عرض رسالة نجاح
        frappe.show_alert({
            message: __('System setup completed successfully! | تم إعداد النظام بنجاح!'),
            indicator: 'green'
        });

        // التوجه للداشبورد بعد ثانيتين
        setTimeout(() => {
            if (response.redirect_to) {
                window.location.href = response.redirect_to;
            } else {
                // رابط احتياطي
                window.location.href = '/app/universal-workshop-dashboard';
            }
        }, 2000);

        return true; // منع إعادة التحميل الافتراضية
    }
    return false;
};

/**
 * التحقق من حالة الإعداد عند تحميل الصفحة
 * Check setup status on page load
 */
$(document).ready(function () {
    // التحقق من حالة الإعداد للمستخدمين في صفحة /app
    if (window.location.pathname === '/app' || window.location.pathname === '/app/') {
        frappe.call({
            method: 'frappe.client.get_single_value',
            args: {
                doctype: 'System Settings',
                field: 'setup_complete'
            },
            callback: function (r) {
                if (r.message === '1') {
                    // الإعداد مكتمل، توجه للداشبورد
                    setTimeout(() => {
                        window.location.href = '/app/universal-workshop-dashboard';
                    }, 1000);
                }
            }
        });
    }
});
