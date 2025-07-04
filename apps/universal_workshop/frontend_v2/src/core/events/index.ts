/**
 * Core Events Module - Universal Workshop Frontend V2
 * 
 * Central exports for all event-related functionality
 */

// Main event bus exports
export { UnifiedEventBus } from './UnifiedEventBus'
export { 
    EnhancedWorkshopEventBus, 
    enhancedWorkshopEventBus, 
    useEnhancedEventBus 
} from './WorkshopEventBus'

// Event types and interfaces
export type { 
    WorkshopEvent, 
    WorkshopEventType, 
    EventHandler, 
    EventFilter,
    EventMetrics,
    SubscriptionConfig 
} from './EventTypes'

// Event handlers
export { eventHandlerRegistry } from './EventHandlers'

// Arabic event templates
export { 
    arabicEventTemplateRegistry, 
    processArabicTemplate 
} from './ArabicEventTemplates'
export type { 
    ArabicEventTemplate, 
    TemplateVariables 
} from './ArabicEventTemplates'

// Default export for convenience
export { useEnhancedEventBus as default } from './WorkshopEventBus'