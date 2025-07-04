<!--
  Badge Component - Universal Workshop Frontend V2
  
  A versatile badge component for displaying status, counts, and labels.
  Supports multiple variants, sizes, and Arabic/RTL layouts.
-->

<template>
  <span
    :class="badgeClasses"
    :style="badgeStyles"
    :aria-label="ariaLabel"
    role="img"
  >
    <!-- Leading icon -->
    <UWIcon
      v-if="iconStart"
      :name="iconStart"
      :size="iconSize"
      class="badge-icon badge-icon--start"
    />
    
    <!-- Badge content -->
    <span class="badge-content">
      <slot>{{ content }}</slot>
    </span>
    
    <!-- Trailing icon -->
    <UWIcon
      v-if="iconEnd"
      :name="iconEnd"
      :size="iconSize"
      class="badge-icon badge-icon--end"
    />
    
    <!-- Removable badge -->
    <button
      v-if="removable && !disabled"
      type="button"
      class="badge-remove"
      @click="handleRemove"
      :aria-label="`Remove ${content || 'badge'}`"
    >
      <UWIcon name="x" :size="iconSize" />
    </button>
  </span>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import UWIcon from '../Icon/Icon.vue'

// Define component props
export interface BadgeProps {
  /** Badge content */
  content?: string | number
  /** Badge variant */
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info'
  /** Badge size */
  size?: 'xs' | 'sm' | 'md' | 'lg'
  /** Badge shape */
  shape?: 'rounded' | 'pill' | 'square'
  /** Leading icon */
  iconStart?: string
  /** Trailing icon */
  iconEnd?: string
  /** Removable badge */
  removable?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Show dot instead of content */
  dot?: boolean
  /** Pulse animation */
  pulse?: boolean
  /** Custom background color */
  color?: string
  /** Custom text color */
  textColor?: string
  /** ARIA label for accessibility */
  ariaLabel?: string
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Define component emits
export interface BadgeEmits {
  remove: [event: MouseEvent]
  click: [event: MouseEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<BadgeProps>(), {
  variant: 'default',
  size: 'md',
  shape: 'rounded',
  removable: false,
  disabled: false,
  dot: false,
  pulse: false,
})

// Setup emits
const emit = defineEmits<BadgeEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Computed icon size based on badge size
const iconSize = computed(() => {
  const sizeMap = {
    xs: 'xs',
    sm: 'xs',
    md: 'sm',
    lg: 'md'
  }
  return sizeMap[props.size] as 'xs' | 'sm' | 'md'
})

// Computed classes
const badgeClasses = computed(() => [
  'uw-badge',
  `uw-badge--${props.variant}`,
  `uw-badge--${props.size}`,
  `uw-badge--${props.shape}`,
  {
    'uw-badge--disabled': props.disabled,
    'uw-badge--removable': props.removable,
    'uw-badge--dot': props.dot,
    'uw-badge--pulse': props.pulse,
    'uw-badge--icon-only': !props.content && !$slots.default && (props.iconStart || props.iconEnd),
    'uw-badge--rtl': isRTL,
  },
  props.class,
])

// Computed styles
const badgeStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  if (props.color) {
    styles.backgroundColor = props.color
  }
  
  if (props.textColor) {
    styles.color = props.textColor
  }
  
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    Object.assign(styles, props.style)
  }
  
  return styles
})

// Event handlers
const handleRemove = (event: MouseEvent) => {
  if (!props.disabled) {
    emit('remove', event)
  }
}

// Handle click on badge
const handleClick = (event: MouseEvent) => {
  if (!props.disabled) {
    emit('click', event)
  }
}
</script>

<script lang="ts">
export default {
  name: 'UWBadge'
}
</script>

<style lang="scss" scoped>
.uw-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-1);
  
  font-family: inherit;
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-none);
  text-align: center;
  vertical-align: middle;
  white-space: nowrap;
  user-select: none;
  
  border: 1px solid transparent;
  transition: var(--transition-colors);
  
  // Disabled state
  &--disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  // Dot variant
  &--dot {
    width: 0.5rem;
    height: 0.5rem;
    padding: 0;
    
    .badge-content {
      display: none;
    }
  }
  
  // Pulse animation
  &--pulse {
    animation: badge-pulse 2s ease-in-out infinite;
  }
  
  // Icon only badge
  &--icon-only {
    aspect-ratio: 1;
    
    .badge-content:empty {
      display: none;
    }
  }
  
  // RTL support
  &--rtl {
    .badge-icon--start {
      order: 2;
    }
    
    .badge-content {
      order: 1;
    }
    
    .badge-icon--end {
      order: 0;
    }
    
    .badge-remove {
      order: -1;
    }
  }
}

