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
          DEFAULT: '#F8FAFC', // Slate 50
          subtle: '#F1F5F9',  // Slate 100
          muted: '#E2E8F0',   // Slate 200
        },
        surface: {
          DEFAULT: '#FFFFFF',
          raised: '#FFFFFF',
          inset: '#F8FAFC',
        },
        ink: {
          primary: '#0F172A',   // Slate 900
          secondary: '#334155', // Slate 700
          muted: '#64748B',     // Slate 500
          subtle: '#94A3B8',    // Slate 400
          inverse: '#FFFFFF',
        },
        brand: {
          DEFAULT: '#0284C7', // Sky 600
          dark: '#0369A1',    // Sky 700
          light: '#38BDF8',   // Sky 400
          soft: '#E0F2FE',    // Sky 100
          subtle: '#F0F9FF',  // Sky 50
        },
        // Restrained utility accents
        ice: {
          DEFAULT: '#0284C7',
          dark: '#0369A1',
          light: '#38BDF8',
          soft: '#E0F2FE',
          subtle: '#F0F9FF',
        },
        teal: {
          DEFAULT: '#0F766E', // Deep Teal (Renewables)
          dark: '#115E59',
          soft: '#CCFBF1',
          subtle: '#F0FDFA',
        },
        copper: {
          DEFAULT: '#D97706', // Reserved for amber/diesel/warning state
          dark: '#B45309',
          light: '#F59E0B',
          soft: '#FEF3C7',
          subtle: '#FFFBEB',
        },
        moss: {
          DEFAULT: '#16A34A', // Green 600
          dark: '#15803D',
          soft: '#DCFCE7',
          subtle: '#F0FDF4',
        },
        border: {
          subtle: '#F1F5F9',
          DEFAULT: '#E2E8F0', // Slate 200
          strong: '#CBD5E1', // Slate 300
          dark: '#1E293B',
        },
        // Operational Status mapping
        state: {
          safe: '#16A34A',
          watch: '#0284C7',
          atrisk: '#D97706',
          threatened: '#EA580C',
          critical: '#DC2626',
          recovery: '#4F46E5',
          blocked: '#64748B',
        },
        resource: {
          solar: '#D97706',
          wind: '#0284C7',
          diesel: '#B45309',
          battery: '#16A34A',
          thermal: '#9333EA',
          fuel: '#64748B',
          grid: '#4F46E5',
        },
      },
      fontFamily: {
        sans: ['"Inter"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sheet: '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)',
        raised: '0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
        floating: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)',
      },
    },
  },
  plugins: [],
}
