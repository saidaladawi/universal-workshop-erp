<!--
  Breadcrumb Component - Universal Workshop Frontend V2
  
  A navigation breadcrumb component showing the user's current location
  in the application hierarchy with Arabic/RTL support.
-->

<template>
  <nav
    :class="breadcrumbClasses"
    :aria-label="ariaLabel"
    role="navigation"
  >
    <ol class="uw-breadcrumb-list">
      <li
        v-for="(item, index) in items"
        :key="item.key || index"
        class="uw-breadcrumb-item"
        :class="{
          'uw-breadcrumb-item--current': index === items.length - 1,
          'uw-breadcrumb-item--disabled': item.disabled,
        }"
      >
        <!-- Link item -->
        <component
          v-if="item.href && index !== items.length - 1 && !item.disabled"
          :is="linkComponent"
          :to="item.href"
          :href="item.href"
          class="uw-breadcrumb-link"
          :aria-current="index === items.length - 1 ? 'page' : undefined"
          @click="handleItemClick(item, index, $event)"
        >
          <!-- Icon -->
          <span
            v-if="item.icon"
            class="uw-breadcrumb-icon"
            v-html="item.icon"
          />
          
          <!-- Label -->
          <span class="uw-breadcrumb-label">
            <span v-if="preferArabic && item.labelAr">{{ item.labelAr }}</span>
            <span v-else-if="item.label">{{ item.label }}</span>
            <span v-else-if="item.labelAr">{{ item.labelAr }}</span>
          </span>
        </component>
        
        <!-- Button item (clickable but no href) -->
        <button
          v-else-if="!item.href && index !== items.length - 1 && !item.disabled && item.clickable"
          type="button"
          class="uw-breadcrumb-button"
          :aria-current="index === items.length - 1 ? 'page' : undefined"
          @click="handleItemClick(item, index, $event)"
        >
          <!-- Icon -->
          <span
            v-if="item.icon"
            class="uw-breadcrumb-icon"
            v-html="item.icon"
          />
          
          <!-- Label -->
          <span class="uw-breadcrumb-label">
            <span v-if="preferArabic && item.labelAr">{{ item.labelAr }}</span>
            <span v-else-if="item.label">{{ item.label }}</span>
            <span v-else-if="item.labelAr">{{ item.labelAr }}</span>
          </span>
        </button>
        
        <!-- Static item (current page or disabled) -->
        <span
          v-else
          class="uw-breadcrumb-text"
          :aria-current="index === items.length - 1 ? 'page' : undefined"
        >
          <!-- Icon -->
          <span
            v-if="item.icon"
            class="uw-breadcrumb-icon"
            v-html="item.icon"
          />
          
          <!-- Label -->
          <span class="uw-breadcrumb-label">
            <span v-if="preferArabic && item.labelAr">{{ item.labelAr }}</span>
            <span v-else-if="item.label">{{ item.label }}</span>
            <span v-else-if="item.labelAr">{{ item.labelAr }}</span>
          </span>
        </span>
        
        <!-- Separator -->
        <span
          v-if="index < items.length - 1"
          class="uw-breadcrumb-separator"
          aria-hidden="true"
        >
          <span v-if="customSeparator" v-html="customSeparator" />
          <svg v-else class="uw-breadcrumb-separator-icon" viewBox="0 0 24 24" fill="currentColor">
            <path :d="separatorPath" />
          </svg>
        </span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
import { computed, inject } from 'vue'

// Define breadcrumb item interface
export interface BreadcrumbItem {
  /** Unique key for the item */
  key?: string
  /** Item label */
  label?: string
  /** Arabic item label */
  labelAr?: string
  /** Link href (for router-link or regular links) */
  href?: string
  /** Custom icon HTML/SVG */
  icon?: string
  /** Item is disabled */
  disabled?: boolean
  /** Item is clickable (for non-href items) */
  clickable?: boolean
  /** Custom data to pass with click events */
  data?: any
}

