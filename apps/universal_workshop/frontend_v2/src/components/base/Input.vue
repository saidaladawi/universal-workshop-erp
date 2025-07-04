<!--
  Input Component - Universal Workshop Frontend V2
  
  A comprehensive input component with validation, Arabic/RTL support,
  and integration with the design token system.
-->

<template>
  <div class="uw-input-wrapper" :class="wrapperClasses">
    <!-- Label -->
    <label
      v-if="label"
      :for="inputId"
      class="uw-input-label"
      :class="labelClasses"
    >
      {{ label }}
      <span v-if="required" class="uw-input-required">*</span>
    </label>
    
    <!-- Input container -->
    <div class="uw-input-container" :class="containerClasses">
      <!-- Leading icon -->
      <span
        v-if="iconStart"
        class="uw-input-icon uw-input-icon--start"
        v-html="iconStart"
      />
      
      <!-- Input element -->
      <input
        :id="inputId"
        ref="inputRef"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :min="min"
        :max="max"
        :step="step"
        :pattern="pattern"
        :autocomplete="autocomplete"
        :dir="inputDirection"
        class="uw-input"
        :class="inputClasses"
        @input="handleInput"
        @change="handleChange"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown="handleKeydown"
      />
      
      <!-- Trailing icon -->
      <span
        v-if="iconEnd"
        class="uw-input-icon uw-input-icon--end"
        v-html="iconEnd"
      />
      
      <!-- Clear button -->
      <button
        v-if="clearable && modelValue && !disabled && !readonly"
        type="button"
        class="uw-input-clear"
        @click="handleClear"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    
    <!-- Help text -->
    <div
      v-if="helpText || errorMessage"
      class="uw-input-help"
      :class="helpClasses"
    >
      {{ errorMessage || helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, nextTick } from 'vue'
import { ArabicUtils } from '@/localization/arabic/arabic-utils'

// Define component props
export interface InputProps {
  /** Input value (v-model) */
  modelValue?: string | number
  /** Input type */
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
  /** Input label */
  label?: string
  /** Input placeholder */
  placeholder?: string
  /** Help text */
  helpText?: string
  /** Error message */
  errorMessage?: string
  /** Input size */
  size?: 'sm' | 'md' | 'lg'
  /** Disabled state */
  disabled?: boolean
  /** Readonly state */
  readonly?: boolean
  /** Required field */
  required?: boolean
  /** Clearable input */
  clearable?: boolean
  /** Leading icon */
  iconStart?: string
  /** Trailing icon */
  iconEnd?: string
  /** Auto-detect text direction */
  autoDirection?: boolean
  /** Force text direction */
  direction?: 'ltr' | 'rtl'
  /** Input ID */
  id?: string
  /** Input name */
  name?: string
  /** Autocomplete */
  autocomplete?: string
  /** Min value (for number inputs) */
  min?: number
  /** Max value (for number inputs) */
  max?: number
  /** Step value (for number inputs) */
  step?: number
  /** Pattern (for validation) */
  pattern?: string
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface InputEmits {
  'update:modelValue': [value: string | number]
  change: [event: Event]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  keydown: [event: KeyboardEvent]
  clear: []
}

// Setup props with defaults
const props = withDefaults(defineProps<InputProps>(), {
  type: 'text',
  size: 'md',
  disabled: false,
  readonly: false,
  required: false,
  clearable: false,
  autoDirection: true,
})

// Setup emits
const emit = defineEmits<InputEmits>()

// Template refs
const inputRef = ref<HTMLInputElement>()

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Generate unique ID
const inputId = computed(() => props.id || `input-${Math.random().toString(36).substr(2, 9)}`)

// Compute input direction
const inputDirection = computed(() => {
  if (props.direction) {
    return props.direction
  }
  
  if (props.autoDirection && props.modelValue) {
    return ArabicUtils.getTextDirection(String(props.modelValue))
  }
  
  return isRTL ? 'rtl' : 'ltr'
})

// Computed classes
const wrapperClasses = computed(() => [
  'uw-input-wrapper',
  `uw-input-wrapper--${props.size}`,
  {
    'uw-input-wrapper--error': !!props.errorMessage,
    'uw-input-wrapper--disabled': props.disabled,
    'uw-input-wrapper--readonly': props.readonly,
    'uw-input-wrapper--rtl': isRTL,
  },
  props.class,
])

const containerClasses = computed(() => [
  'uw-input-container',
  `uw-input-container--${props.size}`,
  {
    'uw-input-container--error': !!props.errorMessage,
    'uw-input-container--disabled': props.disabled,
    'uw-input-container--readonly': props.readonly,
    'uw-input-container--with-start-icon': !!props.iconStart,
    'uw-input-container--with-end-icon': !!props.iconEnd,
    'uw-input-container--clearable': props.clearable && props.modelValue,
  },
])

const inputClasses = computed(() => [
  'uw-input',
  `uw-input--${props.size}`,
  {
    'uw-input--error': !!props.errorMessage,
    'uw-input--with-start-icon': !!props.iconStart,
    'uw-input--with-end-icon': !!props.iconEnd || (props.clearable && props.modelValue),
  },
])

const labelClasses = computed(() => [
  'uw-input-label',
  `uw-input-label--${props.size}`,
  {
    'uw-input-label--error': !!props.errorMessage,
    'uw-input-label--disabled': props.disabled,
  },
])

const helpClasses = computed(() => [
  'uw-input-help',
  {
    'uw-input-help--error': !!props.errorMessage,
  },
])

// Event handlers
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  let value: string | number = target.value
  
  // Convert to number for numeric inputs
  if (props.type === 'number' && value !== '') {
    value = Number(value)
  }
  
  emit('update:modelValue', value)
}

const handleChange = (event: Event) => {
  emit('change', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleKeydown = (event: KeyboardEvent) => {
  emit('keydown', event)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  
  // Focus input after clearing
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// Expose input element for parent access
defineExpose({
  inputRef,
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
  select: () => inputRef.value?.select(),
})
</script>

<style lang="scss" scoped>
.uw-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  
  &--rtl {
    text-align: right;
  }
}

// Label styles
.uw-input-label {
  display: block;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  transition: var(--transition-colors);
  
  &--sm {
    font-size: var(--font-size-sm);
  }
  
  &--md {
    font-size: var(--font-size-base);
  }
  
  &--lg {
    font-size: var(--font-size-lg);
  }
  
  &--error {
    color: var(--color-error);
  }
  
  &--disabled {
    color: var(--color-text-disabled);
  }
}

.uw-input-required {
  color: var(--color-error);
  margin-left: var(--spacing-1);
  
  [dir="rtl"] & {
    margin-left: 0;
    margin-right: var(--spacing-1);
  }
}

// Container styles
.uw-input-container {
  position: relative;
  display: flex;
  align-items: center;
  background-color: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  border-radius: var(--input-radius);
  transition: var(--transition-colors);
  
  &:focus-within {
    border-color: var(--color-border-focus);
    box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
  }
  
  &--error {
    border-color: var(--color-border-error);
    
    &:focus-within {
      border-color: var(--color-border-error);
      box-shadow: 0 0 0 2px rgba(244, 67, 54, 0.1);
    }
  }
  
  &--disabled {
    background-color: var(--color-surface-tertiary);
    cursor: not-allowed;
  }
  
  &--readonly {
    background-color: var(--color-surface-secondary);
  }
}

// Input styles
.uw-input {
  flex: 1;
  width: 100%;
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  font-family: inherit;
  outline: none;
  
  &::placeholder {
    color: var(--color-text-secondary);
  }
  
  &:disabled {
    cursor: not-allowed;
    color: var(--color-text-disabled);
    
    &::placeholder {
      color: var(--color-text-disabled);
    }
  }
  
  // Size variants
  &--sm {
    height: var(--input-height-sm);
    padding: var(--input-padding-sm);
    font-size: var(--font-size-sm);
  }
  
  &--md {
    height: var(--input-height-md);
    padding: var(--input-padding-md);
    font-size: var(--font-size-base);
  }
  
  &--lg {
    height: var(--input-height-lg);
    padding: var(--input-padding-lg);
    font-size: var(--font-size-lg);
  }
  
  // Icon adjustments
  &--with-start-icon {
    padding-left: var(--spacing-10);
    
    [dir="rtl"] & {
      padding-left: var(--spacing-3);
      padding-right: var(--spacing-10);
    }
  }
  
  &--with-end-icon {
    padding-right: var(--spacing-10);
    
    [dir="rtl"] & {
      padding-right: var(--spacing-3);
      padding-left: var(--spacing-10);
    }
  }
}

// Icon styles
.uw-input-icon {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  color: var(--color-text-secondary);
  pointer-events: none;
  
  &--start {
    left: var(--spacing-3);
    
    [dir="rtl"] & {
      left: auto;
      right: var(--spacing-3);
    }
  }
  
  &--end {
    right: var(--spacing-3);
    
    [dir="rtl"] & {
      right: auto;
      left: var(--spacing-3);
    }
  }
  
  svg {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

// Clear button
.uw-input-clear {
  position: absolute;
  right: var(--spacing-2);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.5em;
  height: 1.5em;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    color: var(--color-text-primary);
    background-color: var(--color-surface-secondary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 1px;
  }
  
  [dir="rtl"] & {
    right: auto;
    left: var(--spacing-2);
  }
}

// Help text styles
.uw-input-help {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-tight);
  
  &--error {
    color: var(--color-error);
  }
}

// Responsive design
@media (min-width: 768px) {
  .uw-input-container {
    // Larger touch targets on desktop
    min-height: 44px;
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-input-container {
    border-width: 2px;
    
    &:focus-within {
      border-width: 3px;
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-input-container,
  .uw-input-clear,
  .uw-input-label {
    transition: none;
  }
}
</style>