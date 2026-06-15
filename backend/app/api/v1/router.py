from fastapi import APIRouter

from app.api.v1.complaints import router as complaints_router

router = APIRouter(prefix="/api/v1")
router.include_router(complaints_router)
