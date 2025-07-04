/**
 * Touch Gestures Composable - Universal Workshop Frontend V2
 * 
 * A comprehensive composable for handling touch gestures on mobile devices
 * including swipe, pinch, tap, long press, and drag interactions.
 */

import { ref, computed, onMounted, onUnmounted, type Ref } from 'vue'

// Types
export interface TouchPoint {
  x: number
  y: number
  timestamp: number
}

export interface SwipeEvent {
  direction: 'left' | 'right' | 'up' | 'down'
  distance: number
  velocity: number
  duration: number
  startPoint: TouchPoint
  endPoint: TouchPoint
}

export interface PinchEvent {
  scale: number
  rotation: number
  center: TouchPoint
  distance: number
}

export interface DragEvent {
  deltaX: number
  deltaY: number
  totalX: number
  totalY: number
  startPoint: TouchPoint
  currentPoint: TouchPoint
}

export interface TapEvent {
  point: TouchPoint
  tapCount: number
}

export interface LongPressEvent {
  point: TouchPoint
  duration: number
}

export interface TouchGestureOptions {
  // Swipe options
  swipeThreshold?: number // minimum distance for swipe
  swipeVelocityThreshold?: number // minimum velocity for swipe
  
  // Pinch options
  pinchThreshold?: number // minimum scale change for pinch
  
  // Tap options
  tapTimeout?: number // max time for tap
  doubleTapTimeout?: number // max time between taps for double tap
  tapRadius?: number // max movement for tap
  
  // Long press options
  longPressTimeout?: number // time for long press
  longPressRadius?: number // max movement for long press
  
  // Drag options
  dragThreshold?: number // minimum distance to start drag
  
  // General options
  preventDefault?: boolean
  stopPropagation?: boolean
}

export interface TouchGestureCallbacks {
  onSwipe?: (event: SwipeEvent) => void
  onSwipeStart?: (startPoint: TouchPoint) => void
  onSwipeMove?: (currentPoint: TouchPoint, startPoint: TouchPoint) => void
  onSwipeEnd?: (endPoint: TouchPoint, startPoint: TouchPoint) => void
  
  onPinch?: (event: PinchEvent) => void
  onPinchStart?: (center: TouchPoint, distance: number) => void
  onPinchMove?: (center: TouchPoint, scale: number, distance: number) => void
  onPinchEnd?: (center: TouchPoint, finalScale: number) => void
  
  onDrag?: (event: DragEvent) => void
  onDragStart?: (startPoint: TouchPoint) => void
  onDragMove?: (event: DragEvent) => void
  onDragEnd?: (endPoint: TouchPoint, totalDelta: { x: number; y: number }) => void
  
  onTap?: (event: TapEvent) => void
  onDoubleTap?: (event: TapEvent) => void
  onTripleTap?: (event: TapEvent) => void
  
  onLongPress?: (event: LongPressEvent) => void
  onLongPressStart?: (point: TouchPoint) => void
  onLongPressEnd?: (point: TouchPoint, duration: number) => void
  
  onTouchStart?: (touches: TouchList) => void
  onTouchMove?: (touches: TouchList) => void
  onTouchEnd?: (touches: TouchList) => void
}

