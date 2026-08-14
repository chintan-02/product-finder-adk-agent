"""FastAPI boundary tests that never call Gemini."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from backend.app.agent_runtime import AgentExecutionResult
from backend.app.config import Settings
from backend.app.main import create_app, get_runtime


SUCCESSFUL_TOOL_RESULT = {
    "status": "success",
    "products": [
        {
            "id": 0,
            "name": "UBC Hoodie",
            "category": "clothing",
            "description": "Cozy cotton hoodie with UBC branding.",
            "price": 45,
            "image": "https://i.ebayimg.com/images/g/w4oAAOSwyt9e34Mg/s-l1200.jpg",
        },
        {
            "id": 7,
            "name": "T-Shirt",
            "category": "clothing",
            "description": "Soft cotton material.",
            "price": 15,
            "image": "https://i.ebayimg.com/images/g/w4oAAOSwyt9e34Mg/s-l1200.jpg",
        },
    ],
    "applied_filters": {
        "category": "clothing",
        "price_operator": "lt",
        "price_value": 50,
        "search_text": None,
    },
    "count": 2,
}


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = AsyncMock()
        self.runtime.run.return_value = AgentExecutionResult(
            message="Here are the clothing items under $50.",
            tool_result=SUCCESSFUL_TOOL_RESULT,
        )
        self.app = create_app(
            Settings(
                agent_model="test-model",
                allowed_origins=("https://frontend.example",),
            )
        )
        self.app.dependency_overrides[get_runtime] = lambda: self.runtime
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def test_health_does_not_call_agent(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy", "service": "product_finder"})
        self.runtime.run.assert_not_awaited()

    def test_valid_chat_returns_structured_tool_products(self) -> None:
        response = self.client.post(
            "/api/v1/chat",
            json={"message": "What clothing items are available under $50?"},
        )

        body = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["count"], 2)
        self.assertEqual([item["name"] for item in body["products"]], ["UBC Hoodie", "T-Shirt"])
        self.assertEqual(body["applied_filters"]["price_operator"], "lt")
        self.assertEqual(body["request_id"], response.headers["X-Request-ID"])
        self.runtime.run.assert_awaited_once_with(
            "What clothing items are available under $50?"
        )

    def test_message_is_trimmed_before_agent_call(self) -> None:
        response = self.client.post("/api/v1/chat", json={"message": "  show clothing  "})

        self.assertEqual(response.status_code, 200)
        self.runtime.run.assert_awaited_once_with("show clothing")

    def test_empty_message_is_rejected_without_agent_call(self) -> None:
        response = self.client.post("/api/v1/chat", json={"message": "   "})

        self.assertEqual(response.status_code, 422)
        self.runtime.run.assert_not_awaited()

    def test_overlong_message_is_rejected(self) -> None:
        response = self.client.post("/api/v1/chat", json={"message": "x" * 501})

        self.assertEqual(response.status_code, 422)
        self.runtime.run.assert_not_awaited()

    def test_extra_request_fields_are_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/chat",
            json={"message": "show clothing", "api_key": "must-not-be-accepted"},
        )

        self.assertEqual(response.status_code, 422)
        self.runtime.run.assert_not_awaited()

    def test_agent_tool_error_returns_safe_502(self) -> None:
        self.runtime.run.return_value = AgentExecutionResult(
            message="Unable to search.",
            tool_result={"status": "error", "products": [], "count": 0},
        )

        response = self.client.post("/api/v1/chat", json={"message": "products around $50"})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "The product agent could not complete the request.")
        self.assertNotIn("traceback", response.text.casefold())

    def test_malformed_tool_output_returns_safe_502(self) -> None:
        malformed = dict(SUCCESSFUL_TOOL_RESULT)
        malformed["count"] = 99
        self.runtime.run.return_value = AgentExecutionResult("Done", malformed)

        response = self.client.post("/api/v1/chat", json={"message": "show clothing"})

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("99 products", response.text)

    def test_runtime_failure_returns_safe_502(self) -> None:
        self.runtime.run.side_effect = RuntimeError("sensitive upstream details")

        response = self.client.post("/api/v1/chat", json={"message": "show clothing"})

        self.assertEqual(response.status_code, 502)
        self.assertNotIn("sensitive upstream details", response.text)

    def test_allowed_cors_preflight(self) -> None:
        response = self.client.options(
            "/api/v1/chat",
            headers={
                "Origin": "https://frontend.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"],
            "https://frontend.example",
        )

    def test_unapproved_origin_receives_no_cors_allow_origin_header(self) -> None:
        response = self.client.get(
            "/health",
            headers={"Origin": "https://unapproved.example"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access-control-allow-origin", response.headers)


if __name__ == "__main__":
    unittest.main()
