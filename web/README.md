# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and Ultracite's Oxlint and Oxfmt presets.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.

Note: This will impact Vite dev & build performances. You can also try [the experimental native React Compiler support in plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react/README.md#rust-react-compiler) by using `compiler: true` in the plugin options instead of using the Babel plugin.

## Linting and formatting

Use pnpm and Node.js `^22.22.2 || >=24.15.0`, as required by Ultracite 8.

```sh
pnpm check
pnpm fix
pnpm exec ultracite doctor
```

`pnpm lint` also runs the lint and formatting checks. `oxlint.config.ts` extends `ultracite/oxlint/core` and `ultracite/oxlint/react`, preserving the existing Fast Refresh export rule after the presets. The rules of hooks are included in the React preset. `oxfmt.config.ts` extends `ultracite/oxfmt`.

Type-aware linting and optional JavaScript plugins are not enabled. Codex instructions live in `AGENTS.md`, automatic formatting hooks in `.codex/hooks.json`, and the reusable Ultracite skill in `.agents/skills/ultracite`.
