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
          primary:   '#1a1a2e',
          secondary: '#16162a',
          panel:     '#1e1e3a',
          card:      '#222244',
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
