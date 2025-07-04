<!--
  Checkbox Component - Universal Workshop Frontend V2
  
  A comprehensive checkbox component with indeterminate state,
  Arabic/RTL support, and accessibility features.
-->

<template>
  <div
    :class="checkboxClasses"
    :style="checkboxStyles"
  >
    <label
      :class="labelClasses"
      :for="checkboxId"
    >
      <!-- Checkbox input and visual indicator -->
      <div class="checkbox-control">
        <input
          :id="checkboxId"
          ref="inputRef"
          v-model="internalValue"
          type="checkbox"
          :value="value"
          :disabled="disabled"
          :required="required"
          :aria-describedby="helpText || errorMessage ? `${checkboxId}-help` : undefined"
          :aria-invalid="!!errorMessage"
          class="checkbox-input"
          @change="handleChange"
          @focus="handleFocus"
          @blur="handleBlur"
        />
        
        <div class="checkbox-indicator">
          <!-- Check icon -->
          <UWIcon
            v-if="isChecked && !indeterminate"
            name="check"
            size="xs"
            class="checkbox-icon checkbox-icon--check"
          />
          
          <!-- Indeterminate icon -->
          <UWIcon
            v-else-if="indeterminate"
            name="minus"
            size="xs"
            class="checkbox-icon checkbox-icon--indeterminate"
          />
        </div>
      </div>
      
      <!-- Label content -->
      <div class="checkbox-content">
        <div class="checkbox-label">
          <slot>{{ label }}</slot>
          <span v-if="labelAr && isRTL" class="checkbox-label__ar">{{ labelAr }}</span>
          <span v-if="required" class="checkbox-label__required">*</span>
        </div>
        
        <div
          v-if="description"
          class="checkbox-description"
        >
          {{ description }}
          <span v-if="descriptionAr && isRTL" class="checkbox-description__ar">{{ descriptionAr }}</span>
        </div>
      </div>
    </label>
    
    <!-- Help text or error message -->
    <div
      v-if="helpText || errorMessage"
      :id="`${checkboxId}-help`"
      :class="helpClasses"
    >
      {{ errorMessage || helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject, watch } from 'vue'
import UWIcon from '@/components/primitives/Icon/Icon.vue'

// Define component props
export interface CheckboxProps {
  /** Checkbox value for v-model */
  modelValue?: boolean | any[]
  /** Value when used in checkbox group */
  value?: any
  /** Checkbox label */
  label?: string
  /** Arabic label */
  labelAr?: string
  /** Description text */
  description?: string
  /** Arabic description */
  descriptionAr?: string
  /** Help text */
  helpText?: string
  /** Error message */
  errorMessage?: string
  /** Disabled state */
  disabled?: boolean
  /** Required field */
  required?: boolean
  /** Indeterminate state */
  indeterminate?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Color variant */
  variant?: 'primary' | 'success' | 'warning' | 'error'
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Define component emits
export interface CheckboxEmits {
  'update:modelValue': [value: boolean | any[]]
  'change': [checked: boolean, value?: any]
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<CheckboxProps>(), {
  size: 'md',
  variant: 'primary',
  disabled: false,
  required: false,
  indeterminate: false
})

// Setup emits
const emit = defineEmits<CheckboxEmits>()

// Reactive state
const checkboxId = ref(`checkbox-${Math.random().toString(36).substr(2, 9)}`)
const inputRef = ref<HTMLInputElement>()

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Internal value handling
const internalValue = computed({
  get() {
    if (Array.isArray(props.modelValue)) {
      return props.modelValue.includes(props.value)
    }
    return props.modelValue
  },
  set(newValue) {
    if (Array.isArray(props.modelValue)) {
      const currentArray = [...props.modelValue]
      if (newValue && !currentArray.includes(props.value)) {
        currentArray.push(props.value)
      } else if (!newValue && currentArray.includes(props.value)) {
        const index = currentArray.indexOf(props.value)
        currentArray.splice(index, 1)
      }
      emit('update:modelValue', currentArray)
    } else {
      emit('update:modelValue', newValue)
    }
  }
})

// Computed for checked state
const isChecked = computed(() => {
  if (Array.isArray(props.modelValue)) {
    return props.modelValue.includes(props.value)
  }
  return !!props.modelValue
})

// Computed classes
const checkboxClasses = computed(() => [
  'uw-checkbox',
  `uw-checkbox--${props.size}`,
  `uw-checkbox--${props.variant}`,
  {
    'uw-checkbox--checked': isChecked.value,
    'uw-checkbox--indeterminate': props.indeterminate,
    'uw-checkbox--disabled': props.disabled,
    'uw-checkbox--error': props.errorMessage,
    'uw-checkbox--rtl': isRTL,
  },
  props.class,
])

const labelClasses = computed(() => [
  'checkbox-label-container',
  {
    'checkbox-label-container--disabled': props.disabled,
  }
])

const helpClasses = computed(() => [
  'checkbox-help',
  {
    'checkbox-help--error': props.errorMessage,
  }
])

// Computed styles
const checkboxStyles = computed(() => {
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    return props.style
  }
  return {}
})

// Event handlers
const handleChange = () => {
  emit('change', isChecked.value, props.value)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

// Watch for indeterminate changes and update DOM
watch(() => props.indeterminate, (newVal) => {
  if (inputRef.value) {
    inputRef.value.indeterminate = newVal
  }
}, { immediate: true })
</script>

<script lang="ts">
export default {
  name: 'UWCheckbox'
}
</script>

<style lang="scss" scoped>
.uw-checkbox {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  
  &--disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &--rtl {
    text-align: right;
  }
}

// Label container
.checkbox-label-container {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  cursor: pointer;
  
  &--disabled {
    cursor: not-allowed;
  }
}

// Checkbox control (input + indicator)
.checkbox-control {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

// Hidden input
.checkbox-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  
  &:disabled {
    cursor: not-allowed;
  }
  
  &:focus + .checkbox-indicator {
    box-shadow: 0 0 0 3px var(--color-primary-lighter);
  }
}

// Visual indicator
.checkbox-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--checkbox-size, 1.25rem);
  height: var(--checkbox-size, 1.25rem);
  background: var(--color-background-input);
  border: 2px solid var(--color-border-input);
  border-radius: var(--radius-sm);
  transition: var(--transition-colors);
  
  // Checked state
  .uw-checkbox--checked & {
    background: var(--checkbox-color, var(--color-primary));
    border-color: var(--checkbox-color, var(--color-primary));
    color: var(--color-neutral-white);
  }
  
  // Indeterminate state
  .uw-checkbox--indeterminate & {
    background: var(--checkbox-color, var(--color-primary));
    border-color: var(--checkbox-color, var(--color-primary));
    color: var(--color-neutral-white);
  }
  
  // Error state
  .uw-checkbox--error & {
    border-color: var(--color-error);
  }
  
  // Hover state
  .checkbox-label-container:hover:not(.checkbox-label-container--disabled) & {
    border-color: var(--checkbox-color, var(--color-primary));
  }
}

