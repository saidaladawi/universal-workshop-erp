<!--
  Component Showcase - Universal Workshop Frontend V2
  
  Interactive documentation and showcase system for all components
  with live examples, code snippets, and Arabic/RTL demonstrations.
-->

<template>
  <div :class="showcaseClasses">
    <!-- Header -->
    <header class="showcase-header">
      <div class="showcase-header-content">
        <h1 class="showcase-title">
          {{ preferArabic ? 'معرض مكونات النظام' : 'Component Showcase' }}
        </h1>
        <p class="showcase-subtitle">
          {{ preferArabic 
            ? 'مكتبة تفاعلية لجميع مكونات نظام الورشة الشاملة' 
            : 'Interactive library of Universal Workshop components' 
          }}
        </p>
        
        <!-- Controls -->
        <div class="showcase-controls">
          <Button
            variant="outline"
            size="sm"
            @click="toggleLanguage"
          >
            {{ preferArabic ? 'English' : 'العربية' }}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            @click="toggleTheme"
          >
            {{ isDark ? '☀️' : '🌙' }}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            @click="toggleRTL"
          >
            {{ isRTL ? 'LTR' : 'RTL' }}
          </Button>
        </div>
      </div>
    </header>

    <!-- Navigation -->
    <nav class="showcase-nav">
      <div class="showcase-nav-content">
        <Tabs
          :tabs="navigationTabs"
          :active-tab="activeCategory"
          variant="underlined"
          :prefer-arabic="preferArabic"
          @tab-change="handleCategoryChange"
        />
      </div>
    </nav>

    <!-- Main Content -->
    <main class="showcase-main">
      <Container size="xl" class="showcase-container">
        <Grid cols="auto 1fr" gap="lg" class="showcase-grid">
          <!-- Sidebar -->
          <aside class="showcase-sidebar">
            <div class="component-list">
              <div
                v-for="component in currentComponents"
                :key="component.name"
                class="component-item"
                :class="{ 'component-item--active': activeComponent === component.name }"
                @click="setActiveComponent(component.name)"
              >
                <span class="component-icon" v-html="component.icon" />
                <span class="component-name">
                  {{ preferArabic && component.nameAr ? component.nameAr : component.name }}
                </span>
                <span v-if="component.badge" class="component-badge">{{ component.badge }}</span>
              </div>
            </div>
          </aside>

          <!-- Content Area -->
          <section class="showcase-content">
            <ComponentDocumentation
              :component="currentComponentData"
              :prefer-arabic="preferArabic"
              :is-rtl="isRTL"
              @example-change="handleExampleChange"
            />
          </section>
        </Grid>
      </Container>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, provide, ref, watch } from 'vue'
import { Button } from '@/components/base'
import { Container, Grid } from '@/components/layout'
import { Tabs } from '@/components/navigation'
import ComponentDocumentation from './ComponentDocumentation.vue'
import { componentRegistry } from './component-registry'

// Component state
const preferArabic = ref(true)
const isDark = ref(false)
const isRTL = ref(true)
const activeCategory = ref(0)
const activeComponent = ref('Button')
const currentExample = ref('')

// Provide global context
provide('preferArabic', preferArabic)
provide('isRTL', isRTL)
provide('isDark', isDark)

// Navigation tabs
const navigationTabs = computed(() => [
  {
    key: 'base',
    label: 'Base Components',
    labelAr: 'المكونات الأساسية',
  },
  {
    key: 'forms',
    label: 'Form Components',
    labelAr: 'مكونات النماذج',
  },
  {
    key: 'layout',
    label: 'Layout Components',
    labelAr: 'مكونات التخطيط',
  },
  {
    key: 'navigation',
    label: 'Navigation',
    labelAr: 'التنقل',
  },
  {
    key: 'feedback',
    label: 'Feedback',
    labelAr: 'التفاعل',
  },
  {
    key: 'arabic',
    label: 'Arabic/RTL',
    labelAr: 'العربية/RTL',
  },
])

// Get current category components
const currentComponents = computed(() => {
  const categoryKey = navigationTabs.value[activeCategory.value]?.key
  return componentRegistry[categoryKey] || []
})

// Get current component data
const currentComponentData = computed(() => {
  return currentComponents.value.find(comp => comp.name === activeComponent.value)
})

// Computed classes
const showcaseClasses = computed(() => [
  'component-showcase',
  {
    'component-showcase--rtl': isRTL.value,
    'component-showcase--arabic': preferArabic.value,
    'component-showcase--dark': isDark.value,
  },
])

