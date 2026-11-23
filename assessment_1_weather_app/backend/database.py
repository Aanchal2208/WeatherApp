"""Database session management and engine initialization using SQLAlchemy."""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.config import config

logger = logging.getLogger("weather_app.database")

# Declarative base class for all SQLAlchemy ORM models
Base = declarative_base()

# Configure database engine
# Supports PostgreSQL with psycopg driver
engine_kwargs = {
    "pool_pre_ping": True,  # Test connections before checkout to prevent stale socket errors
}

if "sqlite" not in config.DATABASE_URL:
    engine_kwargs.update({
        "pool_size": config.DB_POOL_SIZE,
        "max_overflow": config.DB_MAX_OVERFLOW,
        "connect_args": {"connect_timeout": 2},  # 2 second connect timeout
    })

engine = create_engine(config.DATABASE_URL, **engine_kwargs)

# Thread-local session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request.

    Guarantees session cleanup in a finally block to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> dict:
    """Verifies active connectivity to the PostgreSQL database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "connected", "database": "PostgreSQL", "error": None}
    except Exception as exc:
        logger.warning("Database connection failed: %s", exc)
        return {
            "status": "disconnected",
            "database": "PostgreSQL",
            "error": str(exc),
            "hint": (
                "PostgreSQL server not detected on localhost:5432. "
                "Ensure PostgreSQL service is running or configure DATABASE_URL in .env."
            ),
        }


def init_db():
    """Initializes database tables defined in models.py."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully.")
    except Exception as exc:
        logger.error("Error creating database tables: %s", exc)
