"""
API Routes package initialization.
"""

from src.api.routes.health import router as health_router
from src.api.routes.models_route import router as models_router
from src.api.routes.analysis import router as analysis_router

__all__ = ["health_router", "models_router", "analysis_router"]
