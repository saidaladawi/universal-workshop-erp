/**
 * Form Components - Universal Workshop Frontend V2
 * 
 * Form components and validation system with comprehensive Arabic/RTL support
 * and integration with the Universal Workshop ERP validation requirements.
 */

// Import components
import Form from './Form.vue'
import FormField from './FormField.vue'

// Import advanced form components
export * from './Select'
export * from './Checkbox'
export * from './RadioGroup'
export * from './Switch'
export * from './DatePicker'
export * from './FileUpload'

// Import composables and utilities
export { useValidation, createRule } from '@/composables/useValidation'
export { validationSchemas } from '@/validation/schemas'

// Export components
export { Form, FormField }

// Export component types
export type { FormProps } from './Form.vue'
export type { FormFieldProps } from './FormField.vue'

// Export validation types
export type {
  ValidationRule,
  ValidationRuleFn,
  FieldValidation,
  FormValidationConfig,
  ValidationResult,
  FieldState,
  FormState
} from '@/composables/useValidation'

// Component registry for global registration
export const formComponents = {
  UWForm: Form,
  UWFormField: FormField,
} as const

// Install function for Vue plugin
export function installFormComponents(app: any) {
  Object.entries(formComponents).forEach(([name, component]) => {
    app.component(name, component)
  })
}

export default {
  Form,
  FormField,
  install: installFormComponents,
}