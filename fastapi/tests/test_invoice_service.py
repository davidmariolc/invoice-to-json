import json
import unittest
from unittest.mock import patch

from app.ai.providers.gemini import MODEL
from app.features.invoices.schemas import InvoiceData
from app.features.invoices.service import (
    InvalidExtractionError,
    UnreadableInvoiceError,
    extract_invoice,
)


class InvoiceServiceTests(unittest.TestCase):
    def setUp(self):
        self.data = {
            "invoice_number": "000123", "issue_date": "2026-10-28", "currency": "PEN",
            "issuer": {"name": "Ejemplo", "tax_id": "00123", "address": None},
            "recipient": {"name": None, "tax_id": None, "address": None},
            "items": [], "subtotal": None, "taxes": None, "total": 118,
        }

    def test_extracts_invoice_without_http_objects(self):
        content = json.dumps({"is_invoice": True, "invoice": self.data})
        with patch("app.features.invoices.service.generate_text", return_value=(MODEL, content)):
            result = extract_invoice(b"validated image", "image/png", "factura.png")
        self.assertEqual(result.model, MODEL)
        self.assertEqual(result.filename, "factura.png")
        self.assertEqual(result.data, InvoiceData.model_validate(self.data))

    def test_invalid_model_output_raises_domain_error(self):
        with patch("app.features.invoices.service.generate_text", return_value=(MODEL, "{}")):
            with self.assertRaises(InvalidExtractionError):
                extract_invoice(b"validated image", "image/png", "factura.png")

    def test_unreadable_invoice_raises_domain_error(self):
        content = json.dumps({"is_invoice": False, "invoice": self.data})
        with patch("app.features.invoices.service.generate_text", return_value=(MODEL, content)):
            with self.assertRaises(UnreadableInvoiceError):
                extract_invoice(b"validated image", "image/png", "factura.png")
