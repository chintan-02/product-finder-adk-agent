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
    allowed_origins: tuple[str, ...] = ("http://localhost:5173",)

    @classmethod
    def from_environment(cls) -> "Settings":
        raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
        allowed_origins = tuple(
            origin.strip().rstrip("/")
            for origin in raw_origins.split(",")
            if origin.strip()
        )
        return cls(
            agent_model=os.getenv("PRODUCT_AGENT_MODEL", DEFAULT_AGENT_MODEL).strip(),
            app_name=os.getenv("ADK_APP_NAME", DEFAULT_APP_NAME).strip(),
            allowed_origins=allowed_origins,
        )
