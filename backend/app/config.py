"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_AGENT_MODEL = "gemini-3.6-flash"
DEFAULT_APP_NAME = "product_finder"


@dataclass(frozen=True, slots=True)
class Settings:
    """Small immutable settings object for the prototype backend."""

    agent_model: str = DEFAULT_AGENT_MODEL
    app_name: str = DEFAULT_APP_NAME

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            agent_model=os.getenv("PRODUCT_AGENT_MODEL", DEFAULT_AGENT_MODEL).strip(),
            app_name=os.getenv("ADK_APP_NAME", DEFAULT_APP_NAME).strip(),
        )
