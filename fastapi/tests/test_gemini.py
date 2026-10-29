import json
import unittest
from unittest.mock import patch

import httpx2
from openai import OpenAI
from pydantic import SecretStr

from app.ai.providers.gemini import MODEL
from app.core.config import settings
from app.main import app


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


class GeminiRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.enterContext(patch(
            "app.ai.providers.gemini.OpenAI",
            side_effect=AssertionError("Unexpected provider call: use a mock transport."),
        ))
        self.client = httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self):
        await self.client.aclose()

    async def request_with_provider(self, handler):
        def create_client(**kwargs):
            return OpenAI(
                **kwargs,
                http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
            )

        with (
            patch.object(settings, "GEMINI_API_KEY", SecretStr("test-key")),
            patch("app.ai.providers.gemini.OpenAI", side_effect=create_client),
        ):
            return await self.client.post("/api/v1/gemini/test")

    async def test_sends_expected_request_and_returns_generated_text(self):
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

        response = await self.request_with_provider(handler)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "model": MODEL,
            "content": "A closure retains access to its enclosing scope.",
        })

    async def test_missing_key_returns_503_without_calling_provider(self):
        with (
            patch.object(settings, "GEMINI_API_KEY", None),
            patch("app.ai.providers.gemini.OpenAI") as client,
        ):
            response = await self.client.post("/api/v1/gemini/test")
        self.assertEqual(response.status_code, 503)
        client.assert_not_called()

    async def test_timeout_returns_504(self):
        def handler(request):
            raise httpx2.ReadTimeout("Test timeout", request=request)

        response = await self.request_with_provider(handler)
        self.assertEqual(response.status_code, 504)

    async def test_connection_failure_returns_502(self):
        def handler(request):
            raise httpx2.ConnectError("Test connection error", request=request)

        response = await self.request_with_provider(handler)
        self.assertEqual(response.status_code, 502)

    async def test_provider_errors_do_not_expose_raw_details(self):
        for provider_status in (401, 404, 429, 500):
            with self.subTest(provider_status=provider_status):
                def handler(request):
                    return httpx2.Response(provider_status, json={
                        "error": {"message": "private provider details", "code": provider_status}
                    })

                response = await self.request_with_provider(handler)
                self.assertEqual(response.status_code, 502)
                self.assertIn(str(provider_status), response.json()["detail"])
                self.assertNotIn("private provider details", response.text)
                self.assertNotIn("test-key", response.text)

    async def test_empty_responses_return_502(self):
        for body in (
            completion_body(choices=[]),
            completion_body(content=None),
            completion_body(content=""),
            completion_body(content="   "),
        ):
            with self.subTest(body=body):
                response = await self.request_with_provider(
                    lambda request: httpx2.Response(200, json=body)
                )
                self.assertEqual(response.status_code, 502)

    async def test_truncated_response_returns_502(self):
        body = completion_body()
        body["choices"][0]["finish_reason"] = "length"
        response = await self.request_with_provider(
            lambda request: httpx2.Response(200, json=body)
        )
        self.assertEqual(response.status_code, 502)
        self.assertIn("respuesta incompleta", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
