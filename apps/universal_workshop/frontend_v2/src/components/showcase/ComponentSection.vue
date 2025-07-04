<!--
  Component Section - Documentation Section Container
-->

<template>
  <section v-if="visible" class="component-section">
    <div class="section-header">
      <h2 class="section-title">{{ title }}</h2>
      <p v-if="description" class="section-description">{{ description }}</p>
      <UWBadge :content="category" variant="secondary" size="sm" />
    </div>
    
    <div class="section-content">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
import { UWBadge } from '@/components/primitives'

interface ComponentSectionProps {
  title: string
  description?: string
  category?: string
  visible?: boolean
}

withDefaults(defineProps<ComponentSectionProps>(), {
  visible: true
})
</script>

<style lang="scss" scoped>
.component-section {
  margin-bottom: var(--spacing-12);
  
  &:last-child {
    margin-bottom: 0;
  }
}

.section-header {
  margin-bottom: var(--spacing-8);
  padding-bottom: var(--spacing-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-2);
}

.section-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-3);
  line-height: var(--line-height-relaxed);
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-8);
}
</style>