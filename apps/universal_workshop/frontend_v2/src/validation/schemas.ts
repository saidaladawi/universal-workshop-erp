/**
 * Validation Schemas - Universal Workshop Frontend V2
 * 
 * Pre-defined validation schemas for common form patterns in the
 * Universal Workshop ERP system with Arabic/English error messages.
 */

import { createRule, type FormValidationConfig } from '@/composables/useValidation'

// User Registration Schema
export const userRegistrationSchema: FormValidationConfig = {
  firstName: {
    rules: ['required', createRule('minLength', { min: 2 })],
    validateOn: 'blur',
    required: true,
    label: 'First Name',
    labelAr: 'الاسم الأول'
  },
  
  lastName: {
    rules: ['required', createRule('minLength', { min: 2 })],
    validateOn: 'blur',
    required: true,
    label: 'Last Name',
    labelAr: 'اسم العائلة'
  },
  
  firstNameAr: {
    rules: ['arabicText', createRule('minLength', { min: 2 })],
    validateOn: 'blur',
    label: 'First Name (Arabic)',
    labelAr: 'الاسم الأول (عربي)'
  },
  
  lastNameAr: {
    rules: ['arabicText', createRule('minLength', { min: 2 })],
    validateOn: 'blur',
    label: 'Last Name (Arabic)',
    labelAr: 'اسم العائلة (عربي)'
  },
  
  email: {
    rules: ['required', 'email'],
    validateOn: 'blur',
    required: true,
    label: 'Email Address',
    labelAr: 'عنوان البريد الإلكتروني'
  },
  
  phone: {
    rules: ['required', 'phone'],
    validateOn: 'blur',
    required: true,
    label: 'Phone Number',
    labelAr: 'رقم الهاتف'
  },
  
  password: {
    rules: [
      'required',
      createRule('minLength', { min: 8 }),
      createRule('pattern', { 
        pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
      }, 'Password must contain uppercase, lowercase, number and special character', 
         'كلمة المرور يجب أن تحتوي على حروف كبيرة وصغيرة ورقم ورمز خاص')
    ],
    validateOn: 'input',
    debounceMs: 500,
    required: true,
    label: 'Password',
    labelAr: 'كلمة المرور'
  },
  
  confirmPassword: {
    rules: [
      'required',
      createRule('sameAs', { field: 'password' }, 'Passwords must match', 'كلمات المرور غير متطابقة')
    ],
    validateOn: 'blur',
    required: true,
    label: 'Confirm Password',
    labelAr: 'تأكيد كلمة المرور'
  }
}

// Vehicle Registration Schema
export const vehicleRegistrationSchema: FormValidationConfig = {
  vin: {
    rules: [
      'required',
      createRule('pattern', { 
        pattern: /^[A-HJ-NPR-Z0-9]{17}$/,
      }, 'VIN must be 17 characters with no I, O, or Q', 
         'رقم الهيكل يجب أن يكون 17 حرف بدون I, O, أو Q')
    ],
    validateOn: 'blur',
    required: true,
    label: 'VIN Number',
    labelAr: 'رقم الهيكل'
  },
  
  plateNumber: {
    rules: [
      'required',
      createRule('pattern', { 
        pattern: /^[A-Z0-9]{1,8}$/,
      }, 'Plate number must be alphanumeric', 'رقم اللوحة يجب أن يكون أرقام وحروف فقط')
    ],
    validateOn: 'blur',
    required: true,
    label: 'Plate Number',
    labelAr: 'رقم اللوحة'
  },
  
  make: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Make',
    labelAr: 'الماركة'
  },
  
  model: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Model',
    labelAr: 'الموديل'
  },
  
  year: {
    rules: [
      'required',
      'integer',
      createRule('min', { min: 1900 }),
      createRule('max', { max: new Date().getFullYear() + 1 })
    ],
    validateOn: 'blur',
    required: true,
    label: 'Year',
    labelAr: 'السنة'
  },
  
  mileage: {
    rules: [
      'required',
      'numeric',
      'positive',
      createRule('max', { max: 999999 })
    ],
    validateOn: 'input',
    debounceMs: 500,
    required: true,
    label: 'Mileage (KM)',
    labelAr: 'المسافة المقطوعة (كم)'
  }
}

