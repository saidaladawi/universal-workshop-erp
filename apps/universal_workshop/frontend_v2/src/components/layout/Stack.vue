<!--
  Stack Component - Universal Workshop Frontend V2
  
  A simple layout component for arranging items in vertical or horizontal
  stacks with consistent spacing and alignment options.
-->

<template>
  <div
    :class="stackClasses"
    :style="stackStyles"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

// Define component props
export interface StackProps {
  /** Stack direction */
  direction?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
  /** Space between items */
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  /** Align items */
  align?: 'start' | 'end' | 'center' | 'stretch' | 'baseline'
  /** Justify content */
  justify?: 'start' | 'end' | 'center' | 'between' | 'around' | 'evenly'
  /** Wrap items */
  wrap?: boolean
  /** Responsive direction changes */
  responsive?: {
    xs?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
    sm?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
    md?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
    lg?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
    xl?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
    '2xl'?: 'row' | 'column' | 'row-reverse' | 'column-reverse'
  }
  /** Divider between items */
  divider?: boolean
  /** Custom divider element */
  dividerElement?: string
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Setup props with defaults
const props = withDefaults(defineProps<StackProps>(), {
  direction: 'column',
  spacing: 'md',
  align: 'stretch',
  justify: 'start',
  wrap: false,
  divider: false,
})

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Spacing mapping
const spacingMap = {
  none: '0',
  xs: 'var(--spacing-1)',
  sm: 'var(--spacing-2)',
  md: 'var(--spacing-4)',
  lg: 'var(--spacing-6)',
  xl: 'var(--spacing-8)',
  '2xl': 'var(--spacing-12)',
}

// Alignment mapping
const alignMap = {
  start: 'flex-start',
  end: 'flex-end',
  center: 'center',
  stretch: 'stretch',
  baseline: 'baseline',
}

// Justify mapping
const justifyMap = {
  start: 'flex-start',
  end: 'flex-end',
  center: 'center',
  between: 'space-between',
  around: 'space-around',
  evenly: 'space-evenly',
}

// Computed classes
const stackClasses = computed(() => [
  'uw-stack',
  `uw-stack--${props.direction}`,
  `uw-stack--spacing-${props.spacing}`,
  `uw-stack--align-${props.align}`,
  `uw-stack--justify-${props.justify}`,
  {
    'uw-stack--wrap': props.wrap,
    'uw-stack--divider': props.divider,
    'uw-stack--rtl': isRTL,
  },
  props.class,
])

// Computed styles
const stackStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  // Base flexbox styles
  styles.display = 'flex'
  styles.flexDirection = props.direction
  styles.alignItems = alignMap[props.align]
  styles.justifyContent = justifyMap[props.justify]
  
  if (props.wrap) {
    styles.flexWrap = 'wrap'
  }
  
  // Spacing - using gap for modern browsers
  if (props.spacing !== 'none') {
    styles.gap = spacingMap[props.spacing]
  }
  
  // Responsive direction
  if (props.responsive) {
    Object.entries(props.responsive).forEach(([breakpoint, direction]) => {
      if (direction) {
        styles[`--stack-direction-${breakpoint}`] = direction
      }
    })
  }
  
  // Custom styles
  if (typeof props.style === 'string') {
    Object.assign(styles, { cssText: props.style })
  } else if (props.style) {
    Object.assign(styles, props.style)
  }
  
  return styles
})
</script>

<style lang="scss" scoped>
.uw-stack {
  // Base stack styles
  display: flex;
  
  // RTL support
  &--rtl {
    &.uw-stack--row {
      flex-direction: row-reverse;
    }
    
    &.uw-stack--row-reverse {
      flex-direction: row;
    }
  }
}

// Direction variants
.uw-stack--row {
  flex-direction: row;
}

.uw-stack--column {
  flex-direction: column;
}

.uw-stack--row-reverse {
  flex-direction: row-reverse;
}

.uw-stack--column-reverse {
  flex-direction: column-reverse;
}

// Spacing variants (fallback for browsers without gap support)
.uw-stack--spacing-xs > * + * {
  margin-top: var(--spacing-1);
}

.uw-stack--spacing-sm > * + * {
  margin-top: var(--spacing-2);
}

.uw-stack--spacing-md > * + * {
  margin-top: var(--spacing-4);
}

