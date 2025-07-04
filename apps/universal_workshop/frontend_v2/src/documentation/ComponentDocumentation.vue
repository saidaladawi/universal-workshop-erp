<!--
  Component Documentation - Universal Workshop Frontend V2
  
  Detailed documentation renderer for individual components including
  examples, props, events, and usage guidelines with Arabic/RTL support.
-->

<template>
  <div v-if="component" :class="documentationClasses">
    <!-- Component Header -->
    <header class="component-header">
      <div class="component-title-section">
        <h1 class="component-title">
          <span class="component-icon" v-html="component.icon" />
          {{ preferArabic && component.nameAr ? component.nameAr : component.name }}
          <span v-if="component.badge" class="component-badge">{{ component.badge }}</span>
        </h1>
        <p class="component-description">
          {{ preferArabic && component.descriptionAr ? component.descriptionAr : component.description }}
        </p>
      </div>
      
      <!-- Quick Actions -->
      <div class="component-actions">
        <Button
          variant="outline"
          size="sm"
          @click="copyComponentImport"
        >
          {{ preferArabic ? 'نسخ الاستيراد' : 'Copy Import' }}
        </Button>
        
        <Button
          variant="outline"
          size="sm"
          @click="toggleCodeView"
        >
          {{ showCode ? (preferArabic ? 'إخفاء الكود' : 'Hide Code') : (preferArabic ? 'إظهار الكود' : 'Show Code') }}
        </Button>
      </div>
    </header>

    <!-- Usage Guidelines -->
    <section v-if="component.usage" class="documentation-section">
      <h2 class="section-title">
        {{ preferArabic ? 'الاستخدام' : 'Usage' }}
      </h2>
      <div class="usage-content">
        <p>{{ preferArabic && component.usageAr ? component.usageAr : component.usage }}</p>
        <div v-if="component.notes" class="usage-notes">
          <strong>{{ preferArabic ? 'ملاحظة:' : 'Note:' }}</strong>
          {{ preferArabic && component.notesAr ? component.notesAr : component.notes }}
        </div>
      </div>
    </section>

    <!-- Live Examples -->
    <section v-if="component.examples.length" class="documentation-section">
      <h2 class="section-title">
        {{ preferArabic ? 'أمثلة تفاعلية' : 'Interactive Examples' }}
      </h2>
      
      <div class="examples-container">
        <Tabs
          :tabs="exampleTabs"
          :active-tab="activeExample"
          variant="pills"
          :prefer-arabic="preferArabic"
          @tab-change="handleExampleChange"
        />
        
        <div class="example-content">
          <div v-if="currentExample" class="example">
            <!-- Example Description -->
            <div class="example-description">
              <h3 class="example-title">
                {{ preferArabic && currentExample.titleAr ? currentExample.titleAr : currentExample.title }}
              </h3>
              <p class="example-text">
                {{ preferArabic && currentExample.descriptionAr ? currentExample.descriptionAr : currentExample.description }}
              </p>
            </div>
            
            <!-- Live Preview -->
            <div class="example-preview">
              <div class="preview-header">
                <span class="preview-label">
                  {{ preferArabic ? 'المعاينة المباشرة' : 'Live Preview' }}
                </span>
                <div class="preview-controls">
                  <Button
                    variant="ghost"
                    size="sm"
                    @click="refreshExample"
                    :title="preferArabic ? 'تحديث المعاينة' : 'Refresh Preview'"
                  >
                    🔄
                  </Button>
                </div>
              </div>
              
              <div class="preview-content">
                <ExampleRenderer
                  :template="currentExample.template"
                  :props="currentExample.props"
                  :prefer-arabic="preferArabic"
                  :is-rtl="isRTL"
                />
              </div>
            </div>
            
            <!-- Code Display -->
            <Transition name="code-collapse">
              <div v-if="showCode" class="example-code">
                <div class="code-header">
                  <span class="code-label">
                    {{ preferArabic ? 'الكود' : 'Code' }}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    @click="copyExampleCode"
                  >
                    {{ preferArabic ? 'نسخ' : 'Copy' }}
                  </Button>
                </div>
                <pre class="code-block"><code>{{ currentExample.code }}</code></pre>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </section>

    <!-- API Reference -->
    <section class="documentation-section">
      <h2 class="section-title">
        {{ preferArabic ? 'مرجع API' : 'API Reference' }}
      </h2>
      
      <Tabs
        :tabs="apiTabs"
        :active-tab="activeApiSection"
        variant="underlined"
        :prefer-arabic="preferArabic"
        @tab-change="handleApiSectionChange"
      />
      
      <div class="api-content">
        <!-- Props -->
        <div v-if="activeApiSection === 0 && component.props.length" class="api-section">
          <div class="props-table">
            <table class="api-table">
              <thead>
                <tr>
                  <th>{{ preferArabic ? 'الاسم' : 'Name' }}</th>
                  <th>{{ preferArabic ? 'النوع' : 'Type' }}</th>
                  <th>{{ preferArabic ? 'افتراضي' : 'Default' }}</th>
                  <th>{{ preferArabic ? 'مطلوب' : 'Required' }}</th>
                  <th>{{ preferArabic ? 'الوصف' : 'Description' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="prop in component.props" :key="prop.name">
                  <td class="prop-name">{{ prop.name }}</td>
                  <td class="prop-type">{{ prop.type }}</td>
                  <td class="prop-default">
                    <code v-if="prop.default !== undefined">{{ prop.default }}</code>
                    <span v-else class="no-default">-</span>
                  </td>
                  <td class="prop-required">
                    <span v-if="prop.required" class="required-badge">
                      {{ preferArabic ? 'نعم' : 'Yes' }}
                    </span>
                    <span v-else class="optional-badge">
                      {{ preferArabic ? 'لا' : 'No' }}
                    </span>
                  </td>
                  <td class="prop-description">
                    {{ preferArabic && prop.descriptionAr ? prop.descriptionAr : prop.description }}
                    <div v-if="prop.options" class="prop-options">
                      <strong>{{ preferArabic ? 'الخيارات:' : 'Options:' }}</strong>
                      <code v-for="option in prop.options" :key="option" class="option-value">{{ option }}</code>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Events -->
        <div v-if="activeApiSection === 1 && component.events.length" class="api-section">
          <div class="events-table">
            <table class="api-table">
              <thead>
                <tr>
                  <th>{{ preferArabic ? 'الحدث' : 'Event' }}</th>
                  <th>{{ preferArabic ? 'البيانات' : 'Payload' }}</th>
                  <th>{{ preferArabic ? 'الوصف' : 'Description' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="event in component.events" :key="event.name">
                  <td class="event-name">{{ event.name }}</td>
                  <td class="event-payload">
                    <code v-if="event.payload">{{ event.payload }}</code>
                    <span v-else>-</span>
                  </td>
                  <td class="event-description">
                    {{ preferArabic && event.descriptionAr ? event.descriptionAr : event.description }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Slots -->
        <div v-if="activeApiSection === 2 && component.slots.length" class="api-section">
          <div class="slots-table">
            <table class="api-table">
              <thead>
                <tr>
                  <th>{{ preferArabic ? 'الفتحة' : 'Slot' }}</th>
                  <th>{{ preferArabic ? 'الخصائص' : 'Props' }}</th>
                  <th>{{ preferArabic ? 'الوصف' : 'Description' }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="slot in component.slots" :key="slot.name">
                  <td class="slot-name">{{ slot.name }}</td>
                  <td class="slot-props">
                    <div v-if="slot.props" class="slot-props-list">
                      <code v-for="(type, name) in slot.props" :key="name" class="slot-prop">
                        {{ name }}: {{ type }}
                      </code>
                    </div>
                    <span v-else>-</span>
                  </td>
                  <td class="slot-description">
                    {{ preferArabic && slot.descriptionAr ? slot.descriptionAr : slot.description }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-if="!hasApiData" class="api-empty">
          <p>{{ preferArabic ? 'لا توجد بيانات API متاحة' : 'No API data available' }}</p>
        </div>
      </div>
    </section>
  </div>
  
  <!-- Loading State -->
  <div v-else class="documentation-loading">
    <div class="loading-spinner">
      <div class="spinner"></div>
    </div>
    <p>{{ preferArabic ? 'جارٍ تحميل الوثائق...' : 'Loading documentation...' }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Button } from '@/components/base'
import { Tabs } from '@/components/navigation'
import type { ComponentInfo } from './component-registry'
import ExampleRenderer from './ExampleRenderer.vue'

// Define component props
export interface ComponentDocumentationProps {
  component?: ComponentInfo
  preferArabic?: boolean
  isRTL?: boolean
}

// Define component emits
export interface ComponentDocumentationEmits {
  'example-change': [exampleKey: string]
}

// Setup props with defaults
const props = withDefaults(defineProps<ComponentDocumentationProps>(), {
  preferArabic: true,
  isRTL: true,
})

// Setup emits
const emit = defineEmits<ComponentDocumentationEmits>()

// Component state
const showCode = ref(false)
const activeExample = ref(0)
const activeApiSection = ref(0)

// Computed values
const documentationClasses = computed(() => [
  'component-documentation',
  {
    'component-documentation--rtl': props.isRTL,
    'component-documentation--arabic': props.preferArabic,
  },
])

const exampleTabs = computed(() => {
  if (!props.component?.examples.length) return []
  
  return props.component.examples.map((example, index) => ({
    key: example.key,
    label: props.preferArabic && example.titleAr ? example.titleAr : example.title,
    labelAr: example.titleAr,
  }))
})

const currentExample = computed(() => {
  if (!props.component?.examples.length) return null
  return props.component.examples[activeExample.value]
})

const apiTabs = computed(() => [
  {
    key: 'props',
    label: props.preferArabic ? 'الخصائص' : 'Props',
    labelAr: 'الخصائص',
    badge: props.component?.props.length || 0,
  },
  {
    key: 'events',
    label: props.preferArabic ? 'الأحداث' : 'Events',
    labelAr: 'الأحداث',
    badge: props.component?.events.length || 0,
  },
  {
    key: 'slots',
    label: props.preferArabic ? 'الفتحات' : 'Slots',
    labelAr: 'الفتحات',
    badge: props.component?.slots.length || 0,
  },
])

const hasApiData = computed(() => {
  if (!props.component) return false
  return props.component.props.length > 0 || 
         props.component.events.length > 0 || 
         props.component.slots.length > 0
})

// Methods
const toggleCodeView = () => {
  showCode.value = !showCode.value
}

const copyComponentImport = async () => {
  if (!props.component) return
  
  const importStatement = `import { ${props.component.name} } from '@/components/${props.component.category}'`
  
  try {
    await navigator.clipboard.writeText(importStatement)
    // Show success message (would integrate with Toast component)
    console.log('Import statement copied to clipboard')
  } catch (error) {
    console.error('Failed to copy import statement:', error)
  }
}

const copyExampleCode = async () => {
  if (!currentExample.value) return
  
  try {
    await navigator.clipboard.writeText(currentExample.value.code)
    console.log('Example code copied to clipboard')
  } catch (error) {
    console.error('Failed to copy example code:', error)
  }
}

const refreshExample = () => {
  // Force re-render of example (would implement proper refresh logic)
  console.log('Refreshing example')
}

const handleExampleChange = (index: number) => {
  activeExample.value = index
  const example = props.component?.examples[index]
  if (example) {
    emit('example-change', example.key)
  }
}

const handleApiSectionChange = (index: number) => {
  activeApiSection.value = index
}

// Watch for component changes to reset state
watch(() => props.component, () => {
  activeExample.value = 0
  activeApiSection.value = 0
  showCode.value = false
})
</script>

<style lang="scss" scoped>
.component-documentation {
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
.component-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-8);
  padding-bottom: var(--spacing-6);
  border-bottom: 2px solid var(--color-border-primary);
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: stretch;
  }
}

.component-title-section {
  flex: 1;
}

.component-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-3) 0;
  line-height: var(--line-height-tight);
}

.component-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--spacing-8);
  height: var(--spacing-8);
  color: var(--color-primary);
  flex-shrink: 0;
  
  :deep(svg) {
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
}

.component-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-1) var(--spacing-2);
  background: var(--color-primary);
  color: var(--color-primary-foreground);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1;
}