// Methods
const toggleLanguage = () => {
  preferArabic.value = !preferArabic.value
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
}

const toggleRTL = () => {
  isRTL.value = !isRTL.value
  document.documentElement.setAttribute('dir', isRTL.value ? 'rtl' : 'ltr')
}

const handleCategoryChange = (index: number) => {
  activeCategory.value = index
  // Set first component as active when changing category
  const firstComponent = currentComponents.value[0]
  if (firstComponent) {
    activeComponent.value = firstComponent.name
  }
}

const setActiveComponent = (componentName: string) => {
  activeComponent.value = componentName
  currentExample.value = ''
}

const handleExampleChange = (exampleKey: string) => {
  currentExample.value = exampleKey
}

// Watch for category changes to update active component
watch(currentComponents, (newComponents) => {
  if (newComponents.length > 0 && !newComponents.find(comp => comp.name === activeComponent.value)) {
    activeComponent.value = newComponents[0].name
  }
})

// Initialize theme and direction
toggleTheme() // Apply initial theme
document.documentElement.setAttribute('dir', isRTL.value ? 'rtl' : 'ltr')
</script>

<style lang="scss" scoped>
.component-showcase {
  min-height: 100vh;
  background: var(--color-surface-primary);
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  // Arabic font preference
  &--arabic {
    font-family: var(--font-family-arabic);
  }
}

// Header styles
.showcase-header {
  background: var(--color-surface-primary);
  border-bottom: 1px solid var(--color-border-primary);
  padding: var(--spacing-6) 0;
}

.showcase-header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-6);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  
  @media (min-width: 768px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.showcase-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
  line-height: var(--line-height-tight);
}

.showcase-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: var(--line-height-relaxed);
}

.showcase-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-shrink: 0;
}

// Navigation styles
.showcase-nav {
  background: var(--color-surface-primary);
  border-bottom: 1px solid var(--color-border-primary);
  padding: 0;
}

.showcase-nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}

// Main content styles
.showcase-main {
  flex: 1;
  padding: var(--spacing-6) 0;
}

.showcase-container {
  height: 100%;
}

.showcase-grid {
  min-height: calc(100vh - 200px);
  align-items: start;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
}

// Sidebar styles
.showcase-sidebar {
  width: 280px;
  background: var(--color-surface-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-primary);
  padding: var(--spacing-4);
  position: sticky;
  top: var(--spacing-6);
  max-height: calc(100vh - var(--spacing-12));
  overflow-y: auto;
  
  @media (max-width: 768px) {
    width: 100%;
    position: static;
    max-height: none;
  }
  
  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--color-surface-primary);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--color-border-secondary);
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb:hover {
    background: var(--color-border-primary);
  }
}

.component-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.component-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-colors);
  text-decoration: none;
  color: var(--color-text-secondary);
  
  &:hover {
    background: var(--color-surface-tertiary);
    color: var(--color-text-primary);
  }
  
  &--active {
    background: var(--color-primary-50);
    color: var(--color-primary);
    font-weight: var(--font-weight-medium);
    
    .component-icon {
      color: var(--color-primary);
    }
  }
}

.component-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-6);
  height: var(--spacing-6);
  flex-shrink: 0;
  color: var(--color-text-tertiary);
  
  :deep(svg) {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

.component-name {
  flex: 1;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.component-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: var(--spacing-5);
  height: var(--spacing-5);
  padding: 0 var(--spacing-1);
  background: var(--color-primary);
  color: var(--color-primary-foreground);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1;
}

// Content styles
.showcase-content {
  min-width: 0;
  flex: 1;
}

// Dark mode adjustments
[data-theme="dark"] {
  .showcase-header,
  .showcase-nav {
    background: var(--color-surface-secondary);
    border-color: var(--color-border-secondary);
  }
  
  .showcase-sidebar {
    background: var(--color-surface-tertiary);
    border-color: var(--color-border-secondary);
  }
  
  .component-item--active {
    background: var(--color-primary-900);
    color: var(--color-primary-200);
  }
}

// High contrast mode
[data-contrast="high"] {
  .showcase-header,
  .showcase-nav {
    border-width: 2px;
  }
  
  .showcase-sidebar {
    border-width: 2px;
  }
  
  .component-item {
    border: 1px solid transparent;
    
    &--active {
      border-color: var(--color-primary);
    }
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .component-item {
    transition: none;
  }
}

// Print styles
@media print {
  .showcase-header,
  .showcase-nav,
  .showcase-sidebar {
    display: none;
  }
  
  .showcase-grid {
    grid-template-columns: 1fr;
  }
}
</style>