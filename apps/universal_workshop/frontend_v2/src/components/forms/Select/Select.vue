<!--
  Select Component - Universal Workshop Frontend V2
  
  A comprehensive select/dropdown component with search, multi-select,
  virtual scrolling, and Arabic/RTL support. Includes accessibility
  features and integrates with the form validation system.
-->

<template>
  <div
    :class="selectClasses"
    :style="selectStyles"
    :data-testid="dataTestId"
  >
    <!-- Label -->
    <label
      v-if="label"
      :for="selectId"
      :class="labelClasses"
    >
      {{ label }}
      <span v-if="labelAr && isRTL" class="select-label__ar">{{ labelAr }}</span>
      <span v-if="required" class="select-label__required" aria-label="required">*</span>
    </label>

    <!-- Select container -->
    <div
      :class="containerClasses"
      @click="toggleDropdown"
      @keydown="handleKeydown"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="isOpen"
      :aria-haspopup="'listbox'"
      :aria-labelledby="label ? `${selectId}-label` : undefined"
      :aria-describedby="helpText || errorMessage ? `${selectId}-help` : undefined"
      role="combobox"
    >
      <!-- Selected value display -->
      <div class="select-display">
        <!-- Multiple selection -->
        <template v-if="multiple && selectedOptions.length > 0">
          <div class="select-tags">
            <div
              v-for="option in selectedOptions.slice(0, maxTagsVisible)"
              :key="option.value"
              class="select-tag"
            >
              <span class="select-tag__text">
                {{ getOptionLabel(option) }}
              </span>
              <button
                v-if="!disabled"
                type="button"
                class="select-tag__remove"
                @click.stop="removeSelection(option.value)"
                :aria-label="`Remove ${getOptionLabel(option)}`"
              >
                <UWIcon name="x" size="xs" />
              </button>
            </div>
            <div
              v-if="selectedOptions.length > maxTagsVisible"
              class="select-tag select-tag--overflow"
            >
              +{{ selectedOptions.length - maxTagsVisible }}
            </div>
          </div>
        </template>

        <!-- Single selection -->
        <template v-else-if="!multiple && selectedOption">
          <span class="select-value">
            {{ getOptionLabel(selectedOption) }}
          </span>
        </template>

        <!-- Placeholder -->
        <span
          v-else
          class="select-placeholder"
        >
          {{ placeholder || (isRTL && placeholderAr ? placeholderAr : 'Select an option') }}
        </span>
      </div>

      <!-- Clear button -->
      <button
        v-if="clearable && hasSelection && !disabled"
        type="button"
        class="select-clear"
        @click.stop="clearSelection"
        :aria-label="'Clear selection'"
      >
        <UWIcon name="x" size="sm" />
      </button>

      <!-- Dropdown arrow -->
      <div class="select-arrow">
        <UWIcon
          name="chevron-down"
          size="sm"
          :class="{ 'select-arrow--open': isOpen }"
        />
      </div>
    </div>

    <!-- Dropdown menu -->
    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="dropdownRef"
        :class="dropdownClasses"
        :style="dropdownStyles"
        @click.stop
      >
        <!-- Search input -->
        <div v-if="searchable" class="select-search">
          <div class="select-search__container">
            <UWIcon name="search" size="sm" class="select-search__icon" />
            <input
              ref="searchInputRef"
              v-model="searchQuery"
              type="text"
              class="select-search__input"
              :placeholder="searchPlaceholder || 'Search options...'"
              :aria-label="'Search options'"
              @keydown="handleSearchKeydown"
            />
            <button
              v-if="searchQuery"
              type="button"
              class="select-search__clear"
              @click="searchQuery = ''"
              :aria-label="'Clear search'"
            >
              <UWIcon name="x" size="xs" />
            </button>
          </div>
        </div>

        <!-- Options list -->
        <div
          ref="optionsRef"
          class="select-options"
          role="listbox"
          :aria-multiselectable="multiple"
        >
          <!-- Virtual scrolling container -->
          <div
            v-if="virtual && filteredOptions.length > virtualThreshold"
            ref="virtualContainerRef"
            class="select-options__virtual"
            :style="{ height: `${virtualHeight}px` }"
          >
            <div
              v-for="(option, index) in visibleOptions"
              :key="option.value"
              :class="getOptionClasses(option, index)"
              :style="getOptionStyles(index)"
              @click="selectOption(option)"
              @mouseenter="setHighlightedIndex(index)"
              role="option"
              :aria-selected="isSelected(option.value)"
            >
              <!-- Option content -->
              <div class="select-option__content">
                <!-- Checkbox for multi-select -->
                <div
                  v-if="multiple"
                  class="select-option__checkbox"
                >
                  <UWIcon
                    :name="isSelected(option.value) ? 'check' : ''"
                    size="sm"
                    class="select-option__check-icon"
                  />
                </div>

                <!-- Option text -->
                <div class="select-option__text">
                  <span class="select-option__label">
                    {{ getOptionLabel(option) }}
                  </span>
                  <span
                    v-if="option.description"
                    class="select-option__description"
                  >
                    {{ option.description }}
                  </span>
                </div>

                <!-- Option icon -->
                <UWIcon
                  v-if="option.icon"
                  :name="option.icon"
                  size="sm"
                  class="select-option__icon"
                />
              </div>
            </div>
          </div>

          <!-- Regular scrolling -->
          <template v-else>
            <div
              v-for="(option, index) in filteredOptions"
              :key="option.value"
              :class="getOptionClasses(option, index)"
              @click="selectOption(option)"
              @mouseenter="setHighlightedIndex(index)"
              role="option"
              :aria-selected="isSelected(option.value)"
            >
              <!-- Option content (same as virtual) -->
              <div class="select-option__content">
                <div
                  v-if="multiple"
                  class="select-option__checkbox"
                >
                  <UWIcon
                    :name="isSelected(option.value) ? 'check' : ''"
                    size="sm"
                    class="select-option__check-icon"
                  />
                </div>

                <div class="select-option__text">
                  <span class="select-option__label">
                    {{ getOptionLabel(option) }}
                  </span>
                  <span
                    v-if="option.description"
                    class="select-option__description"
                  >
                    {{ option.description }}
                  </span>
                </div>

                <UWIcon
                  v-if="option.icon"
                  :name="option.icon"
                  size="sm"
                  class="select-option__icon"
                />
              </div>
            </div>
          </template>

          <!-- No options message -->
          <div
            v-if="filteredOptions.length === 0"
            class="select-no-options"
          >
            {{ noOptionsText || 'No options available' }}
          </div>

          <!-- Loading state -->
          <div
            v-if="loading"
            class="select-loading"
          >
            <UWIcon name="loading" size="sm" spin />
            <span>{{ loadingText || 'Loading...' }}</span>
          </div>
        </div>

        <!-- Create option (for creatable select) -->
        <div
          v-if="creatable && searchQuery && !hasExactMatch"
          class="select-create"
        >
          <button
            type="button"
            class="select-create__button"
            @click="createOption"
          >
            <UWIcon name="plus" size="sm" />
            <span>Create "{{ searchQuery }}"</span>
          </button>
        </div>
      </div>
    </Teleport>

    <!-- Help text -->
    <div
      v-if="helpText || errorMessage"
      :id="`${selectId}-help`"
      :class="helpClasses"
    >
      {{ errorMessage || helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { 
  ref, 
  computed, 
  watch, 
  nextTick, 
  onMounted, 
  onUnmounted, 
  inject,
  type StyleValue 
} from 'vue'
import UWIcon from '@/components/primitives/Icon/Icon.vue'
import { createPopper, type Instance as PopperInstance } from '@popperjs/core'

// Option interface
export interface SelectOption {
  label: string
  labelAr?: string
  value: any
  description?: string
  icon?: string
  disabled?: boolean
  group?: string
}

// Component props
export interface SelectProps {
  /** Options array */
  options: SelectOption[]
  /** Selected value(s) */
  modelValue?: any
  /** Field label */
  label?: string
  /** Arabic label */
  labelAr?: string
  /** Placeholder text */
  placeholder?: string
  /** Arabic placeholder */
  placeholderAr?: string
  /** Help text */
  helpText?: string
  /** Error message */
  errorMessage?: string
  /** Disabled state */
  disabled?: boolean
  /** Required field */
  required?: boolean
  /** Multiple selection */
  multiple?: boolean
  /** Allow clearing selection */
  clearable?: boolean
  /** Enable search */
  searchable?: boolean
  /** Search placeholder */
  searchPlaceholder?: string
  /** Allow creating new options */
  creatable?: boolean
  /** Loading state */
  loading?: boolean
  /** Loading text */
  loadingText?: string
  /** No options text */
  noOptionsText?: string
  /** Maximum visible tags in multi-select */
  maxTagsVisible?: number
  /** Enable virtual scrolling */
  virtual?: boolean
  /** Virtual scrolling threshold */
  virtualThreshold?: number
  /** Virtual scrolling height */
  virtualHeight?: number
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: StyleValue
  /** Test ID for testing */
  dataTestId?: string
}

// Component emits
export interface SelectEmits {
  'update:modelValue': [value: any]
  'change': [value: any, option: SelectOption | SelectOption[]]
  'search': [query: string]
  'create': [value: string]
  'open': []
  'close': []
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
}

// Setup props with defaults
const props = withDefaults(defineProps<SelectProps>(), {
  multiple: false,
  clearable: false,
  searchable: false,
  creatable: false,
  loading: false,
  disabled: false,
  required: false,
  maxTagsVisible: 3,
  virtual: false,
  virtualThreshold: 100,
  virtualHeight: 200,
  size: 'md'
})

// Setup emits
const emit = defineEmits<SelectEmits>()

// Reactive state
const isOpen = ref(false)
const searchQuery = ref('')
const highlightedIndex = ref(-1)
const selectId = ref(`select-${Math.random().toString(36).substr(2, 9)}`)

// Template refs
const dropdownRef = ref<HTMLElement>()
const searchInputRef = ref<HTMLInputElement>()
const optionsRef = ref<HTMLElement>()
const virtualContainerRef = ref<HTMLElement>()

// Popper instance for positioning
let popperInstance: PopperInstance | null = null

// Injected context
const isRTL = inject('isRTL', false)

// Computed properties
const selectedOptions = computed(() => {
  if (!props.multiple) return []
  
  const values = Array.isArray(props.modelValue) ? props.modelValue : []
  return props.options.filter(option => values.includes(option.value))
})

const selectedOption = computed(() => {
  if (props.multiple) return null
  return props.options.find(option => option.value === props.modelValue) || null
})

const hasSelection = computed(() => {
  if (props.multiple) {
    return selectedOptions.value.length > 0
  }
  return selectedOption.value !== null
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(option => {
    const label = getOptionLabel(option).toLowerCase()
    const description = option.description?.toLowerCase() || ''
    return label.includes(query) || description.includes(query)
  })
})

const hasExactMatch = computed(() => {
  return filteredOptions.value.some(option => 
    getOptionLabel(option).toLowerCase() === searchQuery.value.toLowerCase()
  )
})

const visibleOptions = computed(() => {
  if (!props.virtual) return filteredOptions.value
  
  // Virtual scrolling logic would go here
  // For now, return first items
  return filteredOptions.value.slice(0, 10)
})

// Classes
const selectClasses = computed(() => [
  'uw-select',
  `uw-select--${props.size}`,
  {
    'uw-select--disabled': props.disabled,
    'uw-select--error': props.errorMessage,
    'uw-select--open': isOpen.value,
    'uw-select--rtl': isRTL.value,
    'uw-select--multiple': props.multiple,
  },
  props.class
])

const labelClasses = computed(() => [
  'select-label',
  {
    'select-label--required': props.required,
    'select-label--disabled': props.disabled,
  }
])

const containerClasses = computed(() => [
  'select-container',
  {
    'select-container--disabled': props.disabled,
    'select-container--error': props.errorMessage,
    'select-container--open': isOpen.value,
  }
])

const dropdownClasses = computed(() => [
  'select-dropdown',
  {
    'select-dropdown--rtl': isRTL.value,
  }
])

const helpClasses = computed(() => [
  'select-help',
  {
    'select-help--error': props.errorMessage,
  }
])

// Computed styles
const selectStyles = computed(() => {
  return typeof props.style === 'object' ? props.style : {}
})

const dropdownStyles = ref<Record<string, string>>({})

// Methods
const getOptionLabel = (option: SelectOption): string => {
  if (isRTL.value && option.labelAr) {
    return option.labelAr
  }
  return option.label
}

const isSelected = (value: any): boolean => {
  if (props.multiple) {
    const values = Array.isArray(props.modelValue) ? props.modelValue : []
    return values.includes(value)
  }
  return props.modelValue === value
}

const toggleDropdown = (): void => {
  if (props.disabled) return
  
  if (isOpen.value) {
    closeDropdown()
  } else {
    openDropdown()
  }
}

const openDropdown = async (): Promise<void> => {
  isOpen.value = true
  emit('open')
  
  await nextTick()
  
  if (props.searchable && searchInputRef.value) {
    searchInputRef.value.focus()
  }
  
  // Setup positioning
  setupPopper()
}

const closeDropdown = (): void => {
  isOpen.value = false
  searchQuery.value = ''
  highlightedIndex.value = -1
  emit('close')
  
  // Cleanup popper
  if (popperInstance) {
    popperInstance.destroy()
    popperInstance = null
  }
}

const setupPopper = (): void => {
  const trigger = document.getElementById(selectId.value)
  if (!trigger || !dropdownRef.value) return
  
  popperInstance = createPopper(trigger, dropdownRef.value, {
    placement: isRTL.value ? 'bottom-end' : 'bottom-start',
    modifiers: [
      {
        name: 'offset',
        options: {
          offset: [0, 4]
        }
      },
      {
        name: 'preventOverflow',
        options: {
          padding: 8
        }
      }
    ]
  })
}

const selectOption = (option: SelectOption): void => {
  if (option.disabled) return
  
  if (props.multiple) {
    const values = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    const index = values.indexOf(option.value)
    
    if (index > -1) {
      values.splice(index, 1)
    } else {
      values.push(option.value)
    }
    
    emit('update:modelValue', values)
    emit('change', values, selectedOptions.value)
  } else {
    emit('update:modelValue', option.value)
    emit('change', option.value, option)
    closeDropdown()
  }
}

const removeSelection = (value: any): void => {
  if (!props.multiple) return
  
  const values = Array.isArray(props.modelValue) ? [...props.modelValue] : []
  const index = values.indexOf(value)
  
  if (index > -1) {
    values.splice(index, 1)
    emit('update:modelValue', values)
    emit('change', values, selectedOptions.value)
  }
}

const clearSelection = (): void => {
  const newValue = props.multiple ? [] : null
  emit('update:modelValue', newValue)
  emit('change', newValue, props.multiple ? [] : null)
}

const createOption = (): void => {
  if (!searchQuery.value.trim()) return
  
  emit('create', searchQuery.value.trim())
  searchQuery.value = ''
}

const setHighlightedIndex = (index: number): void => {
  highlightedIndex.value = index
}

const getOptionClasses = (option: SelectOption, index: number) => [
  'select-option',
  {
    'select-option--selected': isSelected(option.value),
    'select-option--highlighted': index === highlightedIndex.value,
    'select-option--disabled': option.disabled,
  }
]

const getOptionStyles = (index: number) => {
  // Virtual scrolling styles would go here
  return {}
}

// Keyboard navigation
const handleKeydown = (event: KeyboardEvent): void => {
  switch (event.key) {
    case 'Enter':
    case ' ':
      event.preventDefault()
      if (!isOpen.value) {
        openDropdown()
      } else if (highlightedIndex.value >= 0) {
        selectOption(filteredOptions.value[highlightedIndex.value])
      }
      break
      
    case 'Escape':
      closeDropdown()
      break
      
    case 'ArrowDown':
      event.preventDefault()
      if (!isOpen.value) {
        openDropdown()
      } else {
        setHighlightedIndex(Math.min(highlightedIndex.value + 1, filteredOptions.value.length - 1))
      }
      break
      
    case 'ArrowUp':
      event.preventDefault()
      if (isOpen.value) {
        setHighlightedIndex(Math.max(highlightedIndex.value - 1, 0))
      }
      break
  }
}

const handleSearchKeydown = (event: KeyboardEvent): void => {
  switch (event.key) {
    case 'ArrowDown':
    case 'ArrowUp':
      handleKeydown(event)
      break
      
    case 'Enter':
      event.preventDefault()
      if (highlightedIndex.value >= 0) {
        selectOption(filteredOptions.value[highlightedIndex.value])
      } else if (props.creatable && searchQuery.value && !hasExactMatch.value) {
        createOption()
      }
      break
  }
}

// Click outside handler
const handleClickOutside = (event: Event): void => {
  const target = event.target as HTMLElement
  if (!dropdownRef.value?.contains(target)) {
    closeDropdown()
  }
}

// Watch for search changes
watch(searchQuery, (newQuery) => {
  emit('search', newQuery)
  highlightedIndex.value = 0
})

// Lifecycle
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (popperInstance) {
    popperInstance.destroy()
  }
})
</script>

