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
        edge: "#d0dde3",
        website: "#f4f7f8",
        "website-edge": "#d7e2e8"
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Manrope", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"]
      },
      boxShadow: {
        lift: "0 10px 30px rgba(15, 118, 110, 0.12)",
        "lift-lg": "0 20px 45px rgba(31, 42, 53, 0.16)",
        soft: "0 8px 22px rgba(31, 42, 53, 0.08)"
      }
    }
  },
  plugins: []
};