// Define component props
export interface BreadcrumbProps {
  /** Breadcrumb items */
  items: BreadcrumbItem[]
  /** Custom separator HTML/SVG */
  separator?: string
  /** Maximum items to show before collapsing */
  maxItems?: number
  /** Show home icon for first item */
  showHome?: boolean
  /** Home icon HTML/SVG */
  homeIcon?: string
  /** Link component to use (for router integration) */
  linkComponent?: string | object
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface BreadcrumbEmits {
  'item-click': [item: BreadcrumbItem, index: number, event: Event]
}

// Setup props with defaults
const props = withDefaults(defineProps<BreadcrumbProps>(), {
  maxItems: 0,
  showHome: false,
  linkComponent: 'a',
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<BreadcrumbEmits>()

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Aria label for navigation
const ariaLabel = computed(() => {
  return props.preferArabic ? 'مسار التنقل' : 'Breadcrumb navigation'
})

// Custom separator
const customSeparator = computed(() => props.separator)

// Default separator path (chevron right/left based on RTL)
const separatorPath = computed(() => {
  if (isRTL) {
    // Chevron left for RTL
    return "M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"
  }
  // Chevron right for LTR
  return "M8.59 16.59L10 18l6-6-6-6-1.41 1.41L13.17 12z"
})

// Process items with home icon and collapsing
const processedItems = computed(() => {
  let items = [...props.items]
  
  // Add home icon to first item if requested
  if (props.showHome && items.length > 0 && !items[0].icon) {
    items[0] = {
      ...items[0],
      icon: props.homeIcon || getDefaultHomeIcon(),
    }
  }
  
  // Handle collapsing if maxItems is set
  if (props.maxItems > 0 && items.length > props.maxItems) {
    const firstItem = items[0]
    const lastItems = items.slice(-(props.maxItems - 2))
    const ellipsis: BreadcrumbItem = {
      key: 'ellipsis',
      label: '...',
      labelAr: '...',
      disabled: true,
    }
    
    items = [firstItem, ellipsis, ...lastItems]
  }
  
  return items
})

// Default home icon
const getDefaultHomeIcon = (): string => {
  return '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>'
}

// Computed classes
const breadcrumbClasses = computed(() => [
  'uw-breadcrumb',
  {
    'uw-breadcrumb--rtl': isRTL,
    'uw-breadcrumb--prefer-arabic': props.preferArabic,
  },
  props.class,
])

// Event handlers
const handleItemClick = (item: BreadcrumbItem, index: number, event: Event) => {
  if (item.disabled) {
    event.preventDefault()
    return
  }
  
  emit('item-click', item, index, event)
}

// Expose items for parent access
defineExpose({
  items: processedItems,
})
</script>

<style lang="scss" scoped>
.uw-breadcrumb {
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--prefer-arabic {
    font-family: var(--font-family-arabic);
  }
}

.uw-breadcrumb-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: var(--spacing-2);
}

.uw-breadcrumb-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  
  &--current {
    .uw-breadcrumb-text {
      color: var(--color-text-primary);
      font-weight: var(--font-weight-medium);
    }
  }
  
  &--disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}

// Common styles for interactive elements
.uw-breadcrumb-link,
.uw-breadcrumb-button,
.uw-breadcrumb-text {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-tight);
  text-decoration: none;
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  padding: var(--spacing-1) var(--spacing-2);
  transition: var(--transition-colors);
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
}

// Link styles
.uw-breadcrumb-link {
  &:hover {
    color: var(--color-text-primary);
    background-color: var(--color-surface-secondary);
  }
  
  &:active {
    background-color: var(--color-surface-tertiary);
  }
}

// Button styles
.uw-breadcrumb-button {
  border: none;
  background: transparent;
  cursor: pointer;
  
  &:hover {
    color: var(--color-text-primary);
    background-color: var(--color-surface-secondary);
  }
  
  &:active {
    background-color: var(--color-surface-tertiary);
  }
}

// Text styles (for current/disabled items)
.uw-breadcrumb-text {
  cursor: default;
}

// Icon styles
.uw-breadcrumb-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1em;
  height: 1em;
  flex-shrink: 0;
  
  :deep(svg) {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

// Label styles
.uw-breadcrumb-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  
  @media (max-width: 640px) {
    max-width: 120px;
  }
}

// Separator styles
.uw-breadcrumb-separator {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
  flex-shrink: 0;
  pointer-events: none;
  
  :deep(svg) {
    width: 1em;
    height: 1em;
    fill: currentColor;
  }
}

.uw-breadcrumb-separator-icon {
  width: 1em;
  height: 1em;
}

// Responsive design
@media (max-width: 640px) {
  .uw-breadcrumb-list {
    gap: var(--spacing-1);
  }
  
  .uw-breadcrumb-link,
  .uw-breadcrumb-button,
  .uw-breadcrumb-text {
    padding: var(--spacing-1);
    font-size: var(--font-size-xs);
  }
  
  // Hide middle items on very small screens, keep first and last
  .uw-breadcrumb-item:not(:first-child):not(:last-child):not(:nth-last-child(2)) {
    display: none;
  }
  
  // Show ellipsis between first and last on small screens
  .uw-breadcrumb-item:first-child::after {
    content: "...";
    color: var(--color-text-tertiary);
    margin: 0 var(--spacing-1);
    pointer-events: none;
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-breadcrumb-link,
  .uw-breadcrumb-button {
    border: 1px solid var(--color-border-primary);
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-breadcrumb-separator {
    color: var(--color-text-secondary);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-breadcrumb-link,
  .uw-breadcrumb-button {
    transition: none;
  }
}

// Print styles
@media print {
  .uw-breadcrumb {
    display: none;
  }
}
</style>