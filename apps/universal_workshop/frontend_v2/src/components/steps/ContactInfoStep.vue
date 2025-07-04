<template>
  <div class="step-container">
    <div class="step-header">
      <div class="step-icon">📞</div>
      <h2 class="step-title">{{ $t('Contact Information') }}</h2>
      <p class="step-description">{{ $t('How customers can reach your workshop') }}</p>
    </div>

    <div class="step-content">
      <form @submit.prevent="handleSubmit" class="contact-form">
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">{{ $t('Primary Phone Number') }} *</label>
            <input
              v-model="formData.primary_phone"
              type="tel"
              class="form-control"
              :placeholder="$t('Enter primary phone number')"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('Secondary Phone Number') }}</label>
            <input
              v-model="formData.secondary_phone"
              type="tel"
              class="form-control"
              :placeholder="$t('Enter secondary phone number')"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="form-label">{{ $t('Business Email') }} *</label>
            <input
              v-model="formData.business_email"
              type="email"
              class="form-control"
              :placeholder="$t('Enter business email address')"
              required
            />
          </div>

          <div class="form-group">
            <label class="form-label">{{ $t('Support Email') }}</label>
            <input
              v-model="formData.support_email"
              type="email"
              class="form-control"
              :placeholder="$t('Enter support email address')"
            />
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('WhatsApp Business Number') }}</label>
          <input
            v-model="formData.whatsapp_number"
            type="tel"
            class="form-control"
            :placeholder="$t('Enter WhatsApp business number')"
          />
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Business Hours') }}</h3>
          <div class="business-hours">
            <div 
              v-for="day in weekDays"
              :key="day.key"
              class="day-schedule"
            >
              <div class="day-name">{{ $t(day.name) }}</div>
              <div class="day-controls">
                <label class="checkbox-label">
                  <input
                    type="checkbox"
                    v-model="formData.business_hours[day.key].is_open"
                    class="day-checkbox"
                  />
                  {{ $t('Open') }}
                </label>
                <div v-if="formData.business_hours[day.key].is_open" class="time-inputs">
                  <input
                    v-model="formData.business_hours[day.key].open_time"
                    type="time"
                    class="time-input"
                  />
                  <span class="time-separator">-</span>
                  <input
                    v-model="formData.business_hours[day.key].close_time"
                    type="time"
                    class="time-input"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="form-section">
          <h3 class="section-title">{{ $t('Social Media & Online Presence') }}</h3>
          <div class="social-media-grid">
            <div class="form-group">
              <label class="form-label">{{ $t('Facebook Page') }}</label>
              <input
                v-model="formData.facebook_url"
                type="url"
                class="form-control"
                :placeholder="$t('Facebook page URL')"
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Instagram Profile') }}</label>
              <input
                v-model="formData.instagram_url"
                type="url"
                class="form-control"
                :placeholder="$t('Instagram profile URL')"
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('Google Business Profile') }}</label>
              <input
                v-model="formData.google_business_url"
                type="url"
                class="form-control"
                :placeholder="$t('Google Business profile URL')"
              />
            </div>

            <div class="form-group">
              <label class="form-label">{{ $t('YouTube Channel') }}</label>
              <input
                v-model="formData.youtube_url"
                type="url"
                class="form-control"
                :placeholder="$t('YouTube channel URL')"
              />
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Emergency Contact Number') }}</label>
          <input
            v-model="formData.emergency_contact"
            type="tel"
            class="form-control"
            :placeholder="$t('24/7 emergency contact number')"
          />
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

const weekDays = [
  { key: 'sunday', name: 'Sunday' },
  { key: 'monday', name: 'Monday' },
  { key: 'tuesday', name: 'Tuesday' },
  { key: 'wednesday', name: 'Wednesday' },
  { key: 'thursday', name: 'Thursday' },
  { key: 'friday', name: 'Friday' },
  { key: 'saturday', name: 'Saturday' }
]

const formData = ref({
  primary_phone: '',
  secondary_phone: '',
  business_email: '',
  support_email: '',
  whatsapp_number: '',
  business_hours: {
    sunday: { is_open: false, open_time: '09:00', close_time: '17:00' },
    monday: { is_open: true, open_time: '08:00', close_time: '18:00' },
    tuesday: { is_open: true, open_time: '08:00', close_time: '18:00' },
    wednesday: { is_open: true, open_time: '08:00', close_time: '18:00' },
    thursday: { is_open: true, open_time: '08:00', close_time: '18:00' },
    friday: { is_open: true, open_time: '08:00', close_time: '17:00' },
    saturday: { is_open: true, open_time: '09:00', close_time: '16:00' }
  },
  facebook_url: '',
  instagram_url: '',
  google_business_url: '',
  youtube_url: '',
  emergency_contact: '',
  ...props.modelValue
})

const isFormValid = computed(() => {
  return formData.value.primary_phone && formData.value.business_email
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

.business-hours {
  display: grid;
  gap: 1rem;
}

.day-schedule {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;

  .day-name {
    font-weight: 500;
    color: #374151;
    min-width: 80px;
  }

  .day-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.9rem;
    cursor: pointer;

    .day-checkbox {
      width: 16px;
      height: 16px;
    }
  }

  .time-inputs {
    display: flex;
    align-items: center;
    gap: 0.5rem;

    .time-input {
      padding: 0.5rem;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      font-size: 0.9rem;
      width: 90px;

      &:focus {
        outline: none;
        border-color: #667eea;
      }
    }

    .time-separator {
      color: #718096;
      font-weight: 500;
    }
  }
}

.social-media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
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