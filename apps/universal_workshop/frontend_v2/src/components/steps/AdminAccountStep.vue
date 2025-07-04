<template>
  <div class="admin-account-step">
    <div class="step-header">
      <div class="step-icon">👤</div>
      <h2 class="step-title">{{ texts.steps.admin_account }}</h2>
      <p class="step-description">
        {{ isArabic 
          ? 'قم بإنشاء حساب المدير الرئيسي لورشتك'
          : 'Create the main administrator account for your workshop'
        }}
      </p>
    </div>

    <div class="form-container">
      <!-- Username Field -->
      <div class="form-group">
        <label class="form-label">
          <i class="label-icon">👨‍💼</i>
          {{ isArabic ? 'اسم المستخدم' : 'Username' }}
          <span class="required">*</span>
        </label>
        <div class="input-container">
          <input
            v-model="formData.admin_username"
            type="text"
            class="form-input"
            :class="{ 'error': validationErrors.admin_username, 'success': usernameValid }"
            :placeholder="isArabic ? 'أدخل اسم المستخدم' : 'Enter username'"
            @input="onUsernameInput"
            @blur="validateUsername"
          />
          <div class="input-status">
            <div v-if="isCheckingUsername" class="status-loading">
              <div class="spinner"></div>
            </div>
            <div v-else-if="usernameValid" class="status-success">
              <i>✓</i>
            </div>
            <div v-else-if="validationErrors.admin_username" class="status-error">
              <i>✕</i>
            </div>
          </div>
        </div>
        <div v-if="validationErrors.admin_username" class="field-error">
          {{ validationErrors.admin_username }}
        </div>
        <div v-else-if="usernameSuggestions.length > 0" class="username-suggestions">
          <span class="suggestion-label">{{ isArabic ? 'اقتراحات:' : 'Suggestions:' }}</span>
          <div class="suggestions-list">
            <button 
              v-for="suggestion in usernameSuggestions" 
              :key="suggestion"
              @click="selectUsername(suggestion)"
              class="suggestion-btn"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>
      </div>

      <!-- Password Field -->
      <div class="form-group">
        <label class="form-label">
          <i class="label-icon">🔒</i>
          {{ isArabic ? 'كلمة المرور' : 'Password' }}
          <span class="required">*</span>
        </label>
        <div class="input-container">
          <input
            v-model="formData.admin_password"
            :type="showPassword ? 'text' : 'password'"
            class="form-input"
            :class="{ 'error': validationErrors.admin_password }"
            :placeholder="isArabic ? 'أدخل كلمة مرور قوية' : 'Enter a strong password'"
            @input="onPasswordInput"
          />
          <button 
            type="button"
            @click="showPassword = !showPassword"
            class="password-toggle"
          >
            <i>{{ showPassword ? '🙈' : '👁️' }}</i>
          </button>
        </div>
        
        <!-- Password Strength Meter -->
        <div v-if="formData.admin_password" class="password-strength">
          <div class="strength-bar">
            <div 
              class="strength-fill"
              :class="passwordStrength.level"
              :style="{ width: passwordStrength.percentage + '%' }"
            ></div>
          </div>
          <div class="strength-info">
            <span class="strength-label" :class="passwordStrength.level">
              {{ isArabic ? passwordStrength.label_ar : passwordStrength.label_en }}
            </span>
            <span class="strength-score">{{ passwordStrength.score }}/100</span>
          </div>
        </div>
        
        <div v-if="validationErrors.admin_password" class="field-error">
          {{ validationErrors.admin_password }}
        </div>
        
        <!-- Password Requirements -->
        <div class="password-requirements">
          <div class="requirement-title">{{ isArabic ? 'متطلبات كلمة المرور:' : 'Password Requirements:' }}</div>
          <div class="requirements-list">
            <div 
              class="requirement-item"
              :class="{ 'met': passwordChecks.length }"
            >
              <i>{{ passwordChecks.length ? '✓' : '○' }}</i>
              {{ isArabic ? 'على الأقل 8 أحرف' : 'At least 8 characters' }}
            </div>
            <div 
              class="requirement-item"
              :class="{ 'met': passwordChecks.uppercase }"
            >
              <i>{{ passwordChecks.uppercase ? '✓' : '○' }}</i>
              {{ isArabic ? 'حرف كبير واحد' : 'One uppercase letter' }}
            </div>
            <div 
              class="requirement-item"
              :class="{ 'met': passwordChecks.lowercase }"
            >
              <i>{{ passwordChecks.lowercase ? '✓' : '○' }}</i>
              {{ isArabic ? 'حرف صغير واحد' : 'One lowercase letter' }}
            </div>
            <div 
              class="requirement-item"
              :class="{ 'met': passwordChecks.number }"
            >
              <i>{{ passwordChecks.number ? '✓' : '○' }}</i>
              {{ isArabic ? 'رقم واحد' : 'One number' }}
            </div>
            <div 
              class="requirement-item"
              :class="{ 'met': passwordChecks.special }"
            >
              <i>{{ passwordChecks.special ? '✓' : '○' }}</i>
              {{ isArabic ? 'رمز خاص واحد' : 'One special character' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Email Field -->
      <div class="form-group">
        <label class="form-label">
          <i class="label-icon">📧</i>
          {{ isArabic ? 'البريد الإلكتروني' : 'Email Address' }}
          <span class="required">*</span>
        </label>
        <div class="input-container">
          <input
            v-model="formData.admin_email"
            type="email"
            class="form-input"
            :class="{ 'error': validationErrors.admin_email, 'success': emailValid }"
            :placeholder="isArabic ? 'admin@workshop.com' : 'admin@yourworkshop.com'"
            @input="onEmailInput"
            @blur="validateEmail"
          />
          <div class="input-status">
            <div v-if="emailValid" class="status-success">
              <i>✓</i>
            </div>
            <div v-else-if="validationErrors.admin_email" class="status-error">
              <i>✕</i>
            </div>
          </div>
        </div>
        <div v-if="validationErrors.admin_email" class="field-error">
          {{ validationErrors.admin_email }}
        </div>
        <div v-else class="field-hint">
          {{ isArabic 
            ? 'سيتم استخدام هذا البريد للإشعارات المهمة'
            : 'This email will be used for important notifications'
          }}
        </div>
      </div>

      <!-- Phone Field -->
      <div class="form-group">
        <label class="form-label">
          <i class="label-icon">📱</i>
          {{ isArabic ? 'رقم الهاتف' : 'Contact Number' }}
          <span class="required">*</span>
        </label>
        <div class="input-container">
          <div class="phone-prefix">🇴🇲 +968</div>
          <input
            v-model="phoneNumber"
            type="tel"
            class="form-input phone-input"
            :class="{ 'error': validationErrors.admin_phone, 'success': phoneValid }"
            :placeholder="isArabic ? 'XXXXXXXX' : 'XXXXXXXX'"
            @input="onPhoneInput"
            maxlength="8"
          />
          <div class="input-status">
            <div v-if="phoneValid" class="status-success">
              <i>✓</i>
            </div>
            <div v-else-if="validationErrors.admin_phone" class="status-error">
              <i>✕</i>
            </div>
          </div>
        </div>
        <div v-if="validationErrors.admin_phone" class="field-error">
          {{ validationErrors.admin_phone }}
        </div>
        <div v-else class="field-hint">
          {{ isArabic 
            ? 'رقم هاتف عماني (8 أرقام بعد +968)'
            : 'Omani phone number (8 digits after +968)'
          }}
        </div>
      </div>

      <!-- Optional Profile Section -->
      <div class="optional-section">
        <div class="section-header">
          <h3 class="section-title">
            <i>📝</i>
            {{ isArabic ? 'معلومات إضافية (اختيارية)' : 'Additional Information (Optional)' }}
          </h3>
          <button 
            type="button"
            @click="showOptionalFields = !showOptionalFields"
            class="toggle-btn"
          >
            {{ showOptionalFields 
              ? (isArabic ? 'إخفاء' : 'Hide')
              : (isArabic ? 'إظهار' : 'Show')
            }}
            <i>{{ showOptionalFields ? '↑' : '↓' }}</i>
          </button>
        </div>
        
        <div v-if="showOptionalFields" class="optional-fields">
          <!-- Profile Picture -->
          <div class="form-group">
            <label class="form-label">
              <i class="label-icon">🖼️</i>
              {{ isArabic ? 'صورة الملف الشخصي' : 'Profile Picture' }}
            </label>
            <div class="profile-upload">
              <div class="current-avatar">
                <img v-if="avatarPreview" :src="avatarPreview" alt="Avatar" />
                <div v-else class="default-avatar">
                  <i>👤</i>
                </div>
              </div>
              <div class="upload-controls">
                <input 
                  ref="avatarInput"
                  type="file"
                  accept="image/*"
                  @change="onAvatarChange"
                  class="file-input"
                />
                <button 
                  type="button"
                  @click="$refs.avatarInput.click()"
                  class="upload-btn"
                >
                  {{ isArabic ? 'اختر صورة' : 'Choose Image' }}
                </button>
                <button 
                  v-if="avatarPreview"
                  type="button"
                  @click="removeAvatar"
                  class="remove-btn"
                >
                  {{ isArabic ? 'إزالة' : 'Remove' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Full Name -->
          <div class="form-group">
            <label class="form-label">
              <i class="label-icon">👨‍💼</i>
              {{ isArabic ? 'الاسم الكامل' : 'Full Name' }}
            </label>
            <input
              v-model="formData.admin_full_name"
              type="text"
              class="form-input"
              :placeholder="isArabic ? 'أدخل اسمك الكامل' : 'Enter your full name'"
            />
          </div>

          <!-- Job Title -->
          <div class="form-group">
            <label class="form-label">
              <i class="label-icon">💼</i>
              {{ isArabic ? 'المنصب' : 'Job Title' }}
            </label>
            <select v-model="formData.admin_job_title" class="form-input">
              <option value="">{{ isArabic ? 'اختر المنصب' : 'Select job title' }}</option>
              <option value="owner">{{ isArabic ? 'مالك الورشة' : 'Workshop Owner' }}</option>
              <option value="manager">{{ isArabic ? 'مدير الورشة' : 'Workshop Manager' }}</option>
              <option value="supervisor">{{ isArabic ? 'مشرف' : 'Supervisor' }}</option>
              <option value="admin">{{ isArabic ? 'مدير نظام' : 'System Administrator' }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AdminAccountStep',
  props: {
    texts: Object,
    data: Object,
    validationErrors: Object,
    isArabic: Boolean
  },
  
  data() {
    return {
      formData: {
        admin_username: '',
        admin_password: '',
        admin_email: '',
        admin_phone: '',
        admin_full_name: '',
        admin_job_title: '',
        admin_avatar: null
      },
      
      phoneNumber: '',
      showPassword: false,
      showOptionalFields: false,
      
      usernameValid: false,
      emailValid: false,
      phoneValid: false,
      isCheckingUsername: false,
      
      usernameSuggestions: [],
      avatarPreview: null,
      
      passwordChecks: {
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false
      }
    }
  },
  
  computed: {
    passwordStrength() {
      const password = this.formData.admin_password
      if (!password) return { score: 0, percentage: 0, level: 'none', label_en: '', label_ar: '' }
      
      let score = 0
      const checks = this.passwordChecks
      
      // Length scoring
      if (password.length >= 8) score += 20
      if (password.length >= 12) score += 10
      if (password.length >= 16) score += 10
      
      // Character variety scoring
      if (checks.uppercase) score += 15
      if (checks.lowercase) score += 15
      if (checks.number) score += 15
      if (checks.special) score += 15
      
      // Additional complexity
      if (password.length >= 10 && checks.uppercase && checks.lowercase && checks.number && checks.special) {
        score += 20
      }
      
      let level, label_en, label_ar
      if (score < 40) {
        level = 'weak'
        label_en = 'Weak'
        label_ar = 'ضعيفة'
      } else if (score < 70) {
        level = 'medium'
        label_en = 'Medium'
        label_ar = 'متوسطة'
      } else if (score < 90) {
        level = 'strong'
        label_en = 'Strong'
        label_ar = 'قوية'
      } else {
        level = 'excellent'
        label_en = 'Excellent'
        label_ar = 'ممتازة'
      }
      
      return {
        score: Math.min(score, 100),
        percentage: Math.min(score, 100),
        level,
        label_en,
        label_ar
      }
    }
  },
  
  watch: {
    data: {
      immediate: true,
      handler(newData) {
        if (newData) {
          this.formData = { ...this.formData, ...newData }
          if (newData.admin_phone) {
            this.phoneNumber = newData.admin_phone.replace('+968', '')
          }
        }
      }
    },
    
    formData: {
      deep: true,
      handler() {
        this.$emit('update', this.formData)
        this.validateForm()
      }
    },
    
    phoneNumber(newVal) {
      this.formData.admin_phone = newVal ? `+968${newVal}` : ''
      this.validatePhone()
    }
  },
  
  methods: {
    onUsernameInput() {
      this.usernameValid = false
      this.generateUsernameSuggestions()
      
      // Auto-format: lowercase, no spaces
      this.formData.admin_username = this.formData.admin_username
        .toLowerCase()
        .replace(/[^a-z0-9._-]/g, '')
    },
    
    generateUsernameSuggestions() {
      if (this.formData.admin_username.length >= 3) {
        // Generate smart suggestions based on current input
        const base = this.formData.admin_username.slice(0, 6)
        this.usernameSuggestions = [
          `${base}admin`,
          `${base}mgr`,
          `${base}2024`,
          `${base}_ws`,
          `admin_${base}`
        ].filter(s => s !== this.formData.admin_username)
      } else {
        this.usernameSuggestions = []
      }
    },
    
    selectUsername(username) {
      this.formData.admin_username = username
      this.usernameSuggestions = []
      this.validateUsername()
    },
    
    async validateUsername() {
      if (!this.formData.admin_username || this.formData.admin_username.length < 3) {
        return
      }
      
      this.isCheckingUsername = true
      
      try {
        // Simulate username availability check
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // For demo, consider usernames with 'admin' as taken
        if (this.formData.admin_username.includes('test')) {
          this.usernameValid = false
          this.$emit('validate', false, {
            admin_username: this.isArabic 
              ? 'اسم المستخدم مستخدم مسبقاً' 
              : 'Username already taken'
          })
        } else {
          this.usernameValid = true
        }
      } catch (error) {
        console.error('Username validation error:', error)
      } finally {
        this.isCheckingUsername = false
      }
    },
    
    onPasswordInput() {
      this.checkPasswordRequirements()
    },
    
    checkPasswordRequirements() {
      const password = this.formData.admin_password
      
      this.passwordChecks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
      }
    },
    
    onEmailInput() {
      this.emailValid = false
    },
    
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      this.emailValid = emailRegex.test(this.formData.admin_email)
    },
    
    onPhoneInput() {
      // Auto-format: only numbers
      this.phoneNumber = this.phoneNumber.replace(/\D/g, '')
    },
    
    validatePhone() {
      this.phoneValid = this.phoneNumber.length === 8 && /^\d{8}$/.test(this.phoneNumber)
    },
    
    onAvatarChange(event) {
      const file = event.target.files[0]
      if (file) {
        if (file.size > 2 * 1024 * 1024) { // 2MB limit
          alert(this.isArabic 
            ? 'حجم الصورة يجب أن يكون أقل من 2 ميجابايت'
            : 'Image size must be less than 2MB'
          )
          return
        }
        
        const reader = new FileReader()
        reader.onload = (e) => {
          this.avatarPreview = e.target.result
          this.formData.admin_avatar = file
        }
        reader.readAsDataURL(file)
      }
    },
    
    removeAvatar() {
      this.avatarPreview = null
      this.formData.admin_avatar = null
      this.$refs.avatarInput.value = ''
    },
    
    validateForm() {
      const errors = {}
      
      // Username validation
      if (!this.formData.admin_username) {
        errors.admin_username = this.isArabic ? 'اسم المستخدم مطلوب' : 'Username is required'
      } else if (this.formData.admin_username.length < 3) {
        errors.admin_username = this.isArabic ? 'اسم المستخدم قصير جداً' : 'Username too short'
      } else if (!this.usernameValid && !this.isCheckingUsername) {
        errors.admin_username = this.isArabic ? 'يرجى التحقق من اسم المستخدم' : 'Please verify username'
      }
      
      // Password validation
      if (!this.formData.admin_password) {
        errors.admin_password = this.isArabic ? 'كلمة المرور مطلوبة' : 'Password is required'
      } else if (this.passwordStrength.score < 40) {
        errors.admin_password = this.isArabic ? 'كلمة المرور ضعيفة جداً' : 'Password too weak'
      }
      
      // Email validation
      if (!this.formData.admin_email) {
        errors.admin_email = this.isArabic ? 'البريد الإلكتروني مطلوب' : 'Email is required'
      } else if (!this.emailValid) {
        errors.admin_email = this.isArabic ? 'صيغة البريد الإلكتروني غير صحيحة' : 'Invalid email format'
      }
      
      // Phone validation
      if (!this.phoneNumber) {
        errors.admin_phone = this.isArabic ? 'رقم الهاتف مطلوب' : 'Phone number is required'
      } else if (!this.phoneValid) {
        errors.admin_phone = this.isArabic ? 'رقم الهاتف غير صحيح' : 'Invalid phone number'
      }
      
      const isValid = Object.keys(errors).length === 0
      this.$emit('validate', isValid, errors)
    }
  },
  
  mounted() {
    if (this.data) {
      this.formData = { ...this.formData, ...this.data }
      if (this.data.admin_phone) {
        this.phoneNumber = this.data.admin_phone.replace('+968', '')
      }
    }
    
    this.validateForm()
  }
}
</script>

<style scoped>
/* Import all the styles from the previous component and add specific styles */
.admin-account-step {
  max-width: 600px;
  margin: 0 auto;
}

.step-header {
  text-align: center;
  margin-bottom: 3rem;
}

.step-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  display: block;
}

.step-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: #1e293b;
}

