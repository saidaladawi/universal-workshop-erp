/**
 * Component Registry - Universal Workshop Frontend V2
 * 
 * Central registry of all components for documentation and showcase system
 * with examples, props, and usage patterns.
 */

export interface ComponentExample {
  key: string
  title: string
  titleAr?: string
  description: string
  descriptionAr?: string
  code: string
  template: string
  props?: Record<string, any>
  showCode?: boolean
}

export interface ComponentProp {
  name: string
  type: string
  default?: any
  required?: boolean
  description: string
  descriptionAr?: string
  options?: string[]
}

export interface ComponentEvent {
  name: string
  description: string
  descriptionAr?: string
  payload?: string
}

export interface ComponentSlot {
  name: string
  description: string
  descriptionAr?: string
  props?: Record<string, any>
}

export interface ComponentInfo {
  name: string
  nameAr?: string
  description: string
  descriptionAr?: string
  icon: string
  badge?: string
  category: string
  component: any
  props: ComponentProp[]
  events: ComponentEvent[]
  slots: ComponentSlot[]
  examples: ComponentExample[]
  usage: string
  usageAr?: string
  notes?: string
  notesAr?: string
}

// Base Components
export const baseComponents: ComponentInfo[] = [
  {
    name: 'Button',
    nameAr: 'زر',
    description: 'Interactive button component with multiple variants and states',
    descriptionAr: 'مكون زر تفاعلي مع متغيرات وحالات متعددة',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="8" width="16" height="8" rx="2" fill="currentColor"/></svg>',
    category: 'base',
    component: null, // Would import actual component
    props: [
      {
        name: 'variant',
        type: 'string',
        default: 'primary',
        description: 'Button visual style',
        descriptionAr: 'نمط الزر البصري',
        options: ['primary', 'secondary', 'outline', 'ghost', 'danger']
      },
      {
        name: 'size',
        type: 'string',
        default: 'md',
        description: 'Button size',
        descriptionAr: 'حجم الزر',
        options: ['sm', 'md', 'lg', 'xl']
      },
      {
        name: 'loading',
        type: 'boolean',
        default: false,
        description: 'Show loading state with spinner',
        descriptionAr: 'إظهار حالة التحميل مع دوار'
      },
      {
        name: 'disabled',
        type: 'boolean',
        default: false,
        description: 'Disable button interaction',
        descriptionAr: 'تعطيل تفاعل الزر'
      },
      {
        name: 'fullWidth',
        type: 'boolean',
        default: false,
        description: 'Make button take full width',
        descriptionAr: 'جعل الزر يأخذ العرض الكامل'
      }
    ],
    events: [
      {
        name: 'click',
        description: 'Emitted when button is clicked',
        descriptionAr: 'يُرسل عند النقر على الزر',
        payload: 'MouseEvent'
      }
    ],
    slots: [
      {
        name: 'default',
        description: 'Button content',
        descriptionAr: 'محتوى الزر'
      }
    ],
    examples: [
      {
        key: 'variants',
        title: 'Button Variants',
        titleAr: 'متغيرات الزر',
        description: 'Different visual styles for various use cases',
        descriptionAr: 'أنماط بصرية مختلفة لحالات استخدام متنوعة',
        code: `<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="danger">Danger</Button>`,
        template: 'ButtonVariants'
      },
      {
        key: 'sizes',
        title: 'Button Sizes',
        titleAr: 'أحجام الزر',
        description: 'Various button sizes for different contexts',
        descriptionAr: 'أحجام أزرار متنوعة لسياقات مختلفة',
        code: `<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
<Button size="xl">Extra Large</Button>`,
        template: 'ButtonSizes'
      },
      {
        key: 'states',
        title: 'Button States',
        titleAr: 'حالات الزر',
        description: 'Loading and disabled states',
        descriptionAr: 'حالات التحميل والتعطيل',
        code: `<Button :loading="true">Loading</Button>
<Button :disabled="true">Disabled</Button>`,
        template: 'ButtonStates'
      }
    ],
    usage: 'Use buttons to trigger actions, submit forms, or navigate between pages.',
    usageAr: 'استخدم الأزرار لتنفيذ الإجراءات أو إرسال النماذج أو التنقل بين الصفحات.',
    notes: 'Always provide clear, action-oriented text for button labels.',
    notesAr: 'قدم دائماً نصوص واضحة وموجهة للإجراء في تسميات الأزرار.'
  },

  {
    name: 'Input',
    nameAr: 'حقل إدخال',
    description: 'Text input component with validation and various types',
    descriptionAr: 'مكون إدخال نص مع التحقق وأنواع متنوعة',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="8" width="18" height="8" rx="2" stroke="currentColor" fill="none"/></svg>',
    category: 'base',
    component: null,
    props: [
      {
        name: 'modelValue',
        type: 'string | number',
        description: 'Input value (v-model)',
        descriptionAr: 'قيمة الإدخال (v-model)',
        required: true
      },
      {
        name: 'type',
        type: 'string',
        default: 'text',
        description: 'Input type',
        descriptionAr: 'نوع الإدخال',
        options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search']
      },
      {
        name: 'placeholder',
        type: 'string',
        description: 'Placeholder text',
        descriptionAr: 'النص التوضيحي'
      },
      {
        name: 'error',
        type: 'boolean',
        default: false,
        description: 'Show error state',
        descriptionAr: 'إظهار حالة الخطأ'
      }
    ],
    events: [
      {
        name: 'update:modelValue',
        description: 'Emitted when value changes',
        descriptionAr: 'يُرسل عند تغيير القيمة',
        payload: 'string | number'
      }
    ],
    slots: [],
    examples: [
      {
        key: 'basic',
        title: 'Basic Input',
        titleAr: 'إدخال أساسي',
        description: 'Basic text input with placeholder',
        descriptionAr: 'إدخال نص أساسي مع نص توضيحي',
        code: `<Input v-model="value" placeholder="Enter text" />`,
        template: 'InputBasic'
      }
    ],
    usage: 'Use inputs to collect user data in forms.',
    usageAr: 'استخدم حقول الإدخال لجمع بيانات المستخدم في النماذج.'
  },

  {
    name: 'Card',
    nameAr: 'بطاقة',
    description: 'Content container with header, body, and footer sections',
    descriptionAr: 'حاوي محتوى مع أقسام رأس وجسم وذيل',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="6" width="16" height="12" rx="2" stroke="currentColor" fill="none"/></svg>',
    category: 'base',
    component: null,
    props: [
      {
        name: 'variant',
        type: 'string',
        default: 'elevated',
        description: 'Card visual style',
        descriptionAr: 'نمط البطاقة البصري',
        options: ['elevated', 'outlined', 'filled']
      }
    ],
    events: [],
    slots: [
      {
        name: 'header',
        description: 'Card header content',
        descriptionAr: 'محتوى رأس البطاقة'
      },
      {
        name: 'default',
        description: 'Card body content',
        descriptionAr: 'محتوى جسم البطاقة'
      },
      {
        name: 'footer',
        description: 'Card footer content',
        descriptionAr: 'محتوى ذيل البطاقة'
      }
    ],
    examples: [
      {
        key: 'basic',
        title: 'Basic Card',
        titleAr: 'بطاقة أساسية',
        description: 'Simple card with header and content',
        descriptionAr: 'بطاقة بسيطة مع رأس ومحتوى',
        code: `<Card>
  <template #header>
    <h3>Card Title</h3>
  </template>
  <p>Card content goes here.</p>
</Card>`,
        template: 'CardBasic'
      }
    ],
    usage: 'Use cards to group related content and actions.',
    usageAr: 'استخدم البطاقات لتجميع المحتوى والإجراءات ذات الصلة.'
  }
]

