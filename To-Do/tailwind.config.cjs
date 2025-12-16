/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './**/*.{ts,tsx,js,jsx}'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
