<template>
  <div class="modern-login" :class="{ 'rtl': isRTL }">
    <!-- Animated Background -->
    <div class="login-background">
      <div class="background-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
      </div>
      <div class="background-gradient"></div>
    </div>

    <!-- Main Content -->
    <div class="login-container">
      <!-- Branding Section -->
      <div class="branding-section">
        <div class="logo-container">
          <div class="logo-circle">
            <svg viewBox="0 0 64 64" class="workshop-logo">
              <defs>
                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                  <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                </linearGradient>
              </defs>
              <circle cx="32" cy="32" r="30" fill="url(#logoGradient)" />
              <path d="M20 28h24v8H20z" fill="white" opacity="0.9" />
              <circle cx="26" cy="38" r="4" fill="white" opacity="0.9" />
              <circle cx="38" cy="38" r="4" fill="white" opacity="0.9" />
              <path d="M24 20h16v6H24z" fill="white" opacity="0.7" />
            </svg>
          </div>
          <div class="brand-text">
            <h1 class="brand-name">{{ $t('Universal Workshop') }}</h1>
            <p class="brand-tagline">{{ $t('Modern Workshop Management') }}</p>
          </div>
        </div>

        <!-- Welcome Message -->
        <div class="welcome-section">
          <h2 class="welcome-title">
            {{ isFirstLogin ? $t('Welcome to Your Workshop!') : $t('Welcome Back!') }}
          </h2>
          <p class="welcome-message">
            {{ isFirstLogin 
              ? $t('Your workshop has been set up successfully. Please sign in with your administrator credentials to get started.')
              : $t('Sign in to access your workshop management dashboard.')
            }}
          </p>
          
          <!-- Success Badge for First Login -->
          <div v-if="isFirstLogin" class="success-badge">
            <div class="badge-icon">✓</div>
            <span>{{ $t('Setup Complete') }}</span>
          </div>
        </div>
      </div>

      <!-- Login Form -->
      <div class="login-form-section">
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-header">
            <h3 class="form-title">{{ $t('Sign In') }}</h3>
            <p class="form-subtitle">{{ $t('Enter your credentials to continue') }}</p>
          </div>

          <!-- Username/Email Field -->
          <div class="form-group" :class="{ 'has-error': errors.username }">
            <label for="username" class="form-label">
              {{ $t('Username or Email') }}
            </label>
            <div class="input-container">
              <div class="input-icon">
                <svg viewBox="0 0 24 24">
                  <path d="M12 12C14.21 12 16 10.21 16 8S14.21 4 12 4 8 5.79 8 8 9.79 12 12 12ZM12 14C9.33 14 4 15.34 4 18V20H20V18C20 15.34 14.67 14 12 14Z" fill="currentColor"/>
                </svg>
              </div>
              <input
                id="username"
                v-model="loginForm.username"
                type="text"
                class="form-input"
                :placeholder="$t('Enter username or email')"
                autocomplete="username"
                @blur="validateField('username')"
                @input="clearError('username')"
                @keydown.enter="focusPassword"
              />
              <div v-if="isRemembered" class="remembered-badge">
                <svg viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                </svg>
              </div>
            </div>
            <div v-if="errors.username" class="error-message">
              {{ errors.username }}
            </div>
          </div>

          <!-- Password Field -->
          <div class="form-group" :class="{ 'has-error': errors.password }">
            <label for="password" class="form-label">
              {{ $t('Password') }}
            </label>
            <div class="input-container">
              <div class="input-icon">
                <svg viewBox="0 0 24 24">
                  <path d="M12.65 10C11.83 7.67 9.61 6 7 6C3.69 6 1 8.69 1 12S3.69 18 7 18C9.61 18 11.83 16.33 12.65 14H17V18H21V14H23V10H12.65ZM7 14C5.83 14 5 13.17 5 12S5.83 10 7 10 9 10.83 9 12 8.17 14 7 14Z" fill="currentColor"/>
                </svg>
              </div>
              <input
                id="password"
                ref="passwordInput"
                v-model="loginForm.password"
                :type="showPassword ? 'text' : 'password'"
                class="form-input"
                :placeholder="$t('Enter password')"
                autocomplete="current-password"
                @blur="validateField('password')"
                @input="clearError('password')"
              />
              <button
                type="button"
                class="password-toggle"
                @click="togglePassword"
                :title="showPassword ? $t('Hide password') : $t('Show password')"
              >
                <svg viewBox="0 0 24 24">
                  <path v-if="!showPassword" d="M12 4.5C7 4.5 2.73 7.61 1 12C2.73 16.39 7 19.5 12 19.5S21.27 16.39 23 12C21.27 7.61 17 4.5 12 4.5ZM12 17C9.24 17 7 14.76 7 12S9.24 7 12 7S17 9.24 17 12S14.76 17 12 17ZM12 9C10.34 9 9 10.34 9 12S10.34 15 12 15S15 13.66 15 12S13.66 9 12 9Z" fill="currentColor"/>
                  <path v-else d="M12 7C12.53 7 13.04 7.11 13.5 7.31L11.69 9.12C11.8 9.04 11.9 9 12 9C13.66 9 15 10.34 15 12C15 12.1 14.96 12.2 14.88 12.31L16.69 10.5C17.89 11.47 18.83 12.66 19.5 14C18.83 15.34 17.89 16.53 16.69 17.5L15.31 16.12C14.04 17.11 12.53 17.5 12 17.5C9.24 17.5 7 15.26 7 12.5C7 11.97 7.39 10.46 8.38 9.19L6.19 7L7.31 5.88L18.12 16.69L19.31 15.5L12 7Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
            <div v-if="errors.password" class="error-message">
              {{ errors.password }}
            </div>
          </div>

          <!-- Form Options -->
          <div class="form-options">
            <label class="remember-checkbox">
              <input
                v-model="loginForm.rememberMe"
                type="checkbox"
                class="checkbox-input"
              />
              <div class="checkbox-custom">
                <svg v-if="loginForm.rememberMe" viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
                </svg>
              </div>
              <span class="checkbox-label">{{ $t('Remember me') }}</span>
            </label>

            <button
              type="button"
              class="forgot-password-link"
              @click="showForgotPassword"
            >
              {{ $t('Forgot password?') }}
            </button>
          </div>

          <!-- Submit Button -->
          <button
            type="submit"
            class="login-button"
            :disabled="isLoading || !isFormValid"
            :class="{ 'loading': isLoading }"
          >
            <div v-if="isLoading" class="loading-spinner">
              <div class="spinner"></div>
            </div>
            <span v-else class="button-content">
              <svg viewBox="0 0 24 24" class="login-icon">
                <path d="M10 17L15 12L10 7V10H3V14H10V17ZM21 3H11C9.9 3 9 3.9 9 5V9H11V5H21V19H11V15H9V19C9 20.1 9.9 21 11 21H21C22.1 21 23 20.1 23 19V5C23 3.9 22.1 3 21 3Z" fill="currentColor"/>
              </svg>
              {{ $t('Sign In') }}
            </span>
          </button>

          <!-- Additional Info for First Login -->
          <div v-if="isFirstLogin" class="first-login-info">
            <div class="info-icon">ℹ️</div>
            <div class="info-content">
              <strong>{{ $t('First Time Login') }}</strong>
              <p>{{ $t('Use the administrator credentials you created during setup') }}</p>
            </div>
          </div>
        </form>

        <!-- Workshop Info Card -->
        <div v-if="workshopInfo" class="workshop-info-card">
          <div class="workshop-icon">🏢</div>
          <div class="workshop-details">
            <h4>{{ workshopInfo.name }}</h4>
            <p>{{ workshopInfo.code }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-animation">
          <div class="gear gear-1">⚙️</div>
          <div class="gear gear-2">⚙️</div>
        </div>
        <p class="loading-text">{{ loadingText }}</p>
      </div>
    </div>

    <!-- Success Modal -->
    <Teleport to="body">
      <div v-if="showSuccessModal" class="success-modal-overlay">
        <div class="success-modal">
          <div class="success-animation">
            <div class="success-circle">
              <div class="checkmark">✓</div>
            </div>
            <div class="success-particles">
              <div class="particle" v-for="n in 8" :key="n"></div>
            </div>
          </div>
          <h3 class="success-title">{{ $t('Welcome to Your Workshop!') }}</h3>
          <p class="success-message">
            {{ $t('Login successful! Redirecting to your dashboard...') }}
          </p>
          <div class="success-details">
            <div class="detail-item">
              <strong>{{ $t('Workshop') }}:</strong> {{ workshopInfo?.name }}
            </div>
            <div class="detail-item">
              <strong>{{ $t('Role') }}:</strong> {{ $t('Administrator') }}
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useArabicUtils } from '@/composables/useArabicUtils'
import frappe from '@/api/frappe-adapter'

