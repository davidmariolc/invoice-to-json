# Invoice to JSON API

FastAPI backend for the frontend in `../web`. Application endpoints return JSON; the frontend handles the user interface.

## Project Structure

The API groups business functionality under `app/features/`, with invoice functionality in `app/features/invoices/`, and keeps the shared Gemini provider and configuration separate:

```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── features/
│   ├── __init__.py
│   └── invoices/
│       ├── __init__.py
│       ├── router.py    # Invoice HTTP endpoint and error translation
│       ├── schemas.py   # Pydantic invoice models
│       ├── service.py   # Extraction coordination and result validation
│       ├── images.py    # Image stream reading and validation
│       └── prompts.py   # Extraction instructions
├── ai/
│   ├── __init__.py
│   └── providers/
│       ├── __init__.py
│       └── gemini.py    # Gemini client and provider errors
└── core/
    ├── __init__.py
    └── config.py        # Application settings
```

`app/main.py` registers the invoice router directly with the `/api/v1` prefix. Invoice processing, image validation, and the Gemini provider do not depend on FastAPI or HTTP types. The HTTP router translates their exceptions into the existing status codes and messages. The shared Gemini client lives in `app/ai/providers/gemini.py`; shared settings remain in `app/core/`.

## Getting Started

Install the required dependencies using [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Copy the environment example and set your Gemini API key in `.env`:

```bash
cp .env.example .env
```

Set `GEMINI_API_KEY` to your key. Settings automatically load this file, and the backend can start while the key is empty. The local `.env` file is ignored by Git.

## Running Locally

```bash
uv run uvicorn app.main:app --reload --port 5001
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/invoices/process` | Extract invoice data from an image |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

There is no application page at `/`. Open the frontend separately from `../web`.

## Processing invoices

Submit a JPEG, PNG or WEBP image, up to 10 MB, as multipart form data:

```bash
curl -X POST http://localhost:5001/api/v1/invoices/process \
  -F 'file=@/path/to/invoice.png'
```

The response contains `model`, `filename`, and `data`. All invoice properties use English snake_case: `invoice_number`, `issue_date`, `currency`, `issuer`, `recipient`, `items`, `subtotal`, `taxes`, and `total`. Parties contain `name`, `tax_id`, and `address`; items contain `description`, `quantity`, `unit_price`, and `amount`. Missing or unreadable fields are `null`. Text values retain the document's original language.

The backend verifies the image's actual format, sends it to `gemini-3.5-flash-lite` through the OpenAI-compatible API, requests a JSON Schema response, and validates the result with Pydantic. Unreadable or unrelated documents return HTTP 422; invalid model responses return HTTP 502. Uploaded files are closed after reading and are not stored permanently.

The frontend in `../web` sends files to this endpoint through Vite's `/api` development proxy, which targets `http://127.0.0.1:5001`. Keep both development servers running. `GEMINI_API_KEY` is read only by the backend.

## Testing

Run the backend tests without making external API calls:

```bash
uv run python -m unittest discover -s tests -v
```

The invoice endpoint and Gemini provider tests replace the provider client with an in-memory mock transport and block unexpected provider calls. Service and image tests also run locally, without a real API key or paid model requests.

## Deploying to Vercel

Deploy your project to Vercel with the following command:

```bash
npm install -g vercel
vercel --prod
```

Or `git push` to your repository with our [git integration](https://vercel.com/docs/deployments/git).
