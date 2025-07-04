/**
 * Universal Workshop Component Library - Main Export
 * 
 * Comprehensive Vue 3 component library with Arabic/RTL support,
 * accessibility features, and Frappe ERP integration.
 */

// Export all component categories
export * from './primitives'
export * from './base'
export * from './forms'
export * from './layout'
export * from './navigation'
export * from './feedback'
export * from './arabic'

// Export showcase and documentation
export { default as ComponentShowcase } from './ComponentShowcase.vue'

// Export component registries for plugins
export { formComponents, installFormComponents } from './forms'

// Main installation function
export function installUniversalWorkshopComponents(app: any) {
  // Install form components
  installFormComponents(app)
  
  // Add other component installation functions here as they're created
}

// Component library metadata
export const componentLibraryInfo = {
  name: 'Universal Workshop Component Library',
  version: '2.0.0',
  description: 'Production-ready Vue 3 components for automotive workshop management',
  features: [
    'Arabic/RTL Support',
    'Accessibility (WCAG 2.1 AA)',
    'TypeScript Support',
    'Dark Mode',
    'Responsive Design',
    'Offline Support',
    'Frappe ERP Integration'
  ],
  components: {
    primitives: ['Icon', 'Badge', 'Avatar'],
    base: ['Button', 'Input', 'Card'],
    forms: ['Form', 'FormField', 'Select'],
    layout: ['Container', 'Grid', 'Stack'],
    navigation: ['Breadcrumb', 'Sidebar', 'Tabs'],
    feedback: ['Alert', 'Modal', 'Notification', 'Toast'],
    arabic: ['ArabicInput']
  }
}

export default {
  install: installUniversalWorkshopComponents,
  ...componentLibraryInfo
}