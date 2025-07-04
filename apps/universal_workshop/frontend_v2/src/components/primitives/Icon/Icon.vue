<!--
  Icon Component - Universal Workshop Frontend V2
  
  A centralized icon component that supports multiple icon libraries,
  custom SVGs, and provides consistent sizing and styling.
  Includes Arabic/RTL support and accessibility features.
-->

<template>
  <component
    :is="iconComponent"
    :class="iconClasses"
    :style="iconStyles"
    :aria-hidden="decorative"
    :aria-label="ariaLabel || (decorative ? undefined : name)"
    :role="decorative ? 'presentation' : 'img'"
    v-bind="iconProps"
  >
    <!-- Fallback for custom SVG or Unicode icons -->
    <template v-if="iconComponent === 'span'">
      {{ iconContent }}
    </template>
  </component>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'
import { iconRegistry } from './icon-registry'

// Define component props
export interface IconProps {
  /** Icon name from the registry */
  name: string
  /** Icon size */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | number | string
  /** Icon color */
  color?: string
  /** Rotation in degrees */
  rotate?: number
  /** Flip horizontally */
  flipH?: boolean
  /** Flip vertically */
  flipV?: boolean
  /** Spin animation */
  spin?: boolean
  /** Pulse animation */
  pulse?: boolean
  /** Icon is decorative (hidden from screen readers) */
  decorative?: boolean
  /** Custom aria-label */
  ariaLabel?: string
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Setup props with defaults
const props = withDefaults(defineProps<IconProps>(), {
  size: 'md',
  decorative: true,
  rotate: 0,
  flipH: false,
  flipV: false,
  spin: false,
  pulse: false,
})

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Get icon definition from registry
const iconDefinition = computed(() => {
  return iconRegistry.getIcon(props.name)
})

// Determine the component to render
const iconComponent = computed(() => {
  if (iconDefinition.value?.component) {
    return iconDefinition.value.component
  }
  
  if (iconDefinition.value?.svg) {
    return 'svg'
  }
  
  return 'span'
})

// Icon content for fallback rendering
const iconContent = computed(() => {
  if (iconDefinition.value?.unicode) {
    return iconDefinition.value.unicode
  }
  
  if (iconDefinition.value?.text) {
    return iconDefinition.value.text
  }
  
  return props.name
})

// Icon props to pass to the rendered component
const iconProps = computed(() => {
  const baseProps: Record<string, any> = {}
  
  if (iconComponent.value === 'svg' && iconDefinition.value?.svg) {
    baseProps.viewBox = iconDefinition.value.viewBox || '0 0 24 24'
    baseProps.fill = 'currentColor'
    baseProps.innerHTML = iconDefinition.value.svg
  }
  
  return baseProps
})

// Computed classes
const iconClasses = computed(() => [
  'uw-icon',
  `uw-icon--${typeof props.size === 'string' ? props.size : 'custom'}`,
  {
    'uw-icon--spin': props.spin,
    'uw-icon--pulse': props.pulse,
    'uw-icon--flip-h': props.flipH,
    'uw-icon--flip-v': props.flipV,
    'uw-icon--rtl': isRTL && iconDefinition.value?.rtlFlip,
  },
  props.class,
])

// Computed styles
const iconStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  // Handle custom size
  if (typeof props.size === 'number') {
    styles.width = `${props.size}px`
    styles.height = `${props.size}px`
  } else if (typeof props.size === 'string' && !['xs', 'sm', 'md', 'lg', 'xl', '2xl'].includes(props.size)) {
    styles.width = props.size
    styles.height = props.size
  }
  
  // Handle color
  if (props.color) {
    styles.color = props.color
  }
  
  // Handle rotation
  if (props.rotate !== 0) {
    styles.transform = `rotate(${props.rotate}deg)`
  }
  
  // Apply custom styles
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    Object.assign(styles, props.style)
  }
  
  return styles
})
</script>

<script lang="ts">
// Export component name for debugging
export default {
  name: 'UWIcon'
}
</script>

<style lang="scss" scoped>
.uw-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  user-select: none;
  vertical-align: middle;
  
  // Size variants using design tokens
  &--xs {
    width: var(--icon-size-xs, 0.75rem);
    height: var(--icon-size-xs, 0.75rem);
  }
  
  &--sm {
    width: var(--icon-size-sm, 1rem);
    height: var(--icon-size-sm, 1rem);
  }
  
  &--md {
    width: var(--icon-size-md, 1.25rem);
    height: var(--icon-size-md, 1.25rem);
  }
  
  &--lg {
    width: var(--icon-size-lg, 1.5rem);
    height: var(--icon-size-lg, 1.5rem);
  }
  
  &--xl {
    width: var(--icon-size-xl, 2rem);
    height: var(--icon-size-xl, 2rem);
  }
  
  &--2xl {
    width: var(--icon-size-2xl, 2.5rem);
    height: var(--icon-size-2xl, 2.5rem);
  }
  
  // Transformations
  &--flip-h {
    transform: scaleX(-1);
  }
  
  &--flip-v {
    transform: scaleY(-1);
  }
  
  &--rtl {
    transform: scaleX(-1);
  }
  
  // Animations
  &--spin {
    animation: uw-icon-spin 1s linear infinite;
  }
  
  &--pulse {
    animation: uw-icon-pulse 2s ease-in-out infinite;
  }
  
  // SVG specific styles
  svg {
    width: 100%;
    height: 100%;
    fill: currentColor;
    pointer-events: none;
  }
}

// Animations
@keyframes uw-icon-spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes uw-icon-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .uw-icon--spin,
  .uw-icon--pulse {
    animation: none;
  }
}

// High contrast support
[data-contrast="high"] {
  .uw-icon {
    filter: contrast(1.5);
  }
}
</style>