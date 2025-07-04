<!--
  Container Component - Universal Workshop Frontend V2
  
  A responsive container component that centers content and provides
  consistent max-width and padding across different screen sizes.
-->

<template>
  <div
    :class="containerClasses"
    :style="containerStyles"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

// Define component props
export interface ContainerProps {
  /** Container size */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  /** Fluid container (full width) */
  fluid?: boolean
  /** Center content horizontally */
  centered?: boolean
  /** Custom padding */
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  /** Custom margin */
  margin?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'auto'
  /** Responsive padding adjustments */
  responsivePadding?: boolean
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Setup props with defaults
const props = withDefaults(defineProps<ContainerProps>(), {
  size: 'lg',
  fluid: false,
  centered: true,
  padding: 'md',
  margin: 'auto',
  responsivePadding: true,
})

// Check if RTL context is available
const isRTL = inject('isRTL', false)

// Computed classes
const containerClasses = computed(() => [
  'uw-container',
  `uw-container--${props.size}`,
  `uw-container--padding-${props.padding}`,
  `uw-container--margin-${props.margin}`,
  {
    'uw-container--fluid': props.fluid,
    'uw-container--centered': props.centered,
    'uw-container--responsive-padding': props.responsivePadding,
    'uw-container--rtl': isRTL,
  },
  props.class,
])

// Computed styles
const containerStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  if (typeof props.style === 'string') {
    return props.style
  } else if (props.style) {
    Object.assign(styles, props.style)
  }
  
  return styles
})
</script>

<style lang="scss" scoped>
.uw-container {
  // Base container styles
  width: 100%;
  
  // Centered container
  &--centered {
    margin-left: auto;
    margin-right: auto;
  }
  
  // RTL support
  &--rtl {
    direction: rtl;
  }
}

// Size variants
.uw-container--xs {
  max-width: var(--breakpoint-xs);
}

.uw-container--sm {
  max-width: var(--breakpoint-sm);
}

.uw-container--md {
  max-width: var(--breakpoint-md);
}

.uw-container--lg {
  max-width: var(--breakpoint-lg);
}

.uw-container--xl {
  max-width: var(--breakpoint-xl);
}

.uw-container--2xl {
  max-width: var(--breakpoint-2xl);
}

.uw-container--full {
  max-width: none;
}

// Fluid container
.uw-container--fluid {
  max-width: none !important;
  width: 100%;
}

// Padding variants
.uw-container--padding-none {
  padding: 0;
}

.uw-container--padding-sm {
  padding: var(--spacing-4);
}

.uw-container--padding-md {
  padding: var(--spacing-6);
}

.uw-container--padding-lg {
  padding: var(--spacing-8);
}

.uw-container--padding-xl {
  padding: var(--spacing-12);
}

// Margin variants
.uw-container--margin-none {
  margin: 0;
}

.uw-container--margin-sm {
  margin: var(--spacing-4);
}

.uw-container--margin-md {
  margin: var(--spacing-6);
}

.uw-container--margin-lg {
  margin: var(--spacing-8);
}

.uw-container--margin-xl {
  margin: var(--spacing-12);
}

.uw-container--margin-auto {
  margin-left: auto;
  margin-right: auto;
}

// Responsive padding adjustments
.uw-container--responsive-padding {
  &.uw-container--padding-sm {
    @media (min-width: 640px) {
      padding: var(--spacing-6);
    }
    
    @media (min-width: 1024px) {
      padding: var(--spacing-8);
    }
  }
  
  &.uw-container--padding-md {
    @media (min-width: 640px) {
      padding: var(--spacing-8);
    }
    
    @media (min-width: 1024px) {
      padding: var(--spacing-12);
    }
  }
  
  &.uw-container--padding-lg {
    @media (min-width: 640px) {
      padding: var(--spacing-12);
    }
    
    @media (min-width: 1024px) {
      padding: var(--spacing-16);
    }
  }
  
  &.uw-container--padding-xl {
    @media (min-width: 640px) {
      padding: var(--spacing-16);
    }
    
    @media (min-width: 1024px) {
      padding: var(--spacing-20);
    }
  }
}

// Mobile-first responsive design
@media (max-width: 639px) {
  .uw-container {
    padding-left: var(--spacing-4);
    padding-right: var(--spacing-4);
  }
}

@media (min-width: 640px) {
  .uw-container {
    padding-left: var(--spacing-6);
    padding-right: var(--spacing-6);
  }
}

@media (min-width: 1024px) {
  .uw-container {
    padding-left: var(--spacing-8);
    padding-right: var(--spacing-8);
  }
}

@media (min-width: 1280px) {
  .uw-container {
    padding-left: var(--spacing-12);
    padding-right: var(--spacing-12);
  }
}
</style>