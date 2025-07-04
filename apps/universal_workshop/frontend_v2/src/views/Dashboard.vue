<template>
  <div class="dashboard" :class="{ 'rtl': isRTL }">
    <!-- Dashboard Header -->
    <header class="dashboard-header">
      <div class="header-content">
        <div class="brand-section">
          <div class="logo-container">
            <div class="logo-circle">
              <svg viewBox="0 0 64 64" class="workshop-logo">
                <defs>
                  <linearGradient id="dashboardLogoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
                  </linearGradient>
                </defs>
                <circle cx="32" cy="32" r="30" fill="url(#dashboardLogoGradient)" />
                <path d="M20 28h24v8H20z" fill="white" opacity="0.9" />
                <circle cx="26" cy="38" r="4" fill="white" opacity="0.9" />
                <circle cx="38" cy="38" r="4" fill="white" opacity="0.9" />
                <path d="M24 20h16v6H24z" fill="white" opacity="0.7" />
              </svg>
            </div>
            <div class="brand-text">
              <h1 class="brand-name">{{ $t('Universal Workshop') }}</h1>
              <p class="brand-tagline">{{ workshopName || $t('Workshop Management System') }}</p>
            </div>
          </div>
        </div>
        
        <div class="user-section">
          <div class="user-info">
            <span class="user-name">{{ $t('Administrator') }}</span>
            <span class="user-role">{{ $t('System Admin') }}</span>
          </div>
          <button class="logout-btn" @click="handleLogout">
            <svg viewBox="0 0 24 24">
              <path d="M17 7L15.59 8.41L18.17 11H8V13H18.17L15.59 15.59L17 17L22 12L17 7ZM4 5H12V3H4C2.9 3 2 3.9 2 5V19C2 20.1 2.9 21 4 21H12V19H4V5Z" fill="currentColor"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Welcome Banner (only for first-time login) -->
    <div v-if="isWelcome" class="welcome-banner">
      <div class="welcome-content">
        <div class="welcome-icon">🎉</div>
        <div class="welcome-text">
          <h2>{{ $t('Welcome to Your Workshop!') }}</h2>
          <p>{{ $t('Your setup is complete and your workshop management system is ready to use.') }}</p>
        </div>
        <button @click="dismissWelcome" class="dismiss-btn">
          <svg viewBox="0 0 24 24">
            <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z" fill="currentColor"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Dashboard Content -->
    <main class="dashboard-main">
      <div class="dashboard-grid">
        <!-- Quick Actions -->
        <div class="dashboard-card quick-actions">
          <h3 class="card-title">{{ $t('Quick Actions') }}</h3>
          <div class="action-grid">
            <button class="action-btn">
              <div class="action-icon">🚗</div>
              <span>{{ $t('New Service Order') }}</span>
            </button>
            <button class="action-btn">
              <div class="action-icon">👤</div>
              <span>{{ $t('Add Customer') }}</span>
            </button>
            <button class="action-btn">
              <div class="action-icon">📦</div>
              <span>{{ $t('Inventory') }}</span>
            </button>
            <button class="action-btn">
              <div class="action-icon">📊</div>
              <span>{{ $t('Reports') }}</span>
            </button>
          </div>
        </div>

        <!-- Overview Stats -->
        <div class="dashboard-card stats-overview">
          <h3 class="card-title">{{ $t('Overview') }}</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon">🛠️</div>
              <div class="stat-content">
                <div class="stat-value">0</div>
                <div class="stat-label">{{ $t('Active Orders') }}</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">👥</div>
              <div class="stat-content">
                <div class="stat-value">0</div>
                <div class="stat-label">{{ $t('Customers') }}</div>
              </div>
            </div>
            <div class="stat-item">
              <div class="stat-icon">💰</div>
              <div class="stat-content">
                <div class="stat-value">0.000</div>
                <div class="stat-label">{{ $t('OMR Revenue') }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div class="dashboard-card recent-activity">
          <h3 class="card-title">{{ $t('Recent Activity') }}</h3>
          <div class="activity-list">
            <div class="activity-item empty-state">
              <div class="empty-icon">📝</div>
              <p>{{ $t('No recent activity. Start by creating your first service order!') }}</p>
            </div>
          </div>
        </div>

        <!-- Getting Started -->
        <div class="dashboard-card getting-started">
          <h3 class="card-title">{{ $t('Getting Started') }}</h3>
          <div class="checklist">
            <div class="checklist-item completed">
              <div class="check-icon">✓</div>
              <span>{{ $t('Complete workshop setup') }}</span>
            </div>
            <div class="checklist-item">
              <div class="check-icon">○</div>
              <span>{{ $t('Add your first customer') }}</span>
            </div>
            <div class="checklist-item">
              <div class="check-icon">○</div>
              <span>{{ $t('Configure inventory items') }}</span>
            </div>
            <div class="checklist-item">
              <div class="check-icon">○</div>
              <span>{{ $t('Create service order') }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { useArabicUtils } from '@/composables/useArabicUtils'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { isRTL } = useArabicUtils()

// State
const workshopName = ref('')
const isWelcome = ref(false)

// Computed
const isFirstLogin = computed(() => route.query.welcome === 'true')

// Methods
const handleLogout = () => {
  // Handle logout logic
  router.push('/login')
}

const dismissWelcome = () => {
  isWelcome.value = false
  // Remove welcome query parameter
  router.replace({ query: {} })
}

// Lifecycle
onMounted(() => {
  isWelcome.value = isFirstLogin.value
  
  // In a real app, you would fetch workshop data here
  workshopName.value = 'Universal Workshop'
})
</script>

<style scoped lang="scss">
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

  &.rtl {
    direction: rtl;
    font-family: 'Tajawal', 'Inter', sans-serif;
  }
}

.dashboard-header {
  background: white;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.brand-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-container {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-circle {
  width: 48px;
  height: 48px;
  
  .workshop-logo {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  }
}

.brand-text {
  text-align: left;
  
  .brand-name {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1a202c;
    margin: 0;
  }
  
  .brand-tagline {
    font-size: 0.875rem;
    color: #64748b;
    margin: 0;
  }
}

.user-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  text-align: right;
  
  .user-name {
    display: block;
    font-weight: 600;
    color: #1a202c;
  }
  
  .user-role {
    display: block;
    font-size: 0.875rem;
    color: #64748b;
  }
}

.logout-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s ease;
  
  &:hover {
    background: #f1f5f9;
    color: #e53e3e;
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
}

.welcome-banner {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 2rem;
  margin: 2rem;
  border-radius: 16px;
  position: relative;
  overflow: hidden;
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 1rem;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-icon {
  font-size: 3rem;
}

.welcome-text {
  flex: 1;
  
  h2 {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0 0 0.5rem 0;
  }
  
  p {
    margin: 0;
    opacity: 0.9;
  }
}

.dismiss-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  cursor: pointer;
  color: white;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.3);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
}

.dashboard-main {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.dashboard-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a202c;
  margin: 0 0 1.5rem 0;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.action-btn {
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.5rem 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  
  &:hover {
    border-color: #667eea;
    background: #f0f9ff;
    transform: translateY(-2px);
  }
  
  .action-icon {
    font-size: 2rem;
  }
  
  span {
    font-weight: 500;
    color: #374151;
    text-align: center;
  }
}

.stats-grid {
  display: grid;
  gap: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 12px;
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a202c;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.empty-state {
  text-align: center;
  padding: 2rem 1rem;
  color: #64748b;
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  
  &.completed {
    .check-icon {
      background: #10b981;
      color: white;
    }
  }
}

.check-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .header-content {
    padding: 1rem;
  }
  
  .dashboard-main {
    padding: 1rem;
  }
  
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .action-grid {
    grid-template-columns: 1fr;
  }
  
  .welcome-content {
    flex-direction: column;
    text-align: center;
  }
}
</style>