"""FastAPI application exposing the Product Finder ADK agent."""

from __future__ import annotations

import logging
from functools import lru_cache
from time import perf_counter
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .agent_runtime import ProductAgentRuntime
from .config import Settings
from .models import ChatRequest, ChatResponse, SearchResult


LOGGER = logging.getLogger("product_finder.api")


class AgentUpstreamError(RuntimeError):
    """Raised when ADK fails or returns unusable tool output."""


@lru_cache(maxsize=1)
def get_runtime() -> ProductAgentRuntime:
    """Reuse one runner/session service per backend process."""

    return ProductAgentRuntime()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory used by production and isolated API tests."""

    resolved_settings = settings or Settings.from_environment()
    app = FastAPI(
        title="Product Finder Agent API",
        version="0.1.0",
        description="Custom API for one Google ADK product-finder agent.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(resolved_settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        started_at = perf_counter()

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        LOGGER.info(
            "request_completed method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started_at) * 1000,
            request_id,
        )
        return response

    @app.exception_handler(AgentUpstreamError)
    async def handle_agent_error(request: Request, exc: AgentUpstreamError) -> JSONResponse:
        LOGGER.warning(
            "agent_upstream_error request_id=%s error_type=%s",
            request.state.request_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=502,
            content={
                "detail": "The product agent could not complete the request.",
                "request_id": request.state.request_id,
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        LOGGER.exception(
            "unexpected_error request_id=%s error_type=%s",
            request.state.request_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected server error occurred.",
                "request_id": request.state.request_id,
            },
        )

    @app.get("/health", tags=["operations"])
    async def health() -> dict[str, str]:
        return {"status": "healthy", "service": resolved_settings.app_name}

    @app.post("/api/v1/chat", response_model=ChatResponse, tags=["agent"])
    async def chat(
        payload: ChatRequest,
        request: Request,
        runtime: ProductAgentRuntime = Depends(get_runtime),
    ) -> ChatResponse:
        try:
            execution = await runtime.run(payload.message)
        except Exception as exc:
            raise AgentUpstreamError("ADK invocation failed") from exc

        tool_payload = execution.tool_result
        if tool_payload.get("status") != "success":
            raise AgentUpstreamError("Agent tool rejected its arguments")

        try:
            result = SearchResult.model_validate(
                {
                    "products": tool_payload.get("products"),
                    "applied_filters": tool_payload.get("applied_filters"),
                    "count": tool_payload.get("count"),
                }
            )
        except ValidationError as exc:
            raise AgentUpstreamError("Agent returned malformed tool output") from exc

        return ChatResponse(
            message=execution.message,
            products=result.products,
            applied_filters=result.applied_filters,
            count=result.count,
            request_id=request.state.request_id,
        )

    return app


app = create_app()
