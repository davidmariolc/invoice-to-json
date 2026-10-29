from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.ai.providers.gemini import (
    GeminiConfigurationError,
    GeminiError,
    GeminiTimeoutError,
)
from app.invoices.images import (
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedImageError,
    read_invoice_image,
)
from app.invoices.schemas import InvoiceProcessResponse
from app.invoices.service import (
    InvalidExtractionError,
    UnreadableInvoiceError,
    extract_invoice,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/process", response_model=InvoiceProcessResponse)
def process_invoice(
    file: Annotated[UploadFile, File(description="Imagen JPG, PNG o WEBP de hasta 10 MB.")],
) -> InvoiceProcessResponse:
    try:
        contents, mime_type = read_invoice_image(file.file, file.content_type or "")
        return extract_invoice(contents, mime_type, file.filename or "factura")
    except UnsupportedImageError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except ImageTooLargeError as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, str(exc)) from exc
    except InvalidImageError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except UnreadableInvoiceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    except GeminiConfigurationError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except GeminiTimeoutError as exc:
        raise HTTPException(status.HTTP_504_GATEWAY_TIMEOUT, str(exc)) from exc
    except (GeminiError, InvalidExtractionError) as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
