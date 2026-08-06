import os
import shutil
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
async def full_health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive diagnostic health check verifying DB, storage, and system metrics."""
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check DB error: {str(e)}")

    # Storage Check
    total, used, free = shutil.disk_usage("/")
    free_gb = round(free / (1024 ** 3), 2)

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "storage_free_gb": free_gb,
        "version": "1.0.0"
    }


@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe for container orchestrators (Kubernetes / Docker Swarm)."""
    return {"status": "alive"}


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Readiness probe verifying DB connectivity before serving live traffic."""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        return {"status": "not_ready", "database": "disconnected"}
