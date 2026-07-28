"""
FastAPI middleware: request logging + Prometheus timing.

Two middlewares registered:
  1. LoggingMiddleware  — logs method, path, status code, and duration
  2. PrometheusMiddleware — records request latency histogram per route
"""
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with timing."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = round(time.perf_counter() - start, 4)
        logger.info(
            "%s %s → %s (%.4fs)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )
        return response
