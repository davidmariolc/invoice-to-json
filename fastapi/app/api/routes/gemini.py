from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.ai.providers.gemini import (
    GeminiConfigurationError,
    GeminiError,
    GeminiTimeoutError,
    generate_text,
)

router = APIRouter(prefix="/gemini", tags=["gemini"])


class GeminiTestResponse(BaseModel):
    model: str
    content: str


@router.post("/test", response_model=GeminiTestResponse)
def test_gemini() -> GeminiTestResponse:
    """Send a sample prompt to Gemini using the OpenAI-compatible API."""
    try:
        model, content = generate_text([
            {"role": "user", "content": "Explain closures in one paragraph."}
        ])
    except GeminiConfigurationError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except GeminiTimeoutError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except GeminiError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    return GeminiTestResponse(model=model, content=content)
