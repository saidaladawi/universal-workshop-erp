<template>
  <div class="step-container">
    <div class="step-header">
      <div class="step-icon">⚙️</div>
      <h2 class="step-title">{{ $t('Operational Details') }}</h2>
      <p class="step-description">{{ $t('Configure your workshop operations and preferences') }}</p>
    </div>

    <div class="step-content">
      <form @submit.prevent="handleSubmit" class="operational-form">
        <div class="form-section">
          <h3 class="section-title">{{ $t('Workshop Capacity') }}</h3>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Maximum Vehicles Per Day') }} *</label>
              <input
                v-model.number="formData.max_vehicles_per_day"
                type="number"
                class="form-control"
                :placeholder="$t('Enter maximum vehicles per day')"
                min="1"
                max="100"
                required
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Average Service Time (Hours)') }} *</label>
              <input
                v-model.number="formData.avg_service_time"
                type="number"
                class="form-control"
                :placeholder="$t('Average service time in hours')"
                min="0.5"
                max="24"
                step="0.5"
                required
              />
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Service Categories') }}</h3>
          <div class="service-categories">
            <div
              v-for="category in serviceCategories"
              :key="category.key"
              class="service-category"
            >
              <label class="category-label">
                <input
                  type="checkbox"
                  v-model="formData.service_categories"
                  :value="category.key"
                  class="category-checkbox"
                />
                <div class="category-card">
                  <div class="category-icon">{{ category.icon }}</div>
                  <div class="category-info">
                    <div class="category-name">{{ category.name }}</div>
                    <div class="category-description">{{ category.description }}</div>
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Inventory Management') }}</h3>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Parts Inventory System') }} *</label>
              <select v-model="formData.inventory_system" class="form-control" required>
                <option value="">{{ $t('Select inventory system') }}</option>
                <option value="basic">{{ $t('Basic - Manual tracking') }}</option>
                <option value="barcode">{{ $t('Barcode - Automated scanning') }}</option>
                <option value="rfid">{{ $t('RFID - Real-time tracking') }}</option>
                <option value="integrated">{{ $t('Integrated - ERP integration') }}</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Supplier Integration') }}</label>
              <select v-model="formData.supplier_integration" class="form-control">
                <option value="">{{ $t('Select supplier integration') }}</option>
                <option value="none">{{ $t('No integration') }}</option>
                <option value="basic">{{ $t('Basic - Manual orders') }}</option>
                <option value="automated">{{ $t('Automated - Electronic orders') }}</option>
                <option value="api">{{ $t('API - Real-time integration') }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Quality Control') }}</h3>
          <div class="quality-options">
            <label class="quality-option">
              <input
                type="checkbox"
                v-model="formData.quality_control_enabled"
                class="quality-checkbox"
              />
              <div class="quality-card">
                <div class="quality-icon">✅</div>
                <div class="quality-info">
                  <div class="quality-title">{{ $t('Enable Quality Control Checklists') }}</div>
                  <div class="quality-description">{{ $t('Mandatory quality checks before vehicle delivery') }}</div>
                </div>
              </div>
            </label>

            <label class="quality-option">
              <input
                type="checkbox"
                v-model="formData.photo_documentation"
                class="quality-checkbox"
              />
              <div class="quality-card">
                <div class="quality-icon">📸</div>
                <div class="quality-info">
                  <div class="quality-title">{{ $t('Photo Documentation') }}</div>
                  <div class="quality-description">{{ $t('Capture before/after photos of repairs') }}</div>
                </div>
              </div>
            </label>

            <label class="quality-option">
              <input
                type="checkbox"
                v-model="formData.customer_approval"
                class="quality-checkbox"
              />
              <div class="quality-card">
                <div class="quality-icon">👍</div>
                <div class="quality-info">
                  <div class="quality-title">{{ $t('Customer Approval Required') }}</div>
                  <div class="quality-description">{{ $t('Require customer approval for additional work') }}</div>
                </div>
              </div>
            </label>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Appointment System') }}</h3>
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">{{ $t('Appointment Buffer Time (Minutes)') }}</label>
              <input
                v-model.number="formData.appointment_buffer"
                type="number"
                class="form-control"
                :placeholder="$t('Buffer time between appointments')"
                min="0"
                max="120"
                step="15"
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Advance Booking Days') }}</label>
              <input
                v-model.number="formData.advance_booking_days"
                type="number"
                class="form-control"
                :placeholder="$t('How many days in advance can customers book?')"
                min="1"
                max="365"
              />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Special Requirements or Notes') }}</label>
          <textarea
            v-model="formData.special_requirements"
            class="form-control"
            :placeholder="$t('Any special operational requirements or notes')"
            rows="3"
          ></textarea>
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

const serviceCategories = [
  {
    key: 'general_maintenance',
    name: 'General Maintenance',
    description: 'Oil changes, filters, routine maintenance',
    icon: '🔧'
  },
  {
    key: 'engine_repair',
    name: 'Engine Repair',
    description: 'Engine diagnostics, rebuilds, performance',
    icon: '🏁'
  },
  {
    key: 'brake_service',
    name: 'Brake Service',
    description: 'Brake pads, rotors, brake system',
    icon: '🛑'
  },
  {
    key: 'transmission',
    name: 'Transmission',
    description: 'Automatic & manual transmission service',
    icon: '⚙️'
  },
  {
    key: 'electrical',
    name: 'Electrical',
    description: 'Wiring, battery, alternator, diagnostics',
    icon: '⚡'
  },
  {
    key: 'ac_heating',
    name: 'A/C & Heating',
    description: 'Climate control system service',
    icon: '❄️'
  },
  {
    key: 'body_work',
    name: 'Body Work',
    description: 'Collision repair, dent removal, painting',
    icon: '🔨'
  },
  {
    key: 'tire_service',
    name: 'Tire Service',
    description: 'Tire installation, balancing, alignment',
    icon: '🛞'
  }
]

const formData = ref({
  max_vehicles_per_day: 15,
  avg_service_time: 2,
  service_categories: ['general_maintenance', 'brake_service'],
  inventory_system: '',
  supplier_integration: '',
  quality_control_enabled: true,
  photo_documentation: false,
  customer_approval: true,
  appointment_buffer: 30,
  advance_booking_days: 14,
  special_requirements: '',
  ...props.modelValue
})

const isFormValid = computed(() => {
  return formData.value.max_vehicles_per_day && 
         formData.value.avg_service_time && 
         formData.value.inventory_system &&
         formData.value.service_categories.length > 0
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
  max-width: 800px;
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

.form-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;

  .section-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1a202c;
    margin-bottom: 1rem;
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

  select.form-control {
    cursor: pointer;
  }

  textarea.form-control {
    resize: vertical;
    min-height: 80px;
  }
}

.service-categories {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.service-category {
  .category-label {
    display: block;
    cursor: pointer;
    position: relative;
  }

  .category-checkbox {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .category-card {
    padding: 1rem;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;

    &:hover {
      border-color: #667eea;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }

  .category-checkbox:checked + .category-card {
    border-color: #667eea;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  }

  .category-icon {
    font-size: 1.8rem;
    min-width: 40px;
    text-align: center;
  }

  .category-name {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .category-description {
    font-size: 0.85rem;
    opacity: 0.9;
    line-height: 1.3;
  }
}

.quality-options {
  display: grid;
  gap: 1rem;
}

.quality-option {
  display: block;
  cursor: pointer;
  position: relative;

  .quality-checkbox {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  .quality-card {
    padding: 1rem;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;

    &:hover {
      border-color: #667eea;
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
  }

  .quality-checkbox:checked + .quality-card {
    border-color: #10b981;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
  }

  .quality-icon {
    font-size: 1.5rem;
    min-width: 30px;
    text-align: center;
  }

  .quality-title {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .quality-description {
    font-size: 0.85rem;
    opacity: 0.9;
    line-height: 1.3;
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