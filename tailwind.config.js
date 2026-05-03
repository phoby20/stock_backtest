/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        gh: {
          base:    "#0d1117",
          surface: "#161b22",
          border:  "#21262d",
          border2: "#30363d",
          text:    "#c9d1d9",
          muted:   "#8b949e",
          dim:     "#484f58",
          blue:    "#58a6ff",
          green:   "#3fb950",
          red:     "#f85149",
          merge:   "#238636",
          mergeHover: "#2ea043",
        },
      },
    },
  },
  plugins: [],
}
