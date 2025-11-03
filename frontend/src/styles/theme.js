/**
 * MediScan AI - Professional Design System
 * Modern medical UI theme with glassmorphism and gradients
 */

export const theme = {
  // Color Palette
  colors: {
    // Primary - Medical Blue
    primary: {
      50: '#E6F2FF',
      100: '#CCE5FF',
      200: '#99CCFF',
      300: '#66B3FF',
      400: '#3399FF',
      500: '#0080FF',
      600: '#0066CC',
      700: '#004D99',
      800: '#003366',
      900: '#001A33',
    },
    
    // Secondary - Medical Green
    secondary: {
      50: '#E6F9F0',
      100: '#CCF3E1',
      200: '#99E7C3',
      300: '#66DBA5',
      400: '#33CF87',
      500: '#00C368',
      600: '#009C54',
      700: '#00753F',
      800: '#004E2A',
      900: '#002715',
    },
    
    // Accent - Purple
    accent: {
      50: '#F3E6FF',
      100: '#E7CCFF',
      200: '#CF99FF',
      300: '#B766FF',
      400: '#9F33FF',
      500: '#8700FF',
      600: '#6C00CC',
      700: '#510099',
      800: '#360066',
      900: '#1B0033',
    },
    
    // Neutrals
    gray: {
      50: '#F9FAFB',
      100: '#F3F4F6',
      200: '#E5E7EB',
      300: '#D1D5DB',
      400: '#9CA3AF',
      500: '#6B7280',
      600: '#4B5563',
      700: '#374151',
      800: '#1F2937',
      900: '#111827',
    },
    
    // Semantic
    success: '#00C368',
    warning: '#FFB020',
    error: '#FF4757',
    info: '#0080FF',
  },
  
  // Typography
  typography: {
    fontFamily: {
      sans: "'Inter', 'Segoe UI', system-ui, sans-serif",
      mono: "'JetBrains Mono', 'Fira Code', monospace",
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
  },
  
  // Spacing
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },
  
  // Border Radius
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    '2xl': '1.5rem',
    full: '9999px',
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    glow: '0 0 20px rgba(0, 128, 255, 0.3)',
    glowPurple: '0 0 20px rgba(135, 0, 255, 0.3)',
  },
  
  // Gradients
  gradients: {
    primary: 'linear-gradient(135deg, #0080FF 0%, #0066CC 100%)',
    secondary: 'linear-gradient(135deg, #00C368 0%, #009C54 100%)',
    accent: 'linear-gradient(135deg, #9F33FF 0%, #6C00CC 100%)',
    medical: 'linear-gradient(135deg, #0080FF 0%, #00C368 50%, #9F33FF 100%)',
    sunset: 'linear-gradient(135deg, #FF6B6B 0%, #FFB020 100%)',
    ocean: 'linear-gradient(135deg, #0080FF 0%, #00C368 100%)',
    purple: 'linear-gradient(135deg, #9F33FF 0%, #FF6B9D 100%)',
    glass: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
  },
  
  // Glassmorphism
  glass: {
    background: 'rgba(255, 255, 255, 0.1)',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
  },
  
  // Animations
  animations: {
    fadeIn: 'fadeIn 0.3s ease-in-out',
    slideUp: 'slideUp 0.4s ease-out',
    slideDown: 'slideDown 0.4s ease-out',
    scaleIn: 'scaleIn 0.2s ease-out',
    pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  },
};

export default theme;

