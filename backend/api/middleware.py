"""
POLARIS-EMS — API Middleware
SIH26061: Polar Energy Management & Resilience System

Provides:
- RequestCorrelationMiddleware: Injects deterministic request correlation ID (X-Request-ID).
- Process timing: Records and attaches elapsed execution duration (X-Process-Time-Sec).
- Structured logging: Logs endpoint, method, duration, and outcome.
"""

import time
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = logging.getLogger("polaris.api")


class RequestCorrelationMiddleware(BaseHTTPMiddleware):
    """Assigns unique request correlation ID and records request duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()

        # Extract incoming X-Request-ID or generate new deterministic-format ID
        req_id = request.headers.get("X-Request-ID")
        if not req_id:
            req_id = f"req-{uuid.uuid4().hex[:8]}"

        # Store in request state for downstream handlers and response wrappers
        request.state.request_id = req_id

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_sec = time.perf_counter() - start_time

        # Attach headers
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Sec"] = f"{duration_sec:.4f}"

        # Structured access log
        logger.info(
            f"[{req_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_sec*1000:.1f}ms)"
        )

        return response
