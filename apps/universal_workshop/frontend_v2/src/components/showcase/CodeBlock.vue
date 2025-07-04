<!--
  Code Block - Syntax Highlighted Code Display
-->

<template>
  <div class="code-block">
    <div class="code-header">
      <span class="code-language">{{ language }}</span>
      <button
        class="code-copy"
        @click="copyCode"
        :aria-label="copied ? 'Copied!' : 'Copy code'"
      >
        <UWIcon :name="copied ? 'check' : 'copy'" size="sm" />
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
    </div>
    
    <pre class="code-content"><code :class="`language-${language}`" v-html="highlightedCode"></code></pre>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, useSlots } from 'vue'
import { UWIcon } from '@/components/primitives'

interface CodeBlockProps {
  language?: string
  code?: string
}

const props = withDefaults(defineProps<CodeBlockProps>(), {
  language: 'javascript'
})

const slots = useSlots()
const copied = ref(false)

// Get code content from slot or prop
const codeContent = computed(() => {
  if (props.code) return props.code
  
  const slotContent = slots.default?.()
  if (slotContent && slotContent[0] && typeof slotContent[0].children === 'string') {
    return slotContent[0].children.trim()
  }
  
  return ''
})

// Simple syntax highlighting (in a real app, use Prism.js or similar)
const highlightedCode = computed(() => {
  const code = codeContent.value
  
  // Basic Vue template highlighting
  if (props.language === 'vue') {
    return code
      .replace(/(&lt;[^&]+&gt;)/g, '<span class="token tag">$1</span>')
      .replace(/(v-[a-zA-Z-]+)/g, '<span class="token directive">$1</span>')
      .replace(/(:?[a-zA-Z-]+="[^"]*")/g, '<span class="token attr">$1</span>')
      .replace(/({{[^}]+}})/g, '<span class="token interpolation">$1</span>')
  }
  
  // Basic JavaScript highlighting
  if (props.language === 'javascript' || props.language === 'js') {
    return code
      .replace(/\b(const|let|var|function|return|if|else|for|while|import|export|default)\b/g, '<span class="token keyword">$1</span>')
      .replace(/\b(true|false|null|undefined)\b/g, '<span class="token boolean">$1</span>')
      .replace(/'([^']*)'/g, '<span class="token string">\'$1\'</span>')
      .replace(/"([^"]*)"/g, '<span class="token string">"$1"</span>')
      .replace(/\/\/.*$/gm, '<span class="token comment">$&</span>')
  }
  
  return code
})

// Copy to clipboard
const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(codeContent.value)
    copied.value = true
    
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy code:', err)
  }
}
</script>

<style lang="scss" scoped>
.code-block {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-background-code, #1e1e1e);
  color: var(--color-text-code, #d4d4d4);
  font-family: var(--font-family-mono, 'Fira Code', 'Monaco', 'Consolas', monospace);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2) var(--spacing-4);
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid var(--color-border-subtle);
}

.code-language {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
  color: var(--color-text-secondary);
  letter-spacing: 0.1em;
}

.code-copy {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-1) var(--spacing-2);
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--color-text-primary);
  }
}

.code-content {
  margin: 0;
  padding: var(--spacing-4);
  overflow-x: auto;
  font-size: var(--font-size-sm);
  line-height: var(--line-height-relaxed);
  
  code {
    font-family: inherit;
    background: transparent;
    color: inherit;
  }
}

// Syntax highlighting styles
:deep(.token) {
  &.tag {
    color: #569cd6;
  }
  
  &.directive {
    color: #9cdcfe;
  }
  
  &.attr {
    color: #92c5f7;
  }
  
  &.interpolation {
    color: #ce9178;
  }
  
  &.keyword {
    color: #569cd6;
  }
  
  &.boolean {
    color: #569cd6;
  }
  
  &.string {
    color: #ce9178;
  }
  
  &.comment {
    color: #6a9955;
    font-style: italic;
  }
}

// Light theme overrides
[data-theme="light"] {
  .code-block {
    background: var(--color-background-subtle);
    color: var(--color-text-primary);
    
    .code-header {
      background: rgba(0, 0, 0, 0.05);
    }
    
    .code-copy {
      border-color: var(--color-border-input);
      color: var(--color-text-secondary);
      
      &:hover {
        background: var(--color-background-hover);
      }
    }
  }
  
  :deep(.token) {
    &.tag {
      color: #0000ff;
    }
    
    &.directive {
      color: #800000;
    }
    
    &.attr {
      color: #ff0000;
    }
    
    &.interpolation {
      color: #a31515;
    }
    
    &.keyword {
      color: #0000ff;
    }
    
    &.boolean {
      color: #0000ff;
    }
    
    &.string {
      color: #a31515;
    }
    
    &.comment {
      color: #008000;
    }
  }
}

// Responsive design
@media (max-width: 768px) {
  .code-content {
    font-size: var(--font-size-xs);
  }
  
  .code-header {
    flex-direction: column;
    gap: var(--spacing-2);
    align-items: flex-start;
  }
}
</style>