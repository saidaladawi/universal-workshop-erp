<!--
  Arabic Input Component - Universal Workshop Frontend V2
  
  A specialized input component for Arabic text with automatic direction detection,
  number conversion, and cultural formatting features.
-->

<template>
  <div class="uw-arabic-input-wrapper" :class="wrapperClasses">
    <!-- Label with Arabic support -->
    <label
      v-if="label || labelAr"
      :for="inputId"
      class="uw-arabic-input-label"
      :class="labelClasses"
    >
      <span v-if="preferArabic && labelAr" class="label-ar">{{ labelAr }}</span>
      <span v-if="!preferArabic && label" class="label-en">{{ label }}</span>
      <span v-if="preferArabic && label && !labelAr" class="label-fallback">{{ label }}</span>
      <span v-if="!preferArabic && labelAr && !label" class="label-fallback">{{ labelAr }}</span>
      <span v-if="required" class="uw-arabic-input-required">*</span>
    </label>
    
    <!-- Input container -->
    <div class="uw-arabic-input-container" :class="containerClasses">
      <!-- Leading icon -->
      <span
        v-if="iconStart"
        class="uw-arabic-input-icon uw-arabic-input-icon--start"
        v-html="iconStart"
      />
      
      <!-- Input element -->
      <input
        :id="inputId"
        ref="inputRef"
        :type="type"
        :value="displayValue"
        :placeholder="effectivePlaceholder"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :dir="inputDirection"
        class="uw-arabic-input"
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
        class="uw-arabic-input-icon uw-arabic-input-icon--end"
        v-html="iconEnd"
      />
      
      <!-- Number format toggle -->
      <button
        v-if="showNumberToggle && isNumeric"
        type="button"
        class="uw-arabic-input-toggle"
        :title="numberToggleTitle"
        @click="toggleNumberFormat"
      >
        {{ useArabicNumerals ? '123' : '٠١٢' }}
      </button>
      
      <!-- Clear button -->
      <button
        v-if="clearable && modelValue && !disabled && !readonly"
        type="button"
        class="uw-arabic-input-clear"
        @click="handleClear"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
          <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>
    
    <!-- Help text with Arabic support -->
    <div
      v-if="helpText || helpTextAr || errorMessage || errorMessageAr"
      class="uw-arabic-input-help"
      :class="helpClasses"
    >
      <span v-if="errorMessage || errorMessageAr">
        {{ (preferArabic ? errorMessageAr : errorMessage) || errorMessage || errorMessageAr }}
      </span>
      <span v-else>
        {{ (preferArabic ? helpTextAr : helpText) || helpText || helpTextAr }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, nextTick, watch } from 'vue'
import { ArabicUtils } from '@/localization/arabic/arabic-utils'

