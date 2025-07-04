/**
 * Mobile Components Index - Universal Workshop Frontend V2
 * Comprehensive index for all mobile components with proper exports,
 * component registration, and TypeScript support.
 */

// Import mobile components
export { default as CustomerMobilePortal } from './CustomerMobilePortal.vue'
export { default as TechnicianMobileInterface } from './TechnicianMobileInterface.vue'
export { default as RealTimeChatInterface } from './RealTimeChatInterface.vue'
export { default as MobileNavigation } from './MobileNavigation.vue'
export { default as MobileServiceCard } from './MobileServiceCard.vue'
export { default as MobileDashboard } from './MobileDashboard.vue'
export { default as PullToRefreshIndicator } from './PullToRefreshIndicator.vue'

// Export touch gestures composable
export {
    useTouchGestures,
    useSwipeGestures,
    usePinchGestures,
    useDragGestures,
    useTapGestures,
    isTouchDevice,
    isIOS,
    isAndroid,
    supportsPinchZoom,
    getViewportSize
} from '@/composables/useTouchGestures'

// Export pull-to-refresh composable
export {
    default as usePullToRefresh,
    defaultPullToRefreshMessages,
    pullToRefreshClasses,
    createPullToRefreshStyles
} from '@/composables/usePullToRefresh'

// Export component types
export type { CustomerMobilePortalProps, CustomerMobilePortalEmits } from './CustomerMobilePortal.vue'
export type { TechnicianMobileInterfaceProps, TechnicianMobileInterfaceEmits } from './TechnicianMobileInterface.vue'
export type { RealTimeChatInterfaceProps, RealTimeChatInterfaceEmits } from './RealTimeChatInterface.vue'
export type { MobileNavigationProps, MobileNavigationEmits } from './MobileNavigation.vue'
export type { MobileServiceCardProps, MobileServiceCardEmits } from './MobileServiceCard.vue'
export type { MobileDashboardProps, MobileDashboardEmits } from './MobileDashboard.vue'
export type { PullToRefreshIndicatorProps } from './PullToRefreshIndicator.vue'

// Export pull-to-refresh types
export type {
    PullToRefreshOptions,
    PullToRefreshState
} from '@/composables/usePullToRefresh'

// Component registry for global registration
export const mobileComponents = {
    CustomerMobilePortal: () => import('./CustomerMobilePortal.vue'),
    TechnicianMobileInterface: () => import('./TechnicianMobileInterface.vue'),
    RealTimeChatInterface: () => import('./RealTimeChatInterface.vue'),
    MobileNavigation: () => import('./MobileNavigation.vue'),
    MobileServiceCard: () => import('./MobileServiceCard.vue'),
    MobileDashboard: () => import('./MobileDashboard.vue'),
    PullToRefreshIndicator: () => import('./PullToRefreshIndicator.vue'),
} as const

// Mobile component categories
export const mobileComponentCategories = {
    customer: {
        CustomerMobilePortal: () => import('./CustomerMobilePortal.vue'),
    },
    technician: {
        TechnicianMobileInterface: () => import('./TechnicianMobileInterface.vue'),
    },
    communication: {
        RealTimeChatInterface: () => import('./RealTimeChatInterface.vue'),
    },
    navigation: {
        MobileNavigation: () => import('./MobileNavigation.vue'),
        MobileDashboard: () => import('./MobileDashboard.vue'),
    },
    ui: {
        MobileServiceCard: () => import('./MobileServiceCard.vue'),
        PullToRefreshIndicator: () => import('./PullToRefreshIndicator.vue'),
    }
} as const

// Install function for Vue plugin
export function installMobileComponents(app: any) {
    Object.entries(mobileComponents).forEach(([name, component]) => {
        app.component(name, component)
    })
}

