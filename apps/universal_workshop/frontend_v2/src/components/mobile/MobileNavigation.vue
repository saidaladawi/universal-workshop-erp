<!--
  MobileNavigation Component - Universal Workshop Frontend V2
  
  Mobile-optimized navigation component with bottom tab bar, hamburger menu,
  and gesture support for workshop management on mobile devices.
-->

<template>
  <div :class="navigationClasses" :dir="isRTL ? 'rtl' : 'ltr'">
    <!-- Top Navigation Bar -->
    <div v-if="showTopBar" class="mobile-nav__top-bar">
      <div class="mobile-nav__top-content">
        <!-- Menu Toggle -->
        <button
          class="mobile-nav__menu-toggle"
          @click="toggleSideMenu"
          :aria-label="isRTL ? 'فتح القائمة' : 'Open menu'"
        >
          <UWIcon :name="sideMenuOpen ? 'x' : 'menu'" size="md" />
        </button>

        <!-- Page Title -->
        <div class="mobile-nav__page-title">
          <h1 class="mobile-nav__title">
            {{ isRTL && currentPage.titleAr ? currentPage.titleAr : currentPage.title }}
          </h1>
          <p v-if="currentPage.subtitle" class="mobile-nav__subtitle">
            {{ isRTL && currentPage.subtitleAr ? currentPage.subtitleAr : currentPage.subtitle }}
          </p>
        </div>

        <!-- Action Buttons -->
        <div class="mobile-nav__actions">
          <button
            v-for="action in topActions"
            :key="action.key"
            class="mobile-nav__action-btn"
            @click="handleActionClick(action)"
            :aria-label="isRTL && action.labelAr ? action.labelAr : action.label"
          >
            <UWIcon :name="action.icon" size="sm" />
            <UWBadge 
              v-if="action.badge"
              :content="action.badge"
              variant="error"
              size="xs"
              class="mobile-nav__action-badge"
            />
          </button>
        </div>
      </div>
    </div>

    <!-- Side Menu Overlay -->
    <Transition name="fade">
      <div 
        v-if="sideMenuOpen" 
        class="mobile-nav__overlay"
        @click="closeSideMenu"
      />
    </Transition>

    <!-- Side Menu -->
    <Transition name="slide-menu">
      <nav v-if="sideMenuOpen" class="mobile-nav__side-menu">
        <div class="mobile-nav__side-header">
          <div class="mobile-nav__user-info">
            <UWAvatar 
              :user="currentUser" 
              size="lg"
            />
            <div class="mobile-nav__user-details">
              <div class="mobile-nav__user-name">
                {{ isRTL && currentUser.nameAr ? currentUser.nameAr : currentUser.name }}
              </div>
              <div class="mobile-nav__user-role">
                {{ getUserRoleText() }}
              </div>
            </div>
          </div>
          
          <button
            class="mobile-nav__close-btn"
            @click="closeSideMenu"
            :aria-label="isRTL ? 'إغلاق القائمة' : 'Close menu'"
          >
            <UWIcon name="x" size="md" />
          </button>
        </div>

        <div class="mobile-nav__side-content">
          <!-- Main Navigation Items -->
          <div class="mobile-nav__nav-section">
            <h3 class="mobile-nav__section-title">
              {{ isRTL ? 'التنقل الرئيسي' : 'Main Navigation' }}
            </h3>
            
            <div
              v-for="item in mainNavItems"
              :key="item.key"
              class="mobile-nav__nav-item"
              :class="{ 'mobile-nav__nav-item--active': item.key === currentPage.key }"
              @click="handleNavItemClick(item)"
            >
              <UWIcon :name="item.icon" size="md" />
              <span class="mobile-nav__nav-label">
                {{ isRTL && item.labelAr ? item.labelAr : item.label }}
              </span>
              <UWBadge 
                v-if="item.badge"
                :content="item.badge"
                variant="primary"
                size="xs"
              />
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="mobile-nav__nav-section">
            <h3 class="mobile-nav__section-title">
              {{ isRTL ? 'الإجراءات السريعة' : 'Quick Actions' }}
            </h3>
            
            <div
              v-for="action in quickActions"
              :key="action.key"
              class="mobile-nav__quick-action"
              @click="handleQuickAction(action)"
            >
              <UWIcon :name="action.icon" size="md" :color="action.color" />
              <span class="mobile-nav__action-label">
                {{ isRTL && action.labelAr ? action.labelAr : action.label }}
              </span>
            </div>
          </div>
        </div>

        <div class="mobile-nav__side-footer">
          <!-- Settings -->
          <div class="mobile-nav__settings">
            <button
              class="mobile-nav__settings-btn"
              @click="handleSettings"
            >
              <UWIcon name="settings" size="md" />
              <span>{{ isRTL ? 'الإعدادات' : 'Settings' }}</span>
            </button>
          </div>

          <!-- Logout -->
          <div class="mobile-nav__logout">
            <button
              class="mobile-nav__logout-btn"
              @click="handleLogout"
            >
              <UWIcon name="log-out" size="md" />
              <span>{{ isRTL ? 'تسجيل الخروج' : 'Logout' }}</span>
            </button>
          </div>
        </div>
      </nav>
    </Transition>

    <!-- Bottom Navigation -->
    <nav v-if="showBottomNav" class="mobile-nav__bottom-nav">
      <div
        v-for="item in bottomNavItems"
        :key="item.key"
        class="mobile-nav__bottom-item"
        :class="{ 'mobile-nav__bottom-item--active': item.key === currentPage.key }"
        @click="handleNavItemClick(item)"
      >
        <div class="mobile-nav__bottom-icon">
          <UWIcon :name="item.icon" size="md" />
          <UWBadge 
            v-if="item.badge"
            :content="item.badge"
            variant="error"
            size="xs"
            class="mobile-nav__bottom-badge"
          />
        </div>
        <span class="mobile-nav__bottom-label">
          {{ isRTL && item.labelAr ? item.labelAr : item.label }}
        </span>
      </div>
    </nav>

    <!-- Floating Action Button -->
    <Transition name="fab">
      <button
        v-if="showFab && fabAction"
        class="mobile-nav__fab"
        @click="handleFabClick"
        :aria-label="isRTL && fabAction.labelAr ? fabAction.labelAr : fabAction.label"
      >
        <UWIcon :name="fabAction.icon" size="lg" color="white" />
      </button>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, inject, watch } from 'vue'
