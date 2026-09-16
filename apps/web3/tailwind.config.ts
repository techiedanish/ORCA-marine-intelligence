import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        abyss: {
          950: "#050C14",
          900: "#0A1622",
          800: "#0F2131",
          700: "#16324A",
          600: "#1E4763",
        },
        chart: {
          paper: "#EFEAE0",
          line: "#C9BFA8",
        },
        depth: {
          teal: "#4FD1C5",
          cyan: "#7DD3E8",
        },
        mist: {
          400: "#8FA6B8",
          300: "#B7C7D3",
        },
        verdict: {
          green: "#3FBF7F",
          amber: "#E8A93B",
          red: "#E24C4C",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.04) inset, 0 8px 24px rgba(0,0,0,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;