export function useTouchGestures(
  element: Ref<HTMLElement | null>,
  callbacks: TouchGestureCallbacks = {},
  options: TouchGestureOptions = {}
) {
  // Default options
  const opts = {
    swipeThreshold: 50,
    swipeVelocityThreshold: 0.3,
    pinchThreshold: 0.1,
    tapTimeout: 300,
    doubleTapTimeout: 300,
    tapRadius: 10,
    longPressTimeout: 500,
    longPressRadius: 10,
    dragThreshold: 10,
    preventDefault: false,
    stopPropagation: false,
    ...options
  }

  // State
  const isEnabled = ref(true)
  const currentTouches = ref<TouchList | null>(null)
  const touchStartTime = ref(0)
  const touchStartPoints = ref<TouchPoint[]>([])
  const lastTapTime = ref(0)
  const tapCount = ref(0)
  const longPressTimer = ref<number | null>(null)
  const isDragging = ref(false)
  const isPinching = ref(false)
  const isLongPressing = ref(false)
  const dragStartPoint = ref<TouchPoint | null>(null)
  const pinchStartDistance = ref(0)
  const pinchStartCenter = ref<TouchPoint | null>(null)

  // Computed
  const hasMultipleTouch = computed(() => 
    currentTouches.value && currentTouches.value.length > 1
  )

  // Utility functions
  const getTouchPoint = (touch: Touch): TouchPoint => ({
    x: touch.clientX,
    y: touch.clientY,
    timestamp: Date.now()
  })

  const getDistance = (p1: TouchPoint, p2: TouchPoint): number => {
    const dx = p2.x - p1.x
    const dy = p2.y - p1.y
    return Math.sqrt(dx * dx + dy * dy)
  }

  const getCenter = (p1: TouchPoint, p2: TouchPoint): TouchPoint => ({
    x: (p1.x + p2.x) / 2,
    y: (p1.y + p2.y) / 2,
    timestamp: Date.now()
  })

  const getSwipeDirection = (start: TouchPoint, end: TouchPoint): 'left' | 'right' | 'up' | 'down' => {
    const dx = end.x - start.x
    const dy = end.y - start.y
    
    if (Math.abs(dx) > Math.abs(dy)) {
      return dx > 0 ? 'right' : 'left'
    } else {
      return dy > 0 ? 'down' : 'up'
    }
  }

  const clearTimers = () => {
    if (longPressTimer.value) {
      clearTimeout(longPressTimer.value)
      longPressTimer.value = null
    }
  }

  const resetState = () => {
    clearTimers()
    isDragging.value = false
    isPinching.value = false
    isLongPressing.value = false
    dragStartPoint.value = null
    pinchStartDistance.value = 0
    pinchStartCenter.value = null
    touchStartPoints.value = []
  }

  // Event handlers
  const handleTouchStart = (event: TouchEvent) => {
    if (!isEnabled.value) return

    if (opts.preventDefault) event.preventDefault()
    if (opts.stopPropagation) event.stopPropagation()

    currentTouches.value = event.touches
    touchStartTime.value = Date.now()
    touchStartPoints.value = Array.from(event.touches).map(getTouchPoint)

    callbacks.onTouchStart?.(event.touches)

    // Single touch
    if (event.touches.length === 1) {
      const startPoint = touchStartPoints.value[0]
      
      // Start long press timer
      longPressTimer.value = window.setTimeout(() => {
        if (!isDragging.value && !isPinching.value) {
          isLongPressing.value = true
          callbacks.onLongPressStart?.(startPoint)
          
          const longPressEvent: LongPressEvent = {
            point: startPoint,
            duration: Date.now() - touchStartTime.value
          }
          callbacks.onLongPress?.(longPressEvent)
        }
      }, opts.longPressTimeout)

      callbacks.onSwipeStart?.(startPoint)
      callbacks.onDragStart?.(startPoint)
    }

    // Multi-touch (pinch)
    if (event.touches.length === 2) {
      clearTimers()
      const p1 = touchStartPoints.value[0]
      const p2 = touchStartPoints.value[1]
      pinchStartDistance.value = getDistance(p1, p2)
      pinchStartCenter.value = getCenter(p1, p2)
      isPinching.value = true
      
      callbacks.onPinchStart?.(pinchStartCenter.value, pinchStartDistance.value)
    }
  }

  const handleTouchMove = (event: TouchEvent) => {
    if (!isEnabled.value || !currentTouches.value) return

    if (opts.preventDefault) event.preventDefault()
    if (opts.stopPropagation) event.stopPropagation()

    const currentPoints = Array.from(event.touches).map(getTouchPoint)
    callbacks.onTouchMove?.(event.touches)

    // Single touch movement
    if (event.touches.length === 1 && touchStartPoints.value.length > 0) {
      const startPoint = touchStartPoints.value[0]
      const currentPoint = currentPoints[0]
      const distance = getDistance(startPoint, currentPoint)

      // Check if moved beyond tap/long press radius
      if (distance > opts.tapRadius) {
        clearTimers()
        isLongPressing.value = false
      }

      // Handle drag
      if (distance > opts.dragThreshold && !isDragging.value) {
        isDragging.value = true
        dragStartPoint.value = startPoint
      }

      if (isDragging.value && dragStartPoint.value) {
        const dragEvent: DragEvent = {
          deltaX: currentPoint.x - (dragStartPoint.value?.x || startPoint.x),
          deltaY: currentPoint.y - (dragStartPoint.value?.y || startPoint.y),
          totalX: currentPoint.x - startPoint.x,
          totalY: currentPoint.y - startPoint.y,
          startPoint: dragStartPoint.value,
          currentPoint
        }
        
        callbacks.onDrag?.(dragEvent)
        callbacks.onDragMove?.(dragEvent)
      }

      callbacks.onSwipeMove?.(currentPoint, startPoint)
    }

    // Multi-touch movement (pinch)
    if (event.touches.length === 2 && isPinching.value && pinchStartCenter.value) {
      const p1 = currentPoints[0]
      const p2 = currentPoints[1]
      const currentDistance = getDistance(p1, p2)
      const currentCenter = getCenter(p1, p2)
      const scale = currentDistance / pinchStartDistance.value

      if (Math.abs(scale - 1) > opts.pinchThreshold) {
        const pinchEvent: PinchEvent = {
          scale,
          rotation: 0, // Could calculate rotation if needed
          center: currentCenter,
          distance: currentDistance
        }
        
        callbacks.onPinch?.(pinchEvent)
        callbacks.onPinchMove?.(currentCenter, scale, currentDistance)
      }
    }
  }

  const handleTouchEnd = (event: TouchEvent) => {
    if (!isEnabled.value) return

    if (opts.preventDefault) event.preventDefault()
    if (opts.stopPropagation) event.stopPropagation()

    const endTime = Date.now()
    const duration = endTime - touchStartTime.value
    
    callbacks.onTouchEnd?.(event.touches)

    // Handle single touch end
    if (touchStartPoints.value.length === 1) {
      const startPoint = touchStartPoints.value[0]
      const endPoint: TouchPoint = {
        x: event.changedTouches[0].clientX,
        y: event.changedTouches[0].clientY,
        timestamp: endTime
      }

      const distance = getDistance(startPoint, endPoint)
      const velocity = distance / duration

      // Handle swipe
      if (distance > opts.swipeThreshold && velocity > opts.swipeVelocityThreshold) {
        const swipeEvent: SwipeEvent = {
          direction: getSwipeDirection(startPoint, endPoint),
          distance,
          velocity,
          duration,
          startPoint,
          endPoint
        }
        callbacks.onSwipe?.(swipeEvent)
      }

      // Handle tap
      if (distance <= opts.tapRadius && duration <= opts.tapTimeout && !isDragging.value) {
        const timeSinceLastTap = endTime - lastTapTime.value
        
        if (timeSinceLastTap <= opts.doubleTapTimeout) {
          tapCount.value++
        } else {
          tapCount.value = 1
        }
        
        lastTapTime.value = endTime

        const tapEvent: TapEvent = {
          point: endPoint,
          tapCount: tapCount.value
        }

        // Emit appropriate tap event
        if (tapCount.value === 1) {
          setTimeout(() => {
            if (tapCount.value === 1) {
              callbacks.onTap?.(tapEvent)
            }
          }, opts.doubleTapTimeout)
        } else if (tapCount.value === 2) {
          callbacks.onDoubleTap?.(tapEvent)
        } else if (tapCount.value === 3) {
          callbacks.onTripleTap?.(tapEvent)
          tapCount.value = 0
        }
      }

      // Handle drag end
      if (isDragging.value) {
        const totalDelta = {
          x: endPoint.x - startPoint.x,
          y: endPoint.y - startPoint.y
        }
        callbacks.onDragEnd?.(endPoint, totalDelta)
      }

      // Handle long press end
      if (isLongPressing.value) {
        callbacks.onLongPressEnd?.(endPoint, duration)
      }

      callbacks.onSwipeEnd?.(endPoint, startPoint)
    }

    // Handle pinch end
    if (isPinching.value && pinchStartCenter.value) {
      const finalScale = pinchStartDistance.value > 0 
        ? getDistance(touchStartPoints.value[0], touchStartPoints.value[1]) / pinchStartDistance.value 
        : 1
      
      callbacks.onPinchEnd?.(pinchStartCenter.value, finalScale)
    }

    // Reset state when all touches are lifted
    if (event.touches.length === 0) {
      resetState()
      currentTouches.value = null
    }
  }

  // Lifecycle
  onMounted(() => {
    if (element.value) {
      element.value.addEventListener('touchstart', handleTouchStart, { passive: !opts.preventDefault })
      element.value.addEventListener('touchmove', handleTouchMove, { passive: !opts.preventDefault })
      element.value.addEventListener('touchend', handleTouchEnd, { passive: !opts.preventDefault })
      element.value.addEventListener('touchcancel', handleTouchEnd, { passive: !opts.preventDefault })
    }
  })

  onUnmounted(() => {
    if (element.value) {
      element.value.removeEventListener('touchstart', handleTouchStart)
      element.value.removeEventListener('touchmove', handleTouchMove)
      element.value.removeEventListener('touchend', handleTouchEnd)
      element.value.removeEventListener('touchcancel', handleTouchEnd)
    }
    resetState()
  })

  // API
  const enable = () => {
    isEnabled.value = true
  }

  const disable = () => {
    isEnabled.value = false
    resetState()
  }

  const updateOptions = (newOptions: Partial<TouchGestureOptions>) => {
    Object.assign(opts, newOptions)
  }

  return {
    // State
    isEnabled,
    isDragging,
    isPinching,
    isLongPressing,
    hasMultipleTouch,
    currentTouches,
    
    // API
    enable,
    disable,
    updateOptions,
    resetState,
    
    // Utility functions (exposed for advanced usage)
    getTouchPoint,
    getDistance,
    getCenter,
    getSwipeDirection
  }
}

