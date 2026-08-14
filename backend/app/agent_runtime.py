"""Programmatic ADK execution used later by the custom FastAPI endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent
from .config import Settings


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    """Authoritative result collected from one ADK invocation."""

    message: str
    tool_result: dict[str, Any]


class ProductAgentRuntime:
    """Own the runner and ephemeral sessions for the single ADK agent."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_environment()
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name=self.settings.app_name,
            agent=root_agent,
            session_service=self.session_service,
        )

    async def run(self, message: str) -> AgentExecutionResult:
        """Run one user query and collect final text plus structured tool output."""

        user_id = "anonymous"
        session_id = uuid4().hex
        await self.session_service.create_session(
            app_name=self.settings.app_name,
            user_id=user_id,
            session_id=session_id,
        )

        user_content = types.Content(role="user", parts=[types.Part(text=message)])
        final_message = ""
        tool_result: dict[str, Any] | None = None

        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_content,
        ):
            if event.content:
                for part in event.content.parts or []:
                    if part.function_response and part.function_response.name == "find_products":
                        response = part.function_response.response
                        if isinstance(response, dict):
                            tool_result = response
                    if event.is_final_response() and part.text:
                        final_message += part.text

        if tool_result is None:
            raise RuntimeError("The product agent completed without calling find_products.")

        return AgentExecutionResult(
            message=final_message.strip() or "Product search completed.",
            tool_result=tool_result,
        )
