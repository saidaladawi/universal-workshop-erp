<!--
  Button Component - Universal Workshop Frontend V2
  
  A comprehensive button component with multiple variants, sizes, and states.
  Supports Arabic/RTL layouts and integrates with the design token system.
-->

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    :style="buttonStyles"
    @click="handleClick"
    @focus="handleFocus"
    @blur="handleBlur"
  >
    <!-- Loading spinner -->
    <div
      v-if="loading"
      class="button-spinner"
      :class="{ 'button-spinner--rtl': isRTL }"
    />
    
    <!-- Leading icon -->
    <span
      v-if="iconStart && !loading"
      class="button-icon button-icon--start"
      v-html="iconStart"
    />
    
    <!-- Button content -->
    <span class="button-content">
      <slot />
    </span>
    
    <!-- Trailing icon -->
    <span
      v-if="iconEnd && !loading"
      class="button-icon button-icon--end"
      v-html="iconEnd"
    />
  </button>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { designSystemUtils } from '@/design-system/utils'

// Define component props
export interface ButtonProps {
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  /** Button size */
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** Button type */
  type?: 'button' | 'submit' | 'reset'
  /** Disabled state */
  disabled?: boolean
  /** Loading state */
  loading?: boolean
  /** Full width button */
  fullWidth?: boolean
  /** Rounded button */
  rounded?: boolean
  /** Icon at start of button */
  iconStart?: string
  /** Icon at end of button */
  iconEnd?: string
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Define component emits
export interface ButtonEmits {
  click: [event: MouseEvent]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<ButtonProps>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
  rounded: false,
})

// Setup emits
const emit = defineEmits<ButtonEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Computed classes
const buttonClasses = computed(() => [
  'uw-button',
  `uw-button--${props.variant}`,
  `uw-button--${props.size}`,
  {
    'uw-button--disabled': props.disabled,
    'uw-button--loading': props.loading,
    'uw-button--full-width': props.fullWidth,
    'uw-button--rounded': props.rounded,
    'uw-button--icon-only': !$slots.default && (props.iconStart || props.iconEnd),
    'uw-button--rtl': isRTL,
  },
  props.class,
])

// Computed styles
const buttonStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    Object.assign(styles, props.style)
  }
  
  return styles
})

// Event handlers
const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}

const handleFocus = (event: FocusEvent) => {
  if (!props.disabled) {
    emit('focus', event)
  }
}

const handleBlur = (event: FocusEvent) => {
  if (!props.disabled) {
    emit('blur', event)
  }
}
</script>

<style lang="scss" scoped>
.uw-button {
  // Base styles using design tokens
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  
  border: none;
  border-radius: var(--button-radius-md);
  font-family: inherit;
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-none);
  text-decoration: none;
  cursor: pointer;
  user-select: none;
  
  transition: var(--transition-colors);
  
  // Focus ring
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  // Disabled state
  &--disabled {
    opacity: 0.6;
    cursor: not-allowed;
    
    &:focus {
      outline: none;
    }
  }
  
  // Loading state
  &--loading {
    cursor: wait;
    
    .button-content {
      opacity: 0.7;
    }
  }
  
  // Full width
  &--full-width {
    width: 100%;
  }
  
  // Rounded
  &--rounded {
    border-radius: var(--radius-full);
  }
  
  // Icon only button
  &--icon-only {
    padding: var(--spacing-2);
    
    &.uw-button--sm {
      padding: var(--spacing-1-5);
    }
    
    &.uw-button--lg {
      padding: var(--spacing-3);
    }
    
    &.uw-button--xl {
      padding: var(--spacing-4);
    }
  }
  
  // RTL support
  &--rtl {
    .button-icon--start {
      order: 2;
    }
    
    .button-content {
      order: 1;
    }
    
    .button-icon--end {
      order: 0;
    }
  }
}

// Size variants
.uw-button--sm {
  height: var(--button-height-sm);
  padding: var(--button-padding-sm);
  font-size: var(--font-size-sm);
  border-radius: var(--button-radius-sm);
}

.uw-button--md {
  height: var(--button-height-md);
  padding: var(--button-padding-md);
  font-size: var(--font-size-base);
  border-radius: var(--button-radius-md);
}

.uw-button--lg {
  height: var(--button-height-lg);
  padding: var(--button-padding-lg);
  font-size: var(--font-size-lg);
  border-radius: var(--button-radius-lg);
}

.uw-button--xl {
  height: var(--button-height-xl);
  padding: var(--button-padding-xl);
  font-size: var(--font-size-xl);
  border-radius: var(--button-radius-xl);
}

// Variant styles
.uw-button--primary {
  background-color: var(--color-primary);
  color: var(--color-neutral-white);
  
  &:hover:not(.uw-button--disabled) {
    background-color: var(--color-primary-dark);
  }
  
  &:active:not(.uw-button--disabled) {
    background-color: var(--color-primary-darker);
  }
}

.uw-button--secondary {
  background-color: var(--color-secondary);
  color: var(--color-neutral-white);
  
  &:hover:not(.uw-button--disabled) {
    background-color: var(--color-secondary-dark);
  }
  
  &:active:not(.uw-button--disabled) {
    background-color: var(--color-secondary-darker);
  }
}

.uw-button--outline {
  background-color: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  
  &:hover:not(.uw-button--disabled) {
    background-color: var(--color-primary);
    color: var(--color-neutral-white);
  }
  
  &:active:not(.uw-button--disabled) {
    background-color: var(--color-primary-dark);
  }
}

.uw-button--ghost {
  background-color: transparent;
  color: var(--color-primary);
  
  &:hover:not(.uw-button--disabled) {
    background-color: var(--color-primary-lighter);
  }
  
  &:active:not(.uw-button--disabled) {
    background-color: var(--color-primary-light);
  }
}

.uw-button--danger {
  background-color: var(--color-error);
  color: var(--color-neutral-white);
  
  &:hover:not(.uw-button--disabled) {
    background-color: var(--color-error-dark);
  }
  
  &:active:not(.uw-button--disabled) {
    background-color: var(--color-error-darker);
  }
}

// Button content
.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
}

// Button icons
.button-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  
  svg {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

// Loading spinner
.button-spinner {
  width: 1em;
  height: 1em;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: button-spin 1s linear infinite;
  
  &--rtl {
    animation-direction: reverse;
  }
}

@keyframes button-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

// Responsive design
@media (min-width: 768px) {
  .uw-button {
    // Larger touch targets on desktop
    min-height: 44px;
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-button {
    border: 2px solid currentColor;
    
    &--outline {
      border-width: 3px;
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-button {
    transition: none;
  }
  
  .button-spinner {
    animation: none;
    border: 2px solid currentColor;
    border-radius: 0;
  }
}
</style>