<template>
  <div class="step-container">
    <div class="step-header">
      <div class="step-icon">⚙️</div>
      <h2 class="step-title">{{ $t('Workshop Configuration') }}</h2>
      <p class="step-description">{{ $t('Configure your workshop settings and select modules') }}</p>
    </div>

    <div class="step-content">
      <form @submit.prevent="handleSubmit" class="workshop-form">
        <div class="logo-branding-section">
          <h3 class="section-title">{{ $t('Workshop Branding') }}</h3>
          
          <div class="logo-upload-container">
            <div class="logo-preview">
              <img 
                v-if="logoPreview" 
                :src="logoPreview" 
                alt="Workshop Logo" 
                class="logo-image"
              />
              <div v-else class="logo-placeholder">
                <i class="icon-upload"></i>
                <span>{{ $t('Upload Workshop Logo') }}</span>
              </div>
            </div>
            
            <div class="upload-controls">
              <input
                ref="logoInput"
                type="file"
                accept="image/png,image/jpeg,image/svg+xml"
                @change="handleLogoUpload"
                class="file-input"
                hidden
              />
              <button 
                type="button" 
                @click="$refs.logoInput.click()"
                class="btn btn-secondary"
              >
                {{ logoPreview ? $t('Change Logo') : $t('Upload Logo') }}
              </button>
              <button 
                v-if="logoPreview"
                type="button" 
                @click="removelogo"
                class="btn btn-outline"
              >
                {{ $t('Use Default') }}
              </button>
            </div>
            
            <p class="upload-hint">{{ $t('PNG, JPG, or SVG. Max 2MB. Recommended: 256x256px') }}</p>
          </div>
        </div>

        <div class="basic-settings-section">
          <h3 class="section-title">{{ $t('Basic Settings') }}</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Working Hours Start') }} *</label>
              <input
                v-model="formData.working_hours_start"
                type="time"
                class="form-control"
                required
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Working Hours End') }} *</label>
              <input
                v-model="formData.working_hours_end"
                type="time"
                class="form-control"
                required
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Weekend Days') }}</label>
              <select v-model="formData.weekend_days" class="form-control">
                <option value="Friday-Saturday">{{ $t('Friday - Saturday') }}</option>
                <option value="Friday">{{ $t('Friday Only') }}</option>
                <option value="Saturday-Sunday">{{ $t('Saturday - Sunday') }}</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Daily Service Capacity') }}</label>
              <input
                v-model="formData.service_capacity_daily"
                type="number"
                class="form-control"
                :placeholder="$t('Number of vehicles per day')"
                min="1"
                max="100"
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('Default Currency') }}</label>
            <select v-model="formData.currency" class="form-control">
              <option value="OMR">{{ $t('Omani Rial (OMR)') }}</option>
              <option value="USD">{{ $t('US Dollar (USD)') }}</option>
              <option value="EUR">{{ $t('Euro (EUR)') }}</option>
            </select>
          </div>
        </div>

        <div class="module-selection-section">
          <h3 class="section-title">{{ $t('Select Modules') }}</h3>
          <p class="section-description">
            {{ $t('Choose which modules to enable for your workshop. Core modules are always included.') }}
          </p>

          <div class="modules-grid">
            <!-- Core Modules (Always Enabled) -->
            <div class="module-category">
              <h4 class="category-title">
                <span class="category-icon">🔧</span>
                {{ $t('Core Modules (Always Included)') }}
              </h4>
              <div class="modules-list">
                <div 
                  v-for="module in coreModules" 
                  :key="module.key"
                  class="module-card core-module"
                >
                  <div class="module-icon">{{ module.icon }}</div>
                  <div class="module-content">
                    <h5 class="module-name">{{ $t(module.name) }}</h5>
                    <p class="module-description">{{ $t(module.description) }}</p>
                  </div>
                  <div class="module-status">
                    <span class="status-badge included">{{ $t('Included') }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Optional Modules -->
            <div class="module-category">
              <h4 class="category-title">
                <span class="category-icon">⭐</span>
                {{ $t('Optional Modules') }}
              </h4>
              <div class="modules-list">
                <div 
                  v-for="module in optionalModules" 
                  :key="module.key"
                  class="module-card optional-module"
                  :class="{ 
                    'selected': selectedModules.includes(module.key),
                    'disabled': !isModuleAvailable(module)
                  }"
                  @click="toggleModule(module.key)"
                >
                  <div class="module-icon">{{ module.icon }}</div>
                  <div class="module-content">
                    <h5 class="module-name">{{ $t(module.name) }}</h5>
                    <p class="module-description">{{ $t(module.description) }}</p>
                    <div v-if="module.license_required" class="license-requirement">
                      <span class="license-badge" :class="module.license_required">
                        {{ $t(`${module.license_required} License Required`) }}
                      </span>
                    </div>
                  </div>
                  <div class="module-status">
                    <div class="module-checkbox">
                      <input 
                        type="checkbox"
                        :checked="selectedModules.includes(module.key)"
                        :disabled="!isModuleAvailable(module)"
                        @click.stop
                        @change="toggleModule(module.key)"
                      />
                      <span class="checkmark">✓</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="license-info" v-if="licenseInfo">
            <div class="info-card">
              <div class="info-icon">📄</div>
              <div class="info-content">
                <h4>{{ $t('Your License') }}: {{ getLicenseTypeDisplay(licenseInfo.type) }}</h4>
                <p>{{ $t('You can enable modules up to your license level.') }}</p>
                <div class="license-features">
                  <span 
                    v-for="feature in getLicenseFeatures(licenseInfo.type)" 
                    :key="feature"
                    class="feature-tag"
                  >
                    {{ $t(feature) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="preferences-section">
          <h3 class="section-title">{{ $t('System Preferences') }}</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Default Language') }}</label>
              <select v-model="formData.default_language" class="form-control">
                <option value="en">{{ $t('English') }}</option>
                <option value="ar">{{ $t('العربية') }}</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Time Zone') }}</label>
              <select v-model="formData.timezone" class="form-control">
                <option value="Asia/Muscat">{{ $t('Asia/Muscat (Oman)') }}</option>
                <option value="Asia/Dubai">{{ $t('Asia/Dubai (UAE)') }}</option>
                <option value="UTC">{{ $t('UTC (Universal)') }}</option>
              </select>
            </div>
          </div>

          <div class="checkbox-group">
            <label class="checkbox-label">
              <input
                v-model="formData.enable_notifications"
                type="checkbox"
                class="checkbox-input"
              />
              <div class="checkbox-custom">
                <span v-if="formData.enable_notifications">✓</span>
              </div>
              <span class="checkbox-text">
                {{ $t('Enable system notifications') }}
              </span>
            </label>

            <label class="checkbox-label">
              <input
                v-model="formData.enable_auto_backup"
                type="checkbox"
                class="checkbox-input"
              />
              <div class="checkbox-custom">
                <span v-if="formData.enable_auto_backup">✓</span>
              </div>
              <span class="checkbox-text">
                {{ $t('Enable automatic daily backups') }}
              </span>
            </label>

            <label class="checkbox-label">
              <input
                v-model="formData.enable_dark_mode"
                type="checkbox"
                class="checkbox-input"
              />
              <div class="checkbox-custom">
                <span v-if="formData.enable_dark_mode">✓</span>
              </div>
              <span class="checkbox-text">
                {{ $t('Enable dark mode by default') }}
              </span>
            </label>
          </div>
        </div>
      </form>
    </div>

    <div class="step-footer">
      <button
        type="button"
        @click="$emit('previous')"
        class="btn btn-secondary"
      >
        <span class="btn-icon">←</span>
        {{ $t('Previous') }}
      </button>
      
      <button
        type="button"
        @click="handleSubmit"
        class="btn btn-primary"
        :disabled="!isFormValid || isValidating"
      >
        <span v-if="isValidating" class="loading-spinner">⏳</span>
        {{ $t('Complete Setup') }}
        <span class="btn-icon">🚀</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import OnboardingAPI from '@/api/onboarding'

const { t } = useI18n()

const emit = defineEmits(['next', 'previous', 'validate', 'complete'])

const props = defineProps<{
  modelValue?: any
  validationErrors?: any[]
  isLoading?: boolean
  licenseInfo?: any
}>()

const isValidating = ref(false)
const selectedModules = ref<string[]>([])
const logoPreview = ref<string | null>(null)
const logoFile = ref<File | null>(null)

const coreModules = [
  {
    key: 'workshop_management',
    name: 'Workshop Management',
    description: 'Core workshop operations, service orders, appointments',
    icon: '🔧'
  },
  {
    key: 'vehicle_management',
    name: 'Vehicle Management',
    description: 'VIN decoding, vehicle registry, service history',
    icon: '🚗'
  },
  {
    key: 'customer_management',
    name: 'Customer Management',
    description: 'CRM with Arabic support, loyalty programs',
    icon: '👥'
  },
  {
    key: 'billing_management',
    name: 'Billing Management',
    description: 'Omani VAT compliance, financial reporting',
    icon: '💰'
  }
]

const optionalModules = [
  {
    key: 'parts_inventory',
    name: 'Parts Inventory',
    description: 'Inventory management with barcode scanning',
    icon: '📦',
    license_required: 'basic'
  },
  {
    key: 'user_management',
    name: 'User Management',
    description: 'Enhanced security and session management',
    icon: '🔐',
    license_required: 'basic'
  },
  {
    key: 'training_management',
    name: 'Training Management',
    description: 'Technician training and certification tracking',
    icon: '🎓',
    license_required: 'premium'
  },
  {
    key: 'analytics_reporting',
    name: 'Analytics & Reporting',
    description: 'KPI dashboards and business intelligence',
    icon: '📊',
    license_required: 'premium'
  },
  {
    key: 'mobile_app',
    name: 'Mobile App',
    description: 'PWA and mobile interface for technicians',
    icon: '📱',
    license_required: 'enterprise'
  },
  {
    key: 'communication_management',
    name: 'Communication Management',
    description: 'SMS notifications and customer communication',
    icon: '📞',
    license_required: 'enterprise'
  }
]

const formData = ref({
  working_hours_start: '08:00',
  working_hours_end: '18:00',
  weekend_days: 'Friday-Saturday',
  service_capacity_daily: 20,
  currency: 'OMR',
  default_language: 'en',
  timezone: 'Asia/Muscat',
  enable_notifications: true,
  enable_auto_backup: true,
  enable_dark_mode: false,
  selected_modules: [],
  ...props.modelValue
})

const isFormValid = computed(() => {
  return (
    formData.value.working_hours_start &&
    formData.value.working_hours_end &&
    formData.value.weekend_days &&
    formData.value.currency
  )
})

const isModuleAvailable = (module: any) => {
  if (!props.licenseInfo) return true
  
  const licenseLevel = props.licenseInfo.type || 'basic'
  const requiredLevel = module.license_required || 'basic'
  
  const levels = { basic: 1, premium: 2, enterprise: 3 }
  return levels[licenseLevel] >= levels[requiredLevel]
}

const toggleModule = (moduleKey: string) => {
  const module = optionalModules.find(m => m.key === moduleKey)
  if (!module || !isModuleAvailable(module)) return
  
  const index = selectedModules.value.indexOf(moduleKey)
  if (index > -1) {
    selectedModules.value.splice(index, 1)
  } else {
    selectedModules.value.push(moduleKey)
  }
  
  formData.value.selected_modules = selectedModules.value
}

const handleLogoUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  // Validate file type
  const allowedTypes = ['image/png', 'image/jpeg', 'image/svg+xml']
  if (!allowedTypes.includes(file.type)) {
    alert(t('Please select a PNG, JPG, or SVG file'))
    return
  }
  
  // Validate file size (2MB limit)
  if (file.size > 2 * 1024 * 1024) {
    alert(t('File size must be less than 2MB'))
    return
  }
  
  logoFile.value = file
  
  // Create preview URL
  const reader = new FileReader()
  reader.onload = (e) => {
    logoPreview.value = e.target?.result as string
    // Include logo data in form
    formData.value.workshop_logo = logoPreview.value
  }
  reader.readAsDataURL(file)
}

const removelogo = () => {
  logoPreview.value = null
  logoFile.value = null
  formData.value.workshop_logo = null
  
  // Clear the file input
  const input = document.querySelector('input[type="file"]') as HTMLInputElement
  if (input) input.value = ''
}

const getLicenseTypeDisplay = (type: string) => {
  const types = {
    basic: t('Basic'),
    premium: t('Premium'),
    enterprise: t('Enterprise')
  }
  return types[type] || type
}

const getLicenseFeatures = (type: string) => {
  const features = {
    basic: ['Core Modules', 'Parts Inventory', 'User Management'],
    premium: ['All Basic Features', 'Training Management', 'Analytics & Reporting'],
    enterprise: ['All Premium Features', 'Mobile App', 'Communication Management']
  }
  return features[type] || []
}

const handleSubmit = async () => {
  if (!isFormValid.value) return
  
  isValidating.value = true
  
  try {
    // Update form data with selected modules
    formData.value.selected_modules = selectedModules.value
    
    const validation = await OnboardingAPI.validateStep('workshop_config', formData.value)
    
    if (validation.valid) {
      emit('complete')
    }
  } catch (error) {
    console.error('Workshop configuration validation failed:', error)
  } finally {
    isValidating.value = false
  }
}

watch(formData, (newValue) => {
  emit('validate', newValue)
}, { deep: true })

watch(selectedModules, (newValue) => {
  formData.value.selected_modules = newValue
}, { deep: true })

onMounted(() => {
  // Initialize selected modules from props
  if (props.modelValue?.selected_modules) {
    selectedModules.value = [...props.modelValue.selected_modules]
  }
})
</script>

<style scoped lang="scss">
.step-container {
  padding: 2rem;
  max-width: 800px;
  margin: 0 auto;
  
  @media (max-width: 768px) {
    padding: 1.5rem;
    max-width: 100%;
  }
  
  @media (max-width: 480px) {
    padding: 1rem;
  }
}

.step-header {
  text-align: center;
  margin-bottom: 2rem;

  .step-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .step-title {
    font-size: 1.8rem;
    font-weight: 600;
    color: #1a202c;
    margin-bottom: 0.5rem;
  }

  .step-description {
    color: #718096;
    font-size: 1rem;
    margin: 0;
  }
}

.step-content {
  margin-bottom: 2rem;
}

.basic-settings-section,
.module-selection-section,
.preferences-section {
  background: #f8fafc;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;

  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1a202c;
    margin-bottom: 1rem;
  }

  .section-description {
    color: #718096;
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
  }
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.form-group {
  margin-bottom: 1.5rem;

  .form-label {
    display: block;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .form-control {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.2s;

    &:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
  }
}

.logo-branding-section {
  margin-bottom: 2rem;
  
  .logo-upload-container {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1rem;
    
    @media (max-width: 768px) {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }
  }
  
  .logo-preview {
    width: 120px;
    height: 120px;
    border: 2px dashed #e2e8f0;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f8fafc;
    
    .logo-image {
      width: 100%;
      height: 100%;
      object-fit: contain;
      border-radius: 10px;
    }
    
    .logo-placeholder {
      text-align: center;
      color: #718096;
      
      .icon-upload {
        display: block;
        font-size: 2rem;
        margin-bottom: 0.5rem;
        
        &::before {
          content: "📸";
        }
      }
      
      span {
        font-size: 0.8rem;
      }
    }
  }
  
  .upload-controls {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    
    @media (max-width: 480px) {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5rem;
    }
  }
  
  .upload-hint {
    color: #718096;
    font-size: 0.8rem;
    margin-top: 0.5rem;
    margin-bottom: 0;
  }
}

.modules-grid {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.module-category {
  .category-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 1rem;

    .category-icon {
      font-size: 1.3rem;
    }
  }
}

.modules-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  @media (max-width: 480px) {
    gap: 0.5rem;
  }
}

.module-card {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem;
  background: white;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  transition: all 0.3s;
  
  @media (max-width: 768px) {
    padding: 0.875rem;
    border-radius: 8px;
  }
  
  @media (max-width: 480px) {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  .module-icon {
    font-size: 2rem;
    flex-shrink: 0;
    margin-top: 0.25rem;
  }

  .module-content {
    flex: 1;

    .module-name {
      font-size: 1rem;
      font-weight: 600;
      color: #1a202c;
      margin-bottom: 0.25rem;
    }

    .module-description {
      color: #718096;
      font-size: 0.85rem;
      margin-bottom: 0.5rem;
      line-height: 1.4;
    }

    .license-requirement {
      .license-badge {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-weight: 500;

        &.basic {
          background: #dbeafe;
          color: #1e40af;
        }

        &.premium {
          background: #fef3c7;
          color: #92400e;
        }

        &.enterprise {
          background: #d1fae5;
          color: #065f46;
        }
      }
    }
  }

  .module-status {
    flex-shrink: 0;
  }

  &.core-module {
    border-color: #10b981;
    background: #f0fdf4;

    .status-badge {
      background: #10b981;
      color: white;
      padding: 0.25rem 0.75rem;
      border-radius: 20px;
      font-size: 0.8rem;
      font-weight: 500;
    }
  }

  &.optional-module {
    cursor: pointer;

    &:hover:not(.disabled) {
      border-color: #667eea;
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }

    &.selected {
      border-color: #667eea;
      background: rgba(102, 126, 234, 0.05);
    }

    &.disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}

.module-checkbox {
  position: relative;
  width: 24px;
  height: 24px;

  input[type="checkbox"] {
    opacity: 0;
    position: absolute;
    width: 100%;
    height: 100%;
    margin: 0;
    cursor: pointer;

    &:disabled {
      cursor: not-allowed;
    }
  }

  .checkmark {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: white;
    border: 2px solid #d1d5db;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.8rem;
    transition: all 0.2s;
  }

  input[type="checkbox"]:checked + .checkmark {
    background: #667eea;
    border-color: #667eea;
  }

  input[type="checkbox"]:disabled + .checkmark {
    background: #f3f4f6;
    border-color: #e5e7eb;
  }
}

.license-info {
  margin-top: 1.5rem;

  .info-card {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    background: #e6fffa;
    border: 1px solid #81e6d9;
    border-radius: 8px;

    .info-icon {
      font-size: 1.5rem;
      margin-top: 0.25rem;
    }

    .info-content {
      h4 {
        font-size: 1rem;
        font-weight: 600;
        color: #234e52;
        margin-bottom: 0.5rem;
      }

      p {
        color: #285e61;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
      }

      .license-features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;

        .feature-tag {
          background: white;
          color: #285e61;
          padding: 0.25rem 0.5rem;
          border-radius: 12px;
          font-size: 0.8rem;
          font-weight: 500;
        }
      }
    }
  }
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
  margin-top: 0.125rem;

  span {
    color: white;
    font-size: 0.8rem;
  }
}

.checkbox-input:checked + .checkbox-custom {
  background: #667eea;
  border-color: #667eea;
}

.checkbox-text {
  color: #374151;
  font-size: 0.9rem;
  line-height: 1.4;
}

.step-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 2rem;
  border-top: 1px solid #e2e8f0;
}

.btn {
  padding: 0.875rem 2rem;
  border: none;
  border-radius: 50px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  &.btn-primary {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);

    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
  }

  &.btn-secondary {
    background: rgba(255, 255, 255, 0.9);
    color: #374151;
    border: 2px solid #e2e8f0;

    &:hover:not(:disabled) {
      background: #f7fafc;
      border-color: #cbd5e0;
    }
  }
}

.btn-icon {
  font-size: 1.1rem;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .steps-indicator {
    flex-direction: column;
    gap: 1rem;
  }
  
  .step-indicator {
    flex-direction: row;
    justify-content: flex-start;
    width: 100%;
    max-width: 300px;
  }
  
  .license-features {
    justify-content: flex-start !important;
  }
  
  .checkbox-group {
    gap: 0.75rem;
  }
  
  .form-row {
    gap: 0.75rem;
  }
}

@media (max-width: 480px) {
  .step-header {
    margin-bottom: 1.5rem;
  }
  
  .step-title {
    font-size: 1.5rem;
  }
  
  .step-description {
    font-size: 0.9rem;
  }
  
  .module-icon {
    font-size: 1.75rem;
  }
  
  .category-title {
    font-size: 1rem;
  }
  
  .module-name {
    font-size: 0.9rem;
  }
  
  .module-description {
    font-size: 0.8rem;
  }
}
</style>