const { t } = useI18n()
const router = useRouter()
const { isRTL } = useArabicUtils()

// Props
const props = defineProps<{
  isFirstLogin?: boolean
  workshopInfo?: {
    name: string
    code: string
    adminUsername?: string
  } | null
}>()

// State
const loginForm = ref({
  username: '',
  password: '',
  rememberMe: false
})

const errors = ref<Record<string, string>>({})
const isLoading = ref(false)
const loadingText = ref('')
const showPassword = ref(false)
const showSuccessModal = ref(false)
const passwordInput = ref<HTMLInputElement>()

// Computed
const isFormValid = computed(() => {
  return loginForm.value.username.trim() &&
         loginForm.value.password.trim() &&
         Object.keys(errors.value).length === 0
})

const isRemembered = computed(() => {
  // Check if this username was previously saved
  const savedUsername = localStorage.getItem('workshop_remembered_username')
  return savedUsername === loginForm.value.username
})

// Methods
const validateField = (fieldName: string) => {
  const value = loginForm.value[fieldName]
  
  switch (fieldName) {
    case 'username':
      if (!value.trim()) {
        errors.value.username = t('Username or email is required')
      } else {
        delete errors.value.username
      }
      break
    case 'password':
      if (!value.trim()) {
        errors.value.password = t('Password is required')
      } else if (value.length < 6) {
        errors.value.password = t('Password must be at least 6 characters')
      } else {
        delete errors.value.password
      }
      break
  }
}

