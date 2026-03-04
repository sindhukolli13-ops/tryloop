import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // Tryloop brand tokens will be defined here (colors, fonts, spacing)
    },
  },
  plugins: [],
};

export default config;
