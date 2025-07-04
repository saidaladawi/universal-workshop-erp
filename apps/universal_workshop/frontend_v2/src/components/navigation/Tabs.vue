<!--
  Tabs Component - Universal Workshop Frontend V2
  
  A tabbed interface component for organizing content into switchable panels
  with keyboard navigation and Arabic/RTL support.
-->

<template>
  <div :class="tabsClasses">
    <!-- Tab list -->
    <div
      ref="tabListRef"
      class="uw-tabs-list"
      role="tablist"
      :aria-label="tabsLabel"
      @keydown="handleKeyDown"
    >
      <button
        v-for="(tab, index) in tabs"
        :key="tab.key || index"
        :ref="(el) => setTabRef(el as HTMLElement, index)"
        type="button"
        class="uw-tabs-tab"
        :class="{
          'uw-tabs-tab--active': activeTab === index,
          'uw-tabs-tab--disabled': tab.disabled,
        }"
        role="tab"
        :aria-selected="activeTab === index"
        :aria-controls="`${panelIdPrefix}-${index}`"
        :id="`${tabIdPrefix}-${index}`"
        :disabled="tab.disabled"
        :tabindex="activeTab === index ? 0 : -1"
        @click="handleTabClick(index, tab)"
        @focus="handleTabFocus(index)"
      >
        <!-- Icon -->
        <span
          v-if="tab.icon"
          class="uw-tabs-tab-icon"
          v-html="tab.icon"
        />
        
        <!-- Label -->
        <span class="uw-tabs-tab-label">
          <span v-if="preferArabic && tab.labelAr">{{ tab.labelAr }}</span>
          <span v-else-if="tab.label">{{ tab.label }}</span>
          <span v-else-if="tab.labelAr">{{ tab.labelAr }}</span>
        </span>
        
        <!-- Badge -->
        <span
          v-if="tab.badge !== undefined && tab.badge !== null"
          class="uw-tabs-tab-badge"
          :class="{
            'uw-tabs-tab-badge--dot': tab.badge === true,
          }"
        >
          <span v-if="tab.badge !== true">{{ tab.badge }}</span>
        </span>
        
        <!-- Close button -->
        <button
          v-if="tab.closable"
          type="button"
          class="uw-tabs-tab-close"
          :aria-label="getCloseLabel(tab)"
          @click.stop="handleTabClose(index, tab)"
        >
          <svg class="uw-tabs-tab-close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </button>
      
      <!-- Active tab indicator -->
      <div
        v-if="showIndicator"
        class="uw-tabs-indicator"
        :style="indicatorStyles"
      />
    </div>
    
    <!-- Tab panels -->
    <div class="uw-tabs-panels">
      <div
        v-for="(tab, index) in tabs"
        :key="`panel-${tab.key || index}`"
        :id="`${panelIdPrefix}-${index}`"
        class="uw-tabs-panel"
        :class="{
          'uw-tabs-panel--active': activeTab === index,
        }"
        role="tabpanel"
        :aria-labelledby="`${tabIdPrefix}-${index}`"
        :tabindex="activeTab === index ? 0 : -1"
        :hidden="activeTab !== index"
      >
        <slot
          :name="`panel-${index}`"
          :tab="tab"
          :index="index"
          :active="activeTab === index"
        >
          <slot
            :name="tab.key"
            :tab="tab"
            :index="index"
            :active="activeTab === index"
          >
            <div v-if="tab.content" v-html="tab.content" />
          </slot>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch, nextTick, onMounted } from 'vue'

// Define tab interface
export interface Tab {
  /** Unique key for the tab */
  key?: string
  /** Tab label */
  label?: string
  /** Arabic tab label */
  labelAr?: string
  /** Tab icon HTML/SVG */
  icon?: string
  /** Tab badge (number, string, or true for dot) */
  badge?: string | number | boolean
  /** Tab is disabled */
  disabled?: boolean
  /** Tab is closable */
  closable?: boolean
  /** Tab content (if not using slots) */
  content?: string
  /** Custom data */
  data?: any
}

