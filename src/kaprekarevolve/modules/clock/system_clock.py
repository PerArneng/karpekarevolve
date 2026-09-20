import time
from datetime import datetime


class SystemClock:
    """Reads the real clock."""

    def now(self) -> datetime:
        return datetime.now()

    def elapsed_seconds(self) -> float:
        return time.monotonic()
