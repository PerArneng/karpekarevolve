from datetime import datetime


class FrozenClock:
    """A clock that never moves, so assertions can hardcode timestamps."""

    def __init__(self, moment: datetime, seconds: float = 0.0) -> None:
        self._moment = moment
        self._seconds = seconds

    def now(self) -> datetime:
        return self._moment

    def elapsed_seconds(self) -> float:
        return self._seconds
