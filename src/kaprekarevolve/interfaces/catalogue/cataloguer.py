from collections.abc import Iterator
from typing import Protocol


class Cataloguer(Protocol):
    """Enumerates short formula maps as source. Pure: yields candidates, analyses none."""

    def candidates(self) -> Iterator[tuple[str, str]]:
        """Yield ``(formula, source)`` for every formula in the family."""
        ...
