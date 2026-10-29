import json
import unittest
from unittest.mock import patch

import httpx2
from openai import OpenAI
from pydantic import SecretStr

from app.ai.providers.gemini import (
    MODEL,
    GeminiConfigurationError,
    GeminiError,
    GeminiTimeoutError,
    generate_text,
)
from app.core.config import settings

MESSAGES = [{"role": "user", "content": "Explain closures in one paragraph."}]


def completion_body(content="A closure retains access to its enclosing scope.", choices=None):
    return {
        "id": "test-completion",
        "object": "chat.completion",
        "created": 0,
        "model": MODEL,
        "choices": choices if choices is not None else [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
    }


class GeminiProviderTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch(
            "app.ai.providers.gemini.OpenAI",
            side_effect=AssertionError("Unexpected provider call: use a mock transport."),
        ))

    def request_with_provider(self, handler):
        def create_client(**kwargs):
            return OpenAI(
                **kwargs,
                http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
            )

        with (
            patch.object(settings, "GEMINI_API_KEY", SecretStr("test-key")),
            patch("app.ai.providers.gemini.OpenAI", side_effect=create_client),
        ):
            return generate_text(MESSAGES)

    def test_sends_expected_request_and_returns_generated_text(self):
        def handler(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(
                str(request.url),
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
            )
            self.assertEqual(request.headers["authorization"], "Bearer test-key")
            self.assertEqual(
                json.loads(request.content),
                {
                    "model": "gemini-3.5-flash-lite",
                    "messages": [
                        {"role": "user", "content": "Explain closures in one paragraph."}
                    ],
                },
            )
            return httpx2.Response(200, json=completion_body())

        response = self.request_with_provider(handler)
        self.assertEqual(response, (
            MODEL, "A closure retains access to its enclosing scope.",
        ))

    def test_missing_key_raises_configuration_error_without_calling_provider(self):
        with (
            patch.object(settings, "GEMINI_API_KEY", None),
            patch("app.ai.providers.gemini.OpenAI") as client,
        ):
            with self.assertRaises(GeminiConfigurationError):
                generate_text(MESSAGES)
        client.assert_not_called()

    def test_timeout_raises_timeout_error(self):
        def handler(request):
            raise httpx2.ReadTimeout("Test timeout", request=request)

        with self.assertRaises(GeminiTimeoutError):
            self.request_with_provider(handler)

    def test_connection_failure_raises_provider_error(self):
        def handler(request):
            raise httpx2.ConnectError("Test connection error", request=request)

        with self.assertRaises(GeminiError):
            self.request_with_provider(handler)

    def test_provider_errors_do_not_expose_raw_details(self):
        for provider_status in (401, 404, 429, 500):
            with self.subTest(provider_status=provider_status):
                def handler(request):
                    return httpx2.Response(provider_status, json={
                        "error": {"message": "private provider details", "code": provider_status}
                    })

                with self.assertRaises(GeminiError) as caught:
                    self.request_with_provider(handler)
                message = str(caught.exception)
                self.assertIn(str(provider_status), message)
                self.assertNotIn("private provider details", message)
                self.assertNotIn("test-key", message)

    def test_empty_responses_raise_provider_error(self):
        for body in (
            completion_body(choices=[]),
            completion_body(content=None),
            completion_body(content=""),
            completion_body(content="   "),
        ):
            with self.subTest(body=body):
                with self.assertRaises(GeminiError):
                    self.request_with_provider(
                        lambda request: httpx2.Response(200, json=body)
                    )

    def test_truncated_response_raises_provider_error(self):
        body = completion_body()
        body["choices"][0]["finish_reason"] = "length"
        with self.assertRaisesRegex(GeminiError, "respuesta incompleta"):
            self.request_with_provider(
                lambda request: httpx2.Response(200, json=body)
            )


if __name__ == "__main__":
    unittest.main()
