<!--
  Component Demo - Individual Component Demonstration
-->

<template>
  <div class="component-demo">
    <div class="demo-header">
      <h3 class="demo-title">{{ title }}</h3>
      <p v-if="description" class="demo-description">{{ description }}</p>
    </div>
    
    <div class="demo-tabs">
      <button
        :class="['demo-tab', { 'demo-tab--active': activeTab === 'demo' }]"
        @click="activeTab = 'demo'"
      >
        <UWIcon name="eye" size="sm" />
        Demo
      </button>
      
      <button
        :class="['demo-tab', { 'demo-tab--active': activeTab === 'code' }]"
        @click="activeTab = 'code'"
      >
        <UWIcon name="code" size="sm" />
        Code
      </button>
      
      <button
        v-if="$slots.props"
        :class="['demo-tab', { 'demo-tab--active': activeTab === 'props' }]"
        @click="activeTab = 'props'"
      >
        <UWIcon name="settings" size="sm" />
        Props
      </button>
    </div>
    
    <div class="demo-content">
      <!-- Demo view -->
      <div v-if="activeTab === 'demo'" class="demo-view">
        <div class="demo-preview">
          <slot name="demo" />
        </div>
      </div>
      
      <!-- Code view -->
      <div v-if="activeTab === 'code'" class="demo-code">
        <slot name="code" />
      </div>
      
      <!-- Props view -->
      <div v-if="activeTab === 'props'" class="demo-props">
        <slot name="props">
          <p class="no-props">No props documentation available</p>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UWIcon } from '@/components/primitives'

interface ComponentDemoProps {
  title: string
  description?: string
}

defineProps<ComponentDemoProps>()

const activeTab = ref<'demo' | 'code' | 'props'>('demo')
</script>

<style lang="scss" scoped>
.component-demo {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-background-elevated);
}

.demo-header {
  padding: var(--spacing-4) var(--spacing-6);
  background: var(--color-background-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
}

.demo-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
}

.demo-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

.demo-tabs {
  display: flex;
  background: var(--color-background-muted);
  border-bottom: 1px solid var(--color-border-subtle);
}

.demo-tab {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: transparent;
  border: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
  
  &--active {
    background: var(--color-background-elevated);
    color: var(--color-primary);
    border-bottom: 2px solid var(--color-primary);
  }
}

.demo-content {
  min-height: 200px;
}

.demo-view {
  padding: var(--spacing-6);
}

.demo-preview {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  align-items: flex-start;
}

.demo-code {
  // Code styling will be handled by CodeBlock component
}

.demo-props {
  padding: var(--spacing-6);
}

.no-props {
  color: var(--color-text-secondary);
  font-style: italic;
  text-align: center;
  padding: var(--spacing-8);
}

// Responsive design
@media (max-width: 768px) {
  .demo-tabs {
    flex-direction: column;
  }
  
  .demo-tab {
    justify-content: center;
  }
  
  .demo-preview {
    align-items: stretch;
  }
}
</style>