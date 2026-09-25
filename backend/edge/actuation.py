"""
POLARIS-EMS — Actuation Boundary for Phase 16
SIH26061: Polar Energy Management & Resilience System

Defines the public actuation API that higher-level decision logic uses.
The boundary enforces architectural constraints:
- No real hardware I/O
- Authorization via dispatch_authorized from EdgeDecisionBridge
- Rich provenance metadata on every result

All outcome values are NOT provenance tiers — they describe execution
results within the validation environment.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from backend.edge.adapters import get_global_adapter_registry, DeviceAdapter
from backend.edge.schema import validate_provenance


class ActuationOutcome(str, Enum):
    """Possible outcomes of an actuation request.

    These values are *not* provenance tiers.
    """
    SIMULATED = "SIMULATED"
    HIL = "HIL"
    LAB = "LAB"
    UNAVAILABLE = "UNAVAILABLE"
    REJECTED = "REJECTED"


class ActuationRequest(BaseModel):
    """Schema for an actuation request."""
    station_id: str
    device_id: str
    action: str = Field(..., description="The name of the action to perform.")
    value: Optional[Any] = Field(None, description="Optional value/parameter for the action.")
    environment: Optional[str] = Field(
        None,
        description="Target execution environment (e.g. 'SIMULATOR', 'HIL', 'LAB').",
    )
    reason: Optional[str] = None

    @field_validator("environment")
    @classmethod
    def normalize_env(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else None


class ActuationResult(BaseModel):
    """Detailed result of an actuation request."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    station_id: str
    device_id: str
    action: str
    value: Optional[Any] = None
    authorized: bool
    outcome: ActuationOutcome
    environment: Optional[str] = None
    adapter_name: Optional[str] = None
    provenance: str = "SIMULATED"
    error_message: Optional[str] = None
    reason: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("provenance")
    @classmethod
    def check_prov(cls, v: str) -> str:
        return validate_provenance(v)


class ActuationBoundary:
    """Public facade for actuation requests.

    Orchestrates authorization, adapter resolution, execution,
    and result recording. No real I/O occurs.
    """

    def __init__(
        self,
        dispatch_authorized: bool = True,
        connectivity_state: Optional[str] = None,
    ):
        self.adapter_registry = get_global_adapter_registry()
        self._dispatch_authorized = dispatch_authorized
        self._connectivity_state = connectivity_state or "CONNECTED"
        self._history: List[ActuationResult] = []

    def set_authorization(self, authorized: bool) -> None:
        """Update dispatch authorization state."""
        self._dispatch_authorized = authorized

    def set_connectivity(self, state: str) -> None:
        """Update connectivity state for authorization decisions."""
        self._connectivity_state = state.upper()

    def request_actuation(self, request: ActuationRequest) -> ActuationResult:
        """Process an actuation request through the full boundary pipeline."""
        # 1. Authorization check
        authorized = self._authorize(request)
        if not authorized:
            result = ActuationResult(
                station_id=request.station_id,
                device_id=request.device_id,
                action=request.action,
                value=request.value,
                authorized=False,
                outcome=ActuationOutcome.REJECTED,
                environment=request.environment,
                adapter_name=None,
                error_message="Authorization denied: dispatch_authorized=False or connectivity prevents dispatch.",
                reason=request.reason,
                source_metadata={"source": "ACTUATION_BOUNDARY", "connectivity": self._connectivity_state},
            )
            self._history.append(result)
            return result

        # 2. Resolve adapter
        env = request.environment or "SIMULATOR"
        try:
            adapter: DeviceAdapter = self.adapter_registry.get(env)
        except Exception as exc:
            result = ActuationResult(
                station_id=request.station_id,
                device_id=request.device_id,
                action=request.action,
                value=request.value,
                authorized=True,
                outcome=ActuationOutcome.UNAVAILABLE,
                environment=env,
                adapter_name=None,
                error_message=str(exc),
                reason=request.reason,
                source_metadata={"source": "ACTUATION_BOUNDARY"},
            )
            self._history.append(result)
            return result

        # 3. Execute via adapter write_actuation
        command = {"action": request.action, "value": request.value}
        try:
            exec_result = adapter.write_actuation(request.device_id, command)
            status = exec_result.get("status", "SIMULATED").upper()
            try:
                outcome = ActuationOutcome[status]
            except KeyError:
                outcome = ActuationOutcome.SIMULATED
            error_msg = exec_result.get("error")
        except Exception as exc:
            outcome = ActuationOutcome.UNAVAILABLE
            error_msg = str(exc)

        result = ActuationResult(
            station_id=request.station_id,
            device_id=request.device_id,
            action=request.action,
            value=request.value,
            authorized=True,
            outcome=outcome,
            environment=env,
            adapter_name=adapter.__class__.__name__,
            error_message=error_msg,
            reason=request.reason,
            source_metadata={"source": "ACTUATION_BOUNDARY", "environment": env},
        )
        self._history.append(result)
        return result

    @property
    def history(self) -> List[ActuationResult]:
        """Read-only access to actuation history."""
        return list(self._history)

    def _authorize(self, request: ActuationRequest) -> bool:
        """Check authorization using dispatch_authorized and connectivity state."""
        if not self._dispatch_authorized:
            return False
        # OFFLINE or SAFE_HOLD states cannot dispatch
        if self._connectivity_state in ("OFFLINE", "SAFE_HOLD"):
            return False
        return True