// Size variants
.uw-badge--xs {
  min-height: 1rem;
  padding: 0 var(--spacing-1);
  font-size: var(--font-size-xs);
  
  &.uw-badge--dot {
    width: 0.375rem;
    height: 0.375rem;
  }
}

.uw-badge--sm {
  min-height: 1.25rem;
  padding: 0 var(--spacing-1-5);
  font-size: var(--font-size-xs);
  
  &.uw-badge--dot {
    width: 0.5rem;
    height: 0.5rem;
  }
}

.uw-badge--md {
  min-height: 1.5rem;
  padding: 0 var(--spacing-2);
  font-size: var(--font-size-sm);
  
  &.uw-badge--dot {
    width: 0.625rem;
    height: 0.625rem;
  }
}

.uw-badge--lg {
  min-height: 2rem;
  padding: 0 var(--spacing-3);
  font-size: var(--font-size-base);
  
  &.uw-badge--dot {
    width: 0.75rem;
    height: 0.75rem;
  }
}

// Shape variants
.uw-badge--rounded {
  border-radius: var(--radius-md);
}

.uw-badge--pill {
  border-radius: var(--radius-full);
}

.uw-badge--square {
  border-radius: var(--radius-sm);
}

// Color variants
.uw-badge--default {
  background-color: var(--color-neutral-200);
  color: var(--color-neutral-800);
  border-color: var(--color-neutral-300);
}

.uw-badge--primary {
  background-color: var(--color-primary);
  color: var(--color-neutral-white);
  border-color: var(--color-primary);
}

.uw-badge--secondary {
  background-color: var(--color-secondary);
  color: var(--color-neutral-white);
  border-color: var(--color-secondary);
}

.uw-badge--success {
  background-color: var(--color-success);
  color: var(--color-neutral-white);
  border-color: var(--color-success);
}

.uw-badge--warning {
  background-color: var(--color-warning);
  color: var(--color-neutral-900);
  border-color: var(--color-warning);
}

.uw-badge--error {
  background-color: var(--color-error);
  color: var(--color-neutral-white);
  border-color: var(--color-error);
}

.uw-badge--info {
  background-color: var(--color-info);
  color: var(--color-neutral-white);
  border-color: var(--color-info);
}

// Badge content
.badge-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

// Badge icons
.badge-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: currentColor;
}

// Remove button
.badge-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  padding: 0;
  margin-left: var(--spacing-1);
  
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: currentColor;
  cursor: pointer;
  
  transition: var(--transition-colors);
  
  &:hover:not(:disabled) {
    background-color: rgba(255, 255, 255, 0.2);
  }
  
  &:focus {
    outline: 2px solid currentColor;
    outline-offset: 1px;
  }
  
  .uw-badge--rtl & {
    margin-left: 0;
    margin-right: var(--spacing-1);
  }
}

// Animations
@keyframes badge-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

// Light variant alternatives
.uw-badge--primary.uw-badge--light {
  background-color: var(--color-primary-lighter);
  color: var(--color-primary-dark);
  border-color: var(--color-primary-light);
}

.uw-badge--success.uw-badge--light {
  background-color: var(--color-success-lighter);
  color: var(--color-success-dark);
  border-color: var(--color-success-light);
}

.uw-badge--warning.uw-badge--light {
  background-color: var(--color-warning-lighter);
  color: var(--color-warning-dark);
  border-color: var(--color-warning-light);
}

.uw-badge--error.uw-badge--light {
  background-color: var(--color-error-lighter);
  color: var(--color-error-dark);
  border-color: var(--color-error-light);
}

.uw-badge--info.uw-badge--light {
  background-color: var(--color-info-lighter);
  color: var(--color-info-dark);
  border-color: var(--color-info-light);
}

// High contrast mode
[data-contrast="high"] {
  .uw-badge {
    border-width: 2px;
    font-weight: var(--font-weight-semibold);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-badge {
    transition: none;
  }
  
  .uw-badge--pulse {
    animation: none;
  }
}

// Print styles
@media print {
  .uw-badge {
    color: black !important;
    background: white !important;
    border: 1px solid black !important;
  }
}
</style>