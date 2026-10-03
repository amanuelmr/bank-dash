import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

/**
 * ESLint flat config.
 *
 * Replaces the old `.eslintrc.json`, which ESLint 9 no longer reads.
 * `eslint-config-next` 16 ships native flat configs, so no `FlatCompat`
 * shim is needed.
 */
export default [
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "build/**",
      "next-env.d.ts",
    ],
  },
  ...coreWebVitals,
  ...typescript,
  {
    rules: {
      // Pre-existing debt, kept visible as warnings rather than silenced.
      // Neither is caused by the Next 16 upgrade; both need a dedicated pass.
      //
      // `no-explicit-any`: ~25 hand-written `any`s across components/services.
      // `set-state-in-effect`: a new, opinionated react-hooks v7 rule that
      // flags the fetch-then-setState loading effect this app uses throughout.
      // The alternative (fetching in event handlers or via a store) is a real
      // refactor, not a lint fix.
      "@typescript-eslint/no-explicit-any": "warn",
      "react-hooks/set-state-in-effect": "warn",
    },
  },
];