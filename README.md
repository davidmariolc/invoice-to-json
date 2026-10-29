# Invoice to JSON

Upload an invoice image and extract validated JSON using React, FastAPI, and Google's native `google-genai` SDK.

## Local development

Start the backend from `fastapi/`:

```sh
uv sync --locked
# Set GEMINI_API_KEY in fastapi/.env; see fastapi/.env.example.
uv run uvicorn app.main:app --reload --port 5001
```

Start the frontend from `web/` in another terminal:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

Open http://localhost:5173. Vite forwards `/api` requests to FastAPI on port 5001.

## Vercel deployment

The root `vercel.json` uses [Vercel Services](https://vercel.com/docs/services), currently in beta, to build and deploy both applications in one project:

| Service | Root | Framework | Entry point/output |
| --- | --- | --- | --- |
| Backend | `fastapi/` | FastAPI | `app.main:app`, Python 3.12 |
| Frontend | `web/` | Vite | `pnpm build` → `dist/` |

Import this repository into Vercel, keep Root Directory at the repository root, select Other as the project framework, and use Node.js 24.x. The service definitions provide their own frameworks and build commands. Set `GEMINI_API_KEY` as a Secret in Preview and Production. Do not use a `VITE_` prefix for the key.

Alternatively, use Vercel CLI from the repository root:

```sh
vercel link
vercel
# After verifying the preview:
vercel --prod
```

Public routing sends `/api/*`, `/docs`, `/redoc`, and `/openapi.json` to FastAPI. Other paths go to the frontend, with an SPA fallback for deep links. The frontend uses relative API URLs, so every deployment calls its own backend without additional CORS configuration.

Images must be JPEG, PNG, or WEBP, up to 4 MB. This leaves multipart overhead below [Vercel Functions' 4.5 MB request limit](https://vercel.com/docs/functions/limitations). The function timeout is 90 seconds and the Gemini request timeout is 60 seconds. Uploaded images are not stored permanently.

`.vercelignore` excludes local secrets, dependencies, generated files, and agent configuration from CLI uploads. Keep `.env` and `.vercel/` out of Git.

## Validation

```sh
cd fastapi
uv run --locked python -m unittest discover -s tests -v
cd ../web
pnpm check
pnpm build
```

The automated backend tests use mock Gemini responses and make no paid API calls. See [FastAPI deployment documentation](https://vercel.com/docs/frameworks/backend/fastapi) and [Python backends with Services](https://vercel.com/kb/guide/python-backend-on-vercel).
