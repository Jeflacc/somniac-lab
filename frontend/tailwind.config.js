/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg: {
          primary:   '#E2DFDA',
          secondary: '#D2C49E',
          panel:     '#CBDED3',
          card:      '#CBDED3',
        },
        accent: {
          DEFAULT: '#3B6255',
          2:       '#8BA49A',
        },
      },
    },
  },
  plugins: [],
}
