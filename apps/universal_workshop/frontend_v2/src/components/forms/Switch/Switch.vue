<!--
  Switch Component - Universal Workshop Frontend V2
  
  A toggle switch component with smooth animations,
  Arabic/RTL support, and accessibility features.
-->

<template>
  <div
    :class="switchClasses"
    :style="switchStyles"
  >
    <label
      :class="labelClasses"
      :for="switchId"
    >
      <!-- Switch control -->
      <div class="switch-control">
        <input
          :id="switchId"
          ref="inputRef"
          v-model="internalValue"
          type="checkbox"
          :disabled="disabled"
          :required="required"
          :aria-describedby="helpText || errorMessage ? `${switchId}-help` : undefined"
          :aria-invalid="!!errorMessage"
          class="switch-input"
          @change="handleChange"
          @focus="handleFocus"
          @blur="handleBlur"
        />
        
        <div class="switch-track">
          <!-- Track background -->
          <div class="switch-track-bg" />
          
          <!-- Switch thumb -->
          <div class="switch-thumb">
            <!-- Icons for on/off states -->
            <UWIcon
              v-if="iconOn && isChecked"
              :name="iconOn"
              size="xs"
              class="switch-icon switch-icon--on"
            />
            <UWIcon
              v-else-if="iconOff && !isChecked"
              :name="iconOff"
              size="xs"
              class="switch-icon switch-icon--off"
            />
          </div>
          
          <!-- Loading indicator -->
          <div v-if="loading" class="switch-loading">
            <UWIcon name="loading" size="xs" spin />
          </div>
        </div>
      </div>
      
      <!-- Label content -->
      <div v-if="label || $slots.default" class="switch-content">
        <div class="switch-label">
          <slot>{{ label }}</slot>
          <span v-if="labelAr && isRTL" class="switch-label__ar">{{ labelAr }}</span>
          <span v-if="required" class="switch-label__required">*</span>
        </div>
        
        <div
          v-if="description"
          class="switch-description"
        >
          {{ description }}
          <span v-if="descriptionAr && isRTL" class="switch-description__ar">{{ descriptionAr }}</span>
        </div>
      </div>
    </label>
    
    <!-- Help text or error message -->
    <div
      v-if="helpText || errorMessage"
      :id="`${switchId}-help`"
      :class="helpClasses"
    >
      {{ errorMessage || helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import UWIcon from '@/components/primitives/Icon/Icon.vue'

// Define component props
export interface SwitchProps {
  /** Switch value for v-model */
  modelValue?: boolean
  /** Switch label */
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
  /** Loading state */
  loading?: boolean
  /** Icon for on state */
  iconOn?: string
  /** Icon for off state */
  iconOff?: string
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
export interface SwitchEmits {
  'update:modelValue': [value: boolean]
  'change': [checked: boolean]
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<SwitchProps>(), {
  size: 'md',
  variant: 'primary',
  disabled: false,
  required: false,
  loading: false,
  modelValue: false
})

// Setup emits
const emit = defineEmits<SwitchEmits>()

// Reactive state
const switchId = ref(`switch-${Math.random().toString(36).substr(2, 9)}`)
const inputRef = ref<HTMLInputElement>()

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Internal value handling
const internalValue = computed({
  get() {
    return props.modelValue
  },
  set(newValue) {
    if (!props.disabled && !props.loading) {
      emit('update:modelValue', newValue)
    }
  }
})

// Computed for checked state
const isChecked = computed(() => !!props.modelValue)

// Computed classes
const switchClasses = computed(() => [
  'uw-switch',
  `uw-switch--${props.size}`,
  `uw-switch--${props.variant}`,
  {
    'uw-switch--checked': isChecked.value,
    'uw-switch--disabled': props.disabled,
    'uw-switch--loading': props.loading,
    'uw-switch--error': props.errorMessage,
    'uw-switch--rtl': isRTL,
  },
  props.class,
])

const labelClasses = computed(() => [
  'switch-label-container',
  {
    'switch-label-container--disabled': props.disabled || props.loading,
  }
])

const helpClasses = computed(() => [
  'switch-help',
  {
    'switch-help--error': props.errorMessage,
  }
])

// Computed styles
const switchStyles = computed(() => {
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    return props.style
  }
  return {}
})

// Event handlers
const handleChange = () => {
  if (!props.disabled && !props.loading) {
    emit('change', isChecked.value)
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
  name: 'UWSwitch'
}
</script>

<style lang="scss" scoped>
.uw-switch {
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
.switch-label-container {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  cursor: pointer;
  
  &--disabled {
    cursor: not-allowed;
  }
  
  .uw-switch--rtl & {
    flex-direction: row-reverse;
  }
}

// Switch control
.switch-control {
  position: relative;
  flex-shrink: 0;
}

// Hidden input
.switch-input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  
  &:disabled {
    cursor: not-allowed;
  }
  
  &:focus + .switch-track {
    box-shadow: 0 0 0 3px var(--switch-color-light, var(--color-primary-lighter));
  }
}

// Switch track
.switch-track {
  position: relative;
  width: var(--switch-width, 2.75rem);
  height: var(--switch-height, 1.5rem);
  border-radius: var(--radius-full);
  transition: var(--transition-colors);
  
  // Track background
  .switch-track-bg {
    position: absolute;
    inset: 0;
    background: var(--color-neutral-300);
    border-radius: inherit;
    transition: var(--transition-colors);
    
    .uw-switch--checked & {
      background: var(--switch-color, var(--color-primary));
    }
    
    .uw-switch--error & {
      background: var(--color-error);
    }
  }
}

// Switch thumb
.switch-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: calc(var(--switch-height, 1.5rem) - 4px);
  height: calc(var(--switch-height, 1.5rem) - 4px);
  background: var(--color-neutral-white);
  border-radius: 50%;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s ease, background-color 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .uw-switch--checked & {
    transform: translateX(calc(var(--switch-width, 2.75rem) - var(--switch-height, 1.5rem)));
  }
  
  .uw-switch--rtl.uw-switch--checked & {
    transform: translateX(calc(-1 * (var(--switch-width, 2.75rem) - var(--switch-height, 1.5rem))));
  }
  
  .uw-switch--loading & {
    background: var(--color-neutral-100);
  }
}

// Switch icons
.switch-icon {
  color: var(--color-neutral-600);
  
  &--on {
    color: var(--switch-color, var(--color-primary));
  }
  
  &--off {
    color: var(--color-neutral-500);
  }
}

// Loading indicator
.switch-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--switch-color, var(--color-primary));
  z-index: 2;
}

