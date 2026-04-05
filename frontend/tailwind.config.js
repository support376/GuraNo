/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        truth: '#22c55e',
        suspect: '#eab308',
        lie: '#ef4444',
      },
    },
  },
  plugins: [],
}