.step-description {
  font-size: 1.1rem;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #374151;
  font-size: 1rem;
}

.label-icon {
  font-size: 1.2rem;
}

.required {
  color: #ef4444;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input {
  width: 100%;
  padding: 1rem 3rem 1rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input.error {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.form-input.success {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

/* Phone Input */
.phone-prefix {
  position: absolute;
  left: 1rem;
  color: #6b7280;
  font-weight: 600;
  z-index: 2;
}

.phone-input {
  padding-left: 5rem !important;
}

/* Password Specific */
.password-toggle {
  position: absolute;
  right: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  z-index: 2;
}

.password-strength {
  margin-top: 0.5rem;
}

.strength-bar {
  width: 100%;
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
  border-radius: 3px;
}

.strength-fill.weak {
  background: #ef4444;
}

.strength-fill.medium {
  background: #f59e0b;
}

.strength-fill.strong {
  background: #10b981;
}

.strength-fill.excellent {
  background: #059669;
}

.strength-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.strength-label {
  font-weight: 600;
}

.strength-label.weak {
  color: #ef4444;
}

.strength-label.medium {
  color: #f59e0b;
}

.strength-label.strong {
  color: #10b981;
}

.strength-label.excellent {
  color: #059669;
}

.strength-score {
  color: #6b7280;
}

/* Password Requirements */
.password-requirements {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 0.5rem;
}

.requirement-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.requirement-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #6b7280;
  transition: color 0.3s ease;
}

.requirement-item.met {
  color: #10b981;
}

.requirement-item i {
  width: 16px;
  text-align: center;
}

/* Username Suggestions */
.username-suggestions {
  margin-top: 0.5rem;
}

.suggestion-label {
  font-size: 0.9rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
  display: block;
}

.suggestions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.suggestion-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 20px;
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  color: #374151;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-btn:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* Input Status Icons */
.input-status {
  position: absolute;
  right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.status-loading .spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.status-success {
  background: #10b981;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

.status-error {
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
}

/* Optional Section */
.optional-section {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem;
  background: #fafbfc;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #374151;
  margin: 0;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  background: #5a67d8;
}

.optional-fields {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Profile Upload */
.profile-upload {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.current-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.current-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-avatar {
  width: 100%;
  height: 100%;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: #9ca3af;
}

.upload-controls {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.file-input {
  display: none;
}

.upload-btn,
.remove-btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-btn {
  background: #667eea;
  color: white;
  border: none;
}

.upload-btn:hover {
  background: #5a67d8;
}

.remove-btn {
  background: #f3f4f6;
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.remove-btn:hover {
  background: #fee2e2;
  color: #dc2626;
  border-color: #fca5a5;
}

/* Error and Hint Messages */
.field-error {
  color: #ef4444;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}

.field-hint {
  color: #6b7280;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}

/* Animations */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .profile-upload {
    flex-direction: column;
    align-items: center;
  }
  
  .upload-controls {
    align-items: center;
  }
  
  .suggestions-list {
    justify-content: center;
  }
  
  .section-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}
</style>