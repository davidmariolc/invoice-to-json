import { defineConfig } from "oxlint";
import core from "ultracite/oxlint/core";
import react from "ultracite/oxlint/react";

export default defineConfig({
  env: core.env,
  extends: [core, react],
  // Installed skills include third-party examples and tooling, outside the app.
  ignorePatterns: [...(core.ignorePatterns ?? []), ".agents/skills/**"],
  rules: {
    "react/only-export-components": [
      "warn",
      {
        allowConstantExport: true,
      },
    ],
  },
});
