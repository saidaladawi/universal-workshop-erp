/**
 * Design Tokens - Universal Workshop Frontend V2
 * 
 * Comprehensive design token system providing the foundation for all components.
 * Tokens are organized by category and support dynamic theming and Arabic/RTL layouts.
 */

// Base Color Palette
export const baseColors = {
  // Primary Blues
  blue: {
    50: '#e3f2fd',
    100: '#bbdefb',
    200: '#90caf9',
    300: '#64b5f6',
    400: '#42a5f5',
    500: '#2196f3',
    600: '#1e88e5',
    700: '#1976d2',
    800: '#1565c0',
    900: '#0d47a1',
  },
  
  // Secondary Colors
  indigo: {
    50: '#e8eaf6',
    100: '#c5cae9',
    200: '#9fa8da',
    300: '#7986cb',
    400: '#5c6bc0',
    500: '#3f51b5',
    600: '#3949ab',
    700: '#303f9f',
    800: '#283593',
    900: '#1a237e',
  },
  
  // Success Greens
  green: {
    50: '#e8f5e8',
    100: '#c8e6c9',
    200: '#a5d6a7',
    300: '#81c784',
    400: '#66bb6a',
    500: '#4caf50',
    600: '#43a047',
    700: '#388e3c',
    800: '#2e7d32',
    900: '#1b5e20',
  },
  
  // Warning Oranges
  orange: {
    50: '#fff3e0',
    100: '#ffe0b2',
    200: '#ffcc80',
    300: '#ffb74d',
    400: '#ffa726',
    500: '#ff9800',
    600: '#fb8c00',
    700: '#f57c00',
    800: '#ef6c00',
    900: '#e65100',
  },
  
  // Error Reds
  red: {
    50: '#ffebee',
    100: '#ffcdd2',
    200: '#ef9a9a',
    300: '#e57373',
    400: '#ef5350',
    500: '#f44336',
    600: '#e53935',
    700: '#d32f2f',
    800: '#c62828',
    900: '#b71c1c',
  },
  
  // Neutral Grays
  gray: {
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
  
  // Arabic-specific Colors
  arabicGold: {
    50: '#fefcf3',
    100: '#fdf4d3',
    200: '#fce7a6',
    300: '#fad679',
    400: '#f8c647',
    500: '#f6b73d', // Traditional Arabic gold
    600: '#e09b2d',
    700: '#ca841f',
    800: '#b86f14',
    900: '#a65c0a',
  },
  
  // Cultural Colors
  cultural: {
    omanGreen: '#006a4e', // Omani flag green
    omanRed: '#ed1c24',   // Omani flag red
    omanWhite: '#ffffff', // Omani flag white
    islamicGreen: '#009639', // Traditional Islamic green
    arabicBrown: '#8b4513', // Traditional Arabic brown
  }
} as const

// Semantic Color System
export const semanticColors = {
  primary: {
    lighter: baseColors.blue[100],
    light: baseColors.blue[300],
    base: baseColors.blue[500],
    dark: baseColors.blue[700],
    darker: baseColors.blue[900],
  },
  
  secondary: {
    lighter: baseColors.indigo[100],
    light: baseColors.indigo[300],
    base: baseColors.indigo[500],
    dark: baseColors.indigo[700],
    darker: baseColors.indigo[900],
  },
  
  success: {
    lighter: baseColors.green[100],
    light: baseColors.green[300],
    base: baseColors.green[500],
    dark: baseColors.green[700],
    darker: baseColors.green[900],
  },
  
  warning: {
    lighter: baseColors.orange[100],
    light: baseColors.orange[300],
    base: baseColors.orange[500],
    dark: baseColors.orange[700],
    darker: baseColors.orange[900],
  },
  
  error: {
    lighter: baseColors.red[100],
    light: baseColors.red[300],
    base: baseColors.red[500],
    dark: baseColors.red[700],
    darker: baseColors.red[900],
  },
  
  neutral: {
    white: '#ffffff',
    lighter: baseColors.gray[50],
    light: baseColors.gray[200],
    base: baseColors.gray[500],
    dark: baseColors.gray[700],
    darker: baseColors.gray[900],
    black: '#000000',
  },
  
  accent: {
    arabic: baseColors.arabicGold[500],
    cultural: baseColors.cultural.omanGreen,
    highlight: baseColors.arabicGold[300],
  }
} as const

// Typography System
export const typography = {
  fontFamily: {
    // Arabic Fonts (RTL)
    arabic: {
      primary: ['Cairo', 'Amiri', 'Noto Sans Arabic', 'sans-serif'],
      serif: ['Amiri', 'Noto Serif Arabic', 'serif'],
      display: ['Cairo', 'Tajawal', 'sans-serif'],
      mono: ['JetBrains Mono', 'Courier New', 'monospace'],
    },
    
    // Latin Fonts (LTR)
    latin: {
      primary: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
      serif: ['Playfair Display', 'Georgia', 'serif'],
      display: ['Inter', 'Helvetica Neue', 'sans-serif'],
      mono: ['JetBrains Mono', 'Monaco', 'Consolas', 'monospace'],
    },
  },
  
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
    '5xl': '3rem',      // 48px
    '6xl': '3.75rem',   // 60px
    '7xl': '4.5rem',    // 72px
  },
  
  fontWeight: {
    thin: 100,
    extralight: 200,
    light: 300,
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
    black: 900,
  },
  
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
  
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
} as const