// Define component props
export interface ArabicInputProps {
  /** Input value (v-model) */
  modelValue?: string | number
  /** Input type */
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search'
  /** English label */
  label?: string
  /** Arabic label */
  labelAr?: string
  /** English placeholder */
  placeholder?: string
  /** Arabic placeholder */
  placeholderAr?: string
  /** English help text */
  helpText?: string
  /** Arabic help text */
  helpTextAr?: string
  /** English error message */
  errorMessage?: string
  /** Arabic error message */
  errorMessageAr?: string
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
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Auto-convert numbers to Arabic */
  useArabicNumerals?: boolean
  /** Show number format toggle button */
  showNumberToggle?: boolean
  /** Input ID */
  id?: string
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface ArabicInputEmits {
  'update:modelValue': [value: string | number]
  'update:useArabicNumerals': [value: boolean]
  change: [event: Event]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  keydown: [event: KeyboardEvent]
  clear: []
  'direction-change': [direction: 'ltr' | 'rtl']
}

// Setup props with defaults
const props = withDefaults(defineProps<ArabicInputProps>(), {
  type: 'text',
  size: 'md',
  disabled: false,
  readonly: false,
  required: false,
  clearable: false,
  autoDirection: true,
  preferArabic: true,
  useArabicNumerals: true,
  showNumberToggle: true,
})

// Setup emits
const emit = defineEmits<ArabicInputEmits>()

// Template refs
const inputRef = ref<HTMLInputElement>()

// Internal state
const internalUseArabicNumerals = ref(props.useArabicNumerals)

// Check if RTL context is available
const isRTL = inject('isRTL', true) // Default to RTL for Arabic components

// Generate unique ID
const inputId = computed(() => props.id || `arabic-input-${Math.random().toString(36).substr(2, 9)}`)

// Check if input is numeric
const isNumeric = computed(() => props.type === 'number' || props.type === 'tel')

// Compute input direction
const inputDirection = computed(() => {
  if (props.direction) {
    return props.direction
  }
  
  if (props.autoDirection && props.modelValue) {
    const direction = ArabicUtils.getTextDirection(String(props.modelValue))
    emit('direction-change', direction)
    return direction
  }
  
  return isRTL ? 'rtl' : 'ltr'
})

// Compute effective placeholder
const effectivePlaceholder = computed(() => {
  if (props.preferArabic && props.placeholderAr) {
    return props.placeholderAr
  }
  return props.placeholder || props.placeholderAr || ''
})

// Compute display value with number formatting
const displayValue = computed(() => {
  if (!props.modelValue) return ''
  
  const value = String(props.modelValue)
  
  if (isNumeric.value && internalUseArabicNumerals.value) {
    return ArabicUtils.convertToArabicNumerals(value)
  }
  
  return value
})

// Number toggle title
const numberToggleTitle = computed(() => {
  return internalUseArabicNumerals.value 
    ? 'التبديل إلى الأرقام الإنجليزية' 
    : 'Switch to Arabic numerals'
})

// Computed classes
const wrapperClasses = computed(() => [
  'uw-arabic-input-wrapper',
  `uw-arabic-input-wrapper--${props.size}`,
  {
    'uw-arabic-input-wrapper--error': !!(props.errorMessage || props.errorMessageAr),
    'uw-arabic-input-wrapper--disabled': props.disabled,
    'uw-arabic-input-wrapper--readonly': props.readonly,
    'uw-arabic-input-wrapper--rtl': inputDirection.value === 'rtl',
    'uw-arabic-input-wrapper--prefer-arabic': props.preferArabic,
  },
  props.class,
])

const containerClasses = computed(() => [
  'uw-arabic-input-container',
  `uw-arabic-input-container--${props.size}`,
  {
    'uw-arabic-input-container--error': !!(props.errorMessage || props.errorMessageAr),
    'uw-arabic-input-container--disabled': props.disabled,
    'uw-arabic-input-container--readonly': props.readonly,
    'uw-arabic-input-container--with-start-icon': !!props.iconStart,
    'uw-arabic-input-container--with-end-icon': !!props.iconEnd,
    'uw-arabic-input-container--with-toggle': isNumeric.value && props.showNumberToggle,
    'uw-arabic-input-container--clearable': props.clearable && props.modelValue,
  },
])

const inputClasses = computed(() => [
  'uw-arabic-input',
  `uw-arabic-input--${props.size}`,
  {
    'uw-arabic-input--error': !!(props.errorMessage || props.errorMessageAr),
    'uw-arabic-input--arabic': inputDirection.value === 'rtl',
    'uw-arabic-input--numeric': isNumeric.value,
    'uw-arabic-input--with-start-icon': !!props.iconStart,
    'uw-arabic-input--with-end-icon': !!props.iconEnd || (props.clearable && props.modelValue) || (isNumeric.value && props.showNumberToggle),
  },
])

const labelClasses = computed(() => [
  'uw-arabic-input-label',
  `uw-arabic-input-label--${props.size}`,
  {
    'uw-arabic-input-label--error': !!(props.errorMessage || props.errorMessageAr),
    'uw-arabic-input-label--disabled': props.disabled,
    'uw-arabic-input-label--arabic': props.preferArabic,
  },
])

const helpClasses = computed(() => [
  'uw-arabic-input-help',
  {
    'uw-arabic-input-help--error': !!(props.errorMessage || props.errorMessageAr),
    'uw-arabic-input-help--arabic': props.preferArabic,
  },
])

// Watch for changes in useArabicNumerals prop
watch(() => props.useArabicNumerals, (newValue) => {
  internalUseArabicNumerals.value = newValue
})

// Event handlers
const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  let value: string | number = target.value
  