// Define component props
export interface TabsProps {
  /** Tabs array */
  tabs: Tab[]
  /** Active tab index */
  activeTab?: number
  /** Tabs variant */
  variant?: 'default' | 'pills' | 'bordered' | 'underlined'
  /** Tabs size */
  size?: 'sm' | 'md' | 'lg'
  /** Tabs alignment */
  align?: 'start' | 'center' | 'end' | 'stretch'
  /** Show active tab indicator */
  showIndicator?: boolean
  /** Tabs are vertical */
  vertical?: boolean
  /** Enable keyboard navigation */
  keyboardNavigation?: boolean
  /** Lazy load tab panels */
  lazy?: boolean
  /** Prefer Arabic display */
  preferArabic?: boolean
  /** Custom CSS class */
  class?: string
}

// Define component emits
export interface TabsEmits {
  'update:activeTab': [index: number]
  'tab-click': [index: number, tab: Tab]
  'tab-close': [index: number, tab: Tab]
  'tab-change': [index: number, tab: Tab]
}

// Setup props with defaults
const props = withDefaults(defineProps<TabsProps>(), {
  activeTab: 0,
  variant: 'default',
  size: 'md',
  align: 'start',
  showIndicator: true,
  vertical: false,
  keyboardNavigation: true,
  lazy: false,
  preferArabic: true,
})

// Setup emits
const emit = defineEmits<TabsEmits>()

// Template refs
const tabListRef = ref<HTMLElement>()
const tabRefs = ref<HTMLElement[]>([])

// Check if RTL context is available
const isRTL = inject('isRTL', true)

// Internal state
const internalActiveTab = ref(props.activeTab)
const indicatorStyles = ref<Record<string, string>>({})

// Watch for external active tab changes
watch(() => props.activeTab, (newValue) => {
  internalActiveTab.value = newValue
  updateIndicator()
})

// Watch for internal active tab changes
watch(internalActiveTab, (newValue, oldValue) => {
  emit('update:activeTab', newValue)
  if (oldValue !== newValue) {
    emit('tab-change', newValue, props.tabs[newValue])
  }
  updateIndicator()
})

// Unique IDs for accessibility
const tabIdPrefix = computed(() => `tabs-tab-${Math.random().toString(36).substr(2, 9)}`)
const panelIdPrefix = computed(() => `tabs-panel-${Math.random().toString(36).substr(2, 9)}`)

// Tabs label for accessibility
const tabsLabel = computed(() => {
  return props.preferArabic ? 'تبويبات التنقل' : 'Navigation tabs'
})

// Set tab ref
const setTabRef = (el: HTMLElement, index: number) => {
  if (el) {
    tabRefs.value[index] = el
  }
}

// Get close label for accessibility
const getCloseLabel = (tab: Tab): string => {
  const label = props.preferArabic && tab.labelAr ? tab.labelAr : tab.label
  return props.preferArabic 
    ? `إغلاق تبويب ${label}` 
    : `Close tab ${label}`
}

// Update indicator position and size
const updateIndicator = async () => {
  if (!props.showIndicator || !tabRefs.value.length) return
  
  await nextTick()
  
  const activeTabElement = tabRefs.value[internalActiveTab.value]
  if (!activeTabElement) return
  
  const tabList = tabListRef.value
  if (!tabList) return
  
  const tabListRect = tabList.getBoundingClientRect()
  const tabRect = activeTabElement.getBoundingClientRect()
  
  if (props.vertical) {
    indicatorStyles.value = {
      top: `${tabRect.top - tabListRect.top}px`,
      height: `${tabRect.height}px`,
      width: '2px',
      left: isRTL ? 'auto' : '0',
      right: isRTL ? '0' : 'auto',
    }
  } else {
    indicatorStyles.value = {
      left: `${tabRect.left - tabListRect.left}px`,
      width: `${tabRect.width}px`,
      height: '2px',
      bottom: '0',
    }
  }
}

// Computed classes
const tabsClasses = computed(() => [
  'uw-tabs',
  `uw-tabs--${props.variant}`,
  `uw-tabs--${props.size}`,
  `uw-tabs--align-${props.align}`,
  {
    'uw-tabs--vertical': props.vertical,
    'uw-tabs--rtl': isRTL,
    'uw-tabs--prefer-arabic': props.preferArabic,
  },
  props.class,
])

// Event handlers
const handleTabClick = (index: number, tab: Tab) => {
  if (tab.disabled) return
  
  internalActiveTab.value = index
  emit('tab-click', index, tab)
}

