"""
Main FastAPI Application Module for ContractRisk AI.
Configures FastAPI app, CORS middleware, global exception handlers, and API router endpoints.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import health_router, models_router, analysis_router

app = FastAPI(
    title="ContractRisk AI API",
    description="Production-grade RESTful API for contract processing, hybrid risk analysis, and future scenario prediction.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api/v1
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(models_router, prefix="/api/v1", tags=["Models"])
app.include_router(analysis_router, prefix="/api/v1", tags=["Analysis"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler sanitizing unhandled internal errors.
    Prevents stack trace or filesystem leakage to API clients.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing the request.",
            "error_type": type(exc).__name__
        }
    )