const clearError = (fieldName: string) => {
  delete errors.value[fieldName]
}

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const focusPassword = () => {
  nextTick(() => {
    passwordInput.value?.focus()
  })
}

const handleLogin = async () => {
  if (isLoading.value || !isFormValid.value) return

  // Validate all fields
  validateField('username')
  validateField('password')
  
  if (Object.keys(errors.value).length > 0) return

  try {
    isLoading.value = true
    loadingText.value = t('Signing in...')

    // Call Frappe login API
    const response = await frappe.call('login', {
      usr: loginForm.value.username,
      pwd: loginForm.value.password
    })

    if (response) {
      // Handle remember me
      if (loginForm.value.rememberMe) {
        localStorage.setItem('workshop_remembered_username', loginForm.value.username)
      } else {
        localStorage.removeItem('workshop_remembered_username')
      }

      // Show success modal
      showSuccessModal.value = true
      
      // Redirect after delay
      setTimeout(() => {
        redirectToDashboard()
      }, 2500)
    }
  } catch (error) {
    console.error('Login error:', error)
    
    if (error.message.includes('password')) {
      errors.value.password = t('Invalid password')
    } else if (error.message.includes('user') || error.message.includes('username')) {
      errors.value.username = t('User not found')
    } else {
      errors.value.username = t('Login failed. Please check your credentials.')
    }
  } finally {
    isLoading.value = false
  }
}

const redirectToDashboard = () => {
  // Redirect to dashboard
  if (props.isFirstLogin) {
    router.push('/dashboard?welcome=true')
  } else {
    router.push('/dashboard')
  }
}

const showForgotPassword = () => {
  // Handle forgot password
  alert(t('Forgot password functionality will be implemented here'))
}

// Lifecycle
onMounted(() => {
  // Pre-fill username if it's first login and we have workshop info
  if (props.isFirstLogin && props.workshopInfo?.adminUsername) {
    loginForm.value.username = props.workshopInfo.adminUsername
  }
  
  // Load remembered username
  const savedUsername = localStorage.getItem('workshop_remembered_username')
  if (savedUsername && !loginForm.value.username) {
    loginForm.value.username = savedUsername
    loginForm.value.rememberMe = true
  }
})
</script>

