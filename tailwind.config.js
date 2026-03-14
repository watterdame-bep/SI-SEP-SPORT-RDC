/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './core/templates/**/*.html',
    './gouvernance/templates/**/*.html',
    './infrastructures/templates/**/*.html',
    './referentiel_geo/templates/**/*.html',
    './public/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        'rdc-blue': '#0036ca',
        'rdc-blue-hover': '#0028a0',
        'rdc-blue-dark': '#002a9e',
        'rdc-blue-darker': '#001f7a',
        'rdc-yellow': '#FDE015',
        'rdc-red': '#ED1C24',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 8px 30px rgb(0 0 0 / 0.04)',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
