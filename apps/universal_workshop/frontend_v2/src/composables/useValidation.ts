/**
 * Form Validation Composable - Universal Workshop Frontend V2
 * 
 * A comprehensive validation system with Arabic/English error messages,
 * real-time validation, and integration with form components.
 */

import { computed, reactive, ref, watch } from 'vue'

// Validation rule function type
export type ValidationRuleFn = (value: any, formData?: Record<string, any>, ...params: any[]) => boolean | string | Promise<boolean | string>

// Built-in validation rule
export interface ValidationRule {
  name: string
  message: string
  messageAr?: string
  validator: ValidationRuleFn
}

// Field validation configuration
export interface FieldValidation {
  rules: (ValidationRule | string)[]
  validateOn?: 'blur' | 'input' | 'submit' | 'manual'
  debounceMs?: number
  required?: boolean
  label?: string
  labelAr?: string
}

// Form validation configuration
export interface FormValidationConfig {
  [fieldName: string]: FieldValidation
}

// Validation result
export interface ValidationResult {
  isValid: boolean
  errors: string[]
  errorsAr: string[]
  firstError?: string
  firstErrorAr?: string
}

// Field state
export interface FieldState {
  value: any
  touched: boolean
  dirty: boolean
  validating: boolean
  errors: string[]
  errorsAr: string[]
  isValid: boolean
}

// Form state
export interface FormState {
  fields: Record<string, FieldState>
  isValid: boolean
  isValidating: boolean
  hasErrors: boolean
  isDirty: boolean
  touchedFields: string[]
  dirtyFields: string[]
}

// Built-in validation rules
const builtInRules: Record<string, ValidationRule> = {
  required: {
    name: 'required',
    message: 'This field is required',
    messageAr: 'هذا الحقل مطلوب',
    validator: (value: any) => {
      if (value === null || value === undefined) return false
      if (typeof value === 'string') return value.trim().length > 0
      if (Array.isArray(value)) return value.length > 0
      if (typeof value === 'object') return Object.keys(value).length > 0
      return Boolean(value)
    }
  },

  email: {
    name: 'email',
    message: 'Please enter a valid email address',
    messageAr: 'يرجى إدخال عنوان بريد إلكتروني صحيح',
    validator: (value: string) => {
      if (!value) return true // Let required rule handle empty values
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(value)
    }
  },

  minLength: {
    name: 'minLength',
    message: 'Must be at least {min} characters',
    messageAr: 'يجب أن يكون على الأقل {min} حروف',
    validator: (value: string, _formData: any, min: number) => {
      if (!value) return true
      return value.length >= min
    }
  },

  maxLength: {
    name: 'maxLength',
    message: 'Must be no more than {max} characters',
    messageAr: 'يجب أن لا يتجاوز {max} حروف',
    validator: (value: string, _formData: any, max: number) => {
      if (!value) return true
      return value.length <= max
    }
  },

  min: {
    name: 'min',
    message: 'Must be at least {min}',
    messageAr: 'يجب أن يكون على الأقل {min}',
    validator: (value: number, _formData: any, min: number) => {
      if (value === null || value === undefined) return true
      return Number(value) >= min
    }
  },

  max: {
    name: 'max',
    message: 'Must be no more than {max}',
    messageAr: 'يجب أن لا يتجاوز {max}',
    validator: (value: number, _formData: any, max: number) => {
      if (value === null || value === undefined) return true
      return Number(value) <= max
    }
  },

  pattern: {
    name: 'pattern',
    message: 'Invalid format',
    messageAr: 'تنسيق غير صحيح',
    validator: (value: string, _formData: any, pattern: RegExp | string) => {
      if (!value) return true
      const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern
      return regex.test(value)
    }
  },

  url: {
    name: 'url',
    message: 'Please enter a valid URL',
    messageAr: 'يرجى إدخال رابط صحيح',
    validator: (value: string) => {
      if (!value) return true
      try {
        new URL(value)
        return true
      } catch {
        return false
      }
    }
  },

  phone: {
    name: 'phone',
    message: 'Please enter a valid phone number',
    messageAr: 'يرجى إدخال رقم هاتف صحيح',
    validator: (value: string) => {
      if (!value) return true
      // Basic international phone number validation
      const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/
      return phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))
    }
  },

  arabicText: {
    name: 'arabicText',
    message: 'Must contain Arabic text',
    messageAr: 'يجب أن يحتوي على نص عربي',
    validator: (value: string) => {
      if (!value) return true
      const arabicRegex = /[\u0600-\u06FF]/
      return arabicRegex.test(value)
    }
  },

  englishText: {
    name: 'englishText',
    message: 'Must contain English text',
    messageAr: 'يجب أن يحتوي على نص إنجليزي',
    validator: (value: string) => {
      if (!value) return true
      const englishRegex = /[a-zA-Z]/
      return englishRegex.test(value)
    }
  },

  numeric: {
    name: 'numeric',
    message: 'Must be a valid number',
    messageAr: 'يجب أن يكون رقماً صحيحاً',
    validator: (value: any) => {
      if (value === null || value === undefined || value === '') return true
      return !isNaN(Number(value))
    }
  },

  integer: {
    name: 'integer',
    message: 'Must be a whole number',
    messageAr: 'يجب أن يكون رقماً صحيحاً',
    validator: (value: any) => {
      if (value === null || value === undefined || value === '') return true
      const num = Number(value)
      return !isNaN(num) && Number.isInteger(num)
    }
  },

  positive: {
    name: 'positive',
    message: 'Must be a positive number',
    messageAr: 'يجب أن يكون رقماً موجباً',
    validator: (value: any) => {
      if (value === null || value === undefined || value === '') return true
      return Number(value) > 0
    }
  },

  dateAfter: {
    name: 'dateAfter',
    message: 'Date must be after {date}',
    messageAr: 'يجب أن يكون التاريخ بعد {date}',
    validator: (value: string, _formData: any, afterDate: string | Date) => {
      if (!value) return true
      const inputDate = new Date(value)
      const compareDate = new Date(afterDate)
      return inputDate > compareDate
    }
  },

  dateBefore: {
    name: 'dateBefore',
    message: 'Date must be before {date}',
    messageAr: 'يجب أن يكون التاريخ قبل {date}',
    validator: (value: string, _formData: any, beforeDate: string | Date) => {
      if (!value) return true
      const inputDate = new Date(value)
      const compareDate = new Date(beforeDate)
      return inputDate < compareDate
    }
  },

  sameAs: {
    name: 'sameAs',
    message: 'Must match {field}',
    messageAr: 'يجب أن يطابق {field}',
    validator: (value: any, formData: any, fieldName: string) => {
      if (!formData) return true
      return value === formData[fieldName]
    }
  }
}