// Content area
.switch-content {
  flex: 1;
  min-width: 0;
}

// Label text
.switch-label {
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
.switch-description {
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
.switch-help {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-left: calc(var(--switch-width, 2.75rem) + var(--spacing-3));
  
  &--error {
    color: var(--color-error);
  }
  
  .uw-switch--rtl & {
    margin-left: 0;
    margin-right: calc(var(--switch-width, 2.75rem) + var(--spacing-3));
  }
}

// Size variants
.uw-switch--sm {
  --switch-width: 2.25rem;
  --switch-height: 1.25rem;
  
  .switch-label {
    font-size: var(--font-size-sm);
  }
  
  .switch-description {
    font-size: var(--font-size-xs);
  }
}

.uw-switch--lg {
  --switch-width: 3.25rem;
  --switch-height: 1.75rem;
  
  .switch-label {
    font-size: var(--font-size-lg);
  }
}

// Color variants
.uw-switch--primary {
  --switch-color: var(--color-primary);
  --switch-color-light: var(--color-primary-lighter);
}

.uw-switch--success {
  --switch-color: var(--color-success);
  --switch-color-light: var(--color-success-lighter);
}

.uw-switch--warning {
  --switch-color: var(--color-warning);
  --switch-color-light: var(--color-warning-lighter);
}

.uw-switch--error {
  --switch-color: var(--color-error);
  --switch-color-light: var(--color-error-lighter);
}

// Hover states
.switch-label-container:hover:not(.switch-label-container--disabled) {
  .switch-track-bg {
    background: var(--color-neutral-400);
  }
  
  .uw-switch--checked & .switch-track-bg {
    background: var(--switch-color-dark, var(--switch-color, var(--color-primary)));
    filter: brightness(1.1);
  }
}

// High contrast mode
[data-contrast="high"] {
  .switch-track {
    border: 2px solid var(--color-border);
  }
  
  .switch-thumb {
    border: 2px solid var(--color-border);
  }
  
  .uw-switch--checked .switch-track {
    outline: 2px solid var(--color-background);
    outline-offset: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .switch-track,
  .switch-track-bg,
  .switch-thumb {
    transition: none;
  }
}

// Print styles
@media print {
  .uw-switch {
    color: black !important;
  }
  
  .switch-track-bg {
    background: white !important;
    border: 2px solid black !important;
  }
  
  .uw-switch--checked .switch-track-bg {
    background: black !important;
  }
  
  .switch-thumb {
    background: white !important;
    border: 2px solid black !important;
  }
}
</style>