<style scoped lang="scss">
.modern-login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

  &.rtl {
    direction: rtl;
    font-family: 'Tajawal', 'Inter', sans-serif;
  }
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

.background-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite linear;
  
  &.shape-1 {
    width: 100px;
    height: 100px;
    top: 20%;
    left: 10%;
    animation-delay: 0s;
    background: rgba(102, 126, 234, 0.1);
  }
  
  &.shape-2 {
    width: 150px;
    height: 150px;
    top: 60%;
    right: 15%;
    animation-delay: -5s;
    background: rgba(118, 75, 162, 0.1);
  }
  
  &.shape-3 {
    width: 80px;
    height: 80px;
    bottom: 30%;
    left: 20%;
    animation-delay: -10s;
    background: rgba(16, 185, 129, 0.1);
  }
  
  &.shape-4 {
    width: 120px;
    height: 120px;
    top: 40%;
    right: 30%;
    animation-delay: -15s;
    background: rgba(245, 158, 11, 0.1);
  }
  
  &.shape-5 {
    width: 90px;
    height: 90px;
    bottom: 20%;
    right: 10%;
    animation-delay: -8s;
    background: rgba(239, 68, 68, 0.1);
  }
}

.background-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  opacity: 0.9;
}

.login-container {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  max-width: 1200px;
  width: 100%;
  margin: 2rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 40px 80px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  
  @media (max-width: 968px) {
    grid-template-columns: 1fr;
    max-width: 500px;
  }
}

.branding-section {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
    opacity: 0.3;
  }
  
  @media (max-width: 968px) {
    padding: 2rem;
    text-align: center;
  }
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
  
  @media (max-width: 968px) {
    justify-content: center;
    margin-bottom: 2rem;
  }
}

.logo-circle {
  width: 80px;
  height: 80px;
  
  .workshop-logo {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 8px 16px rgba(0, 0, 0, 0.3));
  }
}

.brand-text {
  @media (max-width: 968px) {
    text-align: center;
  }
}

.brand-name {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  
  @media (max-width: 968px) {
    font-size: 1.5rem;
  }
}

.brand-tagline {
  font-size: 1rem;
  opacity: 0.9;
  margin: 0;
}

.welcome-section {
  position: relative;
  z-index: 1;
}

.welcome-title {
  font-size: 2.5rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
  line-height: 1.2;
  
  @media (max-width: 968px) {
    font-size: 2rem;
  }
}

.welcome-message {
  font-size: 1.1rem;
  line-height: 1.6;
  opacity: 0.9;
  margin: 0 0 2rem 0;
}

.success-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 0.75rem 1.5rem;
  border-radius: 50px;
  backdrop-filter: blur(10px);
  border: 2px solid rgba(16, 185, 129, 0.3);
  
  .badge-icon {
    width: 20px;
    height: 20px;
    background: #10b981;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: bold;
  }
}

.login-form-section {
  padding: 3rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  
  @media (max-width: 968px) {
    padding: 2rem;
  }
}

.login-form {
  max-width: 400px;
  width: 100%;
  margin: 0 auto;
}

.form-header {
  text-align: center;
  margin-bottom: 2rem;
}

.form-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 0.5rem 0;
}

.form-subtitle {
  color: #64748b;
  margin: 0;
}

.form-group {
  margin-bottom: 1.5rem;
  
  &.has-error {
    .form-input {
      border-color: #ef4444;
      box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
    }
  }
}

.form-label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #9ca3af;
  z-index: 1;
  
  .rtl & {
    left: auto;
    right: 1rem;
  }
}

.form-input {
  width: 100%;
  padding: 1rem 1rem 1rem 3.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #fafafa;
  
  .rtl & {
    padding: 1rem 3.5rem 1rem 1rem;
  }
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    background: white;
  }
  
  &::placeholder {
    color: #9ca3af;
  }
}

.password-toggle {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  width: 24px;
  height: 24px;
  padding: 0;
  
  .rtl & {
    right: auto;
    left: 1rem;
  }
  
  &:hover {
    color: #667eea;
  }
}

