/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0B0F1A",
          surface: "#141A2B",
          surface2: "#1C2339",
          border: "#2A3350",
        },
        paper: {
          DEFAULT: "#E9EAF0",
          dim: "#8B92AB",
        },
        gold: {
          DEFAULT: "#D4A94E",
          soft: "#E8C878",
        },
        coral: {
          DEFAULT: "#E2604F",
          soft: "#F08C7E",
        },
        teal: {
          DEFAULT: "#4FB8A8",
          soft: "#7FD4C6",
        },
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
