"""Thread-safe Snowflake ID generation."""

from __future__ import annotations

import threading
import time


class SnowflakeClockRollbackError(RuntimeError):
    """Raised when the system clock moves behind the last generated timestamp."""


class SnowflakeIdGenerator:
    """Generate sortable 64-bit IDs with a 41/5/5/12 bit layout."""

    _TIMESTAMP_BITS = 41
    _WORKER_BITS = 5
    _DATACENTER_BITS = 5
    _SEQUENCE_BITS = 12
    _MAX_WORKER_ID = (1 << _WORKER_BITS) - 1
    _MAX_DATACENTER_ID = (1 << _DATACENTER_BITS) - 1
    _SEQUENCE_MASK = (1 << _SEQUENCE_BITS) - 1
    _WORKER_SHIFT = _SEQUENCE_BITS
    _DATACENTER_SHIFT = _SEQUENCE_BITS + _WORKER_BITS
    _TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_BITS + _DATACENTER_BITS

    def __init__(
        self,
        *,
        epoch_ms: int,
        worker_id: int,
        datacenter_id: int,
    ) -> None:
        if worker_id < 0 or worker_id > self._MAX_WORKER_ID:
            raise ValueError(f"worker_id must be between 0 and {self._MAX_WORKER_ID}")
        if datacenter_id < 0 or datacenter_id > self._MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id must be between 0 and {self._MAX_DATACENTER_ID}")
        if epoch_ms <= 0:
            raise ValueError("epoch_ms must be positive")

        self._epoch_ms = epoch_ms
        self._worker_id = worker_id
        self._datacenter_id = datacenter_id
        self._last_timestamp = -1
        self._sequence = 0
        self._lock = threading.Lock()

    def next_id(self) -> int:
        """Return the next unique, time-sortable integer ID."""
        with self._lock:
            timestamp = self._current_timestamp()
            if timestamp < self._last_timestamp:
                raise SnowflakeClockRollbackError(
                    f"clock moved backwards by {self._last_timestamp - timestamp}ms"
                )

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & self._SEQUENCE_MASK
                if self._sequence == 0:
                    timestamp = self._wait_next_millis(self._last_timestamp)
            else:
                self._sequence = 0

            self._last_timestamp = timestamp
            timestamp_part = (timestamp - self._epoch_ms) << self._TIMESTAMP_SHIFT
            datacenter_part = self._datacenter_id << self._DATACENTER_SHIFT
            worker_part = self._worker_id << self._WORKER_SHIFT
            return timestamp_part | datacenter_part | worker_part | self._sequence

    def next_id_str(self) -> str:
        """Return the next ID in its database/API string representation."""
        return str(self.next_id())

    @staticmethod
    def _current_timestamp() -> int:
        return time.time_ns() // 1_000_000

    def _wait_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            time.sleep(0.0001)
            timestamp = self._current_timestamp()
        return timestamp
