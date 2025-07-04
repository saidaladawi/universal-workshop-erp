<!--
  Date Picker Component - Universal Workshop Frontend V2
  
  A comprehensive date picker with Gregorian/Hijri calendar support,
  Arabic localization, and accessibility features.
-->

<template>
  <div
    :class="datePickerClasses"
    :style="datePickerStyles"
  >
    <!-- Label -->
    <label
      v-if="label"
      :for="datePickerId"
      :class="labelClasses"
    >
      {{ label }}
      <span v-if="labelAr && isRTL" class="date-label__ar">{{ labelAr }}</span>
      <span v-if="required" class="date-label__required">*</span>
    </label>

    <!-- Input container -->
    <div
      :class="containerClasses"
      @click="toggleCalendar"
    >
      <input
        :id="datePickerId"
        ref="inputRef"
        v-model="displayValue"
        type="text"
        :placeholder="placeholder || (isRTL && placeholderAr ? placeholderAr : 'Select date')"
        :disabled="disabled"
        :readonly="readonly"
        :required="required"
        :aria-expanded="isOpen"
        :aria-haspopup="'dialog'"
        :aria-describedby="helpText || errorMessage ? `${datePickerId}-help` : undefined"
        :aria-invalid="!!errorMessage"
        class="date-input"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown="handleKeydown"
      />
      
      <!-- Calendar icon -->
      <div class="date-icon">
        <UWIcon name="calendar" size="sm" />
      </div>
      
      <!-- Clear button -->
      <button
        v-if="clearable && modelValue && !disabled"
        type="button"
        class="date-clear"
        @click.stop="clearValue"
        :aria-label="'Clear date'"
      >
        <UWIcon name="x" size="sm" />
      </button>
    </div>

    <!-- Calendar dropdown -->
    <Teleport to="body">
      <div
        v-if="isOpen"
        ref="calendarRef"
        :class="calendarClasses"
        :style="calendarStyles"
        @click.stop
      >
        <!-- Calendar header -->
        <div class="calendar-header">
          <!-- Navigation buttons -->
          <div class="calendar-nav">
            <button
              type="button"
              class="calendar-nav-btn"
              @click="navigateMonth(-1)"
              :aria-label="'Previous month'"
            >
              <UWIcon name="chevron-left" size="sm" />
            </button>
            
            <button
              type="button"
              class="calendar-nav-btn"
              @click="navigateYear(-1)"
              :aria-label="'Previous year'"
            >
              <UWIcon name="chevron-left" size="sm" />
              <UWIcon name="chevron-left" size="sm" />
            </button>
          </div>
          
          <!-- Month/Year display -->
          <div class="calendar-title">
            <button
              type="button"
              class="calendar-month-btn"
              @click="showMonthPicker = !showMonthPicker"
            >
              {{ formatMonthYear(currentDate) }}
            </button>
          </div>
          
          <!-- Navigation buttons -->
          <div class="calendar-nav">
            <button
              type="button"
              class="calendar-nav-btn"
              @click="navigateYear(1)"
              :aria-label="'Next year'"
            >
              <UWIcon name="chevron-right" size="sm" />
              <UWIcon name="chevron-right" size="sm" />
            </button>
            
            <button
              type="button"
              class="calendar-nav-btn"
              @click="navigateMonth(1)"
              :aria-label="'Next month'"
            >
              <UWIcon name="chevron-right" size="sm" />
            </button>
          </div>
        </div>
        
        <!-- Calendar type toggle -->
        <div v-if="showCalendarToggle" class="calendar-toggle">
          <UWSwitch
            v-model="useHijriCalendar"
            :label="isRTL ? 'التقويم الهجري' : 'Hijri Calendar'"
            size="sm"
          />
        </div>
        
        <!-- Month picker -->
        <div v-if="showMonthPicker" class="month-picker">
          <button
            v-for="(month, index) in monthNames"
            :key="index"
            type="button"
            :class="getMonthClasses(index)"
            @click="selectMonth(index)"
          >
            {{ month }}
          </button>
        </div>
        
        <!-- Calendar grid -->
        <div v-else class="calendar-grid">
          <!-- Day headers -->
          <div class="calendar-header-row">
            <div
              v-for="day in dayHeaders"
              :key="day"
              class="calendar-day-header"
            >
              {{ day }}
            </div>
          </div>
          
          <!-- Calendar days -->
          <button
            v-for="day in calendarDays"
            :key="`${day.year}-${day.month}-${day.day}`"
            type="button"
            :class="getDayClasses(day)"
            :disabled="isDayDisabled(day)"
            @click="selectDate(day)"
            :aria-label="formatDayAriaLabel(day)"
          >
            {{ day.day }}
          </button>
        </div>
        
        <!-- Today button -->
        <div class="calendar-footer">
          <button
            type="button"
            class="calendar-today-btn"
            @click="selectToday"
          >
            {{ isRTL ? 'اليوم' : 'Today' }}
          </button>
        </div>
      </div>
    </Teleport>
    
    <!-- Help text -->
    <div
      v-if="helpText || errorMessage"
      :id="`${datePickerId}-help`"
      :class="helpClasses"
    >
      {{ errorMessage || helpText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted, inject } from 'vue'
import UWIcon from '@/components/primitives/Icon/Icon.vue'
import UWSwitch from '../Switch/Switch.vue'
import { createPopper, type Instance as PopperInstance } from '@popperjs/core'

// Date utility functions (simplified - in production, use a library like date-fns or moment)
interface CalendarDay {
  day: number
  month: number
  year: number
  isCurrentMonth: boolean
  isToday: boolean
  isSelected: boolean
  isDisabled: boolean
  date: Date
}

// Define component props
export interface DatePickerProps {
  /** Selected date value */
  modelValue?: Date | string | null
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
  /** Readonly state */
  readonly?: boolean
  /** Required field */
  required?: boolean
  /** Allow clearing the value */
  clearable?: boolean
  /** Date format for display */
  format?: string
  /** Minimum allowed date */
  minDate?: Date | string
  /** Maximum allowed date */
  maxDate?: Date | string
  /** Disabled dates */
  disabledDates?: (Date | string)[]
  /** Show Hijri calendar toggle */
  showCalendarToggle?: boolean
  /** Default to Hijri calendar */
  defaultHijri?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Custom CSS class */
  class?: string
  /** Custom styles */
  style?: string | Record<string, string>
}

// Define component emits
export interface DatePickerEmits {
  'update:modelValue': [value: Date | null]
  'change': [value: Date | null, formatted: string]
  'focus': [event: FocusEvent]
  'blur': [event: FocusEvent]
  'open': []
  'close': []
}

// Setup props with defaults
const props = withDefaults(defineProps<DatePickerProps>(), {
  size: 'md',
  clearable: false,
  disabled: false,
  readonly: false,
  required: false,
  showCalendarToggle: true,
  defaultHijri: false,
  format: 'DD/MM/YYYY'
})

// Setup emits
const emit = defineEmits<DatePickerEmits>()

// Reactive state
const isOpen = ref(false)
const showMonthPicker = ref(false)
const useHijriCalendar = ref(props.defaultHijri)
const currentDate = ref(new Date())
const datePickerId = ref(`datepicker-${Math.random().toString(36).substr(2, 9)}`)

// Template refs
const inputRef = ref<HTMLInputElement>()
const calendarRef = ref<HTMLElement>()

// Popper instance
let popperInstance: PopperInstance | null = null

// Injected context
const isRTL = inject('isRTL', false)

// Date formatting and parsing
const formatDate = (date: Date | null, hijri = false): string => {
  if (!date) return ''
  
  if (hijri) {
    // Simplified Hijri formatting - in production, use proper Hijri calendar library
    return `${date.getDate()}/${date.getMonth() + 1}/${date.getFullYear() - 579}هـ`
  }
  
  // Gregorian formatting
  const day = date.getDate().toString().padStart(2, '0')
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const year = date.getFullYear()
  
  if (isRTL) {
    return `${day}/${month}/${year}`
  }
  
  return props.format
    .replace('DD', day)
    .replace('MM', month)
    .replace('YYYY', year.toString())
}

const parseDate = (value: string | Date | null): Date | null => {
  if (!value) return null
  if (value instanceof Date) return value
  
  // Simple parsing - in production, use proper date parsing
  const parts = value.split('/')
  if (parts.length === 3) {
    const day = parseInt(parts[0])
    const month = parseInt(parts[1]) - 1
    const year = parseInt(parts[2])
    return new Date(year, month, day)
  }
  
  return null
}

// Display value for input
const displayValue = computed({
  get() {
    const date = parseDate(props.modelValue)
    return formatDate(date, useHijriCalendar.value)
  },
  set(value: string) {
    if (!value.trim()) {
      emit('update:modelValue', null)
      return
    }
    
    const parsed = parseDate(value)
    if (parsed) {
      emit('update:modelValue', parsed)
    }
  }
})

// Calendar data
const monthNames = computed(() => {
  if (useHijriCalendar.value) {
    return isRTL.value ? [
      'محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني', 'جمادى الأولى', 'جمادى الثانية',
      'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'
    ] : [
      'Muharram', 'Safar', 'Rabi I', 'Rabi II', 'Jumada I', 'Jumada II',
      'Rajab', 'Shaban', 'Ramadan', 'Shawwal', 'Dhu al-Qidah', 'Dhu al-Hijjah'
    ]
  }
  
  return isRTL.value ? [
    'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
    'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
  ] : [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]
})

const dayHeaders = computed(() => {
  if (isRTL.value) {
    return ['س', 'أ', 'ث', 'ر', 'خ', 'ج', 'ح'] // Arabic day abbreviations
  }
  return ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']
})

// Generate calendar days
const calendarDays = computed((): CalendarDay[] => {
  const days: CalendarDay[] = []
  const year = currentDate.value.getFullYear()
  const month = currentDate.value.getMonth()
  
  // First day of the month
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  
  // Start from the beginning of the week
  const startDate = new Date(firstDay)
  startDate.setDate(firstDay.getDate() - firstDay.getDay())
  
  // Generate 42 days (6 weeks)
  for (let i = 0; i < 42; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    
    const isCurrentMonth = date.getMonth() === month
    const isToday = isSameDay(date, new Date())
    const selectedDate = parseDate(props.modelValue)
    const isSelected = selectedDate ? isSameDay(date, selectedDate) : false
    
    days.push({
      day: date.getDate(),
      month: date.getMonth(),
      year: date.getFullYear(),
      isCurrentMonth,
      isToday,
      isSelected,
      isDisabled: isDayDisabled({ day: date.getDate(), month: date.getMonth(), year: date.getFullYear(), date } as CalendarDay),
      date
    })
  }
  
  return days
})

// Utility functions
const isSameDay = (date1: Date, date2: Date): boolean => {
  return date1.getDate() === date2.getDate() &&
         date1.getMonth() === date2.getMonth() &&
         date1.getFullYear() === date2.getFullYear()
}

const isDayDisabled = (day: CalendarDay): boolean => {
  if (props.minDate) {
    const minDate = parseDate(props.minDate)
    if (minDate && day.date < minDate) return true
  }
  
  if (props.maxDate) {
    const maxDate = parseDate(props.maxDate)
    if (maxDate && day.date > maxDate) return true
  }
  
  if (props.disabledDates) {
    return props.disabledDates.some(disabledDate => {
      const disabled = parseDate(disabledDate)
      return disabled ? isSameDay(day.date, disabled) : false
    })
  }
  
  return false
}

// Formatting functions
const formatMonthYear = (date: Date): string => {
  const monthIndex = date.getMonth()
  const year = date.getFullYear()
  
  if (useHijriCalendar.value) {
    return `${monthNames.value[monthIndex]} ${year - 579}هـ`
  }
  
  return `${monthNames.value[monthIndex]} ${year}`
}

const formatDayAriaLabel = (day: CalendarDay): string => {
  const monthName = monthNames.value[day.month]
  return `${day.day} ${monthName} ${day.year}`
}

// Computed classes
const datePickerClasses = computed(() => [
  'uw-date-picker',
  `uw-date-picker--${props.size}`,
  {
    'uw-date-picker--disabled': props.disabled,
    'uw-date-picker--error': props.errorMessage,
    'uw-date-picker--open': isOpen.value,
    'uw-date-picker--rtl': isRTL,
  },
  props.class,
])

const labelClasses = computed(() => [
  'date-label',
  {
    'date-label--required': props.required,
    'date-label--disabled': props.disabled,
  }
])

const containerClasses = computed(() => [
  'date-container',
  {
    'date-container--disabled': props.disabled,
    'date-container--error': props.errorMessage,
    'date-container--open': isOpen.value,
  }
])

const calendarClasses = computed(() => [
  'date-calendar',
  {
    'date-calendar--rtl': isRTL,
    'date-calendar--hijri': useHijriCalendar.value,
  }
])

const helpClasses = computed(() => [
  'date-help',
  {
    'date-help--error': props.errorMessage,
  }
])

// Get dynamic classes
const getMonthClasses = (monthIndex: number) => [
  'month-option',
  {
    'month-option--selected': monthIndex === currentDate.value.getMonth(),
  }
]

const getDayClasses = (day: CalendarDay) => [
  'calendar-day',
  {
    'calendar-day--current-month': day.isCurrentMonth,
    'calendar-day--today': day.isToday,
    'calendar-day--selected': day.isSelected,
    'calendar-day--disabled': day.isDisabled,
  }
]

// Computed styles
const datePickerStyles = computed(() => {
  if (typeof props.style === 'object') return props.style
  return {}
})

const calendarStyles = ref<Record<string, string>>({})

// Methods
const toggleCalendar = (): void => {
  if (props.disabled || props.readonly) return
  
  if (isOpen.value) {
    closeCalendar()
  } else {
    openCalendar()
  }
}

const openCalendar = async (): Promise<void> => {
  isOpen.value = true
  showMonthPicker.value = false
  emit('open')
  
  await nextTick()
  setupPopper()
}

const closeCalendar = (): void => {
  isOpen.value = false
  showMonthPicker.value = false
  emit('close')
  
  if (popperInstance) {
    popperInstance.destroy()
    popperInstance = null
  }
}

const setupPopper = (): void => {
  if (!inputRef.value || !calendarRef.value) return
  
  popperInstance = createPopper(inputRef.value, calendarRef.value, {
    placement: isRTL.value ? 'bottom-end' : 'bottom-start',
    modifiers: [
      {
        name: 'offset',
        options: { offset: [0, 4] }
      },
      {
        name: 'preventOverflow',
        options: { padding: 8 }
      }
    ]
  })
}

const navigateMonth = (direction: number): void => {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(newDate.getMonth() + direction)
  currentDate.value = newDate
}

const navigateYear = (direction: number): void => {
  const newDate = new Date(currentDate.value)
  newDate.setFullYear(newDate.getFullYear() + direction)
  currentDate.value = newDate
}

const selectMonth = (monthIndex: number): void => {
  const newDate = new Date(currentDate.value)
  newDate.setMonth(monthIndex)
  currentDate.value = newDate
  showMonthPicker.value = false
}

const selectDate = (day: CalendarDay): void => {
  if (day.isDisabled) return
  
  const selectedDate = new Date(day.year, day.month, day.day)
  emit('update:modelValue', selectedDate)
  emit('change', selectedDate, formatDate(selectedDate, useHijriCalendar.value))
  closeCalendar()
}

const selectToday = (): void => {
  const today = new Date()
  currentDate.value = new Date(today)
  emit('update:modelValue', today)
  emit('change', today, formatDate(today, useHijriCalendar.value))
  closeCalendar()
}

const clearValue = (): void => {
  emit('update:modelValue', null)
  emit('change', null, '')
}

// Event handlers
const handleFocus = (event: FocusEvent): void => {
  emit('focus', event)
}

const handleBlur = (event: FocusEvent): void => {
  emit('blur', event)
}

const handleKeydown = (event: KeyboardEvent): void => {
  switch (event.key) {
    case 'Enter':
    case ' ':
      event.preventDefault()
      toggleCalendar()
      break
    case 'Escape':
      if (isOpen.value) {
        closeCalendar()
      }
      break
  }
}

const handleClickOutside = (event: Event): void => {
  const target = event.target as HTMLElement
  if (!calendarRef.value?.contains(target) && !inputRef.value?.contains(target)) {
    closeCalendar()
  }
}

// Watch for model value changes
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    const date = parseDate(newValue)
    if (date) {
      currentDate.value = new Date(date)
    }
  }
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
  name: 'UWDatePicker'
}
</script>

