/**
 * Router Configuration - Universal Workshop Frontend V2
 */

import { createRouter, createWebHistory } from 'vue-router'
import OnboardingWizard from '@/components/setup/OnboardingWizard.vue'
import ModernLogin from '@/components/auth/ModernLogin.vue'

const routes = [
  {
    path: '/',
    redirect: '/onboarding'
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: OnboardingWizard,
    meta: {
      title: 'Setup Your Workshop',
      requiresAuth: false
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: ModernLogin,
    props: (route: any) => ({
      isFirstLogin: route.query.firstLogin === 'true',
      workshopInfo: route.query.workshop ? {
        name: route.query.workshop,
        code: route.query.workshopCode || '',
        adminUsername: route.query.adminUsername || ''
      } : null
    }),
    meta: {
      title: 'Sign In',
      requiresAuth: false
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: 'Dashboard',
      requiresAuth: true
    }
  }
]

const router = createRouter({
  history: createWebHistory('/frontend_v2/'),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Set page title
  document.title = to.meta?.title ? 
    `${to.meta.title} - Universal Workshop` : 
    'Universal Workshop'
  
  // Check authentication if required
  if (to.meta?.requiresAuth) {
    // Check if user is authenticated
    const isAuthenticated = checkAuthentication()
    
    if (!isAuthenticated) {
      next('/login')
      return
    }
  }
  
  next()
})

// Helper function to check authentication
function checkAuthentication(): boolean {
  // In a real app, this would check for valid session/token
  if (typeof window !== 'undefined' && window.frappe) {
    return window.frappe.session?.user !== 'Guest'
  }
  return false
}

export default router