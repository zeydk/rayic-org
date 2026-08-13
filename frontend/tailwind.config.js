/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        linen: '#FAF8F5',
        sand: '#F4F1EA',
        ink: '#111827',
        terracotta: '#C2410C',
        forest: '#047857',
        ochre: '#B45309',
      },
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
