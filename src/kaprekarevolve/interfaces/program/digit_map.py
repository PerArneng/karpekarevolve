from typing import Protocol


class DigitMap(Protocol):
    """A candidate transform: a four-digit number in, a four-digit number out.

    Implementations must be pure, deterministic and total on ``0..9999``.
    """

    def __call__(self, value: int) -> int:
        """Return the successor of ``value``."""
        ...
