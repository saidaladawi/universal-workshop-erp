<!--
  SidebarMenu Component - Universal Workshop Frontend V2
  
  A recursive menu component for sidebar navigation with multi-level
  support, icons, badges, and Arabic/RTL layout.
-->

<template>
  <ul class="uw-sidebar-menu" :class="`uw-sidebar-menu--level-${level}`">
    <li
      v-for="(item, index) in items"
      :key="item.key || index"
      class="uw-sidebar-menu-item"
      :class="{
        'uw-sidebar-menu-item--disabled': item.disabled,
        'uw-sidebar-menu-item--hidden': item.hidden,
        'uw-sidebar-menu-item--has-children': item.children?.length,
        'uw-sidebar-menu-item--expanded': expandedItems.has(item.key || index),
      }"
    >
      <!-- Menu item link/button -->
      <component
        v-if="item.href && !item.disabled"
        :is="linkComponent"
        :to="item.href"
        :href="item.href"
        class="uw-sidebar-menu-link"
        @click="handleItemClick(item, $event)"
      >
        <SidebarMenuContent :item="item" :expanded="expanded" :prefer-arabic="preferArabic" />
        <SidebarMenuChevron
          v-if="item.children?.length"
          :expanded="expandedItems.has(item.key || index)"
          :prefer-arabic="preferArabic"
        />
      </component>
      
      <button
        v-else-if="!item.disabled"
        type="button"
        class="uw-sidebar-menu-button"
        @click="handleItemClick(item, $event)"
      >
        <SidebarMenuContent :item="item" :expanded="expanded" :prefer-arabic="preferArabic" />
        <SidebarMenuChevron
          v-if="item.children?.length"
          :expanded="expandedItems.has(item.key || index)"
          :prefer-arabic="preferArabic"
        />
      </button>
      
      <span v-else class="uw-sidebar-menu-text">
        <SidebarMenuContent :item="item" :expanded="expanded" :prefer-arabic="preferArabic" />
      </span>
      
      <!-- Submenu -->
      <Transition name="submenu">
        <SidebarMenu
          v-if="item.children?.length && expandedItems.has(item.key || index)"
          :items="item.children"
          :expanded="expanded"
          :level="level + 1"
          :prefer-arabic="preferArabic"
          :link-component="linkComponent"
          @item-click="$emit('item-click', $event.item, $event.event)"
        />
      </Transition>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { inject, ref } from 'vue'
import SidebarMenuContent from './SidebarMenuContent.vue'
import SidebarMenuChevron from './SidebarMenuChevron.vue'

// Define menu item interface
export interface SidebarMenuItem {
  key?: string
  label?: string
  labelAr?: string
  icon?: string
  href?: string
  badge?: string | number | boolean
  disabled?: boolean
  hidden?: boolean
  children?: SidebarMenuItem[]
  data?: any
}

// Define component props
export interface SidebarMenuProps {
  /** Menu items */
  items?: SidebarMenuItem[]
  /** Sidebar is expanded */
  expanded?: boolean
  /** Menu nesting level */
  level?: number
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Link component to use */
  linkComponent?: string | object
}

// Define component emits
export interface SidebarMenuEmits {
  'item-click': [{ item: SidebarMenuItem; event: Event }]
}

// Setup props with defaults
const props = withDefaults(defineProps<SidebarMenuProps>(), {
  level: 0,
  expanded: true,
  preferArabic: true,
  linkComponent: 'a',
})

// Setup emits
const emit = defineEmits<SidebarMenuEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Track expanded menu items
const expandedItems = ref(new Set<string | number>())

// Event handlers
const handleItemClick = (item: SidebarMenuItem, event: Event) => {
  // Toggle submenu if item has children
  if (item.children?.length) {
    const key = item.key || props.items?.indexOf(item) || 0
    if (expandedItems.value.has(key)) {
      expandedItems.value.delete(key)
    } else {
      expandedItems.value.add(key)
    }
  }
  
  emit('item-click', { item, event })
}

// Expose methods
defineExpose({
  expandedItems,
  expandItem: (key: string | number) => {
    expandedItems.value.add(key)
  },
  collapseItem: (key: string | number) => {
    expandedItems.value.delete(key)
  },
  toggleItem: (key: string | number) => {
    if (expandedItems.value.has(key)) {
      expandedItems.value.delete(key)
    } else {
      expandedItems.value.add(key)
    }
  },
})
</script>

<style lang="scss" scoped>
.uw-sidebar-menu {
  list-style: none;
  margin: 0;
  padding: 0;
  
  &--level-0 {
    > .uw-sidebar-menu-item + .uw-sidebar-menu-item {
      margin-top: var(--spacing-1);
    }
  }
  
  &--level-1 {
    padding-left: var(--spacing-8);
    margin-top: var(--spacing-1);
    
    [dir="rtl"] & {
      padding-left: 0;
      padding-right: var(--spacing-8);
    }
  }
  
  &--level-2 {
    padding-left: var(--spacing-12);
    
    [dir="rtl"] & {
      padding-left: 0;
      padding-right: var(--spacing-12);
    }
  }
}

.uw-sidebar-menu-item {
  &--hidden {
    display: none;
  }
  
  &--disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}

.uw-sidebar-menu-link,
.uw-sidebar-menu-button,
.uw-sidebar-menu-text {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: var(--spacing-2) var(--spacing-3);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-md);
  transition: var(--transition-colors);
  cursor: pointer;
  font-size: var(--font-size-sm);
  
  &:hover {
    background: var(--color-surface-secondary);
    color: var(--color-text-primary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  &[aria-current="page"] {
    background: var(--color-primary-50);
    color: var(--color-primary);
    font-weight: var(--font-weight-medium);
  }
}

.uw-sidebar-menu-text {
  cursor: default;
}

// Submenu transitions
.submenu-enter-active,
.submenu-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.submenu-enter-from,
.submenu-leave-to {
  opacity: 0;
  max-height: 0;
}

.submenu-enter-to,
.submenu-leave-from {
  opacity: 1;
  max-height: 200px;
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-sidebar-menu-link,
  .uw-sidebar-menu-button,
  .submenu-enter-active,
  .submenu-leave-active {
    transition: none;
  }
}
</style>