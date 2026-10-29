from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.shared_params import ResponseFormatJSONSchema

from app.core.config import settings

MODEL = "gemini-3.5-flash-lite"


class GeminiError(Exception):
    """Gemini could not return a complete, non-empty text response."""


class GeminiConfigurationError(GeminiError):
    """The Gemini API key is missing."""


class GeminiTimeoutError(GeminiError):
    """The Gemini request timed out."""


def generate_text(
    messages: list[ChatCompletionMessageParam],
    response_format: ResponseFormatJSONSchema | None = None,
) -> tuple[str, str]:
    if settings.GEMINI_API_KEY is None:
        raise GeminiConfigurationError(
            "Configura GEMINI_API_KEY en el archivo .env de FastAPI.",
        )

    options = {"response_format": response_format} if response_format else {}
    try:
        with OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=settings.GEMINI_API_KEY.get_secret_value(),
            timeout=60.0,
            max_retries=0,
        ) as client:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                **options,
            )
    except APITimeoutError as exc:
        raise GeminiTimeoutError(
            "Gemini no respondió dentro del tiempo de espera. Intenta de nuevo.",
        ) from exc
    except APIConnectionError as exc:
        raise GeminiError(
            "No se pudo conectar con la API de Gemini. Intenta de nuevo.",
        ) from exc
    except APIStatusError as exc:
        raise GeminiError(
            f"Gemini devolvió HTTP {exc.status_code} al consultar {MODEL}.",
        ) from exc

    content = response.choices[0].message.content if response.choices else None
    if not content or not content.strip():
        raise GeminiError(
            "Gemini no devolvió una respuesta de texto.",
        )
    if response.choices[0].finish_reason == "length":
        raise GeminiError(
            "Gemini devolvió una respuesta incompleta. Intenta con una imagen más simple.",
        )
    return response.model, content
