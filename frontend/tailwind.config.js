/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ["Cinzel", "Georgia", "serif"],
        mono: ["JetBrains Mono", "monospace"],
        sans: ["Plus Jakarta Sans", "Inter", "sans-serif"],
      },
      colors: {
        slate: {
          950: "#070b14",
        },
      },
    },
  },
  plugins: [],
}
