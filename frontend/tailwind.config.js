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
          primary:   '#0a0a0f',
          secondary: '#0f0f1a',
          panel:     '#12121f',
          card:      '#1a1a2e',
        },
        accent: {
          DEFAULT: '#7c6aff',
          2:       '#a78bfa',
        },
      },
    },
  },
  plugins: [],
}