// Service Order Schema
export const serviceOrderSchema: FormValidationConfig = {
  customerId: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Customer',
    labelAr: 'العميل'
  },
  
  vehicleId: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Vehicle',
    labelAr: 'المركبة'
  },
  
  serviceType: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Service Type',
    labelAr: 'نوع الخدمة'
  },
  
  description: {
    rules: [
      'required',
      createRule('minLength', { min: 10 }),
      createRule('maxLength', { max: 1000 })
    ],
    validateOn: 'input',
    debounceMs: 1000,
    required: true,
    label: 'Service Description',
    labelAr: 'وصف الخدمة'
  },
  
  priority: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Priority',
    labelAr: 'الأولوية'
  },
  
  estimatedCost: {
    rules: [
      'numeric',
      'positive',
      createRule('max', { max: 100000 })
    ],
    validateOn: 'input',
    debounceMs: 500,
    label: 'Estimated Cost (OMR)',
    labelAr: 'التكلفة المتوقعة (ريال عماني)'
  },
  
  scheduledDate: {
    rules: [
      'required',
      createRule('dateAfter', { date: new Date() })
    ],
    validateOn: 'blur',
    required: true,
    label: 'Scheduled Date',
    labelAr: 'تاريخ الموعد'
  }
}

// Parts Inventory Schema
export const partsInventorySchema: FormValidationConfig = {
  partNumber: {
    rules: [
      'required',
      createRule('pattern', { 
        pattern: /^[A-Z0-9-]+$/,
      }, 'Part number must be alphanumeric with hyphens', 
         'رقم القطعة يجب أن يكون أرقام وحروف مع شرطات')
    ],
    validateOn: 'blur',
    required: true,
    label: 'Part Number',
    labelAr: 'رقم القطعة'
  },
  
  name: {
    rules: [
      'required',
      createRule('minLength', { min: 3 }),
      createRule('maxLength', { max: 100 })
    ],
    validateOn: 'blur',
    required: true,
    label: 'Part Name',
    labelAr: 'اسم القطعة'
  },
  
  nameAr: {
    rules: [
      'arabicText',
      createRule('minLength', { min: 3 }),
      createRule('maxLength', { max: 100 })
    ],
    validateOn: 'blur',
    label: 'Part Name (Arabic)',
    labelAr: 'اسم القطعة (عربي)'
  },
  
  barcode: {
    rules: [
      createRule('pattern', { 
        pattern: /^[0-9]{8,13}$/,
      }, 'Barcode must be 8-13 digits', 'الباركود يجب أن يكون 8-13 رقم')
    ],
    validateOn: 'blur',
    label: 'Barcode',
    labelAr: 'الباركود'
  },
  
  quantity: {
    rules: [
      'required',
      'integer',
      createRule('min', { min: 0 })
    ],
    validateOn: 'input',
    debounceMs: 300,
    required: true,
    label: 'Quantity',
    labelAr: 'الكمية'
  },
  
  unitPrice: {
    rules: [
      'required',
      'numeric',
      'positive',
      createRule('max', { max: 10000 })
    ],
    validateOn: 'input',
    debounceMs: 500,
    required: true,
    label: 'Unit Price (OMR)',
    labelAr: 'سعر الوحدة (ريال عماني)'
  },
  
  minStockLevel: {
    rules: [
      'integer',
      createRule('min', { min: 0 })
    ],
    validateOn: 'input',
    debounceMs: 300,
    label: 'Minimum Stock Level',
    labelAr: 'مستوى المخزون الأدنى'
  }
}

