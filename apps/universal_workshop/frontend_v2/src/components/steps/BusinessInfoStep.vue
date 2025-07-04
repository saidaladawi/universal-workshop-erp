<template>
  <div class="step-container">
    <div class="step-header">
      <div class="step-icon">📋</div>
      <h2 class="step-title">{{ $t('Business Information') }}</h2>
      <p class="step-description">{{ $t('Legal and business details for your workshop') }}</p>
    </div>

    <div class="step-content">
      <form @submit.prevent="handleSubmit" class="business-form">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">{{ $t('Business License Number') }} *</label>
            <input
              v-model="formData.business_license"
              type="text"
              class="form-control"
              :placeholder="$t('Enter business license number')"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('Tax Registration Number') }} *</label>
            <input
              v-model="formData.tax_number"
              type="text"
              class="form-control"
              :placeholder="$t('Enter tax registration number')"
              required
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">{{ $t('Business Type') }} *</label>
            <select v-model="formData.business_type" class="form-control" required>
              <option value="">{{ $t('Select business type') }}</option>
              <option value="sole_proprietorship">{{ $t('Sole Proprietorship') }}</option>
              <option value="partnership">{{ $t('Partnership') }}</option>
              <option value="llc">{{ $t('Limited Liability Company') }}</option>
              <option value="corporation">{{ $t('Corporation') }}</option>
            </select>
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('Established Year') }}</label>
            <input
              v-model.number="formData.established_year"
              type="number"
              class="form-control"
              :min="1900"
              :max="currentYear"
              :placeholder="$t('Year established')"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Business Address') }} *</label>
          <textarea
            v-model="formData.business_address"
            class="form-control"
            :placeholder="$t('Enter complete business address')"
            rows="2"
            required
          ></textarea>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">{{ $t('City') }} *</label>
            <input
              v-model="formData.city"
              type="text"
              class="form-control"
              :placeholder="$t('Enter city')"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('Postal Code') }}</label>
            <input
              v-model="formData.postal_code"
              type="text"
              class="form-control"
              :placeholder="$t('Enter postal code')"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Chamber of Commerce Registration') }}</label>
          <input
            v-model="formData.chamber_registration"
            type="text"
            class="form-control"
            :placeholder="$t('Enter chamber of commerce registration (if applicable)')"
          />
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Business Website') }}</label>
          <input
            v-model="formData.website"
            type="url"
            class="form-control"
            :placeholder="$t('Enter business website URL')"
          />
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Number of Employees') }}</label>
          <select v-model="formData.employee_count" class="form-control">
            <option value="">{{ $t('Select employee count') }}</option>
            <option value="1-5">1-5 {{ $t('employees') }}</option>
            <option value="6-10">6-10 {{ $t('employees') }}</option>
            <option value="11-25">11-25 {{ $t('employees') }}</option>
            <option value="26-50">26-50 {{ $t('employees') }}</option>
            <option value="50+">50+ {{ $t('employees') }}</option>
          </select>
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
        :disabled="!isFormValid"
      >
        {{ $t('Continue') }}
        <span class="btn-icon">→</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits(['next', 'previous', 'validate'])

const props = defineProps<{
  modelValue?: any
  validationErrors?: any[]
  isLoading?: boolean
}>()

const currentYear = new Date().getFullYear()

const formData = ref({
  business_license: '',
  tax_number: '',
  business_type: '',
  established_year: null,
  business_address: '',
  city: '',
  postal_code: '',
  chamber_registration: '',
  website: '',
  employee_count: '',
  ...props.modelValue
})

const isFormValid = computed(() => {
  return formData.value.business_license && 
         formData.value.tax_number && 
         formData.value.business_type &&
         formData.value.business_address &&
         formData.value.city
})

const handleSubmit = () => {
  if (isFormValid.value) {
    emit('next')
  }
}

watch(formData, (newValue) => {
  emit('validate', newValue)
}, { deep: true })
</script>

<style scoped lang="scss">
.step-container {
  padding: 2rem;
  max-width: 700px;
  margin: 0 auto;
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

  textarea.form-control {
    resize: vertical;
    min-height: 60px;
  }

  select.form-control {
    cursor: pointer;
  }
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
</style>