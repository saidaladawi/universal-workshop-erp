<!--
  Radio Group Component - Universal Workshop Frontend V2
  
  A comprehensive radio button group with Arabic/RTL support,
  validation, and accessibility features.
-->

<template>
  <fieldset
    :class="radioGroupClasses"
    :style="radioGroupStyles"
    :disabled="disabled"
  >
    <!-- Legend/Label -->
    <legend
      v-if="label"
      :class="legendClasses"
    >
      {{ label }}
      <span v-if="labelAr && isRTL" class="radio-legend__ar">{{ labelAr }}</span>
      <span v-if="required" class="radio-legend__required">*</span>
    </legend>
    
    <!-- Description -->
    <div
      v-if="description"
      class="radio-description"
    >
      {{ description }}
      <span v-if="descriptionAr && isRTL" class="radio-description__ar">{{ descriptionAr }}</span>
    </div>
    
    <!-- Radio options -->
    <div
      :class="optionsClasses"
      role="radiogroup"
      :aria-labelledby="label ? `${radioGroupId}-legend` : undefined"
      :aria-describedby="helpText || errorMessage ? `${radioGroupId}-help` : undefined"
      :aria-invalid="!!errorMessage"
    >
      <label
        v-for="(option, index) in options"
        :key="option.value"
        :class="getOptionLabelClasses(option)"
        :for="`${radioGroupId}-${index}`"
      >
        <!-- Radio input -->
        <input
          :id="`${radioGroupId}-${index}`"
          v-model="internalValue"
          type="radio"
          :value="option.value"
          :disabled="disabled || option.disabled"
          :required="required"
          class="radio-input"
          @change="handleChange"
          @focus="handleFocus"
          @blur="handleBlur"
        />
        
        <!-- Visual indicator -->
        <div class="radio-indicator">
          <div class="radio-dot" />
        </div>
        
        <!-- Option content -->
        <div class="radio-content">
          <!-- Icon -->
          <UWIcon
            v-if="option.icon"
            :name="option.icon"
            size="sm"
            class="radio-icon"
          />
          
          <!-- Label and description -->
          <div class="radio-text">
            <div class="radio-option-label">
              {{ getOptionLabel(option) }}
            </div>
            <div
              v-if="option.description"
              class="radio-option-description"
            >
              {{ getOptionDescription(option) }}
            </div>
          </div>
          
          <!-- Badge -->
          <UWBadge
            v-if="option.badge"
            v-bind="option.badge"
            size="xs"
            class="radio-badge"
          />
        </div>
      </label>
    </div>
    
    <!-- Help text or error message -->
    <div
      v-if="helpText || errorMessage"
      :id="`${radioGroupId}-help`"
      :class="helpClasses"
    >
      {{ errorMessage || helpText }}
    </div>
  </fieldset>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import UWIcon from '@/components/primitives/Icon/Icon.vue'
import UWBadge from '@/components/primitives/Badge/Badge.vue'
import type { BadgeProps } from '@/components/primitives/Badge/Badge.vue'

// Option interface
export interface RadioOption {
  label: string
  labelAr?: string
  value: any
  description?: string
  descriptionAr?: string
  icon?: string
  disabled?: boolean
  badge?: BadgeProps
}

// Define component props
export interface RadioGroupProps {
  /** Selected value */
  modelValue?: any
  /** Radio options */
  options: RadioOption[]
  /** Group label */
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
  /** Layout direction */
  direction?: 'vertical' | 'horizontal'
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
export interface RadioGroupEmits {
  'update:modelValue': [value: any]
  'change': [value: any, option: RadioOption]
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<RadioGroupProps>(), {
  direction: 'vertical',
  size: 'md',
  variant: 'primary',
  disabled: false,
  required: false
})

// Setup emits
const emit = defineEmits<RadioGroupEmits>()

// Reactive state
const radioGroupId = ref(`radio-group-${Math.random().toString(36).substr(2, 9)}`)

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Internal value handling
const internalValue = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    emit('update:modelValue', newValue)
  }
})

// Get option label with Arabic support
const getOptionLabel = (option: RadioOption): string => {
  if (isRTL.value && option.labelAr) {
    return option.labelAr
  }
  return option.label
}

// Get option description with Arabic support
const getOptionDescription = (option: RadioOption): string => {
  if (isRTL.value && option.descriptionAr) {
    return option.descriptionAr
  }
  return option.description || ''
}

// Computed classes
const radioGroupClasses = computed(() => [
  'uw-radio-group',
  `uw-radio-group--${props.size}`,
  `uw-radio-group--${props.variant}`,
  `uw-radio-group--${props.direction}`,
  {
    'uw-radio-group--disabled': props.disabled,
    'uw-radio-group--error': props.errorMessage,
    'uw-radio-group--rtl': isRTL,
  },
  props.class,
])

const legendClasses = computed(() => [
  'radio-legend',
  {
    'radio-legend--required': props.required,
    'radio-legend--disabled': props.disabled,
  }
])

const optionsClasses = computed(() => [
  'radio-options',
  `radio-options--${props.direction}`,
])

const helpClasses = computed(() => [
  'radio-help',
  {
    'radio-help--error': props.errorMessage,
  }
])

