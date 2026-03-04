"""
Tryloop — FastAPI application entry point.
Routers and middleware will be registered here as they are built.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import settings
from core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown: verify DB connection on boot, clean up on exit."""
    try:
        # Quick connectivity check — just open and close a connection
        with engine.connect():
            pass
    except Exception:
        pass  # DB may not be ready during initial dev; don't crash the app
    yield
    engine.dispose()


app = FastAPI(
    title="Tryloop API",
    description="Backend API for the Tryloop device trial platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Simple health check used by Docker and monitoring."""
    return {"status": "ok", "environment": settings.APP_ENV}