<style lang="scss" scoped>
.uw-date-picker {
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
.date-label {
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
.date-container {
  position: relative;
  display: flex;
  align-items: center;
  min-height: var(--input-height-md);
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

// Input styles
.date-input {
  flex: 1;
  padding: var(--spacing-2) var(--spacing-3);
  background: transparent;
  border: none;
  outline: none;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  cursor: pointer;
  
  &::placeholder {
    color: var(--color-text-placeholder);
  }
  
  &:disabled {
    cursor: not-allowed;
  }
}

// Icon and clear button
.date-icon,
.date-clear {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: var(--color-text-secondary);
}

.date-icon {
  margin-right: var(--spacing-3);
  
  .uw-date-picker--rtl & {
    margin-right: 0;
    margin-left: var(--spacing-3);
  }
}

.date-clear {
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  margin-right: var(--spacing-2);
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
  
  .uw-date-picker--rtl & {
    margin-right: 0;
    margin-left: var(--spacing-2);
  }
}

// Calendar styles
.date-calendar {
  z-index: 1000;
  min-width: 280px;
  background: var(--color-background-elevated);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  
  &--rtl {
    text-align: right;
  }
}

// Calendar header
.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-4);
  background: var(--color-background-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
}

.calendar-nav {
  display: flex;
  gap: var(--spacing-1);
}

.calendar-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
}

.calendar-title {
  flex: 1;
  text-align: center;
}

.calendar-month-btn {
  background: transparent;
  border: none;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  cursor: pointer;
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
  }
}

