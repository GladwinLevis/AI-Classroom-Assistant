import logging
from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middleware

# Initialize logging before creating the app instance
setup_logging()
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from app.core.redis import redis_manager
from app.core.database import engine
from app.db.base import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.connect()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# Instantiate FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API services and AI infrastructure for AI Classroom Assistant.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Setup Middlewares (CORS, Request logging, etc.)
register_middleware(app)

# Register Exception Handlers (Mapping custom exceptions to standardized error outputs)
register_exception_handlers(app)

# Include aggregate v1 routing endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root Service Landing"])
async def root_landing():
    """Root landing endpoint providing API status and navigation links."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "frontend_app": "http://localhost:5173",
        "api_docs": "http://127.0.0.1:8000/docs",
        "health_check": "http://127.0.0.1:8000/health",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health Monitoring"])
async def health_check():
    """Simple API endpoint to confirm service status and routing activity."""
    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }


logger.info("FastAPI Application setup complete.")