import { UWIcon, UWBadge, UWAvatar } from '@/components/primitives'

// Types
interface NavigationItem {
  key: string
  label: string
  labelAr?: string
  icon: string
  badge?: string | number
  color?: string
}

interface ActionItem {
  key: string
  label: string
  labelAr?: string
  icon: string
  badge?: string | number
  color?: string
}

interface PageInfo {
  key: string
  title: string
  titleAr?: string
  subtitle?: string
  subtitleAr?: string
}

interface User {
  name: string
  nameAr?: string
  role: string
  roleAr?: string
  avatar?: string
}

export interface MobileNavigationProps {
  currentPage: PageInfo
  currentUser: User
  mainNavItems?: NavigationItem[]
  bottomNavItems?: NavigationItem[]
  quickActions?: ActionItem[]
  topActions?: ActionItem[]
  fabAction?: ActionItem
  showTopBar?: boolean
  showBottomNav?: boolean
  showFab?: boolean
  variant?: 'default' | 'minimal' | 'tabs'
}

export interface MobileNavigationEmits {
  'nav-item-click': [item: NavigationItem]
  'action-click': [action: ActionItem]
  'quick-action': [action: ActionItem]
  'fab-click': []
  'settings': []
  'logout': []
}

const props = withDefaults(defineProps<MobileNavigationProps>(), {
  showTopBar: true,
  showBottomNav: true,
  showFab: false,
  variant: 'default',
  mainNavItems: () => [],
  bottomNavItems: () => [],
  quickActions: () => [],
  topActions: () => []
})