// Icons
.checkbox-icon {
  color: currentColor;
  
  &--check {
    animation: checkbox-check-in 0.2s ease;
  }
  
  &--indeterminate {
    animation: checkbox-indeterminate-in 0.2s ease;
  }
}

// Content area
.checkbox-content {
  flex: 1;
  min-width: 0;
}

// Label text
.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  
  &__ar {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
  
  &__required {
    color: var(--color-error);
  }
}

// Description text
.checkbox-description {
  margin-top: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  
  &__ar {
    font-size: var(--font-size-xs);
    color: var(--color-text-tertiary);
  }
}

// Help text
.checkbox-help {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-left: calc(var(--checkbox-size, 1.25rem) + var(--spacing-2));
  
  &--error {
    color: var(--color-error);
  }
  
  .uw-checkbox--rtl & {
    margin-left: 0;
    margin-right: calc(var(--checkbox-size, 1.25rem) + var(--spacing-2));
  }
}

// Size variants
.uw-checkbox--sm {
  --checkbox-size: 1rem;
  
  .checkbox-label {
    font-size: var(--font-size-sm);
  }
  
  .checkbox-description {
    font-size: var(--font-size-xs);
  }
}

.uw-checkbox--lg {
  --checkbox-size: 1.5rem;
  
  .checkbox-label {
    font-size: var(--font-size-lg);
  }
}

// Color variants
.uw-checkbox--primary {
  --checkbox-color: var(--color-primary);
}

.uw-checkbox--success {
  --checkbox-color: var(--color-success);
}

.uw-checkbox--warning {
  --checkbox-color: var(--color-warning);
}

.uw-checkbox--error {
  --checkbox-color: var(--color-error);
}

// Animations
@keyframes checkbox-check-in {
  0% {
    opacity: 0;
    transform: scale(0.5);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes checkbox-indeterminate-in {
  0% {
    opacity: 0;
    transform: scaleX(0);
  }
  100% {
    opacity: 1;
    transform: scaleX(1);
  }
}

// High contrast mode
[data-contrast="high"] {
  .checkbox-indicator {
    border-width: 3px;
  }
  
  .uw-checkbox--checked .checkbox-indicator,
  .uw-checkbox--indeterminate .checkbox-indicator {
    outline: 2px solid var(--color-background);
    outline-offset: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .checkbox-indicator {
    transition: none;
  }
  
  .checkbox-icon {
    animation: none;
  }
}

// Print styles
@media print {
  .uw-checkbox {
    color: black !important;
  }
  
  .checkbox-indicator {
    border: 2px solid black !important;
    background: white !important;
  }
  
  .uw-checkbox--checked .checkbox-indicator {
    background: black !important;
  }
}
</style>