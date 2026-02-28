/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#eef8ff',
          100: '#d7ecff',
          500: '#0f6db5',
          700: '#0a4f85',
        },
      },
    },
  },
  plugins: [],
}