// Form Components
export const formComponents: ComponentInfo[] = [
  {
    name: 'Form',
    nameAr: 'نموذج',
    description: 'Form wrapper with validation context and submission handling',
    descriptionAr: 'غلاف نموذج مع سياق التحقق ومعالجة الإرسال',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" fill="none"/><path d="M8 8h8M8 12h8M8 16h4"/></svg>',
    category: 'forms',
    component: null,
    props: [
      {
        name: 'initialData',
        type: 'object',
        default: '{}',
        description: 'Initial form data',
        descriptionAr: 'بيانات النموذج الأولية'
      },
      {
        name: 'validationConfig',
        type: 'object',
        default: '{}',
        description: 'Validation configuration',
        descriptionAr: 'تكوين التحقق'
      }
    ],
    events: [
      {
        name: 'submit-valid',
        description: 'Emitted when form is submitted with valid data',
        descriptionAr: 'يُرسل عند إرسال النموذج ببيانات صحيحة',
        payload: 'object'
      }
    ],
    slots: [
      {
        name: 'default',
        description: 'Form content',
        descriptionAr: 'محتوى النموذج',
        props: {
          formData: 'object',
          isValid: 'boolean',
          validate: 'function'
        }
      }
    ],
    examples: [
      {
        key: 'validation',
        title: 'Form with Validation',
        titleAr: 'نموذج مع التحقق',
        description: 'Complete form with validation rules',
        descriptionAr: 'نموذج كامل مع قواعد التحقق',
        code: `<Form 
  :initial-data="formData" 
  :validation-config="validationConfig"
  @submit-valid="handleSubmit"
>
  <FormField name="email">
    <Input v-model="formData.email" type="email" />
  </FormField>
</Form>`,
        template: 'FormValidation'
      }
    ],
    usage: 'Use Form to wrap form fields and handle validation automatically.',
    usageAr: 'استخدم النموذج لتغليف حقول النموذج ومعالجة التحقق تلقائياً.'
  },

  {
    name: 'FormField',
    nameAr: 'حقل نموذج',
    description: 'Form field wrapper with automatic error display and validation',
    descriptionAr: 'غلاف حقل نموذج مع عرض الأخطاء والتحقق التلقائي',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="8" width="16" height="2" fill="currentColor"/><rect x="4" y="12" width="12" height="2" fill="currentColor"/></svg>',
    category: 'forms',
    component: null,
    props: [
      {
        name: 'name',
        type: 'string',
        required: true,
        description: 'Field name for validation',
        descriptionAr: 'اسم الحقل للتحقق'
      },
      {
        name: 'label',
        type: 'string',
        description: 'Field label',
        descriptionAr: 'تسمية الحقل'
      },
      {
        name: 'required',
        type: 'boolean',
        default: false,
        description: 'Field is required',
        descriptionAr: 'الحقل مطلوب'
      }
    ],
    events: [],
    slots: [
      {
        name: 'default',
        description: 'Field input component',
        descriptionAr: 'مكون إدخال الحقل',
        props: {
          fieldId: 'string',
          hasError: 'boolean',
          setValue: 'function'
        }
      }
    ],
    examples: [
      {
        key: 'basic',
        title: 'Basic Form Field',
        titleAr: 'حقل نموذج أساسي',
        description: 'Form field with validation integration',
        descriptionAr: 'حقل نموذج مع تكامل التحقق',
        code: `<FormField name="username" label="Username" required>
  <template #default="{ fieldId, setValue, hasError }">
    <Input 
      :id="fieldId" 
      :error="hasError"
      @update:model-value="setValue" 
    />
  </template>
</FormField>`,
        template: 'FormFieldBasic'
      }
    ],
    usage: 'Use FormField to automatically integrate inputs with form validation.',
    usageAr: 'استخدم حقل النموذج لتكامل الإدخالات تلقائياً مع تحقق النموذج.'
  }
]

