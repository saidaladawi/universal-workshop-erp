/**
 * Touch Gesture Manager for Mobile Interface
 * Phase 3: Sprint 3 Week 3 - Mobile Workflow Enhancement
 * 
 * Features:
 * - Multi-touch gesture recognition
 * - Arabic-aware swipe directions (RTL support)
 * - Haptic feedback integration
 * - Custom gesture definitions for workshop workflows
 * - Performance optimized touch handling
 */

export interface TouchPoint {
    id: number;
    x: number;
    y: number;
    timestamp: number;
    pressure?: number;
    radiusX?: number;
    radiusY?: number;
}

export interface GestureDefinition {
    name: string;
    pattern: TouchPoint[][];
    minDistance?: number;
    maxDistance?: number;
    minDuration?: number;
    maxDuration?: number;
    tolerance?: number;
    arabicDirection?: boolean; // RTL gesture support
}

export interface GestureEvent {
    type: string;
    gesture: string;
    startPoint: TouchPoint;
    endPoint: TouchPoint;
    direction: 'up' | 'down' | 'left' | 'right' | 'none';
    distance: number;
    duration: number;
    velocity: number;
    arabicContext: boolean;
}

export interface HapticOptions {
    enabled: boolean;
    intensity: 'light' | 'medium' | 'heavy';
    pattern?: number[]; // Custom vibration pattern
}

export interface TouchGestureConfig {
    hapticFeedback: HapticOptions;
    arabicRTLSupport: boolean;
    gestureTimeout: number; // milliseconds
    minimumSwipeDistance: number; // pixels
    maximumTapDistance: number; // pixels
    doubleTapDelay: number; // milliseconds
    longPressDelay: number; // milliseconds
    enableCustomGestures: boolean;
}

export class TouchGestureManager {
    private config: TouchGestureConfig;
    private activeTouches: Map<number, TouchPoint> = new Map();
    private gestureHistory: TouchPoint[][] = [];
    private customGestures: Map<string, GestureDefinition> = new Map();
    private gestureListeners: Map<string, Function[]> = new Map();
    private lastTapTime: number = 0;
    private lastTapPosition: { x: number, y: number } = { x: 0, y: 0 };
    private longPressTimer?: NodeJS.Timeout;
    private isArabicMode: boolean = false;

    constructor(config: Partial<TouchGestureConfig> = {}) {
        this.config = {
            hapticFeedback: {
                enabled: true,
                intensity: 'medium'
            },
            arabicRTLSupport: true,
            gestureTimeout: 2000,
            minimumSwipeDistance: 50,
            maximumTapDistance: 10,
            doubleTapDelay: 300,
            longPressDelay: 500,
            enableCustomGestures: true,
            ...config
        };

        this.initialize();
    }

    /**
     * Initialize touch gesture manager
     */
    private initialize(): void {
        this.setupWorkshopGestures();
        this.detectArabicMode();
        this.bindTouchEvents();
        
        console.log('👋 TouchGestureManager initialized with Arabic RTL support');
    }

    /**
     * Register custom gesture for workshop workflows
     */
    registerGesture(definition: GestureDefinition): void {
        this.customGestures.set(definition.name, definition);
        console.log(`🎯 Custom gesture registered: ${definition.name}`);
    }

    /**
     * Add gesture event listener
     */
    on(gestureType: string, callback: (event: GestureEvent) => void): () => void {
        if (!this.gestureListeners.has(gestureType)) {
            this.gestureListeners.set(gestureType, []);
        }
        
        this.gestureListeners.get(gestureType)!.push(callback);

        // Return unsubscribe function
        return () => {
            const listeners = this.gestureListeners.get(gestureType);
            if (listeners) {
                const index = listeners.indexOf(callback);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
            }
        };
    }

    /**
     * Enable/disable haptic feedback
     */
    setHapticFeedback(options: Partial<HapticOptions>): void {
        this.config.hapticFeedback = {
            ...this.config.hapticFeedback,
            ...options
        };
    }