// Mobile component metadata
export const mobileComponentMeta = {
    CustomerMobilePortal: {
        name: 'CustomerMobilePortal',
        category: 'customer',
        description: 'Comprehensive mobile portal for customers with real-time service tracking',
        descriptionAr: 'بوابة محمولة شاملة للعملاء مع تتبع الخدمة المباشر',
        features: [
            'Real-time service tracking',
            'Arabic interface support',
            'Push notifications',
            'Offline capabilities',
            'Service history',
            'Quick actions'
        ],
        featuresAr: [
            'تتبع الخدمة المباشر',
            'دعم الواجهة العربية',
            'الإشعارات الفورية',
            'إمكانيات العمل بدون اتصال',
            'تاريخ الخدمات',
            'الإجراءات السريعة'
        ],
        props: {
            customerId: { type: 'string', optional: true },
            realTimeEnabled: { type: 'boolean', default: true },
            offlineCapable: { type: 'boolean', default: true },
            pushNotificationsEnabled: { type: 'boolean', default: true }
        },
        events: [
            'service-selected',
            'appointment-booked',
            'emergency-contact',
            'notification-action'
        ]
    },

    TechnicianMobileInterface: {
        name: 'TechnicianMobileInterface',
        category: 'technician',
        description: 'Advanced mobile interface for technicians with touch-optimized workflows',
        descriptionAr: 'واجهة محمولة متقدمة للفنيين مع سير عمل محسن للمس',
        features: [
            'Touch-optimized interface',
            'Barcode scanning',
            'Voice recording',
            'Photo capture',
            'Time tracking',
            'Offline sync'
        ],
        featuresAr: [
            'واجهة محسنة للمس',
            'مسح الباركود',
            'التسجيل الصوتي',
            'التقاط الصور',
            'تتبع الوقت',
            'المزامنة بدون اتصال'
        ],
        props: {
            technicianId: { type: 'string', optional: true },
            realTimeEnabled: { type: 'boolean', default: true },
            offlineCapable: { type: 'boolean', default: true }
        },
        events: [
            'task-started',
            'task-completed',
            'photo-captured',
            'voice-recorded',
            'barcode-scanned'
        ]
    },

    RealTimeChatInterface: {
        name: 'RealTimeChatInterface',
        category: 'communication',
        description: 'Advanced real-time chat system with voice messages and translation',
        descriptionAr: 'نظام دردشة مباشرة متقدم مع الرسائل الصوتية والترجمة',
        features: [
            'Real-time messaging',
            'Voice messages',
            'Image sharing',
            'File attachments',
            'Auto translation',
            'Offline message queue'
        ],
        featuresAr: [
            'المراسلة المباشرة',
            'الرسائل الصوتية',
            'مشاركة الصور',
            'مرفقات الملفات',
            'الترجمة التلقائية',
            'قائمة انتظار الرسائل بدون اتصال'
        ],
        props: {
            chatId: { type: 'string', required: true },
            participantId: { type: 'string', required: true },
            serviceContext: { type: 'object', optional: true }
        },
        events: [
            'close',
            'voice-call',
            'video-call',
            'message-sent',
            'file-shared'
        ]
    },

    MobileNavigation: {
        name: 'MobileNavigation',
        category: 'navigation',
        description: 'Mobile-optimized navigation with bottom tabs, hamburger menu, and gesture support',
        descriptionAr: 'التنقل المحسن للجوال مع علامات تبويب سفلية وقائمة همبرغر ودعم الإيماءات',
        features: [
            'Bottom tab navigation',
            'Hamburger side menu',
            'Floating action button',
            'Gesture support',
            'RTL layout support',
            'Safe area handling'
        ],
        featuresAr: [
            'تنقل علامات التبويب السفلية',
            'قائمة جانبية همبرغر',
            'زر الإجراء العائم',
            'دعم الإيماءات',
            'دعم تخطيط RTL',
            'التعامل مع المنطقة الآمنة'
        ],
        props: {
            currentPage: { type: 'object', required: true },
            currentUser: { type: 'object', required: true },
            mainNavItems: { type: 'array', default: [] },
            bottomNavItems: { type: 'array', default: [] },
            showTopBar: { type: 'boolean', default: true },
            showBottomNav: { type: 'boolean', default: true },
            showFab: { type: 'boolean', default: false }
        },
        events: [
            'nav-item-click',
            'action-click',
            'quick-action',
            'fab-click',
            'settings',
            'logout'
        ]
    },

    MobileServiceCard: {
        name: 'MobileServiceCard',
        category: 'ui',
        description: 'Touch-optimized service order card with swipe gestures and comprehensive information display',
        descriptionAr: 'بطاقة طلب خدمة محسنة للمس مع إيماءات السحب وعرض شامل للمعلومات',
        features: [
            'Swipe gestures',
            'Touch feedback',
            'Status indicators',
            'Progress tracking',
            'Cost display',
            'Technician assignment'
        ],
        featuresAr: [
            'إيماءات السحب',
            'ردود فعل اللمس',
            'مؤشرات الحالة',
            'تتبع التقدم',
            'عرض التكلفة',
            'تعيين الفني'
        ],
        props: {
            orderNumber: { type: 'string', required: true },
            status: { type: 'string', required: true },
            priority: { type: 'string', required: true },
            serviceType: { type: 'string', required: true },
            vehicle: { type: 'object', required: true },
            customer: { type: 'object', required: true },
            swipeEnabled: { type: 'boolean', default: true },
            showProgress: { type: 'boolean', default: true }
        },
        events: [
            'click',
            'action',
            'swipe-complete',
            'swipe-edit'
        ]
    },

    MobileDashboard: {
        name: 'MobileDashboard',
        category: 'navigation',
        description: 'Comprehensive mobile dashboard with stats, quick actions, and service management',
        descriptionAr: 'لوحة تحكم محمولة شاملة مع الإحصائيات والإجراءات السريعة وإدارة الخدمات',
        features: [
            'Real-time statistics',
            'Quick action grid',
            'Service order filtering',
            'Pull-to-refresh',
            'Load more pagination',
            'Recent activity feed'
        ],
        featuresAr: [
            'الإحصائيات المباشرة',
            'شبكة الإجراءات السريعة',
            'تصفية طلبات الخدمة',
            'السحب للتحديث',
            'تحميل المزيد',
            'خلاصة النشاط الأخير'
        ],
        props: {
            currentUser: { type: 'object', required: true },
            headerStats: { type: 'array', default: [] },
            quickActionItems: { type: 'array', default: [] },
            services: { type: 'array', default: [] },
            recentActivities: { type: 'array', default: [] },
            servicesPerPage: { type: 'number', default: 10 }
        },
        events: [
            'navigation',
            'action',
            'quick-action',
            'service-click',
            'service-action',
            'stat-click',
            'activity-click',
            'load-more-services',
            'refresh'
        ]
    }
} as const

