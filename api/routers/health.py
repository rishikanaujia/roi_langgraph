"""
Health Check Router

Provides health check endpoint for monitoring.
"""

from datetime import datetime
from fastapi import APIRouter

from api.models.schemas import HealthResponse
from api.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns API status, version, and current timestamp.
    """
    return HealthResponse(
        status="healthy",
        version=settings.api_version,
        timestamp=datetime.now().isoformat()
    )