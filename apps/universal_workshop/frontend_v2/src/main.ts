/**
 * Main Entry Point - Universal Workshop Frontend V2
 * 
 * This is a minimal working version to test the setup
 */

import { createApp } from 'vue'

// Enhanced app component with real Arabic functionality and onboarding
const App = {
  template: `
    <div v-if="!showOnboarding" style="
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      text-align: center;
      padding: 2rem;
      direction: inherit;
    " :dir="isArabic ? 'rtl' : 'ltr'">
      <div>
        <div style="font-size: 4rem; margin-bottom: 2rem;">🏪</div>
        <h1 style="font-size: 3rem; margin: 0 0 1rem 0; font-weight: 700;">
          {{ currentTexts.title }}
        </h1>
        <h2 style="font-size: 1.5rem; margin: 0 0 2rem 0; opacity: 0.9; font-weight: 400;">
          {{ currentTexts.subtitle }}
        </h2>
        <div style="
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 12px;
          padding: 2rem;
          max-width: 600px;
        ">
          <h3 style="margin: 0 0 1rem 0;">{{ currentTexts.successTitle }}</h3>
          <p style="margin: 0; opacity: 0.8; line-height: 1.6;">
            {{ currentTexts.description }}
          </p>
          <div style="margin-top: 2rem;">
            <button @click="startOnboarding" style="
              background: white;
              color: #667eea;
              border: none;
              padding: 1rem 2rem;
              border-radius: 50px;
              font-weight: 600;
              cursor: pointer;
              font-size: 1rem;
              margin: 0 1rem 1rem 0;
              transition: transform 0.2s ease;
            " @mouseenter="$event.target.style.transform='translateY(-2px)'"
               @mouseleave="$event.target.style.transform='translateY(0)'">
              {{ currentTexts.onboardingButton }}
            </button>
            <br>
            <button @click="toggleLanguage" style="
              background: rgba(255, 255, 255, 0.2);
              color: white;
              border: 2px solid white;
              padding: 0.75rem 1.5rem;
              border-radius: 50px;
              font-weight: 600;
              cursor: pointer;
              font-size: 0.9rem;
              transition: all 0.2s ease;
            " @mouseenter="$event.target.style.background='rgba(255, 255, 255, 0.3)'"
               @mouseleave="$event.target.style.background='rgba(255, 255, 255, 0.2)'">
              {{ currentTexts.languageToggle }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Onboarding Wizard Component -->
    <div v-else style="
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      padding: 2rem;
      direction: inherit;
    " :dir="isArabic ? 'rtl' : 'ltr'">
      <div style="
        background: rgba(255, 255, 255, 0.95);
        color: #333;
        border-radius: 20px;
        padding: 3rem;
        max-width: 800px;
        width: 100%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(20px);
      ">
        <div style="text-align: center; margin-bottom: 2rem;">
          <div style="font-size: 3rem; margin-bottom: 1rem;">🚀</div>
          <h2 style="margin: 0 0 1rem 0; color: #667eea; font-size: 2rem;">
            {{ currentTexts.wizardTitle }}
          </h2>
          <p style="margin: 0; opacity: 0.7;">
            {{ currentTexts.wizardSubtitle }}
          </p>
        </div>

        <!-- Step Progress -->
        <div style="display: flex; justify-content: center; margin-bottom: 3rem;">
          <div v-for="step in 6" :key="step" style="
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 0.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
          " :style="{
            background: step <= currentStep ? '#667eea' : '#e5e7eb',
            color: step <= currentStep ? 'white' : '#9ca3af'
          }">
            {{ step }}
          </div>
        </div>

        <!-- Current Step Content -->
        <div style="margin-bottom: 3rem;">
          <h3 style="margin: 0 0 1rem 0; color: #374151;">
            {{ currentStepData.title }}
          </h3>
          <p style="margin: 0 0 2rem 0; opacity: 0.7; line-height: 1.6;">
            {{ currentStepData.description }}
          </p>
          
          <!-- Form fields would go here -->
          <div style="
            background: #f8fafc;
            border-radius: 12px;
            padding: 1.5rem;
            border: 2px dashed #d1d5db;
            text-align: center;
            color: #6b7280;
          ">
            {{ currentTexts.formPlaceholder }}
          </div>
        </div>

        <!-- Navigation Buttons -->
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <button @click="goBack" v-if="currentStep > 1" style="
            background: #e5e7eb;
            color: #374151;
            border: none;
            padding: 1rem 2rem;
            border-radius: 50px;
            font-weight: 600;
            cursor: pointer;
          ">
            {{ currentTexts.backButton }}
          </button>
          <div v-else></div>

          <div>
            <button @click="exitOnboarding" style="
              background: none;
              color: #9ca3af;
              border: 2px solid #e5e7eb;
              padding: 1rem 2rem;
              border-radius: 50px;
              font-weight: 600;
              cursor: pointer;
              margin-right: 1rem;
            ">
              {{ currentTexts.exitButton }}
            </button>
            <button @click="nextStep" style="
              background: linear-gradient(135deg, #667eea, #764ba2);
              color: white;
              border: none;
              padding: 1rem 2rem;
              border-radius: 50px;
              font-weight: 600;
              cursor: pointer;
              box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            ">
              {{ currentStep === 6 ? currentTexts.finishButton : currentTexts.nextButton }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  data() {
    return {
      isArabic: false,
      showOnboarding: false,
      currentStep: 1,
      texts: {
        en: {
          title: 'Universal Workshop',
          subtitle: 'Frontend V2 - Working Perfectly!',
          successTitle: '🎉 Successfully Loaded!',
          description: 'The Vue.js 3 frontend is now running with full Arabic support. Click below to start the interactive onboarding wizard.',
          onboardingButton: '🚀 Start Onboarding Wizard',
          languageToggle: '🔄 التبديل إلى العربية',
          wizardTitle: 'Welcome to Universal Workshop',
          wizardSubtitle: 'Let\'s set up your automotive workshop management system',
          formPlaceholder: 'Interactive form fields will be implemented here',
          backButton: '← Back',
          nextButton: 'Next →',
          finishButton: '✅ Complete Setup',
          exitButton: '✕ Exit',
          steps: [
            { title: 'Welcome & Introduction', description: 'Learn about Universal Workshop features and benefits' },
            { title: 'Business Information', description: 'Enter your workshop details and business information' },
            { title: 'Admin Account Setup', description: 'Create your administrator account and security settings' },
            { title: 'Operational Settings', description: 'Configure your workshop operations and service types' },
            { title: 'Financial Configuration', description: 'Set up billing, VAT, and payment methods' },
            { title: 'Final Review', description: 'Review your settings and complete the setup' }
          ]
        },
        ar: {
          title: 'نظام إدارة الورش الشامل',
          subtitle: 'الواجهة الثانية - تعمل بشكل مثالي!',
          successTitle: '🎉 تم التحميل بنجاح!',
          description: 'تعمل واجهة Vue.js 3 الآن مع دعم كامل للغة العربية. انقر أدناه لبدء معالج الإعداد التفاعلي.',
          onboardingButton: '🚀 ابدأ معالج الإعداد',
          languageToggle: '🔄 Switch to English',
          wizardTitle: 'مرحباً بك في نظام إدارة الورش الشامل',
          wizardSubtitle: 'دعنا نقوم بإعداد نظام إدارة ورشة السيارات الخاص بك',
          formPlaceholder: 'سيتم تنفيذ حقول النموذج التفاعلية هنا',
          backButton: '→ رجوع',
          nextButton: '← التالي',
          finishButton: '✅ إكمال الإعداد',
          exitButton: '✕ خروج',
          steps: [
            { title: 'الترحيب والمقدمة', description: 'تعرف على ميزات وفوائد نظام إدارة الورش الشامل' },
            { title: 'معلومات الأعمال', description: 'أدخل تفاصيل ورشتك ومعلومات العمل' },
            { title: 'إعداد حساب المدير', description: 'إنشاء حساب المدير وإعدادات الأمان' },
            { title: 'الإعدادات التشغيلية', description: 'تكوين عمليات الورشة وأنواع الخدمات' },
            { title: 'التكوين المالي', description: 'إعداد الفواتير وضريبة القيمة المضافة وطرق الدفع' },
            { title: 'المراجعة النهائية', description: 'راجع إعداداتك وأكمل التثبيت' }
          ]
        }
      }
    }
  },
  computed: {
    currentTexts() {
      return this.texts[this.isArabic ? 'ar' : 'en']
    },
    currentStepData() {
      return this.currentTexts.steps[this.currentStep - 1] || this.currentTexts.steps[0]
    }
  },
  methods: {
    startOnboarding() {
      this.showOnboarding = true
    },
    exitOnboarding() {
      this.showOnboarding = false
      this.currentStep = 1
    },
    toggleLanguage() {
      this.isArabic = !this.isArabic
      document.documentElement.dir = this.isArabic ? 'rtl' : 'ltr'
      document.documentElement.lang = this.isArabic ? 'ar' : 'en'
      
      // Update body font family for Arabic
      if (this.isArabic) {
        document.body.style.fontFamily = "'Tajawal', 'Arabic UI Text', sans-serif"
      } else {
        document.body.style.fontFamily = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
      }
    },
    nextStep() {
      if (this.currentStep < 6) {
        this.currentStep++
      } else {
        // Complete setup
        alert('🎉 ' + (this.isArabic ? 'تم إكمال الإعداد بنجاح!' : 'Setup completed successfully!'))
        this.exitOnboarding()
      }
    },
    goBack() {
      if (this.currentStep > 1) {
        this.currentStep--
      }
    }
  }
}

// Create and mount the app
const app = createApp(App)

// Error handling
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err, info)
}

// Mount when ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Starting Universal Workshop Frontend V2...')
  app.mount('#app')
  console.log('✅ Frontend V2 mounted successfully!')
  
  // Hide loading screen
  const showApp = (window as any).showApp
  if (typeof showApp === 'function') {
    showApp()
  }
})

// Global access
;(window as any).WorkshopV2 = {
  version: '2.0.0',
  initialized: true,
  vue: app
}