"""Health and readiness endpoints."""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    """Minimal liveness check. Returns no sensitive information."""
    return {"status": "ok", "service": "dailyforge-backend"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    """
    Readiness check — verifies database connectivity.
    Returns safe status information only, no internal details.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        logger.exception("Database connectivity check failed")
        db_status = "unavailable"

    ready = db_status == "connected"
    return {
        "status": "ready" if ready else "not_ready",
        "database": db_status,
    }
