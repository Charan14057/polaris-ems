/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        polar: {
          950: '#070b14',
          900: '#0a0f1d',
          850: '#0f172a',
          800: '#111827',
          750: '#151f33',
          700: '#1e293b',
          600: '#334155',
          500: '#475569',
          400: '#94a3b8',
          300: '#cbd5e1',
          200: '#e2e8f0',
          100: '#f1f5f9',
          50: '#f8fafc',
        },
        state: {
          safe: '#10b981',
          watch: '#3b82f6',
          atrisk: '#f59e0b',
          threatened: '#f97316',
          critical: '#ef4444',
          recovery: '#8b5cf6',
          blocked: '#64748b',
        },
        resource: {
          solar: '#eab308',
          wind: '#06b6d4',
          diesel: '#f97316',
          battery: '#10b981',
          thermal: '#ec4899',
          fuel: '#64748b',
          grid: '#3b82f6',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
