"""
POLARIS-EMS — Standard API Response Envelope
SIH26061: Polar Energy Management & Resilience System

Provides a consistent, typed API response envelope across all endpoints.
Preserves distinction between HTTP status codes and domain-level statuses:
- SUCCESS: Operation executed and domain status is nominal/optimal.
- PARTIAL: Operation completed with fallback, advisory, or requires-optimization status.
- ERROR: Operation could not proceed or encountered validation failure.

Strictly enforces the locked 6-tier provenance taxonomy:
{REAL, CONFIGURED, ASSUMED, SYNTHETIC, FORECAST, SIMULATED}
"""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
import uuid


T = TypeVar("T")

LOCKED_PROVENANCE_TIERS = {
    "REAL",
    "CONFIGURED",
    "ASSUMED",
    "SYNTHETIC",
    "FORECAST",
    "SIMULATED"
}


class APIResponse(BaseModel, Generic[T]):
    """Standardized production API response envelope for Polaris-EMS."""
    request_id: str = Field(..., description="Unique deterministic-format request correlation ID")
    status: str = Field(..., description="Domain execution status: SUCCESS | PARTIAL | ERROR")
    data: Optional[T] = Field(None, description="Typed domain payload")
    diagnostics: List[str] = Field(default_factory=list, description="Diagnostic, warning, or audit messages")
    provenance: str = Field("SIMULATED", description="Authoritative locked 6-tier provenance value")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 response creation timestamp"
    )
    api_version: str = Field("v1", description="Semantic API version")

    @field_validator("provenance")
    @classmethod
    def validate_provenance_tier(cls, v: str) -> str:
        prov_upper = v.upper()
        if prov_upper not in LOCKED_PROVENANCE_TIERS:
            raise ValueError(
                f"Provenance '{v}' violates the locked 6-tier taxonomy: {sorted(list(LOCKED_PROVENANCE_TIERS))}"
            )
        return prov_upper

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"SUCCESS", "PARTIAL", "ERROR"}
        v_upper = v.upper()
        if v_upper not in valid_statuses:
            raise ValueError(f"Status '{v}' must be one of {valid_statuses}")
        return v_upper

    @classmethod
    def success(
        cls,
        data: T,
        request_id: Optional[str] = None,
        provenance: str = "SIMULATED",
        diagnostics: Optional[List[str]] = None,
        status: str = "SUCCESS"
    ) -> "APIResponse[T]":
        """Factory for successful responses."""
        return cls(
            request_id=request_id or f"req-{uuid.uuid4().hex[:8]}",
            status=status,
            data=data,
            diagnostics=diagnostics or [],
            provenance=provenance,
            timestamp=datetime.now(timezone.utc).isoformat(),
            api_version="v1"
        )

    @classmethod
    def error(
        cls,
        message: str,
        request_id: Optional[str] = None,
        diagnostics: Optional[List[str]] = None,
        provenance: str = "CONFIGURED"
    ) -> "APIResponse[None]":
        """Factory for error responses."""
        diag = diagnostics or []
        if message and message not in diag:
            diag = [message] + diag
        return cls(
            request_id=request_id or f"req-{uuid.uuid4().hex[:8]}",
            status="ERROR",
            data=None,
            diagnostics=diag,
            provenance=provenance,
            timestamp=datetime.now(timezone.utc).isoformat(),
            api_version="v1"
        )