    /**
     * Set Arabic/RTL mode
     */
    setArabicMode(enabled: boolean): void {
        this.isArabicMode = enabled;
        console.log(`🔄 Arabic RTL mode ${enabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Get current touch points
     */
    getActiveTouches(): TouchPoint[] {
        return Array.from(this.activeTouches.values());
    }

    /**
     * Setup workshop-specific gestures
     */
    private setupWorkshopGestures(): void {
        // Swipe left/right for work order navigation (RTL aware)
        this.registerGesture({
            name: 'workorder_next',
            pattern: [],
            minDistance: this.config.minimumSwipeDistance,
            arabicDirection: true
        });

        // Swipe up for quick actions menu
        this.registerGesture({
            name: 'quick_actions',
            pattern: [],
            minDistance: this.config.minimumSwipeDistance
        });

        // Pinch gesture for inventory zoom
        this.registerGesture({
            name: 'inventory_zoom',
            pattern: []
        });

        // Three-finger tap for emergency mode
        this.registerGesture({
            name: 'emergency_mode',
            pattern: []
        });

        // Arabic-specific: Swipe from right edge for navigation (LTR equivalent)
        this.registerGesture({
            name: 'arabic_navigation',
            pattern: [],
            arabicDirection: true
        });
    }

    /**
     * Detect if Arabic/RTL mode should be enabled
     */
    private detectArabicMode(): void {
        if (!this.config.arabicRTLSupport) return;

        // Check document direction
        const isRTL = document.dir === 'rtl' || 
                     document.documentElement.dir === 'rtl' ||
                     getComputedStyle(document.documentElement).direction === 'rtl';

        // Check for Arabic language
        const isArabic = document.documentElement.lang.startsWith('ar') ||
                        navigator.language.startsWith('ar');

        this.isArabicMode = isRTL || isArabic;
    }

    /**
     * Bind touch event listeners
     */
    private bindTouchEvents(): void {
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        document.addEventListener('touchcancel', this.handleTouchCancel.bind(this), { passive: false });
    }

    /**
     * Handle touch start events
     */
    private handleTouchStart(event: TouchEvent): void {
        const now = Date.now();

        for (let i = 0; i < event.changedTouches.length; i++) {
            const touch = event.changedTouches[i];
            const touchPoint: TouchPoint = {
                id: touch.identifier,
                x: touch.clientX,
                y: touch.clientY,
                timestamp: now,
                pressure: touch.force,
                radiusX: touch.radiusX,
                radiusY: touch.radiusY
            };

            this.activeTouches.set(touch.identifier, touchPoint);
        }

        // Handle single touch scenarios
        if (this.activeTouches.size === 1) {
            const touchPoint = Array.from(this.activeTouches.values())[0];
            
            // Setup long press detection
            this.longPressTimer = setTimeout(() => {
                this.handleLongPress(touchPoint);
            }, this.config.longPressDelay);

            // Check for double tap
            this.checkDoubleTap(touchPoint);
        }

        // Handle multi-touch scenarios
        if (this.activeTouches.size > 1) {
            this.clearLongPressTimer();
            this.handleMultiTouchStart();
        }

        // Start gesture recording
        this.startGestureRecording();
    }

    /**
     * Handle touch move events
     */
    private handleTouchMove(event: TouchEvent): void {
        event.preventDefault(); // Prevent scrolling

        const now = Date.now();

        for (let i = 0; i < event.changedTouches.length; i++) {
            const touch = event.changedTouches[i];
            const touchPoint: TouchPoint = {
                id: touch.identifier,
                x: touch.clientX,
                y: touch.clientY,
                timestamp: now,
                pressure: touch.force,
                radiusX: touch.radiusX,
                radiusY: touch.radiusY
            };

            this.activeTouches.set(touch.identifier, touchPoint);
        }

        // Clear long press if movement detected
        if (this.activeTouches.size === 1) {
            const startPoint = this.gestureHistory[0]?.[0];
            const currentPoint = Array.from(this.activeTouches.values())[0];
            
            if (startPoint && this.calculateDistance(startPoint, currentPoint) > this.config.maximumTapDistance) {
                this.clearLongPressTimer();
            }
        }

        // Update gesture recording
        this.updateGestureRecording();

        // Handle multi-touch movements
        if (this.activeTouches.size === 2) {
            this.handlePinchGesture();
        }
    }

    /**
     * Handle touch end events
     */
    private handleTouchEnd(event: TouchEvent): void {
        const now = Date.now();
        
        for (let i = 0; i < event.changedTouches.length; i++) {
            const touch = event.changedTouches[i];
            this.activeTouches.delete(touch.identifier);
        }

        this.clearLongPressTimer();

        // Process completed gesture
        if (this.activeTouches.size === 0) {
            this.processCompletedGesture();
        }

        // Handle remaining touches
        if (this.activeTouches.size === 1) {
            // Continue with single touch if multi-touch ended
            this.handleSingleTouchContinuation();
        }
    }

    /**
     * Handle touch cancel events
     */
    private handleTouchCancel(event: TouchEvent): void {
        for (let i = 0; i < event.changedTouches.length; i++) {
            const touch = event.changedTouches[i];
            this.activeTouches.delete(touch.identifier);
        }

        this.clearLongPressTimer();
        this.clearGestureHistory();
    }

    /**
     * Process completed gesture and emit appropriate events
     */
    private processCompletedGesture(): void {
        if (this.gestureHistory.length === 0) return;

        const startPoint = this.gestureHistory[0][0];
        const endPoint = this.gestureHistory[this.gestureHistory.length - 1][0];
        const duration = endPoint.timestamp - startPoint.timestamp;
        const distance = this.calculateDistance(startPoint, endPoint);

        // Determine gesture type
        let gestureType = 'unknown';
        let gestureName = 'unknown';

        // Simple tap
        if (distance <= this.config.maximumTapDistance && duration < this.config.longPressDelay) {
            gestureType = 'tap';
            gestureName = 'tap';
        }
        // Swipe gesture
        else if (distance >= this.config.minimumSwipeDistance) {
            gestureType = 'swipe';
            const direction = this.getSwipeDirection(startPoint, endPoint);
            gestureName = `swipe_${direction}`;
            
            // Adjust for Arabic RTL mode
            if (this.isArabicMode && (direction === 'left' || direction === 'right')) {
                gestureName = direction === 'left' ? 'swipe_right' : 'swipe_left';
            }
        }

        // Check custom gestures
        const customGesture = this.matchCustomGesture();
        if (customGesture) {
            gestureType = 'custom';
            gestureName = customGesture.name;
        }

        // Create gesture event
        const gestureEvent: GestureEvent = {
            type: gestureType,
            gesture: gestureName,
            startPoint,
            endPoint,
            direction: this.getSwipeDirection(startPoint, endPoint),
            distance,
            duration,
            velocity: distance / (duration || 1),
            arabicContext: this.isArabicMode
        };

        // Emit gesture event
        this.emitGestureEvent(gestureEvent);

        // Trigger haptic feedback
        this.triggerHapticFeedback(gestureType);

        // Clear gesture history
        this.clearGestureHistory();
    }

    /**
     * Handle double tap detection
     */
    private checkDoubleTap(touchPoint: TouchPoint): void {
        const now = touchPoint.timestamp;
        const timeDiff = now - this.lastTapTime;
        const distance = this.calculateDistance(touchPoint, this.lastTapPosition);

        if (timeDiff < this.config.doubleTapDelay && distance < this.config.maximumTapDistance) {
            // Double tap detected
            const gestureEvent: GestureEvent = {
                type: 'tap',
                gesture: 'double_tap',
                startPoint: touchPoint,
                endPoint: touchPoint,
                direction: 'none',
                distance: 0,
                duration: timeDiff,
                velocity: 0,
                arabicContext: this.isArabicMode
            };

            this.emitGestureEvent(gestureEvent);
            this.triggerHapticFeedback('double_tap');

            // Reset tap tracking
            this.lastTapTime = 0;
        } else {
            // Update last tap info
            this.lastTapTime = now;
            this.lastTapPosition = { x: touchPoint.x, y: touchPoint.y };
        }
    }

    /**
     * Handle long press gesture
     */
    private handleLongPress(touchPoint: TouchPoint): void {
        const gestureEvent: GestureEvent = {
            type: 'press',
            gesture: 'long_press',
            startPoint: touchPoint,
            endPoint: touchPoint,
            direction: 'none',
            distance: 0,
            duration: this.config.longPressDelay,
            velocity: 0,
            arabicContext: this.isArabicMode
        };

        this.emitGestureEvent(gestureEvent);
        this.triggerHapticFeedback('long_press');
    }

    /**
     * Handle pinch gesture for zoom
     */
    private handlePinchGesture(): void {
        const touches = Array.from(this.activeTouches.values());
        if (touches.length !== 2) return;

        const [touch1, touch2] = touches;
        const currentDistance = this.calculateDistance(touch1, touch2);
        
        // Store initial distance if not set
        if (!this.hasOwnProperty('initialPinchDistance')) {
            (this as any).initialPinchDistance = currentDistance;
            return;
        }

        const initialDistance = (this as any).initialPinchDistance;
        const scale = currentDistance / initialDistance;

        const gestureEvent: GestureEvent = {
            type: 'pinch',
            gesture: scale > 1 ? 'pinch_out' : 'pinch_in',
            startPoint: touch1,
            endPoint: touch2,
            direction: 'none',
            distance: currentDistance,
            duration: 0,
            velocity: 0,
            arabicContext: this.isArabicMode
        };

        this.emitGestureEvent(gestureEvent);
    }

    /**
     * Match against custom gesture definitions
     */
    private matchCustomGesture(): GestureDefinition | null {
        if (!this.config.enableCustomGestures) return null;

        for (const [name, definition] of this.customGestures) {
            if (this.isGestureMatch(definition)) {
                return definition;
            }
        }

        return null;
    }

    /**
     * Check if current gesture matches definition
     */
    private isGestureMatch(definition: GestureDefinition): boolean {
        if (this.gestureHistory.length === 0) return false;

        const startPoint = this.gestureHistory[0][0];
        const endPoint = this.gestureHistory[this.gestureHistory.length - 1][0];
        const distance = this.calculateDistance(startPoint, endPoint);
        const duration = endPoint.timestamp - startPoint.timestamp;

        // Check distance constraints
        if (definition.minDistance && distance < definition.minDistance) return false;
        if (definition.maxDistance && distance > definition.maxDistance) return false;

        // Check duration constraints
        if (definition.minDuration && duration < definition.minDuration) return false;
        if (definition.maxDuration && duration > definition.maxDuration) return false;

        // Check Arabic direction if specified
        if (definition.arabicDirection && !this.isArabicMode) return false;

        return true;
    }

    /**
     * Get swipe direction
     */
    private getSwipeDirection(start: TouchPoint, end: TouchPoint): 'up' | 'down' | 'left' | 'right' | 'none' {
        const deltaX = end.x - start.x;
        const deltaY = end.y - start.y;

        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            return deltaX > 0 ? 'right' : 'left';
        } else if (Math.abs(deltaY) > Math.abs(deltaX)) {
            return deltaY > 0 ? 'down' : 'up';
        }

        return 'none';
    }

    /**
     * Calculate distance between two points
     */
    private calculateDistance(point1: { x: number, y: number }, point2: { x: number, y: number }): number {
        const deltaX = point2.x - point1.x;
        const deltaY = point2.y - point1.y;
        return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
    }

    /**
     * Emit gesture event to listeners
     */
    private emitGestureEvent(gestureEvent: GestureEvent): void {
        // Emit specific gesture event
        const specificListeners = this.gestureListeners.get(gestureEvent.gesture);
        if (specificListeners) {
            specificListeners.forEach(callback => callback(gestureEvent));
        }

        // Emit general gesture event  
        const generalListeners = this.gestureListeners.get('gesture');
        if (generalListeners) {
            generalListeners.forEach(callback => callback(gestureEvent));
        }

        console.log(`👋 Gesture detected: ${gestureEvent.gesture}`, gestureEvent);
    }

    /**
     * Trigger haptic feedback based on gesture type
     */
    private triggerHapticFeedback(gestureType: string): void {
        if (!this.config.hapticFeedback.enabled) return;

        if ('vibrate' in navigator) {
            let pattern: number[] = [];

            switch (gestureType) {
                case 'tap':
                    pattern = [10];
                    break;
                case 'double_tap':
                    pattern = [10, 50, 10];
                    break;
                case 'long_press':
                    pattern = [100];
                    break;
                case 'swipe':
                    pattern = [20];
                    break;
                case 'pinch':
                    pattern = [30];
                    break;
                case 'custom':
                    pattern = this.config.hapticFeedback.pattern || [50];
                    break;
                default:
                    pattern = [15];
            }

            navigator.vibrate(pattern);
        }
    }

    // Gesture recording helpers
    private startGestureRecording(): void {
        this.gestureHistory = [];
        this.updateGestureRecording();
    }

    private updateGestureRecording(): void {
        const currentTouches = Array.from(this.activeTouches.values());
        this.gestureHistory.push([...currentTouches]);
    }

    private clearGestureHistory(): void {
        this.gestureHistory = [];
        delete (this as any).initialPinchDistance;
    }

    private clearLongPressTimer(): void {
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = undefined;
        }
    }

    private handleMultiTouchStart(): void {
        // Handle multi-touch specific initialization
        console.log(`🤚 Multi-touch started: ${this.activeTouches.size} touches`);
    }

    private handleSingleTouchContinuation(): void {
        // Handle transition from multi-touch to single touch
        console.log('👆 Continuing with single touch');
    }

    /**
     * Cleanup and destroy gesture manager
     */
    destroy(): void {
        this.clearLongPressTimer();
        this.clearGestureHistory();
        this.activeTouches.clear();
        this.gestureListeners.clear();
        this.customGestures.clear();

        // Remove event listeners
        document.removeEventListener('touchstart', this.handleTouchStart.bind(this));
        document.removeEventListener('touchmove', this.handleTouchMove.bind(this));
        document.removeEventListener('touchend', this.handleTouchEnd.bind(this));
        document.removeEventListener('touchcancel', this.handleTouchCancel.bind(this));

        console.log('👋 TouchGestureManager destroyed');
    }
}

// Export singleton instance for global use
export const touchGestureManager = new TouchGestureManager();
