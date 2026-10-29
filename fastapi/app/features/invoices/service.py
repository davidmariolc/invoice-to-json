from pydantic import ValidationError

from app.ai.providers.gemini import generate_text
from app.features.invoices.prompts import EXTRACTION_PROMPT
from app.features.invoices.schemas import InvoiceExtraction, InvoiceProcessResponse


class InvalidExtractionError(ValueError):
    """The model response does not match the invoice schema."""


class UnreadableInvoiceError(ValueError):
    """The image does not contain a readable invoice."""


def extract_invoice(
    contents: bytes,
    mime_type: str,
    filename: str,
) -> InvoiceProcessResponse:
    """Extract and validate invoice data from an already validated image."""
    model, content = generate_text(
        "Lee esta factura y extrae sus datos.",
        system_instruction=EXTRACTION_PROMPT,
        image=contents,
        mime_type=mime_type,
        response_json_schema=InvoiceExtraction.model_json_schema(),
    )
    try:
        extraction = InvoiceExtraction.model_validate_json(content)
    except ValidationError as exc:
        raise InvalidExtractionError("El modelo no devolvió datos con el formato esperado. Intenta de nuevo.") from exc
    if not extraction.is_invoice:
        raise UnreadableInvoiceError("No se reconoce una factura legible en esta imagen. Prueba con una foto más clara.")

    return InvoiceProcessResponse(model=model, filename=filename, data=extraction.invoice)
