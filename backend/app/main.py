from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.errors import APIError
from app.core.config import Settings
from app.core.logging import configure_logging, get_trace_id, set_trace_id


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

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    app = FastAPI(
        title="suzhida-api",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIDMiddleware)

    # Exception handler
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

    # Health endpoint
    @app.get("/health")
    async def health():
        return {"service": settings.service_name, "status": "ok"}

    # Catch-all 404 handler
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "code": "NOT_FOUND",
                "message": "The requested resource was not found.",
                "trace_id": get_trace_id(),
            },
        )

    return app
