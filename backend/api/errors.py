"""
POLARIS-EMS — Structured API Error Contracts & Exception Handlers
SIH26061: Polar Energy Management & Resilience System

Provides structured, machine-readable error contracts and FastAPI handlers.
Guarantees:
- Zero raw Python tracebacks leaked to clients.
- Distinct error codes: STATION_NOT_FOUND, SCENARIO_NOT_FOUND, INVALID_REQUEST, UPSTREAM_UNAVAILABLE, INTERNAL_ERROR.
- Request correlation ID attached to all error responses.
"""

from typing import List, Optional, Any
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field
import uuid


class ErrorDetail(BaseModel):
    """Machine-readable and human-readable error container."""
    code: str = Field(..., description="Unique machine-readable error code")
    message: str = Field(..., description="Human-readable explanation")
    diagnostics: List[str] = Field(default_factory=list, description="Diagnostic details")
    field: Optional[str] = Field(None, description="Request field that caused the error if applicable")


class ErrorResponse(BaseModel):
    """Standardized error response payload."""
    request_id: str
    status: str = "ERROR"
    error: ErrorDetail
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    api_version: str = "v1"


# ------------------------------------------------------------------------------
# Custom Polaris API Exceptions
# ------------------------------------------------------------------------------

class PolarisAPIException(Exception):
    """Base exception for all Polaris-EMS API errors."""
    def __init__(
        self,
        message: str,
        code: str = "POLARIS_API_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        diagnostics: Optional[List[str]] = None,
        field: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.diagnostics = diagnostics or []
        self.field = field


class StationNotFoundException(PolarisAPIException):
    """Raised when a requested station ID does not exist."""
    def __init__(self, station_id: str):
        super().__init__(
            message=f"Station '{station_id}' not found. Available stations: BHARATI, MAITRI, HIMADRI",
            code="STATION_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            diagnostics=[f"Unknown station_id: {station_id}"],
            field="station_id"
        )


class ScenarioNotFoundException(PolarisAPIException):
    """Raised when a requested scenario ID does not exist."""
    def __init__(self, scenario_id: str):
        super().__init__(
            message=f"Scenario '{scenario_id}' not found in the authoritative ScenarioRegistry",
            code="SCENARIO_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            diagnostics=[f"Unknown scenario_id: {scenario_id}"],
            field="scenario_id"
        )


class InvalidRequestException(PolarisAPIException):
    """Raised when request parameters violate domain or input contracts."""
    def __init__(self, message: str, diagnostics: Optional[List[str]] = None, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            diagnostics=diagnostics or [message],
            field=field
        )


class UpstreamUnavailableException(PolarisAPIException):
    """Raised when a required upstream engine or data provider is unavailable."""
    def __init__(self, message: str, diagnostics: Optional[List[str]] = None):
        super().__init__(
            message=message,
            code="UPSTREAM_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            diagnostics=diagnostics or [message]
        )


# ------------------------------------------------------------------------------
# FastAPI Exception Handlers
# ------------------------------------------------------------------------------

def get_request_id_from_request(request: Request) -> str:
    """Retrieves request_id from state or header, or generates fallback."""
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:8]}"


async def polaris_exception_handler(request: Request, exc: PolarisAPIException) -> JSONResponse:
    """Handles all domain-specific PolarisAPIException instances."""
    req_id = get_request_id_from_request(request)
    error_payload = ErrorResponse(
        request_id=req_id,
        status="ERROR",
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            diagnostics=exc.diagnostics,
            field=exc.field
        )
    )
    return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI/Pydantic request body and query validation errors."""
    req_id = get_request_id_from_request(request)
    diagnostics = []
    first_field = None
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", [])])
        msg = err.get("msg", "Validation error")
        diagnostics.append(f"{loc}: {msg}")
        if first_field is None and err.get("loc"):
            first_field = str(err["loc"][-1])

    error_payload = ErrorResponse(
        request_id=req_id,
        status="ERROR",
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request schema validation failed",
            diagnostics=diagnostics,
            field=first_field
        )
    )
    status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
    return JSONResponse(status_code=status_code, content=error_payload.model_dump())


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles generic HTTP exceptions (e.g. 404 routes, 405 methods)."""
    req_id = get_request_id_from_request(request)
    code_map = {
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN"
    }
    err_code = code_map.get(exc.status_code, "HTTP_ERROR")
    error_payload = ErrorResponse(
        request_id=req_id,
        status="ERROR",
        error=ErrorDetail(
            code=err_code,
            message=str(exc.detail),
            diagnostics=[str(exc.detail)]
        )
    )
    return JSONResponse(status_code=exc.status_code, content=error_payload.model_dump())


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled server exceptions, preventing raw Python tracebacks from leaking."""
    req_id = get_request_id_from_request(request)
    error_payload = ErrorResponse(
        request_id=req_id,
        status="ERROR",
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal server error occurred while processing the request",
            diagnostics=[f"Unhandled exception type: {type(exc).__name__}"]
        )
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_payload.model_dump())
