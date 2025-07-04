<template>
  <div class="license-verification-step">
    <div class="step-header">
      <div class="step-icon">🔐</div>
      <h2 class="step-title">{{ texts.steps.license_verification }}</h2>
      <p class="step-description">
        {{ isArabic 
          ? 'أدخل رقم رخصة العمل الخاص بك للتحقق واستخراج معلومات الورشة'
          : 'Enter your business license key to verify and extract workshop information'
        }}
      </p>
    </div>

    <div class="form-container">
      <!-- License Key Input -->
      <div class="form-group">
        <label class="form-label">
          <i class="label-icon">📄</i>
          {{ isArabic ? 'رقم رخصة العمل' : 'Business License Key' }}
          <span class="required">*</span>
        </label>
        <div class="input-container">
          <input
            v-model="formData.license_key"
            type="text"
            class="form-input"
            :class="{ 'error': validationErrors.license_key, 'success': licenseValidated }"
            :placeholder="isArabic ? 'أدخل رقم الرخصة (7 أرقام)' : 'Enter 7-digit license number'"
            @input="onLicenseInput"
            @blur="validateLicense"
            maxlength="7"
          />
          <div class="input-status">
            <div v-if="isValidatingLicense" class="status-loading">
              <div class="spinner"></div>
            </div>
            <div v-else-if="licenseValidated" class="status-success">
              <i>✓</i>
            </div>
            <div v-else-if="validationErrors.license_key" class="status-error">
              <i>✕</i>
            </div>
          </div>
        </div>
        <div v-if="validationErrors.license_key" class="field-error">
          {{ validationErrors.license_key }}
        </div>
        <div v-else class="field-hint">
          {{ isArabic 
            ? 'رقم الرخصة التجارية العماني (7 أرقام)'
            : 'Oman business license number (7 digits)'
          }}
        </div>
      </div>

      <!-- Workshop Info Preview (shown after license validation) -->
      <div v-if="workshopInfo" class="workshop-preview">
        <h3 class="preview-title">
          <i>🏪</i>
          {{ isArabic ? 'معلومات الورشة' : 'Workshop Information' }}
        </h3>
        <div class="preview-content">
          <div class="info-row">
            <span class="info-label">{{ isArabic ? 'اسم الورشة (English)' : 'Workshop Name (English)' }}:</span>
            <span class="info-value">{{ workshopInfo.workshop_name_en }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ isArabic ? 'اسم الورشة (العربية)' : 'Workshop Name (Arabic)' }}:</span>
            <span class="info-value">{{ workshopInfo.workshop_name_ar }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ isArabic ? 'نوع الترخيص' : 'License Type' }}:</span>
            <span class="info-value license-type" :class="workshopInfo.license_type">
              {{ getLicenseTypeDisplay(workshopInfo.license_type) }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ isArabic ? 'الموقع' : 'Location' }}:</span>
            <span class="info-value">{{ workshopInfo.governorate }}, {{ isArabic ? 'عُمان' : 'Oman' }}</span>
          </div>
        </div>
      </div>

      <!-- Language Preference -->
      <div class="form-group">
        <label class="form-label">
          <i class="label-icon">🌐</i>
          {{ isArabic ? 'اللغة الأساسية' : 'Primary Language' }}
          <span class="required">*</span>
        </label>
        <div class="language-options">
          <div 
            v-for="option in languageOptions" 
            :key="option.value"
            class="language-option"
            :class="{ 'selected': formData.language_preference === option.value }"
            @click="selectLanguage(option.value)"
          >
            <div class="option-icon">{{ option.icon }}</div>
            <div class="option-content">
              <div class="option-title">{{ option.title }}</div>
              <div class="option-subtitle">{{ option.subtitle }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Terms Acceptance -->
      <div class="form-group">
        <div class="checkbox-container">
          <label class="checkbox-label">
            <input
              v-model="formData.terms_accepted"
              type="checkbox"
              class="checkbox-input"
              @change="validateForm"
            />
            <div class="checkbox-custom">
              <i v-if="formData.terms_accepted">✓</i>
            </div>
            <span class="checkbox-text">
              {{ isArabic 
                ? 'أوافق على شروط وأحكام الخدمة ولوائح حماية البيانات'
                : 'I accept the Terms of Service and Data Protection regulations'
              }}
              <span class="required">*</span>
            </span>
          </label>
        </div>
        <div v-if="validationErrors.terms_accepted" class="field-error">
          {{ validationErrors.terms_accepted }}
        </div>
      </div>

      <!-- License Features Preview -->
      <div v-if="workshopInfo && workshopInfo.features" class="features-preview">
        <h3 class="preview-title">
          <i>✨</i>
          {{ isArabic ? 'الميزات المتاحة' : 'Available Features' }}
        </h3>
        <div class="features-grid">
          <div 
            v-for="feature in workshopInfo.features" 
            :key="feature.key"
            class="feature-item"
            :class="{ 'available': feature.available }"
          >
            <i class="feature-icon">{{ feature.icon }}</i>
            <span class="feature-name">{{ isArabic ? feature.name_ar : feature.name_en }}</span>
            <i v-if="feature.available" class="feature-status available">✓</i>
            <i v-else class="feature-status unavailable">−</i>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LicenseVerificationStep',
  props: {
    texts: Object,
    data: Object,
    validationErrors: Object,
    isArabic: Boolean
  },
  
  data() {
    return {
      formData: {
        license_key: '',
        language_preference: 'both',
        terms_accepted: false
      },
      
      licenseValidated: false,
      isValidatingLicense: false,
      workshopInfo: null,
      
      languageOptions: [
        {
          value: 'ar',
          icon: '🇴🇲',
          title: this.isArabic ? 'العربية فقط' : 'Arabic Only',
          subtitle: this.isArabic ? 'الواجهة باللغة العربية' : 'Arabic interface'
        },
        {
          value: 'en', 
          icon: '🇬🇧',
          title: this.isArabic ? 'الإنجليزية فقط' : 'English Only',
          subtitle: this.isArabic ? 'الواجهة باللغة الإنجليزية' : 'English interface'
        },
        {
          value: 'both',
          icon: '🌐',
          title: this.isArabic ? 'العربية والإنجليزية' : 'Arabic & English',
          subtitle: this.isArabic ? 'دعم كامل للغتين' : 'Full bilingual support'
        }
      ]
    }
  },
  
  watch: {
    data: {
      immediate: true,
      handler(newData) {
        if (newData) {
          this.formData = { ...this.formData, ...newData }
        }
      }
    },
    
    formData: {
      deep: true,
      handler() {
        this.$emit('update', this.formData)
        this.validateForm()
      }
    }
  },
  
  methods: {
    onLicenseInput() {
      this.licenseValidated = false
      this.workshopInfo = null
      
      // Auto-format: Only allow numbers
      this.formData.license_key = this.formData.license_key.replace(/\D/g, '')
      
      // Auto-validate when 7 digits are entered
      if (this.formData.license_key.length === 7) {
        this.validateLicense()
      }
    },
    
    async validateLicense() {
      if (!this.formData.license_key || this.formData.license_key.length !== 7) {
        return
      }
      
      this.isValidatingLicense = true
      
      try {
        const response = await fetch('/api/method/universal_workshop.license_management.api.validate_business_license', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Frappe-CSRF-Token': window.csrf_token || ''
          },
          body: JSON.stringify({
            license_number: this.formData.license_key
          })
        })
        
        const result = await response.json()
        const data = result.message || result
        
        if (data.valid) {
          this.licenseValidated = true
          this.workshopInfo = {
            workshop_name_en: data.business_name_en || 'Professional Auto Workshop',
            workshop_name_ar: data.business_name_ar || 'ورشة السيارات المحترفة',
            license_type: data.license_type || 'basic',
            governorate: data.governorate || 'Muscat',
            features: this.getFeaturesByLicenseType(data.license_type || 'basic')
          }
          
          // Clear any validation errors
          this.$emit('validate', true, {})
        } else {
          this.licenseValidated = false
          this.workshopInfo = null
          this.$emit('validate', false, {
            license_key: this.isArabic 
              ? 'رقم الرخصة غير صحيح أو غير مسجل في النظام'
              : 'Invalid license number or not registered in the system'
          })
        }
      } catch (error) {
        console.error('License validation error:', error)
        this.licenseValidated = false
        this.workshopInfo = null
        this.$emit('validate', false, {
          license_key: this.isArabic 
            ? 'خطأ في التحقق من الرخصة. يرجى المحاولة مرة أخرى'
            : 'Error validating license. Please try again'
        })
      } finally {
        this.isValidatingLicense = false
      }
    },
    
    selectLanguage(value) {
      this.formData.language_preference = value
    },
    
    getLicenseTypeDisplay(type) {
      const types = {
        basic: this.isArabic ? 'أساسي' : 'Basic',
        premium: this.isArabic ? 'متقدم' : 'Premium', 
        enterprise: this.isArabic ? 'مؤسسي' : 'Enterprise'
      }
      return types[type] || type
    },
    
    getFeaturesByLicenseType(licenseType) {
      const allFeatures = [
        {
          key: 'workshop_management',
          icon: '🔧',
          name_en: 'Workshop Management',
          name_ar: 'إدارة الورشة',
          available: true // Always available
        },
        {
          key: 'vehicle_management',
          icon: '🚗', 
          name_en: 'Vehicle Management',
          name_ar: 'إدارة المركبات',
          available: true // Always available
        },
        {
          key: 'customer_management',
          icon: '👥',
          name_en: 'Customer Management', 
          name_ar: 'إدارة العملاء',
          available: true // Always available
        },
        {
          key: 'parts_inventory',
          icon: '📦',
          name_en: 'Parts Inventory',
          name_ar: 'مخزون قطع الغيار',
          available: licenseType !== 'basic' || true // Available for all
        },
        {
          key: 'training_management',
          icon: '🎓',
          name_en: 'Training Management',
          name_ar: 'إدارة التدريب',
          available: licenseType === 'premium' || licenseType === 'enterprise'
        },
        {
          key: 'analytics_reporting',
          icon: '📊',
          name_en: 'Analytics & Reporting',
          name_ar: 'التحليلات والتقارير',
          available: licenseType === 'premium' || licenseType === 'enterprise'
        },
        {
          key: 'mobile_app',
          icon: '📱',
          name_en: 'Mobile App',
          name_ar: 'التطبيق المحمول',
          available: licenseType === 'enterprise'
        },
        {
          key: 'communication_management',
          icon: '📞',
          name_en: 'Communication Management',
          name_ar: 'إدارة التواصل',
          available: licenseType === 'enterprise'
        }
      ]
      
      return allFeatures
    },
    
    validateForm() {
      const errors = {}
      
      // Validate license key
      if (!this.formData.license_key) {
        errors.license_key = this.isArabic 
          ? 'رقم الرخصة مطلوب'
          : 'License key is required'
      } else if (this.formData.license_key.length !== 7) {
        errors.license_key = this.isArabic 
          ? 'يجب أن يكون رقم الرخصة 7 أرقام'
          : 'License key must be 7 digits'
      } else if (!this.licenseValidated) {
        errors.license_key = this.isArabic 
          ? 'يرجى التحقق من صحة رقم الرخصة'
          : 'Please validate the license key'
      }
      
      // Validate language preference
      if (!this.formData.language_preference) {
        errors.language_preference = this.isArabic 
          ? 'يرجى اختيار اللغة المفضلة'
          : 'Please select language preference'
      }
      
      // Validate terms acceptance
      if (!this.formData.terms_accepted) {
        errors.terms_accepted = this.isArabic 
          ? 'يجب الموافقة على الشروط والأحكام'
          : 'You must accept the terms and conditions'
      }
      
      const isValid = Object.keys(errors).length === 0
      this.$emit('validate', isValid, errors)
    }
  },
  
  mounted() {
    // Initialize with any existing data
    if (this.data) {
      this.formData = { ...this.formData, ...this.data }
    }
    
    // Initial validation
    this.validateForm()
  }
}
</script>

