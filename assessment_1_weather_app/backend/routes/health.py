"""FastAPI router for application health and diagnostics."""

from fastapi import APIRouter
from backend.config import config
from backend.database import check_database_connection
from backend.services.integrations import PM_ACCELERATOR_DETAILS

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check():
    """System diagnostic endpoint verifying database connectivity and configuration."""
    db_status = check_database_connection()

    return {
        "status": "healthy" if db_status["status"] == "connected" else "degraded",
        "project": config.PROJECT_NAME,
        "version": config.VERSION,
        "developer": PM_ACCELERATOR_DETAILS["developer"],
        "organization": PM_ACCELERATOR_DETAILS["organization"],
        "database": db_status,
        "apis": {
            "open_meteo": "operational (free tier, no key required)",
            "nominatim_osm": "operational (free tier, 1 req/sec)",
            "youtube_v3": "configured" if config.YOUTUBE_API_KEY else "fallback_url_mode",
        },
    }
