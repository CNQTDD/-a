from fastapi import APIRouter

from app.api.v1.complaints import router as complaints_router
from app.api.v1.metrics import router as metrics_router

router = APIRouter(prefix="/api/v1")
router.include_router(complaints_router)
router.include_router(metrics_router)
