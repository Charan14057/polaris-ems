/**
 * POLARIS-EMS DESIGN SYSTEM TOKENS
 * Direction: Copper × Ice (Editorial Control Room)
 * Light-first, warm material palette with Indian mineral accents and polar precision.
 */

export const colors = {
  // Canvas & Surfaces
  canvas: {
    DEFAULT: '#FBF9F5', // Warm Ivory / Alabaster
    subtle: '#F6F3EC',  // Soft Parchment
    muted: '#EFECE3',   // Muted Sandstone
  },
  surface: {
    DEFAULT: '#FFFFFF', // Crisp Chalk White
    raised: '#FFFFFF',  // Elevated Card Sheet
    inset: '#F4F1EA',   // Inset Technical Plate
    overlay: 'rgba(251, 249, 245, 0.94)',
  },
  // Typography Ink
  ink: {
    primary: '#1C1917',   // Deep Mineral Charcoal (Stone 900)
    secondary: '#44403C', // Weathered Iron (Stone 700)
    muted: '#78716C',     // Technical Caption (Stone 500)
    subtle: '#A8A29E',    // Alignment Mark / Watermark (Stone 400)
    inverse: '#FAFAF9',   // Crisp White for high-contrast pills
  },
  // Signature Accents
  copper: {
    DEFAULT: '#B45309', // Burnished Terracotta Copper (Amber 700)
    dark: '#92400E',    // Deep Copper
    light: '#D97706',   // Radiant Copper
    soft: '#FEF3C7',    // Warm Amber Wash (Amber 100)
    subtle: '#FFFBEB',  // Pale Tint (Amber 50)
  },
  ice: {
    DEFAULT: '#0284C7', // Antarctic Glacial Ice (Sky 600)
    dark: '#0369A1',    // Deep Polar Crevasse (Sky 700)
    light: '#38BDF8',   // Surface Ice Reflection
    soft: '#E0F2FE',    // Glacial Mist Wash (Sky 100)
    subtle: '#F0F9FF',  // Pale Ice Tint (Sky 50)
  },
  teal: {
    DEFAULT: '#0F766E', // Himalayan Mineral Teal (Teal 700)
    dark: '#115E59',    // Deep Pine Teal
    soft: '#CCFBF1',    // Sage Mist (Teal 100)
    subtle: '#F0FDFA',
  },
  moss: {
    DEFAULT: '#15803D', // Arctic Lichen Moss (Green 700)
    dark: '#166534',
    soft: '#DCFCE7',
    subtle: '#F0FDF4',
  },
  // Operational Status Tokens (Accessible WCAG 2.1 AA)
  status: {
    safe: {
      ink: '#166534',
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
      ink: '#92400E',
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
      ink: '#991B1B',
      bg: '#FEF2F2',
      border: '#FECACA',
      dot: '#DC2626',
    },
    recovery: {
      ink: '#3730A3',
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
    subtle: '#E7E2D6',  // Delicate Paper Edge
    DEFAULT: '#DDD6C6', // Architectural Divider
    strong: '#BCB39E',  // Emphasized Technical Border
    dark: '#292524',    // High-contrast Anchor
  },
  // Subsystem Generation Colors
  generation: {
    solar: '#D97706',
    wind: '#0284C7',
    diesel: '#B45309',
    battery: '#15803D',
    thermal: '#BE185D',
    grid: '#4F46E5',
  },
};

export const typography = {
  fontSerif: '"Cormorant Garamond", Georgia, "Times New Roman", serif',
  fontSans: '"IBM Plex Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontMono: '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  scale: {
    displayXl: 'clamp(2.5rem, 4vw, 3.75rem)',
    displayL: 'clamp(2rem, 3vw, 2.75rem)',
    displayM: 'clamp(1.5rem, 2.5vw, 2.125rem)',
    headingL: '1.5rem',
    headingM: '1.25rem',
    headingS: '1rem',
    bodyL: '1.125rem',
    body: '0.9375rem',
    bodyS: '0.8125rem',
    caption: '0.75rem',
    micro: '0.6875rem',
  },
};

export const spacing = {
  unit: 8,
  layout: {
    gutter: 'clamp(1rem, 2vw, 2rem)',
    maxWidth: '1520px',
  },
};

export const radii = {
  none: '0px',
  subtle: '2px',
  sm: '4px',
  md: '6px',
  lg: '8px',
  pill: '9999px',
};

export const shadows = {
  sheet: '0 1px 3px rgba(28, 25, 23, 0.05), 0 1px 2px rgba(28, 25, 23, 0.03)',
  raised: '0 4px 6px -1px rgba(28, 25, 23, 0.07), 0 2px 4px -2px rgba(28, 25, 23, 0.05)',
  floating: '0 12px 24px -4px rgba(28, 25, 23, 0.09), 0 4px 8px -2px rgba(28, 25, 23, 0.04)',
  inset: 'inset 0 1px 2px rgba(28, 25, 23, 0.04)',
};

export const motion = {
  micro: '140ms cubic-bezier(0.16, 1, 0.3, 1)',
  hover: '180ms cubic-bezier(0.16, 1, 0.3, 1)',
  panel: '240ms cubic-bezier(0.16, 1, 0.3, 1)',
  drawer: '320ms cubic-bezier(0.16, 1, 0.3, 1)',
  page: '380ms cubic-bezier(0.16, 1, 0.3, 1)',
};

export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1440px',
  '3xl': '1600px',
};
