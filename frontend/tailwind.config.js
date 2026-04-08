/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2a35",
        mist: "#e8eff2",
        brand: "#0f766e",
        accent: "#ea580c",
        panel: "#f8fafb",
        edge: "#d0dde3"
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"]
      },
      boxShadow: {
        lift: "0 10px 30px rgba(15, 118, 110, 0.12)"
      }
    }
  },
  plugins: []
};
