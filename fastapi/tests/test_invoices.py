import base64
import json
import unittest
from io import BytesIO
from unittest.mock import patch

import httpx
from google.genai import Client
from PIL import Image
from pydantic import SecretStr

from app.features.invoices.images import MAX_IMAGE_BYTES
from app.features.invoices.prompts import EXTRACTION_PROMPT
from app.core.config import settings
from app.main import app
from app.ai.providers.gemini import (
    MODEL,
    GeminiConfigurationError,
    GeminiError,
    GeminiTimeoutError,
)

INVOICE_DATA = {
    "invoice_number": "F001-000123",
    "issue_date": "2026-10-28",
    "currency": "PEN",
    "issuer": {"name": "Comercial Ejemplo", "tax_id": "20123456789", "address": None},
    "recipient": {"name": "Cliente Demo", "tax_id": None, "address": None},
    "items": [{"description": "Servicio", "quantity": 2, "unit_price": 50, "amount": 100}],
    "subtotal": 100,
    "taxes": 18,
    "total": 118,
}


class InvoiceRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.enterContext(patch(
            "app.ai.providers.gemini.genai.Client",
            side_effect=AssertionError("Unexpected provider call: use a mock transport."),
        ))
        image = BytesIO()
        Image.new("RGB", (80, 80), "white").save(image, format="PNG")
        self.image = image.getvalue()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def request_with_provider(self, content, verify_request=None):
        def handler(request):
            if verify_request:
                verify_request(request)
            return httpx.Response(200, json={
                "modelVersion": MODEL,
                "candidates": [{
                    "content": {"role": "model", "parts": [{"text": content}]},
                    "finishReason": "STOP",
                }],
            })

        def create_client(**kwargs):
            kwargs["http_options"] = kwargs["http_options"].model_copy(update={
                "client_args": {"transport": httpx.MockTransport(handler)},
            })
            return Client(**kwargs)

        with (
            patch.object(settings, "GEMINI_API_KEY", SecretStr("test-key")),
            patch("app.ai.providers.gemini.genai.Client", side_effect=create_client),
        ):
            return await self.client.post(
                "/api/v1/invoices/process",
                files={"file": ("factura.png", self.image, "image/png")},
            )

    async def test_sends_image_and_schema_and_returns_validated_invoice(self):
        def verify(request):
            payload = json.loads(request.content)
            self.assertEqual(request.method, "POST")
            self.assertEqual(
                str(request.url),
                f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            )
            self.assertEqual(request.headers["x-goog-api-key"], "test-key")
            self.assertEqual(payload["systemInstruction"]["parts"][0]["text"], EXTRACTION_PROMPT)
            self.assertEqual(payload["contents"][0]["role"], "user")
            self.assertEqual(payload["contents"][0]["parts"][0]["text"], "Lee esta factura y extrae sus datos.")
            image = payload["contents"][0]["parts"][1]["inlineData"]
            self.assertEqual(image["mime_type"], "image/png")
            self.assertEqual(base64.urlsafe_b64decode(image["data"]), self.image)
            config = payload["generationConfig"]
            self.assertEqual(config["responseMimeType"], "application/json")
            schema = config["responseJsonSchema"]
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(schema["properties"]), {"is_invoice", "invoice"})
            definitions = schema["$defs"]
            self.assertEqual(set(definitions["InvoiceData"]["properties"]), set(INVOICE_DATA))
            self.assertEqual(set(definitions["InvoiceParty"]["properties"]), {"name", "tax_id", "address"})
            self.assertEqual(set(definitions["InvoiceItem"]["properties"]), {"description", "quantity", "unit_price", "amount"})

        response = await self.request_with_provider(
            json.dumps({"is_invoice": True, "invoice": INVOICE_DATA}), verify
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"model": MODEL, "filename": "factura.png", "data": INVOICE_DATA})

    async def test_rejects_invalid_uploads_without_calling_provider(self):
        cases = [
            ("archivo.txt", b"text", "text/plain", 415),
            ("vacio.png", b"", "image/png", 400),
            ("corrupto.png", b"not an image", "image/png", 400),
            ("formato.jpg", self.image, "image/jpeg", 415),
            ("grande.png", b"x" * (MAX_IMAGE_BYTES + 1), "image/png", 413),
        ]
        for name, contents, mime_type, expected_status in cases:
            with self.subTest(name=name), patch("app.ai.providers.gemini.genai.Client") as client:
                response = await self.client.post(
                    "/api/v1/invoices/process", files={"file": (name, contents, mime_type)}
                )
                self.assertEqual(response.status_code, expected_status)
                client.assert_not_called()

    async def test_missing_file_returns_422(self):
        with patch("app.ai.providers.gemini.genai.Client") as client:
            response = await self.client.post("/api/v1/invoices/process")
        self.assertEqual(response.status_code, 422)
        client.assert_not_called()

    async def test_missing_key_returns_503(self):
        with patch.object(settings, "GEMINI_API_KEY", None):
            response = await self.client.post(
                "/api/v1/invoices/process", files={"file": ("factura.png", self.image, "image/png")}
            )
        self.assertEqual(response.status_code, 503)

    async def test_provider_errors_are_translated_to_http(self):
        cases = [
            (GeminiConfigurationError("Missing key"), 503),
            (GeminiTimeoutError("Request timed out"), 504),
            (GeminiError("Provider unavailable"), 502),
        ]
        for error, expected_status in cases:
            with self.subTest(error=error), patch(
                "app.features.invoices.service.generate_text", side_effect=error,
            ):
                response = await self.client.post(
                    "/api/v1/invoices/process",
                    files={"file": ("factura.png", self.image, "image/png")},
                )
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(response.json(), {"detail": str(error)})

    async def test_non_invoice_returns_422(self):
        response = await self.request_with_provider(json.dumps({"is_invoice": False, "invoice": INVOICE_DATA}))
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("data", response.json())

    async def test_malformed_or_incomplete_model_output_returns_502(self):
        invalid_outputs = [
            "not JSON", "{}",
            json.dumps({"is_invoice": True, "invoice": {**INVOICE_DATA, "issue_date": "invalid date"}}),
            json.dumps({"is_invoice": True, "invoice": {**INVOICE_DATA, "total": "unknown"}}),
        ]
        for content in invalid_outputs:
            with self.subTest(content=content):
                response = await self.request_with_provider(content)
                self.assertEqual(response.status_code, 502)

    async def test_unknown_fields_stay_null(self):
        empty_party = {"name": None, "tax_id": None, "address": None}
        data = {
            "invoice_number": None, "issue_date": None, "currency": None,
            "issuer": empty_party, "recipient": empty_party, "items": [],
            "subtotal": None, "taxes": None, "total": None,
        }
        response = await self.request_with_provider(json.dumps({"is_invoice": True, "invoice": data}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], data)


if __name__ == "__main__":
    unittest.main()
