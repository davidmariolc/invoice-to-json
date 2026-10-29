import json
import unittest
from unittest.mock import patch

import httpx
from google.genai import Client
from pydantic import SecretStr

from app.ai.providers.gemini import (
    MODEL,
    GeminiConfigurationError,
    GeminiError,
    GeminiTimeoutError,
    generate_text,
)
from app.core.config import settings

PROMPT = "Explain closures in one paragraph."


def completion_body(content="A closure retains access to its enclosing scope.", candidates=None):
    return {
        "modelVersion": MODEL,
        "candidates": candidates if candidates is not None else [{
            "content": {"role": "model", "parts": [{"text": content}]},
            "finishReason": "STOP",
        }],
    }


class GeminiProviderTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch(
            "app.ai.providers.gemini.genai.Client",
            side_effect=AssertionError("Unexpected provider call: use a mock transport."),
        ))

    def request_with_provider(self, handler):
        def create_client(**kwargs):
            options = kwargs["http_options"]
            self.assertEqual(options.timeout, 60_000)
            self.assertEqual(options.retry_options.attempts, 1)
            kwargs["http_options"] = options.model_copy(update={
                "client_args": {"transport": httpx.MockTransport(handler)},
            })
            return Client(**kwargs)

        with (
            patch.object(settings, "GEMINI_API_KEY", SecretStr("test-key")),
            patch("app.ai.providers.gemini.genai.Client", side_effect=create_client),
        ):
            return generate_text(PROMPT)

    def test_sends_expected_request_and_returns_generated_text(self):
        def handler(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(
                str(request.url),
                f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            )
            self.assertEqual(request.headers["x-goog-api-key"], "test-key")
            self.assertEqual(json.loads(request.content)["contents"], [{
                "role": "user", "parts": [{"text": PROMPT}],
            }])
            self.assertNotIn("responseMimeType", json.loads(request.content).get("generationConfig", {}))
            return httpx.Response(200, json=completion_body())

        self.assertEqual(self.request_with_provider(handler), (
            MODEL, "A closure retains access to its enclosing scope.",
        ))

    def test_missing_key_raises_configuration_error_without_calling_provider(self):
        with (
            patch.object(settings, "GEMINI_API_KEY", None),
            patch("app.ai.providers.gemini.genai.Client") as client,
        ):
            with self.assertRaises(GeminiConfigurationError):
                generate_text(PROMPT)
        client.assert_not_called()

    def test_timeout_raises_timeout_error(self):
        calls = []

        def handler(request):
            calls.append(request)
            raise httpx.ReadTimeout("Test timeout", request=request)

        with self.assertRaises(GeminiTimeoutError):
            self.request_with_provider(handler)
        self.assertEqual(len(calls), 1)

    def test_connection_failure_raises_provider_error(self):
        def handler(request):
            raise httpx.ConnectError("Test connection error", request=request)

        with self.assertRaises(GeminiError):
            self.request_with_provider(handler)

    def test_provider_errors_do_not_expose_raw_details_or_retry(self):
        for provider_status in (401, 404, 429, 500):
            with self.subTest(provider_status=provider_status):
                calls = []

                def handler(request):
                    calls.append(request)
                    return httpx.Response(provider_status, json={
                        "error": {"message": "private provider details", "code": provider_status}
                    })

                with self.assertRaises(GeminiError) as caught:
                    self.request_with_provider(handler)
                message = str(caught.exception)
                self.assertIn(str(provider_status), message)
                self.assertNotIn("private provider details", message)
                self.assertNotIn("test-key", message)
                self.assertEqual(len(calls), 1)

    def test_provider_deadline_raises_timeout_error(self):
        with self.assertRaises(GeminiTimeoutError):
            self.request_with_provider(lambda request: httpx.Response(504, json={
                "error": {"code": 504, "message": "private timeout details", "status": "DEADLINE_EXCEEDED"},
            }))

    def test_empty_responses_raise_provider_error(self):
        for body in (
            completion_body(candidates=[]),
            completion_body(candidates=[{"finishReason": "SAFETY"}]),
            completion_body(content=None),
            completion_body(content=""),
            completion_body(content="   "),
        ):
            with self.subTest(body=body), self.assertRaises(GeminiError):
                self.request_with_provider(lambda request: httpx.Response(200, json=body))

    def test_incomplete_responses_raise_provider_error(self):
        for reason in ("MAX_TOKENS", "SAFETY", None):
            body = completion_body()
            body["candidates"][0]["finishReason"] = reason
            with self.subTest(reason=reason), self.assertRaisesRegex(GeminiError, "respuesta incompleta"):
                self.request_with_provider(lambda request: httpx.Response(200, json=body))

    def test_missing_model_version_uses_requested_model(self):
        body = completion_body()
        del body["modelVersion"]
        model, _ = self.request_with_provider(lambda request: httpx.Response(200, json=body))
        self.assertEqual(model, MODEL)


if __name__ == "__main__":
    unittest.main()