  // Convert Arabic numerals to Latin for processing
  if (isNumeric.value && ArabicUtils.containsArabic(value)) {
    value = ArabicUtils.convertToLatinNumerals(value)
  }
  
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

const toggleNumberFormat = () => {
  internalUseArabicNumerals.value = !internalUseArabicNumerals.value
  emit('update:useArabicNumerals', internalUseArabicNumerals.value)
}

// Expose input element for parent access
defineExpose({
  inputRef,
  focus: () => inputRef.value?.focus(),
  blur: () => inputRef.value?.blur(),
  select: () => inputRef.value?.select(),
  toggleNumberFormat,
})
</script>

<style lang="scss" scoped>
.uw-arabic-input-wrapper {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
}

// Label styles with Arabic support
.uw-arabic-input-label {
  display: block;
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  transition: var(--transition-colors);
  
  &--arabic {
    font-family: var(--font-family-arabic);
    text-align: right;
  }
  
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

.label-ar {
  font-family: var(--font-family-arabic);
  direction: rtl;
}

.label-en {
  font-family: var(--font-family-latin);
  direction: ltr;
}

.label-fallback {
  opacity: 0.8;
}

.uw-arabic-input-required {
  color: var(--color-error);
  margin-inline-start: var(--spacing-1);
}

// Container styles
.uw-arabic-input-container {
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
.uw-arabic-input {
  flex: 1;
  width: 100%;
  border: none;
  background: transparent;
  color: var(--color-text-primary);
  font-family: inherit;
  outline: none;
  
  &--arabic {
    font-family: var(--font-family-arabic);
    text-align: right;
    direction: rtl;
  }
  
  &--numeric {
    font-variant-numeric: tabular-nums;
  }
  
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
    padding-inline-start: var(--spacing-10);
  }
  
  &--with-end-icon {
    padding-inline-end: var(--spacing-10);
  }
}

// Icon styles
.uw-arabic-input-icon {
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
    inset-inline-start: var(--spacing-3);
  }
  
  &--end {
    inset-inline-end: var(--spacing-3);
  }
  
  svg {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

// Number format toggle
.uw-arabic-input-toggle {
  position: absolute;
  inset-inline-end: var(--spacing-8);
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2em;
  height: 1.5em;
  border: 1px solid var(--color-border-primary);
  background: var(--color-surface-secondary);
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  font-size: 0.75em;
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    color: var(--color-text-primary);
    border-color: var(--color-border-secondary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 1px;
  }
}

// Clear button
.uw-arabic-input-clear {
  position: absolute;
  inset-inline-end: var(--spacing-2);
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
}

// Help text styles
.uw-arabic-input-help {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-tight);
  
  &--arabic {
    font-family: var(--font-family-arabic);
    text-align: right;
    direction: rtl;
  }
  
  &--error {
    color: var(--color-error);
  }
}

// Responsive design
@media (min-width: 768px) {
  .uw-arabic-input-container {
    min-height: 44px;
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-arabic-input-container {
    border-width: 2px;
    
    &:focus-within {
      border-width: 3px;
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-arabic-input-container,
  .uw-arabic-input-clear,
  .uw-arabic-input-toggle,
  .uw-arabic-input-label {
    transition: none;
  }
}
</style>