<script lang="ts">
export default {
  name: 'UWSelect'
}
</script>

<style lang="scss" scoped>
.uw-select {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  
  &--disabled {
    opacity: 0.6;
    pointer-events: none;
  }
  
  &--rtl {
    text-align: right;
  }
}

// Label styles
.select-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  
  &__ar {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }
  
  &__required {
    color: var(--color-error);
  }
  
  &--disabled {
    color: var(--color-text-disabled);
  }
}

// Container styles
.select-container {
  position: relative;
  display: flex;
  align-items: center;
  min-height: var(--input-height-md);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-background-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover:not(&--disabled) {
    border-color: var(--color-border-hover);
  }
  
  &:focus-within,
  &--open {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px var(--color-primary-lighter);
  }
  
  &--error {
    border-color: var(--color-error);
    
    &:focus-within {
      box-shadow: 0 0 0 3px var(--color-error-lighter);
    }
  }
  
  &--disabled {
    background: var(--color-background-disabled);
    cursor: not-allowed;
  }
}

// Display area
.select-display {
  flex: 1;
  display: flex;
  align-items: center;
  min-height: 1.25rem;
}

.select-value {
  color: var(--color-text-primary);
}

.select-placeholder {
  color: var(--color-text-placeholder);
}

// Tags for multi-select
.select-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
}

