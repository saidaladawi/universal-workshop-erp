🚗 Universal Workshop - Modern Onboarding Wizard Plan

  📋 PHASE 1: Car Workshop Logo & Branding

  1.1 Automotive Logo Design

  - Replace 🏪 with custom car workshop SVG icon:
    - Main Elements: Car silhouette, wrench/tools,
  workshop building
    - Style: Modern flat design with gradient colors
    - Colors: Match the blue gradient theme (#667eea to
  #764ba2)
    - Variations: Logo + text, icon only, Arabic version

  1.2 Visual Theme Enhancement

  - Background: Add subtle car/workshop patterns
  - Icons: Automotive-themed icons for each step
  - Color Palette: Professional automotive workshop
  colors
  - Typography: Bold, modern fonts suitable for workshop
   branding

  ---
  📋 PHASE 2: Modern Onboarding Wizard Architecture

  2.1 Step Structure (6 Steps)

  1. 🏁 Welcome & Company Overview
    - Workshop introduction with animated logo
    - Feature highlights carousel
    - Language selection (English/Arabic)
  2. 🏢 Workshop Information
    - Business name, address, contact details
    - Workshop type (general, specialist, etc.)
    - Operating hours and capacity
  3. 👤 Administrator Account
    - Admin user creation with avatar upload
    - Security settings and password
    - Contact information
  4. ⚙️ Operational Configuration
    - Service types offered (brake, engine, etc.)
    - Workshop bays setup
    - Technician roles configuration
  5. 💰 Financial & VAT Setup
    - Omani VAT configuration (5%)
    - Payment methods setup
    - Currency and pricing
  6. ✅ Review & Confirmation
    - Summary of all settings
    - Terms acceptance
    - Final setup completion

  2.2 Modern UI Components

  - Progress Indicator: Animated progress bar with car
  icons
  - Form Design: Glass-morphism cards with smooth
  transitions
  - Animations: Slide transitions, micro-interactions
  - Validation: Real-time form validation with Arabic
  support
  - Navigation: Smooth step transitions with breadcrumbs

  ---
  📋 PHASE 3: Beautiful & Modern Design System

  3.1 Visual Design

  - Layout: Split-screen design (progress + content)
  - Background: Animated automotive workshop scene
  - Cards: Floating glass panels with shadow effects
  - Buttons: Modern gradient buttons with hover effects
  - Inputs: Floating label inputs with Arabic RTL
  support

  3.2 Interactive Elements

  - Car Workshop Scene: SVG animation showing workshop
  activity
  - Step Icons: Animated automotive icons for each step
  - Progress: Car moving along a road/timeline
  - Feedback: Success animations and celebration effects

  3.3 Mobile Optimization

  - Responsive: Mobile-first approach
  - Touch: Touch-friendly form controls
  - Gestures: Swipe navigation between steps
  - Performance: Optimized animations for mobile

  ---
  📋 PHASE 4: Login Page Integration

  4.1 Modern Login Design

  - Split Layout: Workshop branding left, login form
  right
  - Background: Blurred workshop image or video
  - Form: Clean, minimal login form
  - Features: Remember me, forgot password, biometric
  auth

  4.2 User Flow

  Onboarding Complete → Celebration Animation →
  Auto-redirect (3s) → Login Page
                                      ↓
                              Pass setup data to login
  form
                                      ↓
                                Pre-fill admin username

  4.3 Authentication Flow

  - First Login: Use credentials from onboarding
  - Session Management: Secure token handling
  - Dashboard Redirect: After successful login
  - Arabic Support: RTL login form

  ---
  📋 PHASE 5: Technical Implementation

  5.1 Component Structure

  src/
  ├── components/
  │   ├── onboarding/
  │   │   ├── OnboardingWizard.vue (Main container)
  │   │   ├── steps/
  │   │   │   ├── WelcomeStep.vue
  │   │   │   ├── WorkshopInfoStep.vue
  │   │   │   ├── AdminAccountStep.vue
  │   │   │   ├── OperationalStep.vue
  │   │   │   ├── FinancialStep.vue
  │   │   │   └── ReviewStep.vue
  │   │   ├── common/
  │   │   │   ├── ProgressIndicator.vue
  │   │   │   ├── StepNavigation.vue
  │   │   │   └── FormField.vue
  │   └── auth/
  │       └── ModernLogin.vue
  ├── assets/
  │   ├── icons/ (Car workshop SVG icons)
  │   ├── animations/ (Lottie/CSS animations)
  │   └── images/ (Workshop backgrounds)
  └── utils/
      ├── onboarding-api.ts
      ├── validation.ts
      └── arabic-utils.ts

  5.2 Data Management

  - State Management: Pinia for wizard state
  - Data Persistence: localStorage for step progress
  - Validation: Real-time validation with Yup
  - API Integration: Frappe backend integration

  5.3 Features Implementation

  - Form Wizards: Multi-step form handling
  - File Upload: Logo and document uploads
  - Real-time Preview: Live preview of settings
  - Auto-save: Progress saving between steps
  - Accessibility: WCAG compliance for Arabic/English

  ---
  📋 PHASE 6: Advanced Features

  6.1 Enhanced UX

  - Smart Defaults: Pre-filled common workshop settings
  - Guided Tour: Interactive tooltips and hints
  - Help System: Context-sensitive help
  - Error Recovery: Graceful error handling

  6.2 Arabic/RTL Excellence

  - Typography: Proper Arabic font rendering
  - Layout: Perfect RTL layout adaptation
  - Numbers: Arabic-Indic numerals support
  - Dates: Hijri calendar integration

  6.3 Performance & Polish

  - Animations: 60fps smooth animations
  - Loading States: Beautiful loading indicators
  - Offline Support: Progressive Web App features
  - SEO: Meta tags and structured data

  ---
  🎯 Implementation Timeline

  | Phase   | Duration | Priority | Deliverable
           |
  |---------|----------|----------|---------------------
  ---------|
  | Phase 1 | 2 hours  | High     | Car workshop logo &
  branding |
  | Phase 2 | 4 hours  | High     | 6-step wizard
  structure      |
  | Phase 3 | 6 hours  | High     | Modern UI components
           |
  | Phase 4 | 3 hours  | High     | Login page
  integration       |
  | Phase 5 | 4 hours  | Medium   | Technical refinement
           |
  | Phase 6 | 3 hours  | Low      | Advanced features
           |

  Total Estimated Time: 22 hours

  ---
  🚀 Expected Result

  A world-class onboarding experience featuring:
  - ✅ Beautiful car workshop themed design
  - ✅ Smooth 6-step wizard with real forms
  - ✅ Perfect Arabic/English bilingual support
  - ✅ Modern glass-morphism UI design
  - ✅ Seamless flow to login page
  - ✅ Mobile-responsive and accessible
  - ✅ Integration with Frappe backend

  Do you approve this plan? If yes, I'll start 
  implementing it step by step! 🚗⚙️