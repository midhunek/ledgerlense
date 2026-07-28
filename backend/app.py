from __future__ import annotations
"""
LedgerLens FastAPI application entry point.

Startup sequence:
  1. Create DB tables
  2. Register middleware (logging + Prometheus)
  3. Mount API router
  4. Expose /metrics endpoint for Prometheus scraping
  5. Serve /health endpoint
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from config.settings import settings
from core.middleware import LoggingMiddleware
from database.database import create_tables
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    create_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered invoice & receipt extraction with confidence-scored fields and human review queue.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
app.add_middleware(LoggingMiddleware)

# Include all API routes
app.include_router(router)

# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.APP_NAME}
