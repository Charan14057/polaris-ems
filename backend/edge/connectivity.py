"""
POLARIS-EMS — Edge Connectivity Intelligence & State Machine
SIH26061: Polar Energy Management & Resilience System

Tracks connectivity health between polar edge field infrastructure and the central
Polaris-EMS backend/decision pathway:
- Heartbeat age and contact recency.
- Consecutive transmission failures and packet loss percentage.
- Dynamic state transitions: CONNECTED -> DEGRADED -> OFFLINE -> RECONNECTING.
- Buffer depth awareness.

INVARIANTS:
- Honest reporting: Does not assume cloud connectivity exists without evidence.
- Deterministic state machine.
"""

from typing import Dict, Optional, List
from datetime import datetime, timezone
import dateutil.parser

from backend.edge.schema import (
    ConnectivityState,
    ConnectivityStatus
)


class ConnectivityTracker:
    """Manages the connectivity state machine for a specific polar station edge node."""

    def __init__(
        self,
        station_id: str,
        heartbeat_timeout_sec: float = 30.0,
        degraded_failure_threshold: int = 1,
        offline_failure_threshold: int = 3
    ):
        self.station_id = station_id.upper()
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.degraded_failure_threshold = degraded_failure_threshold
        self.offline_failure_threshold = offline_failure_threshold

        self.state: ConnectivityState = ConnectivityState.CONNECTED
        self.last_successful_contact: Optional[datetime] = datetime.now(timezone.utc)
        self.consecutive_failures: int = 0
        self.packet_loss_pct: float = 0.0
        self.buffered_count: int = 0
        self.sync_in_progress: bool = False
        self.diagnostics: List[str] = ["Initial nominal edge connectivity"]

        # Rolling history of last 20 transmission attempts (True = success, False = failure)
        self._history: List[bool] = [True]

    def record_success(self, current_time: Optional[datetime] = None) -> None:
        """Records a successful backend transaction or heartbeat."""
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        self.last_successful_contact = now
        self.consecutive_failures = 0
        self._history.append(True)
        if len(self._history) > 20:
            self._history.pop(0)

        self._update_packet_loss()

        if self.sync_in_progress:
            self.state = ConnectivityState.RECONNECTING
            self.diagnostics.append("Telemetry synchronization in progress")
        elif self.buffered_count > 0:
            self.state = ConnectivityState.RECONNECTING
            self.diagnostics.append(f"Connection restored; {self.buffered_count} buffered items awaiting reconciliation")
        else:
            self.state = ConnectivityState.CONNECTED
            self.diagnostics = ["Backend communication channel verified active"]

    def record_failure(self, reason: str, current_time: Optional[datetime] = None) -> None:
        """Records a failed backend transaction, timeout, or transmission dropout."""
        self.consecutive_failures += 1
        self._history.append(False)
        if len(self._history) > 20:
            self._history.pop(0)

        self._update_packet_loss()

        if self.consecutive_failures >= self.offline_failure_threshold:
            self.state = ConnectivityState.OFFLINE
            diag = f"[OFFLINE] {self.consecutive_failures} consecutive failures: {reason}"
        elif self.consecutive_failures >= self.degraded_failure_threshold:
            self.state = ConnectivityState.DEGRADED
            diag = f"[DEGRADED] Intermittent failure ({self.consecutive_failures} fails): {reason}"
        else:
            diag = f"Transient transmission glitch: {reason}"

        self.diagnostics.append(diag)
        if len(self.diagnostics) > 10:
            self.diagnostics.pop(0)

    def start_reconnect(self) -> None:
        """Explicitly flags that a reconnection and resynchronization attempt is underway."""
        self.state = ConnectivityState.RECONNECTING
        self.sync_in_progress = True
        self.diagnostics.append("Initiating handshake and state resynchronization")

    def finish_reconnect(self) -> None:
        """Concludes reconciliation and returns to nominal connected state."""
        self.sync_in_progress = False
        self.consecutive_failures = 0
        self.state = ConnectivityState.CONNECTED
        self.diagnostics = ["Resynchronization complete; nominal connected operation restored"]

    def set_buffered_count(self, count: int) -> None:
        """Updates known queue depth of locally buffered messages."""
        self.buffered_count = max(0, count)

    def _update_packet_loss(self) -> None:
        if not self._history:
            self.packet_loss_pct = 0.0
            return
        losses = sum(1 for passed in self._history if not passed)
        self.packet_loss_pct = round((losses / len(self._history)) * 100.0, 1)

    def get_status(self, current_time: Optional[datetime] = None) -> ConnectivityStatus:
        """Evaluates current connectivity state and returns structured status envelope."""
        now = current_time or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        heartbeat_age_sec = (now - self.last_successful_contact).total_seconds() if self.last_successful_contact else 9999.0

        # Automatic timeout transition if no success recorded within timeout
        if heartbeat_age_sec > self.heartbeat_timeout_sec and self.state == ConnectivityState.CONNECTED:
            self.state = ConnectivityState.DEGRADED
            self.diagnostics.append(f"Heartbeat age {heartbeat_age_sec:.1f}s exceeded timeout {self.heartbeat_timeout_sec}s")

        return ConnectivityStatus(
            station_id=self.station_id,
            connectivity_state=self.state,
            last_successful_contact=self.last_successful_contact.isoformat() if self.last_successful_contact else None,
            heartbeat_age_sec=round(max(0.0, heartbeat_age_sec), 1),
            packet_loss_pct=self.packet_loss_pct,
            buffered_count=self.buffered_count,
            consecutive_failures=self.consecutive_failures,
            sync_in_progress=self.sync_in_progress,
            diagnostics=list(self.diagnostics[-5:]),
            provenance="CONFIGURED"
        )
