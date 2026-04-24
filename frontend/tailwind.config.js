/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Sora', 'Neo Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        bg: {
          primary:   '#FFFFFF',
          secondary: '#F9FAFB',
          panel:     '#F3F4F6',
          card:      '#FFFFFF',
        },
        accent: {
          DEFAULT: '#3B6255',
          2:       '#F97316',
        },
      },
    },
  },
  plugins: [],
}
