/**
 * Design System Utilities - Universal Workshop Frontend V2
 * 
 * Utility functions for working with design tokens in TypeScript.
 * Provides runtime access to design tokens and CSS custom property generation.
 */

import { designTokens, type DesignTokens, type SemanticColors } from './tokens'

/**
 * Get a design token value by path
 */
export function getToken(path: string): string | number | undefined {
  const keys = path.split('.')
  let current: any = designTokens
  
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key]
    } else {
      return undefined
    }
  }
  
  return current
}

/**
 * Generate CSS custom property name from token path
 */
export function getCSSVar(path: string, fallback?: string): string {
  const customPropertyName = `--${path.replace(/\./g, '-')}`
  return fallback ? `var(${customPropertyName}, ${fallback})` : `var(${customPropertyName})`
}

/**
 * Convert design token object to CSS custom properties
 */
export function tokensToCSSVars(
  tokens: Record<string, any>, 
  prefix: string = ''
): Record<string, string> {
  const cssVars: Record<string, string> = {}
  
  function traverse(obj: any, currentPath: string[] = []) {
    for (const [key, value] of Object.entries(obj)) {
      const path = [...currentPath, key]
      const cssVarName = `--${prefix}${prefix ? '-' : ''}${path.join('-')}`
      
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        traverse(value, path)
      } else {
        cssVars[cssVarName] = String(value)
      }
    }
  }
  
  traverse(tokens)
  return cssVars
}

/**
 * Color utility functions
 */
export const colorUtils = {
  /**
   * Get semantic color with variant
   */
  getSemanticColor(color: keyof SemanticColors, variant: string = 'base'): string {
    return getToken(`colors.semantic.${color}.${variant}`) as string || '#000000'
  },
  
  /**
   * Get CSS variable for semantic color
   */
  getSemanticColorVar(color: keyof SemanticColors, variant: string = 'base'): string {
    return getCSSVar(`color-${color}-${variant}`)
  },
  
  /**
   * Generate color scale CSS variables
   */
  generateColorScale(name: string, scale: Record<string, string>): Record<string, string> {
    const vars: Record<string, string> = {}
    Object.entries(scale).forEach(([key, value]) => {
      vars[`--color-${name}-${key}`] = value
    })
    return vars
  },
}

/**
 * Typography utility functions
 */
export const typographyUtils = {
  /**
   * Get font size token
   */
  getFontSize(size: keyof typeof designTokens.typography.fontSize): string {
    return designTokens.typography.fontSize[size]
  },
  
  /**
   * Get font weight token
   */
  getFontWeight(weight: keyof typeof designTokens.typography.fontWeight): number {
    return designTokens.typography.fontWeight[weight]
  },
  
  /**
   * Get line height token
   */
  getLineHeight(height: keyof typeof designTokens.typography.lineHeight): number {
    return designTokens.typography.lineHeight[height]
  },
  
  /**
   * Generate typography CSS variables
   */
  generateTypographyVars(): Record<string, string> {
    return {
      ...tokensToCSSVars(designTokens.typography.fontSize, 'font-size'),
      ...tokensToCSSVars(designTokens.typography.fontWeight, 'font-weight'),
      ...tokensToCSSVars(designTokens.typography.lineHeight, 'line-height'),
    }
  },
}

/**
 * Spacing utility functions
 */
