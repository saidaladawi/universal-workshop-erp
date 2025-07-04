<!--
  Grid Component - Universal Workshop Frontend V2
  
  A flexible CSS Grid-based layout component with responsive capabilities
  and support for various grid patterns and gap configurations.
-->

<template>
  <div
    :class="gridClasses"
    :style="gridStyles"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

// Define component props
export interface GridProps {
  /** Number of columns */
  cols?: number | string
  /** Number of rows */
  rows?: number | string
  /** Gap between grid items */
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  /** Column gap */
  colGap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  /** Row gap */
  rowGap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  /** Grid template areas */
  areas?: string[]
  /** Responsive columns for different breakpoints */
  responsive?: {
    xs?: number | string
    sm?: number | string
    md?: number | string
    lg?: number | string
    xl?: number | string
    '2xl'?: number | string
  }
  /** Auto-fit columns with minimum width */
  autoFit?: string
  /** Auto-fill columns with minimum width */
  autoFill?: string
  /** Align items */
  alignItems?: 'start' | 'end' | 'center' | 'stretch'
  /** Justify items */
  justifyItems?: 'start' | 'end' | 'center' | 'stretch'
  /** Align content */
  alignContent?: 'start' | 'end' | 'center' | 'stretch' | 'space-between' | 'space-around' | 'space-evenly'
  /** Justify content */
  justifyContent?: 'start' | 'end' | 'center' | 'stretch' | 'space-between' | 'space-around' | 'space-evenly'
  /** Dense grid packing */
  dense?: boolean
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Setup props with defaults
const props = withDefaults(defineProps<GridProps>(), {
  cols: 'auto',
  gap: 'md',
  alignItems: 'stretch',
  justifyItems: 'stretch',
  dense: false,
})

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Gap mapping
const gapMap = {
  none: '0',
  xs: 'var(--spacing-1)',
  sm: 'var(--spacing-2)',
  md: 'var(--spacing-4)',
  lg: 'var(--spacing-6)',
  xl: 'var(--spacing-8)',
  '2xl': 'var(--spacing-12)',
}

// Computed classes
const gridClasses = computed(() => [
  'uw-grid',
  `uw-grid--gap-${props.gap}`,
  {
    'uw-grid--dense': props.dense,
    'uw-grid--rtl': isRTL,
    'uw-grid--auto-fit': !!props.autoFit,
    'uw-grid--auto-fill': !!props.autoFill,
  },
  props.class,
])

// Generate grid template columns
const getGridTemplateColumns = (cols: number | string): string => {
  if (typeof cols === 'number') {
    return `repeat(${cols}, 1fr)`
  }
  return cols
}

// Generate grid template rows
const getGridTemplateRows = (rows: number | string): string => {
  if (typeof rows === 'number') {
    return `repeat(${rows}, auto)`
  }
  return rows
}

// Computed styles
const gridStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  // Grid template columns
  if (props.autoFit) {
    styles.gridTemplateColumns = `repeat(auto-fit, minmax(${props.autoFit}, 1fr))`
  } else if (props.autoFill) {
    styles.gridTemplateColumns = `repeat(auto-fill, minmax(${props.autoFill}, 1fr))`
  } else if (props.cols) {
    styles.gridTemplateColumns = getGridTemplateColumns(props.cols)
  }
  
  // Grid template rows
  if (props.rows) {
    styles.gridTemplateRows = getGridTemplateRows(props.rows)
  }
  
  // Grid template areas
  if (props.areas && props.areas.length > 0) {
    styles.gridTemplateAreas = props.areas.map(area => `"${area}"`).join(' ')
  }
  
  // Gap settings
  if (props.colGap && props.colGap !== props.gap) {
    styles.columnGap = gapMap[props.colGap]
  }
  if (props.rowGap && props.rowGap !== props.gap) {
    styles.rowGap = gapMap[props.rowGap]
  }
  
  // Alignment
  if (props.alignItems !== 'stretch') {
    styles.alignItems = props.alignItems
  }
  if (props.justifyItems !== 'stretch') {
    styles.justifyItems = props.justifyItems
  }
  if (props.alignContent) {
    styles.alignContent = props.alignContent
  }
  if (props.justifyContent) {
    styles.justifyContent = props.justifyContent
  }
  
  // Responsive columns
  if (props.responsive) {
    // CSS custom properties for responsive behavior
    Object.entries(props.responsive).forEach(([breakpoint, cols]) => {
      if (cols) {
        styles[`--grid-cols-${breakpoint}`] = getGridTemplateColumns(cols)
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
.uw-grid {
  display: grid;
  
  // RTL support
  &--rtl {
    direction: rtl;
  }
  
  // Dense grid packing
  &--dense {
    grid-auto-flow: dense;
  }
}

// Gap variants
.uw-grid--gap-none { gap: 0; }
.uw-grid--gap-xs { gap: var(--spacing-1); }
.uw-grid--gap-sm { gap: var(--spacing-2); }
.uw-grid--gap-md { gap: var(--spacing-4); }
.uw-grid--gap-lg { gap: var(--spacing-6); }
.uw-grid--gap-xl { gap: var(--spacing-8); }
.uw-grid--gap-2xl { gap: var(--spacing-12); }

// Responsive grid columns
.uw-grid {
  // Default responsive behavior for auto grids
  &--auto-fit,
  &--auto-fill {
    @media (max-width: 639px) {
      grid-template-columns: 1fr;
    }
  }
  
  // Custom responsive columns
  @media (min-width: 320px) {
    &[style*="--grid-cols-xs"] {
      grid-template-columns: var(--grid-cols-xs);
    }
  }
  
  @media (min-width: 640px) {
    &[style*="--grid-cols-sm"] {
      grid-template-columns: var(--grid-cols-sm);
    }
  }
  
  @media (min-width: 768px) {
    &[style*="--grid-cols-md"] {
      grid-template-columns: var(--grid-cols-md);
    }
  }
  
  @media (min-width: 1024px) {
    &[style*="--grid-cols-lg"] {
      grid-template-columns: var(--grid-cols-lg);
    }
  }
  
  @media (min-width: 1280px) {
    &[style*="--grid-cols-xl"] {
      grid-template-columns: var(--grid-cols-xl);
    }
  }
  
  @media (min-width: 1536px) {
    &[style*="--grid-cols-2xl"] {
      grid-template-columns: var(--grid-cols-2xl);
    }
  }
}

// Common grid patterns
.uw-grid {
  // Sidebar layout
  &--sidebar {
    grid-template-columns: auto 1fr;
    
    @media (max-width: 768px) {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
    }
  }
  
  // Header layout
  &--header {
    grid-template-rows: auto 1fr;
  }
  
  // Full layout (header + sidebar + main)
  &--full {
    grid-template-areas:
      "header header"
      "sidebar main";
    grid-template-columns: auto 1fr;
    grid-template-rows: auto 1fr;
    
    @media (max-width: 768px) {
      grid-template-areas:
        "header"
        "main";
      grid-template-columns: 1fr;
    }
  }
  
  // Card grid (auto-responsive)
  &--cards {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    
    @media (max-width: 640px) {
      grid-template-columns: 1fr;
    }
  }
  
  // Masonry-like layout
  &--masonry {
    grid-auto-rows: masonry;
    grid-auto-flow: dense;
  }
}
</style>