// Mobile utilities and helpers
export const mobileUtils = {
    // Check if device is mobile
    isMobileDevice(): boolean {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
    },

    // Check if device supports touch
    isTouchDevice(): boolean {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0
    },

    // Get device orientation
    getDeviceOrientation(): 'portrait' | 'landscape' {
        return window.innerHeight > window.innerWidth ? 'portrait' : 'landscape'
    },

    // Check if device is in standalone mode (PWA)
    isStandaloneMode(): boolean {
        return window.matchMedia('(display-mode: standalone)').matches ||
            (window.navigator as any).standalone === true
    },

    // Get safe area insets for notched devices
    getSafeAreaInsets(): { top: number; bottom: number; left: number; right: number } {
        const style = getComputedStyle(document.documentElement)
        return {
            top: parseInt(style.getPropertyValue('--safe-area-inset-top') || '0'),
            bottom: parseInt(style.getPropertyValue('--safe-area-inset-bottom') || '0'),
            left: parseInt(style.getPropertyValue('--safe-area-inset-left') || '0'),
            right: parseInt(style.getPropertyValue('--safe-area-inset-right') || '0')
        }
    },

    // Vibrate device if supported
    vibrate(pattern: number | number[]): boolean {
        if ('vibrate' in navigator) {
            navigator.vibrate(pattern)
            return true
        }
        return false
    },

    // Request device wake lock
    async requestWakeLock(): Promise<WakeLockSentinel | null> {
        if ('wakeLock' in navigator) {
            try {
                return await (navigator as any).wakeLock.request('screen')
            } catch (error) {
                console.warn('Wake lock request failed:', error)
            }
        }
        return null
    },

    // Check if device supports camera
    async supportsCameraAccess(): Promise<boolean> {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true })
            stream.getTracks().forEach(track => track.stop())
            return true
        } catch {
            return false
        }
    },

    // Check if device supports geolocation
    supportsGeolocation(): boolean {
        return 'geolocation' in navigator
    },

    // Get device pixel ratio
    getDevicePixelRatio(): number {
        return window.devicePixelRatio || 1
    },

    // Check if device supports push notifications
    supportsPushNotifications(): boolean {
        return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
    }
}

