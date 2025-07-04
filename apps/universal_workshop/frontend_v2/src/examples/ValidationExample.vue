<!--
  Validation Example - Universal Workshop Frontend V2
  
  Example demonstrating the comprehensive validation system with Arabic/RTL support,
  real-time validation, and integration with form components.
-->

<template>
  <div class="validation-example">
    <h1>{{ title }}</h1>
    
    <!-- Language Toggle -->
    <div class="language-toggle">
      <Button
        variant="outline"
        size="sm"
        @click="toggleLanguage"
      >
        {{ preferArabic ? 'English' : 'العربية' }}
      </Button>
    </div>

    <!-- User Registration Form -->
    <Card class="form-card">
      <template #header>
        <h2>{{ preferArabic ? 'تسجيل مستخدم جديد' : 'User Registration' }}</h2>
      </template>

      <Form
        :initial-data="userFormData"
        :validation-config="userValidationConfig"
        :prefer-arabic="preferArabic"
        @submit-valid="handleUserRegistration"
        @submit-invalid="handleInvalidSubmit"
      >
        <template #default="{ isValid, isValidating }">
          <!-- Personal Information Section -->
          <div class="form-section">
            <h3 class="form-section-title">
              {{ preferArabic ? 'المعلومات الشخصية' : 'Personal Information' }}
            </h3>
            
            <div class="form-row">
              <FormField
                name="firstName"
                :prefer-arabic="preferArabic"
                class="form-field-half"
              >
                <template #default="{ fieldId, setValue, touch, hasError }">
                  <Input
                    :id="fieldId"
                    :model-value="userFormData.firstName"
                    :label="preferArabic ? 'الاسم الأول' : 'First Name'"
                    :placeholder="preferArabic ? 'أدخل الاسم الأول' : 'Enter first name'"
                    :error="hasError"
                    required
                    @update:model-value="setValue"
                    @blur="touch"
                  />
                </template>
              </FormField>
              
              <FormField
                name="lastName"
                :prefer-arabic="preferArabic"
                class="form-field-half"
              >
                <template #default="{ fieldId, setValue, touch, hasError }">
                  <Input
                    :id="fieldId"
                    :model-value="userFormData.lastName"
                    :label="preferArabic ? 'اسم العائلة' : 'Last Name'"
                    :placeholder="preferArabic ? 'أدخل اسم العائلة' : 'Enter last name'"
                    :error="hasError"
                    required
                    @update:model-value="setValue"
                    @blur="touch"
                  />
                </template>
              </FormField>
            </div>

            <div class="form-row">
              <FormField
                name="firstNameAr"
                :prefer-arabic="preferArabic"
                class="form-field-half"
              >
                <template #default="{ fieldId, setValue, touch, hasError }">
                  <ArabicInput
                    :id="fieldId"
                    :model-value="userFormData.firstNameAr"
                    :label="preferArabic ? 'الاسم الأول (عربي)' : 'First Name (Arabic)'"
                    :placeholder="preferArabic ? 'أدخل الاسم الأول بالعربي' : 'Enter first name in Arabic'"
                    :error="hasError"
                    auto-direction
                    @update:model-value="setValue"
                    @blur="touch"
                  />
                </template>
              </FormField>
              
              <FormField
                name="lastNameAr"
                :prefer-arabic="preferArabic"
                class="form-field-half"
              >
                <template #default="{ fieldId, setValue, touch, hasError }">
                  <ArabicInput
                    :id="fieldId"
                    :model-value="userFormData.lastNameAr"
                    :label="preferArabic ? 'اسم العائلة (عربي)' : 'Last Name (Arabic)'"
                    :placeholder="preferArabic ? 'أدخل اسم العائلة بالعربي' : 'Enter last name in Arabic'"
                    :error="hasError"
                    auto-direction
                    @update:model-value="setValue"
                    @blur="touch"
                  />
                </template>
              </FormField>
            </div>
          </div>

          <!-- Contact Information Section -->
          <div class="form-section">
            <h3 class="form-section-title">
              {{ preferArabic ? 'معلومات الاتصال' : 'Contact Information' }}
            </h3>
            
            <FormField
              name="email"
              :prefer-arabic="preferArabic"
            >
              <template #default="{ fieldId, setValue, touch, hasError }">
                <Input
                  :id="fieldId"
                  :model-value="userFormData.email"
                  :label="preferArabic ? 'عنوان البريد الإلكتروني' : 'Email Address'"
                  :placeholder="preferArabic ? 'user@example.com' : 'user@example.com'"
                  type="email"
                  :error="hasError"
                  required
                  @update:model-value="setValue"
                  @blur="touch"
                />
              </template>
            </FormField>
            
            <FormField
              name="phone"
              :prefer-arabic="preferArabic"
            >
              <template #default="{ fieldId, setValue, touch, hasError }">
                <Input
                  :id="fieldId"
                  :model-value="userFormData.phone"
                  :label="preferArabic ? 'رقم الهاتف' : 'Phone Number'"
                  :placeholder="preferArabic ? '+968 9XXX XXXX' : '+968 9XXX XXXX'"
                  type="tel"
                  :error="hasError"
                  required
                  @update:model-value="setValue"
                  @blur="touch"
                />
              </template>
            </FormField>
          </div>

          <!-- Security Section -->
          <div class="form-section">
            <h3 class="form-section-title">
              {{ preferArabic ? 'الأمان' : 'Security' }}
            </h3>
            
            <FormField
              name="password"
              :prefer-arabic="preferArabic"
              show-validation-status
            >
              <template #default="{ fieldId, setValue, touch, hasError, isValidating }">
                <Input
                  :id="fieldId"
                  :model-value="userFormData.password"
                  :label="preferArabic ? 'كلمة المرور' : 'Password'"
                  :placeholder="preferArabic ? 'أدخل كلمة مرور قوية' : 'Enter a strong password'"
                  type="password"
                  :error="hasError"
                  :loading="isValidating"
                  required
                  @update:model-value="setValue"
                  @blur="touch"
                />
              </template>
            </FormField>
            
            <FormField
              name="confirmPassword"
              :prefer-arabic="preferArabic"
            >
              <template #default="{ fieldId, setValue, touch, hasError }">
                <Input
                  :id="fieldId"
                  :model-value="userFormData.confirmPassword"
                  :label="preferArabic ? 'تأكيد كلمة المرور' : 'Confirm Password'"
                  :placeholder="preferArabic ? 'أعد إدخال كلمة المرور' : 'Re-enter password'"
                  type="password"
                  :error="hasError"
                  required
                  @update:model-value="setValue"
                  @blur="touch"
                />
              </template>
            </FormField>
          </div>

          <!-- Form Actions -->
          <div class="form-actions">
            <Button
              type="submit"
              variant="primary"
              :loading="isValidating"
              :disabled="!isValid || isValidating"
            >
              {{ preferArabic ? 'تسجيل المستخدم' : 'Register User' }}
            </Button>
            
            <Button
              type="reset"
              variant="outline"
            >
              {{ preferArabic ? 'إعادة تعيين' : 'Reset' }}
            </Button>
          </div>
        </template>
      </Form>
    </Card>

    <!-- Validation Status Display -->
    <Card v-if="showValidationStatus" class="status-card">
      <template #header>
        <h3>{{ preferArabic ? 'حالة التحقق' : 'Validation Status' }}</h3>
      </template>
      
      <div class="validation-status">
        <div class="status-item">
          <strong>{{ preferArabic ? 'صحيح:' : 'Valid:' }}</strong>
          <span :class="{ 'text-success': isFormValid, 'text-error': !isFormValid }">
            {{ isFormValid ? (preferArabic ? 'نعم' : 'Yes') : (preferArabic ? 'لا' : 'No') }}
          </span>
        </div>
        
        <div class="status-item">
          <strong>{{ preferArabic ? 'يتم التحقق:' : 'Validating:' }}</strong>
          <span>{{ isFormValidating ? (preferArabic ? 'نعم' : 'Yes') : (preferArabic ? 'لا' : 'No') }}</span>
        </div>
        
        <div class="status-item">
          <strong>{{ preferArabic ? 'يحتوي على أخطاء:' : 'Has Errors:' }}</strong>
          <span :class="{ 'text-error': hasFormErrors }">
            {{ hasFormErrors ? (preferArabic ? 'نعم' : 'Yes') : (preferArabic ? 'لا' : 'No') }}
          </span>
        </div>
        
        <div class="status-item">
          <strong>{{ preferArabic ? 'تم التعديل:' : 'Dirty:' }}</strong>
          <span>{{ isFormDirty ? (preferArabic ? 'نعم' : 'Yes') : (preferArabic ? 'لا' : 'No') }}</span>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { Form, FormField, validationSchemas } from '@/components/forms'