const emit = defineEmits<MobileNavigationEmits>()

// Injected context
const isRTL = inject('isRTL', false)

// Local state
const sideMenuOpen = ref(false)

// Computed properties
const navigationClasses = computed(() => [
  'mobile-nav',
  `mobile-nav--${props.variant}`,
  {
    'mobile-nav--rtl': isRTL,
    'mobile-nav--side-open': sideMenuOpen.value,
    'mobile-nav--with-top': props.showTopBar,
    'mobile-nav--with-bottom': props.showBottomNav,
    'mobile-nav--with-fab': props.showFab
  }
])

// Methods
const toggleSideMenu = () => {
  sideMenuOpen.value = !sideMenuOpen.value
}

const closeSideMenu = () => {
  sideMenuOpen.value = false
}

const getUserRoleText = () => {
  return isRTL && props.currentUser.roleAr 
    ? props.currentUser.roleAr 
    : props.currentUser.role
}

const handleNavItemClick = (item: NavigationItem) => {
  closeSideMenu()
  emit('nav-item-click', item)
}

const handleActionClick = (action: ActionItem) => {
  emit('action-click', action)
}

const handleQuickAction = (action: ActionItem) => {
  closeSideMenu()
  emit('quick-action', action)
}

const handleFabClick = () => {
  emit('fab-click')
}

const handleSettings = () => {
  closeSideMenu()
  emit('settings')
}

const handleLogout = () => {
  closeSideMenu()
  emit('logout')
}

// Close side menu when clicking outside
watch(sideMenuOpen, (isOpen) => {
  if (isOpen) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})
</script>

<style lang="scss" scoped>
.mobile-nav {
  --nav-height: 56px;
  --bottom-nav-height: 60px;
  --side-menu-width: 280px;
  --fab-size: 56px;
  
  position: relative;
  height: 100vh;
  
  // RTL support
  &--rtl {
    direction: rtl;
    text-align: right;
  }
  
  &--side-open {
    .mobile-nav__overlay {
      display: block;
    }
  }
}

.mobile-nav__top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--nav-height);
  background: var(--color-background-elevated);
  border-bottom: 1px solid var(--color-border-subtle);
  z-index: 100;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.mobile-nav__top-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 var(--spacing-4);
  gap: var(--spacing-3);
}

.mobile-nav__menu-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
  
  &:hover {
    background: var(--color-background-subtle);
  }
}

.mobile-nav__page-title {
  flex: 1;
  min-width: 0;
}

.mobile-nav__title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-nav__subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-nav__actions {
  display: flex;
  gap: var(--spacing-2);
}

.mobile-nav__action-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
  
  &:hover {
    background: var(--color-background-subtle);
  }
}

.mobile-nav__action-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  
  .mobile-nav--rtl & {
    right: auto;
    left: -2px;
  }
}

.mobile-nav__overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.mobile-nav__side-menu {
  position: fixed;
  top: 0;
  left: 0;
  width: var(--side-menu-width);
  height: 100vh;
  background: var(--color-background-elevated);
  z-index: 300;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
  
  .mobile-nav--rtl & {
    left: auto;
    right: 0;
  }
}

.mobile-nav__side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-6) var(--spacing-4) var(--spacing-4);
  border-bottom: 1px solid var(--color-border-subtle);
}

.mobile-nav__user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  flex: 1;
}

.mobile-nav__user-details {
  flex: 1;
  min-width: 0;
}

.mobile-nav__user-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-nav__user-role {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-nav__close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  
  &:hover {
    background: var(--color-background-subtle);
    color: var(--color-text-primary);
  }
}

.mobile-nav__side-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-4);
}

.mobile-nav__nav-section {
  margin-bottom: var(--spacing-6);
}

.mobile-nav__section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--spacing-3) 0;
}

.mobile-nav__nav-item,
.mobile-nav__quick-action {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--color-background-subtle);
  }
  
  &:not(:last-child) {
    margin-bottom: var(--spacing-1);
  }
}

