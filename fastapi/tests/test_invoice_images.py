import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image

from app.features.invoices.images import (
    IMAGE_FORMATS,
    MAX_IMAGE_BYTES,
    ImageTooLargeError,
    InvalidImageError,
    UnsupportedImageError,
    read_invoice_image,
)


class InvoiceImageTests(unittest.TestCase):
    def test_supported_formats_are_read_and_streams_are_closed(self):
        for mime_type, image_format in IMAGE_FORMATS.items():
            with self.subTest(mime_type=mime_type):
                stream = BytesIO()
                Image.new("RGB", (80, 80), "white").save(stream, format=image_format)
                contents = stream.getvalue()
                stream.seek(0)
                self.assertEqual(read_invoice_image(stream, mime_type), (contents, mime_type))
                self.assertTrue(stream.closed)

    def test_invalid_images_raise_domain_errors_and_close_streams(self):
        image = BytesIO()
        Image.new("RGB", (80, 80), "white").save(image, format="PNG")
        cases = [
            (b"text", "text/plain", UnsupportedImageError),
            (b"", "image/png", InvalidImageError),
            (b"corrupt", "image/png", InvalidImageError),
            (image.getvalue(), "image/jpeg", UnsupportedImageError),
            (b"x" * (MAX_IMAGE_BYTES + 1), "image/png", ImageTooLargeError),
        ]
        for contents, mime_type, error in cases:
            with self.subTest(mime_type=mime_type, error=error):
                stream = BytesIO(contents)
                with self.assertRaises(error):
                    read_invoice_image(stream, mime_type)
                self.assertTrue(stream.closed)

    def test_unsafe_resolution_is_rejected(self):
        image = BytesIO()
        Image.new("RGB", (80, 80), "white").save(image, format="PNG")
        # Exercise Pillow's actual warning and error paths with a small image.
        for limit in (4000, 1000):
            with self.subTest(limit=limit), patch.object(Image, "MAX_IMAGE_PIXELS", limit):
                stream = BytesIO(image.getvalue())
                with self.assertRaisesRegex(InvalidImageError, "resolución"):
                    read_invoice_image(stream, "image/png")
                self.assertTrue(stream.closed)
