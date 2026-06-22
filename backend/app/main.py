from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.errors import APIError
from app.core.config import Settings
from app.core.logging import configure_logging, get_trace_id, set_trace_id
from app.observability.metrics import CONTENT_TYPE_LATEST, render_prometheus_metrics


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        set_trace_id(trace_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = trace_id
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    configure_logging(settings)

    app = FastAPI(
        title="suzhida-api",
        version="0.1.0",
    )

    # Store settings on app state for dependency injection
    app.state.settings = settings

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:4173",
            "http://localhost:4173",
            "http://127.0.0.1:5280",
            "http://localhost:5280",
            "http://127.0.0.1:5299",
            "http://localhost:5299",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "trace_id": get_trace_id(),
            },
        )

    # Register v1 API router
    from app.api.v1.router import router as v1_router

    app.include_router(v1_router)

    # Health endpoint
    @app.get("/health")
    async def health():
        return {"service": settings.service_name, "status": "ok"}

    @app.get("/metrics")
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(
            render_prometheus_metrics(),
            media_type=CONTENT_TYPE_LATEST,
        )

    # Catch-all 404 — uses a proper exception handler instead of middleware
    @app.exception_handler(404)
    async def http_not_found_handler(request: Request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
                "trace_id": get_trace_id(),
            },
        )

    # Middleware: transform 404 starlette responses (from routing) into our envelope
    @app.middleware("http")
    async def wrap_404_responses(request: Request, call_next):
        response = await call_next(request)
        if response.status_code == 404 and "text/html" in response.headers.get(
            "content-type", ""
        ):
            return JSONResponse(
                status_code=404,
                content={
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "trace_id": get_trace_id(),
                },
            )
        return response

    return app
