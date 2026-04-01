/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "beige-50": "#faf8f5",
        "beige-100": "#f3efe8",
        "beige-200": "#e8e0d4",
        "beige-300": "#d4c8b8",
        "warm-50": "#fdfcfa",
        "warm-100": "#f9f7f4",
        "warm-200": "#f0ece5",
        sidebar: "#1c1917",
        "sidebar-hover": "#292524",
        "sidebar-text": "#e7e5e4",
        "sidebar-muted": "#a8a29e",
        accent: "#b45309",
        "accent-light": "#fef3c7",
        ink: "#1c1917",
        muted: "#78716c",
      },
      fontFamily: {
        sans: ['"Noto Sans KR"', '"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ['"Noto Serif KR"', '"Georgia"', "ui-serif", "serif"],
      },
    },
  },
  plugins: [],
};