export const spacingUtils = {
  /**
   * Get spacing token
   */
  getSpacing(size: keyof typeof designTokens.spacing): string {
    return designTokens.spacing[size]
  },
  
  /**
   * Get spacing CSS variable
   */
  getSpacingVar(size: keyof typeof designTokens.spacing): string {
    return getCSSVar(`spacing-${size}`)
  },
  
  /**
   * Generate margin utilities
   */
  generateMarginUtils(): Record<string, string> {
    const utils: Record<string, string> = {}
    Object.keys(designTokens.spacing).forEach(key => {
      const value = getCSSVar(`spacing-${key}`)
      utils[`.m-${key}`] = `margin: ${value};`
      utils[`.mt-${key}`] = `margin-top: ${value};`
      utils[`.mr-${key}`] = `margin-right: ${value};`
      utils[`.mb-${key}`] = `margin-bottom: ${value};`
      utils[`.ml-${key}`] = `margin-left: ${value};`
      utils[`.mx-${key}`] = `margin-left: ${value}; margin-right: ${value};`
      utils[`.my-${key}`] = `margin-top: ${value}; margin-bottom: ${value};`
    })
    return utils
  },
  
  /**
   * Generate padding utilities
   */
  generatePaddingUtils(): Record<string, string> {
    const utils: Record<string, string> = {}
    Object.keys(designTokens.spacing).forEach(key => {
      const value = getCSSVar(`spacing-${key}`)
      utils[`.p-${key}`] = `padding: ${value};`
      utils[`.pt-${key}`] = `padding-top: ${value};`
      utils[`.pr-${key}`] = `padding-right: ${value};`
      utils[`.pb-${key}`] = `padding-bottom: ${value};`
      utils[`.pl-${key}`] = `padding-left: ${value};`
      utils[`.px-${key}`] = `padding-left: ${value}; padding-right: ${value};`
      utils[`.py-${key}`] = `padding-top: ${value}; padding-bottom: ${value};`
    })
    return utils
  },
}

/**
 * Responsive design utilities
 */
export const responsiveUtils = {
  /**
   * Get breakpoint value
   */
  getBreakpoint(size: keyof typeof designTokens.breakpoints): string {
    return designTokens.breakpoints[size]
  },
  
  /**
   * Generate media query for breakpoint
   */
  mediaQuery(size: keyof typeof designTokens.breakpoints): string {
    return `@media (min-width: ${designTokens.breakpoints[size]})`
  },
  
  /**
   * Generate responsive CSS classes
   */
  generateResponsiveClasses(
    baseClass: string, 
    property: string, 
    values: Record<string, string>
  ): Record<string, string> {
    const classes: Record<string, string> = {}
    
    // Base classes
    Object.entries(values).forEach(([key, value]) => {
      classes[`.${baseClass}-${key}`] = `${property}: ${value};`
    })
    
    // Responsive classes
    Object.keys(designTokens.breakpoints).forEach(breakpoint => {
      const mediaQuery = responsiveUtils.mediaQuery(breakpoint as keyof typeof designTokens.breakpoints)
      Object.entries(values).forEach(([key, value]) => {
        classes[`.${breakpoint}\\:${baseClass}-${key}`] = `${mediaQuery} { ${property}: ${value}; }`
      })
    })
    
    return classes
  },
}

/**
 * RTL/Arabic utilities
 */
export const rtlUtils = {
  /**
   * Get directional CSS property
   */
  getDirectionalProperty(
    property: string, 
    ltrValue: string, 
    rtlValue: string
  ): Record<string, string> {
    return {
      [property]: ltrValue,
      [`[dir="rtl"] &`]: {
        [property]: rtlValue
      }
    }
  },
  
  /**
   * Get logical CSS property (modern approach)
   */
  getLogicalProperty(
    property: 'margin' | 'padding' | 'border',
    direction: 'start' | 'end',
    value: string
  ): Record<string, string> {
    const logicalProps = {
      margin: {
        start: 'margin-inline-start',
        end: 'margin-inline-end'
      },
      padding: {
        start: 'padding-inline-start', 
        end: 'padding-inline-end'
      },
      border: {
        start: 'border-inline-start',
        end: 'border-inline-end'
      }
    }
    
    return {
      [logicalProps[property][direction]]: value
    }
  },
  
  /**
   * Generate RTL-aware spacing utilities
   */
  generateRTLSpacingUtils(): Record<string, string> {
    const utils: Record<string, string> = {}
    
    Object.keys(designTokens.spacing).forEach(key => {
      const value = getCSSVar(`spacing-${key}`)
      
      // Logical margin utilities
      utils[`.ms-${key}`] = `margin-inline-start: ${value};`
      utils[`.me-${key}`] = `margin-inline-end: ${value};`
      
      // Logical padding utilities
      utils[`.ps-${key}`] = `padding-inline-start: ${value};`
      utils[`.pe-${key}`] = `padding-inline-end: ${value};`
    })
    
    return utils
  },
}