const handleTabClose = (index: number, tab: Tab) => {
  emit('tab-close', index, tab)
}

const handleTabFocus = (index: number) => {
  if (props.keyboardNavigation) {
    internalActiveTab.value = index
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  if (!props.keyboardNavigation) return
  
  const { key } = event
  const currentIndex = internalActiveTab.value
  let newIndex = currentIndex
  
  if (props.vertical) {
    if (key === 'ArrowDown' || key === 'Down') {
      newIndex = currentIndex < props.tabs.length - 1 ? currentIndex + 1 : 0
    } else if (key === 'ArrowUp' || key === 'Up') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : props.tabs.length - 1
    }
  } else {
    if (key === 'ArrowRight' || key === 'Right') {
      newIndex = isRTL 
        ? (currentIndex > 0 ? currentIndex - 1 : props.tabs.length - 1)
        : (currentIndex < props.tabs.length - 1 ? currentIndex + 1 : 0)
    } else if (key === 'ArrowLeft' || key === 'Left') {
      newIndex = isRTL 
        ? (currentIndex < props.tabs.length - 1 ? currentIndex + 1 : 0)
        : (currentIndex > 0 ? currentIndex - 1 : props.tabs.length - 1)
    }
  }
  
  if (key === 'Home') {
    newIndex = 0
  } else if (key === 'End') {
    newIndex = props.tabs.length - 1
  }
  
  // Skip disabled tabs
  while (props.tabs[newIndex]?.disabled && newIndex !== currentIndex) {
    if (newIndex < currentIndex) {
      newIndex = newIndex > 0 ? newIndex - 1 : props.tabs.length - 1
    } else {
      newIndex = newIndex < props.tabs.length - 1 ? newIndex + 1 : 0
    }
  }
  
  if (newIndex !== currentIndex && !props.tabs[newIndex]?.disabled) {
    event.preventDefault()
    internalActiveTab.value = newIndex
    tabRefs.value[newIndex]?.focus()
  }
}

// Lifecycle
onMounted(() => {
  updateIndicator()
})

// Expose methods
defineExpose({
  activeTab: internalActiveTab,
  setActiveTab: (index: number) => {
    if (index >= 0 && index < props.tabs.length && !props.tabs[index].disabled) {
      internalActiveTab.value = index
    }
  },
  updateIndicator,
})
</script>

<style lang="scss" scoped>
.uw-tabs {
  display: flex;
  
  // Vertical layout
  &--vertical {
    flex-direction: row;
    
    .uw-tabs-list {
      flex-direction: column;
      border-right: 1px solid var(--color-border-primary);
      border-bottom: none;
      min-width: 200px;
    }
    
    .uw-tabs-panels {
      flex: 1;
      padding-left: var(--spacing-4);
    }
    
    &.uw-tabs--rtl {
      .uw-tabs-list {
        border-right: none;
        border-left: 1px solid var(--color-border-primary);
      }
      
      .uw-tabs-panels {
        padding-left: 0;
        padding-right: var(--spacing-4);
      }
    }
  }
  
  // Horizontal layout (default)
  &:not(&--vertical) {
    flex-direction: column;
    
    .uw-tabs-list {
      border-bottom: 1px solid var(--color-border-primary);
    }
    
    .uw-tabs-panels {
      padding-top: var(--spacing-4);
    }
  }
  
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

// Tab list styles
.uw-tabs-list {
  position: relative;
  display: flex;
  background: var(--color-surface-primary);
  
  // Alignment variants
  .uw-tabs--align-center & {
    justify-content: center;
  }
  
  .uw-tabs--align-end & {
    justify-content: flex-end;
  }
  
  .uw-tabs--align-stretch & {
    .uw-tabs-tab {
      flex: 1;
    }
  }
}

// Tab styles
.uw-tabs-tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: var(--transition-colors);
  color: var(--color-text-secondary);
  text-decoration: none;
  white-space: nowrap;
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: -2px;
  }
  
  &:hover:not(&--disabled) {
    color: var(--color-text-primary);
    background: var(--color-surface-secondary);
  }
  
  &--active {
    color: var(--color-primary);
    
    .uw-tabs--bordered & {
      background: var(--color-surface-primary);
      border-color: var(--color-border-primary);
      border-bottom-color: var(--color-surface-primary);
    }
  }
  
  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
    pointer-events: none;
  }
}