.mobile-nav__nav-item--active {
  background: var(--color-primary-background);
  color: var(--color-primary);
  
  .mobile-nav__nav-label {
    font-weight: var(--font-weight-semibold);
  }
}

.mobile-nav__nav-label,
.mobile-nav__action-label {
  flex: 1;
  font-size: var(--font-size-md);
  color: var(--color-text-primary);
}

.mobile-nav__side-footer {
  padding: var(--spacing-4);
  border-top: 1px solid var(--color-border-subtle);
}

.mobile-nav__settings-btn,
.mobile-nav__logout-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  width: 100%;
  padding: var(--spacing-3);
  background: none;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  cursor: pointer;
  text-align: left;
  
  .mobile-nav--rtl & {
    text-align: right;
  }
  
  &:hover {
    background: var(--color-background-subtle);
  }
}

.mobile-nav__logout-btn {
  color: var(--color-error);
  margin-top: var(--spacing-2);
  
  &:hover {
    background: var(--color-error-background);
  }
}

.mobile-nav__bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--bottom-nav-height);
  background: var(--color-background-elevated);
  border-top: 1px solid var(--color-border-subtle);
  display: flex;
  z-index: 100;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.mobile-nav__bottom-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-1);
  padding: var(--spacing-2);
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--color-background-subtle);
  }
  
  &--active {
    color: var(--color-primary);
    
    .mobile-nav__bottom-label {
      font-weight: var(--font-weight-semibold);
    }
  }
}

.mobile-nav__bottom-icon {
  position: relative;
}

.mobile-nav__bottom-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  
  .mobile-nav--rtl & {
    right: auto;
    left: -4px;
  }
}

.mobile-nav__bottom-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.mobile-nav__bottom-item--active .mobile-nav__bottom-label {
  color: var(--color-primary);
}

.mobile-nav__fab {
  position: fixed;
  bottom: calc(var(--bottom-nav-height) + var(--spacing-4));
  right: var(--spacing-4);
  width: var(--fab-size);
  height: var(--fab-size);
  background: var(--color-primary);
  border: none;
  border-radius: 50%;
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  z-index: 50;
  transition: all 0.3s ease;
  
  .mobile-nav--rtl & {
    right: auto;
    left: var(--spacing-4);
  }
  
  &:hover {
    transform: scale(1.1);
    box-shadow: var(--shadow-xl);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

// Animations
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-menu-enter-active,
.slide-menu-leave-active {
  transition: transform 0.3s ease;
}

.slide-menu-enter-from,
.slide-menu-leave-to {
  transform: translateX(-100%);
  
  .mobile-nav--rtl & {
    transform: translateX(100%);
  }
}

.fab-enter-active,
.fab-leave-active {
  transition: all 0.3s ease;
}

.fab-enter-from,
.fab-leave-to {
  opacity: 0;
  transform: scale(0);
}

// Safe area support for devices with notches
@supports (padding: max(0px)) {
  .mobile-nav__top-bar {
    padding-top: max(0px, env(safe-area-inset-top));
    height: calc(var(--nav-height) + max(0px, env(safe-area-inset-top)));
  }
  
  .mobile-nav__bottom-nav {
    padding-bottom: max(0px, env(safe-area-inset-bottom));
    height: calc(var(--bottom-nav-height) + max(0px, env(safe-area-inset-bottom)));
  }
  
  .mobile-nav__fab {
    bottom: calc(var(--bottom-nav-height) + var(--spacing-4) + max(0px, env(safe-area-inset-bottom)));
  }
}

// Landscape orientation adjustments
@media (orientation: landscape) and (max-height: 500px) {
  .mobile-nav__side-menu {
    width: 240px;
  }
  
  .mobile-nav__side-header {
    padding: var(--spacing-4) var(--spacing-3) var(--spacing-3);
  }
  
  .mobile-nav__side-content {
    padding: var(--spacing-3);
  }
}
</style>