// Mobile-specific CSS classes
export const mobileCSSClasses = {
    container: 'mobile-container',
    header: 'mobile-header',
    content: 'mobile-content',
    footer: 'mobile-footer',
    fab: 'mobile-fab',
    bottomNav: 'mobile-bottom-nav',
    touchTarget: 'mobile-touch-target',
    swipeContainer: 'mobile-swipe-container',
    pullToRefresh: 'mobile-pull-to-refresh',
    safeArea: 'mobile-safe-area'
}

// Mobile breakpoints
export const mobileBreakpoints = {
    xs: '320px',
    sm: '375px',
    md: '414px',
    lg: '768px',
    xl: '1024px'
}

// Mobile component themes
export const mobileThemes = {
    light: {
        primary: '#3B82F6',
        secondary: '#6B7280',
        background: '#FFFFFF',
        surface: '#F9FAFB',
        text: '#111827',
        textSecondary: '#6B7280',
        border: '#E5E7EB',
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6'
    },
    dark: {
        primary: '#60A5FA',
        secondary: '#9CA3AF',
        background: '#111827',
        surface: '#1F2937',
        text: '#F9FAFB',
        textSecondary: '#9CA3AF',
        border: '#374151',
        success: '#34D399',
        warning: '#FBBF24',
        error: '#F87171',
        info: '#60A5FA'
    }
}

// Mobile accessibility helpers
export const mobileA11y = {
    // Add focus management for mobile
    manageFocus(element: HTMLElement): void {
        element.focus()
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
    },

    // Announce to screen readers
    announce(message: string): void {
        const announcement = document.createElement('div')
        announcement.setAttribute('aria-live', 'polite')
        announcement.setAttribute('aria-atomic', 'true')
        announcement.style.position = 'absolute'
        announcement.style.left = '-10000px'
        announcement.style.width = '1px'
        announcement.style.height = '1px'
        announcement.style.overflow = 'hidden'
        announcement.textContent = message

        document.body.appendChild(announcement)
        setTimeout(() => document.body.removeChild(announcement), 1000)
    },

    // Check if reduced motion is preferred
    prefersReducedMotion(): boolean {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    },

    // Check if high contrast is preferred
    prefersHighContrast(): boolean {
        return window.matchMedia('(prefers-contrast: high)').matches
    }
}

// All utilities are already exported above as const declarations

// Default export for convenience
export default {
    components: mobileComponents,
    categories: mobileComponentCategories,
    meta: mobileComponentMeta,
    utils: mobileUtils,
    cssClasses: mobileCSSClasses,
    breakpoints: mobileBreakpoints,
    themes: mobileThemes,
    a11y: mobileA11y,
    install: installMobileComponents
} 