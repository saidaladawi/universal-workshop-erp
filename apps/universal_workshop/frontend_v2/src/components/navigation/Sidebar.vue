<!--
  Sidebar Component - Universal Workshop Frontend V2
  
  A collapsible sidebar navigation component with multi-level menus,
  user profile, and mobile overlay support with Arabic/RTL layout.
-->

<template>
  <aside
    :class="sidebarClasses"
    :style="sidebarStyles"
    :aria-expanded="isExpanded"
    :aria-label="sidebarLabel"
  >
    <!-- Mobile overlay -->
    <div
      v-if="overlay && isExpanded"
      class="uw-sidebar-overlay"
      @click="handleOverlayClick"
    />
    
    <!-- Sidebar content -->
    <div class="uw-sidebar-content">
      <!-- Header -->
      <div v-if="$slots.header || showHeader" class="uw-sidebar-header">
        <slot name="header">
          <!-- Logo/Brand -->
          <div v-if="logo || brand" class="uw-sidebar-brand">
            <img
              v-if="logo"
              :src="logo"
              :alt="brandAlt || brand"
              class="uw-sidebar-logo"
            />
            <span v-if="brand && (isExpanded || !logo)" class="uw-sidebar-brand-text">
              {{ brand }}
            </span>
          </div>
          
          <!-- Toggle button -->
          <button
            v-if="collapsible"
            type="button"
            class="uw-sidebar-toggle"
            :aria-label="toggleLabel"
            @click="handleToggle"
          >
            <svg class="uw-sidebar-toggle-icon" viewBox="0 0 24 24" fill="currentColor">
              <path :d="toggleIconPath" />
            </svg>
          </button>
        </slot>
      </div>
      
      <!-- User profile -->
      <div v-if="$slots.profile || user" class="uw-sidebar-profile">
        <slot name="profile" :user="user" :expanded="isExpanded">
          <div v-if="user" class="uw-sidebar-user">
            <img
              v-if="user.avatar"
              :src="user.avatar"
              :alt="user.name || user.nameAr"
              class="uw-sidebar-user-avatar"
            />
            <div v-if="isExpanded" class="uw-sidebar-user-info">
              <div class="uw-sidebar-user-name">
                <span v-if="preferArabic && user.nameAr">{{ user.nameAr }}</span>
                <span v-else-if="user.name">{{ user.name }}</span>
                <span v-else-if="user.nameAr">{{ user.nameAr }}</span>
              </div>
              <div v-if="user.role || user.roleAr" class="uw-sidebar-user-role">
                <span v-if="preferArabic && user.roleAr">{{ user.roleAr }}</span>
                <span v-else-if="user.role">{{ user.role }}</span>
                <span v-else-if="user.roleAr">{{ user.roleAr }}</span>
              </div>
            </div>
          </div>
        </slot>
      </div>
      
      <!-- Navigation -->
      <nav class="uw-sidebar-nav">
        <div class="uw-sidebar-nav-content">
          <slot name="navigation" :expanded="isExpanded">
            <SidebarMenu
              :items="menuItems"
              :expanded="isExpanded"
              :prefer-arabic="preferArabic"
              @item-click="handleMenuItemClick"
            />
          </slot>
        </div>
      </nav>
      
      <!-- Footer -->
      <div v-if="$slots.footer" class="uw-sidebar-footer">
        <slot name="footer" :expanded="isExpanded" />
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue'
import SidebarMenu from './SidebarMenu.vue'

