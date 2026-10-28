import { defineConfig } from "oxfmt";
import ultracite from "ultracite/oxfmt";

export default defineConfig({
  ...ultracite,
  // Keep installed third-party skills consistent with their upstream sources.
  ignorePatterns: [...(ultracite.ignorePatterns ?? []), ".agents/skills/**"],
});
