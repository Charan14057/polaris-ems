"""
POLARIS-EMS — API Middleware
SIH26061: Polar Energy Management & Resilience System

Provides:
- RequestCorrelationMiddleware: Injects deterministic request correlation ID (X-Request-ID).
- Process timing: Records and attaches elapsed execution duration (X-Process-Time-Sec).
- SecurityHeadersMiddleware: Enforces standard enterprise HTTP security headers.
- PayloadLimitMiddleware: Prevents denial-of-service via oversized request payloads.
- Structured logging: Logs endpoint, method, duration, and outcome.
"""

import time
import uuid
import logging
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse

from backend.config.settings import get_settings

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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces enterprise security headers across all API responses."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        settings = get_settings()

        if settings.security.enable_security_headers:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self' http: https:;"
            )
        return response


class PayloadLimitMiddleware(BaseHTTPMiddleware):
    """Rejects request bodies exceeding configured maximum payload size."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length: Optional[str] = request.headers.get("content-length")
        settings = get_settings()

        if content_length:
            try:
                length = int(content_length)
                if length > settings.security.max_request_bytes:
                    req_id = getattr(request.state, "request_id", f"req-{uuid.uuid4().hex[:8]}")
                    logger.warning(f"[{req_id}] Rejected oversized payload: {length} bytes > {settings.security.max_request_bytes}")
                    return JSONResponse(
                        status_code=413,
                        content={
                            "request_id": req_id,
                            "status": "ERROR",
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request body size ({length} bytes) exceeds limit ({settings.security.max_request_bytes} bytes)",
                                "details": {"max_bytes": settings.security.max_request_bytes, "actual_bytes": length}
                            },
                            "provenance": "CONFIGURED"
                        }
                    )
            except ValueError:
                pass

        return await call_next(request)