// Define user interface
export interface SidebarUser {
  name?: string
  nameAr?: string
  role?: string
  roleAr?: string
  avatar?: string
  email?: string
}

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
export interface SidebarProps {
  /** Sidebar is expanded */
  expanded?: boolean
  /** Sidebar is collapsible */
  collapsible?: boolean
  /** Sidebar width when expanded */
  width?: string
  /** Sidebar width when collapsed */
  collapsedWidth?: string
  /** Show mobile overlay */
  overlay?: boolean
  /** Logo image URL */
  logo?: string
  /** Brand text */
  brand?: string
  /** Brand alt text */
  brandAlt?: string
  /** Show header */
  showHeader?: boolean
  /** User information */
  user?: SidebarUser
  /** Menu items */
  menuItems?: SidebarMenuItem[]
  /** Link component to use */
  linkComponent?: string | object
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface SidebarEmits {
  'update:expanded': [value: boolean]
  toggle: [expanded: boolean]
  'menu-item-click': [item: SidebarMenuItem, event: Event]
  'overlay-click': []
}

// Setup props with defaults
const props = withDefaults(defineProps<SidebarProps>(), {
  expanded: true,
  collapsible: true,
  width: '280px',
  collapsedWidth: '64px',
  overlay: false,
  showHeader: true,
  linkComponent: 'a',
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<SidebarEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Internal state
const internalExpanded = ref(props.expanded)

// Watch for external expanded changes
watch(() => props.expanded, (newValue) => {
  internalExpanded.value = newValue
})

// Watch for internal expanded changes
watch(internalExpanded, (newValue) => {
  emit('update:expanded', newValue)
  emit('toggle', newValue)
})

// Computed values
const isExpanded = computed(() => internalExpanded.value)

const sidebarLabel = computed(() => {
  return props.preferArabic ? 'القائمة الجانبية للتنقل' : 'Navigation sidebar'
})

const toggleLabel = computed(() => {
  const action = isExpanded.value 
    ? (props.preferArabic ? 'طي' : 'Collapse')
    : (props.preferArabic ? 'توسيع' : 'Expand')
  return `${action} ${props.preferArabic ? 'الشريط الجانبي' : 'sidebar'}`
})

// Toggle icon path based on state and RTL
const toggleIconPath = computed(() => {
  const isCollapsed = !isExpanded.value
  
  if (isRTL) {
    // RTL: chevron-right for collapsed, chevron-left for expanded
    return isCollapsed
      ? "M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"  // chevron-right
      : "M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"   // chevron-left
  } else {
    // LTR: chevron-left for collapsed, chevron-right for expanded
    return isCollapsed
      ? "M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"   // chevron-left
      : "M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"  // chevron-right
  }
})

// Computed classes
const sidebarClasses = computed(() => [
  'uw-sidebar',
  {
    'uw-sidebar--expanded': isExpanded.value,
    'uw-sidebar--collapsed': !isExpanded.value,
    'uw-sidebar--collapsible': props.collapsible,
    'uw-sidebar--overlay': props.overlay,
    'uw-sidebar--rtl': isRTL,
    'uw-sidebar--prefer-arabic': props.preferArabic,
  },
  props.class,
])

// Computed styles
const sidebarStyles = computed(() => {
  const styles: Record<string, string> = {}
  
  if (isExpanded.value) {
    styles.width = props.width
  } else {
    styles.width = props.collapsedWidth
  }
  
  return styles
})

// Event handlers
const handleToggle = () => {
  internalExpanded.value = !internalExpanded.value
}

const handleOverlayClick = () => {
  emit('overlay-click')
  if (props.overlay) {
    internalExpanded.value = false
  }
}

const handleMenuItemClick = (item: SidebarMenuItem, event: Event) => {
  emit('menu-item-click', item, event)
}

// Expose methods
defineExpose({
  expanded: internalExpanded,
  toggle: handleToggle,
  expand: () => { internalExpanded.value = true },
  collapse: () => { internalExpanded.value = false },
})
</script>

<script lang="ts">
// SidebarMenu component (inline to avoid circular dependencies)
export interface SidebarMenuProps {
  items?: SidebarMenuItem[]
  expanded?: boolean
  level?: number
  preferArabic?: boolean
}

export interface SidebarMenuEmits {
  'item-click': [item: SidebarMenuItem, event: Event]
}
</script>

<template name="SidebarMenu">
  <ul class="uw-sidebar-menu" :class="`uw-sidebar-menu--level-${level}`">
    <li
      v-for="(item, index) in items"
      :key="item.key || index"
      class="uw-sidebar-menu-item"
      :class="{
        'uw-sidebar-menu-item--disabled': item.disabled,
        'uw-sidebar-menu-item--hidden': item.hidden,
        'uw-sidebar-menu-item--has-children': item.children?.length,
      }"
    >
      <!-- Menu item link/button -->
      <component
        v-if="item.href && !item.disabled"
        :is="linkComponent"
        :to="item.href"
        :href="item.href"
        class="uw-sidebar-menu-link"
        @click="$emit('item-click', item, $event)"
      >
        <SidebarMenuContent :item="item" :expanded="expanded" :prefer-arabic="preferArabic" />
      </component>
      
      <button
        v-else-if="!item.disabled"
        type="button"
        class="uw-sidebar-menu-button"
        @click="$emit('item-click', item, $event)"
      >
        <SidebarMenuContent :item="item" :expanded="expanded" :prefer-arabic="preferArabic" />
      </button>
      
      <span v-else class="uw-sidebar-menu-text">
        <SidebarMenuContent :item="item" :expanded="expanded" :prefer-arabic="preferArabic" />
      </span>
      
      <!-- Submenu -->
      <SidebarMenu
        v-if="item.children?.length && expanded"
        :items="item.children"
        :expanded="expanded"
        :level="level + 1"
        :prefer-arabic="preferArabic"
        @item-click="$emit('item-click', $event)"
      />
    </li>
  </ul>
</template>

<script setup lang="ts" name="SidebarMenu">
// This would normally be a separate component, but included inline for simplicity
const props = withDefaults(defineProps<SidebarMenuProps>(), {
  level: 0,
  expanded: true,
  preferArabic: true,
})

defineEmits<SidebarMenuEmits>()
</script>

<style lang="scss" scoped>
.uw-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  background: var(--color-surface-primary);
  border-right: 1px solid var(--color-border-primary);
  transition: width 0.3s ease;
  z-index: var(--z-sidebar, 100);
  overflow: hidden;
  
  // RTL support
  &--rtl {
    left: auto;
    right: 0;
    border-right: none;
    border-left: 1px solid var(--color-border-primary);
    direction: rtl;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
  
  // Overlay mode (mobile)
  &--overlay {
    position: fixed;
    z-index: var(--z-overlay, 1000);
    box-shadow: var(--shadow-xl);
    
    &:not(&--expanded) {
      transform: translateX(-100%);
      
      &.uw-sidebar--rtl {
        transform: translateX(100%);
      }
    }
  }
  
  // Collapsed state
  &--collapsed {
    .uw-sidebar-brand-text,
    .uw-sidebar-user-info,
    .uw-sidebar-menu-label,
    .uw-sidebar-menu-badge {
      opacity: 0;
      visibility: hidden;
    }
  }
}

.uw-sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: -1;
}

.uw-sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

// Header styles
.uw-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.uw-sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  flex: 1;
}

