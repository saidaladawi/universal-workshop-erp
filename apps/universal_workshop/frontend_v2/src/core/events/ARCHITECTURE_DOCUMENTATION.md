# Event Bus Architecture - Universal Workshop Frontend V2

## Overview

This document clarifies the architecture and purpose of different Event Bus implementations in our system to eliminate confusion and prevent code duplication.

## Architecture Layers

### 1. Core Event System (`/src/core/events/`)
**Purpose**: Foundation layer providing event type definitions, handlers registry, and shared utilities.

**Components**:
- `EventTypes.ts` - Type definitions for all workshop events
- `EventHandlers.ts` - Event handler registry and default handlers
- `ArabicEventTemplates.ts` - Arabic notification templates and formatting
- `WorkshopEventBus.ts` - Enhanced event bus with comprehensive features
- `index.ts` - Centralized exports and utilities

**Responsibilities**:
- Define event type system
- Provide event handler registry
- Manage Arabic localization templates
- Offer advanced event management features (batching, persistence, analytics)

### 2. Real-Time Feature (`/src/features/realtime/`)
**Purpose**: WebSocket-based real-time communication layer.

**Components**:
- `WorkshopEventBus.ts` - WebSocket event bus for real-time communication

**Responsibilities**:
- WebSocket connection management
- Real-time event broadcasting
- Connection pooling and rate limiting
- Network-specific event handling

### 3. Vue Composables (`/src/composables/`)
**Purpose**: Vue 3 reactive composition layer for components.

**Components**:
- `useEventBus.ts` - Vue composable wrapper for event bus functionality

**Responsibilities**:
- Vue 3 reactivity integration
- Component lifecycle management
- Reactive state management for UI
- Specialized composables for specific use cases

## Data Flow

```
Component (Vue)
    ↓ uses
Composable (useEventBus)
    ↓ delegates to
Core Events (Enhanced Event Bus)
    ↓ integrates with
Real-Time (WebSocket Event Bus)
    ↓ communicates with
Backend WebSocket Server
```

## Interaction Patterns

### 1. Component Usage
```typescript
// In Vue components
const { subscribe, broadcast, notify } = useEventBus()
```

### 2. Service Usage
```typescript
// In services/utilities
import { getEventBus } from '@/core/events'
const eventBus = getEventBus()
```

### 3. Real-Time Integration
```typescript
// Core event bus automatically integrates with real-time layer
const enhancedBus = new EnhancedWorkshopEventBus({
  enableRealTime: true // Automatically uses WebSocket layer
})
```

## Key Differences

| Layer | Purpose | When to Use |
|-------|---------|-------------|
| Core Events | Event system foundation | Services, utilities, advanced features |
| Real-Time | WebSocket communications | Real-time updates, live notifications |
| Composables | Vue integration | Vue components, reactive UI state |

## Best Practices

### 1. Use Appropriate Layer
- **Components**: Always use `useEventBus()` composable
- **Services**: Use core event bus directly
- **Real-time**: Handled automatically by core layer

### 2. Avoid Direct Access
- Don't import real-time event bus directly in components
- Don't bypass composables in Vue components
- Don't duplicate event definitions

### 3. Event Naming
- Use consistent event types from `EventTypes.ts`
- Follow Arabic naming conventions for localization
- Use priority levels appropriately

## Migration Guide

### From Old Pattern
```typescript
// ❌ Old - Direct WebSocket usage
import { WorkshopEventBus } from '@/features/realtime/WorkshopEventBus'
const eventBus = new WorkshopEventBus()
```

### To New Pattern
```typescript
// ✅ New - Use appropriate layer
// In Vue components:
const { subscribe, broadcast } = useEventBus()

// In services:
import { getEventBus } from '@/core/events'
const eventBus = getEventBus()
```

## Configuration

### Core Event Bus Configuration
```typescript
const config: EnhancedEventBusConfig = {
  enableRealTime: true,      // Integrate with WebSocket layer
  enablePersistence: true,   // Store events locally
  enableAnalytics: true,     // Track event metrics
  enableArabicTemplates: true, // Arabic localization
  maxEventHistory: 1000,     // Event history limit
  batchSize: 50,            // Batch processing size
  retryAttempts: 3,         // Retry failed events
  retryDelay: 1000,         // Retry delay (ms)
  compressionEnabled: false, // Event compression
  encryptionEnabled: false   // Event encryption
}
```

### WebSocket Configuration
```typescript
const wsConfig = {
  url: 'ws://localhost:8080/workshop',
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  maxMessagesPerMinute: 60
}
```

## Integration Points

### 1. Event Types
All layers use the same event types defined in `core/events/EventTypes.ts`.

### 2. Arabic Templates
Arabic localization is handled centrally in `core/events/ArabicEventTemplates.ts`.

### 3. Real-Time Integration
Core event bus automatically integrates with real-time layer when `enableRealTime: true`.

### 4. Vue Reactivity
Composables provide Vue 3 reactivity while delegating to core event bus.

## Performance Considerations

### 1. Event Batching
Core layer handles event batching for performance optimization.

### 2. Connection Pooling
Real-time layer manages WebSocket connection pooling.

### 3. Memory Management
Event history is limited and automatically cleaned up.

### 4. Rate Limiting
Real-time layer includes rate limiting to prevent spam.

## Troubleshooting

### Common Issues

1. **Events not firing**: Check if event types match between publisher and subscriber
2. **Arabic text not showing**: Ensure Arabic templates are enabled in configuration
3. **WebSocket not connecting**: Verify WebSocket URL and server availability
4. **Memory leaks**: Ensure proper cleanup in component `onUnmounted`

### Debug Mode
```typescript
const { subscribe } = useEventBus({ debug: true })
```

This will enable detailed logging of all event bus operations.