.remembered-badge {
  position: absolute;
  right: 3rem;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  color: #10b981;
  
  .rtl & {
    right: auto;
    left: 3rem;
  }
}

.error-message {
  color: #ef4444;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  
  @media (max-width: 480px) {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
}

.remember-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.checkbox-input {
  display: none;
}

.checkbox-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  .checkbox-input:checked + & {
    background: #667eea;
    border-color: #667eea;
    color: white;
  }
  
  svg {
    width: 12px;
    height: 12px;
  }
}

.checkbox-label {
  font-size: 0.875rem;
  color: #374151;
}

.forgot-password-link {
  background: none;
  border: none;
  color: #667eea;
  font-size: 0.875rem;
  cursor: pointer;
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
}

.login-button {
  width: 100%;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
  
  &.loading {
    pointer-events: none;
  }
}

.loading-spinner {
  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top: 2px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

.button-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  .login-icon {
    width: 20px;
    height: 20px;
  }
}

.first-login-info {
  display: flex;
  gap: 0.75rem;
  padding: 1rem;
  background: #f0f9ff;
  border: 2px solid #bae6fd;
  border-radius: 12px;
  font-size: 0.875rem;
  
  .info-icon {
    font-size: 1.2rem;
  }
  
  .info-content {
    strong {
      color: #0369a1;
      display: block;
      margin-bottom: 0.25rem;
    }
    
    p {
      color: #0c4a6e;
      margin: 0;
      line-height: 1.4;
    }
  }
}

.workshop-info-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 2rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  
  .workshop-icon {
    font-size: 1.5rem;
  }
  
  .workshop-details {
    h4 {
      margin: 0 0 0.25rem 0;
      color: #374151;
      font-size: 0.9rem;
      font-weight: 600;
    }
    
    p {
      margin: 0;
      color: #6b7280;
      font-size: 0.8rem;
      font-family: 'Monaco', monospace;
    }
  }
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
  color: white;
}

.loading-animation {
  position: relative;
  margin: 0 auto 2rem;
  width: 100px;
  height: 100px;
  
  .gear {
    position: absolute;
    font-size: 3rem;
    animation: rotate 2s linear infinite;
    
    &.gear-1 {
      top: 0;
      left: 0;
      animation-direction: normal;
    }
    
    &.gear-2 {
      bottom: 0;
      right: 0;
      animation-direction: reverse;
      animation-delay: -1s;
    }
  }
}

.loading-text {
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0;
}

.success-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
  animation: fadeIn 0.3s ease-out;
}

.success-modal {
  background: white;
  border-radius: 20px;
  padding: 3rem;
  text-align: center;
  max-width: 500px;
  margin: 2rem;
  box-shadow: 0 40px 80px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.success-animation {
  position: relative;
  margin-bottom: 2rem;
}

.success-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  animation: bounceIn 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  
  .checkmark {
    color: white;
    font-size: 3rem;
    font-weight: bold;
  }
}

.success-particles {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  
  .particle {
    position: absolute;
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    animation: explode 1s ease-out forwards;
    
    @for $i from 1 through 8 {
      &:nth-child(#{$i}) {
        animation-delay: #{$i * 0.1}s;
        transform: rotate(#{$i * 45}deg) translateX(60px);
      }
    }
  }
}

.success-title {
  color: #1a202c;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
}

.success-message {
  color: #64748b;
  font-size: 1.1rem;
  margin: 0 0 2rem 0;
}

.success-details {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1.5rem;
  text-align: left;
  
  .detail-item {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    strong {
      color: #374151;
    }
  }
}

// Animations
@keyframes float {
  0%, 100% {
    transform: translateY(0px) rotate(0deg);
    opacity: 0.7;
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
    opacity: 0.3;
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes bounceIn {
  0% {
    opacity: 0;
    transform: scale(0.3);
  }
  50% {
    opacity: 1;
    transform: scale(1.05);
  }
  70% {
    transform: scale(0.9);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes explode {
  0% {
    opacity: 1;
    transform: scale(0);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0);
  }
}
</style>