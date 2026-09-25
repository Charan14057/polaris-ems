/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#FBF9F5',
          subtle: '#F6F3EC',
          muted: '#EFECE3',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          raised: '#FFFFFF',
          inset: '#F4F1EA',
        },
        ink: {
          primary: '#1C1917',
          secondary: '#44403C',
          muted: '#78716C',
          subtle: '#A8A29E',
          inverse: '#FAFAF9',
        },
        copper: {
          DEFAULT: '#B45309',
          dark: '#92400E',
          light: '#D97706',
          soft: '#FEF3C7',
          subtle: '#FFFBEB',
        },
        ice: {
          DEFAULT: '#0284C7',
          dark: '#0369A1',
          light: '#38BDF8',
          soft: '#E0F2FE',
          subtle: '#F0F9FF',
        },
        teal: {
          DEFAULT: '#0F766E',
          dark: '#115E59',
          soft: '#CCFBF1',
          subtle: '#F0FDFA',
        },
        moss: {
          DEFAULT: '#15803D',
          dark: '#166534',
          soft: '#DCFCE7',
          subtle: '#F0FDF4',
        },
        border: {
          subtle: '#E7E2D6',
          DEFAULT: '#DDD6C6',
          strong: '#BCB39E',
          dark: '#292524',
        },
        // Operational Status mapping
        state: {
          safe: '#15803D',
          watch: '#0284C7',
          atrisk: '#B45309',
          threatened: '#C2410C',
          critical: '#B91C1C',
          recovery: '#4338CA',
          blocked: '#64748B',
        },
        resource: {
          solar: '#D97706',
          wind: '#0284C7',
          diesel: '#B45309',
          battery: '#15803D',
          thermal: '#BE185D',
          fuel: '#78716C',
          grid: '#4338CA',
        },
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Georgia', '"Times New Roman"', 'serif'],
        sans: ['"IBM Plex Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        sheet: '0 1px 3px rgba(28, 25, 23, 0.05), 0 1px 2px rgba(28, 25, 23, 0.03)',
        raised: '0 4px 6px -1px rgba(28, 25, 23, 0.07), 0 2px 4px -2px rgba(28, 25, 23, 0.05)',
        floating: '0 12px 24px -4px rgba(28, 25, 23, 0.09), 0 4px 8px -2px rgba(28, 25, 23, 0.04)',
      },
    },
  },
  plugins: [],
}
