from typing import Protocol

from kaprekarevolve.interfaces.program.digit_map import DigitMap


class ProgramLoader(Protocol):
    """Turns candidate source code into a callable. An edge: it executes code."""

    def load(self, source: str) -> DigitMap:
        """Return the transform defined by ``source``.

        Raises:
            ProgramLoadError: if the source does not define a usable transform.

        """
        ...
