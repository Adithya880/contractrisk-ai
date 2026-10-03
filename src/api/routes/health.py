"""
Health route module for GET /api/v1/health.
"""

from fastapi import APIRouter
from src.api.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns the health status and version of the ContractRisk AI service."
)
async def health_check() -> HealthResponse:
    """Check API service health status."""
    return HealthResponse(
        status="healthy",
        service="ContractRisk AI",
        version="1.0.0"
    )
