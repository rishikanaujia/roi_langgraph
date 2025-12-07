"""
Phase 1 Rankings REST API

Main application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routers import health, rankings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: runs on startup and shutdown."""
    # ---- startup ----
    logger.info("=" * 70)
    logger.info(f"{settings.api_title} v{settings.api_version}")
    logger.info("=" * 70)
    logger.info(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info(f"Health Check: http://{settings.host}:{settings.port}/api/v1/health")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Reports Directory: {settings.reports_dir}")
    logger.info("=" * 70)

    # Hand control back to FastAPI (app is running here)
    try:
        yield
    finally:
        # ---- shutdown ----
        logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(rankings.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
    )