// Layout Components
export const layoutComponents: ComponentInfo[] = [
  {
    name: 'Container',
    nameAr: 'حاوي',
    description: 'Responsive container for centering and constraining content width',
    descriptionAr: 'حاوي مرن لتوسيط وتقييد عرض المحتوى',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="2" y="6" width="20" height="12" rx="2" stroke="currentColor" fill="none"/></svg>',
    category: 'layout',
    component: null,
    props: [
      {
        name: 'size',
        type: 'string',
        default: 'lg',
        description: 'Container maximum width',
        descriptionAr: 'العرض الأقصى للحاوي',
        options: ['xs', 'sm', 'md', 'lg', 'xl', '2xl', 'full']
      }
    ],
    events: [],
    slots: [
      {
        name: 'default',
        description: 'Container content',
        descriptionAr: 'محتوى الحاوي'
      }
    ],
    examples: [
      {
        key: 'sizes',
        title: 'Container Sizes',
        titleAr: 'أحجام الحاوي',
        description: 'Different container sizes for various layouts',
        descriptionAr: 'أحجام حاوي مختلفة لتخطيطات متنوعة',
        code: `<Container size="sm">Small container</Container>
<Container size="lg">Large container</Container>
<Container size="full">Full width</Container>`,
        template: 'ContainerSizes'
      }
    ],
    usage: 'Use Container to create consistent page layouts with proper spacing.',
    usageAr: 'استخدم الحاوي لإنشاء تخطيطات صفحة متسقة مع تباعد مناسب.'
  },

  {
    name: 'Grid',
    nameAr: 'شبكة',
    description: 'CSS Grid-based layout component with responsive capabilities',
    descriptionAr: 'مكون تخطيط قائم على شبكة CSS مع قدرات مرونة',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="6" height="6" fill="currentColor"/><rect x="14" y="4" width="6" height="6" fill="currentColor"/><rect x="4" y="14" width="6" height="6" fill="currentColor"/><rect x="14" y="14" width="6" height="6" fill="currentColor"/></svg>',
    category: 'layout',
    component: null,
    props: [
      {
        name: 'cols',
        type: 'number | string',
        default: 'auto',
        description: 'Number of columns',
        descriptionAr: 'عدد الأعمدة'
      },
      {
        name: 'gap',
        type: 'string',
        default: 'md',
        description: 'Gap between grid items',
        descriptionAr: 'الفراغ بين عناصر الشبكة',
        options: ['none', 'xs', 'sm', 'md', 'lg', 'xl', '2xl']
      }
    ],
    events: [],
    slots: [
      {
        name: 'default',
        description: 'Grid content',
        descriptionAr: 'محتوى الشبكة'
      }
    ],
    examples: [
      {
        key: 'basic',
        title: 'Basic Grid',
        titleAr: 'شبكة أساسية',
        description: 'Simple grid layout with equal columns',
        descriptionAr: 'تخطيط شبكة بسيط مع أعمدة متساوية',
        code: `<Grid cols="3" gap="md">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Grid>`,
        template: 'GridBasic'
      }
    ],
    usage: 'Use Grid for complex layouts that require precise control over positioning.',
    usageAr: 'استخدم الشبكة للتخطيطات المعقدة التي تتطلب تحكماً دقيقاً في المواضع.'
  }
]

