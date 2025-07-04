<!--
  SidebarMenuContent Component - Universal Workshop Frontend V2
  
  Content renderer for sidebar menu items including icon, label, and badge
  with collapsed state support and Arabic/RTL layout.
-->

<template>
  <div class="uw-sidebar-menu-content">
    <!-- Icon -->
    <span
      v-if="item.icon"
      class="uw-sidebar-menu-icon"
      v-html="item.icon"
    />
    
    <!-- Label -->
    <span
      v-if="expanded"
      class="uw-sidebar-menu-label"
    >
      <span v-if="preferArabic && item.labelAr">{{ item.labelAr }}</span>
      <span v-else-if="item.label">{{ item.label }}</span>
      <span v-else-if="item.labelAr">{{ item.labelAr }}</span>
    </span>
    
    <!-- Badge -->
    <span
      v-if="expanded && item.badge !== undefined && item.badge !== null"
      class="uw-sidebar-menu-badge"
      :class="{
        'uw-sidebar-menu-badge--dot': item.badge === true,
      }"
    >
      <span v-if="item.badge !== true">{{ item.badge }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import type { SidebarMenuItem } from './SidebarMenu.vue'

// Define component props
export interface SidebarMenuContentProps {
  /** Menu item data */
  item: SidebarMenuItem
  /** Sidebar is expanded */
  expanded?: boolean
  /** Prefer Arabic display */
  preferArabic?: boolean
}

// Setup props with defaults
defineProps<SidebarMenuContentProps>()
</script>

<style lang="scss" scoped>
.uw-sidebar-menu-content {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  flex: 1;
  min-width: 0;
}

.uw-sidebar-menu-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  flex-shrink: 0;
  
  :deep(svg) {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

.uw-sidebar-menu-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: opacity 0.3s ease, visibility 0.3s ease;
  min-width: 0;
}

.uw-sidebar-menu-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 1.2em;
  height: 1.2em;
  padding: 0 var(--spacing-1);
  background: var(--color-error);
  color: var(--color-error-foreground);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  transition: opacity 0.3s ease, visibility 0.3s ease;
  flex-shrink: 0;
  
  &--dot {
    min-width: 0.5em;
    height: 0.5em;
    padding: 0;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-sidebar-menu-label,
  .uw-sidebar-menu-badge {
    transition: none;
  }
}
</style>