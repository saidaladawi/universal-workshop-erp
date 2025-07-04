<!--
  FormField Component - Universal Workshop Frontend V2
  
  A wrapper component that integrates form inputs with the validation system,
  providing automatic error display and validation triggers with Arabic/RTL support.
-->

<template>
  <div :class="fieldClasses">
    <!-- Label -->
    <label
      v-if="label || labelAr"
      :for="fieldId"
      class="uw-form-field-label"
      :class="labelClasses"
    >
      <span v-if="preferArabic && labelAr">{{ labelAr }}</span>
      <span v-else-if="label">{{ label }}</span>
      <span v-else-if="labelAr">{{ labelAr }}</span>
      <span v-if="required" class="uw-form-field-required">*</span>
    </label>

    <!-- Input wrapper -->
    <div class="uw-form-field-input">
      <slot
        :field-id="fieldId"
        :error-message="currentErrorMessage"
        :error-messages="currentErrorMessages"
        :has-error="hasError"
        :is-validating="isValidating"
        :is-valid="isValid"
        :value="currentValue"
        :set-value="setValue"
        :touch="touch"
        :validate="validate"
      />
    </div>

    <!-- Error messages -->
    <Transition name="error-message">
      <div
        v-if="showErrors && hasError"
        class="uw-form-field-errors"
        role="alert"
        :aria-live="errorAriaLive"
      >
        <div
          v-if="showSingleError"
          class="uw-form-field-error"
        >
          {{ currentErrorMessage }}
        </div>
        <ul v-else class="uw-form-field-error-list">
          <li
            v-for="(error, index) in currentErrorMessages"
            :key="index"
            class="uw-form-field-error"
          >
            {{ error }}
          </li>
        </ul>
      </div>
    </Transition>

    <!-- Help text -->
    <div
      v-if="helpText || helpTextAr"
      class="uw-form-field-help"
      :class="helpClasses"
    >
      <span v-if="preferArabic && helpTextAr">{{ helpTextAr }}</span>
      <span v-else-if="helpText">{{ helpText }}</span>
      <span v-else-if="helpTextAr">{{ helpTextAr }}</span>
    </div>

    <!-- Validation status indicator -->
    <div
      v-if="showValidationStatus"
      class="uw-form-field-status"
      :class="statusClasses"
    >
      <!-- Loading indicator -->
      <svg
        v-if="isValidating"
        class="uw-form-field-status-icon uw-form-field-status-loading"
        viewBox="0 0 24 24"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="2"
          fill="none"
          stroke-dasharray="60"
          stroke-dashoffset="60"
        />
      </svg>
      
      <!-- Success indicator -->
      <svg
        v-else-if="isValid && hasBeenValidated"
        class="uw-form-field-status-icon uw-form-field-status-success"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      
      <!-- Error indicator -->
      <svg
        v-else-if="hasError"
        class="uw-form-field-status-icon uw-form-field-status-error"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, watch } from 'vue'
import type { FieldState } from '@/composables/useValidation'