/**
 * Component token utilities
 */
export const componentUtils = {
  /**
   * Get component token
   */
  getComponentToken(component: string, property: string, variant: string = 'md'): string {
    return getToken(`components.${component}.${property}.${variant}`) as string || 'auto'
  },
  
  /**
   * Generate component CSS variables
   */
  generateComponentVars(component: keyof typeof designTokens.components): Record<string, string> {
    return tokensToCSSVars(designTokens.components[component], component)
  },
}

/**
 * Animation utilities
 */
export const animationUtils = {
  /**
   * Get duration token
   */
  getDuration(duration: keyof typeof designTokens.motion.duration): string {
    return designTokens.motion.duration[duration]
  },
  
  /**
   * Get easing token
   */
  getEasing(easing: keyof typeof designTokens.motion.easing): string {
    return designTokens.motion.easing[easing]
  },
  
  /**
   * Create transition string
   */
  createTransition(
    property: string,
    duration: keyof typeof designTokens.motion.duration = '200',
    easing: keyof typeof designTokens.motion.easing = 'out'
  ): string {
    return `${property} ${designTokens.motion.duration[duration]} ${designTokens.motion.easing[easing]}`
  },
  
  /**
   * Generate transition utilities
   */
  generateTransitionUtils(): Record<string, string> {
    return {
      '.transition-none': 'transition: none;',
      '.transition-all': `transition: all ${designTokens.motion.duration[200]} ${designTokens.motion.easing.out};`,
      '.transition-colors': `transition: color ${designTokens.motion.duration[200]} ${designTokens.motion.easing.out}, background-color ${designTokens.motion.duration[200]} ${designTokens.motion.easing.out}, border-color ${designTokens.motion.duration[200]} ${designTokens.motion.easing.out};`,
      '.transition-opacity': `transition: opacity ${designTokens.motion.duration[200]} ${designTokens.motion.easing.out};`,
      '.transition-transform': `transition: transform ${designTokens.motion.duration[200]} ${designTokens.motion.easing.out};`,
    }
  },
}

/**
 * Theme utilities
 */
export const themeUtils = {
  /**
   * Apply design tokens to document
   */
  applyTokensToDocument(customTokens?: Record<string, string>): void {
    const root = document.documentElement
    const allTokens = {
      ...tokensToCSSVars(designTokens.colors.semantic, 'color'),
      ...tokensToCSSVars(designTokens.spacing, 'spacing'),
      ...tokensToCSSVars(designTokens.borderRadius, 'radius'),
      ...customTokens
    }
    
    Object.entries(allTokens).forEach(([property, value]) => {
      root.style.setProperty(property, value)
    })
  },
  
  /**
   * Toggle theme
   */
  toggleTheme(theme: 'light' | 'dark'): void {
    document.documentElement.setAttribute('data-theme', theme)
  },
  
  /**
   * Toggle contrast
   */
  toggleContrast(contrast: 'normal' | 'high'): void {
    document.documentElement.setAttribute('data-contrast', contrast)
  },
  
  /**
   * Apply Arabic layout
   */
  applyArabicLayout(enabled: boolean): void {
    const root = document.documentElement
    if (enabled) {
      root.dir = 'rtl'
      root.classList.add('arabic-layout')
      root.style.setProperty('--font-family-primary', 'var(--font-family-arabic)')
    } else {
      root.dir = 'ltr'
      root.classList.remove('arabic-layout')
      root.style.setProperty('--font-family-primary', 'var(--font-family-latin)')
    }
  },
}

/**
 * Complete utility export
 */
export const designSystemUtils = {
  token: {
    get: getToken,
    cssVar: getCSSVar,
    toCSSVars: tokensToCSSVars,
  },
  color: colorUtils,
  typography: typographyUtils,
  spacing: spacingUtils,
  responsive: responsiveUtils,
  rtl: rtlUtils,
  component: componentUtils,
  animation: animationUtils,
  theme: themeUtils,
}

export default designSystemUtils