<style scoped>
.license-verification-step {
  max-width: 600px;
  margin: 0 auto;
}

.step-header {
  text-align: center;
  margin-bottom: 3rem;
}

.step-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  display: block;
}

.step-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: #1e293b;
}

.step-description {
  font-size: 1.1rem;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #374151;
  font-size: 1rem;
}

.label-icon {
  font-size: 1.2rem;
}

.required {
  color: #ef4444;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input {
  width: 100%;
  padding: 1rem 3rem 1rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.form-input.success {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.input-status {
  position: absolute;
  right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.status-loading .spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.status-success {
  background: #10b981;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.status-error {
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.field-error {
  color: #ef4444;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}

.field-hint {
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}

/* Workshop Preview */
.workshop-preview {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
  border: 2px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.3rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 1rem 0;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 600;
  color: #374151;
  flex: 1;
}

.info-value {
  color: #1e293b;
  font-weight: 500;
  text-align: right;
}

.license-type {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.license-type.basic {
  background: #dbeafe;
  color: #1e40af;
}

.license-type.premium {
  background: #fef3c7;
  color: #92400e;
}

.license-type.enterprise {
  background: #d1fae5;
  color: #065f46;
}

/* Language Options */
.language-options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.language-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
}

.language-option:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.02);
}

.language-option.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.option-icon {
  font-size: 2rem;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
}

.option-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.25rem;
}

.option-subtitle {
  color: #6b7280;
  font-size: 0.9rem;
}

/* Checkbox */
.checkbox-container {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
  line-height: 1.5;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 24px;
  height: 24px;
  border: 2px solid #d1d5db;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.checkbox-input:checked + .checkbox-custom {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

.checkbox-text {
  color: #374151;
  font-size: 0.95rem;
}

/* Features Preview */
.features-preview {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 1.5rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.feature-item.available {
  border-color: #d1fae5;
  background: #f0fdf4;
}

.feature-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.feature-name {
  flex: 1;
  font-weight: 500;
  color: #374151;
}

.feature-status {
  font-size: 1.2rem;
  flex-shrink: 0;
}

.feature-status.available {
  color: #10b981;
}

.feature-status.unavailable {
  color: #9ca3af;
}

/* Animations */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .language-options {
    gap: 0.75rem;
  }
  
  .language-option {
    padding: 0.75rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
  
  .info-value {
    text-align: left;
  }
}
</style>