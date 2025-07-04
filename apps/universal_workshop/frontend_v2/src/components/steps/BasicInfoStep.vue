<template>
  <div class="step-container">
    <div class="step-header">
      <div class="step-icon">🏢</div>
      <h2 class="step-title">{{ $t('Workshop Information') }}</h2>
      <p class="step-description">{{ $t('Tell us about your automotive workshop') }}</p>
    </div>

    <div class="step-content">
      <form @submit.prevent="handleSubmit" class="workshop-form">
        <div class="form-group">
          <label class="form-label">{{ $t('Workshop Name') }} *</label>
          <input
            v-model="formData.workshop_name"
            type="text"
            class="form-control"
            :placeholder="$t('Enter your workshop name')"
            required
          />
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Workshop Type') }} *</label>
          <div class="workshop-types-grid">
            <div
              v-for="type in workshopTypes"
              :key="type.key"
              class="workshop-type-card"
              :class="{ active: formData.workshop_type === type.key }"
              @click="selectWorkshopType(type)"
            >
              <div class="type-icon">{{ type.icon }}</div>
              <div class="type-name">{{ type.name }}</div>
              <div class="type-description">{{ type.description }}</div>
            </div>
          </div>
        </div>

        <div class="form-group" v-if="formData.workshop_type">
          <label class="form-label">{{ $t('Primary Services') }}</label>
          <div class="services-list">
            <div
              v-for="service in selectedWorkshopServices"
              :key="service"
              class="service-tag"
            >
              {{ service }}
            </div>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Number of Service Bays') }}</label>
          <input
            v-model.number="formData.service_bays"
            type="number"
            class="form-control"
            :placeholder="$t('How many service bays do you have?')"
            min="1"
            max="50"
          />
        </div>

        <div class="form-group">
          <label class="form-label">{{ $t('Workshop Description') }}</label>
          <textarea
            v-model="formData.description"
            class="form-control"
            :placeholder="$t('Brief description of your workshop services')"
            rows="3"
          ></textarea>
        </div>
      </form>
    </div>

    <div class="step-footer">
      <button
        type="button"
        @click="$emit('next')"
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
import { useWorkshopTypes } from '@/composables/useWorkshopTypes'

const { t } = useI18n()
const { workshopTypes, getWorkshopTypeServices } = useWorkshopTypes()

const emit = defineEmits(['next', 'previous', 'validate'])

const props = defineProps<{
  modelValue?: any
  validationErrors?: any[]
  isLoading?: boolean
}>()

const formData = ref({
  workshop_name: '',
  workshop_type: '',
  service_bays: 3,
  description: '',
  ...props.modelValue
})

const selectedWorkshopServices = computed(() => {
  if (!formData.value.workshop_type) return []
  return getWorkshopTypeServices(formData.value.workshop_type)
})

const isFormValid = computed(() => {
  return formData.value.workshop_name && formData.value.workshop_type
})

const selectWorkshopType = (type: any) => {
  formData.value.workshop_type = type.key
}

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
  max-width: 600px;
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
    min-height: 80px;
  }
}

.workshop-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.workshop-type-card {
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;

  &:hover {
    border-color: #667eea;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  }

  &.active {
    border-color: #667eea;
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
  }

  .type-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .type-name {
    font-weight: 600;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
  }

  .type-description {
    font-size: 0.85rem;
    opacity: 0.9;
    line-height: 1.4;
  }
}

.services-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.service-tag {
  background: #e2e8f0;
  color: #374151;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.step-footer {
  display: flex;
  justify-content: flex-end;
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
}

.btn-icon {
  font-size: 1.1rem;
}
</style>