<!--
  Form Component - Universal Workshop Frontend V2
  
  A form wrapper that provides validation context to child FormField components
  and handles form submission with Arabic/RTL support.
-->

<template>
  <form
    :class="formClasses"
    :novalidate="noValidate"
    @submit="handleSubmit"
    @reset="handleReset"
  >
    <slot
      :form-data="formData"
      :form-state="formState"
      :is-valid="isFormValid"
      :is-validating="isFormValidating"
      :has-errors="hasFormErrors"
      :is-dirty="isFormDirty"
      :validate="validateForm"
      :reset="resetForm"
      :set-field-value="setFieldValue"
      :get-field-error="getFieldError"
      :get-field-errors="getFieldErrors"
    />
  </form>
</template>

<script setup lang="ts">
import { computed, inject, provide } from 'vue'
import { useValidation, type FormValidationConfig } from '@/composables/useValidation'

// Define component props
export interface FormProps {
  /** Initial form data */
  initialData?: Record<string, any>
  /** Validation configuration */
  validationConfig?: FormValidationConfig
  /** Validate on mount */
  validateOnMount?: boolean
  /** Stop validation on first error */
  stopOnFirstError?: boolean
  /** Disable HTML5 validation */
  noValidate?: boolean
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface FormEmits {
  submit: [data: Record<string, any>, isValid: boolean]
  'submit-valid': [data: Record<string, any>]
  'submit-invalid': [data: Record<string, any>, errors: string[]]
  reset: []
  'validation-change': [isValid: boolean, errors: string[]]
  'field-change': [fieldName: string, value: any]
}

// Setup props with defaults
const props = withDefaults(defineProps<FormProps>(), {
  initialData: () => ({}),
  validationConfig: () => ({}),
  validateOnMount: false,
  stopOnFirstError: false,
  noValidate: true,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<FormEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Initialize validation
const validation = useValidation(
  props.initialData,
  props.validationConfig,
  {
    preferArabic: props.preferArabic,
    validateOnMount: props.validateOnMount,
    stopOnFirstError: props.stopOnFirstError,
  }
)

// Destructure validation composable
const {
  formData,
  formState,
  isFormValid,
  isFormValidating,
  hasFormErrors,
  isFormDirty,
  setFieldValue,
  touchField,
  validateField,
  validateForm,
  resetForm,
  getFieldError,
  getFieldErrors,
} = validation

// Computed classes
const formClasses = computed(() => [
  'uw-form',
  {
    'uw-form--rtl': isRTL,
    'uw-form--prefer-arabic': props.preferArabic,
    'uw-form--validating': isFormValidating.value,
    'uw-form--valid': isFormValid.value,
    'uw-form--invalid': hasFormErrors.value,
    'uw-form--dirty': isFormDirty.value,
  },
  props.class,
])

// Provide validation context to child components
provide('validation-context', {
  formData,
  formState,
  setFieldValue: (name: string, value: any) => {
    setFieldValue(name, value)
    emit('field-change', name, value)
  },
  touchField,
  validateField,
  getFieldError,
  getFieldErrors,
})

// Event handlers
const handleSubmit = async (event: Event) => {
  event.preventDefault()
  
  const result = await validateForm()
  
  emit('submit', formData, result.isValid)
  
  if (result.isValid) {
    emit('submit-valid', formData)
  } else {
    emit('submit-invalid', formData, result.errors)
  }
}

const handleReset = (event: Event) => {
  event.preventDefault()
  resetForm()
  emit('reset')
}

// Watch for validation changes
const unwatchValidation = validation.formState
// Note: In a real implementation, we'd use a proper watcher here
// This is simplified for the component structure

// Expose validation methods and state
defineExpose({
  formData,
  formState,
  isFormValid,
  isFormValidating,
  hasFormErrors,
  isFormDirty,
  validateForm,
  validateField,
  resetForm,
  setFieldValue,
  touchField,
  getFieldError,
  getFieldErrors,
})
</script>

<style lang="scss" scoped>
.uw-form {
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
  
  // State classes for styling
  &--validating {
    opacity: 0.9;
  }
  
  &--valid {
    // Add any valid form styles if needed
  }
  
  &--invalid {
    // Add any invalid form styles if needed
  }
  
  &--dirty {
    // Add any dirty form styles if needed
  }
}

// Global form field spacing
.uw-form :deep(.uw-form-field + .uw-form-field) {
  margin-top: var(--spacing-4);
}

// Form sections
.uw-form :deep(.uw-form-section) {
  margin-bottom: var(--spacing-6);
  
  + .uw-form-section {
    border-top: 1px solid var(--color-border-primary);
    padding-top: var(--spacing-6);
  }
}

.uw-form :deep(.uw-form-section-title) {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-4);
}

.uw-form :deep(.uw-form-section-description) {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-4);
  line-height: var(--line-height-relaxed);
}

// Form actions
.uw-form :deep(.uw-form-actions) {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border-primary);
  
  .uw-form--rtl & {
    justify-content: flex-start;
  }
  
  &:not(.uw-form--rtl) {
    justify-content: flex-end;
  }
}

// Responsive form layout
@media (max-width: 640px) {
  .uw-form :deep(.uw-form-actions) {
    flex-direction: column;
    align-items: stretch;
    
    .uw-button {
      width: 100%;
      justify-content: center;
    }
  }
}

// Print styles
@media print {
  .uw-form :deep(.uw-form-actions) {
    display: none;
  }
}
</style>