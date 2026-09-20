from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Source of time. An edge: reading a real clock is non-deterministic."""

    def now(self) -> datetime:
        """Return the current wall-clock time."""
        ...

    def elapsed_seconds(self) -> float:
        """Return a monotonic seconds counter, for measuring durations."""
        ...
