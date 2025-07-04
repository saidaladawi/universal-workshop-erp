/**
 * Documentation System - Universal Workshop Frontend V2
 * 
 * Complete documentation and showcase system for all components
 * with interactive examples and Arabic/RTL support.
 */

// Import main components
import ComponentShowcase from './ComponentShowcase.vue'
import ComponentDocumentation from './ComponentDocumentation.vue'
import ExampleRenderer from './ExampleRenderer.vue'

// Import registry and types
export { componentRegistry, allComponents } from './component-registry'
export type { 
  ComponentInfo, 
  ComponentExample, 
  ComponentProp, 
  ComponentEvent, 
  ComponentSlot 
} from './component-registry'

// Export main components
export { 
  ComponentShowcase, 
  ComponentDocumentation, 
  ExampleRenderer 
}

// Documentation utilities
export const createDocumentationApp = (app: any) => {
  // Register documentation components globally
  app.component('ComponentShowcase', ComponentShowcase)
  app.component('ComponentDocumentation', ComponentDocumentation)
  app.component('ExampleRenderer', ExampleRenderer)
  
  return app
}

// Generate component documentation data
export const getComponentDocumentation = (componentName: string) => {
  return allComponents.find(comp => comp.name === componentName)
}

// Search components by category
export const getComponentsByCategory = (category: string) => {
  return componentRegistry[category] || []
}

// Search components by name or description
export const searchComponents = (query: string, preferArabic = false) => {
  const searchTerm = query.toLowerCase()
  
  return allComponents.filter(component => {
    const name = component.name.toLowerCase()
    const nameAr = component.nameAr?.toLowerCase() || ''
    const description = component.description.toLowerCase()
    const descriptionAr = component.descriptionAr?.toLowerCase() || ''
    
    if (preferArabic) {
      return nameAr.includes(searchTerm) || 
             descriptionAr.includes(searchTerm) ||
             name.includes(searchTerm) ||
             description.includes(searchTerm)
    }
    
    return name.includes(searchTerm) || 
           description.includes(searchTerm) ||
           nameAr.includes(searchTerm) ||
           descriptionAr.includes(searchTerm)
  })
}

// Get component usage statistics
export const getComponentStats = () => {
  const stats = {
    totalComponents: allComponents.length,
    componentsByCategory: Object.keys(componentRegistry).map(category => ({
      category,
      count: componentRegistry[category].length,
      components: componentRegistry[category].map(comp => comp.name)
    })),
    componentsWithExamples: allComponents.filter(comp => comp.examples.length > 0).length,
    totalExamples: allComponents.reduce((total, comp) => total + comp.examples.length, 0),
    arabicSupport: allComponents.filter(comp => comp.nameAr || comp.descriptionAr).length
  }
  
  return stats
}

// Documentation configuration
export const documentationConfig = {
  title: 'Universal Workshop Components',
  titleAr: 'مكونات الورشة الشاملة',
  description: 'Comprehensive component library for Universal Workshop ERP',
  descriptionAr: 'مكتبة مكونات شاملة لنظام إدارة الورشة الشاملة',
  version: '2.0.0',
  categories: [
    {
      key: 'base',
      name: 'Base Components',
      nameAr: 'المكونات الأساسية',
      description: 'Fundamental UI components like buttons, inputs, and cards',
      descriptionAr: 'مكونات واجهة المستخدم الأساسية مثل الأزرار وحقول الإدخال والبطاقات'
    },
    {
      key: 'forms',
      name: 'Form Components',
      nameAr: 'مكونات النماذج',
      description: 'Form handling and validation components',
      descriptionAr: 'مكونات معالجة النماذج والتحقق من صحة البيانات'
    },
    {
      key: 'layout',
      name: 'Layout Components',
      nameAr: 'مكونات التخطيط',
      description: 'Layout and positioning components',
      descriptionAr: 'مكونات التخطيط وتنسيق المواضع'
    },
    {
      key: 'navigation',
      name: 'Navigation',
      nameAr: 'التنقل',
      description: 'Navigation and routing components',
      descriptionAr: 'مكونات التنقل والتوجيه'
    },
    {
      key: 'feedback',
      name: 'Feedback',
      nameAr: 'التفاعل',
      description: 'User feedback and notification components',
      descriptionAr: 'مكونات ردود الفعل والإشعارات للمستخدم'
    },
    {
      key: 'arabic',
      name: 'Arabic/RTL',
      nameAr: 'العربية/RTL',
      description: 'Specialized Arabic and RTL components',
      descriptionAr: 'مكونات متخصصة للعربية والتخطيط من اليمين لليسار'
    }
  ],
  features: [
    {
      name: 'Arabic/RTL Support',
      nameAr: 'دعم العربية/RTL',
      description: 'Complete right-to-left language support',
      descriptionAr: 'دعم كامل للغات التي تُكتب من اليمين إلى اليسار'
    },
    {
      name: 'Vue 3 Composition API',
      nameAr: 'Vue 3 Composition API',
      description: 'Built with modern Vue 3 and TypeScript',
      descriptionAr: 'مبني بـ Vue 3 الحديث و TypeScript'
    },
    {
      name: 'Design System',
      nameAr: 'نظام التصميم',
      description: 'Consistent design tokens and theming',
      descriptionAr: 'رموز تصميم متسقة ونظام الألوان'
    },
    {
      name: 'Accessibility',
      nameAr: 'إمكانية الوصول',
      description: 'WCAG compliant with screen reader support',
      descriptionAr: 'متوافق مع WCAG ودعم قارئات الشاشة'
    }
  ]
}

export default {
  ComponentShowcase,
  ComponentDocumentation,
  ExampleRenderer,
  componentRegistry,
  allComponents,
  createDocumentationApp,
  getComponentDocumentation,
  getComponentsByCategory,
  searchComponents,
  getComponentStats,
  documentationConfig
}