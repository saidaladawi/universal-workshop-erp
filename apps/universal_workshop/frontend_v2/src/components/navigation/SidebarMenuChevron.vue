<!--
  SidebarMenuChevron Component - Universal Workshop Frontend V2
  
  Chevron indicator for expandable sidebar menu items with smooth
  rotation animation and Arabic/RTL support.
-->

<template>
  <span class="uw-sidebar-menu-chevron" :class="chevronClasses">
    <svg class="uw-sidebar-menu-chevron-icon" viewBox="0 0 24 24" fill="currentColor">
      <path :d="chevronPath" />
    </svg>
  </span>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

// Define component props
export interface SidebarMenuChevronProps {
  /** Submenu is expanded */
  expanded?: boolean
  /** Prefer Arabic display */
  preferArabic?: boolean
}

// Setup props with defaults
const props = withDefaults(defineProps<SidebarMenuChevronProps>(), {
  expanded: false,
  preferArabic: true,
})

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Chevron path (down-pointing arrow)
const chevronPath = computed(() => {
  return "M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"
})

// Computed classes
const chevronClasses = computed(() => [
  'uw-sidebar-menu-chevron',
  {
    'uw-sidebar-menu-chevron--expanded': props.expanded,
    'uw-sidebar-menu-chevron--rtl': isRTL,
  },
])
</script>

<style lang="scss" scoped>
.uw-sidebar-menu-chevron {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
  transition: transform 0.2s ease;
  
  // Expanded state rotates chevron
  &--expanded {
    transform: rotate(180deg);
  }
  
  // RTL adjustment - flip horizontal for natural feel
  &--rtl {
    transform: scaleX(-1);
    
    &.uw-sidebar-menu-chevron--expanded {
      transform: scaleX(-1) rotate(180deg);
    }
  }
}

.uw-sidebar-menu-chevron-icon {
  width: 100%;
  height: 100%;
  fill: currentColor;
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-sidebar-menu-chevron {
    transition: none;
  }
}
</style>