.uw-stack--spacing-lg > * + * {
  margin-top: var(--spacing-6);
}

.uw-stack--spacing-xl > * + * {
  margin-top: var(--spacing-8);
}

.uw-stack--spacing-2xl > * + * {
  margin-top: var(--spacing-12);
}

// Row direction spacing
.uw-stack--row {
  &.uw-stack--spacing-xs > * + * {
    margin-top: 0;
    margin-left: var(--spacing-1);
  }
  
  &.uw-stack--spacing-sm > * + * {
    margin-top: 0;
    margin-left: var(--spacing-2);
  }
  
  &.uw-stack--spacing-md > * + * {
    margin-top: 0;
    margin-left: var(--spacing-4);
  }
  
  &.uw-stack--spacing-lg > * + * {
    margin-top: 0;
    margin-left: var(--spacing-6);
  }
  
  &.uw-stack--spacing-xl > * + * {
    margin-top: 0;
    margin-left: var(--spacing-8);
  }
  
  &.uw-stack--spacing-2xl > * + * {
    margin-top: 0;
    margin-left: var(--spacing-12);
  }
}

// RTL row spacing adjustments
.uw-stack--rtl.uw-stack--row {
  &.uw-stack--spacing-xs > * + * {
    margin-left: 0;
    margin-right: var(--spacing-1);
  }
  
  &.uw-stack--spacing-sm > * + * {
    margin-left: 0;
    margin-right: var(--spacing-2);
  }
  
  &.uw-stack--spacing-md > * + * {
    margin-left: 0;
    margin-right: var(--spacing-4);
  }
  
  &.uw-stack--spacing-lg > * + * {
    margin-left: 0;
    margin-right: var(--spacing-6);
  }
  
  &.uw-stack--spacing-xl > * + * {
    margin-left: 0;
    margin-right: var(--spacing-8);
  }
  
  &.uw-stack--spacing-2xl > * + * {
    margin-left: 0;
    margin-right: var(--spacing-12);
  }
}

// Wrap support
.uw-stack--wrap {
  flex-wrap: wrap;
}

// Divider support
.uw-stack--divider {
  &.uw-stack--column > * + *::before {
    content: '';
    display: block;
    width: 100%;
    height: 1px;
    background-color: var(--color-border-primary);
    margin-bottom: calc(var(--spacing-4) / 2);
    margin-top: calc(var(--spacing-4) / -2);
  }
  
  &.uw-stack--row > * + *::before {
    content: '';
    display: block;
    width: 1px;
    height: 100%;
    background-color: var(--color-border-primary);
    margin-right: calc(var(--spacing-4) / 2);
    margin-left: calc(var(--spacing-4) / -2);
  }
}

// Responsive direction changes
.uw-stack {
  @media (min-width: 320px) {
    &[style*="--stack-direction-xs"] {
      flex-direction: var(--stack-direction-xs);
    }
  }
  
  @media (min-width: 640px) {
    &[style*="--stack-direction-sm"] {
      flex-direction: var(--stack-direction-sm);
    }
  }
  
  @media (min-width: 768px) {
    &[style*="--stack-direction-md"] {
      flex-direction: var(--stack-direction-md);
    }
  }
  
  @media (min-width: 1024px) {
    &[style*="--stack-direction-lg"] {
      flex-direction: var(--stack-direction-lg);
    }
  }
  
  @media (min-width: 1280px) {
    &[style*="--stack-direction-xl"] {
      flex-direction: var(--stack-direction-xl);
    }
  }
  
  @media (min-width: 1536px) {
    &[style*="--stack-direction-2xl"] {
      flex-direction: var(--stack-direction-2xl);
    }
  }
}

// Common responsive patterns
.uw-stack {
  // Mobile stacked, desktop horizontal
  &--responsive-horizontal {
    flex-direction: column;
    
    @media (min-width: 768px) {
      flex-direction: row;
    }
  }
  
  // Mobile horizontal, desktop stacked (rare but possible)
  &--responsive-vertical {
    flex-direction: row;
    
    @media (min-width: 768px) {
      flex-direction: column;
    }
  }
}

// Support for browsers without gap
@supports not (gap: 1rem) {
  .uw-stack {
    // Reset gap fallback when gap is supported
    > * + * {
      margin: 0;
    }
  }
}
</style>