import asyncio
import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from google.adk.models import BaseLlm, LlmResponse
from google.genai import types

from backend.app.agent_runtime import ProductAgentRuntime
from backend.app.main import create_app, get_runtime
from backend.app.models import ProductFilters

CASES = json.loads((Path(__file__).parents[1] / "eval/conversations.json").read_text())
PATCHES = {turn["message"]: turn["patch"] for turns in CASES.values() for turn in turns}


class ScriptedModel(BaseLlm):
    async def generate_content_async(self, llm_request, stream=False):
        context = llm_request.contents[-1].parts[0].text
        query = context.split("Latest user message: ", 1)[1]
        call = types.Part.from_function_call(name="find_products", args=PATCHES[query])
        yield LlmResponse(content=types.Content(role="model", parts=[call]))


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ProductAgentRuntime()
        self.runtime.runner.agent.model = ScriptedModel(model="scripted")
        app = create_app()
        app.dependency_overrides[get_runtime] = lambda: self.runtime
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def send(self, message, filters=None, **options):
        response = self.client.post("/api/v1/chat", json={
            "message": message, "demo_catalogue": True,
            "active_filters": filters, **options,
        })
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_scripted_conversations_through_adk_and_api(self):
        for case, turns in CASES.items():
            filters = None
            for turn in turns:
                with self.subTest(case=case, turn=turn["message"]):
                    result = self.send(turn["message"], filters)
                    filters = result["applied_filters"]
                    self.assertEqual({k:v for k,v in filters.items() if v is not None}, turn["filters"])
                    self.assertEqual([p["id"] for p in result["products"]], turn["ids"])
                    self.assertEqual(result["relaxation_offer"], turn.get("offer"))
                    self.assertEqual(result["clarification"], turn.get("clarification", False))

    def test_concurrent_searches_preserve_independent_filters(self):
        async def run():
            return await asyncio.gather(
                self.runtime.run("Make that under $100.", demo=True,
                                 filters=ProductFilters(color="black", size="XL")),
                self.runtime.run("Make that under $100.", demo=True,
                                 filters=ProductFilters(color="blue", size="L")),
            )

        first, second = asyncio.run(run())
        self.assertEqual(first.tool_result["count"], 0)
        self.assertEqual(first.tool_result["applied_filters"]["size"], "XL")
        self.assertEqual([p["id"] for p in second.tool_result["products"]], [101])
        sessions = asyncio.run(self.runtime.session_service.list_sessions(
            app_name=self.runtime.settings.app_name, user_id="anonymous",
        ))
        self.assertEqual(sessions.sessions, [])

    def test_button_applies_only_the_calculated_budget_offer(self):
        result = self.send("Accept", CASES["walkthrough"][3]["filters"], accept_relaxation=True)
        self.assertEqual(result["applied_filters"]["max_price"], 115)
        self.assertEqual(result["applied_filters"]["size"], "XL")
        self.assertEqual([p["id"] for p in result["products"]], [102])

    def test_invalid_updates_are_atomic(self):
        previous = ProductFilters(color="black", min_price=80, max_price=100)
        from backend.app.conversation import apply_filters
        for changes, clear in [({"max_price": -1}, []), ({"max_price": 70}, []), ({}, ["unknown"])]:
            with self.assertRaises(ValueError):
                apply_filters(previous, changes, clear, False)
        self.assertEqual(previous.max_price, 100)
        self.assertEqual(previous.color, "black")