// Calendar toggle
.calendar-toggle {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

// Month picker
.month-picker {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-1);
  padding: var(--spacing-3);
}

.month-option {
  padding: var(--spacing-2);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
  }
  
  &--selected {
    background: var(--color-primary);
    color: var(--color-neutral-white);
  }
}

// Calendar grid
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: var(--color-border-subtle);
  margin: var(--spacing-3);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.calendar-header-row {
  display: contents;
}

.calendar-day-header {
  padding: var(--spacing-2);
  background: var(--color-background-subtle);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-align: center;
}

.calendar-day {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  background: var(--color-background-elevated);
  border: none;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover:not(&--disabled) {
    background: var(--color-background-hover);
    color: var(--color-text-primary);
  }
  
  &--current-month {
    color: var(--color-text-primary);
  }
  
  &--today {
    background: var(--color-primary-lighter);
    color: var(--color-primary-dark);
    font-weight: var(--font-weight-semibold);
  }
  
  &--selected {
    background: var(--color-primary);
    color: var(--color-neutral-white);
  }
  
  &--disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

// Calendar footer
.calendar-footer {
  padding: var(--spacing-3);
  border-top: 1px solid var(--color-border-subtle);
  text-align: center;
}

.calendar-today-btn {
  padding: var(--spacing-2) var(--spacing-4);
  background: transparent;
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: var(--transition-colors);
  
  &:hover {
    background: var(--color-background-hover);
    border-color: var(--color-primary);
  }
}

// Help text
.date-help {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  
  &--error {
    color: var(--color-error);
  }
}

// Size variants
.uw-date-picker--sm {
  .date-container {
    min-height: var(--input-height-sm);
  }
  
  .date-input {
    padding: var(--spacing-1-5) var(--spacing-2);
    font-size: var(--font-size-sm);
  }
}

.uw-date-picker--lg {
  .date-container {
    min-height: var(--input-height-lg);
  }
  
  .date-input {
    padding: var(--spacing-3) var(--spacing-4);
    font-size: var(--font-size-lg);
  }
}

// High contrast mode
[data-contrast="high"] {
  .date-container {
    border-width: 2px;
  }
  
  .calendar-day--selected {
    outline: 2px solid var(--color-background);
    outline-offset: 2px;
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .date-container,
  .calendar-nav-btn,
  .calendar-day {
    transition: none;
  }
}
</style>