.uw-sidebar-logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
  flex-shrink: 0;
}

.uw-sidebar-brand-text {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-lg);
  color: var(--color-text-primary);
  transition: opacity 0.3s ease, visibility 0.3s ease;
  white-space: nowrap;
  overflow: hidden;
}

.uw-sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-8);
  height: var(--spacing-8);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: var(--transition-colors);
  flex-shrink: 0;
  
  &:hover {
    background: var(--color-surface-secondary);
    color: var(--color-text-primary);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

.uw-sidebar-toggle-icon {
  width: var(--spacing-5);
  height: var(--spacing-5);
}

// Profile styles
.uw-sidebar-profile {
  padding: var(--spacing-4);
  border-bottom: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

.uw-sidebar-user {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.uw-sidebar-user-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  object-fit: cover;
  flex-shrink: 0;
}

.uw-sidebar-user-info {
  flex: 1;
  min-width: 0;
  transition: opacity 0.3s ease, visibility 0.3s ease;
}

.uw-sidebar-user-name {
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uw-sidebar-user-role {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// Navigation styles
.uw-sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--spacing-2) 0;
  
  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--color-border-secondary);
    border-radius: 2px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-primary);
  }
}

.uw-sidebar-nav-content {
  padding: 0 var(--spacing-2);
}

// Menu styles
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
    
    .uw-sidebar--rtl & {
      padding-left: 0;
      padding-right: var(--spacing-8);
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
  gap: var(--spacing-3);
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

// Menu content component styles (would be separate in real implementation)
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
  
  &--dot {
    min-width: 0.5em;
    height: 0.5em;
    padding: 0;
  }
}

// Footer styles
.uw-sidebar-footer {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border-primary);
  flex-shrink: 0;
}

// Responsive design
@media (max-width: 768px) {
  .uw-sidebar {
    &:not(&--overlay) {
      position: relative;
      height: auto;
      width: 100% !important;
      border-right: none;
      border-bottom: 1px solid var(--color-border-primary);
    }
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-sidebar {
    background: var(--color-surface-secondary);
    border-color: var(--color-border-secondary);
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-sidebar {
    border-width: 2px;
  }
  
  .uw-sidebar-menu-link,
  .uw-sidebar-menu-button {
    border: 1px solid transparent;
    
    &:focus {
      border-color: var(--color-primary);
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-sidebar,
  .uw-sidebar-brand-text,
  .uw-sidebar-user-info,
  .uw-sidebar-menu-label,
  .uw-sidebar-menu-badge,
  .uw-sidebar-menu-link,
  .uw-sidebar-menu-button,
  .uw-sidebar-toggle {
    transition: none;
  }
}
</style>