"""Run one ADK turn with validated filters supplied by the caller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import create_root_agent
from .config import Settings
from .models import ProductFilters


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    message: str
    tool_result: dict[str, Any]


class ProductAgentRuntime:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_environment()
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name=self.settings.app_name,
            agent=create_root_agent(self.settings),
            session_service=self.session_service,
        )

    async def run(
        self, message: str, *, filters: ProductFilters | None = None, demo: bool = False,
    ) -> AgentExecutionResult:
        identity = {
            "app_name": self.settings.app_name,
            "user_id": "anonymous",
            "session_id": uuid4().hex,
        }
        active = filters.model_dump(mode="json", exclude_none=True) if filters else {}
        await self.session_service.create_session(
            **identity, state={"active_filters": active, "demo_catalogue": demo},
        )
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=f"Current filters: {active!r}. Latest user message: {message}")],
        )
        tool_results = []
        try:
            async for event in self.runner.run_async(
                user_id=identity["user_id"],
                session_id=identity["session_id"],
                new_message=user_content,
            ):
                if event.content:
                    for part in event.content.parts or []:
                        response = part.function_response
                        if response and response.name == "find_products":
                            tool_results.append(response.response)
        finally:
            await self.session_service.delete_session(**identity)

        if len(tool_results) != 1 or not isinstance(tool_results[0], dict):
            raise RuntimeError("Expected exactly one structured product search result.")
        result = tool_results[0]
        reply = (
            "Which filter would you like to change? For a budget, enter an amount."
            if result.get("clarification") else f"{result['count']} exact matches."
        )
        return AgentExecutionResult(reply, result)
