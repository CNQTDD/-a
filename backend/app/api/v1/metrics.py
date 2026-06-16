from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.observability.metrics import (
    CONTENT_TYPE_LATEST,
    build_metrics_summary,
    render_prometheus_metrics,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
async def metrics_summary(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return build_metrics_summary(settings.service_name)


@router.get("")
async def prometheus_metrics() -> PlainTextResponse:
    return PlainTextResponse(render_prometheus_metrics(), media_type=CONTENT_TYPE_LATEST)

