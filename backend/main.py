"""
Tryloop — FastAPI application entry point.
Routers and middleware will be registered here as they are built.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Tryloop API",
    description="Backend API for the Tryloop device trial platform",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    """Simple health check used by Docker and monitoring."""
    return {"status": "ok"}
