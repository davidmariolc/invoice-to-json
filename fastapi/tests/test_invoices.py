import base64
import json
import unittest
from io import BytesIO
from unittest.mock import patch

import httpx2
from openai import OpenAI
from PIL import Image
from pydantic import SecretStr

from app.features.invoices.images import MAX_IMAGE_BYTES
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
            "app.ai.providers.gemini.OpenAI",
            side_effect=AssertionError("Unexpected provider call: use a mock transport."),
        ))
        image = BytesIO()
        Image.new("RGB", (80, 80), "white").save(image, format="PNG")
        self.image = image.getvalue()
        self.client = httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app), base_url="http://testserver"
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def request_with_provider(self, content, verify_request=None):
        def handler(request):
            if verify_request:
                verify_request(request)
            return httpx2.Response(200, json={
                "id": "invoice-test", "object": "chat.completion", "created": 0,
                "model": MODEL,
                "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
            })

        def create_client(**kwargs):
            return OpenAI(**kwargs, http_client=httpx2.Client(transport=httpx2.MockTransport(handler)))

        with (
            patch.object(settings, "GEMINI_API_KEY", SecretStr("test-key")),
            patch("app.ai.providers.gemini.OpenAI", side_effect=create_client),
        ):
            return await self.client.post(
                "/api/v1/invoices/process",
                files={"file": ("factura.png", self.image, "image/png")},
            )

    async def test_sends_image_and_schema_and_returns_validated_invoice(self):
        def verify(request):
            payload = json.loads(request.content)
            self.assertEqual(payload["model"], "gemini-3.5-flash-lite")
            self.assertEqual(request.headers["authorization"], "Bearer test-key")
            self.assertEqual(payload["messages"][0]["role"], "system")
            image_url = payload["messages"][1]["content"][1]["image_url"]["url"]
            prefix, encoded = image_url.split(",", 1)
            self.assertEqual(prefix, "data:image/png;base64")
            self.assertEqual(base64.b64decode(encoded), self.image)
            schema = payload["response_format"]["json_schema"]
            self.assertTrue(schema["strict"])
            self.assertFalse(schema["schema"]["additionalProperties"])
            self.assertEqual(set(schema["schema"]["properties"]), {"is_invoice", "invoice"})
            definitions = schema["schema"]["$defs"]
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
            with self.subTest(name=name), patch("app.ai.providers.gemini.OpenAI") as client:
                response = await self.client.post(
                    "/api/v1/invoices/process", files={"file": (name, contents, mime_type)}
                )
                self.assertEqual(response.status_code, expected_status)
                client.assert_not_called()

    async def test_missing_file_returns_422(self):
        with patch("app.ai.providers.gemini.OpenAI") as client:
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