.select-tag {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: var(--spacing-1) var(--spacing-2);
  background: var(--color-background-subtle);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  
  &--overflow {
    background: var(--color-background-muted);
    color: var(--color-text-secondary);
  }
  
  &__text {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__remove {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: var(--transition-colors);
    
    &:hover {
      background: var(--color-background-hover);
      color: var(--color-text-primary);
    }
  }
}

// Control buttons
.select-clear,
.select-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: var(--color-text-secondary);
}

.select-clear {
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
}

.select-arrow {
  margin-left: var(--spacing-1);
  
  &--open {
    transform: rotate(180deg);
  }
}

// Dropdown styles
.select-dropdown {
  z-index: 1000;
  min-width: 200px;
  max-width: 400px;
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  
  &--rtl {
    text-align: right;
  }
}

// Search input
.select-search {
  padding: var(--spacing-2);
  border-bottom: 1px solid var(--color-border-subtle);
  
  &__container {
    position: relative;
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }
  
  &__icon {
    color: var(--color-text-secondary);
  }
  
  &__input {
    flex: 1;
    padding: var(--spacing-2);
    background: transparent;
    border: none;
    outline: none;
    font-size: var(--font-size-sm);
    color: var(--color-text-primary);
    
    &::placeholder {
      color: var(--color-text-placeholder);
    }
  }
  
  &__clear {
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    
    &:hover {
      color: var(--color-text-primary);
    }
  }
}

