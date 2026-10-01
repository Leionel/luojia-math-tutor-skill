import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  {
    rules: {
      // Existing pages intentionally hydrate client state from local storage/API.
      // Keep the pre-Next-16 lint behavior for these effects during migration.
      "react-hooks/set-state-in-effect": "off",
      // ESLint 9's refs rule flags existing imperative canvas/history refs.
      "react-hooks/refs": "off",
    },
  },
  globalIgnores([
    ".next/**",
    "node_modules/**",
    "next-env.d.ts",
  ]),
]);