// Specialized composables for specific gestures
export function useSwipeGestures(
  element: Ref<HTMLElement | null>,
  onSwipe: (event: SwipeEvent) => void,
  options: Pick<TouchGestureOptions, 'swipeThreshold' | 'swipeVelocityThreshold' | 'preventDefault'> = {}
) {
  return useTouchGestures(element, { onSwipe }, options)
}

export function usePinchGestures(
  element: Ref<HTMLElement | null>,
  onPinch: (event: PinchEvent) => void,
  options: Pick<TouchGestureOptions, 'pinchThreshold' | 'preventDefault'> = {}
) {
  return useTouchGestures(element, { onPinch }, options)
}

export function useDragGestures(
  element: Ref<HTMLElement | null>,
  callbacks: {
    onDragStart?: (startPoint: TouchPoint) => void
    onDragMove?: (event: DragEvent) => void
    onDragEnd?: (endPoint: TouchPoint, totalDelta: { x: number; y: number }) => void
  },
  options: Pick<TouchGestureOptions, 'dragThreshold' | 'preventDefault'> = {}
) {
  return useTouchGestures(element, callbacks, options)
}

export function useTapGestures(
  element: Ref<HTMLElement | null>,
  callbacks: {
    onTap?: (event: TapEvent) => void
    onDoubleTap?: (event: TapEvent) => void
    onLongPress?: (event: LongPressEvent) => void
  },
  options: Pick<TouchGestureOptions, 'tapTimeout' | 'doubleTapTimeout' | 'longPressTimeout' | 'tapRadius' | 'longPressRadius'> = {}
) {
  return useTouchGestures(element, callbacks, options)
}

// Device detection utilities
export function isTouchDevice(): boolean {
  return 'ontouchstart' in window || navigator.maxTouchPoints > 0
}

export function isIOS(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent)
}

export function isAndroid(): boolean {
  return /Android/.test(navigator.userAgent)
}

export function supportsPinchZoom(): boolean {
  return isTouchDevice() && 'ontouchstart' in window
}

export function getViewportSize() {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
    isPortrait: window.innerHeight > window.innerWidth,
    isLandscape: window.innerWidth > window.innerHeight
  }
}