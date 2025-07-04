# Frontend V2 - Modern Architecture

## Overview
This is the modernized frontend architecture for Universal Workshop ERP, built alongside the existing system for safe migration.

## Architecture Principles
- **Parallel Development**: Coexists with existing frontend without disruption
- **TypeScript First**: Type safety and modern tooling
- **Component-Based**: Reusable, modular components
- **Performance Optimized**: Bundle splitting and modern build tools
- **Arabic/RTL Ready**: Comprehensive internationalization support

## Directory Structure

### `/src/core/`
Core system functionality that doesn't belong to specific features:
- `auth/` - Authentication utilities and components
- `session/` - Session management and timeout handling  
- `setup/` - System setup and configuration

### `/src/components/`
Reusable UI components following design system principles:
- `common/` - Basic UI elements (Button, Input, Card, etc.)
- `forms/` - Form-specific components with validation
- `tables/` - Data table components with sorting/filtering
- `modals/` - Modal dialogs and overlays

### `/src/modules/`
Feature-specific modules organized by business domain:
- `dashboard/` - Main dashboard and KPI displays
- `inventory/` - Parts and inventory management
- `customer/` - Customer management and portal
- `workshop/` - Core workshop operations
- `analytics/` - Reporting and analytics
- `mobile/` - Mobile-specific interfaces

### `/src/branding/`
Dynamic branding and theming system:
- `themes/` - Theme definitions and color schemes
- `components/` - Brand-aware components
- `utils/` - Branding utilities and helpers

### `/src/localization/`
Internationalization and Arabic/RTL support:
- `arabic/` - Arabic-specific utilities and formatting
- `utils/` - Translation and localization helpers
- `styles/` - RTL and Arabic typography styles

### `/src/styles/`
Consolidated CSS architecture:
- `base/` - Reset, typography, base styles
- `components/` - Component-specific styles
- `themes/` - Theme and branding styles
- `utilities/` - Utility classes and helpers

### `/src/utils/`
Shared utilities and helper functions:
- `api/` - API client and request utilities
- `helpers/` - General helper functions
- `constants/` - Application constants and enums

## Build System
- **Vite** - Modern build tool with HMR
- **TypeScript** - Type safety and modern JavaScript features
- **Vue 3** - Progressive framework with Composition API
- **Sass** - CSS preprocessing with design tokens

## Development Status
- ✅ Directory structure created
- ⏳ Build system setup (in progress)
- ⏳ TypeScript configuration
- ⏳ Component library development

## Safety Notes
- This directory is completely isolated from existing frontend
- No existing functionality is affected
- Can be safely removed if needed
- Feature flags control gradual migration

---
**Created**: December 29, 2024  
**Phase**: 1 - Foundation & Consolidation  
**Status**: Parallel Development Environment Ready