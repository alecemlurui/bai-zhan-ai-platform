"""
api/health.py

健康检查。
"""

from fastapi import APIRouter

from ..config import SETTINGS
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": SETTINGS.APP_VERSION,
        "environment": SETTINGS.ENVIRONMENT,
    }