// Create validation rule with parameters
export function createRule(
  ruleName: string,
  params: Record<string, any> = {},
  customMessage?: string,
  customMessageAr?: string
): ValidationRule {
  const baseRule = builtInRules[ruleName]
  if (!baseRule) {
    throw new Error(`Unknown validation rule: ${ruleName}`)
  }

  // Replace placeholders in messages
  const replacePlaceholders = (message: string) => {
    return Object.entries(params).reduce((msg, [key, value]) => {
      return msg.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value))
    }, message)
  }

  return {
    ...baseRule,
    message: customMessage || replacePlaceholders(baseRule.message),
    messageAr: customMessageAr || (baseRule.messageAr ? replacePlaceholders(baseRule.messageAr) : undefined),
    validator: (value: any, formData?: Record<string, any>) => {
      const paramValues = Object.values(params)
      return baseRule.validator(value, formData, ...paramValues)
    }
  }
}

// Main validation composable
export function useValidation(
  initialData: Record<string, any> = {},
  validationConfig: FormValidationConfig = {},
  options: {
    preferArabic?: boolean
    validateOnMount?: boolean
    stopOnFirstError?: boolean
  } = {}
) {
  const { preferArabic = true, validateOnMount = false, stopOnFirstError = false } = options

  // Form data
  const formData = reactive({ ...initialData })

  // Form state
  const formState = reactive<FormState>({
    fields: {},
    isValid: true,
    isValidating: false,
    hasErrors: false,
    isDirty: false,
    touchedFields: [],
    dirtyFields: []
  })

  // Validation timeouts for debouncing
  const validationTimeouts = ref<Record<string, number>>({})

  // Initialize field states
  const initializeField = (fieldName: string) => {
    if (!formState.fields[fieldName]) {
      formState.fields[fieldName] = {
        value: formData[fieldName],
        touched: false,
        dirty: false,
        validating: false,
        errors: [],
        errorsAr: [],
        isValid: true
      }
    }
  }

  // Validate a single field
  const validateField = async (fieldName: string): Promise<ValidationResult> => {
    const config = validationConfig[fieldName]
    if (!config) {
      return { isValid: true, errors: [], errorsAr: [] }
    }

    initializeField(fieldName)
    const fieldState = formState.fields[fieldName]
    fieldState.validating = true

    const errors: string[] = []
    const errorsAr: string[] = []
    const value = formData[fieldName]

    // Check required first if configured
    if (config.required && !builtInRules.required.validator(value)) {
      errors.push(builtInRules.required.message)
      if (builtInRules.required.messageAr) {
        errorsAr.push(builtInRules.required.messageAr)
      }
      
      if (stopOnFirstError) {
        fieldState.validating = false
        fieldState.errors = errors
        fieldState.errorsAr = errorsAr
        fieldState.isValid = false
        return { isValid: false, errors, errorsAr, firstError: errors[0], firstErrorAr: errorsAr[0] }
      }
    }

    // Validate each rule
    for (const ruleConfig of config.rules) {
      let rule: ValidationRule

      if (typeof ruleConfig === 'string') {
        rule = builtInRules[ruleConfig]
        if (!rule) {
          console.warn(`Unknown validation rule: ${ruleConfig}`)
          continue
        }
      } else {
        rule = ruleConfig
      }

      try {
        const result = await rule.validator(value, formData)
        
        if (result !== true) {
          const errorMessage = typeof result === 'string' ? result : rule.message
          errors.push(errorMessage)
          
          if (rule.messageAr) {
            const errorMessageAr = typeof result === 'string' && rule.messageAr ? rule.messageAr : rule.messageAr
            errorsAr.push(errorMessageAr)
          }

          if (stopOnFirstError) break
        }
      } catch (error) {
        console.error(`Validation error for field ${fieldName}:`, error)
        errors.push('Validation error')
        errorsAr.push('خطأ في التحقق')
      }
    }

    fieldState.validating = false
    fieldState.errors = errors
    fieldState.errorsAr = errorsAr
    fieldState.isValid = errors.length === 0

    return {
      isValid: errors.length === 0,
      errors,
      errorsAr,
      firstError: errors[0],
      firstErrorAr: errorsAr[0]
    }
  }

  // Validate all fields
  const validateForm = async (): Promise<ValidationResult> => {
    formState.isValidating = true

    const allErrors: string[] = []
    const allErrorsAr: string[] = []

    const fieldNames = Object.keys(validationConfig)
    const validationPromises = fieldNames.map(fieldName => validateField(fieldName))
    
    try {
      const results = await Promise.all(validationPromises)
      
      results.forEach(result => {
        allErrors.push(...result.errors)
        allErrorsAr.push(...result.errorsAr)
      })

      const isValid = allErrors.length === 0
      formState.isValid = isValid
      formState.hasErrors = !isValid

    } finally {
      formState.isValidating = false
    }

    return {
      isValid: formState.isValid,
      errors: allErrors,
      errorsAr: allErrorsAr,
      firstError: allErrors[0],
      firstErrorAr: allErrorsAr[0]
    }
  }

  // Set field value with validation
  const setFieldValue = (fieldName: string, value: any, shouldValidate = true) => {
    initializeField(fieldName)
    
    const fieldState = formState.fields[fieldName]
    const oldValue = formData[fieldName]
    
    formData[fieldName] = value
    fieldState.value = value
    
    // Update dirty state
    if (!fieldState.dirty && value !== oldValue) {
      fieldState.dirty = true
      if (!formState.dirtyFields.includes(fieldName)) {
        formState.dirtyFields.push(fieldName)
      }
      formState.isDirty = true
    }

    // Validate if needed
    if (shouldValidate) {
      const config = validationConfig[fieldName]
      if (config?.validateOn === 'input') {
        scheduleValidation(fieldName, config.debounceMs || 300)
      }
    }
  }

  // Touch field (mark as interacted with)
  const touchField = (fieldName: string, shouldValidate = true) => {
    initializeField(fieldName)
    
    const fieldState = formState.fields[fieldName]
    if (!fieldState.touched) {
      fieldState.touched = true
      if (!formState.touchedFields.includes(fieldName)) {
        formState.touchedFields.push(fieldName)
      }
    }

    // Validate if needed
    if (shouldValidate) {
      const config = validationConfig[fieldName]
      if (config?.validateOn === 'blur') {
        validateField(fieldName)
      }
    }
  }

  // Schedule validation with debouncing
  const scheduleValidation = (fieldName: string, debounceMs = 300) => {
    // Clear existing timeout
    if (validationTimeouts.value[fieldName]) {
      clearTimeout(validationTimeouts.value[fieldName])
    }

    // Schedule new validation
    validationTimeouts.value[fieldName] = window.setTimeout(() => {
      validateField(fieldName)
      delete validationTimeouts.value[fieldName]
    }, debounceMs)
  }

  // Get field error message (localized)
  const getFieldError = (fieldName: string): string => {
    const fieldState = formState.fields[fieldName]
    if (!fieldState || !fieldState.errors.length) return ''
    
    if (preferArabic && fieldState.errorsAr.length > 0) {
      return fieldState.errorsAr[0]
    }
    return fieldState.errors[0]
  }

  // Get all field errors (localized)
  const getFieldErrors = (fieldName: string): string[] => {
    const fieldState = formState.fields[fieldName]
    if (!fieldState) return []
    
    if (preferArabic && fieldState.errorsAr.length > 0) {
      return fieldState.errorsAr
    }
    return fieldState.errors
  }

  // Reset field
  const resetField = (fieldName: string) => {
    if (formState.fields[fieldName]) {
      const initialValue = initialData[fieldName]
      formData[fieldName] = initialValue
      formState.fields[fieldName] = {
        value: initialValue,
        touched: false,
        dirty: false,
        validating: false,
        errors: [],
        errorsAr: [],
        isValid: true
      }
    }

    // Remove from touched and dirty arrays
    const touchedIndex = formState.touchedFields.indexOf(fieldName)
    if (touchedIndex > -1) {
      formState.touchedFields.splice(touchedIndex, 1)
    }

    const dirtyIndex = formState.dirtyFields.indexOf(fieldName)
    if (dirtyIndex > -1) {
      formState.dirtyFields.splice(dirtyIndex, 1)
    }

    // Update form state
    formState.isDirty = formState.dirtyFields.length > 0
  }

  // Reset form
  const resetForm = () => {
    Object.keys(formData).forEach(key => {
      formData[key] = initialData[key]
    })

    formState.fields = {}
    formState.isValid = true
    formState.isValidating = false
    formState.hasErrors = false
    formState.isDirty = false
    formState.touchedFields = []
    formState.dirtyFields = []

    // Clear any pending validations
    Object.values(validationTimeouts.value).forEach(timeout => clearTimeout(timeout))
    validationTimeouts.value = {}
  }

  // Watch for field changes
  Object.keys(validationConfig).forEach(fieldName => {
    initializeField(fieldName)
    
    watch(
      () => formData[fieldName],
      (newValue, oldValue) => {
        if (newValue !== oldValue) {
          setFieldValue(fieldName, newValue, false) // Don't double-validate
        }
      }
    )
  })

  // Validate on mount if requested
  if (validateOnMount) {
    validateForm()
  }

  // Computed properties
  const isFormValid = computed(() => formState.isValid)
  const isFormValidating = computed(() => formState.isValidating)
  const hasFormErrors = computed(() => formState.hasErrors)
  const isFormDirty = computed(() => formState.isDirty)

  return {
    // Form data
    formData,
    formState,

    // Computed states
    isFormValid,
    isFormValidating,
    hasFormErrors,
    isFormDirty,

    // Field methods
    setFieldValue,
    touchField,
    resetField,
    getFieldError,
    getFieldErrors,

    // Form methods
    validateField,
    validateForm,
    resetForm,

    // Utilities
    createRule,
    builtInRules
  }
}