// Get option label classes
const getOptionLabelClasses = (option: RadioOption) => [
  'radio-option',
  {
    'radio-option--selected': option.value === props.modelValue,
    'radio-option--disabled': props.disabled || option.disabled,
  }
]

// Computed styles
const radioGroupStyles = computed(() => {
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    return props.style
  }
  return {}
})

// Event handlers
const handleChange = () => {
  const selectedOption = props.options.find(option => option.value === internalValue.value)
  if (selectedOption) {
    emit('change', internalValue.value, selectedOption)
  }
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}
</script>

<script lang="ts">
export default {
  name: 'UWRadioGroup'
}
</script>

<style lang="scss" scoped>
.uw-radio-group {
  border: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
  
  &--disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  &--rtl {
    text-align: right;
  }
}

// Legend/Label
.radio-legend {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  
  &__ar {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }
  
  &__required {
    color: var(--color-error);
  }
  
  &--disabled {
    color: var(--color-text-disabled);
  }
}

// Description
.radio-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  margin-bottom: var(--spacing-2);
  
  &__ar {
    font-size: var(--font-size-xs);
    color: var(--color-text-tertiary);
  }
}

// Options container
.radio-options {
  display: flex;
  gap: var(--spacing-3);
  
  &--vertical {
    flex-direction: column;
  }
  
  &--horizontal {
    flex-direction: row;
    flex-wrap: wrap;
  }
}

// Individual option
.radio-option {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover:not(&--disabled) {
    background: var(--color-background-hover);
  }
  
  &--selected {
    background: var(--color-background-subtle);
  }
  
  &--disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
}

// Hidden input
.radio-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  overflow: hidden;
  
  &:focus + .radio-indicator {
    box-shadow: 0 0 0 3px var(--radio-color, var(--color-primary-lighter));
  }
}

// Visual indicator
.radio-indicator {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--radio-size, 1.25rem);
  height: var(--radio-size, 1.25rem);
  background: var(--color-background-input);
  border: 2px solid var(--color-border-input);
  border-radius: 50%;
  transition: var(--transition-colors);
  flex-shrink: 0;
  margin-top: 0.125rem; // Align with text baseline
  
  // Selected state
  .radio-option--selected & {
    border-color: var(--radio-color, var(--color-primary));
  }
  
  // Error state
  .uw-radio-group--error & {
    border-color: var(--color-error);
  }
  
  // Hover state
  .radio-option:hover:not(.radio-option--disabled) & {
    border-color: var(--radio-color, var(--color-primary));
  }
}

// Radio dot
.radio-dot {
  width: 0.5rem;
  height: 0.5rem;
  background: var(--radio-color, var(--color-primary));
  border-radius: 50%;
  transform: scale(0);
  transition: transform 0.2s ease;
  
  .radio-option--selected & {
    transform: scale(1);
  }
}

// Content area
.radio-content {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  flex: 1;
  min-width: 0;
}

// Icon
.radio-icon {
  color: var(--color-text-secondary);
  margin-top: 0.125rem; // Align with text
  
  .radio-option--selected & {
    color: var(--radio-color, var(--color-primary));
  }
}

// Text content
.radio-text {
  flex: 1;
  min-width: 0;
}

.radio-option-label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
}

.radio-option-description {
  margin-top: var(--spacing-1);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

// Badge
.radio-badge {
  margin-top: 0.125rem; // Align with text
}

// Help text
.radio-help {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  
  &--error {
    color: var(--color-error);
  }
}

// Size variants
.uw-radio-group--sm {
  --radio-size: 1rem;
  
  .radio-legend {
    font-size: var(--font-size-sm);
  }
  
  .radio-option-label {
    font-size: var(--font-size-sm);
  }
  
  .radio-option-description {
    font-size: var(--font-size-xs);
  }
  
  .radio-dot {
    width: 0.375rem;
    height: 0.375rem;
  }
}

.uw-radio-group--lg {
  --radio-size: 1.5rem;
  
  .radio-legend {
    font-size: var(--font-size-lg);
  }
  
  .radio-option-label {
    font-size: var(--font-size-lg);
  }
  
  .radio-dot {
    width: 0.625rem;
    height: 0.625rem;
  }
}

// Color variants
.uw-radio-group--primary {
  --radio-color: var(--color-primary);
}

.uw-radio-group--success {
  --radio-color: var(--color-success);
}

.uw-radio-group--warning {
  --radio-color: var(--color-warning);
}

.uw-radio-group--error {
  --radio-color: var(--color-error);
}

// Horizontal layout adjustments
.radio-options--horizontal {
  .radio-option {
    flex: 1;
    min-width: 0;
  }
}

// High contrast mode
[data-contrast="high"] {
  .radio-indicator {
    border-width: 3px;
  }
  
  .radio-option--selected .radio-indicator {
    outline: 2px solid var(--color-background);
    outline-offset: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .radio-indicator,
  .radio-dot,
  .radio-option {
    transition: none;
  }
}

// Responsive design
@media (max-width: 768px) {
  .radio-options--horizontal {
    flex-direction: column;
  }
}

// Print styles
@media print {
  .uw-radio-group {
    color: black !important;
  }
  
  .radio-indicator {
    border: 2px solid black !important;
    background: white !important;
  }
  
  .radio-option--selected .radio-dot {
    background: black !important;
  }
}
</style>