import { Button } from '@/components/base'
import { Input, ArabicInput } from '@/components/base'
import { Card } from '@/components/base'

// Component state
const preferArabic = ref(true)
const showValidationStatus = ref(true)

// Form data
const userFormData = reactive({
  firstName: '',
  lastName: '',
  firstNameAr: '',
  lastNameAr: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

// Use predefined validation schema
const userValidationConfig = validationSchemas.userRegistration

// Form validation state (would be provided by Form component)
const isFormValid = ref(false)
const isFormValidating = ref(false)
const hasFormErrors = ref(false)
const isFormDirty = ref(false)

// Computed title
const title = computed(() => {
  return preferArabic.value ? 'مثال على نظام التحقق' : 'Validation System Example'
})

// Methods
const toggleLanguage = () => {
  preferArabic.value = !preferArabic.value
}

const handleUserRegistration = (data: Record<string, any>) => {
  console.log('Valid user registration:', data)
  
  // Show success message (would integrate with Toast component)
  alert(preferArabic.value 
    ? 'تم تسجيل المستخدم بنجاح!' 
    : 'User registered successfully!'
  )
}

const handleInvalidSubmit = (data: Record<string, any>, errors: string[]) => {
  console.log('Invalid form submission:', { data, errors })
  
  // Show error message
  alert(preferArabic.value 
    ? 'يرجى تصحيح الأخطاء في النموذج' 
    : 'Please correct the errors in the form'
  )
}
</script>

<style lang="scss" scoped>
.validation-example {
  max-width: 800px;
  margin: 0 auto;
  padding: var(--spacing-6);
  
  h1 {
    text-align: center;
    margin-bottom: var(--spacing-6);
    color: var(--color-text-primary);
  }
}

.language-toggle {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--spacing-4);
}

.form-card {
  margin-bottom: var(--spacing-6);
}

.form-section {
  margin-bottom: var(--spacing-6);
  
  &:not(:last-child) {
    border-bottom: 1px solid var(--color-border-primary);
    padding-bottom: var(--spacing-6);
  }
}

.form-section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-4);
  border-bottom: 2px solid var(--color-primary);
  padding-bottom: var(--spacing-2);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
  
  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.form-field-half {
  @media (max-width: 640px) {
    grid-column: 1;
  }
}

.form-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  justify-content: flex-end;
  margin-top: var(--spacing-6);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--color-border-primary);
  
  @media (max-width: 640px) {
    flex-direction: column;
    align-items: stretch;
  }
}

.status-card {
  margin-top: var(--spacing-4);
}

.validation-status {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-3);
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-surface-secondary);
  border-radius: var(--radius-md);
  
  strong {
    color: var(--color-text-primary);
  }
  
  span {
    color: var(--color-text-secondary);
    
    &.text-success {
      color: var(--color-success);
      font-weight: var(--font-weight-medium);
    }
    
    &.text-error {
      color: var(--color-error);
      font-weight: var(--font-weight-medium);
    }
  }
}

// RTL support
[dir="rtl"] {
  .language-toggle {
    justify-content: flex-start;
  }
  
  .form-actions {
    justify-content: flex-start;
  }
}
</style>