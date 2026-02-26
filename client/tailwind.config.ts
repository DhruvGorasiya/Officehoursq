import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0A0E17",
        surface: "#111827",
        card: "#161F31",
        accent: "#6366F1",
        green: "#10B981",
        amber: "#F59E0B",
        red: "#EF4444",
        cyan: "#06B6D4",
        purple: "#A855F7",
      },
      fontFamily: {
        sans: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "14px",
        input: "10px",
        button: "10px",
        badge: "20px",
      },
    },
  },
  plugins: [],
};

export default config;