// Spacing System
export const spacing = {
  0: '0',
  px: '1px',
  0.5: '0.125rem',   // 2px
  1: '0.25rem',      // 4px
  1.5: '0.375rem',   // 6px
  2: '0.5rem',       // 8px
  2.5: '0.625rem',   // 10px
  3: '0.75rem',      // 12px
  3.5: '0.875rem',   // 14px
  4: '1rem',         // 16px
  5: '1.25rem',      // 20px
  6: '1.5rem',       // 24px
  7: '1.75rem',      // 28px
  8: '2rem',         // 32px
  9: '2.25rem',      // 36px
  10: '2.5rem',      // 40px
  11: '2.75rem',     // 44px
  12: '3rem',        // 48px
  14: '3.5rem',      // 56px
  16: '4rem',        // 64px
  20: '5rem',        // 80px
  24: '6rem',        // 96px
  28: '7rem',        // 112px
  32: '8rem',        // 128px
  36: '9rem',        // 144px
  40: '10rem',       // 160px
  44: '11rem',       // 176px
  48: '12rem',       // 192px
  52: '13rem',       // 208px
  56: '14rem',       // 224px
  60: '15rem',       // 240px
  64: '16rem',       // 256px
  72: '18rem',       // 288px
  80: '20rem',       // 320px
  96: '24rem',       // 384px
} as const

// Border Radius
export const borderRadius = {
  none: '0',
  sm: '0.125rem',     // 2px
  base: '0.25rem',    // 4px
  md: '0.375rem',     // 6px
  lg: '0.5rem',       // 8px
  xl: '0.75rem',      // 12px
  '2xl': '1rem',      // 16px
  '3xl': '1.5rem',    // 24px
  full: '9999px',
} as const

// Shadows
export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  none: 'none',
} as const

// Animation & Motion
export const motion = {
  duration: {
    75: '75ms',
    100: '100ms',
    150: '150ms',
    200: '200ms',
    300: '300ms',
    500: '500ms',
    700: '700ms',
    1000: '1000ms',
  },
  
  easing: {
    linear: 'linear',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  scale: {
    0: '0',
    50: '.5',
    75: '.75',
    90: '.9',
    95: '.95',
    100: '1',
    105: '1.05',
    110: '1.1',
    125: '1.25',
    150: '1.5',
  },
} as const

// Breakpoints for Responsive Design
export const breakpoints = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const

// Z-Index Scale
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const

// Component-Specific Tokens
export const componentTokens = {
  button: {
    height: {
      sm: spacing[8],    // 32px
      md: spacing[10],   // 40px
      lg: spacing[12],   // 48px
      xl: spacing[14],   // 56px
    },
    
    padding: {
      sm: `${spacing[2]} ${spacing[3]}`,
      md: `${spacing[2.5]} ${spacing[4]}`,
      lg: `${spacing[3]} ${spacing[6]}`,
      xl: `${spacing[4]} ${spacing[8]}`,
    },
    
    borderRadius: {
      sm: borderRadius.sm,
      md: borderRadius.base,
      lg: borderRadius.md,
      xl: borderRadius.lg,
    },
  },
  
  input: {
    height: {
      sm: spacing[8],
      md: spacing[10],
      lg: spacing[12],
    },
    
    padding: {
      sm: `${spacing[1.5]} ${spacing[2.5]}`,
      md: `${spacing[2]} ${spacing[3]}`,
      lg: `${spacing[2.5]} ${spacing[3.5]}`,
    },
    
    borderRadius: borderRadius.base,
  },
  
  card: {
    padding: {
      sm: spacing[4],
      md: spacing[6],
      lg: spacing[8],
    },
    
    borderRadius: borderRadius.lg,
    shadow: shadows.base,
  },
  
  modal: {
    borderRadius: borderRadius.xl,
    shadow: shadows['2xl'],
    backdrop: 'rgba(0, 0, 0, 0.5)',
  },
} as const

// Arabic/RTL Specific Tokens
export const arabicTokens = {
  direction: {
    ltr: 'ltr',
    rtl: 'rtl',
  },
  
  textAlign: {
    start: 'start',
    end: 'end',
    right: 'right',
    left: 'left',
    center: 'center',
  },
  
  spacing: {
    // RTL-aware spacing utilities
    marginStart: 'margin-inline-start',
    marginEnd: 'margin-inline-end',
    paddingStart: 'padding-inline-start',
    paddingEnd: 'padding-inline-end',
  },
  
  borders: {
    // RTL-aware border utilities
    borderStart: 'border-inline-start',
    borderEnd: 'border-inline-end',
  },
} as const

// Complete Design Token Export
export const designTokens = {
  colors: {
    base: baseColors,
    semantic: semanticColors,
  },
  typography,
  spacing,
  borderRadius,
  shadows,
  motion,
  breakpoints,
  zIndex,
  components: componentTokens,
  arabic: arabicTokens,
} as const

// Type definitions for design tokens
export type DesignTokens = typeof designTokens
export type SemanticColors = typeof semanticColors
export type Typography = typeof typography
export type Spacing = typeof spacing
export type ComponentTokens = typeof componentTokens

export default designTokens