// Variant styles
.uw-tabs--default {
  .uw-tabs-tab {
    padding: var(--spacing-3) var(--spacing-4);
  }
}

.uw-tabs--pills {
  .uw-tabs-tab {
    padding: var(--spacing-2) var(--spacing-4);
    border-radius: var(--radius-full);
    margin: var(--spacing-1);
    
    &--active {
      background: var(--color-primary);
      color: var(--color-primary-foreground);
    }
  }
  
  .uw-tabs-indicator {
    display: none;
  }
}

.uw-tabs--bordered {
  .uw-tabs-tab {
    padding: var(--spacing-3) var(--spacing-4);
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    margin-bottom: -1px;
    
    &--active {
      border-color: var(--color-border-primary);
      border-bottom: 1px solid var(--color-surface-primary);
    }
  }
  
  .uw-tabs-indicator {
    display: none;
  }
}

.uw-tabs--underlined {
  .uw-tabs-tab {
    padding: var(--spacing-3) var(--spacing-4);
    border-bottom: 2px solid transparent;
    
    &--active {
      border-bottom-color: var(--color-primary);
    }
  }
  
  .uw-tabs-indicator {
    display: none;
  }
}

// Size variants
.uw-tabs--sm {
  .uw-tabs-tab {
    font-size: var(--font-size-sm);
    padding: var(--spacing-2) var(--spacing-3);
  }
}

.uw-tabs--md {
  .uw-tabs-tab {
    font-size: var(--font-size-base);
    padding: var(--spacing-3) var(--spacing-4);
  }
}

.uw-tabs--lg {
  .uw-tabs-tab {
    font-size: var(--font-size-lg);
    padding: var(--spacing-4) var(--spacing-6);
  }
}

// Tab elements
.uw-tabs-tab-icon {
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

.uw-tabs-tab-label {
  font-weight: var(--font-weight-medium);
}

.uw-tabs-tab-badge {
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
  
  &--dot {
    min-width: 0.5em;
    height: 0.5em;
    padding: 0;
  }
  
  .uw-tabs-tab--active & {
    background: var(--color-primary-600);
    color: var(--color-primary-foreground);
  }
}

.uw-tabs-tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.2em;
  height: 1.2em;
  border: none;
  background: transparent;
  color: currentColor;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: var(--transition-colors);
  margin-left: var(--spacing-1);
  
  &:hover {
    background: rgba(0, 0, 0, 0.1);
  }
  
  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
  
  .uw-tabs--rtl & {
    margin-left: 0;
    margin-right: var(--spacing-1);
  }
}

.uw-tabs-tab-close-icon {
  width: 0.8em;
  height: 0.8em;
}

// Active indicator
.uw-tabs-indicator {
  position: absolute;
  background: var(--color-primary);
  transition: all 0.2s ease-out;
  pointer-events: none;
  z-index: 1;
}

// Panels
.uw-tabs-panels {
  flex: 1;
  min-height: 0;
}

.uw-tabs-panel {
  &:not(&--active) {
    display: none;
  }
  
  &:focus {
    outline: none;
  }
}

// Responsive design
@media (max-width: 640px) {
  .uw-tabs--vertical {
    flex-direction: column;
    
    .uw-tabs-list {
      flex-direction: row;
      border-right: none;
      border-bottom: 1px solid var(--color-border-primary);
      min-width: auto;
      overflow-x: auto;
    }
    
    .uw-tabs-panels {
      padding-left: 0;
      padding-top: var(--spacing-4);
    }
  }
  
  .uw-tabs-list {
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    
    &::-webkit-scrollbar {
      display: none;
    }
  }
  
  .uw-tabs-tab {
    flex-shrink: 0;
  }
}

// Dark mode support
[data-theme="dark"] {
  .uw-tabs--bordered {
    .uw-tabs-tab--active {
      background: var(--color-surface-secondary);
    }
  }
}

// High contrast mode
[data-contrast="high"] {
  .uw-tabs-tab {
    border: 1px solid transparent;
    
    &--active {
      border-color: var(--color-primary);
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .uw-tabs-tab,
  .uw-tabs-indicator {
    transition: none;
  }
}
</style>