// Customer Registration Schema
export const customerRegistrationSchema: FormValidationConfig = {
  name: {
    rules: [
      'required',
      createRule('minLength', { min: 2 }),
      createRule('maxLength', { max: 100 })
    ],
    validateOn: 'blur',
    required: true,
    label: 'Customer Name',
    labelAr: 'اسم العميل'
  },
  
  nameAr: {
    rules: [
      'arabicText',
      createRule('minLength', { min: 2 }),
      createRule('maxLength', { max: 100 })
    ],
    validateOn: 'blur',
    label: 'Customer Name (Arabic)',
    labelAr: 'اسم العميل (عربي)'
  },
  
  email: {
    rules: ['email'],
    validateOn: 'blur',
    label: 'Email Address',
    labelAr: 'عنوان البريد الإلكتروني'
  },
  
  phone: {
    rules: ['required', 'phone'],
    validateOn: 'blur',
    required: true,
    label: 'Phone Number',
    labelAr: 'رقم الهاتف'
  },
  
  civilId: {
    rules: [
      createRule('pattern', { 
        pattern: /^[0-9]{8}$/,
      }, 'Civil ID must be 8 digits', 'الرقم المدني يجب أن يكون 8 أرقام')
    ],
    validateOn: 'blur',
    label: 'Civil ID',
    labelAr: 'الرقم المدني'
  },
  
  address: {
    rules: [
      createRule('minLength', { min: 10 }),
      createRule('maxLength', { max: 200 })
    ],
    validateOn: 'input',
    debounceMs: 1000,
    label: 'Address',
    labelAr: 'العنوان'
  },
  
  dateOfBirth: {
    rules: [
      createRule('dateBefore', { date: new Date() })
    ],
    validateOn: 'blur',
    label: 'Date of Birth',
    labelAr: 'تاريخ الميلاد'
  }
}

// Invoice Schema
export const invoiceSchema: FormValidationConfig = {
  customerId: {
    rules: ['required'],
    validateOn: 'blur',
    required: true,
    label: 'Customer',
    labelAr: 'العميل'
  },
  
  invoiceDate: {
    rules: [
      'required',
      createRule('dateBefore', { date: new Date(Date.now() + 24 * 60 * 60 * 1000) }) // Tomorrow
    ],
    validateOn: 'blur',
    required: true,
    label: 'Invoice Date',
    labelAr: 'تاريخ الفاتورة'
  },
  
  dueDate: {
    rules: [
      'required',
      createRule('dateAfter', { date: new Date() })
    ],
    validateOn: 'blur',
    required: true,
    label: 'Due Date',
    labelAr: 'تاريخ الاستحقاق'
  },
  
  subtotal: {
    rules: [
      'required',
      'numeric',
      'positive'
    ],
    validateOn: 'input',
    debounceMs: 500,
    required: true,
    label: 'Subtotal (OMR)',
    labelAr: 'المجموع الفرعي (ريال عماني)'
  },
  
  vatRate: {
    rules: [
      'required',
      'numeric',
      createRule('min', { min: 0 }),
      createRule('max', { max: 100 })
    ],
    validateOn: 'input',
    debounceMs: 300,
    required: true,
    label: 'VAT Rate (%)',
    labelAr: 'معدل ضريبة القيمة المضافة (%)'
  },
  
  notes: {
    rules: [
      createRule('maxLength', { max: 500 })
    ],
    validateOn: 'input',
    debounceMs: 1000,
    label: 'Notes',
    labelAr: 'ملاحظات'
  }
}

// Export all schemas
export const validationSchemas = {
  userRegistration: userRegistrationSchema,
  vehicleRegistration: vehicleRegistrationSchema,
  serviceOrder: serviceOrderSchema,
  partsInventory: partsInventorySchema,
  customerRegistration: customerRegistrationSchema,
  invoice: invoiceSchema,
}

export default validationSchemas