// Navigation Components
export const navigationComponents: ComponentInfo[] = [
  {
    name: 'Breadcrumb',
    nameAr: 'مسار التنقل',
    description: 'Navigation breadcrumb showing current page location in hierarchy',
    descriptionAr: 'مسار تنقل يُظهر موقع الصفحة الحالية في التسلسل الهرمي',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 6l6 6-6 6"/></svg>',
    category: 'navigation',
    component: null,
    props: [
      {
        name: 'items',
        type: 'array',
        required: true,
        description: 'Breadcrumb items array',
        descriptionAr: 'مصفوفة عناصر مسار التنقل'
      }
    ],
    events: [],
    slots: [],
    examples: [],
    usage: 'Use Breadcrumb to help users understand their current location.',
    usageAr: 'استخدم مسار التنقل لمساعدة المستخدمين على فهم موقعهم الحالي.'
  }
]

// Feedback Components
export const feedbackComponents: ComponentInfo[] = [
  {
    name: 'Alert',
    nameAr: 'تنبيه',
    description: 'Static alert component for displaying important messages',
    descriptionAr: 'مكون تنبيه ثابت لعرض الرسائل المهمة',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>',
    category: 'feedback',
    component: null,
    props: [
      {
        name: 'variant',
        type: 'string',
        default: 'info',
        description: 'Alert type',
        descriptionAr: 'نوع التنبيه',
        options: ['info', 'success', 'warning', 'error']
      }
    ],
    events: [],
    slots: [],
    examples: [],
    usage: 'Use Alert to communicate important information to users.',
    usageAr: 'استخدم التنبيه لتوصيل المعلومات المهمة للمستخدمين.'
  }
]

// Arabic/RTL Components
export const arabicComponents: ComponentInfo[] = [
  {
    name: 'ArabicInput',
    nameAr: 'إدخال عربي',
    description: 'Specialized input for Arabic text with direction detection',
    descriptionAr: 'إدخال متخصص للنص العربي مع كشف الاتجاه',
    icon: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>',
    badge: 'RTL',
    category: 'arabic',
    component: null,
    props: [
      {
        name: 'autoDirection',
        type: 'boolean',
        default: true,
        description: 'Auto-detect text direction',
        descriptionAr: 'كشف اتجاه النص تلقائياً'
      },
      {
        name: 'useArabicNumerals',
        type: 'boolean',
        default: true,
        description: 'Use Arabic numerals for numbers',
        descriptionAr: 'استخدام الأرقام العربية للأرقام'
      }
    ],
    events: [],
    slots: [],
    examples: [],
    usage: 'Use ArabicInput for forms that need to handle Arabic text properly.',
    usageAr: 'استخدم الإدخال العربي للنماذج التي تحتاج لمعالجة النص العربي بشكل صحيح.'
  }
]

// Main component registry
export const componentRegistry: Record<string, ComponentInfo[]> = {
  base: baseComponents,
  forms: formComponents,
  layout: layoutComponents,
  navigation: navigationComponents,
  feedback: feedbackComponents,
  arabic: arabicComponents,
}

// Flat list of all components
export const allComponents = Object.values(componentRegistry).flat()

export default componentRegistry