.component-description {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: var(--line-height-relaxed);
}

.component-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-shrink: 0;
}

// Section styles
.documentation-section {
  margin-bottom: var(--spacing-8);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--spacing-4) 0;
  padding-bottom: var(--spacing-2);
  border-bottom: 1px solid var(--color-border-primary);
}

// Usage section
.usage-content {
  background: var(--color-surface-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  
  p {
    margin: 0 0 var(--spacing-3) 0;
    line-height: var(--line-height-relaxed);
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.usage-notes {
  background: var(--color-warning-50);
  border: 1px solid var(--color-warning-200);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  font-size: var(--font-size-sm);
  color: var(--color-warning-800);
  
  strong {
    color: var(--color-warning-900);
  }
}

// Examples section
.examples-container {
  background: var(--color-surface-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-primary);
  overflow: hidden;
}

.example-content {
  padding: var(--spacing-6);
}

.example {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.example-description {
  h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text-primary);
    margin: 0 0 var(--spacing-2) 0;
  }
  
  p {
    color: var(--color-text-secondary);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }
}

.example-preview {
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-surface-tertiary);
  border-bottom: 1px solid var(--color-border-primary);
}

.preview-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.preview-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.preview-content {
  padding: var(--spacing-6);
  background: var(--color-surface-primary);
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

// Code section
.example-code {
  border: 1px solid var(--color-border-primary);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-surface-tertiary);
  border-bottom: 1px solid var(--color-border-primary);
}

.code-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.code-block {
  margin: 0;
  padding: var(--spacing-4);
  background: var(--color-surface-primary);
  color: var(--color-text-primary);
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  overflow-x: auto;
  
  code {
    font-family: inherit;
    white-space: pre;
  }
}

// API section
.api-content {
  background: var(--color-surface-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-primary);
  padding: var(--spacing-6);
}

.api-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
  
  th {
    text-align: left;
    padding: var(--spacing-3);
    background: var(--color-surface-tertiary);
    color: var(--color-text-primary);
    font-weight: var(--font-weight-semibold);
    border-bottom: 2px solid var(--color-border-primary);
    
    .component-documentation--rtl & {
      text-align: right;
    }
  }
  
  td {
    padding: var(--spacing-3);
    border-bottom: 1px solid var(--color-border-primary);
    vertical-align: top;
  }
  
  tr:last-child td {
    border-bottom: none;
  }
}

