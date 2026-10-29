from typing import Any

import httpx
from google import genai
from google.genai import errors, types

from app.core.config import settings

MODEL = "gemini-3.5-flash-lite"


class GeminiError(Exception):
    """Gemini could not return a complete, non-empty text response."""


class GeminiConfigurationError(GeminiError):
    """The Gemini API key is missing."""


class GeminiTimeoutError(GeminiError):
    """The Gemini request timed out."""


def generate_text(
    prompt: str,
    *,
    system_instruction: str | None = None,
    image: bytes | None = None,
    mime_type: str | None = None,
    response_json_schema: dict[str, Any] | None = None,
) -> tuple[str, str]:
    if settings.GEMINI_API_KEY is None:
        raise GeminiConfigurationError(
            "Configura GEMINI_API_KEY en el archivo .env de FastAPI.",
        )

    parts = [types.Part.from_text(text=prompt)]
    if image is not None:
        if not mime_type:
            raise ValueError("An image MIME type is required.")
        parts.append(types.Part.from_bytes(data=image, mime_type=mime_type))

    try:
        with genai.Client(
            api_key=settings.GEMINI_API_KEY.get_secret_value(),
            http_options=types.HttpOptions(
                timeout=60_000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        ) as client:
            response = client.models.generate_content(
                model=MODEL,
                contents=types.Content(role="user", parts=parts),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json" if response_json_schema else None,
                    response_json_schema=response_json_schema,
                ),
            )
    except httpx.TimeoutException as exc:
        raise GeminiTimeoutError(
            "Gemini no respondió dentro del tiempo de espera. Intenta de nuevo.",
        ) from exc
    except httpx.RequestError as exc:
        raise GeminiError(
            "No se pudo conectar con la API de Gemini. Intenta de nuevo.",
        ) from exc
    except errors.APIError as exc:
        if exc.code == 504:
            raise GeminiTimeoutError(
                "Gemini no respondió dentro del tiempo de espera. Intenta de nuevo.",
            ) from exc
        raise GeminiError(
            f"Gemini devolvió HTTP {exc.code} al consultar {MODEL}.",
        ) from exc

    content = response.text
    if not content or not content.strip():
        raise GeminiError(
            "Gemini no devolvió una respuesta de texto.",
        )
    if not response.candidates or response.candidates[0].finish_reason != types.FinishReason.STOP:
        raise GeminiError(
            "Gemini devolvió una respuesta incompleta. Intenta con una imagen más simple.",
        )
    return response.model_version or MODEL, content
