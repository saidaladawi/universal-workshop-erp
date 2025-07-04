<!--
  Card Component - Universal Workshop Frontend V2
  
  A flexible card component for content organization with support for
  headers, footers, and various styling options.
-->

<template>
  <div
    :class="cardClasses"
    :style="cardStyles"
    @click="handleClick"
  >
    <!-- Card Header -->
    <header
      v-if="$slots.header || title || subtitle"
      class="uw-card-header"
      :class="headerClasses"
    >
      <slot name="header">
        <div v-if="title || subtitle" class="uw-card-header-content">
          <h3 v-if="title" class="uw-card-title">{{ title }}</h3>
          <p v-if="subtitle" class="uw-card-subtitle">{{ subtitle }}</p>
        </div>
      </slot>
      
      <!-- Header actions -->
      <div v-if="$slots.actions" class="uw-card-actions">
        <slot name="actions" />
      </div>
    </header>
    
    <!-- Card Content -->
    <div
      v-if="$slots.default"
      class="uw-card-content"
      :class="contentClasses"
    >
      <slot />
    </div>
    
    <!-- Card Footer -->
    <footer
      v-if="$slots.footer"
      class="uw-card-footer"
      :class="footerClasses"
    >
      <slot name="footer" />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

// Define component props
export interface CardProps {
  /** Card title */
  title?: string
  /** Card subtitle */
  subtitle?: string
  /** Card variant */
  variant?: 'default' | 'outlined' | 'elevated' | 'filled'
  /** Card size */
  size?: 'sm' | 'md' | 'lg'
  /** Clickable card */
  clickable?: boolean
  /** Loading state */
  loading?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Custom padding */
  padding?: 'none' | 'sm' | 'md' | 'lg'
  /** Border radius */
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  /** Shadow level */
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Define component emits
export interface CardEmits {
  click: [event: MouseEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<CardProps>(), {
  variant: 'default',
  size: 'md',
  clickable: false,
  loading: false,
  disabled: false,
  padding: 'md',
  rounded: 'md',
  shadow: 'sm',
})

// Setup emits
const emit = defineEmits<CardEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Computed classes
const cardClasses = computed(() => [
  'uw-card',
  `uw-card--${props.variant}`,
  `uw-card--${props.size}`,
  `uw-card--padding-${props.padding}`,
  `uw-card--rounded-${props.rounded}`,
  `uw-card--shadow-${props.shadow}`,
  {
    'uw-card--clickable': props.clickable,
    'uw-card--loading': props.loading,
    'uw-card--disabled': props.disabled,
    'uw-card--rtl': isRTL,
  },
  props.class,
])

const headerClasses = computed(() => [
  'uw-card-header',
  `uw-card-header--${props.size}`,
  {
    'uw-card-header--rtl': isRTL,
  },
])

const contentClasses = computed(() => [
  'uw-card-content',
  `uw-card-content--${props.size}`,
  {
    'uw-card-content--rtl': isRTL,
  },
])

const footerClasses = computed(() => [
  'uw-card-footer',
  `uw-card-footer--${props.size}`,
  {
    'uw-card-footer--rtl': isRTL,
  },
])

// Computed styles
const cardStyles = computed(() => {
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
  if (props.clickable && !props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style lang="scss" scoped>
.uw-card {
  // Base styles using design tokens
  position: relative;
  display: flex;
  flex-direction: column;
  background-color: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
  overflow: hidden;
  transition: var(--transition-all);
  
  // Clickable state
  &--clickable {
    cursor: pointer;
    
    &:hover:not(.uw-card--disabled) {
      border-color: var(--color-border-secondary);
      transform: translateY(-1px);
    }
    
    &:active:not(.uw-card--disabled) {
      transform: translateY(0);
    }
    
    &:focus {
      outline: 2px solid var(--color-primary);
      outline-offset: 2px;
    }
  }
  
  // Loading state
  &--loading {
    opacity: 0.8;
    pointer-events: none;
    
    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        90deg,
        transparent 25%,
        rgba(255, 255, 255, 0.5) 50%,
        transparent 75%
      );
      animation: card-loading 1.5s infinite;
    }
  }
  
  // Disabled state
  &--disabled {
    opacity: 0.6;
    cursor: not-allowed;
    
    &:focus {
      outline: none;
    }
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
  }
}

// Variant styles
.uw-card--default {
  background-color: var(--color-surface-primary);
  border: 1px solid var(--color-border-primary);
}

.uw-card--outlined {
  background-color: transparent;
  border: 2px solid var(--color-border-primary);
}

.uw-card--elevated {
  background-color: var(--color-surface-primary);
  border: none;
  box-shadow: var(--shadow-lg);
}

.uw-card--filled {
  background-color: var(--color-surface-secondary);
  border: 1px solid transparent;
}

// Size variants
.uw-card--sm {
  min-height: 120px;
}

.uw-card--md {
  min-height: 200px;
}

.uw-card--lg {
  min-height: 300px;
}

// Padding variants
.uw-card--padding-none {
  .uw-card-header,
  .uw-card-content,
  .uw-card-footer {
    padding: 0;
  }
}

.uw-card--padding-sm {
  .uw-card-header,
  .uw-card-content,
  .uw-card-footer {
    padding: var(--card-padding-sm);
  }
}

.uw-card--padding-md {
  .uw-card-header,
  .uw-card-content,
  .uw-card-footer {
    padding: var(--card-padding-md);
  }
}

.uw-card--padding-lg {
  .uw-card-header,
  .uw-card-content,
  .uw-card-footer {
    padding: var(--card-padding-lg);
  }
}

// Rounded variants
.uw-card--rounded-none { border-radius: var(--radius-none); }
.uw-card--rounded-sm { border-radius: var(--radius-sm); }
.uw-card--rounded-md { border-radius: var(--radius-md); }
.uw-card--rounded-lg { border-radius: var(--radius-lg); }
.uw-card--rounded-xl { border-radius: var(--radius-xl); }

// Shadow variants
.uw-card--shadow-none { box-shadow: var(--shadow-none); }
.uw-card--shadow-sm { box-shadow: var(--shadow-sm); }
.uw-card--shadow-md { box-shadow: var(--shadow-md); }
.uw-card--shadow-lg { box-shadow: var(--shadow-lg); }
.uw-card--shadow-xl { box-shadow: var(--shadow-xl); }

// Header styles
.uw-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  border-bottom: 1px solid var(--color-border-primary);
  
  &:last-child {
    border-bottom: none;
  }
  
  &--rtl {
    flex-direction: row-reverse;
  }
}

.uw-card-header-content {
  flex: 1;
  min-width: 0;
}

.uw-card-title {
  margin: 0;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
}

.uw-card-subtitle {
  margin: var(--spacing-1) 0 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-normal);
}

.uw-card-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-shrink: 0;
}

// Content styles
.uw-card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  
  &--rtl {
    text-align: right;
  }
}

// Footer styles
.uw-card-footer {
  border-top: 1px solid var(--color-border-primary);
  
  &:first-child {
    border-top: none;
  }
  
  &--rtl {
    text-align: right;
  }
}

// Loading animation
@keyframes card-loading {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

// Responsive design
@media (min-width: 768px) {
  .uw-card {
    &--clickable:hover:not(.uw-card--disabled) {
      box-shadow: var(--shadow-md);
    }
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-card--filled {
    background-color: var(--color-surface-tertiary);
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-card {
    border-width: 2px;
    
    &--outlined {
      border-width: 3px;
    }
  }
  
  .uw-card-header,
  .uw-card-footer {
    border-width: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-card {
    transition: none;
    
    &--clickable:hover:not(.uw-card--disabled) {
      transform: none;
    }
    
    &--clickable:active:not(.uw-card--disabled) {
      transform: none;
    }
    
    &--loading::after {
      animation: none;
    }
  }
}
</style>