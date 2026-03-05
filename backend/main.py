"""
Tryloop — FastAPI application entry point.
Routers and middleware will be registered here as they are built.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import engine
from routers import auth


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

# ── CORS — allow the Next.js frontend to call the API ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.NEXTAUTH_URL,  # frontend URL (e.g. http://localhost:3000)
        "http://localhost:3000",
        "https://tryloop.nl",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──
app.include_router(auth.router)


@app.get("/health")
def health_check():
    """Simple health check used by Docker and monitoring."""
    return {"status": "ok", "environment": settings.APP_ENV}
