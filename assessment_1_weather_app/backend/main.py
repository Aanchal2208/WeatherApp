"""FastAPI Application Entry Point for Weather Intelligence Platform — Assessment 1.

Author: Aanchal Singh
Organization: PM Accelerator / Product Manager Accelerator
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import config
from backend.database import init_db
from backend.routes import weather, locations, integrations, exports, health

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("weather_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager initializing database tables on startup."""
    logger.info("Initializing database schema...")
    init_db()
    logger.info("Application startup complete.")
    yield


app = FastAPI(
    title=config.PROJECT_NAME,
    description=(
        "Technical Assessment 1: Robust FastAPI weather backend with PostgreSQL persistence, "
        "complete CRUD operations, Open-Meteo & Nominatim integrations, Leaflet maps, and multi-format exports."
    ),
    version=config.VERSION,
    lifespan=lifespan,
    contact={
        "name": config.DEVELOPER,
        "organization": config.ORGANIZATION,
    },
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Centralized exception handlers
@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    """Handles data validation and geocoding lookup failures cleanly."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "detail": str(exc)},
    )


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors and hides internal stack traces from API consumers."""
    logger.error("Unhandled server exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred while processing your request. Please try again later.",
        },
    )


# Register API Routers
app.include_router(weather.router)
app.include_router(locations.router)
app.include_router(integrations.router)
app.include_router(exports.router)
app.include_router(health.router)

# Mount frontend static directory
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Weather Intelligence Platform API is running. Access /docs for Swagger UI."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
