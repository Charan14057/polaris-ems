/**
 * POLARIS-EMS DESIGN SYSTEM TOKENS
 * Direction: Quiet Industrial / Arctic Utility
 * Clean white/cool-gray canvas, deep slate typography, restrained blue/teal accents.
 */

export const colors = {
  // Canvas & Surfaces
  canvas: {
    DEFAULT: '#F8FAFC', // Slate 50
    subtle: '#F1F5F9',  // Slate 100
    muted: '#E2E8F0',   // Slate 200
  },
  surface: {
    DEFAULT: '#FFFFFF', // Pure White
    raised: '#FFFFFF',  // Elevated Card Sheet
    inset: '#F8FAFC',   // Inset Slate Plate
    overlay: 'rgba(15, 23, 42, 0.4)',
  },
  // Typography Ink
  ink: {
    primary: '#0F172A',   // Slate 900
    secondary: '#334155', // Slate 700
    muted: '#64748B',     // Slate 500
    subtle: '#94A3B8',    // Slate 400
    inverse: '#FFFFFF',   // White
  },
  // Signature Accents
  brand: {
    DEFAULT: '#0284C7', // Sky 600
    dark: '#0369A1',    // Sky 700
    light: '#38BDF8',   // Sky 400
    soft: '#E0F2FE',    // Sky 100
    subtle: '#F0F9FF',  // Sky 50
  },
  ice: {
    DEFAULT: '#0284C7',
    dark: '#0369A1',
    light: '#38BDF8',
    soft: '#E0F2FE',
    subtle: '#F0F9FF',
  },
  teal: {
    DEFAULT: '#0F766E', // Renewable Deep Teal
    dark: '#115E59',
    soft: '#CCFBF1',
    subtle: '#F0FDFA',
  },
  copper: {
    DEFAULT: '#D97706', // Alert & Diesel Amber
    dark: '#B45309',
    light: '#F59E0B',
    soft: '#FEF3C7',
    subtle: '#FFFBEB',
  },
  moss: {
    DEFAULT: '#16A34A', // Green
    dark: '#15803D',
    soft: '#DCFCE7',
    subtle: '#F0FDF4',
  },
  // Operational Status Tokens (Accessible WCAG 2.1 AA)
  status: {
    safe: {
      ink: '#15803D',
      bg: '#F0FDF4',
      border: '#BBF7D0',
      dot: '#16A34A',
    },
    watch: {
      ink: '#0369A1',
      bg: '#F0F9FF',
      border: '#BAE6FD',
      dot: '#0284C7',
    },
    atRisk: {
      ink: '#B45309',
      bg: '#FFFBEB',
      border: '#FDE68A',
      dot: '#D97706',
    },
    threatened: {
      ink: '#C2410C',
      bg: '#FFF7ED',
      border: '#FED7AA',
      dot: '#EA580C',
    },
    critical: {
      ink: '#B91C1C',
      bg: '#FEF2F2',
      border: '#FECACA',
      dot: '#DC2626',
    },
    recovery: {
      ink: '#4338CA',
      bg: '#EEF2FF',
      border: '#C7D2FE',
      dot: '#4F46E5',
    },
    blocked: {
      ink: '#475569',
      bg: '#F8FAFC',
      border: '#CBD5E1',
      dot: '#64748B',
    },
  },
  // Rules, Dividers & Outlines
  border: {
    subtle: '#F1F5F9',
    DEFAULT: '#E2E8F0', // Slate 200
    strong: '#CBD5E1', // Slate 300
    dark: '#1E293B',
  },
} as const;

export const typography = {
  fontFamily: {
    sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, monospace',
  },
  fontSize: {
    display: ['2.25rem', { lineHeight: '2.5rem', letterSpacing: '-0.02em' }],
    h1: ['1.875rem', { lineHeight: '2.25rem', letterSpacing: '-0.02em' }],
    h2: ['1.5rem', { lineHeight: '2rem', letterSpacing: '-0.01em' }],
    h3: ['1.25rem', { lineHeight: '1.75rem', letterSpacing: '-0.01em' }],
    h4: ['1.125rem', { lineHeight: '1.5rem', letterSpacing: '0em' }],
    body: ['0.875rem', { lineHeight: '1.25rem' }],
    bodySm: ['0.8125rem', { lineHeight: '1.125rem' }],
    caption: ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.01em' }],
    tiny: ['0.6875rem', { lineHeight: '0.875rem', letterSpacing: '0.02em' }],
  },
} as const;

export const spacing = {
  containerMax: '1520px',
  headerHeight: '52px',
  sidebarWidth: '240px',
  sidebarCollapsedWidth: '64px',
} as const;

export const radii = {
  xs: '0.125rem',
  sm: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
  full: '9999px',
} as const;

export const shadows = {
  card: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  sheet: '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)',
  raised: '0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
  floating: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)',
} as const;
