/**
 * Pull-to-Refresh Composable - Universal Workshop Frontend V2
 * 
 * A comprehensive composable for implementing pull-to-refresh functionality
 * on mobile devices with smooth animations and customizable behavior.
 */

import { ref, computed, onMounted, onUnmounted, type Ref } from 'vue'

// Types
export interface PullToRefreshOptions {
  threshold?: number // Distance to trigger refresh (in pixels)
  maxDistance?: number // Maximum pull distance
  resistance?: number // Resistance factor (0-1, lower = more resistance)
  refreshFunction?: () => Promise<void> | void
  disabled?: boolean
  damping?: number // Animation damping factor
  snapBackDuration?: number // Snap back animation duration (ms)
  triggerHaptic?: boolean // Trigger haptic feedback on trigger
}

export interface PullToRefreshState {
  isPulling: boolean
  isRefreshing: boolean
  pullDistance: number
  canRefresh: boolean
  progress: number // 0-1 progress indicator
}

export function usePullToRefresh(
  element: Ref<HTMLElement | null>,
  options: PullToRefreshOptions = {}
) {
  // Default options
  const opts = {
    threshold: 80,
    maxDistance: 120,
    resistance: 0.5,
    disabled: false,
    damping: 0.6,
    snapBackDuration: 300,
    triggerHaptic: true,
    ...options
  }

  // State
  const state = ref<PullToRefreshState>({
    isPulling: false,
    isRefreshing: false,
    pullDistance: 0,
    canRefresh: false,
    progress: 0
  })

  // Internal state
  const startY = ref(0)
  const currentY = ref(0)
  const isScrollable = ref(true)
  const refreshTriggered = ref(false)

  // Computed
  const isActive = computed(() => state.value.isPulling || state.value.isRefreshing)
  const pullProgress = computed(() => 
    Math.min(state.value.pullDistance / opts.threshold, 1)
  )
  const rotationDegrees = computed(() => pullProgress.value * 180)
  
  // Helper functions
  const hasReachedTop = (): boolean => {
    if (!element.value) return false
    return element.value.scrollTop <= 0
  }

  const applyResistance = (distance: number): number => {
    return distance * Math.pow(opts.resistance, distance / opts.threshold)
  }

  const triggerHapticFeedback = (): void => {
    if (opts.triggerHaptic && 'vibrate' in navigator) {
      navigator.vibrate(50)
    }
  }

  const updatePullDistance = (deltaY: number): void => {
    if (deltaY <= 0) {
      state.value.pullDistance = 0
      state.value.canRefresh = false
      state.value.progress = 0
      return
    }

    // Apply resistance
    const resistedDistance = applyResistance(deltaY)
    
    // Clamp to max distance
    state.value.pullDistance = Math.min(resistedDistance, opts.maxDistance)
    
    // Calculate progress (0-1)
    state.value.progress = Math.min(state.value.pullDistance / opts.threshold, 1)
    
    // Check if can refresh
    const wasCanRefresh = state.value.canRefresh
    state.value.canRefresh = state.value.pullDistance >= opts.threshold
    
    // Trigger haptic feedback when threshold is reached
    if (!wasCanRefresh && state.value.canRefresh) {
      triggerHapticFeedback()
    }
  }

  const snapBack = (): void => {
    if (!element.value) return

    const startDistance = state.value.pullDistance
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / opts.snapBackDuration, 1)
      
      // Easing function (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3)
      
      const currentDistance = startDistance * (1 - easeOut)
      state.value.pullDistance = currentDistance
      state.value.progress = Math.min(currentDistance / opts.threshold, 1)

      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        state.value.pullDistance = 0
        state.value.progress = 0
        state.value.isPulling = false
        state.value.canRefresh = false
      }
    }

    requestAnimationFrame(animate)
  }

  const executeRefresh = async (): Promise<void> => {
    if (!opts.refreshFunction) {
      snapBack()
      return
    }

    state.value.isRefreshing = true
    refreshTriggered.value = true

    try {
      await opts.refreshFunction()
    } catch (error) {
      console.warn('Pull to refresh function failed:', error)
    } finally {
      state.value.isRefreshing = false
      refreshTriggered.value = false
      snapBack()
    }
  }

  // Event handlers
  const handleTouchStart = (event: TouchEvent): void => {
    if (opts.disabled || !hasReachedTop()) return

    startY.value = event.touches[0].clientY
    currentY.value = startY.value
    isScrollable.value = true
  }

  const handleTouchMove = (event: TouchEvent): void => {
    if (opts.disabled || refreshTriggered.value) return

    currentY.value = event.touches[0].clientY
    const deltaY = currentY.value - startY.value

    // Only handle downward pulls when at top
    if (deltaY > 0 && hasReachedTop()) {
      event.preventDefault()
      
      if (!state.value.isPulling) {
        state.value.isPulling = true
      }

      updatePullDistance(deltaY)
      isScrollable.value = false
    } else if (state.value.isPulling && deltaY <= 0) {
      // User is pulling up while in pull state
      updatePullDistance(0)
    }
  }

  const handleTouchEnd = (): void => {
    if (opts.disabled || !state.value.isPulling) return

    if (state.value.canRefresh && !state.value.isRefreshing) {
      executeRefresh()
    } else {
      snapBack()
    }

    isScrollable.value = true
  }

  // Mouse events for desktop testing
  const handleMouseDown = (event: MouseEvent): void => {
    if (opts.disabled || !hasReachedTop()) return

    startY.value = event.clientY
    currentY.value = startY.value
    
    const handleMouseMove = (e: MouseEvent) => {
      currentY.value = e.clientY
      const deltaY = currentY.value - startY.value

      if (deltaY > 0 && hasReachedTop()) {
        if (!state.value.isPulling) {
          state.value.isPulling = true
        }
        updatePullDistance(deltaY)
      }
    }

    const handleMouseUp = () => {
      if (state.value.isPulling) {
        if (state.value.canRefresh && !state.value.isRefreshing) {
          executeRefresh()
        } else {
          snapBack()
        }
      }
      
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  // Lifecycle
  onMounted(() => {
    if (element.value) {
      element.value.addEventListener('touchstart', handleTouchStart, { passive: false })
      element.value.addEventListener('touchmove', handleTouchMove, { passive: false })
      element.value.addEventListener('touchend', handleTouchEnd, { passive: true })
      element.value.addEventListener('touchcancel', handleTouchEnd, { passive: true })
      
      // Add mouse events for desktop testing
      element.value.addEventListener('mousedown', handleMouseDown)
    }
  })

  onUnmounted(() => {
    if (element.value) {
      element.value.removeEventListener('touchstart', handleTouchStart)
      element.value.removeEventListener('touchmove', handleTouchMove)
      element.value.removeEventListener('touchend', handleTouchEnd)
      element.value.removeEventListener('touchcancel', handleTouchEnd)
      element.value.removeEventListener('mousedown', handleMouseDown)
    }
  })

  // API
  const triggerRefresh = async (): Promise<void> => {
    if (state.value.isRefreshing || opts.disabled) return
    await executeRefresh()
  }

  const reset = (): void => {
    state.value.isPulling = false
    state.value.isRefreshing = false
    state.value.pullDistance = 0
    state.value.canRefresh = false
    state.value.progress = 0
    refreshTriggered.value = false
  }

  const updateOptions = (newOptions: Partial<PullToRefreshOptions>): void => {
    Object.assign(opts, newOptions)
  }

  return {
    // State
    state: computed(() => state.value),
    isActive,
    pullProgress,
    rotationDegrees,
    
    // API
    triggerRefresh,
    reset,
    updateOptions,
    
    // For advanced usage
    hasReachedTop,
    
    // Getters for individual state properties
    isPulling: computed(() => state.value.isPulling),
    isRefreshing: computed(() => state.value.isRefreshing),
    pullDistance: computed(() => state.value.pullDistance),
    canRefresh: computed(() => state.value.canRefresh),
    progress: computed(() => state.value.progress)
  }
}

// Helper component props interface
export interface PullToRefreshIndicatorProps {
  isPulling: boolean
  isRefreshing: boolean
  progress: number
  pullDistance: number
  canRefresh: boolean
  rotationDegrees: number
  threshold: number
  messages?: {
    pullToRefresh?: string
    releaseToRefresh?: string
    refreshing?: string
    pullToRefreshAr?: string
    releaseToRefreshAr?: string
    refreshingAr?: string
  }
}

// Default messages
export const defaultPullToRefreshMessages = {
  pullToRefresh: 'Pull to refresh',
  releaseToRefresh: 'Release to refresh',
  refreshing: 'Refreshing...',
  pullToRefreshAr: 'اسحب للتحديث',
  releaseToRefreshAr: 'اتركه للتحديث',
  refreshingAr: 'جاري التحديث...'
}

// CSS classes for styling
export const pullToRefreshClasses = {
  container: 'pull-to-refresh-container',
  indicator: 'pull-to-refresh-indicator',
  icon: 'pull-to-refresh-icon',
  text: 'pull-to-refresh-text',
  spinner: 'pull-to-refresh-spinner',
  active: 'pull-to-refresh-active',
  refreshing: 'pull-to-refresh-refreshing',
  canRefresh: 'pull-to-refresh-can-refresh'
}

// Utility function to create pull-to-refresh styles
export function createPullToRefreshStyles(options: {
  indicatorHeight?: number
  indicatorColor?: string
  textColor?: string
  backgroundColor?: string
  borderRadius?: number
} = {}): string {
  const {
    indicatorHeight = 60,
    indicatorColor = '#3B82F6',
    textColor = '#6B7280',
    backgroundColor = '#FFFFFF',
    borderRadius = 12
  } = options

  return `
    .pull-to-refresh-container {
      position: relative;
      overflow: hidden;
    }
    
    .pull-to-refresh-indicator {
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%) translateY(-100%);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 120px;
      height: ${indicatorHeight}px;
      background: ${backgroundColor};
      border-radius: ${borderRadius}px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      z-index: 1000;
      transition: transform 0.3s ease;
    }
    
    .pull-to-refresh-indicator.pull-to-refresh-active {
      transform: translateX(-50%) translateY(0);
    }
    
    .pull-to-refresh-icon {
      color: ${indicatorColor};
      transition: transform 0.3s ease;
    }
    
    .pull-to-refresh-text {
      color: ${textColor};
      font-size: 12px;
      margin-top: 4px;
      text-align: center;
    }
    
    .pull-to-refresh-spinner {
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    
    .pull-to-refresh-can-refresh .pull-to-refresh-icon {
      transform: rotate(180deg);
    }
  `
}

export default usePullToRefresh