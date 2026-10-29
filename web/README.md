# Invoice to JSON Web

React frontend for uploading invoice images and viewing the extracted data as JSON. Uses Vite, Tailwind CSS, shadcn/ui, React Hook Form, Zod, and Ultracite.

## Project structure

```text
src/
├── app.tsx                          # Page composition and processing state
├── features/
│   └── invoices/
│       ├── components/
│       │   ├── invoice-upload-form.tsx
│       │   └── invoice-output.tsx
│       ├── api.ts                   # Multipart API request and response validation
│       └── schemas.ts               # Invoice validation schemas and types
├── components/
│   └── ui/                          # Shared shadcn/ui components
└── lib/
    └── utils.ts                     # General utilities
```

Import invoice modules directly from `@/features/invoices/`. Shared UI components and general utilities stay in `@/components/ui/` and `@/lib/`.

## Running locally

Start FastAPI in a separate terminal, with `GEMINI_API_KEY` set in `../fastapi/.env`:

```bash
cd ../fastapi
uv sync
uv run uvicorn app.main:app --reload --port 5001
```

From this `web` directory, start the frontend:

```bash
pnpm install
pnpm dev
```

Select a JPG, PNG, or WEBP image up to 4 MB and click **Subir factura**. The frontend posts multipart form data to `/api/v1/invoices/process`; Vite proxies `/api` requests to `http://127.0.0.1:5001` during development. The repository-root `vercel.json` routes production `/api` requests to the FastAPI service and other paths to the Vite service. Deploy from the repository root; see `../README.md`.

The result panel displays the validated invoice JSON with English properties such as `invoice_number`, `issue_date`, `issuer`, `recipient`, and `items`, including nullable unreadable fields. Changing or removing an image clears previous results. Upload controls are disabled while processing, and failures leave the image available for another attempt. No API key is exposed to the frontend.

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

Run `pnpm check` for linting and formatting, and `pnpm build` for TypeScript checks and the production build. These commands do not call the backend or the model.

`pnpm lint` also runs the lint and formatting checks. `oxlint.config.ts` extends `ultracite/oxlint/core` and `ultracite/oxlint/react`, preserving the existing Fast Refresh export rule after the presets. The rules of hooks are included in the React preset. `oxfmt.config.ts` extends `ultracite/oxfmt`.

Type-aware linting and optional JavaScript plugins are not enabled. Codex instructions live in `AGENTS.md`, automatic formatting hooks in `.codex/hooks.json`, and the reusable Ultracite skill in `.agents/skills/ultracite`.