// Options list
.select-options {
  max-height: 200px;
  overflow-y: auto;
  
  &__virtual {
    position: relative;
    overflow-y: auto;
  }
}

.select-option {
  display: flex;
  align-items: center;
  padding: var(--spacing-2) var(--spacing-3);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover:not(&--disabled) {
    background: var(--color-background-hover);
  }
  
  &--selected {
    background: var(--color-primary-lighter);
    color: var(--color-primary-dark);
  }
  
  &--highlighted {
    background: var(--color-background-subtle);
  }
  
  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  &__content {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    width: 100%;
  }
  
  &__checkbox {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    border: 1px solid var(--color-border-input);
    border-radius: var(--radius-sm);
    
    .select-option--selected & {
      background: var(--color-primary);
      border-color: var(--color-primary);
      color: white;
    }
  }
  
  &__text {
    flex: 1;
    min-width: 0;
  }
  
  &__label {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__description {
    display: block;
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  &__icon {
    color: var(--color-text-secondary);
  }
}

// Empty state
.select-no-options {
  padding: var(--spacing-4);
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

// Loading state
.select-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-4);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

// Create option
.select-create {
  padding: var(--spacing-2);
  border-top: 1px solid var(--color-border-subtle);
  
  &__button {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    width: 100%;
    padding: var(--spacing-2);
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    color: var(--color-primary);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: var(--transition-colors);
    
    &:hover {
      background: var(--color-primary-lighter);
    }
  }
}

// Help text
.select-help {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  
  &--error {
    color: var(--color-error);
  }
}

// Size variants
.uw-select--sm {
  .select-container {
    min-height: var(--input-height-sm);
    padding: var(--spacing-1-5) var(--spacing-2);
    font-size: var(--font-size-sm);
  }
}

.uw-select--lg {
  .select-container {
    min-height: var(--input-height-lg);
    padding: var(--spacing-3) var(--spacing-4);
    font-size: var(--font-size-lg);
  }
}

// High contrast mode
[data-contrast="high"] {
  .select-container {
    border-width: 2px;
  }
  
  .select-option--selected {
    outline: 2px solid var(--color-primary);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .select-container,
  .select-option,
  .select-arrow {
    transition: none;
  }
}
</style>