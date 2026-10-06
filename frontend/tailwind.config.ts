import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";
import tailwindScrollbar from "tailwind-scrollbar";

const config = {
  // "class" was replaced by "selector" in Tailwind 3.4.1; this project is
  // on 3.4.19, so the old name works but is deprecated.
  darkMode: "selector",
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
    "./constants/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Semantic tokens, defined as CSS variables in globals.css so light and
        // dark share one definition and swap by the `.dark` class. The
        // <alpha-value> slot keeps `/50` opacity modifiers working.
        surface: {
          base: "rgb(var(--surface-base) / <alpha-value>)",
          1: "rgb(var(--surface-1) / <alpha-value>)",
          2: "rgb(var(--surface-2) / <alpha-value>)",
          3: "rgb(var(--surface-3) / <alpha-value>)",
        },
        line: {
          DEFAULT: "rgb(var(--line) / <alpha-value>)",
          strong: "rgb(var(--line-strong) / <alpha-value>)",
        },
        content: {
          primary: "rgb(var(--content-primary) / <alpha-value>)",
          secondary: "rgb(var(--content-secondary) / <alpha-value>)",
          muted: "rgb(var(--content-muted) / <alpha-value>)",
          inverse: "rgb(var(--content-inverse) / <alpha-value>)",
        },
        brand: {
          DEFAULT: "rgb(var(--brand) / <alpha-value>)",
          fill: "rgb(var(--brand-fill) / <alpha-value>)",
          on: "rgb(var(--on-brand-fill) / <alpha-value>)",
        },
        accentSecondary: "rgb(var(--accent-secondary) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)",

        // `dark` is a legacy alias for the page surface, kept so the existing
        // `bg-dark` usages resolve into the new scale instead of staying a
        // one-off navy that matches nothing else.
        "dark": "rgb(var(--surface-base) / <alpha-value>)",
        darkComponent: "rgb(var(--surface-3) / <alpha-value>)",
        medium: "rgb(var(--surface-2) / <alpha-value>)",
        fill: {
          1: "rgba(255, 255, 255, 0.10)",
        },
        bankGradient: "#0179FE",
        indigo: {
          // Was #6172F3, which managed only 4.03:1 against white text - the
          // primary button failed WCAG AA. Darkened to clear 4.5:1 (4.53:1)
          // while staying recognisably the same brand hue.
          500: "#546CE3",
          700: "#3D4FBF",
        },
        success: {
          25: "#F6FEF9",
          50: "#ECFDF3",
          100: "#D1FADF",
          600: "#039855",
          700: "#027A48",
          900: "#054F31",
        },
        pink: {
          25: "#FEF6FB",
          100: "#FCE7F6",
          500: "#EE46BC",
          600: "#DD2590",
          700: "#C11574",
          900: "#851651",
        },
        blue: {
          25: "#F5FAFF",
          100: "#D1E9FF",
          500: "#2E90FA",
          600: "#1570EF",
          700: "#175CD3",
          900: "#194185",
        },
        sky: {
          1: "#F3F9FF",
        },
        black: {
          1: "#00214F",
          2: "#344054",
        },
        gray: {
          25: "#FCFCFD",
          200: "#EAECF0",
          300: "#D0D5DD",
          500: "#667085",
          600: "#475467",
          700: "#344054",
          900: "#101828",
        },
      },
      backgroundImage: {
        "bank-gradient": "linear-gradient(90deg, #0179FE 0%, #4893FF 100%)",
        "gradient-mesh": "url('/icons/gradient-mesh.svg')",
        "bank-green-gradient":
          "linear-gradient(90deg, #01797A 0%, #489399 100%)",
      },
      boxShadow: {
        form: "0px 1px 2px 0px rgba(16, 24, 40, 0.05)",
        chart:
          "0px 1px 3px 0px rgba(16, 24, 40, 0.10), 0px 1px 2px 0px rgba(16, 24, 40, 0.06)",
        profile:
          "0px 12px 16px -4px rgba(16, 24, 40, 0.08), 0px 4px 6px -2px rgba(16, 24, 40, 0.03)",
        creditCard: "8px 10px 16px 0px rgba(0, 0, 0, 0.05)",
      },
      fontFamily: {
        inter: "var(--font-inter)",
        "ibm-plex-serif": "var(--font-ibm-plex-serif)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [tailwindcssAnimate, tailwindScrollbar],
} satisfies Config;

export default config;
