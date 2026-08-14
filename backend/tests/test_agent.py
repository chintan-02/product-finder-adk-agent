"""Credential-free tests for the ADK agent definition and function tool."""

from __future__ import annotations

import unittest

from backend.app.agent import AGENT_INSTRUCTION, create_root_agent, find_products
from backend.app.config import Settings


class ProductToolTests(unittest.TestCase):
    def test_tool_returns_required_combined_filter_results(self) -> None:
        result = find_products(category="clothing", price_operator="lt", price_value=50)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 2)
        self.assertEqual(
            [product["name"] for product in result["products"]],
            ["UBC Hoodie", "T-Shirt"],
        )

    def test_tool_returns_all_products_without_filters(self) -> None:
        result = find_products()

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["count"], 13)

    def test_tool_returns_safe_error_for_invalid_operator(self) -> None:
        result = find_products(price_operator="around", price_value=50)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["products"], [])
        self.assertNotIn("traceback", result["message"].casefold())

    def test_tool_returns_serializable_product_urls(self) -> None:
        result = find_products(search_text="headphones")

        self.assertIsInstance(result["products"][0]["image"], str)


class AgentDefinitionTests(unittest.TestCase):
    def test_exactly_one_agent_with_one_search_tool(self) -> None:
        agent = create_root_agent(Settings(agent_model="test-model"))

        self.assertEqual(agent.name, "product_finder_agent")
        self.assertEqual(agent.model, "test-model")
        self.assertEqual(len(agent.sub_agents), 0)
        self.assertEqual(len(agent.tools), 1)
        self.assertEqual(agent.tools[0].__name__, "find_products")

    def test_instruction_preserves_deterministic_boundary(self) -> None:
        normalized = AGENT_INSTRUCTION.casefold()

        self.assertIn("only authoritative product source", normalized)
        self.assertIn("never perform category or numeric price filtering yourself", normalized)
        self.assertIn("call find_products exactly once", normalized)


if __name__ == "__main__":
    unittest.main()
