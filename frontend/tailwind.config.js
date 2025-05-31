/** @type {import('tailwindcss').Config} */
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    screens: {
      'xs': '375px',   // Small phones
      'sm': '640px',   // Large phones
      'md': '768px',   // Tablets
      'lg': '1024px',  // Laptops
      'xl': '1280px',  // Desktops
      '2xl': '1536px', // Large screens
    },
    extend: {
      colors: {
        'chatchonk': {
          'pink': {
            50: '#FFF0F5',
            100: '#FFE1EB',
            200: '#FFC3D7',
            300: '#FFA5C3',
            400: '#FF87AF',
            500: '#FF4B8C', // Primary pink
            600: '#E63574',
            700: '#CC1F5C',
            800: '#B30844',
            900: '#80062E',
          },
          'blue': {
            50: '#F0F7FF',
            100: '#E1EFFF',
            200: '#C3DFFF',
            300: '#A5CFFF',
            400: '#87BFFF',
            500: '#4A90F7', // Primary blue
            600: '#2C7BE5',
            700: '#1A66D3',
            800: '#0851C1',
            900: '#063C9C',
          },
          'yellow': {
            50: '#FFFCF0',
            100: '#FFF9E1',
            200: '#FFF3C3',
            300: '#FFEDA5',
            400: '#FFE787',
            500: '#FFB84D', // Primary yellow
            600: '#E69A2E',
            700: '#CC7C15',
            800: '#B35E00',
            900: '#804400',
          },
          'neutral': {
            50: '#F8F9FA',
            100: '#F1F3F4',
            200: '#E8EAED',
            300: '#DADCE0',
            400: '#BDC1C6',
            500: '#9AA0A6',
            600: '#80868B',
            700: '#5F6368',
            800: '#3C4043',
            900: '#1A1A1A', // Primary black
          }
        }
      },
      fontFamily: {
        'primary': ['Inter', ...defaultTheme.fontFamily.sans],
        'secondary': ['Poppins', ...defaultTheme.fontFamily.sans],
        'mono': ['JetBrains Mono', ...defaultTheme.fontFamily.mono],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1' }],
        '6xl': ['3.75rem', { lineHeight: '1' }],
      },
      boxShadow: {
        'brand': '0 4px 20px rgba(255, 75, 140, 0.15)',
        'brand-lg': '0 10px 40px rgba(255, 75, 140, 0.2)',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(to right, var(--chatchonk-pink-500), var(--chatchonk-blue-500))',
        'gradient-accent': 'linear-gradient(to right, var(--chatchonk-yellow-400), var(--chatchonk-pink-500))',
        'gradient-subtle': 'linear-gradient(to bottom right, var(--chatchonk-pink-50), var(--chatchonk-blue-50))',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'bounce-light': 'bounceLight 2s infinite',
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
        bounceLight: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
      },
      transitionProperty: {
        'height': 'height',
        'spacing': 'margin, padding',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      spacing: {
        '18': '4.5rem',
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      minHeight: {
        '0': '0',
        '1/4': '25%',
        '1/2': '50%',
        '3/4': '75%',
        'full': '100%',
        'screen-1/4': '25vh',
        'screen-1/2': '50vh',
        'screen-3/4': '75vh',
      },
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
    function ({ addUtilities, theme }) {
      const newUtilities = {
        '.transition-brand': {
          'transition-property': 'all',
          'transition-timing-function': 'cubic-bezier(0.4, 0, 0.2, 1)',
          'transition-duration': '300ms',
        },
        '.hover-lift': {
          'transition-property': 'transform',
          'transition-timing-function': 'cubic-bezier(0.4, 0, 0.2, 1)',
          'transition-duration': '200ms',
          '&:hover': {
            'transform': 'translateY(-0.25rem)',
          },
        },
        '.hover-scale': {
          'transition-property': 'transform',
          'transition-timing-function': 'cubic-bezier(0.4, 0, 0.2, 1)',
          'transition-duration': '200ms',
          '&:hover': {
            'transform': 'scale(1.05)',
          },
        },
        '.focus-brand': {
          '&:focus': {
            'outline': 'none',
            'ring': '4px',
            'ring-color': theme('colors.chatchonk.pink.200'),
            'border-color': theme('colors.chatchonk.pink.500'),
          },
        },
      };
      addUtilities(newUtilities);
    },
    function ({ addComponents, theme }) {
      const components = {
        '.btn-primary': {
          backgroundColor: theme('colors.chatchonk.pink.500'),
          color: theme('colors.white'),
          fontWeight: theme('fontWeight.medium'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          borderRadius: theme('borderRadius.xl'),
          transition: 'background-color 200ms',
          '&:hover': {
            backgroundColor: theme('colors.chatchonk.pink.600'),
          },
          '&:active': {
            backgroundColor: theme('colors.chatchonk.pink.700'),
          },
          '&:focus': {
            outline: 'none',
            boxShadow: `0 0 0 4px ${theme('colors.chatchonk.pink.200')}`,
          },
        },
        '.btn-secondary': {
          backgroundColor: theme('colors.chatchonk.blue.500'),
          color: theme('colors.white'),
          fontWeight: theme('fontWeight.medium'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          borderRadius: theme('borderRadius.xl'),
          transition: 'background-color 200ms',
          '&:hover': {
            backgroundColor: theme('colors.chatchonk.blue.600'),
          },
          '&:active': {
            backgroundColor: theme('colors.chatchonk.blue.700'),
          },
        },
        '.btn-accent': {
          backgroundColor: theme('colors.chatchonk.yellow.500'),
          color: theme('colors.chatchonk.neutral.900'),
          fontWeight: theme('fontWeight.medium'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          borderRadius: theme('borderRadius.xl'),
          transition: 'background-color 200ms',
          '&:hover': {
            backgroundColor: theme('colors.chatchonk.yellow.600'),
          },
          '&:active': {
            backgroundColor: theme('colors.chatchonk.yellow.700'),
          },
        },
        '.btn-ghost': {
          borderWidth: '2px',
          borderColor: theme('colors.chatchonk.pink.500'),
          color: theme('colors.chatchonk.pink.500'),
          fontWeight: theme('fontWeight.medium'),
          padding: `${theme('spacing.3')} ${theme('spacing.6')}`,
          borderRadius: theme('borderRadius.xl'),
          transition: 'all 200ms',
          '&:hover': {
            backgroundColor: theme('colors.chatchonk.pink.500'),
            color: theme('colors.white'),
          },
        },
        '.card': {
          backgroundColor: theme('colors.white'),
          borderRadius: theme('borderRadius.2xl'),
          boxShadow: theme('boxShadow.lg'),
          transition: 'box-shadow 300ms',
          padding: theme('spacing.6'),
          borderWidth: '1px',
          borderColor: theme('colors.chatchonk.neutral.200'),
          '&:hover': {
            boxShadow: theme('boxShadow.xl'),
          },
        },
        '.card-feature': {
          background: 'linear-gradient(to bottom right, var(--tw-gradient-stops))',
          '--tw-gradient-from': theme('colors.chatchonk.pink.50'),
          '--tw-gradient-to': theme('colors.chatchonk.blue.50'),
          '--tw-gradient-stops': 'var(--tw-gradient-from), var(--tw-gradient-to)',
          borderRadius: theme('borderRadius.2xl'),
          padding: theme('spacing.6'),
          borderWidth: '2px',
          borderColor: theme('colors.chatchonk.pink.200'),
        },
        // Typography classes
        '.heading-xl': {
          fontSize: theme('fontSize.4xl[0]'),
          lineHeight: theme('fontSize.4xl[1].lineHeight'),
          fontWeight: theme('fontWeight.bold'),
          fontFamily: theme('fontFamily.secondary').join(', '),
          '@screen md': {
            fontSize: theme('fontSize.5xl[0]'),
            lineHeight: theme('fontSize.5xl[1].lineHeight'),
          },
        },
        '.heading-lg': {
          fontSize: theme('fontSize.3xl[0]'),
          lineHeight: theme('fontSize.3xl[1].lineHeight'),
          fontWeight: theme('fontWeight.bold'),
          fontFamily: theme('fontFamily.secondary').join(', '),
          '@screen md': {
            fontSize: theme('fontSize.4xl[0]'),
            lineHeight: theme('fontSize.4xl[1].lineHeight'),
          },
        },
        '.heading-md': {
          fontSize: theme('fontSize.2xl[0]'),
          lineHeight: theme('fontSize.2xl[1].lineHeight'),
          fontWeight: theme('fontWeight.semibold'),
          fontFamily: theme('fontFamily.secondary').join(', '),
          '@screen md': {
            fontSize: theme('fontSize.3xl[0]'),
            lineHeight: theme('fontSize.3xl[1].lineHeight'),
          },
        },
        '.heading-sm': {
          fontSize: theme('fontSize.xl[0]'),
          lineHeight: theme('fontSize.xl[1].lineHeight'),
          fontWeight: theme('fontWeight.semibold'),
          fontFamily: theme('fontFamily.primary').join(', '),
          '@screen md': {
            fontSize: theme('fontSize.2xl[0]'),
            lineHeight: theme('fontSize.2xl[1].lineHeight'),
          },
        },
        '.body-lg': {
          fontSize: theme('fontSize.lg[0]'),
          lineHeight: theme('fontSize.lg[1].lineHeight'),
          fontFamily: theme('fontFamily.primary').join(', '),
        },
        '.body-md': {
          fontSize: theme('fontSize.base[0]'),
          lineHeight: theme('fontSize.base[1].lineHeight'),
          fontFamily: theme('fontFamily.primary').join(', '),
        },
        '.body-sm': {
          fontSize: theme('fontSize.sm[0]'),
          lineHeight: theme('fontSize.sm[1].lineHeight'),
          fontFamily: theme('fontFamily.primary').join(', '),
        },
        '.body-xs': {
          fontSize: theme('fontSize.xs[0]'),
          lineHeight: theme('fontSize.xs[1].lineHeight'),
          fontFamily: theme('fontFamily.primary').join(', '),
        },
        '.label-lg': {
          fontSize: theme('fontSize.sm[0]'),
          lineHeight: theme('fontSize.sm[1].lineHeight'),
          fontWeight: theme('fontWeight.medium'),
          fontFamily: theme('fontFamily.primary').join(', '),
          textTransform: 'uppercase',
          letterSpacing: theme('letterSpacing.wide'),
        },
        '.label-md': {
          fontSize: theme('fontSize.xs[0]'),
          lineHeight: theme('fontSize.xs[1].lineHeight'),
          fontWeight: theme('fontWeight.medium'),
          fontFamily: theme('fontFamily.primary').join(', '),
          textTransform: 'uppercase',
          letterSpacing: theme('letterSpacing.wide'),
        },
      };
      addComponents(components);
    },
  ],
}