.prop-name,
.event-name,
.slot-name {
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
}

.prop-type {
  font-family: var(--font-family-mono);
  color: var(--color-text-secondary);
}

.prop-default {
  code {
    font-family: var(--font-family-mono);
    background: var(--color-surface-primary);
    padding: var(--spacing-1);
    border-radius: var(--radius-sm);
  }
}

.no-default {
  color: var(--color-text-tertiary);
}

.required-badge {
  background: var(--color-error-50);
  color: var(--color-error);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.optional-badge {
  background: var(--color-surface-primary);
  color: var(--color-text-tertiary);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.prop-options {
  margin-top: var(--spacing-2);
  
  .option-value {
    display: inline-block;
    margin-right: var(--spacing-2);
    margin-top: var(--spacing-1);
    font-family: var(--font-family-mono);
    background: var(--color-surface-primary);
    padding: var(--spacing-1);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
  }
}

.slot-props-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.slot-prop {
  font-family: var(--font-family-mono);
  background: var(--color-surface-primary);
  padding: var(--spacing-1);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
}

.api-empty {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-text-secondary);
}

// Loading state
.documentation-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  text-align: center;
}

.loading-spinner {
  margin-bottom: var(--spacing-4);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-border-primary);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

// Transitions
.code-collapse-enter-active,
.code-collapse-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.code-collapse-enter-from,
.code-collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.code-collapse-enter-to,
.code-collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}

// Animations
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// Dark mode support
[data-theme="dark"] {
  .usage-notes {
    background: var(--color-warning-900);
    border-color: var(--color-warning-700);
    color: var(--color-warning-200);
    
    strong {
      color: var(--color-warning-100);
    }
  }
  
  .examples-container,
  .api-content {
    background: var(--color-surface-tertiary);
    border-color: var(--color-border-secondary);
  }
  
  .preview-header,
  .code-header {
    background: var(--color-surface-secondary);
  }
  
  .api-table th {
    background: var(--color-surface-secondary);
  }
}

// Responsive design
@media (max-width: 768px) {
  .api-table {
    font-size: var(--font-size-xs);
    
    th,
    td {
      padding: var(--spacing-2);
    }
  }
  
  .example-preview,
  .example-code {
    margin: 0 -var(--spacing-4);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .code-collapse-enter-active,
  .code-collapse-leave-active,
  .spinner {
    animation: none;
    transition: none;
  }
}

// Print styles
@media print {
  .component-actions,
  .preview-controls,
  .code-header {
    display: none;
  }
  
  .example-code {
    border: 1px solid #000;
  }
}
</style>