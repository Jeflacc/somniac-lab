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
          primary:   '#121212',
          secondary: '#0a0a0a',
          panel:     '#181818',
          card:      '#1e1e1e',
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
