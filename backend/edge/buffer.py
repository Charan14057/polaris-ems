"""
POLARIS-EMS — Bounded Local Telemetry Buffer & Store
SIH26061: Polar Energy Management & Resilience System

Provides local FIFO buffering for telemetry during connectivity degradation or blackouts:
- Bounded retention preventing memory exhaustion at polar edge nodes.
- Chronological ordering and duplicate suppression.
- Three-state lifecycle: BUFFERED -> IN_FLIGHT -> CONFIRMED (acknowledged).
- Resilient replay and failed-synchronization retry.

INVARIANTS:
- Does not falsely mark buffered data as backend-confirmed.
- Deterministic queue behavior.
"""

from typing import List, Dict, Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timezone
import uuid

from backend.edge.schema import TelemetryReading


class BufferedItem:
    """Wrapper around TelemetryReading tracking buffering lifecycle."""
    def __init__(self, reading: TelemetryReading):
        self.item_id: str = f"buf_{uuid.uuid4().hex[:12]}"
        self.reading: TelemetryReading = reading
        self.enqueued_at: str = datetime.now(timezone.utc).isoformat()
        self.state: str = "BUFFERED"  # BUFFERED | IN_FLIGHT | CONFIRMED
        self.retry_count: int = 0


class LocalTelemetryBuffer:
    """Bounded, chronological local buffer with deduplication and delivery guarantees."""

    def __init__(self, max_capacity: int = 5000):
        self.max_capacity = max_capacity
        # item_id -> BufferedItem
        self._items: OrderedDict[str, BufferedItem] = OrderedDict()
        # Deduplication index: (station_id, device_id, channel, timestamp) -> item_id
        self._dedup_keys: Dict[Tuple[str, str, str, str], str] = {}

    def enqueue(self, reading: TelemetryReading) -> Tuple[bool, str]:
        """
        Enqueues a reading into the bounded buffer.
        Returns: (enqueued: bool, message: str)
        """
        key = (
            reading.station_id.upper(),
            reading.device_id,
            reading.channel,
            reading.timestamp
        )

        # 1. Deduplication check
        if key in self._dedup_keys:
            existing_id = self._dedup_keys[key]
            return False, f"Duplicate telemetry rejected: already buffered as '{existing_id}'"

        # 2. Bounded capacity check (FIFO eviction if full)
        if len(self._items) >= self.max_capacity:
            # Evict oldest BUFFERED item
            oldest_id, oldest_item = next(iter(self._items.items()))
            old_key = (
                oldest_item.reading.station_id.upper(),
                oldest_item.reading.device_id,
                oldest_item.reading.channel,
                oldest_item.reading.timestamp
            )
            self._items.pop(oldest_id, None)
            self._dedup_keys.pop(old_key, None)

        item = BufferedItem(reading)
        self._items[item.item_id] = item
        self._dedup_keys[key] = item.item_id
        return True, item.item_id

    def peek_unconfirmed(self, limit: int = 100) -> List[BufferedItem]:
        """Returns the oldest unconfirmed buffered items without state transition."""
        result: List[BufferedItem] = []
        for item in self._items.values():
            if item.state in ("BUFFERED", "IN_FLIGHT"):
                result.append(item)
                if len(result) >= limit:
                    break
        return result

    def mark_in_flight(self, item_ids: List[str]) -> int:
        """Transitions items to IN_FLIGHT during a sync transmission."""
        count = 0
        for iid in item_ids:
            if iid in self._items and self._items[iid].state == "BUFFERED":
                self._items[iid].state = "IN_FLIGHT"
                self._items[iid].retry_count += 1
                count += 1
        return count

    def acknowledge(self, item_ids: List[str]) -> int:
        """Removes successfully confirmed items from the buffer."""
        acknowledged = 0
        for iid in item_ids:
            if iid in self._items:
                item = self._items.pop(iid)
                key = (
                    item.reading.station_id.upper(),
                    item.reading.device_id,
                    item.reading.channel,
                    item.reading.timestamp
                )
                self._dedup_keys.pop(key, None)
                acknowledged += 1
        return acknowledged

    def reset_in_flight(self) -> int:
        """Resets all IN_FLIGHT items back to BUFFERED upon transmission failure."""
        count = 0
        for item in self._items.values():
            if item.state == "IN_FLIGHT":
                item.state = "BUFFERED"
                count += 1
        return count

    def size(self) -> int:
        """Current number of items in the buffer."""
        return len(self._items)

    def clear(self) -> None:
        """Flushes the buffer completely."""
        self._items.clear()
        self._dedup_keys.clear()