// Define component props
export interface FormFieldProps {
  /** Field name for validation */
  name: string
  /** Field label */
  label?: string
  /** Arabic field label */
  labelAr?: string
  /** Help text */
  helpText?: string
  /** Arabic help text */
  helpTextAr?: string
  /** Field is required */
  required?: boolean
  /** Show validation errors */
  showErrors?: boolean
  /** Show only first error or all errors */
  showSingleError?: boolean
  /** Show validation status icons */
  showValidationStatus?: boolean
  /** Field size */
  size?: 'sm' | 'md' | 'lg'
  /** Field is disabled */
  disabled?: boolean
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface FormFieldEmits {
  'update:modelValue': [value: any]
  'field-change': [name: string, value: any]
  'field-blur': [name: string]
  'field-focus': [name: string]
  'validation-change': [name: string, isValid: boolean, errors: string[]]
}

// Setup props with defaults
const props = withDefaults(defineProps<FormFieldProps>(), {
  showErrors: true,
  showSingleError: true,
  showValidationStatus: false,
  size: 'md',
  disabled: false,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<FormFieldEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Inject validation context (if available)
const validationContext = inject<{
  formData: Record<string, any>
  formState: { fields: Record<string, FieldState> }
  setFieldValue: (name: string, value: any) => void
  touchField: (name: string) => void
  validateField: (name: string) => Promise<any>
  getFieldError: (name: string) => string
  getFieldErrors: (name: string) => string[]
}>('validation-context', null as any)

// Generate unique field ID
const fieldId = computed(() => `form-field-${props.name}-${Math.random().toString(36).substr(2, 9)}`)

// Get field state from validation context
const fieldState = computed(() => {
  return validationContext?.formState.fields[props.name] || {
    value: undefined,
    touched: false,
    dirty: false,
    validating: false,
    errors: [],
    errorsAr: [],
    isValid: true
  }
})

// Current field value
const currentValue = computed(() => {
  return validationContext?.formData[props.name]
})

// Validation state
const isValidating = computed(() => fieldState.value.validating)
const isValid = computed(() => fieldState.value.isValid)
const hasError = computed(() => fieldState.value.errors.length > 0)
const hasBeenValidated = computed(() => fieldState.value.touched || fieldState.value.dirty)

// Error messages
const currentErrorMessage = computed(() => {
  if (!validationContext) return ''
  return validationContext.getFieldError(props.name)
})

const currentErrorMessages = computed(() => {
  if (!validationContext) return []
  return validationContext.getFieldErrors(props.name)
})

// ARIA live setting for error announcements
const errorAriaLive = computed(() => {
  return hasError.value ? 'assertive' : 'polite'
})

// Computed classes
const fieldClasses = computed(() => [
  'uw-form-field',
  `uw-form-field--${props.size}`,
  {
    'uw-form-field--required': props.required,
    'uw-form-field--disabled': props.disabled,
    'uw-form-field--error': hasError.value,
    'uw-form-field--valid': isValid.value && hasBeenValidated.value,
    'uw-form-field--validating': isValidating.value,
    'uw-form-field--rtl': isRTL,
    'uw-form-field--prefer-arabic': props.preferArabic,
  },
  props.class,
])

const labelClasses = computed(() => [
  'uw-form-field-label',
  {
    'uw-form-field-label--required': props.required,
    'uw-form-field-label--error': hasError.value,
    'uw-form-field-label--disabled': props.disabled,
  },
])

const helpClasses = computed(() => [
  'uw-form-field-help',
  {
    'uw-form-field-help--error': hasError.value,
  },
])

const statusClasses = computed(() => [
  'uw-form-field-status',
  {
    'uw-form-field-status--validating': isValidating.value,
    'uw-form-field-status--valid': isValid.value && hasBeenValidated.value,
    'uw-form-field-status--error': hasError.value,
  },
])

// Methods
const setValue = (value: any) => {
  if (validationContext) {
    validationContext.setFieldValue(props.name, value)
  }
  emit('update:modelValue', value)
  emit('field-change', props.name, value)
}

const touch = () => {
  if (validationContext) {
    validationContext.touchField(props.name)
  }
  emit('field-blur', props.name)
}

const validate = async () => {
  if (validationContext) {
    return await validationContext.validateField(props.name)
  }
}

// Watch for validation changes
watch(
  [isValid, () => fieldState.value.errors],
  ([valid, errors]) => {
    emit('validation-change', props.name, valid, errors)
  }
)

// Expose methods for parent components
defineExpose({
  fieldId,
  setValue,
  touch,
  validate,
  isValid,
  hasError,
  isValidating,
  currentValue,
  currentErrorMessage,
  currentErrorMessages,
})
</script>

<style lang="scss" scoped>
.uw-form-field {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  position: relative;
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
  
  // Size variants
  &--sm {
    gap: var(--spacing-1);
  }
  
  &--lg {
    gap: var(--spacing-3);
  }
  
  // State variants
  &--disabled {
    opacity: 0.6;
    pointer-events: none;
  }
}

// Label styles
.uw-form-field-label {
  display: block;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  transition: var(--transition-colors);
  
  .uw-form-field--sm & {
    font-size: var(--font-size-sm);
  }
  
  .uw-form-field--md & {
    font-size: var(--font-size-base);
  }
  
  .uw-form-field--lg & {
    font-size: var(--font-size-lg);
  }
  
  &--error {
    color: var(--color-error);
  }
  
  &--disabled {
    color: var(--color-text-disabled);
  }
}

.uw-form-field-required {
  color: var(--color-error);
  margin-inline-start: var(--spacing-1);
  font-weight: var(--font-weight-normal);
}

// Input wrapper
.uw-form-field-input {
  position: relative;
  flex: 1;
}

// Error styles
.uw-form-field-errors {
  margin-top: var(--spacing-1);
}

.uw-form-field-error {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-tight);
  
  .uw-form-field--sm & {
    font-size: var(--font-size-xs);
  }
}

.uw-form-field-error-list {
  list-style: none;
  margin: 0;
  padding: 0;
  
  .uw-form-field-error {
    margin-bottom: var(--spacing-1);
    
    &:last-child {
      margin-bottom: 0;
    }
    
    &::before {
      content: "•";
      margin-inline-end: var(--spacing-1);
    }
  }
}

// Help text styles
.uw-form-field-help {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  
  .uw-form-field--sm & {
    font-size: var(--font-size-xs);
  }
  
  &--error {
    color: var(--color-error-600);
  }
}

// Validation status styles
.uw-form-field-status {
  position: absolute;
  top: 0;
  right: var(--spacing-3);
  height: 100%;
  display: flex;
  align-items: center;
  pointer-events: none;
  
  .uw-form-field--rtl & {
    right: auto;
    left: var(--spacing-3);
  }
}

.uw-form-field-status-icon {
  width: var(--spacing-5);
  height: var(--spacing-5);
  flex-shrink: 0;
}

.uw-form-field-status-loading {
  color: var(--color-primary);
  animation: spin 1s linear infinite;
}

.uw-form-field-status-success {
  color: var(--color-success);
}

.uw-form-field-status-error {
  color: var(--color-error);
}

// Error message transitions
.error-message-enter-active,
.error-message-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.error-message-enter-from,
.error-message-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
}

.error-message-enter-to,
.error-message-leave-from {
  opacity: 1;
  max-height: 100px;
  margin-top: var(--spacing-1);
}

// Animations
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-form-field-help {
    color: var(--color-text-tertiary);
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-form-field--error {
    .uw-form-field-label {
      font-weight: var(--font-weight-bold);
    }
  }
  
  .uw-form-field-error {
    font-weight: var(--font-weight-medium);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-form-field-label,
  .error-message-enter-active,
  .error-message-leave-active,
  .uw-form-field-status-loading {
    transition: none;
    animation: none;
  }
}

// Print styles
@media print {
  .uw-form-field-status,
  .uw-form-field-errors {
    display: none;
  }
}
</style>